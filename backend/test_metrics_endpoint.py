#!/usr/bin/env python3
"""
Test script for metrics endpoint
"""

import sqlite3
import sys
from datetime import datetime, timedelta

from database import db
from services.metrics import MetricsCalculator

# Ensure we have the database initialized
print("Initializing database...")
db.run_migrations()

# Insert test data if none exists
conn = db.get_connection()
cursor = conn.execute("SELECT COUNT(*) as count FROM incidents")
count = cursor.fetchone()["count"]

if count == 0:
    print("No incidents found. Creating sample data...")

    # Create sample incidents
    base_time = datetime.now() - timedelta(days=30)
    test_incidents = [
        (
            "INC-001",
            "jira",
            "SEV1",
            "Production outage",
            base_time,
            base_time + timedelta(hours=2),
            "alice",
        ),
        (
            "INC-002",
            "jira",
            "SEV2",
            "Database slow",
            base_time + timedelta(days=1),
            base_time + timedelta(days=1, hours=4),
            "bob",
        ),
        (
            "INC-003",
            "slack",
            "SEV3",
            "Minor issue",
            base_time + timedelta(days=2),
            base_time + timedelta(days=2, hours=1),
            "alice",
        ),
        (
            "INC-004",
            "jira",
            "SEV1",
            "Critical failure",
            base_time + timedelta(days=5),
            base_time + timedelta(days=5, hours=3),
            "charlie",
        ),
        (
            "INC-005",
            "slack",
            "SEV4",
            "Low priority",
            base_time + timedelta(days=7),
            base_time + timedelta(days=8),
            "bob",
        ),
    ]

    for ext_id, source, severity, title, occurred, resolved, assignee in test_incidents:
        conn.execute(
            """
            INSERT INTO incidents (
                external_id, source, severity, title, description,
                occurred_at, resolved_at, assignee, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ext_id,
                source,
                severity,
                title,
                title,
                occurred.isoformat(),
                resolved.isoformat(),
                assignee,
                "{}",
            ),
        )

    conn.commit()
    print(f"Created {len(test_incidents)} sample incidents")
else:
    print(f"Found {count} existing incidents")

# Test the metrics calculator
print("\nTesting MetricsCalculator...")
calc = MetricsCalculator(conn)
metrics = calc.calculate()

print("\n=== Metrics Results ===")
print(f"Total incidents: {metrics.total_incidents}")
print(
    f"SEV1: {metrics.sev1_count}, SEV2: {metrics.sev2_count}, SEV3: {metrics.sev3_count}, SEV4: {metrics.sev4_count}"
)
print(
    f"MTTR: {metrics.mean_resolution_hours:.2f}h" if metrics.mean_resolution_hours else "MTTR: N/A"
)
print(f"P50: {metrics.p50_resolution_hours:.2f}h" if metrics.p50_resolution_hours else "P50: N/A")
print(f"P90: {metrics.p90_resolution_hours:.2f}h" if metrics.p90_resolution_hours else "P90: N/A")
print(f"\nBy Severity: {metrics.by_severity}")
print(f"By Month: {metrics.by_month}")
print(f"By Assignee: {metrics.by_assignee}")

conn.close()

print("\n✓ Metrics endpoint test complete!")
print("✓ Backend is ready for Phase 3 visualization")
