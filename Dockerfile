FROM python:3.11-slim

# Paquetes del sistema: icecast2, ffmpeg, supervisor
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    icecast2 ffmpeg supervisor ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencias Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Código y configuraciones
COPY . /app

# Asegura permisos de lectura/ejecución para que icecast2 pueda leer /app/icecast.xml
RUN chmod 755 /app && \
    chmod 644 /app/icecast.xml

# Config de supervisor
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Un solo puerto público (Flask/Gunicorn a $PORT)
EXPOSE 10000

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
