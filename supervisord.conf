[supervisord]
nodaemon=true
logfile=/dev/stdout
logfile_maxbytes=0
pidfile=/tmp/supervisord.pid
user=root

; -------- Flask (Gunicorn) ----------
[program:flask]
command=/usr/bin/env bash -lc "gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT:-10000} app:app"
directory=/app
autostart=true
autorestart=true
startsecs=3
stopasgroup=true
killasgroup=true
stdout_logfile=/dev/stdout
redirect_stderr=true
priority=10

; -------- Icecast en primer plano ----------
[program:icecast]
command=/usr/bin/icecast2 -c /app/icecast.xml
directory=/app
autostart=true
autorestart=true
startsecs=5
stdout_logfile=/dev/stdout
redirect_stderr=true
user=icecast2
priority=20
