"""Ollama Provider for local/self-hosted models.

Completely free - runs models locally on your hardware.
"""

import asyncio
import json
import logging
from typing import AsyncIterator, List, Optional

import httpx

from app.providers.base import (
    BaseProvider,
    ProviderConfig,
    Message,
    Role,
    CompletionResponse,
    StreamEvent,
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """
    Provider that uses locally running Ollama server.
    
    Completely free - uses local hardware.
    Requires Ollama installed and running.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or config.extra.get(
            "ollama_url", "http://localhost:11434"
        )

    @property
    def provider_type(self) -> str:
        return "ollama"

    @property
    def supports_streaming(self) -> bool:
        return True

    def _convert_messages(
        self,
        messages: List[Message],
        system: Optional[str] = None,
    ) -> List[dict]:
        """Convert messages to Ollama format."""
        result = []
        
        if system:
            result.append({"role": "system", "content": system})
        
        for msg in messages:
            result.append({
                "role": msg.role.value,
                "content": msg.content,
            })
        
        return result

    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> CompletionResponse:
        """Generate completion using Ollama API."""
        ollama_messages = self._convert_messages(messages, system)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {
                        "num_predict": kwargs.get("max_tokens", self.max_tokens),
                        "temperature": kwargs.get("temperature", self.config.temperature),
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get("message", {}).get("content", "")
        
        # Ollama provides token counts in eval_count and prompt_eval_count
        input_tokens = data.get("prompt_eval_count")
        output_tokens = data.get("eval_count")
        
        return CompletionResponse(
            content=content,
            model=data.get("model", self.model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens_used=(input_tokens or 0) + (output_tokens or 0) if input_tokens or output_tokens else None,
            finish_reason=data.get("done_reason", "stop"),
            raw_response=data,
        )

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """Stream completion using Ollama API."""
        ollama_messages = self._convert_messages(messages, system)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": ollama_messages,
                        "stream": True,
                        "options": {
                            "num_predict": kwargs.get("max_tokens", self.max_tokens),
                            "temperature": kwargs.get("temperature", self.config.temperature),
                        },
                    },
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            
                            # Extract content from message
                            message = data.get("message", {})
                            content = message.get("content", "")
                            
                            if content:
                                yield StreamEvent(type="text_delta", content=content)
                            
                            # Check if done
                            if data.get("done"):
                                if data.get("prompt_eval_count"):
                                    yield StreamEvent(
                                        type="input_tokens",
                                        tokens=data["prompt_eval_count"],
                                    )
                                if data.get("eval_count"):
                                    yield StreamEvent(
                                        type="output_tokens",
                                        tokens=data["eval_count"],
                                    )
                                yield StreamEvent(type="done")
                                
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPStatusError as e:
            yield StreamEvent(type="error", error=f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.ConnectError:
            yield StreamEvent(type="error", error=f"Cannot connect to Ollama at {self.base_url}")
        except Exception as e:
            yield StreamEvent(type="error", error=str(e))

    async def health_check(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Check if Ollama is running
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                # Check if our model is available
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                
                # Model names might have :latest suffix
                model_base = self.model.split(":")[0]
                return any(model_base in m for m in models)
                
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []
