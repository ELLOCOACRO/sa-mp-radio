import os
from flask import Flask, render_template, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Ruta base de estaciones
STATIONS_DIR = os.path.join("static", "stations")
os.makedirs(STATIONS_DIR, exist_ok=True)


@app.route("/")
def home():
    stations = []
    for folder in os.listdir(STATIONS_DIR):
        path = os.path.join(STATIONS_DIR, folder)
        if os.path.isdir(path):
            songs = [f for f in os.listdir(path) if f.endswith(('.mp3', '.wav'))]
            stations.append({
                "name": folder,
                "song_count": len(songs),
                "stream_link": f"https://{request.host}/static/stations/{folder}/"
            })
    return render_template("index.html", stations=stations)


@app.route("/create_station", methods=["POST"])
def create_station():
    data = request.get_json()
    name = data.get("name")
    path = os.path.join(STATIONS_DIR, name)
    if not os.path.exists(path):
        os.makedirs(path)
        return jsonify({"success": True, "message": f"Estación '{name}' creada."})
    return jsonify({"success": False, "message": "La estación ya existe."})


@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat()
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
