# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Instala dependencias del sistema necesarias para FFmpeg e Icecast
RUN apt-get update && apt-get install -y ffmpeg icecast2 && apt-get clean

# Crea el directorio de trabajo
WORKDIR /app

# Copia los archivos de la app
COPY . /app

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer los puertos de Flask (10000) e Icecast (8000)
EXPOSE 10000 8000

# Comando para iniciar Icecast y luego Flask
CMD service icecast2 start && gunicorn -b 0.0.0.0:10000 app:app
