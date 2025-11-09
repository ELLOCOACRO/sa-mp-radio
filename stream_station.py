import os
import subprocess
from pathlib import Path

STATIONS_DIR = Path("static/stations")
STATIONS_DIR.mkdir(parents=True, exist_ok=True)
ICECAST_CONFIG = Path("icecast.xml")

def create_station(name):
    station_path = STATIONS_DIR / name
    if not station_path.exists():
        station_path.mkdir(parents=True)
    return station_path

def list_stations():
    stations = {}
    for i, folder in enumerate(STATIONS_DIR.iterdir()):
        if folder.is_dir():
            songs = [f.name for f in folder.glob("*.mp3")]
            stations[i] = {
                "name": folder.name,
                "songs": songs,
                "path": str(folder),
                "streaming": False
            }
    return stations

def start_stream(station_name):
    station_path = STATIONS_DIR / station_name
    if not station_path.exists():
        raise FileNotFoundError("La estación no existe.")

    mp3_files = list(station_path.glob("*.mp3"))
    if not mp3_files:
        raise FileNotFoundError("No hay canciones en esta estación.")

    song = mp3_files[0]
    print(f"🎧 Transmitiendo: {song.name}")

    command = [
        "ffmpeg", "-re",
        "-i", str(song),
        "-acodec", "libmp3lame",
        "-b:a", "128k",
        "-content_type", "audio/mpeg",
        "-f", "mp3",
        "icecast://source:hackme@localhost:8000/stream"
    ]
    process = subprocess.Popen(command)
    return process

def stop_stream(process):
    if process and process.poll() is None:
        process.terminate()
        print("🛑 Transmisión detenida.")

def get_stream_url(render_host, station_id):
    if render_host:
        return f"https://{render_host}/{station_id}"
    return f"http://localhost:8000/{station_id}"
