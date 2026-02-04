"""Anthropic API Provider using direct API calls.

Requires API key and uses pay-as-you-go billing.
"""

import logging
from typing import AsyncIterator, List, Optional

from app.providers.base import (
    BaseProvider,
    ProviderConfig,
    Message,
    Role,
    CompletionResponse,
    StreamEvent,
)

logger = logging.getLogger(__name__)


class AnthropicAPIProvider(BaseProvider):
    """
    Provider that uses Anthropic's direct API.
    
    Requires ANTHROPIC_API_KEY and uses pay-as-you-go billing.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None
        self.api_key = config.api_key

    @property
    def provider_type(self) -> str:
        return "anthropic"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        return True

    @property
    def client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                if not self.api_key:
                    raise ValueError("ANTHROPIC_API_KEY not configured")
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed")
        return self._client

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert Message objects to Anthropic format."""
        return [
            {"role": msg.role.value if msg.role != Role.SYSTEM else "user", "content": msg.content}
            for msg in messages
            if msg.role != Role.SYSTEM
        ]

    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> CompletionResponse:
        """Generate completion using Anthropic API."""
        anthropic_messages = self._convert_messages(messages)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            system=system or "",
            messages=anthropic_messages,
            temperature=kwargs.get("temperature", self.config.temperature),
        )
        
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        
        return CompletionResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
        )

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """Stream completion using Anthropic API."""
        anthropic_messages = self._convert_messages(messages)
        
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                system=system or "",
                messages=anthropic_messages,
                temperature=kwargs.get("temperature", self.config.temperature),
            ) as stream:
                for text in stream.text_stream:
                    yield StreamEvent(type="text_delta", content=text)
                
                # Get final message for token counts
                final = stream.get_final_message()
                yield StreamEvent(
                    type="input_tokens",
                    tokens=final.usage.input_tokens,
                )
                yield StreamEvent(
                    type="output_tokens", 
                    tokens=final.usage.output_tokens,
                )
                yield StreamEvent(type="done")
                
        except Exception as e:
            yield StreamEvent(type="error", error=str(e))

    async def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            # Quick test with minimal tokens
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}],
            )
            return bool(response.content)
        except Exception as e:
            logger.warning(f"Anthropic health check failed: {e}")
            return False
