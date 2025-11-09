# Imagen base con Python
FROM python:3.12-slim

# Instala ffmpeg e icecast
RUN apt-get update && apt-get install -y ffmpeg icecast2 && rm -rf /var/lib/apt/lists/*

# Carpeta de la app
WORKDIR /app

# Copia todo
COPY . /app

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto de Flask y Icecast
EXPOSE 5000 8000

# Comando para correr Flask y Icecast
CMD icecast2 -c /app/icecast.xml & python app.py
