FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y ffmpeg icecast2 && pip install -r requirements.txt

EXPOSE 10000

CMD bash -c "icecast2 -c ./icecast.xml & python app.py"
