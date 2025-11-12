FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Instalar Icecast, FFmpeg, Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    icecast2 ffmpeg supervisor ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencias Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Código
COPY . /app

# Config de supervisor
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Config de Icecast (sin changeowner)
RUN mkdir -p /etc/icecast2 /tmp/icecast && chown -R nobody:nogroup /tmp/icecast
COPY icecast.xml /etc/icecast2/icecast.xml
RUN chown root:root /etc/icecast2/icecast.xml

# Puertos
ENV PORT=10000
EXPOSE 10000 8000

CMD ["/usr/bin/supervisord","-n","-c","/etc/supervisor/conf.d/supervisord.conf"]
