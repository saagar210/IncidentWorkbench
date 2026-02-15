"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    db_path: Path = Path.home() / ".incident-workbench" / "incidents.db"
    ollama_url: str = "http://127.0.0.1:11434"

    model_config = {
        "env_prefix": "WORKBENCH_",
        "case_sensitive": False,
    }


settings = Settings()
