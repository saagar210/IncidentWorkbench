"""Incident data normalization from external sources."""

import re
from datetime import datetime

from models.incident import Incident, IncidentSource, Severity


class IncidentNormalizer:
    """Normalize incidents from Jira and Slack to common format."""

    # Jira priority to severity mapping
    JIRA_SEVERITY_MAP = {
        "Highest": Severity.SEV1,
        "High": Severity.SEV2,
        "Medium": Severity.SEV3,
        "Low": Severity.SEV4,
        "Lowest": Severity.SEV4,
    }

    @classmethod
    def normalize_jira_issue(cls, issue: dict) -> Incident:
        """Normalize a Jira issue to Incident model.

        Args:
            issue: Raw Jira issue dict from API

        Returns:
            Normalized Incident
        """
        fields = issue.get("fields", {})

        # Extract basic fields
        external_id = issue.get("key", "")
        title = fields.get("summary", "Untitled Incident")
        description = fields.get("description", "")

        # Parse timestamps (Jira format: "2024-01-15T10:30:00.000+0000")
        occurred_at_str = fields.get("created", "")
        occurred_at = cls._parse_jira_timestamp(occurred_at_str)

        resolved_at = None
        resolved_at_str = fields.get("resolutiondate")
        if resolved_at_str:
            resolved_at = cls._parse_jira_timestamp(resolved_at_str)

        # Map priority to severity
        priority = fields.get("priority", {})
        priority_name = priority.get("name", "Unknown") if priority else "Unknown"
        severity = cls.JIRA_SEVERITY_MAP.get(priority_name, Severity.UNKNOWN)

        # Store raw data for debugging
        raw_data = {
            "key": issue.get("key"),
            "status": fields.get("status", {}).get("name"),
            "assignee": cls._extract_assignee(fields.get("assignee")),
            "labels": fields.get("labels", []),
            "project": fields.get("project", {}).get("key"),
        }

        return Incident(
            external_id=external_id,
            source=IncidentSource.JIRA,
            severity=severity,
            title=title,
            description=description,
            occurred_at=occurred_at,
            resolved_at=resolved_at,
            raw_data=raw_data,
        )

    @classmethod
    def normalize_slack_thread(
        cls, messages: list[dict], channel: str, source: IncidentSource = IncidentSource.SLACK
    ) -> Incident:
        """Normalize a Slack thread to Incident model.

        Args:
            messages: List of Slack message dicts in thread (ordered chronologically)
            channel: Channel ID or name
            source: Either SLACK or SLACK_EXPORT

        Returns:
            Normalized Incident
        """
        if not messages:
            raise ValueError("Cannot normalize empty message list")

        # First message is parent, last is resolution (heuristic)
        first_msg = messages[0]
        last_msg = messages[-1]

        # Build title from first message (truncate to 200 chars)
        first_text = first_msg.get("text", "Untitled Incident")
        title = first_text[:200]

        # Concatenate all message text for description
        description_parts = []
        for msg in messages:
            text = msg.get("text", "")
            user = msg.get("user", "unknown")
            ts = msg.get("ts", "")
            description_parts.append(f"[{user} @ {ts}]: {text}")
        description = "\n\n".join(description_parts)

        # Parse timestamps
        occurred_at = cls._parse_slack_timestamp(first_msg.get("ts", "0"))
        # Only set resolved_at if there are multiple messages (indicating a resolution)
        resolved_at = (
            cls._parse_slack_timestamp(last_msg.get("ts", "0")) if len(messages) > 1 else None
        )

        # Infer severity from message text keywords
        combined_text = " ".join(msg.get("text", "") for msg in messages).lower()
        severity = cls._infer_slack_severity(combined_text)

        # External ID is the thread timestamp
        external_id = f"{channel}_{first_msg.get('ts', '0')}"

        raw_data = {
            "channel": channel,
            "thread_ts": first_msg.get("ts"),
            "message_count": len(messages),
            "users": list(set(msg.get("user", "unknown") for msg in messages)),
        }

        return Incident(
            external_id=external_id,
            source=source,
            severity=severity,
            title=title,
            description=description,
            occurred_at=occurred_at,
            resolved_at=resolved_at,
            raw_data=raw_data,
        )

    @staticmethod
    def _parse_jira_timestamp(ts_str: str) -> datetime:
        """Parse Jira ISO timestamp with timezone suffix.

        Handles formats like: "2024-01-15T10:30:00.000+0000"
        """
        if not ts_str:
            import logging

            logging.warning(
                "Empty timestamp string received from Jira, using current time as fallback"
            )
            return datetime.utcnow()

        try:
            # Remove timezone suffix and milliseconds for simplicity
            # Format: 2024-01-15T10:30:00.000+0000 -> 2024-01-15T10:30:00
            clean_ts = re.sub(r"\.\d{3}[+-]\d{4}$", "", ts_str)
            return datetime.fromisoformat(clean_ts)
        except (ValueError, AttributeError) as e:
            import logging

            logging.error(
                f"Failed to parse Jira timestamp '{ts_str}': {e}. Using current time as fallback."
            )
            return datetime.utcnow()

    @staticmethod
    def _parse_slack_timestamp(ts: str) -> datetime:
        """Parse Slack timestamp (Unix epoch with microseconds).

        Format: "1234567890.123456"
        """
        try:
            epoch = float(ts)
            return datetime.fromtimestamp(epoch)
        except (ValueError, TypeError) as e:
            import logging

            logging.error(
                f"Failed to parse Slack timestamp '{ts}': {e}. Using current time as fallback."
            )
            return datetime.utcnow()

    @staticmethod
    def _extract_assignee(assignee: dict | None) -> str:
        """Extract assignee display name from Jira assignee object."""
        if not assignee:
            return "Unassigned"
        return assignee.get("displayName", assignee.get("name", "Unknown"))

    @staticmethod
    def _infer_slack_severity(text: str) -> Severity:
        """Infer severity from Slack message text keywords.

        Args:
            text: Combined lowercase message text

        Returns:
            Inferred Severity
        """
        # SEV1 keywords
        if any(kw in text for kw in ["sev1", "p1", "critical", "outage", "down"]):
            return Severity.SEV1

        # SEV2 keywords
        if any(kw in text for kw in ["sev2", "p2", "major", "degraded", "urgent"]):
            return Severity.SEV2

        # SEV3 keywords
        if any(kw in text for kw in ["sev3", "p3", "minor", "issue"]):
            return Severity.SEV3

        # SEV4 keywords
        if any(kw in text for kw in ["sev4", "p4", "low", "question"]):
            return Severity.SEV4

        return Severity.UNKNOWN
