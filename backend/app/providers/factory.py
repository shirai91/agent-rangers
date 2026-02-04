"""Provider Factory for creating providers from configuration."""

import logging
import os
from typing import Dict, Optional, Any

from app.providers.base import BaseProvider, ProviderConfig

logger = logging.getLogger(__name__)


# Example configurations for different use cases
EXAMPLE_CONFIGS = {
    # All OAuth - uses Claude Max subscription (recommended for Max users)
    "all_oauth_max": {
        "default": {
            "type": "claude-code",
            "model": "claude-sonnet-4-20250514",
        },
        "architect": {
            "type": "claude-code",
            "model": "claude-sonnet-4-20250514",
        },
        "developer": {
            "type": "claude-code",
            "model": "claude-sonnet-4-20250514",
            "allowed_tools": ["Read", "Write", "Edit", "Bash"],
        },
        "reviewer": {
            "type": "claude-code",
            "model": "claude-sonnet-4-20250514",
        },
    },
    
    # OAuth + Local (completely free operations)
    "oauth_plus_local": {
        "architect": {
            "type": "claude-code",
            "model": "claude-sonnet-4-20250514",
        },
        "developer": {
            "type": "claude-code",
            "model": "claude-sonnet-4-20250514",
            "allowed_tools": ["Read", "Write", "Edit", "Bash"],
        },
        "reviewer": {
            "type": "ollama",
            "model": "qwen2.5-coder:32b",
        },
    },
    
    # API-based (pay-as-you-go)
    "api_only": {
        "default": {
            "type": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_key": "${ANTHROPIC_API_KEY}",
        },
    },
    
    # Local only (completely free, requires good hardware)
    "local_only": {
        "default": {
            "type": "ollama",
            "model": "qwen2.5-coder:32b",
        },
    },
}


class ProviderFactory:
    """Factory for creating AI providers from configuration."""

    _provider_classes = {}
    _instances: Dict[str, BaseProvider] = {}

    @classmethod
    def _load_provider_classes(cls):
        """Lazy load provider classes to avoid circular imports."""
        if not cls._provider_classes:
            from app.providers.claude_oauth import ClaudeOAuthProvider
            from app.providers.anthropic_api import AnthropicAPIProvider
            from app.providers.ollama import OllamaProvider
            
            cls._provider_classes = {
                "claude-code": ClaudeOAuthProvider,
                "anthropic": AnthropicAPIProvider,
                "openai": None,  # TODO: Implement OpenAI provider
                "ollama": OllamaProvider,
            }

    @classmethod
    def create(
        cls,
        config: Dict[str, Any],
        cache: bool = True,
    ) -> BaseProvider:
        """
        Create a provider from configuration dict.
        
        Args:
            config: Provider configuration dict
            cache: Whether to cache and reuse provider instances
            
        Returns:
            Configured provider instance
        """
        cls._load_provider_classes()
        
        provider_type = config.get("type", "claude-code")
        
        logger.info(f"Creating provider type={provider_type}, config={config}")
        
        # Generate cache key
        cache_key = f"{provider_type}:{config.get('model', 'default')}"
        
        if cache and cache_key in cls._instances:
            logger.info(f"Returning cached provider for {cache_key}")
            return cls._instances[cache_key]
        
        # Get provider class
        provider_class = cls._provider_classes.get(provider_type)
        if provider_class is None:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        # Expand environment variables in config
        expanded_config = cls._expand_env_vars(config)
        
        # Create ProviderConfig
        provider_config = ProviderConfig(
            type=provider_type,
            model=expanded_config.get("model", "claude-sonnet-4-20250514"),
            api_key=expanded_config.get("api_key"),
            base_url=expanded_config.get("base_url"),
            timeout=expanded_config.get("timeout", 300),
            max_tokens=expanded_config.get("max_tokens", 4096),
            temperature=expanded_config.get("temperature", 0.7),
            allowed_tools=expanded_config.get("allowed_tools", []),
            extra=expanded_config.get("extra", {}),
        )
        
        # Create provider instance
        provider = provider_class(provider_config)
        
        if cache:
            cls._instances[cache_key] = provider
        
        logger.info(f"Created provider: {provider}")
        return provider

    @classmethod
    def create_for_role(
        cls,
        role: str,
        providers_config: Dict[str, Dict[str, Any]],
    ) -> BaseProvider:
        """
        Create a provider for a specific agent role.
        
        Args:
            role: Agent role (architect, developer, reviewer)
            providers_config: Full providers configuration
            
        Returns:
            Provider configured for the role
        """
        # Try role-specific config first, fall back to default
        config = providers_config.get(role, providers_config.get("default", {}))
        
        if not config:
            # Ultimate fallback: OAuth provider
            config = {"type": "claude-code", "model": "claude-sonnet-4-20250514"}
        
        return cls.create(config)

    @classmethod
    def create_oauth_provider(
        cls,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> BaseProvider:
        """Convenience method to create OAuth provider."""
        return cls.create({
            "type": "claude-code",
            "model": model,
            **kwargs,
        })

    @classmethod
    def create_api_provider(
        cls,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> BaseProvider:
        """Convenience method to create API provider."""
        return cls.create({
            "type": "anthropic",
            "model": model,
            "api_key": api_key,
            **kwargs,
        })

    @classmethod
    def create_local_provider(
        cls,
        model: str = "qwen2.5-coder:32b",
        base_url: str = "http://localhost:11434",
        **kwargs,
    ) -> BaseProvider:
        """Convenience method to create local Ollama provider."""
        return cls.create({
            "type": "ollama",
            "model": model,
            "base_url": base_url,
            **kwargs,
        })

    @classmethod
    def _expand_env_vars(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Expand ${VAR} environment variables in config values."""
        result = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                result[key] = os.environ.get(env_var, "")
            elif isinstance(value, dict):
                result[key] = cls._expand_env_vars(value)
            else:
                result[key] = value
        return result

    @classmethod
    def clear_cache(cls):
        """Clear cached provider instances."""
        cls._instances.clear()

    @classmethod
    async def health_check_all(
        cls,
        providers_config: Dict[str, Dict[str, Any]],
    ) -> Dict[str, bool]:
        """Check health of all configured providers."""
        results = {}
        
        for role, config in providers_config.items():
            try:
                provider = cls.create(config, cache=False)
                results[role] = await provider.health_check()
            except Exception as e:
                logger.warning(f"Health check failed for {role}: {e}")
                results[role] = False
        
        return results
