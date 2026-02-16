"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    db_path: Path = Path.home() / ".incident-workbench" / "incidents.db"
    ollama_url: str = "http://127.0.0.1:11434"
    webhook_secret: str = "dev-webhook-secret"
    webhook_max_attempts: int = 5
    auth_enabled: bool = True
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin-dev-change-me"

    model_config = {
        "env_prefix": "WORKBENCH_",
        "case_sensitive": False,
    }


settings = Settings()
