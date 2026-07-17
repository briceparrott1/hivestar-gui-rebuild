"""Environment-driven configuration for the Log Replay Service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# services/log-replay/config.py -> services/log-replay -> services -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LOG_FILE = _REPO_ROOT / "data" / "sample_logs.jsonl"


@dataclass(frozen=True)
class Config:
    """Immutable runtime configuration for a replay."""

    log_file: str
    target_url: str
    replay_speed: float
    post_timeout: float
    max_step_sleep: float


def load_config() -> Config:
    """Build a :class:`Config` from environment variables, applying defaults."""
    return Config(
        log_file=os.environ.get("LOG_FILE", str(_DEFAULT_LOG_FILE)),
        target_url=os.environ.get("TARGET_URL", "http://localhost:9000/ingest"),
        replay_speed=float(os.environ.get("REPLAY_SPEED", "60")),
        post_timeout=float(os.environ.get("POST_TIMEOUT", "5")),
        max_step_sleep=float(os.environ.get("MAX_STEP_SLEEP", "5")),
    )
