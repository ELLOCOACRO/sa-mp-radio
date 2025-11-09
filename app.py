from flask import Flask, render_template, request, redirect, url_for
import os
from stream_station import start_stream, stop_stream  # tu script de streaming

app = Flask(__name__)

# Diccionario de estaciones con sus canciones
stations = {
    "station1": {
        "name": "Estación 1",
        "songs": [
            "static/stations/station1/cancion1.mp3",
            "static/stations/station1/Canserbero - Tiempos de Cambio  Letra - Lyrics.mp3",
            "static/stations/station1/Canserbero - Y la Felicidad Qu\303\251_ [Vida].mp3"
        ],
        "streaming": False
    }
    # Puedes agregar más estaciones aquí
}

@app.route('/')
def index():
    return render_template("index.html", stations=stations)

@app.route('/start/<station_id>')
def start_station(station_id):
    if station_id in stations and not stations[station_id]["streaming"]:
        # Inicia el streaming usando tu script
        start_stream(station_id, stations[station_id]["songs"])
        stations[station_id]["streaming"] = True
    return redirect(url_for('index'))

@app.route('/stop/<station_id>')
def stop_station(station_id):
    if station_id in stations and stations[station_id]["streaming"]:
        # Detiene el streaming
        stop_stream(station_id)
        stations[station_id]["streaming"] = False
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Detecta el puerto que Render asigna o usa 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    # Escucha en todas las interfaces para que Render pueda conectarse
    app.run(host="0.0.0.0", port=port, debug=True)

