# core/services/session_tracker.py
"""
Study session tracking for analytics and progress monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

from utils.logger import get_logger
from utils.helpers import get_data_dir

logger = get_logger("session_tracker")


@dataclass
class StudySession:
    """Represents a single study session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    note_id: Optional[int] = None
    note_title: str = ""
    
    # Activity metrics
    flashcards_reviewed: int = 0
    flashcards_correct: int = 0
    quiz_questions: int = 0
    quiz_correct: int = 0
    summaries_generated: int = 0
    chat_messages: int = 0
    
    # Focus metrics
    is_active: bool = True
    breaks_taken: int = 0
    
    def __post_init__(self):
        if not self.session_id:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @property
    def duration(self) -> timedelta:
        """Get session duration."""
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return int(self.duration.total_seconds() / 60)
    
    @property
    def flashcard_accuracy(self) -> float:
        """Get flashcard accuracy percentage."""
        if self.flashcards_reviewed == 0:
            return 0.0
        return (self.flashcards_correct / self.flashcards_reviewed) * 100
    
    @property
    def quiz_accuracy(self) -> float:
        """Get quiz accuracy percentage."""
        if self.quiz_questions == 0:
            return 0.0
        return (self.quiz_correct / self.quiz_questions) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "note_id": self.note_id,
            "note_title": self.note_title,
            "flashcards_reviewed": self.flashcards_reviewed,
            "flashcards_correct": self.flashcards_correct,
            "quiz_questions": self.quiz_questions,
            "quiz_correct": self.quiz_correct,
            "summaries_generated": self.summaries_generated,
            "chat_messages": self.chat_messages,
            "breaks_taken": self.breaks_taken,
            "duration_minutes": self.duration_minutes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StudySession':
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            note_id=data.get("note_id"),
            note_title=data.get("note_title", ""),
            flashcards_reviewed=data.get("flashcards_reviewed", 0),
            flashcards_correct=data.get("flashcards_correct", 0),
            quiz_questions=data.get("quiz_questions", 0),
            quiz_correct=data.get("quiz_correct", 0),
            summaries_generated=data.get("summaries_generated", 0),
            chat_messages=data.get("chat_messages", 0),
            breaks_taken=data.get("breaks_taken", 0),
            is_active=False
        )


