# Imagen base
FROM python:3.11-slim

# Instalar dependencias
RUN apt-get update && apt-get install -y icecast2 && rm -rf /var/lib/apt/lists/*

# Crear directorio de la app
WORKDIR /app

# Copiar archivos
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puertos (Flask + Icecast)
EXPOSE 10000 8000

# Comando principal
CMD ["python", "app.py"]
