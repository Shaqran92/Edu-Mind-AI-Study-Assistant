"""
Advanced Analytics Service
Tracks learning progress, study patterns, and performance metrics.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from utils.logger import get_logger

logger = get_logger("advanced_analytics")


class StudySession:
    """Represents a single study session."""
    
    def __init__(self, session_id: str, subject: str, start_time: datetime = None):
        self.session_id = session_id
        self.subject = subject
        self.start_time = start_time or datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration_minutes: int = 0
        
        self.content_processed: int = 0  # Characters processed
        self.summaries_created: int = 0
        self.flashcards_created: int = 0
        self.quizzes_taken: int = 0
        self.quiz_scores: List[float] = []
        self.ai_provider: str = "offline"
        
    def end_session(self) -> None:
        """End the study session and calculate duration."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self.duration_minutes = int(duration / 60)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "subject": self.subject,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "content_processed": self.content_processed,
            "summaries_created": self.summaries_created,
            "flashcards_created": self.flashcards_created,
            "quizzes_taken": self.quizzes_taken,
            "quiz_scores": self.quiz_scores,
            "average_score": sum(self.quiz_scores) / len(self.quiz_scores) if self.quiz_scores else 0,
            "ai_provider": self.ai_provider,
        }


class AdvancedAnalytics:
    """
    Advanced analytics system for tracking learning progress.
    
    Features:
    - Session tracking
    - Performance metrics
    - Learning patterns
    - Productivity insights
    - Spaced repetition recommendations
    """
    
    def __init__(self, data_dir: str = "data/analytics"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[StudySession] = None
        self.sessions_file = self.data_dir / "sessions.json"
        self.sessions: List[Dict[str, Any]] = self._load_sessions()
    
    def _load_sessions(self) -> List[Dict[str, Any]]:
        """Load existing sessions from disk."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
        return []
    
    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def start_session(self, subject: str, ai_provider: str = "offline") -> str:
        """
        Start a new study session.
        
        Args:
            subject: Subject or topic being studied
            ai_provider: AI provider being used (openai, gemini, offline)
        
        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = StudySession(session_id, subject)
        self.current_session.ai_provider = ai_provider
        logger.info(f"Started session: {session_id} for {subject}")
        return session_id
    
    def end_session(self) -> Dict[str, Any]:
        """
        End the current study session.
        
        Returns:
            Session summary
        """
        if not self.current_session:
            return {}
        
        self.current_session.end_session()
        session_dict = self.current_session.to_dict()
        self.sessions.append(session_dict)
        self._save_sessions()
        
        logger.info(f"Ended session: {self.current_session.session_id}")
        logger.info(f"Duration: {self.current_session.duration_minutes} minutes")
        logger.info(f"Content processed: {self.current_session.content_processed} chars")
        
        return session_dict
    
    def record_content_processed(self, content_length: int) -> None:
        """Record content processed in current session."""
        if self.current_session:
            self.current_session.content_processed += content_length
    
    def record_summary_created(self) -> None:
        """Record summary creation in current session."""
        if self.current_session:
            self.current_session.summaries_created += 1
    
    def record_flashcards_created(self, count: int) -> None:
        """Record flashcard creation in current session."""
        if self.current_session:
            self.current_session.flashcards_created += count
    
    def record_quiz_taken(self, score: float) -> None:
        """
        Record a quiz session.
        
        Args:
            score: Quiz score (0-100)
        """
        if self.current_session:
            self.current_session.quizzes_taken += 1
            self.current_session.quiz_scores.append(score)
    
    def get_session_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get statistics for the past N days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Statistics dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sessions = []
        
        for session in self.sessions:
            session_time = datetime.fromisoformat(session["start_time"])
            if session_time >= cutoff_date:
                recent_sessions.append(session)
        
        if not recent_sessions:
            return {
                "total_sessions": 0,
                "total_study_minutes": 0,
                "average_session_minutes": 0,
                "total_content_processed": 0,
                "total_summaries": 0,
                "total_flashcards": 0,
                "total_quizzes": 0,
                "average_quiz_score": 0,
            }
        
        return {
            "total_sessions": len(recent_sessions),
            "total_study_minutes": sum(s.get("duration_minutes", 0) for s in recent_sessions),
            "average_session_minutes": sum(s.get("duration_minutes", 0) for s in recent_sessions) // len(recent_sessions),
            "total_content_processed": sum(s.get("content_processed", 0) for s in recent_sessions),
            "total_summaries": sum(s.get("summaries_created", 0) for s in recent_sessions),
            "total_flashcards": sum(s.get("flashcards_created", 0) for s in recent_sessions),
            "total_quizzes": sum(s.get("quizzes_taken", 0) for s in recent_sessions),
            "average_quiz_score": sum(
                s.get("average_score", 0) 
                for s in recent_sessions 
                if s.get("quizzes_taken", 0) > 0
            ) / len([s for s in recent_sessions if s.get("quizzes_taken", 0) > 0]) if any(s.get("quizzes_taken", 0) > 0 for s in recent_sessions) else 0,
            "subjects_studied": list(set(s.get("subject") for s in recent_sessions)),
        }
    
    def get_learning_patterns(self) -> Dict[str, Any]:
        """Analyze learning patterns."""
        if not self.sessions:
            return {}
        
        # Peak study times
        hour_distribution = defaultdict(int)
        subject_distribution = defaultdict(int)
        provider_distribution = defaultdict(int)
        
        for session in self.sessions[-30:]:  # Last 30 sessions
            start_time = datetime.fromisoformat(session["start_time"])
            hour_distribution[start_time.hour] += 1
            subject_distribution[session.get("subject", "unknown")] += 1
            provider_distribution[session.get("ai_provider", "offline")] += 1
        
        return {
            "peak_study_hour": max(hour_distribution, key=hour_distribution.get) if hour_distribution else None,
            "favorite_subjects": dict(sorted(
                subject_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]),
            "preferred_ai_provider": max(provider_distribution, key=provider_distribution.get) if provider_distribution else "offline",
            "total_sessions_tracked": len(self.sessions),
        }
    
    def get_recommendations(self) -> List[str]:
        """Get personalized learning recommendations."""
        recommendations = []
        
        stats = self.get_session_stats(days=7)
        patterns = self.get_learning_patterns()
        
        # Check study consistency
        if stats.get("total_sessions", 0) < 3:
            recommendations.append("💡 Try studying 3+ times per week for better retention")
        
        # Check average score
        avg_score = stats.get("average_quiz_score", 0)
        if 0 < avg_score < 70:
            recommendations.append("📚 Your quiz scores are improving! Review key concepts for better results")
        elif avg_score >= 85:
            recommendations.append("🎉 Great performance! Try more challenging topics")
        
        # Check session length
        avg_session = stats.get("average_session_minutes", 0)
        if 0 < avg_session < 15:
            recommendations.append("⏱️ Try longer study sessions (30-45 minutes) for deeper understanding")
        elif avg_session > 120:
            recommendations.append("🧠 Consider taking breaks during long sessions for better focus")
        
        # Check variety
        subjects = len(stats.get("subjects_studied", []))
        if subjects < 2:
            recommendations.append("🌍 Diversify your studies - try learning about different subjects")
        
        return recommendations or ["✅ Keep up the great work!"]


# Global analytics instance
_analytics_instance = None


def get_analytics() -> AdvancedAnalytics:
    """Get the global analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AdvancedAnalytics()
    return _analytics_instance
