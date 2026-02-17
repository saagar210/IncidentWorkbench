"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings

DEFAULT_WEBHOOK_SECRET = "dev-webhook-secret"


class Settings(BaseSettings):
    """Application settings."""

    app_env: str = "development"
    db_path: Path = Path.home() / ".incident-workbench" / "incidents.db"
    slack_export_dir: Path = Path.home() / ".incident-workbench" / "imports"
    ollama_url: str = "http://127.0.0.1:11434"
    webhook_secret: str = DEFAULT_WEBHOOK_SECRET
    webhook_max_attempts: int = 5
    auth_enabled: bool = True
    bootstrap_admin_username: str = ""
    bootstrap_admin_password: str = ""

    model_config = {
        "env_prefix": "WORKBENCH_",
        "case_sensitive": False,
    }

    def validate_security(self) -> None:
        """Enforce production-safe defaults for secrets and bootstrap credentials."""
        if self.app_env.lower() not in {"prod", "production"}:
            return

        if self.webhook_secret.strip() in {"", DEFAULT_WEBHOOK_SECRET}:
            raise ValueError(
                "WORKBENCH_WEBHOOK_SECRET must be configured in production "
                "(default secret is not allowed)."
            )

        if self.bootstrap_admin_password.strip():
            raise ValueError(
                "WORKBENCH_BOOTSTRAP_ADMIN_PASSWORD must be empty in production. "
                "Use managed identity provisioning instead."
            )


settings = Settings()
