import logging

from app.ai.base import AIProvider
from app.ai.gemini import GeminiProvider
from app.ai.openrouter import OpenRouterProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    _providers: dict[str, type[AIProvider]] = {}

    @classmethod
    def register(cls, provider: type[AIProvider]) -> None:
        if not hasattr(provider, "name") or not provider.name:
            raise ValueError(f"Provider {provider.__name__} must define `name`")
        cls._providers[provider.name] = provider
        logger.debug("Registered AI provider: %s", provider.name)

    @classmethod
    def get(cls, name: str) -> AIProvider:
        provider_cls = cls._providers.get(name)
        if not provider_cls:
            available = ", ".join(cls._providers)
            raise ValueError(f"Unknown provider '{name}'. Available: {available}")
        return provider_cls()

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers)


ProviderRegistry.register(GeminiProvider)
ProviderRegistry.register(OpenRouterProvider)
