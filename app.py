import os
from flask import Flask, render_template, jsonify, request
import subprocess

app = Flask(__name__, static_folder='static', template_folder='templates')

# --- Configuración base ---
ICECAST_CONFIG = "/app/icecast.xml"
ICECAST_PORT = 8000
STREAM_DIR = "static/stations"
os.makedirs(STREAM_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html', stream_link=f"http://{request.host}:{ICECAST_PORT}/stream")

@app.route('/create_station', methods=['POST'])
def create_station():
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Debes ingresar un nombre"}), 400

    station_path = os.path.join(STREAM_DIR, name)
    os.makedirs(station_path, exist_ok=True)
    return jsonify({"message": f"Estación '{name}' creada correctamente."})

@app.route('/songs')
def songs():
    songs_list = []
    for root, _, files in os.walk(STREAM_DIR):
        for file in files:
            if file.endswith(('.mp3', '.ogg', '.wav')):
                songs_list.append(os.path.relpath(os.path.join(root, file), STREAM_DIR))
    return jsonify(songs_list)

@app.route('/status')
def status():
    # Simple status mock
    return jsonify({"status": "online", "icecast_port": ICECAST_PORT})

if __name__ == "__main__":
    # Inicia Icecast antes del servidor Flask
    try:
        subprocess.Popen(["icecast2", "-c", ICECAST_CONFIG])
        print("✅ Icecast iniciado correctamente.")
    except Exception as e:
        print(f"⚠️ Error al iniciar Icecast: {e}")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
