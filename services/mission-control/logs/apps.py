"""App configuration for the ``logs`` app."""

from __future__ import annotations

from django.apps import AppConfig


class LogsConfig(AppConfig):
    """Configuration for the mission-control ``logs`` app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "logs"
