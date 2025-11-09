from flask import Flask, render_template, redirect, url_for
import os
from stream_station import start_stream, stop_stream

app = Flask(__name__)

# Lista de estaciones
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stations_dir = os.path.join(BASE_DIR, "static", "stations")

stations = {}
for station_id in os.listdir(stations_dir):
    station_path = os.path.join(stations_dir, station_id)
    if os.path.isdir(station_path):
        songs = [f for f in os.listdir(station_path) if f.endswith(".mp3")]
        stations[station_id] = {
            "name": station_id,
            "songs": songs,
            "streaming": False
        }

@app.route('/')
def index():
    return render_template("index.html", stations=stations)

@app.route('/start/<station_id>')
def start_station(station_id):
    if station_id in stations and not stations[station_id]["streaming"]:
        start_stream(station_id, stations[station_id]["songs"])
        stations[station_id]["streaming"] = True
    return redirect(url_for('index'))

@app.route('/stop/<station_id>')
def stop_station(station_id):
    if station_id in stations and stations[station_id]["streaming"]:
        stop_stream(station_id)
        stations[station_id]["streaming"] = False
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
