"""Metrics calculation service."""

import sqlite3
from collections import Counter
from datetime import datetime

from models.report import MetricsResult


class MetricsCalculator:
    """Service for calculating incident metrics."""

    def __init__(self, db_conn: sqlite3.Connection) -> None:
        self.db = db_conn

    def calculate(self, incident_ids: list[int] | None = None) -> MetricsResult:
        """
        Calculate all metrics for incidents.

        Args:
            incident_ids: Optional list of incident IDs to calculate metrics for.
                         If None, calculates for all incidents.

        Returns:
            MetricsResult with calculated metrics.
        """
        # Build query with optional filtering
        where_clause = ""
        params: tuple = ()
        if incident_ids:
            placeholders = ",".join("?" * len(incident_ids))
            where_clause = f"WHERE id IN ({placeholders})"
            params = tuple(incident_ids)

        cursor = self.db.execute(f"""
            SELECT
                id, severity, status, occurred_at, resolved_at,
                assignee, jira_project,
                CASE
                    WHEN resolved_at IS NOT NULL AND occurred_at IS NOT NULL
                    THEN (julianday(resolved_at) - julianday(occurred_at)) * 86400
                    ELSE NULL
                END as duration_seconds
            FROM incidents
            {where_clause}
        """, params)
        rows = cursor.fetchall()

        total = len(rows)

        # Calculate durations
        durations = [
            row["duration_seconds"]
            for row in rows
            if row["duration_seconds"] is not None
        ]

        # MTTR calculation (in hours)
        mttr = (sum(durations) / len(durations) / 3600) if durations else None

        # Percentiles
        durations_sorted = sorted(durations)
        p50 = None
        p90 = None
        if durations_sorted:
            # P50: use proper median calculation
            n = len(durations_sorted)
            if n % 2 == 0:
                p50 = (durations_sorted[n // 2 - 1] + durations_sorted[n // 2]) / 2 / 3600
            else:
                p50 = durations_sorted[n // 2] / 3600

            # P90: use proper percentile formula (nearest rank method)
            p90_rank = int(0.9 * n)
            # Clamp to valid index range (0 to n-1)
            p90_idx = min(p90_rank, n - 1)
            p90 = durations_sorted[p90_idx] / 3600

        # Breakdowns
        by_severity = self._count_by(rows, "severity")
        by_status = self._count_by(rows, "status")
        by_month = self._count_by_month(rows)
        by_assignee = self._count_by(rows, "assignee", top_n=10)
        by_project = self._count_by(rows, "jira_project")

        return MetricsResult(
            total_incidents=total,
            sev1_count=by_severity.get("SEV1", 0),
            sev2_count=by_severity.get("SEV2", 0),
            sev3_count=by_severity.get("SEV3", 0),
            sev4_count=by_severity.get("SEV4", 0),
            unknown_count=by_severity.get("UNKNOWN", 0),
            mean_resolution_hours=mttr,
            median_resolution_hours=p50,
            p50_resolution_hours=p50,
            p90_resolution_hours=p90,
            mttr_by_severity=self._calculate_mttr_by_severity(rows),
            by_severity=by_severity,
            by_status=by_status,
            by_month=by_month,
            by_assignee=by_assignee,
            by_project=by_project,
        )

    def _count_by(
        self,
        rows: list,
        field: str,
        top_n: int | None = None
    ) -> dict[str, int]:
        """Count occurrences of field values."""
        counts = Counter(row[field] for row in rows if row[field] is not None and row[field] != "")
        if top_n:
            return dict(counts.most_common(top_n))
        return dict(counts)

    def _count_by_month(self, rows: list) -> dict[str, int]:
        """Group incidents by month."""
        months = []
        for row in rows:
            if row["occurred_at"]:
                try:
                    # Parse occurred_at and extract YYYY-MM
                    dt = datetime.fromisoformat(row["occurred_at"].replace("Z", "+00:00"))
                    month = dt.strftime("%Y-%m")
                    months.append(month)
                except (ValueError, AttributeError):
                    pass
        return dict(Counter(months))

    def _calculate_mttr_by_severity(self, rows: list) -> dict[str, float]:
        """Calculate MTTR grouped by severity."""
        by_severity: dict[str, list[float]] = {}

        for row in rows:
            severity = row["severity"]
            duration = row["duration_seconds"]

            if severity and duration is not None:
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(duration)

        # Calculate mean for each severity
        result = {}
        for severity, durations in by_severity.items():
            result[severity] = sum(durations) / len(durations) / 3600

        return result
