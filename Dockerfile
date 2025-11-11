FROM python:3.11-slim

# Instalamos dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    icecast2 \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Creamos usuario no-root
RUN useradd -m radio
USER radio

WORKDIR /app

# Copiamos archivos del proyecto
COPY . /app

# Instalamos dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Creamos logs y configuración de supervisor
RUN mkdir -p /home/radio/logs

COPY <<EOF /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true

[program:icecast]
command=icecast2 -c /app/icecast.xml
autostart=true
autorestart=true
stdout_logfile=/home/radio/logs/icecast.out.log
stderr_logfile=/home/radio/logs/icecast.err.log

[program:flask]
command=gunicorn -w 2 -b 0.0.0.0:10000 app:app
autostart=true
autorestart=true
stdout_logfile=/home/radio/logs/flask.out.log
stderr_logfile=/home/radio/logs/flask.err.log
EOF

EXPOSE 8000 10000
CMD ["/usr/bin/supervisord"]
