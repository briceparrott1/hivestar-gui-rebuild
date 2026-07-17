"""Pytest configuration: make the log-replay service importable.

The service lives under ``services/log-replay`` (a hyphenated directory that is
not a normal Python package), so its modules are imported as top-level modules
by putting the service directory on ``sys.path``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SERVICE_DIR = Path(__file__).resolve().parents[1] / "services" / "log-replay"
if str(_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICE_DIR))
