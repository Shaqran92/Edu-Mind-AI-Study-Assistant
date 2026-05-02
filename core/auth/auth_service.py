# core/auth/auth_service.py
"""
Authentication service for EduMind.
Handles user registration, login, and session management.
"""

import json
import secrets
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from core.auth.user_model import User, UserProfile, Session, AuthProvider
from utils.logger import get_logger

logger = get_logger("auth")


class AuthError(Exception):
    """Authentication error."""
    pass


class AuthService:
    """
    Authentication service for managing users and sessions.
    
    Features:
    - Email/password registration and login
    - OAuth support (Google, GitHub)
    - Session management
    - Per-user data isolation
    
    Example:
        >>> auth = AuthService()
        >>> user = auth.signup("test@example.com", "TestUser", "password123")
        >>> session = auth.login("test@example.com", "password123")
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.users_file = self.data_dir / "users.json"
        self.sessions_file = self.data_dir / "sessions.json"
        
        self._users: dict[str, User] = {}
        self._sessions: dict[str, Session] = {}
        self._current_session: Optional[Session] = None
        
        self._load_data()
        logger.info(f"AuthService initialized with {len(self._users)} users")
    
    def _load_data(self):
        """Load users and sessions from files."""
        # Load users
        try:
            if self.users_file.exists():
                with open(self.users_file) as f:
                    data = json.load(f)
                    for user_data in data.get("users", []):
                        user = User.from_dict(user_data)
                        self._users[user.email.lower()] = user
        except Exception as e:
            logger.warning(f"Could not load users: {e}")
        
        # Load sessions
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file) as f:
                    data = json.load(f)
                    for session_data in data.get("sessions", []):
                        session = Session.from_dict(session_data)
                        if not session.is_expired:
                            self._sessions[session.session_id] = session
        except Exception as e:
            logger.warning(f"Could not load sessions: {e}")
    
    def _save_users(self):
        """Save users to file."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.users_file, 'w') as f:
                json.dump({
                    "users": [u.to_dict() for u in self._users.values()]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save users: {e}")
    
    def _save_sessions(self):
        """Save sessions to file."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.sessions_file, 'w') as f:
                json.dump({
                    "sessions": [s.to_dict() for s in self._sessions.values() if not s.is_expired]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save sessions: {e}")
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        return True, ""
    
    def signup(
        self,
        email: str,
        username: str,
        password: str,
        profile: Optional[UserProfile] = None
    ) -> User:
        """
        Register a new user.
        
        Args:
            email: User's email address
            username: Display username
            password: Password (will be hashed)
            profile: Optional user profile
        
        Returns:
            The created User object
        
        Raises:
            AuthError: If validation fails or email exists
        """
        email = email.lower().strip()
        username = username.strip()
        
        # Validate email
        if not self._validate_email(email):
            raise AuthError("Invalid email format")
        
        # Check if email exists
        if email in self._users:
            raise AuthError("Email already registered")
        
        # Validate password
        is_valid, error = self._validate_password(password)
        if not is_valid:
            raise AuthError(error)
        
        # Validate username
        if len(username) < 3:
            raise AuthError("Username must be at least 3 characters")
        
        # Create user
        user_id = f"user_{secrets.token_hex(8)}"
        user = User(
            id=user_id,
            email=email,
            username=username,
            profile=profile or UserProfile(display_name=username)
        )
        user.set_password(password)
        
        # Save
        self._users[email] = user
        self._save_users()
        
        # Create user data directory
        user.get_data_directory(str(self.data_dir))
        
        logger.info(f"New user registered: {email}")
        return user
    
    def login(self, email: str, password: str) -> Session:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email
            password: User's password
        
        Returns:
            Session object
        
        Raises:
            AuthError: If credentials are invalid
        """
        email = email.lower().strip()
        
        # Find user
        user = self._users.get(email)
        if not user:
            raise AuthError("Invalid email or password")
        
        # Verify password
        if not user.verify_password(password):
            raise AuthError("Invalid email or password")
        
        # Check if active
        if not user.is_active:
            raise AuthError("Account is deactivated")
        
        # Update last login
        user.last_login = datetime.now()
        self._save_users()
        
        # Create session
        session = Session(
            session_id=secrets.token_urlsafe(32),
            user_id=user.id
        )
        self._sessions[session.session_id] = session
        self._current_session = session
        self._save_sessions()
        
        logger.info(f"User logged in: {email}")
        return session
    
    def login_with_oauth(
        self,
        provider: AuthProvider,
        email: str,
        username: str,
        oauth_token: str,
        avatar_url: str = ""
    ) -> Session:
        """
        Login or register with OAuth provider.
        
        Args:
            provider: OAuth provider (Google, GitHub)
            email: Email from OAuth provider
            username: Username from OAuth provider
            oauth_token: OAuth access token
            avatar_url: Profile picture URL
        
        Returns:
            Session object
        """
        email = email.lower().strip()
        
        # Check if user exists
        user = self._users.get(email)
        
        if not user:
            # Create new user
            user_id = f"user_{secrets.token_hex(8)}"
            user = User(
                id=user_id,
                email=email,
                username=username,
                auth_provider=provider,
                oauth_token=oauth_token,
                profile=UserProfile(
                    display_name=username,
                    avatar_url=avatar_url
                ),
                is_verified=True  # OAuth users are pre-verified
            )
            self._users[email] = user
            self._save_users()
            logger.info(f"New OAuth user registered: {email} via {provider.value}")
        else:
            # Update OAuth token
            user.oauth_token = oauth_token
            user.last_login = datetime.now()
            self._save_users()
        
        # Create session
        session = Session(
            session_id=secrets.token_urlsafe(32),
            user_id=user.id
        )
        self._sessions[session.session_id] = session
        self._current_session = session
        self._save_sessions()
        
        logger.info(f"OAuth login: {email}")
        return session
    
    def logout(self, session_id: Optional[str] = None):
        """Logout and invalidate session."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        
        if sid and sid in self._sessions:
            self._sessions[sid].is_active = False
            del self._sessions[sid]
            self._save_sessions()
        
        if self._current_session and self._current_session.session_id == sid:
            self._current_session = None
        
        logger.info("User logged out")
    
    def get_current_user(self) -> Optional[User]:
        """Get the currently logged in user."""
        if not self._current_session:
            return None
        
        if self._current_session.is_expired:
            self.logout()
            return None
        
        for user in self._users.values():
            if user.id == self._current_session.user_id:
                return user
        
        return None
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate a session ID and return the user."""
        session = self._sessions.get(session_id)
        
        if not session or session.is_expired or not session.is_active:
            return None
        
        for user in self._users.values():
            if user.id == session.user_id:
                return user
        
        return None
    
    def update_profile(self, user_id: str, profile: UserProfile) -> bool:
        """Update a user's profile."""
        for user in self._users.values():
            if user.id == user_id:
                user.profile = profile
                self._save_users()
                return True
        return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        for user in self._users.values():
            if user.id == user_id:
                if not user.verify_password(old_password):
                    raise AuthError("Current password is incorrect")
                
                is_valid, error = self._validate_password(new_password)
                if not is_valid:
                    raise AuthError(error)
                
                user.set_password(new_password)
                self._save_users()
                return True
        return False
    
    def get_user_count(self) -> int:
        """Get total number of registered users."""
        return len(self._users)
    
    @property
    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in."""
        return self.get_current_user() is not None


# Global instance
_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    """Get the global auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
