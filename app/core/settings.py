from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Changed to False for compatibility
        extra="ignore",
    )

    APP_NAME: str = "Stripe Idempotent Payments Demo"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="production")

    # API Configuration
    API_PREFIX: str = "/api/v1"
    API_KEY: str | None = Field(default=None)

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./stripe_demo.db")
    SQL_ECHO: bool = Field(default=False)

    # Stripe Configuration
    STRIPE_API_KEY: str = Field(default="sk_test_fake_key_for_demo_only")
    STRIPE_WEBHOOK_SECRET: str = Field(default="whsec_test_fake_secret_only")
    USE_STRIPE_REAL: bool = Field(
        default=False,
        description="Use real Stripe API (True) or mock for tests (False)"
    )

    @field_validator('API_KEY', mode='before')
    @classmethod
    def empty_str_to_none(cls, v: Any) -> str | None:
        """Convert empty string to None."""
        if v == "" or v is None:
            return None
        return v


settings = Settings()
