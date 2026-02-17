"""Slack integration client."""

import asyncio
import json
from typing import Callable

import httpx

from clients.http import new_async_client, request_with_retries
from exceptions import SlackAPIError, SlackRateLimitError


class SlackClient:
    """Client for Slack API integration with dual-path design."""

    RATE_LIMIT_DELAY = 61  # seconds between requests
    MAX_ITEMS_PER_REQUEST = 15

    def __init__(self, bot_token: str, user_token: str | None = None) -> None:
        self.bot_token = bot_token
        self.user_token = user_token
        self.base_url = "https://slack.com/api"

    async def test_connection(self) -> dict:
        """Test connection to Slack with bot token.

        Returns:
            Dict with team and user info
        """
        try:
            async with new_async_client(timeout=httpx.Timeout(10.0)) as client:
                response = await request_with_retries(
                    client,
                    "POST",
                    f"{self.base_url}/auth.test",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    max_attempts=2,
                )

                data = response.json()

                if not data.get("ok"):
                    error = data.get("error", "unknown_error")
                    if error == "invalid_auth":
                        raise SlackAPIError(
                            "Invalid bot token. Check your credentials.",
                            details={"error": error},
                        )
                    elif error == "account_inactive":
                        raise SlackAPIError(
                            "Slack account is inactive.",
                            details={"error": error},
                        )
                    else:
                        raise SlackAPIError(
                            f"Slack API error: {error}",
                            details={"error": error},
                        )

                # Check rate limit headers
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    raise SlackRateLimitError(
                        "Rate limit exceeded.",
                        details={"retry_after": retry_after},
                    )

                return {
                    "team": data.get("team", "Unknown"),
                    "user": data.get("user", "Unknown"),
                }

        except httpx.TimeoutException:
            raise SlackAPIError(
                "Connection timed out. Check your network connection.",
                details={},
            )
        except httpx.ConnectError:
            raise SlackAPIError(
                "Could not connect to Slack API.",
                details={},
            )
        except (SlackAPIError, SlackRateLimitError):
            raise
        except Exception as e:
            raise SlackAPIError(
                f"Unexpected error: {str(e)}",
                details={"error": str(e)},
            )

    async def fetch_channel_messages(
        self,
        channel_id: str,
        oldest: float,
        latest: float,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict]:
        """Fetch messages from a channel with rate limiting.

        Args:
            channel_id: Slack channel ID
            oldest: Unix timestamp for oldest message
            latest: Unix timestamp for latest message
            progress_callback: Optional callback(fetched_count, total, delay_seconds)

        Returns:
            List of message dicts
        """
        messages = []
        cursor = None
        fetched_count = 0

        try:
            async with new_async_client(timeout=httpx.Timeout(30.0)) as client:
                while True:
                    params = {
                        "channel": channel_id,
                        "oldest": oldest,
                        "latest": latest,
                        "limit": self.MAX_ITEMS_PER_REQUEST,
                    }
                    if cursor:
                        params["cursor"] = cursor

                    response = await request_with_retries(
                        client,
                        "GET",
                        f"{self.base_url}/conversations.history",
                        params=params,
                        headers={"Authorization": f"Bearer {self.bot_token}"},
                        max_attempts=3,
                    )

                    data = response.json()

                    if not data.get("ok"):
                        error = data.get("error", "unknown_error")
                        raise SlackAPIError(
                            f"Failed to fetch messages: {error}",
                            details={"error": error, "channel": channel_id},
                        )

                    batch = data.get("messages", [])
                    messages.extend(batch)
                    fetched_count += len(batch)

                    # Call progress callback
                    if progress_callback:
                        progress_callback(fetched_count, -1, self.RATE_LIMIT_DELAY)

                    # Check for more pages
                    cursor = data.get("response_metadata", {}).get("next_cursor")
                    if not cursor:
                        break

                    # Rate limit delay between requests
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)

            return messages

        except (SlackAPIError, SlackRateLimitError):
            raise
        except Exception as e:
            raise SlackAPIError(
                f"Unexpected error fetching messages: {str(e)}",
                details={"error": str(e), "channel": channel_id},
            )

    async def fetch_thread_replies(self, channel_id: str, thread_ts: str) -> list[dict]:
        """Fetch replies in a thread.

        Args:
            channel_id: Slack channel ID
            thread_ts: Thread timestamp

        Returns:
            List of reply message dicts (includes parent message)
        """
        # Always sleep before calling to respect rate limits
        await asyncio.sleep(self.RATE_LIMIT_DELAY)

        try:
            async with new_async_client(timeout=httpx.Timeout(30.0)) as client:
                # User token required for thread replies
                token = self.user_token or self.bot_token

                response = await request_with_retries(
                    client,
                    "GET",
                    f"{self.base_url}/conversations.replies",
                    params={
                        "channel": channel_id,
                        "ts": thread_ts,
                    },
                    headers={"Authorization": f"Bearer {token}"},
                    max_attempts=3,
                )

                data = response.json()

                if not data.get("ok"):
                    error = data.get("error", "unknown_error")
                    raise SlackAPIError(
                        f"Failed to fetch thread replies: {error}",
                        details={"error": error, "thread_ts": thread_ts},
                    )

                return data.get("messages", [])

        except (SlackAPIError, SlackRateLimitError):
            raise
        except Exception as e:
            raise SlackAPIError(
                f"Unexpected error fetching thread: {str(e)}",
                details={"error": str(e), "thread_ts": thread_ts},
            )

    @staticmethod
    def parse_export(export_json: str | list | dict) -> list[dict]:
        """Parse Slack workspace export JSON.

        Args:
            export_json: JSON string or parsed dict/list from Slack export

        Returns:
            Flat list of message dicts
        """
        try:
            # Handle string input
            if isinstance(export_json, str):
                data = json.loads(export_json)
            else:
                data = export_json

            # Handle list format (array of messages)
            if isinstance(data, list):
                return data

            # Handle dict format (object with messages array)
            if isinstance(data, dict):
                if "messages" in data:
                    return data["messages"]
                # If dict doesn't have messages key, assume it's a single message
                return [data]

            return []

        except json.JSONDecodeError as e:
            raise SlackAPIError(
                "Invalid JSON format in export.",
                details={"error": str(e)},
            )
        except Exception as e:
            raise SlackAPIError(
                f"Failed to parse export: {str(e)}",
                details={"error": str(e)},
            )
