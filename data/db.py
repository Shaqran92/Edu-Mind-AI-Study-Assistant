# data/db.py
import sqlite3
import os
from typing import Optional, Dict, Any, List
from config import settings
from utils import now_iso
import json


os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)

def get_conn():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        # Add mode, length, language columns to summaries table
        try:
            c.execute("ALTER TABLE summaries ADD COLUMN mode TEXT;")
            c.execute("ALTER TABLE summaries ADD COLUMN length TEXT;")
            c.execute("ALTER TABLE summaries ADD COLUMN language TEXT;")
        except sqlite3.OperationalError:
            # Columns likely already exist, ignore error
            pass
            
        c.execute("""
        CREATE TABLE IF NOT EXISTS notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, filepath TEXT, content TEXT, created_at TEXT
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS summaries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER,
            mode TEXT DEFAULT 'concise',
            length TEXT DEFAULT 'medium',
            language TEXT DEFAULT 'en',
            text TEXT, key_points TEXT, created_at TEXT,
            FOREIGN KEY(note_id) REFERENCES notes(id)
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS quizzes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_id INTEGER,
            quiz_json TEXT, created_at TEXT,
            FOREIGN KEY(summary_id) REFERENCES summaries(id)
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS flashcards(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_id INTEGER,
            cards_json TEXT, created_at TEXT,
            FOREIGN KEY(summary_id) REFERENCES summaries(id)
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS stats(
            id INTEGER PRIMARY KEY CHECK (id=1),
            total_notes INTEGER DEFAULT 0, total_quizzes INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, last_active TEXT
        );
        """)
        c.execute("INSERT OR IGNORE INTO stats(id) VALUES (1);")
        
        # Quiz History (persistent score tracking)
        c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_id INTEGER,
            score INTEGER,
            total_questions INTEGER,
            correct_answers INTEGER,
            details_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)
        
        # Study Sessions (for analytics & Pomodoro tracking)
        c.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            start_time TEXT DEFAULT (datetime('now')),
            duration_minutes INTEGER,
            focus_score INTEGER,
            notes TEXT
        );
        """)
        
        # Flashcard Reviews (spaced repetition tracking)
        c.execute("""
        CREATE TABLE IF NOT EXISTS flashcard_reviews(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flashcard_id INTEGER,
            card_index INTEGER,
            ease_factor REAL DEFAULT 2.5,
            interval_days INTEGER DEFAULT 1,
            repetitions INTEGER DEFAULT 0,
            next_review TEXT,
            last_reviewed TEXT
        );
        """)
        
        # Chat History (persistent AI conversations)
        c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)
        
        # AI Response Cache
        c.execute("""
        CREATE TABLE IF NOT EXISTS ai_cache(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_hash TEXT UNIQUE,
            response_type TEXT,
            response_text TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)
        
        # Performance indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_quiz_date ON quiz_history(created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON study_sessions(start_time)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_chat_note ON chat_history(note_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_cache_hash ON ai_cache(input_hash)")
        
        conn.commit()

def add_note(title: str, filepath: str, content: str) -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO notes(title, filepath, content, created_at) VALUES (?,?,?,?)",
                  (title, filepath, content, now_iso()))
        note_id = c.lastrowid
        c.execute("UPDATE stats SET total_notes = total_notes + 1 WHERE id=1")
        conn.commit()
        return note_id

def list_notes() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT id, title, created_at FROM notes ORDER BY id DESC").fetchall()

def get_note(note_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()

def create_new_quiz(summary_id: int, generator_func) -> List[Dict[str, Any]]:
    """
    Generates a NEW quiz every time it is called, without checking the cache.
    This ensures the user can always retry quiz generation.
    It returns the quiz data directly, without saving it.
    """
    with get_conn() as conn:
        # We still need the summary text to generate the quiz
        summary = conn.execute("SELECT text FROM summaries WHERE id=?", (summary_id,)).fetchone()
        if not summary or not summary['text']:
            print("   - ❌ Cannot generate quiz: Summary text not found in database.")
            return []

        # Call the AI generator function passed from the UI
        quiz_data = generator_func(summary["text"])
        
        # We will NOT save the quiz to the database here.
        # This forces regeneration on every button click.
        # We only update the stats.
        if quiz_data:
            conn.execute("UPDATE stats SET total_quizzes = total_quizzes + 1 WHERE id=1")
            conn.commit()
            print(f"   - ✅ Successfully generated a new quiz with {len(quiz_data)} questions.")
        
        return quiz_data

# ... (rest of db.py is largely unchanged but updated to use summary_id correctly) ...
def get_or_create_flashcards(summary_id: int, generator) -> sqlite3.Row:
    with get_conn() as conn:
        existing = conn.execute("SELECT * FROM flashcards WHERE summary_id=?", (summary_id,)).fetchone()
        if existing: return existing
        summary = conn.execute("SELECT * FROM summaries WHERE id=?", (summary_id,)).fetchone()
        cards = generator(summary["text"])
        c = conn.cursor()
        c.execute("INSERT INTO flashcards(summary_id, cards_json, created_at) VALUES (?,?,?)",
                  (summary_id, json.dumps(cards), now_iso()))
        fid = c.lastrowid
        conn.commit()
        return conn.execute("SELECT * FROM flashcards WHERE id=?", (fid,)).fetchone()

def get_or_create_quiz(summary_id: int, generator) -> sqlite3.Row:
    with get_conn() as conn:
        existing = conn.execute("SELECT * FROM quizzes WHERE summary_id=?", (summary_id,)).fetchone()
        if existing: return existing
        summary = conn.execute("SELECT * FROM summaries WHERE id=?", (summary_id,)).fetchone()
        quiz = generator(summary["text"])
        c = conn.cursor()
        c.execute("INSERT INTO quizzes(summary_id, quiz_json, created_at) VALUES (?,?,?)",
                  (summary_id, json.dumps(quiz), now_iso()))
        qid = c.lastrowid
        c.execute("UPDATE stats SET total_quizzes = total_quizzes + 1 WHERE id=1")
        conn.commit()
        return conn.execute("SELECT * FROM quizzes WHERE id=?", (qid,)).fetchone()

def get_stats():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM stats WHERE id=1").fetchone()

def add_xp(points: int):
    with get_conn() as conn:
        conn.execute("UPDATE stats SET xp = xp + ? WHERE id=1", (points,))
        conn.commit()