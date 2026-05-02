# setup.py
"""
EduMind Setup Script
Initializes the EduMind environment without requiring .env files or exposing API keys.
"""

import os
import sys
from pathlib import Path

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


def setup_environment():
    """
    Setup the EduMind environment with safe defaults.
    Does NOT create .env files or expose API keys.
    """
    print("🚀 Setting up EduMind...\n")
    
    # Create necessary directories
    dirs = ["assets", "data", "logs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Ensured directory: {dir_name}/")
    
    print("\n" + "="*60)
    print("🎉 EduMind Setup Complete!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("\n1. Configure API Keys (Optional)")
    print("   The app works offline by default.")
    print("   To use OpenAI or Gemini, launch the app and:")
    print("   - Go to Settings → API Configuration")
    print("   - Select your provider (OpenAI or Gemini)")
    print("   - Enter your API key (stored securely in system keyring)")
    
    print("\n2. Run EduMind")
    print("   python -m ui.main")
    
    print("\n3. Start Learning!")
    print("   Create notes, generate flashcards, and ace your tests.")
    
    print("\n" + "="*60)
    print("💡 SECURITY NOTES:")
    print("="*60)
    print("✓ No .env files required (avoiding accidental exposure)")
    print("✓ API keys stored securely in system keyring")
    print("✓ Works completely offline (no API keys needed)")
    print("✓ Settings persist across sessions")
    
    if not KEYRING_AVAILABLE:
        print("\n⚠️  WARNING: python-keyring not installed")
        print("   API keys will not be stored persistently.")
        print("   Install with: pip install keyring")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    setup_environment()