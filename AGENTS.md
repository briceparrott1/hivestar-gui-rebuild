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
