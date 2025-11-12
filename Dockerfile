# Usa una imagen base oficial de Python
FROM python:3.10-slim

# Actualiza e instala ffmpeg para procesar audio
RUN apt-get update && apt-get install -y ffmpeg

# Crea carpetas necesarias
RUN mkdir -p /app /etc/supervisor/conf.d /etc/icecast2 /tmp/icecast

# Copia todo el proyecto al contenedor
COPY . /app
WORKDIR /app

# Instala dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia la configuración de Icecast y Supervisor
COPY icecast.xml /etc/icecast2/icecast.xml
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Ajusta permisos
RUN touch /tmp/icecast/error.log /tmp/icecast/access.log /tmp/icecast/playlist.log && \
    chown -R nobody:nogroup /tmp/icecast

# Exponer el puerto Flask (Render detecta automáticamente)
EXPOSE 10000

# Inicia ambos procesos (Flask + Icecast)
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
