# config.py
"""
EduMind Configuration Module
Provides centralized configuration management without external dependencies.
API keys are loaded from secure keyring storage, not environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def _get_api_key_from_keyring(service: str, key_name: str) -> str:
    """
    Safely retrieve API key from system keyring.
    
    Args:
        service: Service name in keyring (usually 'EduMind')
        key_name: Key identifier (e.g., 'openai_api_key')
    
    Returns:
        API key string, or empty string if not found or keyring unavailable
    """
    if not KEYRING_AVAILABLE:
        return ""
    
    try:
        key = keyring.get_password(service, key_name)
        return key or ""
    except Exception:
        return ""


# ─── Direct API Key Fallback ───
# If keyring doesn't have keys, these will be used as fallback
_FALLBACK_GEMINI_KEY = "AIzaSyDYRdUb0-zn5lPPo-z-nDldCkLXt0ptV_A"


def _resolve_gemini_key() -> str:
    """Resolve Gemini API key from keyring or fallback."""
    key = _get_api_key_from_keyring("EduMind", "gemini_api_key")
    if key:
        return key
    return _FALLBACK_GEMINI_KEY


@dataclass
class Settings:
    """Application settings with safe defaults."""
    
    # AI Provider Configuration
    provider: str = "gemini"  # "offline" | "openai" | "gemini"
    
    # API Keys (loaded from secure keyring with fallback)
    openai_api_key: str = field(default_factory=lambda: _get_api_key_from_keyring("EduMind", "openai_api_key"))
    gemini_api_key: str = field(default_factory=_resolve_gemini_key)
    
    # Model Configuration
    model_openai: str = "gpt-4o-mini"
    model_gemini: str = ""   # empty = auto-detect best available model at startup
    
    # Database Configuration
    db_path: str = "data/edumind.db"
    assets_dir: str = "assets"
    
    # Application Settings
    default_language: str = "en"
    max_chunk_chars: int = 1800
    auto_save_interval: int = 300  # 5 minutes in seconds
    
    # Feature Flags
    enable_analytics: bool = True
    enable_voice: bool = True
    enable_offline_models: bool = True
    cache_ai_responses: bool = True
    
    # Performance Settings
    thread_pool_size: int = 4
    cache_max_size_mb: int = 100

    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return _get_project_root()
    
    def ensure_directories_exist(self) -> None:
        """Ensure all required directories exist."""
        root = self.get_project_root()
        
        dirs_to_create = [
            root / self.db_path.split("/")[0] if "/" in self.db_path else root / "data",
            root / self.assets_dir,
            root / "logs",
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_provider(self) -> None:
        """Validate that the selected provider is properly configured."""
        self.provider = self.provider.lower()
        
        if self.provider == "openai" and not self.openai_api_key:
            print("[WARNING] OpenAI provider selected but no API key found.")
            print("   Please configure your API key in Settings -> API Configuration")
            self.provider = "offline"
        
        elif self.provider == "gemini" and not self.gemini_api_key:
            print("[WARNING] Gemini provider selected but no API key found.")
            print("   Please configure your API key in Settings -> API Configuration")
            self.provider = "offline"


# Create the global settings instance
settings = Settings()

# Validate and initialize on import
settings.ensure_directories_exist()
settings.validate_provider()

print(f"[SUCCESS] EduMind Configuration Loaded")
print(f"   Provider: {settings.provider}")
print(f"   Database: {settings.db_path}")
print(f"   Language: {settings.default_language}")