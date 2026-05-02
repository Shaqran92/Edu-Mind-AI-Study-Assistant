# core/auth/__init__.py
"""
Authentication module for EduMind.
"""

from core.auth.user_model import User, UserProfile
from core.auth.auth_service import AuthService, AuthError, get_auth_service

__all__ = ["User", "UserProfile", "AuthService", "AuthError", "get_auth_service"]
