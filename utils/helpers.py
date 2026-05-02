# utils/helpers.py
"""
General helper utilities for EduMind.
"""

from datetime import datetime, timezone
from typing import Optional
import os
import sys
from pathlib import Path


def now_iso() -> str:
    """
    Returns the current UTC time in ISO 8601 format.
    
    Returns:
        Timestamp string like "2024-01-15T10:30:00Z"
    """
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def now_local() -> str:
    """
    Returns the current local time in human-readable format.
    
    Returns:
        Timestamp string like "January 15, 2024 10:30 AM"
    """
    return datetime.now().strftime('%B %d, %Y %I:%M %p')


def get_project_root() -> Path:
    """
    Get the project root directory.
    Works both in development and when packaged.
    
    Returns:
        Path to project root
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script - go up from utils/
        return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """
    Get the data directory for storing user data.
    Creates the directory if it doesn't exist.
    
    Returns:
        Path to data directory
    """
    data_dir = get_project_root() / 'data'
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_assets_dir() -> Path:
    """
    Get the assets directory.
    
    Returns:
        Path to assets directory
    """
    return get_project_root() / 'assets'


def get_temp_dir() -> Path:
    """
    Get a temporary directory for processing files.
    Creates it if it doesn't exist.
    
    Returns:
        Path to temp directory
    """
    temp_dir = get_project_root() / 'temp'
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """
    Sanitize a string for use as a filename.
    
    Args:
        name: Original string
        max_length: Maximum filename length
    
    Returns:
        Safe filename string
    """
    # Replace disallowed characters
    safe = "".join(c if c.isalnum() or c in '-_. ' else '_' for c in name)
    # Remove multiple underscores/spaces
    safe = ' '.join(safe.split())
    safe = '_'.join(part for part in safe.split('_') if part)
    # Truncate
    if len(safe) > max_length:
        safe = safe[:max_length].rstrip('_')
    return safe or "unnamed"


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Human-readable size string
    
    Example:
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1073741824)
        '1.0 GB'
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with a suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: String to append when truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Return singular or plural form based on count.
    
    Args:
        count: The count
        singular: Singular form
        plural: Plural form (defaults to singular + 's')
    
    Returns:
        Appropriate form with count
    
    Example:
        >>> pluralize(1, "note")
        '1 note'
        >>> pluralize(5, "quiz", "quizzes")
        '5 quizzes'
    """
    if plural is None:
        plural = singular + 's'
    word = singular if count == 1 else plural
    return f"{count} {word}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))
