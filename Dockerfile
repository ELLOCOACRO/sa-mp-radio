FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN apt-get update && \
    apt-get install -y ffmpeg icecast2 && \
    touch /etc/mime.types && \
    groupadd -r radio && useradd -r -g radio radio && \
    mkdir -p /tmp && \
    chown -R radio:radio /app /tmp && \
    pip install --no-cache-dir -r requirements.txt

USER radio

EXPOSE 10000

CMD icecast2 -c /app/icecast.xml & gunicorn --bind 0.0.0.0:$PORT app:app
