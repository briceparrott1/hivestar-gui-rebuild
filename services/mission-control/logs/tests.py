"""End-to-end test for the mission-control ``logs`` app.

Proves the one required path: write (POST /ingest) -> store (RawLog row) ->
display (GET / shows the stored string).
"""

from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from .models import RawLog

SAMPLE_LOG = '{"ts":"2026-07-16T08:00:00.000Z","type":"heartbeat","sat_id":"HIVE-01"}'


class IngestToDisplayTests(TestCase):
    """Write -> store -> display, end to end, via the test client."""

    def test_ingest_stores_and_dashboard_displays(self) -> None:
        # 1. Write: POST the raw log to /ingest.
        response = self.client.post(
            reverse("ingest"),
            data=SAMPLE_LOG,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        # Store: exactly one row exists, holding the payload verbatim.
        self.assertEqual(RawLog.objects.count(), 1)
        self.assertEqual(RawLog.objects.get().payload, SAMPLE_LOG)

        # 2. Display: the dashboard renders that exact string.
        page = self.client.get(reverse("dashboard"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "HIVE-01")

    def test_empty_body_is_rejected(self) -> None:
        response = self.client.post(
            reverse("ingest"),
            data="",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RawLog.objects.count(), 0)


class EventsEndpointTests(TestCase):
    """The ``/events`` JSON feed that powers the dashboard's live poller."""

    def test_after_zero_returns_all_ascending(self) -> None:
        first = RawLog.objects.create(payload='{"n":1}')
        second = RawLog.objects.create(payload='{"n":2}')

        response = self.client.get(reverse("events"), {"after": 0})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        ids = [row["id"] for row in data["logs"]]
        self.assertEqual(ids, [first.id, second.id])  # ascending
        self.assertEqual(data["latest_id"], second.id)
        # Each row carries the fields the poller renders.
        self.assertEqual(data["logs"][0]["payload"], '{"n":1}')
        self.assertIn("received_at", data["logs"][0])

    def test_after_max_returns_empty_and_echoes_after(self) -> None:
        RawLog.objects.create(payload='{"n":1}')
        max_id = RawLog.objects.create(payload='{"n":2}').id

        response = self.client.get(reverse("events"), {"after": max_id})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["logs"], [])
        self.assertEqual(data["latest_id"], max_id)

    def test_invalid_after_falls_back_to_zero(self) -> None:
        RawLog.objects.create(payload='{"n":1}')

        response = self.client.get(reverse("events"), {"after": "not-an-int"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["logs"]), 1)


class LivePathTests(TestCase):
    """A new ingest surfaces through ``/events`` without a page reload."""

    def test_new_ingest_surfaces_to_poller(self) -> None:
        RawLog.objects.create(payload='{"seed":true}')
        prev_max = RawLog.objects.order_by("-id").first().id

        response = self.client.post(
            reverse("ingest"),
            data=SAMPLE_LOG,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        data = self.client.get(reverse("events"), {"after": prev_max}).json()
        self.assertEqual(len(data["logs"]), 1)
        self.assertEqual(data["logs"][0]["payload"], SAMPLE_LOG)
        self.assertEqual(data["latest_id"], data["logs"][0]["id"])
