"""Flask app factory and routes for the Log Replay Service."""

from __future__ import annotations

import threading
import time
from typing import Optional

from flask import Flask, jsonify

from config import Config, load_config
from replay import ReplayState, run_replay


def create_app(config: Optional[Config] = None) -> Flask:
    """Build the Flask application.

    Replay state lives in process memory, so the service must run as a single
    worker (see the README).
    """
    app = Flask(__name__)
    cfg = config or load_config()
    state = ReplayState()
    app.config["REPLAY_CONFIG"] = cfg
    app.config["REPLAY_STATE"] = state

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "replay": state.snapshot()}), 200

    @app.post("/replay")
    def replay():
        if not state.try_start(time.time()):
            # A replay is already running — do not start a second one.
            return jsonify(state.snapshot()), 409
        worker = threading.Thread(
            target=run_replay,
            args=(state, cfg),
            name="log-replay-worker",
            daemon=True,
        )
        worker.start()
        return jsonify(state.snapshot()), 202

    return app


# Module-level app for `flask --app app run` / gunicorn `app:app`.
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
