"""A tiny real WSGI receiver used by the end-to-end tests.

It runs in a background thread on an ephemeral port and appends every POSTed
JSON body to a list, so tests can assert exactly what the replay engine sent —
over a real HTTP path, not a mock.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Optional
from wsgiref.simple_server import WSGIRequestHandler, make_server

_REASONS = {200: "200 OK", 500: "500 Internal Server Error"}


class _QuietHandler(WSGIRequestHandler):
    """WSGIRequestHandler that does not spam stderr with request logs."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


class Receiver:
    """WSGI application that records received JSON bodies.

    :param status: HTTP status code to return for every request.
    :param gate: optional :class:`threading.Event`; when supplied, each request
        blocks until it is set. Used to hold a replay in the ``running`` state
        deterministically.
    """

    def __init__(self, status: int = 200, gate: Optional[threading.Event] = None):
        self.status = status
        self.gate = gate
        self.received: list[Any] = []
        self.lock = threading.Lock()

    def __call__(self, environ, start_response):
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        body = environ["wsgi.input"].read(length) if length else b""
        if self.gate is not None:
            self.gate.wait(timeout=10)
        payload = json.loads(body.decode("utf-8")) if body else None
        with self.lock:
            self.received.append(payload)
        start_response(_REASONS[self.status], [("Content-Type", "application/json")])
        return [b"{}"]

    def bodies(self) -> list[Any]:
        with self.lock:
            return list(self.received)


class RunningReceiver:
    """A :class:`Receiver` bound to a live server thread and its URL."""

    def __init__(self, status: int = 200, gate: Optional[threading.Event] = None):
        self.app = Receiver(status=status, gate=gate)
        self._server = make_server(
            "127.0.0.1", 0, self.app, handler_class=_QuietHandler
        )
        self.url = f"http://127.0.0.1:{self._server.server_port}/ingest"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> "RunningReceiver":
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def bodies(self) -> list[Any]:
        return self.app.bodies()
