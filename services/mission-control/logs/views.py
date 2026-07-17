"""Views for the mission-control ``logs`` app.

Three endpoints:

* ``POST /ingest`` — store the raw request body verbatim as a ``RawLog``.
* ``GET /`` — render the mission-control dashboard.
* ``GET /events?after=<id>`` — JSON feed of logs newer than ``after`` for the
  dashboard's live auto-refresh poller.
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import RawLog

# Cap on rows returned per ``/events`` poll, so a caller that has been offline
# for a while can't pull an unbounded page in one request.
EVENTS_PAGE_LIMIT = 200


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


@require_GET
def events(request: HttpRequest) -> JsonResponse:
    """Return logs newer than ``after`` as JSON for the dashboard poller.

    The dashboard's short-polling loop calls this with ``after`` set to the
    highest ``RawLog`` id it has already shown. Rows are returned oldest-first
    so the poller can prepend each in turn and keep the feed newest-first.

    Response shape::

        {"logs": [{"id", "received_at" (isoformat), "payload"}, ...],
         "latest_id": <max id returned, or ``after`` if none>}
    """
    try:
        after = int(request.GET.get("after", 0))
    except (TypeError, ValueError):
        after = 0

    rows = RawLog.objects.filter(id__gt=after).order_by("id")[:EVENTS_PAGE_LIMIT]
    logs = [
        {
            "id": row.id,
            "received_at": row.received_at.isoformat(),
            "payload": row.payload,
        }
        for row in rows
    ]
    latest_id = logs[-1]["id"] if logs else after
    return JsonResponse({"logs": logs, "latest_id": latest_id})
