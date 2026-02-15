"""Health check router."""

from fastapi import APIRouter

from database import db
from services.ollama_client import OllamaClient

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    """Health check endpoint."""
    # Check database connectivity
    try:
        conn = db.get_connection()
        cursor = conn.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check Ollama availability
    ollama_client = OllamaClient()
    try:
        is_available = await ollama_client.is_available()
        ollama_status = "ok" if is_available else "unavailable"
    except Exception as e:
        ollama_status = f"error: {str(e)}"
    finally:
        await ollama_client.close()

    return {
        "status": "ok",
        "database": db_status,
        "ollama": ollama_status,
    }
