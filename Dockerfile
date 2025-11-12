FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    icecast2 supervisor ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# supervisor + icecast config
RUN mkdir -p /etc/supervisor/conf.d /etc/icecast2 /tmp/icecast && \
    touch /tmp/icecast/error.log /tmp/icecast/access.log /tmp/icecast/playlist.log && \
    chown -R nobody:nogroup /tmp/icecast

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY icecast.xml /etc/icecast2/icecast.xml

# Render inyecta PORT en runtime; EXPOSE es opcional
EXPOSE 10000

CMD ["supervisord","-n","-c","/etc/supervisor/conf.d/supervisord.conf"]
