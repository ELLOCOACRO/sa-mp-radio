import os
import subprocess
import requests
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

app = Flask(__name__)

# Configuración básica del servidor Icecast
ICECAST_HOST = "localhost"
ICECAST_PORT = 8000
ICECAST_PASS = "hackme"
STREAM_NAME = "stream"
ICECAST_URL = f"http://{ICECAST_HOST}:{ICECAST_PORT}/{STREAM_NAME}"

@app.route("/")
def index():
    """Página principal con el reproductor de la radio"""
    return render_template("index.html", stream_url="/radio.mp3")

@app.route("/start", methods=["POST"])
def start_stream():
    """Inicia la transmisión de un archivo MP3 hacia el servidor Icecast"""
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No se subió ningún archivo"}), 400

    # Guardar archivo temporal
    filepath = "/tmp/upload.mp3"
    file.save(filepath)

    # Comando FFmpeg para enviar el audio a Icecast
    ffmpeg_cmd = [
        "ffmpeg",
        "-re",  # Leer en tiempo real
        "-i", filepath,  # Archivo de entrada
        "-acodec", "libmp3lame",  # Codificador MP3
        "-b:a", "128k",  # Bitrate
        "-content_type", "audio/mpeg",
        "-f", "mp3",
        f"icecast://source:{ICECAST_PASS}@{ICECAST_HOST}:{ICECAST_PORT}/{STREAM_NAME}"
    ]

    try:
        subprocess.Popen(ffmpeg_cmd)
        return jsonify({"message": "🎶 Transmisión iniciada correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/radio.mp3")
def proxy_stream():
    """Canaliza el flujo de Icecast hacia Flask (Render-friendly)"""
    def generate():
        with requests.get(ICECAST_URL, stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

    return Response(stream_with_context(generate()), mimetype="audio/mpeg")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Servidor Flask ejecutándose en el puerto {port}")
    app.run(host="0.0.0.0", port=port)
