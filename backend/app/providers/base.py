"""Base classes for the Provider Abstraction Layer."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional, List, Dict, Any


class Role(str, Enum):
    """Message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A message in a conversation."""
    role: Role
    content: str


@dataclass
class CompletionResponse:
    """Response from a completion request."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class StreamEvent:
    """Event from a streaming response."""
    type: str  # "text_delta", "input_tokens", "output_tokens", "done", "error"
    content: Optional[str] = None
    tokens: Optional[int] = None
    error: Optional[str] = None


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    type: str  # "claude-code", "anthropic", "openai", "ollama"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 300  # 5 minutes default
    max_tokens: int = 4096
    temperature: float = 0.7
    allowed_tools: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, config: ProviderConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self.model = config.model
        self.timeout = config.timeout
        self.max_tokens = config.max_tokens

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return the provider type identifier."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Return whether this provider supports streaming."""
        pass

    @property
    def supports_tools(self) -> bool:
        """Return whether this provider supports tool use."""
        return False

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> CompletionResponse:
        """
        Generate a completion for the given messages.
        
        Args:
            messages: List of conversation messages
            system: Optional system prompt
            **kwargs: Additional provider-specific options
            
        Returns:
            CompletionResponse with the generated content
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """
        Stream a completion for the given messages.
        
        Args:
            messages: List of conversation messages
            system: Optional system prompt
            **kwargs: Additional provider-specific options
            
        Yields:
            StreamEvent objects with content chunks
        """
        pass

    async def health_check(self) -> bool:
        """Check if the provider is available and working."""
        try:
            response = await asyncio.wait_for(
                self.complete(
                    messages=[Message(role=Role.USER, content="Say 'ok'")],
                    system="Respond with only 'ok'",
                ),
                timeout=30,
            )
            return bool(response.content)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
