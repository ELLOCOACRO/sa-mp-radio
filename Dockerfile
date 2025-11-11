# Imagen base de Python ligera
FROM python:3.11-slim

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar todos los archivos del proyecto (incluye requirements.txt)
COPY . .

# Instalar dependencias del sistema (ffmpeg, icecast2) y luego Python
RUN apt-get update && \
    apt-get install -y ffmpeg icecast2 && \
    groupadd -r radio && useradd -r -g radio radio && \
    pip install --no-cache-dir -r requirements.txt

# Dar permisos al usuario "radio" sobre los directorios necesarios
RUN chown -R radio:radio /app /tmp

# Cambiar el usuario activo (ya no root)
USER radio

# Exponer el puerto que usará Flask
EXPOSE 10000

# Iniciar Icecast y Flask (con pausa para que Icecast arranque primero)
CMD bash -c "icecast2 -c ./icecast.xml & sleep 3 && python app.py"
