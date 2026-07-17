# Log Replay Service

Service #1 of `hivestar-gui-rebuild`. Reads a JSON-lines telemetry log and
replays each event as an individual HTTP `POST` to a configured endpoint, paced
to the original timeline.

## Endpoints

| Method | Path      | Behavior                                                                                     |
| ------ | --------- | -------------------------------------------------------------------------------------------- |
| `GET`  | `/health` | `200` with `{"status": "ok", "replay": <snapshot>}`. Works before any replay has run.        |
| `POST` | `/replay` | Starts a replay in a background thread; `202` + initial snapshot. `409` if one is running.    |

There is deliberately no separate status endpoint — progress is observed by
polling `/health`. The `<snapshot>` fields are:

```json
{
  "state": "idle | running | done | error",
  "total": 0,
  "posted": 0,
  "failures": 0,
  "started_at": null,
  "error": null
}
```

Each event that gets a `2xx` increments `posted`; a non-`2xx` response or any
request exception/timeout increments `failures` and the loop continues
(continue-on-error). The run always reaches a terminal state.

## Configuration (environment variables)

| Variable         | Default                        | Meaning                                   |
| ---------------- | ------------------------------ | ----------------------------------------- |
| `LOG_FILE`       | `data/sample_logs.jsonl`       | Path to the JSONL log to replay.          |
| `TARGET_URL`     | `http://localhost:9000/ingest` | Endpoint each event is POSTed to.         |
| `REPLAY_SPEED`   | `60`                           | Speed factor; higher replays faster.      |
| `POST_TIMEOUT`   | `5`                            | Per-request timeout in seconds.           |
| `MAX_STEP_SLEEP` | `5`                            | Cap (seconds) on any single inter-event pause. |

Pacing: `delay = min((ts_i − ts_{i-1}) / REPLAY_SPEED, MAX_STEP_SLEEP)`, slept
before each POST. The first event posts immediately. `ts` is ISO-8601 UTC, e.g.
`"2026-07-16T08:00:47.963Z"`.

## Single-worker constraint

Replay state lives in **process memory** (a single in-process `ReplayState`
guarded by a lock). The service **must run as one worker** — multiple workers
would each have their own state, so `/health` and the one-replay-at-a-time
guard would be inconsistent. Do not scale it with `--workers > 1`.

## Running

```bash
cd services/log-replay
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# single worker only
flask --app app run --port 8000
# or: gunicorn --workers 1 app:app
```

Then:

```bash
curl localhost:8000/health
curl -X POST localhost:8000/replay
```

## Tests

End-to-end tests (`tests/`) drive both endpoints against a real in-process WSGI
receiver — the replay POSTs travel over a real socket, nothing is mocked.

```bash
pip install -r requirements-dev.txt
pytest tests/            # run from the repo root
```
