"""Settings and connection testing router."""

from typing import Annotated

from fastapi import APIRouter, Depends

from exceptions import JiraConnectionError, SlackAPIError
from models.api import (
    JiraConnectionTestRequest,
    SlackConnectionTestRequest,
    TestConnectionResponse,
)
from security.auth import AuthUser, require_roles_dependency
from services.jira_client import JiraClient
from services.slack_client import SlackClient

router = APIRouter(prefix="/settings", tags=["settings"])
AdminUser = Annotated[AuthUser, Depends(require_roles_dependency({"admin"}))]


@router.post("/test-jira")
async def test_jira_connection(
    request: JiraConnectionTestRequest,
    current_user: AdminUser,
) -> TestConnectionResponse:
    """Test Jira connection with provided credentials."""
    del current_user
    client = JiraClient(
        url=request.url,
        email=request.email,
        api_token=request.api_token,
    )

    try:
        server_info = await client.test_connection()
        return TestConnectionResponse(
            success=True,
            message="Successfully connected to Jira",
            details={
                "url": request.url,
                "email": request.email,
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
    request: SlackConnectionTestRequest,
    current_user: AdminUser,
) -> TestConnectionResponse:
    """Test Slack connection with provided bot token."""
    del current_user
    client = SlackClient(bot_token=request.bot_token)

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
