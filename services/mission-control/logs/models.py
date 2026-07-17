"""Data models for the mission-control ``logs`` app.

This scaffolding cut ships exactly **one** concrete, migrated table, ``RawLog``,
which stores each ingested request body verbatim. The richer, normalized schema
that a later PR will parse those raw logs into is sketched below as a commented
placeholder — it is intentionally **not** defined, **not** migrated, and **not**
populated on this cut.
"""

from __future__ import annotations

from django.db import models


class RawLog(models.Model):
    """A single ingested log line, stored exactly as received.

    ``/ingest`` decodes the raw request body to text and writes it here without
    any parsing. The dashboard renders these newest-first.
    """

    payload = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self) -> str:
        return f"RawLog(id={self.pk}, received_at={self.received_at:%Y-%m-%d %H:%M:%S})"


# ---------------------------------------------------------------------------
# STUBBED normalized schema — NOT IMPLEMENTED ON THIS CUT.
#
# A later PR will parse each RawLog.payload into the normalized mission-control
# model below. These classes are deliberately left commented out: they are not
# defined, not migrated, and not populated here. The shape is recorded now only
# to fix the intended relationships for that future work.
#
#   class Satellite(models.Model):
#       """A physical asset that emits telemetry (e.g. "HIVE-01")."""
#       sat_id = models.CharField(max_length=64, unique=True)  # e.g. "HIVE-01"
#       name = models.CharField(max_length=128, blank=True)
#
#   class Mission(models.Model):
#       """A campaign a satellite is flying; groups tasks and events."""
#       satellite = models.ForeignKey(
#           Satellite, on_delete=models.CASCADE, related_name="missions"
#       )
#       name = models.CharField(max_length=128)
#       started_at = models.DateTimeField(null=True, blank=True)
#
#   class Task(models.Model):
#       """A unit of work within a mission."""
#       mission = models.ForeignKey(
#           Mission, on_delete=models.CASCADE, related_name="tasks"
#       )
#       label = models.CharField(max_length=128)
#       status = models.CharField(max_length=32)  # queued|running|done|failed
#
#   class Event(models.Model):
#       """A parsed telemetry event, traceable back to its RawLog source.
#
#       This is where a raw log becomes structured: type/timestamp are pulled
#       out of the payload, and the originating RawLog is kept for provenance.
#       """
#       raw_log = models.ForeignKey(
#           RawLog, on_delete=models.SET_NULL, null=True, related_name="events"
#       )
#       satellite = models.ForeignKey(
#           Satellite, on_delete=models.CASCADE, related_name="events"
#       )
#       task = models.ForeignKey(
#           Task, on_delete=models.SET_NULL, null=True, related_name="events"
#       )
#       type = models.CharField(max_length=64)  # e.g. "heartbeat"
#       ts = models.DateTimeField()             # parsed from the payload
# ---------------------------------------------------------------------------
