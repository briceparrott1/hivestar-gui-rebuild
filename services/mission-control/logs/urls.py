"""URL routes for the mission-control ``logs`` app."""

from __future__ import annotations

from django.urls import path

from . import views

# ``ingest`` has no trailing slash so it matches service #1's default target
# URL (``http://localhost:9000/ingest``) exactly, with no APPEND_SLASH redirect.
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("ingest", views.ingest, name="ingest"),
]