class SessionTracker:
    """
    Tracks study sessions and provides analytics.
    
    Example:
        >>> tracker = SessionTracker()
        >>> tracker.start_session(note_id=1, note_title="Biology Notes")
        >>> tracker.record_flashcard(correct=True)
        >>> tracker.end_session()
        >>> stats = tracker.get_weekly_stats()
    """
    
    def __init__(self):
        self._current_session: Optional[StudySession] = None
        self._sessions: List[StudySession] = []
        self._data_file = get_data_dir() / "sessions.json"
        self._load_sessions()
        logger.info("Session Tracker initialized")
    
    def _load_sessions(self):
        """Load session history from file."""
        try:
            if self._data_file.exists():
                with open(self._data_file, 'r') as f:
                    data = json.load(f)
                self._sessions = [StudySession.from_dict(s) for s in data.get("sessions", [])]
                logger.info(f"Loaded {len(self._sessions)} historical sessions")
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            self._sessions = []
    
    def _save_sessions(self):
        """Save session history to file."""
        try:
            data = {"sessions": [s.to_dict() for s in self._sessions[-100:]]}  # Keep last 100
            with open(self._data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    @property
    def current_session(self) -> Optional[StudySession]:
        return self._current_session
    
    @property
    def is_session_active(self) -> bool:
        return self._current_session is not None and self._current_session.is_active
    
    def start_session(self, note_id: Optional[int] = None, note_title: str = "") -> StudySession:
        """Start a new study session."""
        # End any existing session first
        if self._current_session and self._current_session.is_active:
            self.end_session()
        
        self._current_session = StudySession(
            session_id="",
            start_time=datetime.now(),
            note_id=note_id,
            note_title=note_title
        )
        
        logger.info(f"Started session {self._current_session.session_id}")
        return self._current_session
    
    def end_session(self) -> Optional[StudySession]:
        """End the current session and save it."""
        if not self._current_session:
            return None
        
        self._current_session.end_time = datetime.now()
        self._current_session.is_active = False
        
        # Only save if there was meaningful activity
        if (self._current_session.flashcards_reviewed > 0 or 
            self._current_session.quiz_questions > 0 or
            self._current_session.summaries_generated > 0 or
            self._current_session.duration_minutes >= 1):
            
            self._sessions.append(self._current_session)
            self._save_sessions()
            logger.info(f"Ended session {self._current_session.session_id}, "
                       f"duration: {self._current_session.duration_minutes}m")
        
        session = self._current_session
        self._current_session = None
        return session
    
    def record_flashcard(self, correct: bool):
        """Record a flashcard review."""
        if self._current_session:
            self._current_session.flashcards_reviewed += 1
            if correct:
                self._current_session.flashcards_correct += 1
    
    def record_quiz_answer(self, correct: bool):
        """Record a quiz answer."""
        if self._current_session:
            self._current_session.quiz_questions += 1
            if correct:
                self._current_session.quiz_correct += 1
    
    def record_summary(self):
        """Record a summary generation."""
        if self._current_session:
            self._current_session.summaries_generated += 1
    
    def record_chat_message(self):
        """Record a chat message."""
        if self._current_session:
            self._current_session.chat_messages += 1
    
    def record_break(self):
        """Record a break taken."""
        if self._current_session:
            self._current_session.breaks_taken += 1
    
    def get_today_stats(self) -> Dict[str, Any]:
        """Get today's study statistics."""
        today = datetime.now().date()
        today_sessions = [s for s in self._sessions if s.start_time.date() == today]
        
        if self._current_session:
            today_sessions.append(self._current_session)
        
        return self._aggregate_sessions(today_sessions)
    
    def get_weekly_stats(self) -> Dict[str, Any]:
        """Get this week's study statistics."""
        week_ago = datetime.now() - timedelta(days=7)
        week_sessions = [s for s in self._sessions if s.start_time >= week_ago]
        
        if self._current_session:
            week_sessions.append(self._current_session)
        
        stats = self._aggregate_sessions(week_sessions)
        
        # Add daily breakdown
        daily_minutes = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            day_sessions = [s for s in week_sessions if s.start_time.date() == date]
            daily_minutes[date.strftime("%a")] = sum(s.duration_minutes for s in day_sessions)
        
        stats["daily_minutes"] = daily_minutes
        return stats
    
    def get_streak(self) -> int:
        """Calculate current study streak in days."""
        if not self._sessions:
            return 0
        
        today = datetime.now().date()
        streak = 0
        current_date = today
        
        # Check if studied today (including current session)
        studied_today = (
            any(s.start_time.date() == today for s in self._sessions) or
            (self._current_session and self._current_session.start_time.date() == today)
        )
        
        if not studied_today:
            # Check if studied yesterday to not break streak
            yesterday = today - timedelta(days=1)
            if not any(s.start_time.date() == yesterday for s in self._sessions):
                return 0
            current_date = yesterday
        
        # Count consecutive days
        while True:
            if any(s.start_time.date() == current_date for s in self._sessions):
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _aggregate_sessions(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Aggregate statistics from multiple sessions."""
        if not sessions:
            return {
                "total_minutes": 0,
                "sessions_count": 0,
                "flashcards_reviewed": 0,
                "flashcards_accuracy": 0.0,
                "quiz_questions": 0,
                "quiz_accuracy": 0.0,
                "summaries_generated": 0,
                "chat_messages": 0
            }
        
        total_fc = sum(s.flashcards_reviewed for s in sessions)
        correct_fc = sum(s.flashcards_correct for s in sessions)
        total_quiz = sum(s.quiz_questions for s in sessions)
        correct_quiz = sum(s.quiz_correct for s in sessions)
        
        return {
            "total_minutes": sum(s.duration_minutes for s in sessions),
            "sessions_count": len(sessions),
            "flashcards_reviewed": total_fc,
            "flashcards_accuracy": (correct_fc / total_fc * 100) if total_fc else 0.0,
            "quiz_questions": total_quiz,
            "quiz_accuracy": (correct_quiz / total_quiz * 100) if total_quiz else 0.0,
            "summaries_generated": sum(s.summaries_generated for s in sessions),
            "chat_messages": sum(s.chat_messages for s in sessions)
        }


# Global tracker instance
_tracker: Optional[SessionTracker] = None

def get_tracker() -> SessionTracker:
    """Get the global session tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = SessionTracker()
    return _tracker
