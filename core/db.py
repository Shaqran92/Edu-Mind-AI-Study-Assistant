# core/db.py
"""
SQLite Database Manager for EduMind.
Handles connection and schema creation.
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from utils.logger import get_logger

logger = get_logger("db")

DB_FILE = "edumind.db"

class DatabaseManager:
    """Singleton database manager."""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()
        
    def _get_conn(self):
        """Get a configured connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def _init_db(self):
        """Initialize database schema."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                # Users Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    avatar_url TEXT,
                    is_guest BOOLEAN DEFAULT 0
                )
                """)
                
                # User Profiles Table (Extended info)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    school TEXT,
                    grade_level TEXT,
                    bio TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    streak_days INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """)
                
                # Study Sessions (for Analytics/Gamification)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_minutes INTEGER,
                    focus_score INTEGER,
                    notes TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """)
                
                # Reminders
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    time_str TEXT,
                    days TEXT, -- JSON string [1, 3, 5]
                    message TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """)
                # Quiz History (persistent score tracking)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS quiz_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary_id INTEGER,
                    score INTEGER,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    details_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Flashcard Reviews (spaced repetition tracking)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS flashcard_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flashcard_id INTEGER,
                    card_index INTEGER,
                    ease_factor REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 1,
                    repetitions INTEGER DEFAULT 0,
                    next_review TEXT,
                    last_reviewed TEXT,
                    FOREIGN KEY(flashcard_id) REFERENCES flashcards(id)
                )
                """)

                # Performance indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_start ON study_sessions(start_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_history_date ON quiz_history(created_at)")

                # Chat History (AI conversation persistence)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                # AI Response Cache (avoid redundant API calls)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_hash TEXT UNIQUE,
                    response_type TEXT,
                    response_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_note ON chat_history(note_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_hash ON ai_cache(input_hash)")

                conn.commit()
                logger.info("Database schema initialized.")
        except Exception as e:
            logger.error(f"Failed to init DB: {e}")

    @contextmanager
    def get_cursor(self):
        """Context manager for database transactions."""
        conn = self._get_conn()
        try:
            yield conn.cursor()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a query immediately."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

# Global Instance
_db_manager = None

def get_db():
    global _db_manager
    if not _db_manager:
        _db_manager = DatabaseManager()
    return _db_manager

def init_db():
    """Ensure DB is ready."""
    get_db()
