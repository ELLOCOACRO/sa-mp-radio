from flask import Flask, render_template, request
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return {"status": "ok", "message": "SA-MP Radio funcionando correctamente"}

if __name__ == "__main__":
    # Puerto dinámico para Render o 5000 en local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
