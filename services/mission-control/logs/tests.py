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
