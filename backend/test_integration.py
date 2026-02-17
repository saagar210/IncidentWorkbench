"""Integration tests for Phase 1."""

import asyncio
import json
import pytest
from database import Database
from services.normalizer import IncidentNormalizer
from models.incident import IncidentSource, Severity

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_full_pipeline():
    """Test full ingestion pipeline with database."""
    # Initialize database
    db = Database()
    db.run_migrations()

    conn = db.get_connection()

    try:
        # Clear incidents table
        conn.execute("DELETE FROM incidents")
        conn.commit()

        # Create sample Jira issues
        jira_issues = [
            {
                "key": "OPS-101",
                "fields": {
                    "summary": "Production outage in us-east-1",
                    "description": "Database connection pool exhausted",
                    "created": "2024-01-15T10:30:00.000+0000",
                    "resolutiondate": "2024-01-15T12:45:00.000+0000",
                    "priority": {"name": "Highest"},
                    "status": {"name": "Resolved"},
                    "assignee": {"displayName": "John Doe"},
                    "labels": ["production", "database"],
                    "project": {"key": "OPS"},
                },
            },
            {
                "key": "OPS-102",
                "fields": {
                    "summary": "API rate limiting issue",
                    "description": "Users experiencing 429 errors",
                    "created": "2024-01-16T14:20:00.000+0000",
                    "resolutiondate": None,
                    "priority": {"name": "High"},
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Jane Smith"},
                    "labels": ["api", "performance"],
                    "project": {"key": "OPS"},
                },
            },
        ]

        # Normalize and insert Jira issues
        for issue in jira_issues:
            incident = IncidentNormalizer.normalize_jira_issue(issue)

            conn.execute(
                """
                INSERT INTO incidents (
                    external_id, source, severity, title, description,
                    occurred_at, resolved_at, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.external_id,
                    incident.source.value,
                    incident.severity.value,
                    incident.title,
                    incident.description,
                    incident.occurred_at.isoformat(),
                    incident.resolved_at.isoformat() if incident.resolved_at else None,
                    json.dumps(incident.raw_data),
                ),
            )

        conn.commit()

        # Create sample Slack threads
        slack_threads = [
            {
                "channel": "C12345",
                "messages": [
                    {
                        "text": "SEV2: Payment processing degraded",
                        "ts": "1705315800.123456",
                        "user": "U12345",
                    },
                    {
                        "text": "Investigating with payment provider",
                        "ts": "1705316100.123456",
                        "user": "U12345",
                    },
                    {
                        "text": "Issue resolved after provider fix",
                        "ts": "1705319700.123456",
                        "user": "U12345",
                    },
                ],
            }
        ]

        # Normalize and insert Slack threads
        for thread in slack_threads:
            incident = IncidentNormalizer.normalize_slack_thread(
                messages=thread["messages"],
                channel=thread["channel"],
                source=IncidentSource.SLACK,
            )

            conn.execute(
                """
                INSERT INTO incidents (
                    external_id, source, severity, title, description,
                    occurred_at, resolved_at, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.external_id,
                    incident.source.value,
                    incident.severity.value,
                    incident.title,
                    incident.description,
                    incident.occurred_at.isoformat(),
                    incident.resolved_at.isoformat() if incident.resolved_at else None,
                    json.dumps(incident.raw_data),
                ),
            )

        conn.commit()

        # Query all incidents
        cursor = conn.execute("SELECT COUNT(*) as count FROM incidents")
        count = cursor.fetchone()["count"]
        print(f"✓ Inserted {count} incidents into database")

        # Query by source
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM incidents WHERE source = ?",
            (IncidentSource.JIRA.value,),
        )
        jira_count = cursor.fetchone()["count"]
        print(f"✓ Found {jira_count} Jira incidents")

        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM incidents WHERE source = ?",
            (IncidentSource.SLACK.value,),
        )
        slack_count = cursor.fetchone()["count"]
        print(f"✓ Found {slack_count} Slack incidents")

        # Query by severity
        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM incidents WHERE severity = ?",
            (Severity.SEV1.value,),
        )
        sev1_count = cursor.fetchone()["count"]
        print(f"✓ Found {sev1_count} SEV1 incidents")

        # Test duplicate handling
        duplicate_issue = jira_issues[0]
        incident = IncidentNormalizer.normalize_jira_issue(duplicate_issue)

        conn.execute(
            """
            INSERT INTO incidents (
                external_id, source, severity, title, description,
                occurred_at, resolved_at, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id, source) DO NOTHING
            """,
            (
                incident.external_id,
                incident.source.value,
                incident.severity.value,
                incident.title,
                incident.description,
                incident.occurred_at.isoformat(),
                incident.resolved_at.isoformat() if incident.resolved_at else None,
                json.dumps(incident.raw_data),
            ),
        )
        conn.commit()

        # Verify count hasn't changed
        cursor = conn.execute("SELECT COUNT(*) as count FROM incidents")
        new_count = cursor.fetchone()["count"]
        assert new_count == count, "Duplicate was inserted!"
        print("✓ Duplicate prevention works correctly")

        # Clean up
        conn.execute("DELETE FROM incidents")
        conn.commit()

        print("\n✓ All integration tests passed!")

    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
