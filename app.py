import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory, Response, stream_with_context, abort
import requests

from station_manager import MANAGER, STATIONS_ROOT, ICECAST_PORT

app = Flask(__name__)

@app.get("/")
def index():
    stations = MANAGER.list_stations()
    # URLs públicas de stream (Flask proxyea a Icecast)
    for s in stations:
        s["public_url"] = f"/stream/{s['mount']}"
        s["music_path"] = f"stations/{s['name']}/music"
    return render_template("index.html", stations=stations)

@app.post("/api/stations")
def create_station():
    data = request.get_json(silent=True) or {}
    name = data.get("name") or request.args.get("name")
    if not name:
        return jsonify({"error": "Falta 'name'"}), 400
    try:
        mount = MANAGER.create_station(name)
        return jsonify({"name": name, "mount": mount, "stream_url": f"/stream/{mount}"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.post("/api/stations/<name>/upload")
def upload_music(name):
    st = MANAGER.get_station(name)
    if not st:
        return jsonify({"error": "Estación no existe"}), 404
    music_dir = STATIONS_ROOT / name / "music"
    music_dir.mkdir(parents=True, exist_ok=True)
    if "file" not in request.files:
        return jsonify({"error": "Sube un archivo en form-data con clave 'file'"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Archivo inválido"}), 400
    # Guardar
    dest = music_dir / f.filename
    f.save(dest.as_posix())
    return jsonify({"ok": True, "saved": dest.name}), 201

@app.get("/api/stations")
def list_stations():
    return jsonify(MANAGER.list_stations())

@app.post("/api/stations/<name>/stop")
def stop_station(name):
    st = MANAGER.get_station(name)
    if not st:
        return jsonify({"error": "Estación no existe"}), 404
    MANAGER.stop_station(name)
    return jsonify({"ok": True})

@app.get("/stream/<mount>")
def proxy_stream(mount):
    # Proxy del stream de Icecast → cliente final (Render expone solo $PORT)
    # Ej: /stream/stream_rock proxyea a http://127.0.0.1:8000/stream_rock
    upstream = f"http://127.0.0.1:{ICECAST_PORT}/{mount}"
    try:
        r = requests.get(upstream, stream=True, timeout=5)
    except requests.exceptions.RequestException:
        abort(502, description="No se pudo conectar al Icecast")

    if r.status_code != 200:
        abort(r.status_code)

    def generate():
        try:
            for chunk in r.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk
        finally:
            r.close()

    # Content-Type típico del mp3 icecast
    return Response(stream_with_context(generate()), content_type="audio/mpeg")

@app.get("/health")
def health():
    return {"status": "ok"}

# Static (por si quieres listar canciones subidas)
@app.get("/stations/<path:subpath>")
def serve_stations(subpath):
    safe_root = Path("stations").resolve()
    requested = (safe_root / subpath).resolve()
    if safe_root not in requested.parents and requested != safe_root:
        abort(403)
    directory = requested.parent
    filename = requested.name
    return send_from_directory(directory, filename)
