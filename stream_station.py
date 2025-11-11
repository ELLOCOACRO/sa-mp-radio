import os
import subprocess
from pathlib import Path

BASE_DIR = Path("static/stations")
ICECAST_HOST = "0.0.0.0"
ICECAST_PORT = 8000
ICECAST_PASS = "hackme"

def create_station(name):
    """Crea una carpeta para una estación."""
    station_dir = BASE_DIR / name
    station_dir.mkdir(parents=True, exist_ok=True)
    return station_dir

def list_stations():
    """Lista todas las estaciones disponibles y sus canciones."""
    stations = {}
    BASE_DIR.mkdir(exist_ok=True)
    for station in BASE_DIR.iterdir():
        if station.is_dir():
            songs = [f.name for f in station.iterdir() if f.suffix in [".mp3", ".wav"]]
            stations[station.name] = songs
    return stations

def start_stream(name):
    """Inicia una transmisión continua de todas las canciones en la estación."""
    station_path = BASE_DIR / name
    if not station_path.exists():
        raise Exception(f"La estación '{name}' no existe.")

    playlist = [str(station_path / s) for s in os.listdir(station_path) if s.endswith((".mp3", ".wav"))]
    if not playlist:
        raise Exception(f"No hay canciones en la estación '{name}'.")

    ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",
        "-i", f"concat:{'|'.join(playlist)}",
        "-acodec", "libmp3lame",
        "-b:a", "128k",
        "-content_type", "audio/mpeg",
        "-f", "mp3",
        f"icecast://source:{ICECAST_PASS}@{ICECAST_HOST}:{ICECAST_PORT}/stream_{name}"
    ]
    return subprocess.Popen(ffmpeg_cmd)

def stop_stream(process):
    """Detiene un proceso de transmisión."""
    if process:
        process.terminate()

def get_stream_url(render_host, station_id):
    """Devuelve la URL pública del stream."""
    if render_host:
        return f"https://{render_host}/{station_id}"
    return f"http://localhost:8000/{station_id}"
