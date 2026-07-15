"""
Application configuration — loaded from environment / .env file.
All secrets come from environment variables; nothing is hardcoded.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Azure OpenAI ──────────────────────────────────────────────
    azure_openai_endpoint: str = Field(default="")
    azure_openai_api_key: str = Field(default="")
    azure_openai_deployment: str = Field(default="gpt-4o-mini")
    azure_openai_api_version: str = Field(default="2024-02-01")

    # ── Azure AI Search ───────────────────────────────────────────
    azure_search_endpoint: str = Field(default="")
    azure_search_api_key: str = Field(default="")
    azure_search_index_name: str = Field(default="helpdesk-kb")

    # ── Application Settings ──────────────────────────────────────
    confidence_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    low_confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    max_retrieval_chunks: int = Field(default=5, ge=1, le=20)
    max_input_chars: int = Field(default=2000, ge=50, le=10000)
    max_output_tokens: int = Field(default=600, ge=50, le=4096)
    request_timeout_seconds: float = Field(default=15.0, ge=1.0)
    environment: str = Field(default="development")

    # ── Security ──────────────────────────────────────────────────
    session_secret_key: str = Field(default="changeme-use-32-random-chars-please!")
    rate_limit_per_session: int = Field(default=20, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=10)
    rate_limit_per_ip: int = Field(default=100, ge=1)
    rate_limit_ip_window_seconds: int = Field(default=600, ge=30)

    # ── Mock Mode ─────────────────────────────────────────────────
    mock_mode: bool = Field(default=False)
    kb_path: Path = Field(default=Path("../kb"))

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    audit_log_path: Path = Field(default=Path("./logs/audit.jsonl"))
    app_log_path: Path = Field(default=Path("./logs/app.jsonl"))

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def azure_configured(self) -> bool:
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_search_endpoint
            and self.azure_search_api_key
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance (singleton)."""
    return Settings()
