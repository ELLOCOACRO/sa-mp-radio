import os
import shutil
from pathlib import Path
from typing import Generator

from flask import Flask, jsonify, render_template, request, Response, abort
import requests

from station_manager import MANAGER, STATIONS_ROOT, ICECAST_HOST, ICECAST_PORT

app = Flask(__name__)

# ---- Crear estación por defecto al iniciar ----
def ensure_default_station():
    stations = MANAGER.list_stations()
    if not stations:
        MANAGER.create_station("default")
    else:
        for s in stations:
            if s["name"].lower() == "default" and not MANAGER.is_running(s["name"]):
                MANAGER.start_by_name(s["name"])
ensure_default_station()


def station_view_model():
    out = []
    for s in MANAGER.list_stations():
        status = "running" if MANAGER.is_running(s["name"]) else "stopped"
        out.append(
            {
                "id": s["id"],
                "name": s["name"],
                "mount": s["mount"],
                "enabled": bool(s["enabled"]),
                "status": status,
                "stream_url": f"/stream/{s['mount']}",
                "music_path": f"stations/{s['name']}/music",
            }
        )
    return out


@app.get("/")
def index():
    return render_template("index.html", stations=station_view_model())


@app.get("/api/stations")
def api_list():
    return jsonify(station_view_model())


@app.post("/api/stations")
def api_create():
    data = request.get_json(silent=True) or {}
    name = data.get("name") or request.args.get("name")
    if not name:
        return jsonify({"error": "Falta 'name'"}), 400
    try:
        mount = MANAGER.create_station(name)
        return jsonify({"name": name, "mount": mount, "stream_url": f"/stream/{mount}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/stations/<name>/start")
def api_start(name: str):
    if not MANAGER.get_station(name):
        return jsonify({"error": "No existe"}), 404
    MANAGER.start_by_name(name)
    return jsonify({"ok": True})


@app.post("/api/stations/<name>/stop")
def api_stop(name: str):
    if not MANAGER.get_station(name):
        return jsonify({"error": "No existe"}), 404
    MANAGER.stop_station(name)
    return jsonify({"ok": True})


@app.delete("/api/stations/<name>")
def api_delete(name: str):
    st = MANAGER.get_station(name)
    if not st:
        return jsonify({"error": "No existe"}), 404
    MANAGER.stop_station(name)
    MANAGER.delete_station_record(name)
    folder = STATIONS_ROOT / name
    try:
        if folder.exists():
            shutil.rmtree(folder)
    except Exception as e:
        return jsonify({"error": f"No se pudo borrar carpeta: {e}"}), 500
    return jsonify({"ok": True})


@app.post("/api/stations/<name>/upload")
def api_upload(name: str):
    st = MANAGER.get_station(name)
    if not st:
        return jsonify({"error": "No existe"}), 404
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "Sube al menos un archivo"}), 400
    music_dir = STATIONS_ROOT / name / "music"
    music_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        fname = f.filename or ""
        if not fname:
            continue
        if not any(fname.lower().endswith(ext) for ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a")):
            continue
        path = music_dir / fname
        f.save(path)
        saved.append(path.name)

    return jsonify({"ok": True, "saved": saved})


@app.get("/stream/<mount>")
def stream_proxy(mount: str):
    url = f"http://{ICECAST_HOST}:{ICECAST_PORT}/{mount}"
    try:
        r = requests.get(url, stream=True, timeout=5)
    except Exception:
        abort(502, description="Icecast no disponible")

    def generate() -> Generator[bytes, None, None]:
        try:
            for chunk in r.iter_content(chunk_size=32 * 1024):
                if chunk:
                    yield chunk
        finally:
            r.close()

    headers = {
        "Content-Type": r.headers.get("Content-Type", "audio/mpeg"),
        "Cache-Control": "no-cache",
        "Access-Control-Allow-Origin": "*",
    }
    return Response(generate(), headers=headers)


@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
