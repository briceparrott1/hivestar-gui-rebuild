# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # SQLite lives on a mounted volume so data survives container restarts.
    SQLITE_PATH=/data/db.sqlite3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The DB file is created/migrated at container start (below), so the directory
# it lives in must exist and be a mount point.
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 9000

# Migrate at *start* (not build) so migrations apply to the mounted SQLite file,
# then serve. Port 9000 matches service #1's default TARGET_URL.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn missioncontrol.wsgi:application --bind 0.0.0.0:9000 --workers 3"]
