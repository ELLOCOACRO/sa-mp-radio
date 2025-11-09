import os
import subprocess
import threading

# Carpeta base de estaciones (relativa)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIONS_DIR = os.path.join(BASE_DIR, "static", "stations")

# Diccionario para hilos de streaming activos
threads = {}

def start_stream(station_id, songs):
    if station_id in threads:
        return  # Ya está transmitiendo

    def stream():
        while True:
            for song in songs:
                song_path = os.path.join(STATIONS_DIR, station_id, song) if not os.path.isabs(song) else song
                # Usa Icecast en localhost:8000, contraseña 'hackme', nombre de la estación = station_id
                cmd = [
                    "ffmpeg",
                    "-re",
                    "-i", song_path,
                    "-c:a", "libmp3lame",
                    "-b:a", "128k",
                    "-content_type", "audio/mpeg",
                    "-f", "mp3",
                    f"icecast://source:hackme@localhost:8000/{station_id}"
                ]
                subprocess.run(cmd)

    t = threading.Thread(target=stream, daemon=True)
    t.start()
    threads[station_id] = t

def stop_stream(station_id):
    # Simplemente eliminamos el hilo activo
    if station_id in threads:
        # No hay forma directa de matar ffmpeg, reiniciar sería opción
        threads.pop(station_id)
