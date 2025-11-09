from flask import Flask, render_template, request, redirect, url_for
import os
import shutil

app = Flask(__name__)
BASE_PATH = os.path.join("static", "stations")

def get_stations():
    stations = {}
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)
    for folder in os.listdir(BASE_PATH):
        path = os.path.join(BASE_PATH, folder)
        if os.path.isdir(path):
            stations[folder] = [f for f in os.listdir(path) if f.endswith(".mp3")]
    return stations

@app.route("/")
def index():
    stations = get_stations()
    return render_template("index.html", stations=stations)

# Crear estación
@app.route("/add_station", methods=["POST"])
def add_station():
    name = request.form.get("station_name")
    if name:
        os.makedirs(os.path.join(BASE_PATH, name), exist_ok=True)
    return redirect(url_for('index'))

# Borrar estación
@app.route("/delete_station/<station>")
def delete_station(station):
    path = os.path.join(BASE_PATH, station)
    if os.path.exists(path):
        shutil.rmtree(path)
    return redirect(url_for('index'))

# Subir canción
@app.route("/upload/<station>", methods=["POST"])
def upload_song(station):
    file = request.files.get("song_file")
    if file and file.filename.endswith(".mp3"):
        save_path = os.path.join(BASE_PATH, station, file.filename)
        file.save(save_path)
    return redirect(url_for('index'))

# Borrar canción
@app.route("/delete_song/<station>/<song>")
def delete_song(station, song):
    path = os.path.join(BASE_PATH, station, song)
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
