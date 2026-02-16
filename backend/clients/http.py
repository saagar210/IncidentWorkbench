"""HTTP client defaults with timeout and bounded retries."""

from __future__ import annotations

import asyncio
import random

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(5.0, connect=1.0, read=4.0, write=4.0, pool=1.0)
DEFAULT_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)
RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


def new_async_client(*, timeout: httpx.Timeout | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout or DEFAULT_TIMEOUT, limits=DEFAULT_LIMITS)


async def request_with_retries(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.2,
    max_delay_seconds: float = 2.0,
    retry_statuses: set[int] | None = None,
    **kwargs,
) -> httpx.Response:
    """Send request with exponential backoff and jitter for transient failures."""

    retry_codes = retry_statuses or RETRYABLE_STATUS_CODES

    attempt = 1
    while True:
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code not in retry_codes or attempt >= max_attempts:
                return response
        except (httpx.TimeoutException, httpx.ConnectError):
            if attempt >= max_attempts:
                raise

        delay = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
        jitter = random.uniform(0.0, delay / 2)
        await asyncio.sleep(delay + jitter)
        attempt += 1
