# Imagen base con Python
FROM python:3.12-slim

# Instalar FFmpeg e Icecast
RUN apt-get update && \
    apt-get install -y ffmpeg icecast2 && \
    apt-get clean

# Crear carpeta de trabajo
WORKDIR /app

# Copiar todos los archivos del proyecto al contenedor
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requeriments.txt

# Configurar Icecast
RUN mkdir -p /etc/icecast2
COPY icecast.xml /etc/icecast2/icecast.xml

# Exponer puertos: 5000 para Flask, 8000 para Icecast
EXPOSE 5000 8000

# Comando de inicio: primero Icecast, luego Flask
CMD icecast2 -c /etc/icecast2/icecast.xml & python app.py
