from flask import Flask, render_template, request, jsonify
from stream_station import create_station, list_stations, start_stream, stop_stream, get_stream_url
import os

app = Flask(__name__)

# Para almacenar los procesos de transmisión activos
active_streams = {}

@app.route("/")
def index():
    stations = list_stations()
    return render_template("index.html", stations=stations)

@app.route("/create_station", methods=["POST"])
def create_station_route():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Nombre de estación requerido"}), 400
    path = create_station(name)
    return jsonify({"message": f"Estación '{name}' creada exitosamente.", "path": str(path)})

@app.route("/start_stream", methods=["POST"])
def start_stream_route():
    data = request.get_json()
    name = data.get("name")
    try:
        process = start_stream(name)
        active_streams[name] = process
        render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        stream_url = get_stream_url(render_host, f"stream_{name}")
        return jsonify({"message": f"🎶 Transmisión iniciada en {stream_url}", "url": stream_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stop_stream", methods=["POST"])
def stop_stream_route():
    data = request.get_json()
    name = data.get("name")
    process = active_streams.get(name)
    if not process:
        return jsonify({"error": "No hay transmisión activa para esta estación."}), 404
    stop_stream(process)
    del active_streams[name]
    return jsonify({"message": f"🛑 Transmisión de '{name}' detenida."})

@app.route("/status")
def status():
    return jsonify({
        "stations": list(list_stations().keys()),
        "active_streams": list(active_streams.keys())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Servidor Flask en marcha en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
