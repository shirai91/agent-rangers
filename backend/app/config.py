"""Application configuration using Pydantic settings."""

import json
from typing import List, Union, Dict, Any, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    PROJECT_NAME: str = "Agent Rangers API"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = True

    # AI Provider Configuration
    # Provider mode: "oauth" (Claude Max), "api" (pay-as-you-go), "local" (Ollama), "auto"
    AI_PROVIDER_MODE: str = "auto"  # auto detects OAuth first, then API key, then local
    
    # Provider-specific settings
    ANTHROPIC_API_KEY: str = ""  # For API mode
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    
    # Claude CLI / OAuth settings
    CLAUDE_CONFIG_DIR: str = "/root/.claude"  # Where OAuth tokens are stored
    
    # Ollama settings (for local mode)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:32b"
    
    # Provider configuration JSON (advanced - overrides above settings)
    # Format: {"architect": {"type": "claude-code", "model": "..."}, ...}
    AI_PROVIDERS_CONFIG: str = ""
    
    # Legacy settings (kept for backwards compatibility)
    USE_HYBRID_AGENTS: bool = True
    USE_CLI_FOR_ALL_PHASES: str = "auto"
    
    def get_providers_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the providers configuration dict."""
        # If explicit JSON config provided, use it
        if self.AI_PROVIDERS_CONFIG:
            try:
                return json.loads(self.AI_PROVIDERS_CONFIG)
            except json.JSONDecodeError:
                pass
        
        # Build config based on mode
        mode = self.AI_PROVIDER_MODE.lower()
        
        if mode == "oauth" or (mode == "auto" and self._has_oauth()):
            # OAuth mode - use Claude Max subscription
            return {
                "default": {
                    "type": "claude-code",
                    "model": self.ANTHROPIC_MODEL,
                },
                "architect": {
                    "type": "claude-code",
                    "model": self.ANTHROPIC_MODEL,
                },
                "developer": {
                    "type": "claude-code",
                    "model": self.ANTHROPIC_MODEL,
                    "allowed_tools": ["Read", "Write", "Edit", "Bash"],
                },
                "reviewer": {
                    "type": "claude-code",
                    "model": self.ANTHROPIC_MODEL,
                },
            }
        
        elif mode == "api" or (mode == "auto" and self.ANTHROPIC_API_KEY):
            # API mode - pay-as-you-go
            return {
                "default": {
                    "type": "anthropic",
                    "model": self.ANTHROPIC_MODEL,
                    "api_key": self.ANTHROPIC_API_KEY,
                },
            }
        
        elif mode == "local":
            # Local mode - Ollama
            return {
                "default": {
                    "type": "ollama",
                    "model": self.OLLAMA_MODEL,
                    "base_url": self.OLLAMA_URL,
                },
            }
        
        else:
            # Fallback to OAuth (will use simulated if not available)
            return {
                "default": {
                    "type": "claude-code",
                    "model": self.ANTHROPIC_MODEL,
                },
            }
    
    def _has_oauth(self) -> bool:
        """Check if OAuth credentials are available."""
        from pathlib import Path
        try:
            creds_file = Path(self.CLAUDE_CONFIG_DIR) / ".credentials.json"
            if creds_file.exists():
                import json
                with open(creds_file) as f:
                    creds = json.load(f)
                return bool(creds.get("claudeAiOauth", {}).get("accessToken"))
        except Exception:
            pass
        return False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://soloboy:eW880dRvPhVRIBi3IajQRt77@localhost:5432/agent_rangers"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000", "http://192.168.1.225:5173"]

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
