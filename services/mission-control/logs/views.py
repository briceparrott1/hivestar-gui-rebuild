"""Views for the mission-control ``logs`` app.

Two endpoints only:

* ``POST /ingest`` — store the raw request body verbatim as a ``RawLog``.
* ``GET /`` — render the mission-control dashboard.
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import RawLog


@csrf_exempt
@require_POST
def ingest(request: HttpRequest) -> HttpResponse:
    """Store the raw request body verbatim as a :class:`RawLog` row.

    The caller is service #1 (a machine, not a browser), so the endpoint is
    CSRF-exempt. An empty body is rejected with ``400``; anything else is
    decoded to text and stored without parsing, returning ``201``.
    """
    if not request.body:
        return HttpResponse("empty body", status=400, content_type="text/plain")

    payload = request.body.decode("utf-8", errors="replace")
    RawLog.objects.create(payload=payload)
    return HttpResponse("created", status=201, content_type="text/plain")


@require_GET
def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the mission-control dashboard with stored logs, newest first."""
    logs: QuerySet[RawLog] = RawLog.objects.all()
    return render(request, "logs/dashboard.html", {"logs": logs})
