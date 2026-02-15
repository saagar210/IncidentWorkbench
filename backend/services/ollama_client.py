"""Ollama integration client."""

import httpx

from config import settings
from exceptions import OllamaModelNotFoundError, OllamaUnavailableError


class OllamaClient:
    """Client for Ollama local LLM integration."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_url).rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

    async def embed_batch(self, texts: list[str], model: str = "nomic-embed-text") -> list[list[float]]:
        """POST /api/embed with batch input. Returns list of 768-dim vectors."""
        try:
            resp = await self.client.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": texts}
            )
            resp.raise_for_status()
            return resp.json()["embeddings"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model}' not found. Pull it with: ollama pull {model}",
                    details={"model": model}
                )
            raise OllamaUnavailableError(
                f"Ollama API error: {e}",
                details={"status_code": e.response.status_code}
            )
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            raise OllamaUnavailableError(
                "Could not connect to Ollama. Is it running?",
                details={"url": self.base_url, "error": str(e)}
            )

    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2",
        format_schema: dict | None = None
    ) -> str:
        """POST /api/generate with optional structured output."""
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if format_schema:
            payload["format"] = format_schema

        try:
            resp = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=180.0
            )
            resp.raise_for_status()
            return resp.json()["response"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model}' not found. Pull it with: ollama pull {model}",
                    details={"model": model}
                )
            raise OllamaUnavailableError(
                f"Ollama API error: {e}",
                details={"status_code": e.response.status_code}
            )
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            raise OllamaUnavailableError(
                "Could not connect to Ollama. Is it running?",
                details={"url": self.base_url, "error": str(e)}
            )

    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            resp = await self.client.get(f"{self.base_url}/api/version", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Get list of pulled models."""
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
