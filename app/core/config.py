from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Production application settings managed via Pydantic Settings."""

    APP_NAME: str = "Autonomous Code & Analysis Workspace"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Gemini LLM Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    # Comma-separated models tried in order when the primary model is overloaded
    # (503), rate-limited (429), times out (504) or has been retired (404).
    GEMINI_FALLBACK_MODELS: str = "gemini-3.5-flash-lite,gemini-3.1-flash-lite"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_TIMEOUT_SECONDS: int = 60
    GEMINI_MAX_RETRIES: int = 2  # retries per model on transient errors

    @property
    def gemini_model_chain(self) -> list[str]:
        chain = [self.GEMINI_MODEL] + [
            m.strip() for m in self.GEMINI_FALLBACK_MODELS.split(",") if m.strip()
        ]
        return list(dict.fromkeys(chain))  # dedupe, keep order

    # Docker Sandbox Configuration
    DOCKER_SANDBOX_IMAGE: str = "python:3.11-slim"
    EXECUTION_TIMEOUT_SECONDS: int = 30
    MAX_CONTAINER_MEMORY: str = "512m"  # Hard memory limit to prevent OOM on host
    CPU_QUOTA_MICROS: int = 100000       # 1 CPU core equivalent
    SANDBOX_NETWORK_MODE: str = "none"   # Prevent SSRF and network access unless whitelisted

    # Guardrails
    MAX_ITERATIONS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

