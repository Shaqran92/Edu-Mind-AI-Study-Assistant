"""
Advanced Session Management
Provides robust session persistence and recovery.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from utils.logger import get_logger

logger = get_logger("session_manager")


class SessionState:
    """Represents the application session state."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # UI state
        self.current_tab: str = "dashboard"
        self.window_geometry: Dict[str, int] = {}
        
        # Study state
        self.current_subject: Optional[str] = None
        self.recent_files: List[str] = []
        self.open_notes: List[Dict[str, Any]] = []
        
        # AI state
        self.ai_provider: str = "offline"
        self.model_in_use: str = "offline"
        
        # User preferences
        self.theme: str = "dark"
        self.language: str = "en"
        self.auto_save_enabled: bool = True
        
        # Custom data
        self.custom_data: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "current_tab": self.current_tab,
            "window_geometry": self.window_geometry,
            "current_subject": self.current_subject,
            "recent_files": self.recent_files,
            "open_notes": self.open_notes,
            "ai_provider": self.ai_provider,
            "model_in_use": self.model_in_use,
            "theme": self.theme,
            "language": self.language,
            "auto_save_enabled": self.auto_save_enabled,
            "custom_data": self.custom_data,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SessionState":
        """Create from dictionary."""
        state = SessionState(data.get("session_id", "unknown"))
        state.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        state.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        state.current_tab = data.get("current_tab", "dashboard")
        state.window_geometry = data.get("window_geometry", {})
        state.current_subject = data.get("current_subject")
        state.recent_files = data.get("recent_files", [])
        state.open_notes = data.get("open_notes", [])
        state.ai_provider = data.get("ai_provider", "offline")
        state.model_in_use = data.get("model_in_use", "offline")
        state.theme = data.get("theme", "dark")
        state.language = data.get("language", "en")
        state.auto_save_enabled = data.get("auto_save_enabled", True)
        state.custom_data = data.get("custom_data", {})
        return state


class AdvancedSessionManager:
    """
    Advanced session management with:
    - State persistence
    - Crash recovery
    - Multi-session support
    - State synchronization
    """
    
    def __init__(self, session_dir: str = "data/sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[SessionState] = None
        self.backup_dir = self.session_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self.max_backups = 5
    
    def create_session(self, session_id: str = None) -> SessionState:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID (auto-generated if not provided)
        
        Returns:
            New session state
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = SessionState(session_id)
        logger.info(f"Created new session: {session_id}")
        return self.current_session
    
    def load_session(self, session_id: str) -> Optional[SessionState]:
        """
        Load an existing session.
        
        Args:
            session_id: Session ID to load
        
        Returns:
            Session state, or None if not found
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            logger.warning(f"Session not found: {session_id}")
            return None
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            self.current_session = SessionState.from_dict(data)
            logger.info(f"Loaded session: {session_id}")
            return self.current_session
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def save_session(self) -> bool:
        """
        Save the current session.
        
        Returns:
            True if successful
        """
        if not self.current_session:
            logger.warning("No session to save")
            return False
        
        self.current_session.last_updated = datetime.now()
        session_file = self.session_dir / f"{self.current_session.session_id}.json"
        
        try:
            # Create backup
            if session_file.exists():
                self._create_backup(session_file)
            
            # Save new version
            with open(session_file, 'w') as f:
                json.dump(self.current_session.to_dict(), f, indent=2)
            
            logger.debug(f"Saved session: {self.current_session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def _create_backup(self, session_file: Path) -> None:
        """Create a backup of the session file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"{session_file.stem}_{timestamp}.json"
            
            with open(session_file, 'r') as f:
                content = f.read()
            with open(backup_file, 'w') as f:
                f.write(content)
            
            # Clean old backups
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backups keeping only the latest N."""
        try:
            backups = sorted(self.backup_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            for old_backup in backups[self.max_backups:]:
                old_backup.unlink()
        except Exception as e:
            logger.error(f"Failed to cleanup backups: {e}")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session info dictionaries
        """
        sessions = []
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                sessions.append({
                    "session_id": data.get("session_id"),
                    "created_at": data.get("created_at"),
                    "last_updated": data.get("last_updated"),
                    "subject": data.get("current_subject"),
                    "file": session_file.name,
                })
            except Exception as e:
                logger.error(f"Failed to read session file {session_file}: {e}")
        
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session to delete
        
        Returns:
            True if successful
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        try:
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Deleted session: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
        
        return False
    
    def export_session(self, session_id: str, export_path: str) -> bool:
        """
        Export a session to a file.
        
        Args:
            session_id: Session to export
            export_path: Path to export to
        
        Returns:
            True if successful
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            logger.warning(f"Session not found: {session_id}")
            return False
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            export_file = Path(export_path)
            with open(export_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported session to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return False
    
    def auto_save(self, interval_seconds: int = 300) -> None:
        """
        Enable auto-saving of the current session.
        
        Args:
            interval_seconds: Auto-save interval in seconds
        """
        # This would typically be called periodically by the UI
        if self.current_session:
            self.save_session()


# Global session manager instance
_session_manager_instance = None


def get_session_manager() -> AdvancedSessionManager:
    """Get the global session manager."""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = AdvancedSessionManager()
    return _session_manager_instance
