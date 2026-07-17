"""Root URL configuration for the mission-control project."""

from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("", include("logs.urls")),
]
