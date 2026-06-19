import pytest

from app.ai import ProviderRegistry, GeminiProvider, OpenRouterProvider
from app.ai.base import AIProvider


class TestProviderRegistry:
    def test_list_providers(self):
        providers = ProviderRegistry.list_providers()
        assert "gemini" in providers
        assert "openrouter" in providers

    def test_get_gemini(self):
        instance = ProviderRegistry.get("gemini")
        assert isinstance(instance, GeminiProvider)

    def test_get_openrouter(self):
        instance = ProviderRegistry.get("openrouter")
        assert isinstance(instance, OpenRouterProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider 'nonexistent'"):
            ProviderRegistry.get("nonexistent")

    def test_all_providers_implement_interface(self):
        for name in ProviderRegistry.list_providers():
            instance = ProviderRegistry.get(name)
            assert isinstance(instance, AIProvider)
            assert hasattr(instance, "complete")
            assert callable(instance.complete)
