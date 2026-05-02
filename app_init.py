"""
Application Initialization Module
Initializes all core services and ensures proper setup.
"""

import sys
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger("app_init")


def initialize_app() -> bool:
    """
    Initialize the EduMind application.
    
    Performs:
    - Configuration validation
    - Database initialization
    - Service startup
    - Directory creation
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("🚀 Initializing EduMind Application")
    logger.info("=" * 60)
    
    try:
        # Step 1: Initialize configuration
        logger.info("\n📋 Step 1: Loading configuration...")
        from config import settings
        settings.ensure_directories_exist()
        settings.validate_provider()
        logger.info("✅ Configuration loaded successfully")
        
        # Step 2: Initialize database
        logger.info("\n📊 Step 2: Initializing database...")
        from data.db import init_db, get_conn
        init_db()
        conn = get_conn()
        if conn:
            logger.info("✅ Database initialized successfully")
        else:
            raise RuntimeError("Failed to initialize database")
        
        # Step 3: Initialize analytics
        logger.info("\n📈 Step 3: Initializing analytics...")
        from core.services.advanced_analytics import get_analytics
        analytics = get_analytics()
        logger.info(f"✅ Analytics service ready (tracked sessions: {len(analytics.sessions)})")
        
        # Step 4: Initialize performance monitor
        logger.info("\n⚡ Step 4: Initializing performance monitor...")
        from core.services.performance import get_performance_monitor, get_task_pool
        monitor = get_performance_monitor()
        pool = get_task_pool()
        logger.info("✅ Performance monitoring enabled")
        
        # Step 5: Initialize session manager
        logger.info("\n💾 Step 5: Initializing session manager...")
        from core.services.session_manager import get_session_manager
        manager = get_session_manager()
        available_sessions = manager.list_sessions()
        logger.info(f"✅ Session manager ready ({len(available_sessions)} sessions available)")
        
        # Step 6: Initialize response cache
        logger.info("\n💾 Step 6: Initializing response cache...")
        from core.services.response_cache import get_cache
        cache = get_cache()
        cache_stats = cache.get_stats()
        logger.info(f"✅ Response cache ready ({cache_stats['total_entries']} cached responses)")
        
        # Step 7: Validate AI providers
        logger.info("\n🤖 Step 7: Checking AI providers...")
        _validate_providers(settings)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ EduMind Initialization Complete!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Initialization failed: {e}", exc_info=True)
        logger.error("\nPlease check:")
        logger.error("1. Write permissions for data/ directory")
        logger.error("2. Required Python packages installed")
        logger.error("3. Disk space available (minimum 100MB)")
        return False


def _validate_providers(settings) -> None:
    """Validate configured AI providers."""
    logger.debug("\nValidating AI providers...")
    
    # Check offline provider (always available)
    try:
        from core.ai.offline_provider import OfflineProvider
        provider = OfflineProvider()
        logger.debug("  ✓ Offline provider available")
    except Exception as e:
        logger.warning(f"  ✗ Offline provider error: {e}")
    
    # Check OpenAI provider
    if settings.openai_api_key:
        try:
            from core.ai.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            if provider.is_available():
                logger.debug(f"  ✓ OpenAI provider available ({provider.get_model_name()})")
        except Exception as e:
            logger.warning(f"  ✗ OpenAI provider not available: {e}")
    else:
        logger.debug("  - OpenAI provider (no API key configured)")
    
    # Check Gemini provider
    if settings.gemini_api_key:
        try:
            from core.ai.gemini_provider import GeminiProvider
            provider = GeminiProvider()
            if provider.is_available():
                logger.debug(f"  ✓ Gemini provider available ({provider.get_model_name()})")
        except Exception as e:
            logger.warning(f"  ✗ Gemini provider not available: {e}")
    else:
        logger.debug("  - Gemini provider (no API key configured)")
    
    # Log current provider
    logger.debug(f"\n  Current provider: {settings.provider}")


def cleanup_app() -> None:
    """
    Cleanup and shutdown the application.
    
    Performs:
    - Session saving
    - Cache cleanup
    - Resource cleanup
    - Database closure
    """
    logger.info("\n🛑 Shutting down EduMind...")
    
    try:
        # Save current session if active
        from core.services.session_manager import get_session_manager
        manager = get_session_manager()
        if manager.current_session:
            manager.save_session()
            logger.info("✓ Session saved")
        
        # Close database connections
        from data.db import close_conn
        close_conn()
        logger.info("✓ Database closed")
        
        # Shutdown task pool
        from core.services.performance import get_task_pool
        pool = get_task_pool()
        pool.shutdown()
        logger.info("✓ Task pool shutdown")
        
        logger.info("✅ Shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def validate_environment() -> bool:
    """
    Validate the environment before running.
    
    Returns:
        True if environment is valid, False otherwise
    """
    logger.info("Validating environment...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        logger.error(f"Python 3.10+ required, found {sys.version}")
        return False
    
    logger.debug(f"Python: {sys.version.split()[0]}")
    
    # Check required packages
    required_packages = [
        'PyQt6',
        'numpy',
        'networkx',
        'pdfplumber',
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.debug(f"✓ {package}")
        except ImportError:
            logger.warning(f"✗ {package} not installed")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.error("Run: pip install -r requirements.txt")
        return False
    
    logger.info("✅ Environment validation passed")
    return True


if __name__ == "__main__":
    # Test initialization
    success = validate_environment()
    if success:
        success = initialize_app()
    
    sys.exit(0 if success else 1)
