"""Jira integration client."""

import httpx

from exceptions import JiraConnectionError, JiraQueryError


class JiraClient:
    """Client for Jira API integration."""

    def __init__(self, url: str, email: str, api_token: str) -> None:
        self.url = url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.auth = (email, api_token)

    async def test_connection(self) -> dict:
        """Test connection to Jira instance.

        Returns:
            Dict with server info (title and version)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.url}/rest/api/2/serverInfo",
                    auth=self.auth,
                )

                if response.status_code == 401:
                    raise JiraConnectionError(
                        "Authentication failed. Check your email and API token.",
                        details={"status_code": 401},
                    )

                if response.status_code == 404:
                    raise JiraConnectionError(
                        "Jira instance not found. Check your URL.",
                        details={"status_code": 404, "url": self.url},
                    )

                if response.status_code >= 400:
                    raise JiraConnectionError(
                        f"Jira API error: {response.status_code}",
                        details={"status_code": response.status_code, "body": response.text},
                    )

                data = response.json()
                return {
                    "title": data.get("serverTitle", "Unknown"),
                    "version": data.get("version", "Unknown"),
                }

        except httpx.TimeoutException:
            raise JiraConnectionError(
                "Connection timed out. Check your URL and network connection.",
                details={"url": self.url},
            )
        except httpx.ConnectError:
            raise JiraConnectionError(
                "Could not connect to Jira. Check your URL.",
                details={"url": self.url},
            )
        except JiraConnectionError:
            raise
        except Exception as e:
            raise JiraConnectionError(
                f"Unexpected error: {str(e)}",
                details={"error": str(e)},
            )

    async def search_issues(self, jql: str, max_results: int = 200) -> list[dict]:
        """Search for issues using JQL with pagination.

        Args:
            jql: JQL query string
            max_results: Maximum number of issues to return

        Returns:
            List of raw issue dicts from Jira API
        """
        issues = []
        start_at = 0
        batch_size = 50  # Jira's recommended page size

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    response = await client.get(
                        f"{self.url}/rest/api/2/search",
                        params={
                            "jql": jql,
                            "startAt": start_at,
                            "maxResults": batch_size,
                            "fields": "summary,description,status,priority,assignee,created,resolutiondate,labels,project",
                        },
                        auth=self.auth,
                    )

                    if response.status_code == 400:
                        raise JiraQueryError(
                            "Invalid JQL query.",
                            details={"jql": jql, "body": response.text},
                        )

                    if response.status_code == 401:
                        raise JiraConnectionError(
                            "Authentication failed.",
                            details={"status_code": 401},
                        )

                    if response.status_code >= 400:
                        raise JiraQueryError(
                            f"Jira search failed: {response.status_code}",
                            details={"status_code": response.status_code, "body": response.text},
                        )

                    data = response.json()
                    batch_issues = data.get("issues", [])
                    total = data.get("total", 0)

                    issues.extend(batch_issues)

                    # Check if we're done
                    start_at += len(batch_issues)
                    if start_at >= total or len(issues) >= max_results:
                        break

                    # Limit to max_results
                    if len(issues) >= max_results:
                        issues = issues[:max_results]
                        break

            return issues

        except httpx.TimeoutException:
            raise JiraQueryError(
                "Query timed out.",
                details={"jql": jql},
            )
        except (JiraConnectionError, JiraQueryError):
            raise
        except Exception as e:
            raise JiraQueryError(
                f"Unexpected error during search: {str(e)}",
                details={"error": str(e), "jql": jql},
            )
