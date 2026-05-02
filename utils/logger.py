# utils/logger.py
"""
Structured logging system for EduMind with file rotation and console output.
Replaces print statements with proper logging infrastructure.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    # Emoji indicators for visual scanning
    ICONS = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color and icon for console
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        icon = self.ICONS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format the message
        original_msg = record.msg
        record.msg = f"{color}{icon} {record.msg}{reset}"
        result = super().format(record)
        record.msg = original_msg
        
        return result


class PlainFormatter(logging.Formatter):
    """Plain text formatter for file output."""
    
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record)


def get_log_directory() -> Path:
    """Get or create the logs directory."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_dir = Path(sys.executable).parent
    else:
        # Running as script
        base_dir = Path(__file__).parent.parent
    
    log_dir = base_dir / 'logs'
    log_dir.mkdir(exist_ok=True)
    return log_dir


def setup_logger(
    name: str = "edumind",
    log_file: Optional[str] = None,
    level: int = logging.DEBUG,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (used for hierarchical logging)
        log_file: Optional custom log file path
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger("edumind.core")
        >>> logger.info("Application started")
        >>> logger.error("Something went wrong", exc_info=True)
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False
    
    # Create formatters
    file_format = '%(asctime)s | %(name)-20s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s'
    console_format = '%(asctime)s | %(name)s | %(message)s'
    
    file_formatter = PlainFormatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
    console_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S')
    
    # File handler with rotation
    if log_file is None:
        log_dir = get_log_directory()
        log_file = log_dir / f"{name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Only INFO+ to console
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the specified name.
    
    Args:
        name: Logger name (will be prefixed with 'edumind.')
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger("llm")  # Creates "edumind.llm" logger
        >>> logger.info("LLM provider initialized")
    """
    full_name = f"edumind.{name}" if not name.startswith("edumind") else name
    return logging.getLogger(full_name)


# Create root logger on module import
_root_logger = setup_logger("edumind")


# Convenience functions for quick logging
def debug(msg: str, *args, **kwargs):
    _root_logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    _root_logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    _root_logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    _root_logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    _root_logger.critical(msg, *args, **kwargs)


if __name__ == "__main__":
    # Test the logging system
    logger = setup_logger("edumind.test")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test child logger
    child_logger = get_logger("llm")
    child_logger.info("Child logger test")
