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
    GEMINI_TEMPERATURE: float = 0.2

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

