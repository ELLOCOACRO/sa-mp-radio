import os
import sqlite3
import threading
import time
import random
import subprocess
from pathlib import Path
from typing import Dict, Optional, List

DB_PATH = "stations.db"
STATIONS_ROOT = Path("stations")
ICECAST_HOST = "127.0.0.1"
ICECAST_PORT = 8000
ICECAST_SOURCE_PASS = os.getenv("ICECAST_SOURCE_PASS", "sourcepassword")

# Asegura carpetas base
STATIONS_ROOT.mkdir(parents=True, exist_ok=True)


def db():
    """Inicializa (si no existe) y retorna una conexión SQLite thread-safe."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            mount TEXT UNIQUE NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.commit()
    return conn


DB_CONN = db()
DB_LOCK = threading.Lock()


class FFmpegRunner(threading.Thread):
    """
    Hilo que mantiene una estación transmitiendo 24/7.
    Crea playlists aleatorias (evita repetir la misma canción consecutivamente)
    y relanza ffmpeg cuando termina la lista.
    """

    def __init__(self, station_name: str, mount: str, music_dir: Path):
        super().__init__(daemon=True)
        self.station_name = station_name
        self.mount = mount
        self.music_dir = music_dir
        self.proc: Optional[subprocess.Popen] = None
        self.stop_event = threading.Event()

    def build_playlist(self) -> List[Path]:
        """Devuelve la lista de archivos de audio admitidos en la carpeta de la estación."""
        files: List[Path] = []
        for ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
            files += list(self.music_dir.glob(f"*{ext}"))
        return [f for f in files if f.is_file()]

    def write_concat_file(self, files: List[Path]) -> Optional[Path]:
        """
        Crea un archivo de lista para el demuxer 'concat' de ffmpeg.
        Usa rutas absolutas para evitar duplicaciones relativas.
        Devuelve la ruta al archivo o None si no hay música.
        """
        if not files:
            return None

        order = files[:]
        random.shuffle(order)

        if len(order) > 1:
            while any(order[i] == order[i + 1] for i in range(len(order) - 1)):
                random.shuffle(order)

        concat_path = self.music_dir / "_playlist.txt"
        with open(concat_path, "w", encoding="utf-8") as f:
            for p in order:
                abs_path = p.resolve().as_posix()        # ABSOLUTO
                safe = abs_path.replace("'", r"'\''")    # escape de comillas simples
                f.write(f"file '{safe}'\n")
        return concat_path

    def build_ffmpeg_cmd(self, concat_file: Path) -> List[str]:
        """Construye el comando ffmpeg para emitir a Icecast como MP3 128 kbps."""
        url = (
            f"icecast://source:{ICECAST_SOURCE_PASS}@"
            f"{ICECAST_HOST}:{ICECAST_PORT}/{self.mount}"
        )
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-re",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            "-content_type",
            "audio/mpeg",
            "-f",
            "mp3",
            url,
        ]
        return cmd

    def stop(self):
        """Solicita parada del hilo y termina ffmpeg si está corriendo."""
        self.stop_event.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

    def run(self):
        """Bucle principal: genera playlist y lanza ffmpeg; repite para 24/7."""
        while not self.stop_event.is_set():
            files = self.build_playlist()
            if not files:
                time.sleep(5)
                continue

            concat_file = self.write_concat_file(files)
            if concat_file is None:
                time.sleep(5)
                continue

            cmd = self.build_ffmpeg_cmd(concat_file)
            try:
                self.proc = subprocess.Popen(cmd)
                self.proc.wait()
            except Exception:
                time.sleep(2)
            finally:
                self.proc = None


class StationManager:
    """Administra estaciones: crea, inicia, detiene y lista."""

    def __init__(self):
        self.runners: Dict[str, FFmpegRunner] = {}
        self.lock = threading.Lock()
        self._load_existing()

    def _load_existing(self):
        with DB_LOCK:
            cur = DB_CONN.execute("SELECT name, mount, enabled FROM stations")
            rows = cur.fetchall()
        for name, mount, enabled in rows:
            music_dir = STATIONS_ROOT / name / "music"
            music_dir.mkdir(parents=True, exist_ok=True)
            if enabled:
                self.start_station(name, mount, music_dir)

    def create_station(self, name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Nombre inválido")
        mount = f"stream_{name.lower().replace(' ', '_')}"
        music_dir = STATIONS_ROOT / name / "music"
        music_dir.mkdir(parents=True, exist_ok=True)

        with DB_LOCK:
            DB_CONN.execute(
                "INSERT INTO stations (name, mount, enabled) VALUES (?, ?, ?)",
                (name, mount, 1),
            )
            DB_CONN.commit()

        self.start_station(name, mount, music_dir)
        return mount

    def start_station(self, name: str, mount: str, music_dir: Path):
        with self.lock:
            runner = self.runners.get(name)
            if runner and runner.is_alive():
                return
            runner = FFmpegRunner(name, mount, music_dir)
            self.runners[name] = runner
            runner.start()

    def stop_station(self, name: str):
        with self.lock:
            runner = self.runners.get(name)
            if runner:
                runner.stop()
                self.runners.pop(name, None)
        with DB_LOCK:
            DB_CONN.execute("UPDATE stations SET enabled=0 WHERE name=?", (name,))
            DB_CONN.commit()

    def list_stations(self):
        with DB_LOCK:
            cur = DB_CONN.execute(
                "SELECT id, name, mount, enabled FROM stations ORDER BY id ASC"
            )
            return [
                {"id": r[0], "name": r[1], "mount": r[2], "enabled": bool(r[3])}
                for r in cur.fetchall()
            ]

    def get_station(self, name: str):
        with DB_LOCK:
            cur = DB_CONN.execute(
                "SELECT id, name, mount, enabled FROM stations WHERE name=?",
                (name,),
            )
            r = cur.fetchone()
            if not r:
                return None
            return {"id": r[0], "name": r[1], "mount": r[2], "enabled": bool(r[3])}


# Instancia global usada por app.py
MANAGER = StationManager()
