"""WSGI entrypoint for the mission-control service.

Served by gunicorn as ``missioncontrol.wsgi:application`` (see the Dockerfile).
"""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missioncontrol.settings")

application = get_wsgi_application()
