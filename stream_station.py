import os
import random
import subprocess
import time

STATION_NAME = "station1"
STATION_PATH = os.path.join("C:\\Users\\Erick\\Documents\\sa-mp-radio\\static\\stations", STATION_NAME)

ICECAST_URL = f"icecast://source:hackme@localhost:8000/{STATION_NAME}"

while True:
    songs = [f for f in os.listdir(STATION_PATH) if f.endswith(".mp3")]
    if not songs:
        time.sleep(5)
        continue
    song = random.choice(songs)
    song_path = os.path.join(STATION_PATH, song)

    # Ejecutar FFmpeg
    cmd = [
        "ffmpeg",
        "-re",
        "-i", song_path,
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        "-content_type", "audio/mpeg",
        "-f", "mp3",
        ICECAST_URL
    ]
    subprocess.run(cmd)
