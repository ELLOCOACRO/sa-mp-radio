FROM python:3.11-slim

# Instalar Icecast, FFmpeg y Supervisor
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    icecast2 ffmpeg supervisor ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar código fuente y configuraciones
COPY . /app

# Permisos correctos
RUN chmod 755 /app && \
    chmod 644 /app/icecast.xml

# Configurar supervisor
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Exponer puerto de Flask
EXPOSE 10000

# Iniciar supervisord (que lanza Flask + Icecast)
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
