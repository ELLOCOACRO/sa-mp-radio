FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema y Python
RUN apt-get update && \
    apt-get install -y ffmpeg icecast2 && \
    groupadd -r radio && useradd -r -g radio radio && \
    pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Ajustar permisos de directorios
RUN chown -R radio:radio /app /tmp

# Cambiar usuario (ya no root)
USER radio

# Puerto donde Flask correrá
EXPOSE 10000

# Iniciar Icecast + Flask
CMD bash -c "icecast2 -c ./icecast.xml & sleep 3 && python app.py"
