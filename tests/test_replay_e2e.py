"""End-to-end tests for the Log Replay Service.

These exercise both endpoints against a real in-process HTTP receiver (see
``receiver.py``). The replay POSTs travel over a real socket; only ``/health``
and ``/replay`` are driven via the Flask test client.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest

from app import create_app
from config import Config
from receiver import RunningReceiver

# A small, self-contained fixture log (independent of the bundled sample).
FIXTURE_EVENTS = [
    {"ts": "2026-07-16T08:00:00.000Z", "type": "heartbeat", "seq": 1},
    {"ts": "2026-07-16T08:00:01.000Z", "type": "telemetry", "battery_pct": 90.1},
    {"ts": "2026-07-16T08:00:02.500Z", "type": "task_announced", "task_id": "T-1"},
    {"ts": "2026-07-16T08:00:03.000Z", "type": "bid_accepted", "task_id": "T-1"},
    {"ts": "2026-07-16T08:00:04.250Z", "type": "task_completed", "task_id": "T-1"},
]


@pytest.fixture
def log_file(tmp_path: Path) -> str:
    path = tmp_path / "fixture.jsonl"
    lines = [json.dumps(event) for event in FIXTURE_EVENTS]
    # Include a blank line to prove blank lines are skipped.
    path.write_text("\n".join(lines) + "\n\n", encoding="utf-8")
    return str(path)


def _make_client(target_url: str, log_file: str):
    cfg = Config(
        log_file=log_file,
        target_url=target_url,
        replay_speed=100_000.0,
        post_timeout=5.0,
        max_step_sleep=0.0,
    )
    return create_app(cfg).test_client()


def _wait_for_state(client, target: str, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    snapshot = client.get("/health").get_json()["replay"]
    while snapshot["state"] != target and time.time() < deadline:
        time.sleep(0.01)
        snapshot = client.get("/health").get_json()["replay"]
    return snapshot


def test_health_while_idle(log_file: str) -> None:
    with RunningReceiver() as receiver:
        client = _make_client(receiver.url, log_file)
        response = client.get("/health")
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "ok"
        assert body["replay"]["state"] == "idle"
        assert body["replay"]["total"] == 0
        assert body["replay"]["error"] is None


def test_replay_delivers_all_events_in_order(log_file: str) -> None:
    with RunningReceiver() as receiver:
        client = _make_client(receiver.url, log_file)

        start = client.post("/replay")
        assert start.status_code == 202
        assert start.get_json()["state"] == "running"

        snapshot = _wait_for_state(client, "done")
        assert snapshot["state"] == "done"
        assert snapshot["total"] == len(FIXTURE_EVENTS)
        assert snapshot["posted"] == len(FIXTURE_EVENTS)
        assert snapshot["failures"] == 0
        assert snapshot["started_at"] is not None

        assert receiver.bodies() == FIXTURE_EVENTS


def test_second_replay_while_running_returns_409(log_file: str) -> None:
    gate = threading.Event()
    with RunningReceiver(gate=gate) as receiver:
        client = _make_client(receiver.url, log_file)

        first = client.post("/replay")
        assert first.status_code == 202

        # The first POST is blocked in the gated receiver, so the run stays
        # "running" while we attempt a second start.
        running = _wait_for_state(client, "running")
        assert running["state"] == "running"

        second = client.post("/replay")
        assert second.status_code == 409
        assert second.get_json()["state"] == "running"

        # Release the receiver and let the run finish cleanly.
        gate.set()
        done = _wait_for_state(client, "done")
        assert done["state"] == "done"
        assert receiver.bodies() == FIXTURE_EVENTS


def test_failure_path_counts_failures_and_still_completes(log_file: str) -> None:
    with RunningReceiver(status=500) as receiver:
        client = _make_client(receiver.url, log_file)

        assert client.post("/replay").status_code == 202

        snapshot = _wait_for_state(client, "done")
        assert snapshot["state"] == "done"
        assert snapshot["total"] == len(FIXTURE_EVENTS)
        assert snapshot["failures"] == len(FIXTURE_EVENTS)
        assert snapshot["posted"] == 0
        # Every event still reached the receiver even though it returned 500.
        assert receiver.bodies() == FIXTURE_EVENTS
