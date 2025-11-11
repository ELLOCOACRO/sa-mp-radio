FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Copiar todo el contenido del proyecto
COPY . .

# Instalar dependencias del sistema y Python
RUN apt-get update && \
    apt-get install -y ffmpeg icecast2 && \
    pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de Flask
EXPOSE 10000

# Iniciar Icecast primero y luego Flask
# El 'sleep 3' da tiempo a que Icecast se inicie antes de que Flask use ffmpeg
CMD bash -c "icecast2 -c ./icecast.xml & sleep 3 && python app.py"
