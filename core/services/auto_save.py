# core/services/auto_save.py
"""
Auto-save service for preventing data loss.
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable

from utils.logger import get_logger
from utils.helpers import get_data_dir

logger = get_logger("auto_save")


class AutoSaveService:
    """
    Service for automatically saving application state.
    
    Features:
    - Configurable save interval
    - Crash recovery
    - State versioning
    
    Example:
        >>> auto_save = AutoSaveService(interval_seconds=60)
        >>> auto_save.register("notes", lambda: get_current_notes())
        >>> auto_save.start()
    """
    
    def __init__(self, interval_seconds: int = 300):  # Default 5 minutes
        self._interval = interval_seconds
        self._is_running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._state_providers: Dict[str, Callable[[], Any]] = {}
        self._save_dir = get_data_dir() / "auto_save"
        self._save_dir.mkdir(exist_ok=True)
        
        logger.info(f"Auto-save service initialized (interval: {interval_seconds}s)")
    
    def register(self, name: str, provider: Callable[[], Any]):
        """
        Register a state provider.
        
        Args:
            name: Unique name for this state
            provider: Callable that returns the state to save
        """
        self._state_providers[name] = provider
        logger.debug(f"Registered state provider: {name}")
    
    def unregister(self, name: str):
        """Unregister a state provider."""
        if name in self._state_providers:
            del self._state_providers[name]
            logger.debug(f"Unregistered state provider: {name}")
    
    def start(self):
        """Start auto-save background thread."""
        if self._is_running:
            return
        
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Auto-save service started")
    
    def stop(self):
        """Stop auto-save and perform final save."""
        if not self._is_running:
            return
        
        self._stop_event.set()
        self._is_running = False
        
        # Final save
        self.save_now()
        logger.info("Auto-save service stopped")
    
    def save_now(self) -> bool:
        """Manually trigger a save."""
        try:
            state = {}
            for name, provider in self._state_providers.items():
                try:
                    state[name] = provider()
                except Exception as e:
                    logger.error(f"Error getting state for '{name}': {e}")
            
            if not state:
                return True
            
            # Save with timestamp
            save_data = {
                "saved_at": datetime.now().isoformat(),
                "version": 1,
                "state": state
            }
            
            save_path = self._save_dir / "current_state.json"
            
            # Write to temp file first, then rename (atomic operation)
            temp_path = self._save_dir / "current_state.tmp"
            with open(temp_path, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
            
            temp_path.replace(save_path)
            
            logger.debug(f"Auto-saved state ({len(state)} providers)")
            return True
            
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
            return False
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load previously saved state."""
        try:
            save_path = self._save_dir / "current_state.json"
            
            if not save_path.exists():
                return None
            
            with open(save_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded state from {data.get('saved_at', 'unknown')}")
            return data.get("state", {})
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def has_recovery_data(self) -> bool:
        """Check if recovery data exists."""
        save_path = self._save_dir / "current_state.json"
        return save_path.exists()
    
    def clear_recovery_data(self):
        """Clear recovery data after successful load."""
        try:
            save_path = self._save_dir / "current_state.json"
            if save_path.exists():
                # Archive instead of delete
                archive_path = self._save_dir / f"archived_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_path.rename(archive_path)
                
                # Keep only last 5 archives
                archives = sorted(self._save_dir.glob("archived_*.json"))
                for old_archive in archives[:-5]:
                    old_archive.unlink()
                
                logger.debug("Recovery data archived")
        except Exception as e:
            logger.error(f"Failed to clear recovery data: {e}")
    
    def _run(self):
        """Background thread loop."""
        while not self._stop_event.is_set():
            # Wait for interval or stop signal
            self._stop_event.wait(self._interval)
            
            if not self._stop_event.is_set():
                self.save_now()


class CrashRecoveryManager:
    """
    Manager for handling crash recovery.
    
    Usage:
        >>> manager = CrashRecoveryManager()
        >>> if manager.has_recovery_data():
        >>>     if manager.prompt_recovery():
        >>>         state = manager.recover()
        >>>         # Restore application state
        >>>     else:
        >>>         manager.discard_recovery()
    """
    
    def __init__(self):
        self._auto_save = AutoSaveService()
        self._recovery_data: Optional[Dict[str, Any]] = None
    
    def has_recovery_data(self) -> bool:
        """Check if recovery data exists from a previous session."""
        return self._auto_save.has_recovery_data()
    
    def get_recovery_info(self) -> Optional[Dict[str, str]]:
        """Get info about available recovery data."""
        try:
            save_path = get_data_dir() / "auto_save" / "current_state.json"
            if not save_path.exists():
                return None
            
            with open(save_path, 'r') as f:
                data = json.load(f)
            
            return {
                "saved_at": data.get("saved_at", "Unknown"),
                "providers": ", ".join(data.get("state", {}).keys())
            }
        except:
            return None
    
    def recover(self) -> Optional[Dict[str, Any]]:
        """Load and return recovery data."""
        self._recovery_data = self._auto_save.load_state()
        return self._recovery_data
    
    def discard_recovery(self):
        """Discard recovery data without loading."""
        self._auto_save.clear_recovery_data()
        logger.info("Recovery data discarded by user")
    
    def confirm_recovery_complete(self):
        """Confirm that recovery was successful."""
        self._auto_save.clear_recovery_data()
        logger.info("Recovery completed and data cleared")


# Global instance
_auto_save: Optional[AutoSaveService] = None

def get_auto_save() -> AutoSaveService:
    """Get the global auto-save service instance."""
    global _auto_save
    if _auto_save is None:
        _auto_save = AutoSaveService()
    return _auto_save
