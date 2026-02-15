"""Settings and connection testing router."""

from fastapi import APIRouter, HTTPException

from exceptions import JiraConnectionError, SlackAPIError
from models.api import TestConnectionResponse
from services.jira_client import JiraClient
from services.slack_client import SlackClient

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/test-jira")
async def test_jira_connection(
    url: str,
    email: str,
    api_token: str,
) -> TestConnectionResponse:
    """Test Jira connection with provided credentials."""
    client = JiraClient(url=url, email=email, api_token=api_token)

    try:
        server_info = await client.test_connection()
        return TestConnectionResponse(
            success=True,
            message="Successfully connected to Jira",
            details={
                "url": url,
                "email": email,
                "server_title": server_info.get("title", "Unknown"),
                "server_version": server_info.get("version", "Unknown"),
            },
        )
    except JiraConnectionError as e:
        return TestConnectionResponse(
            success=False,
            message=e.message,
            details=e.details,
        )
    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=f"Unexpected error: {str(e)}",
            details={},
        )


@router.post("/test-slack")
async def test_slack_connection(
    bot_token: str,
) -> TestConnectionResponse:
    """Test Slack connection with provided bot token."""
    client = SlackClient(bot_token=bot_token)

    try:
        auth_info = await client.test_connection()
        return TestConnectionResponse(
            success=True,
            message="Successfully connected to Slack",
            details={
                "team": auth_info.get("team", "Unknown"),
                "user": auth_info.get("user", "Unknown"),
            },
        )
    except SlackAPIError as e:
        return TestConnectionResponse(
            success=False,
            message=e.message,
            details=e.details,
        )
    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=f"Unexpected error: {str(e)}",
            details={},
        )
