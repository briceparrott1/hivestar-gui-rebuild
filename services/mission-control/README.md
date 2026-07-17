# services/mission-control (service #2)

A single Django app that **ingests**, **stores**, and **displays** telemetry
logs. It listens for logs at `POST /ingest`, writes each request body to SQLite
**verbatim** (no parsing on this cut), and renders them on a dark,
mission-control-style dashboard at `GET /`.

This is **scaffolding**: the frameworks are wired up, the app is Dockerized, the
richer normalized data model is stubbed, and exactly one end-to-end write path
(ingest → store → display) is proven.

## Endpoints

| Method | Path      | Purpose                                                          |
| ------ | --------- | --------------------------------------------------------------- |
| `POST` | `/ingest` | Store the raw request body verbatim as a `RawLog`. Returns `201`. CSRF-exempt (the caller is service #1, a machine). Empty body → `400`. |
| `GET`  | `/`       | Server-rendered dashboard listing stored logs, newest first.    |

The `/ingest` path (no trailing slash) matches service #1's default
`TARGET_URL` (`http://localhost:9000/ingest`), so the two services wire together
directly.

## Data model

- **Concrete + migrated:** `RawLog(payload: TextField, received_at: DateTimeField
  auto_now_add)`, ordered newest-first.
- **Stubbed (not migrated):** `Satellite`, `Mission`, `Task`, `Event` and their
  relationships are sketched as a commented placeholder in
  [`logs/models.py`](logs/models.py) for a later PR that will parse raw logs into
  a normalized schema. They are intentionally not defined or migrated here.

## Run with Docker

The container migrates SQLite at **start** (not build) so the DB lives on a
mounted volume and persists across restarts.

```bash
cd services/mission-control
docker build -t hivestar-mission-control .
docker run --rm -p 9000:9000 -v mc-data:/data hivestar-mission-control
```

Then:

```bash
# Ingest a log (as service #1 would):
curl -X POST http://localhost:9000/ingest \
  --data '{"ts":"2026-07-16T08:00:00.000Z","type":"heartbeat","sat_id":"HIVE-01"}'
# View the dashboard:
open http://localhost:9000/
```

**SQLite is a single file** at `/data/db.sqlite3` (configurable via
`SQLITE_PATH`). Mount a volume at `/data` to persist it; without a volume the
data is lost when the container is removed.

## Run locally (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 9000
```

## Test

The one required end-to-end test (write → store → display) is a Django
`TestCase` in [`logs/tests.py`](logs/tests.py):

```bash
cd services/mission-control
python manage.py test
```

## Configuration

| Env var                 | Default                        | Purpose                                   |
| ----------------------- | ------------------------------ | ----------------------------------------- |
| `SQLITE_PATH`           | `<project>/db.sqlite3`         | SQLite file location (`/data/db.sqlite3` in Docker). |
| `DJANGO_ALLOWED_HOSTS`  | `*`                            | Comma-separated allowed hosts.            |
| `DJANGO_DEBUG`          | `0`                            | Set to `1` to enable debug mode.          |
| `DJANGO_SECRET_KEY`     | insecure scaffolding default   | Override in any real deployment.          |
