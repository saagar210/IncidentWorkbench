"""Incident ingestion router."""

import json
import sqlite3
from datetime import datetime, timedelta

from fastapi import APIRouter

from database import db
from exceptions import JiraConnectionError, JiraQueryError, SlackAPIError
from models.api import IngestResponse, JiraIngestRequest, SlackIngestRequest, SlackExportIngestRequest
from models.incident import IncidentSource
from services.jira_client import JiraClient
from services.normalizer import IncidentNormalizer
from services.slack_client import SlackClient

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/jira")
async def ingest_from_jira(request: JiraIngestRequest) -> IngestResponse:
    """Ingest incidents from Jira using JQL query."""
    errors = []
    ingested = 0
    updated = 0

    try:
        # Initialize Jira client
        client = JiraClient(
            url=request.url,
            email=request.email,
            api_token=request.api_token,
        )

        # Fetch issues
        issues = await client.search_issues(jql=request.jql)

        # Normalize and insert each issue
        conn = db.get_connection()
        try:
            for issue in issues:
                try:
                    incident = IncidentNormalizer.normalize_jira_issue(issue)

                    # Check if row exists before upsert to track inserts vs updates
                    check = conn.execute(
                        "SELECT id FROM incidents WHERE external_id = ? AND source = ?",
                        (incident.external_id, incident.source.value),
                    ).fetchone()
                    existed_before = check is not None

                    # Prepare insert query
                    cursor = conn.execute(
                        """
                        INSERT INTO incidents (
                            external_id, source, severity, title, description,
                            occurred_at, resolved_at, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(external_id, source) DO UPDATE SET
                            severity = excluded.severity,
                            title = excluded.title,
                            description = excluded.description,
                            resolved_at = excluded.resolved_at,
                            raw_data = excluded.raw_data
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

                    # Track whether this was an insert or update
                    if cursor.rowcount > 0:
                        if existed_before:
                            updated += 1
                        else:
                            ingested += 1

                except Exception as e:
                    errors.append(f"Failed to normalize issue {issue.get('key', 'unknown')}: {str(e)}")

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    except JiraConnectionError as e:
        errors.append(f"Connection error: {e.message}")
    except JiraQueryError as e:
        errors.append(f"Query error: {e.message}")
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")

    return IngestResponse(
        incidents_ingested=ingested,
        incidents_updated=updated,
        errors=errors,
    )


@router.post("/slack")
async def ingest_from_slack(request: SlackIngestRequest) -> IngestResponse:
    """Ingest incidents from Slack channel history."""
    errors = []
    ingested = 0
    updated = 0

    try:
        # Initialize Slack client
        client = SlackClient(bot_token=request.bot_token)

        # Calculate time range
        now = datetime.utcnow()
        oldest = (now - timedelta(days=request.days_back)).timestamp()
        latest = now.timestamp()

        # Fetch messages
        messages = await client.fetch_channel_messages(
            channel_id=request.channel_id,
            oldest=oldest,
            latest=latest,
        )

        # Group messages by thread
        threads = {}
        for msg in messages:
            thread_ts = msg.get("thread_ts", msg.get("ts"))
            if thread_ts not in threads:
                threads[thread_ts] = []
            threads[thread_ts].append(msg)

        # Normalize and insert each thread
        conn = db.get_connection()
        try:
            for thread_ts, thread_msgs in threads.items():
                try:
                    # Sort messages by timestamp
                    thread_msgs.sort(key=lambda m: float(m.get("ts", "0")))

                    incident = IncidentNormalizer.normalize_slack_thread(
                        messages=thread_msgs,
                        channel=request.channel_id,
                        source=IncidentSource.SLACK,
                    )

                    # Check if row exists before upsert to track inserts vs updates
                    check = conn.execute(
                        "SELECT id FROM incidents WHERE external_id = ? AND source = ?",
                        (incident.external_id, incident.source.value),
                    ).fetchone()
                    existed_before = check is not None

                    # Insert or update
                    cursor = conn.execute(
                        """
                        INSERT INTO incidents (
                            external_id, source, severity, title, description,
                            occurred_at, resolved_at, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(external_id, source) DO UPDATE SET
                            severity = excluded.severity,
                            title = excluded.title,
                            description = excluded.description,
                            resolved_at = excluded.resolved_at,
                            raw_data = excluded.raw_data
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

                    if cursor.rowcount > 0:
                        if existed_before:
                            updated += 1
                        else:
                            ingested += 1

                except Exception as e:
                    errors.append(f"Failed to normalize thread {thread_ts}: {str(e)}")

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    except SlackAPIError as e:
        errors.append(f"Slack API error: {e.message}")
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")

    return IngestResponse(
        incidents_ingested=ingested,
        incidents_updated=updated,
        errors=errors,
    )


@router.post("/slack-export")
async def ingest_from_slack_export(request: SlackExportIngestRequest) -> IngestResponse:
    """Ingest incidents from exported Slack JSON."""
    errors = []
    ingested = 0
    updated = 0

    try:
        # Load export data from either inline JSON or file path.
        if request.json_content is not None:
            export_data = request.json_content
        elif request.json_path is not None:
            with open(request.json_path, "r") as f:
                export_data = f.read()
        else:
            # Should be unreachable due request model validation.
            raise ValueError("Either json_content or json_path must be provided")

        # Parse export
        messages = SlackClient.parse_export(export_data)

        # Group by thread
        threads = {}
        for msg in messages:
            thread_ts = msg.get("thread_ts", msg.get("ts"))
            if thread_ts not in threads:
                threads[thread_ts] = []
            threads[thread_ts].append(msg)

        # Normalize and insert
        conn = db.get_connection()
        try:
            for thread_ts, thread_msgs in threads.items():
                try:
                    thread_msgs.sort(key=lambda m: float(m.get("ts", "0")))

                    incident = IncidentNormalizer.normalize_slack_thread(
                        messages=thread_msgs,
                        channel=request.channel_name,
                        source=IncidentSource.SLACK_EXPORT,
                    )

                    # Check if row exists before upsert to track inserts vs updates
                    check = conn.execute(
                        "SELECT id FROM incidents WHERE external_id = ? AND source = ?",
                        (incident.external_id, incident.source.value),
                    ).fetchone()
                    existed_before = check is not None

                    cursor = conn.execute(
                        """
                        INSERT INTO incidents (
                            external_id, source, severity, title, description,
                            occurred_at, resolved_at, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(external_id, source) DO UPDATE SET
                            severity = excluded.severity,
                            title = excluded.title,
                            description = excluded.description,
                            resolved_at = excluded.resolved_at,
                            raw_data = excluded.raw_data
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

                    if cursor.rowcount > 0:
                        if existed_before:
                            updated += 1
                        else:
                            ingested += 1

                except Exception as e:
                    errors.append(f"Failed to normalize thread {thread_ts}: {str(e)}")

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    except FileNotFoundError:
        errors.append(f"File not found: {request.json_path}")
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {str(e)}")
    except SlackAPIError as e:
        errors.append(f"Parse error: {e.message}")
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")

    return IngestResponse(
        incidents_ingested=ingested,
        incidents_updated=updated,
        errors=errors,
    )
