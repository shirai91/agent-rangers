"""Provider Abstraction Layer for AI model access.

Supports multiple provider types:
- OAuth: Claude Code CLI (uses Max subscription)
- API: Direct Anthropic/OpenAI API calls
- Local: Ollama for self-hosted models
"""

from app.providers.base import (
    BaseProvider,
    ProviderConfig,
    Message,
    Role,
    CompletionResponse,
    StreamEvent,
)
from app.providers.factory import ProviderFactory
from app.providers.claude_oauth import ClaudeOAuthProvider
from app.providers.anthropic_api import AnthropicAPIProvider
from app.providers.ollama import OllamaProvider

__all__ = [
    "BaseProvider",
    "ProviderConfig", 
    "Message",
    "Role",
    "CompletionResponse",
    "StreamEvent",
    "ProviderFactory",
    "ClaudeOAuthProvider",
    "AnthropicAPIProvider",
    "OllamaProvider",
]
