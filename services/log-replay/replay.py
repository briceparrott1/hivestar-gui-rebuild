"""Thread-safe replay state and the background replay engine."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

import requests

from config import Config


class ReplayState:
    """Shared, thread-safe view of a replay's progress.

    The background worker mutates the counters and terminal state; ``/health``
    reads a consistent snapshot. Every mutation and read is guarded by a single
    lock.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = "idle"
        self._total = 0
        self._posted = 0
        self._failures = 0
        self._started_at: Optional[float] = None
        self._error: Optional[str] = None

    def try_start(self, started_at: float) -> bool:
        """Atomically transition ``idle``/terminal -> ``running``.

        Returns ``True`` only for the caller that won the transition; a caller
        that finds a replay already ``running`` gets ``False`` and must not
        start a second worker.
        """
        with self._lock:
            if self._state == "running":
                return False
            self._state = "running"
            self._total = 0
            self._posted = 0
            self._failures = 0
            self._started_at = started_at
            self._error = None
            return True

    def set_total(self, total: int) -> None:
        with self._lock:
            self._total = total

    def record_posted(self) -> None:
        with self._lock:
            self._posted += 1

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1

    def mark_done(self) -> None:
        with self._lock:
            self._state = "done"

    def mark_error(self, message: str) -> None:
        with self._lock:
            self._state = "error"
            self._error = message

    def snapshot(self) -> dict[str, Any]:
        """Return a consistent copy of the current state."""
        with self._lock:
            return {
                "state": self._state,
                "total": self._total,
                "posted": self._posted,
                "failures": self._failures,
                "started_at": self._started_at,
                "error": self._error,
            }


def parse_ts(value: str) -> float:
    """Parse an ISO-8601 UTC timestamp to epoch seconds.

    Accepts the trailing ``Z`` form (e.g. ``"2026-07-16T08:00:47.963Z"``) as
    well as explicit offsets. A naive timestamp is assumed to be UTC.
    """
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def load_events(log_file: str) -> list[dict[str, Any]]:
    """Load a JSON-lines log, skipping blank lines. One object per line."""
    events: list[dict[str, Any]] = []
    with open(log_file, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            events.append(json.loads(stripped))
    return events


def _event_ts(event: dict[str, Any]) -> Optional[float]:
    raw = event.get("ts")
    if not isinstance(raw, str):
        return None
    try:
        return parse_ts(raw)
    except ValueError:
        return None


def _post_event(
    session: requests.Session,
    config: Config,
    state: ReplayState,
    event: dict[str, Any],
) -> None:
    """POST one event, counting the outcome. Never raises (continue-on-error)."""
    try:
        response = session.post(
            config.target_url, json=event, timeout=config.post_timeout
        )
    except requests.RequestException:
        state.record_failure()
        return
    if 200 <= response.status_code < 300:
        state.record_posted()
    else:
        state.record_failure()


def run_replay(state: ReplayState, config: Config) -> None:
    """Background worker: replay every event paced to the original timeline.

    The run always reaches a terminal state (``done`` on success, ``error`` on
    an unexpected failure). Per-event POST failures are counted and skipped.
    """
    try:
        events = load_events(config.log_file)
        state.set_total(len(events))
        session = requests.Session()
        prev_ts: Optional[float] = None
        for event in events:
            ts = _event_ts(event)
            if prev_ts is not None and ts is not None:
                delay = min((ts - prev_ts) / config.replay_speed, config.max_step_sleep)
                if delay > 0:
                    time.sleep(delay)
            if ts is not None:
                prev_ts = ts
            _post_event(session, config, state, event)
        state.mark_done()
    except Exception as exc:  # noqa: BLE001 - terminal safety net
        state.mark_error(str(exc))
