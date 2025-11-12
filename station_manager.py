import os
import random
import sqlite3
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = "stations.db"
STATIONS_ROOT = Path("stations")

ICECAST_HOST = "127.0.0.1"
ICECAST_PORT = 8000
ICECAST_SOURCE_PASS = os.getenv("ICECAST_SOURCE_PASS", "sourcepassword")

STATIONS_ROOT.mkdir(parents=True, exist_ok=True)


def db():
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
    def __init__(self, station_name: str, mount: str, music_dir: Path):
        super().__init__(daemon=True)
        self.station_name = station_name
        self.mount = mount
        self.music_dir = music_dir
        self.proc: Optional[subprocess.Popen] = None
        self.stop_event = threading.Event()

    def build_playlist(self) -> List[Path]:
        files: List[Path] = []
        for ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
            files += list(self.music_dir.glob(f"*{ext}"))
        return [f for f in files if f.is_file()]

    def write_concat_file(self, files: List[Path]) -> Optional[Path]:
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
                abs_path = p.resolve().as_posix()
                safe = abs_path.replace("'", r"'\''")
                f.write(f"file '{safe}'\n")
        return concat_path

    def build_cmd(self, concat_file: Path) -> List[str]:
        url = f"icecast://source:{ICECAST_SOURCE_PASS}@{ICECAST_HOST}:{ICECAST_PORT}/{self.mount}"
        return [
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

    def stop(self):
        self.stop_event.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

    def run(self):
        while not self.stop_event.is_set():
            files = self.build_playlist()
            if not files:
                time.sleep(5)
                continue
            concat_file = self.write_concat_file(files)
            if not concat_file:
                time.sleep(5)
                continue
            try:
                self.proc = subprocess.Popen(self.build_cmd(concat_file))
                self.proc.wait()
            except Exception:
                time.sleep(2)
            finally:
                self.proc = None


class StationManager:
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

    def delete_station_record(self, name: str):
        with DB_LOCK:
            DB_CONN.execute("DELETE FROM stations WHERE name=?", (name,))
            DB_CONN.commit()

    def start_station(self, name: str, mount: str, music_dir: Path):
        with self.lock:
            r = self.runners.get(name)
            if r and r.is_alive():
                return
            runner = FFmpegRunner(name, mount, music_dir)
            self.runners[name] = runner
            runner.start()
        with DB_LOCK:
            DB_CONN.execute("UPDATE stations SET enabled=1 WHERE name=?", (name,))
            DB_CONN.commit()

    def start_by_name(self, name: str):
        st = self.get_station(name)
        if not st:
            return
        music_dir = STATIONS_ROOT / name / "music"
        music_dir.mkdir(parents=True, exist_ok=True)
        self.start_station(name, st["mount"], music_dir)

    def stop_station(self, name: str):
        with self.lock:
            r = self.runners.get(name)
            if r:
                r.stop()
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
                "SELECT id, name, mount, enabled FROM stations WHERE name=?", (name,)
            )
            r = cur.fetchone()
            if not r:
                return None
            return {"id": r[0], "name": r[1], "mount": r[2], "enabled": bool(r[3])}

    def is_running(self, name: str) -> bool:
        r = self.runners.get(name)
        return bool(r and r.is_alive())


MANAGER = StationManager()
