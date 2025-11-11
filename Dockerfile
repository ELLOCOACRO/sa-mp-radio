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

# Instala la config de Icecast en su ruta estándar
RUN mkdir -p /etc/icecast2 && \
    cp /app/icecast.xml /etc/icecast2/icecast.xml

# Config de supervisor
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Permisos recomendados
RUN chown -R root:root /etc/icecast2

# Render expone 1 puerto (usaremos $PORT). No expongas 8000.
# EXPOSE no es obligatorio en Render, pero no hace daño:
EXPOSE 10000

# Inicia supervisor en primer plano
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
