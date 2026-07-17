# hivestar-gui-rebuild

A multi-service project. Each service is a self-contained directory under
`services/<name>/` with its own Flask app factory (`create_app`), supporting
modules, `requirements.txt`, and `README.md`. Shared sample data lives in
`data/`, and pytest suites live in `tests/` at the repo root.

## Services

- [`services/log-replay`](services/log-replay/README.md) — service #1: a Flask
  service that replays a JSON-lines telemetry log as paced HTTP `POST`s.
  Endpoints: `GET /health` and `POST /replay`. Must run as a single worker.
- [`services/mission-control`](services/mission-control/README.md) — service #2:
  a Django + SQLite app that ingests, stores, and displays telemetry logs.
  Endpoints: `POST /ingest` (stores the raw body verbatim) and `GET /` (a
  server-rendered dashboard). Dockerized; models beyond `RawLog` are stubbed.

## Running tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r services/log-replay/requirements-dev.txt
pytest tests/                 # from the repo root
```

See [`AGENTS.md`](AGENTS.md) for project conventions and layout details.
