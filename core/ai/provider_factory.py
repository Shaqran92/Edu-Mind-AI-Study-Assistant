# core/ai/provider_factory.py
"""
Factory for creating AI provider instances based on configuration.
"""

from typing import Optional
from core.ai.base_provider import LLMProvider
from config import settings
from utils.logger import get_logger

logger = get_logger("ai.factory")

# Provider instances cache
_provider_cache: dict = {}


def get_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """
    Factory function to get the configured AI provider.
    
    Args:
        provider_name: Optional override for provider name.
                      If not provided, uses settings.provider
    
    Returns:
        An instance of LLMProvider
    
    Raises:
        RuntimeError: If the requested provider is not available
    
    Example:
        >>> provider = get_provider()  # Uses configured provider
        >>> provider = get_provider("gemini")  # Force Gemini
    """
    name = (provider_name or settings.provider).lower()
    
    # Check cache first
    if name in _provider_cache:
        logger.debug(f"Returning cached provider: {name}")
        return _provider_cache[name]
    
    logger.info(f"Initializing provider: {name}")
    
    if name == "openai":
        provider = _create_openai_provider()
    elif name == "gemini":
        provider = _create_gemini_provider()
    elif name == "offline":
        provider = _create_offline_provider()
    else:
        logger.warning(f"Unknown provider '{name}', falling back to offline")
        provider = _create_offline_provider()
    
    _provider_cache[name] = provider
    return provider


def _create_openai_provider() -> LLMProvider:
    """Create an OpenAI provider instance."""
    try:
        from core.ai.openai_provider import OpenAIProvider
        provider = OpenAIProvider()
        if provider.is_available():
            logger.info(f"OpenAI provider ready (model: {provider.get_model_name()})")
            return provider
        else:
            logger.warning("OpenAI API key not configured, falling back to offline")
            return _create_offline_provider()
    except ImportError as e:
        logger.error(f"Failed to import OpenAI provider: {e}")
        return _create_offline_provider()
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI provider: {e}")
        return _create_offline_provider()


def _create_gemini_provider() -> LLMProvider:
    """Create a Gemini provider instance."""
    try:
        from core.ai.gemini_provider import GeminiProvider
        provider = GeminiProvider()
        if provider.is_available():
            logger.info(f"Gemini provider ready (model: {provider.get_model_name()})")
            return provider
        else:
            logger.warning("Gemini API key not configured, falling back to offline")
            return _create_offline_provider()
    except ImportError as e:
        logger.error(f"Failed to import Gemini provider: {e}")
        return _create_offline_provider()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini provider: {e}")
        return _create_offline_provider()


def _create_offline_provider() -> LLMProvider:
    """Create an offline provider instance."""
    from core.ai.offline_provider import OfflineProvider
    logger.info("Using offline provider")
    return OfflineProvider()


def clear_provider_cache():
    """Clear the provider cache. Useful for testing or config changes."""
    global _provider_cache
    _provider_cache = {}
    logger.debug("Provider cache cleared")
