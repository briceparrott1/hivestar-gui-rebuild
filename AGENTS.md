# Project agent memory

Project-intrinsic knowledge for `hivestar-gui-rebuild`. This is a multi-service
project; services live under `services/<name>/` and slot in beside each other.

## Layout convention

- Each service is a self-contained directory under `services/<name>/` with its
  own `app.py` (Flask **app factory** `create_app`), supporting modules,
  `requirements.txt`, and `README.md`.
- `data/` at the repo root holds shared/bundled sample data (e.g.
  `data/sample_logs.jsonl`).
- `tests/` at the repo root holds pytest suites. Because service directories can
  be hyphenated (not importable as packages), `tests/conftest.py` puts the
  relevant service directory on `sys.path` so its modules import as top-level
  modules (`from app import create_app`).

## Services

### services/log-replay (service #1)

Flask service that replays a JSON-lines telemetry log as paced HTTP POSTs.
Two endpoints only: `GET /health` and `POST /replay`. See its README for the
config vars and pacing formula.

**Single-worker constraint:** replay state lives in process memory
(`ReplayState`, guarded by a lock). Run it as exactly **one** worker
(`flask --app app run` or `gunicorn --workers 1 app:app`); multiple workers each
get their own state and break `/health` and the one-replay-at-a-time guard.

### services/mission-control (service #2)

Django + SQLite app that **ingests, stores, and displays** telemetry logs. It is
a standard Django project (`missioncontrol/` settings) with **one** app
(`logs/`). Unlike service #1's flat hyphenated-dir modules, this is a real Django
project run via `manage.py`, so its `__init__.py` files are required — do not
remove them.

Two endpoints:

- `POST /ingest` — stores the raw request body **verbatim** as a `RawLog` row
  (no parsing on this cut). CSRF-exempt (caller is service #1, a machine); empty
  body → `400`, otherwise `201`. Path has no trailing slash to match service #1's
  default `TARGET_URL` (`http://localhost:9000/ingest`).
- `GET /` — server-rendered dark dashboard listing stored logs newest-first,
  plus a stubbed "Missions" panel. No JS build step.

**Models are stubbed:** only `RawLog(payload, received_at)` is concrete and
migrated. `Satellite`, `Mission`, `Task`, `Event` and their relationships are a
commented placeholder in `logs/models.py` for a later parsing PR — not defined,
not migrated.

**Run via Docker** (migrates at container **start**, not build, so SQLite
persists on the mounted volume):

```bash
cd services/mission-control
docker build -t hivestar-mission-control .
docker run --rm -p 9000:9000 -v mc-data:/data hivestar-mission-control
```

**SQLite is a single file** at `/data/db.sqlite3` (env `SQLITE_PATH`); mount a
volume at `/data` to persist it. The one end-to-end test (write → store →
display) is a Django `TestCase`: `python manage.py test` from
`services/mission-control`. See its README for config vars.

## Running & testing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r services/log-replay/requirements-dev.txt
pytest tests/                 # from the repo root
```

## Conventions

- Python: PEP 8, formatted with Black (88 cols), linted with Ruff
  (`black --check .` and `ruff check .` must pass). Type hints on public
  functions; no unused imports.
