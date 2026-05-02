# core/auth/user_model.py
"""
User model and profile for EduMind authentication.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
import hashlib
import secrets
import json
from pathlib import Path


class AuthProvider(Enum):
    """Authentication provider types."""
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"


@dataclass
class UserProfile:
    """Extended user profile information."""
    display_name: str = ""
    avatar_url: str = ""
    bio: str = ""
    school: str = ""
    grade_level: str = ""
    subjects: List[str] = field(default_factory=list)
    study_goals: str = ""
    timezone: str = "UTC"
    language: str = "en"
    
    def to_dict(self) -> dict:
        return {
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "school": self.school,
            "grade_level": self.grade_level,
            "subjects": self.subjects,
            "study_goals": self.study_goals,
            "timezone": self.timezone,
            "language": self.language
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        return cls(
            display_name=data.get("display_name", ""),
            avatar_url=data.get("avatar_url", ""),
            bio=data.get("bio", ""),
            school=data.get("school", ""),
            grade_level=data.get("grade_level", ""),
            subjects=data.get("subjects", []),
            study_goals=data.get("study_goals", ""),
            timezone=data.get("timezone", "UTC"),
            language=data.get("language", "en")
        )


@dataclass
class User:
    """
    User model for EduMind.
    
    Stores user authentication and profile data.
    """
    id: str
    email: str
    username: str
    password_hash: str = ""
    salt: str = ""
    auth_provider: AuthProvider = AuthProvider.EMAIL
    profile: UserProfile = field(default_factory=UserProfile)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime = field(default_factory=datetime.now)
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    
    # OAuth tokens (encrypted in production)
    oauth_token: str = ""
    oauth_refresh_token: str = ""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        """
        Hash a password with salt.
        
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password_bytes,
            salt_bytes,
            iterations=100000
        )
        
        return hash_bytes.hex(), salt
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not self.password_hash or not self.salt:
            return False
        
        hash_check, _ = self.hash_password(password, self.salt)
        return secrets.compare_digest(hash_check, self.password_hash)
    
    def set_password(self, password: str):
        """Set a new password."""
        self.password_hash, self.salt = self.hash_password(password)
    
    def to_dict(self) -> dict:
        """Serialize user to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "auth_provider": self.auth_provider.value,
            "profile": self.profile.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat(),
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "oauth_token": self.oauth_token,
            "oauth_refresh_token": self.oauth_refresh_token
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Deserialize user from dictionary."""
        return cls(
            id=data["id"],
            email=data["email"],
            username=data["username"],
            password_hash=data.get("password_hash", ""),
            salt=data.get("salt", ""),
            auth_provider=AuthProvider(data.get("auth_provider", "email")),
            profile=UserProfile.from_dict(data.get("profile", {})),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_login=datetime.fromisoformat(data.get("last_login", datetime.now().isoformat())),
            is_active=data.get("is_active", True),
            is_verified=data.get("is_verified", False),
            oauth_token=data.get("oauth_token", ""),
            oauth_refresh_token=data.get("oauth_refresh_token", "")
        )
    
    def get_data_directory(self, base_path: str = ".") -> Path:
        """Get the user's data directory for isolated storage."""
        user_dir = Path(base_path) / "user_data" / self.id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir


@dataclass
class Session:
    """User session for maintaining login state."""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.expires_at is None:
            # Default: 7 days
            from datetime import timedelta
            self.expires_at = datetime.now() + timedelta(days=7)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            is_active=data.get("is_active", True)
        )
