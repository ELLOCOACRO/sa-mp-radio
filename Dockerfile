# Imagen base de Python ligera
FROM python:3.11-slim

# Instala Icecast2 y FFmpeg
RUN apt-get update && apt-get install -y icecast2 ffmpeg && apt-get clean

# Crea usuario no root (necesario para Icecast)
RUN adduser --disabled-password --gecos "" iceuser

# Directorio del proyecto
WORKDIR /app

# Copia los archivos del proyecto
COPY . .

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Cambia permisos
RUN chown -R iceuser:iceuser /app

# Cambia al usuario no root
USER iceuser

# Expone puertos (Icecast y Flask)
EXPOSE 8000
EXPOSE 5000

# Comando para ejecutar ambos servicios
CMD bash -c "icecast2 -b -c /app/icecast.xml & python app.py"
