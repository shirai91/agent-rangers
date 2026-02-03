"""Application configuration using Pydantic settings."""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    PROJECT_NAME: str = "Agent Rangers API"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://agent_rangers:agent_rangers_dev@localhost:5432/agent_rangers"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_MESSAGE_QUEUE_SIZE: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
