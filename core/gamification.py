# core/gamification.py
"""
Gamification system for EduMind.
Provides XP, levels, achievements, and streaks to motivate learning.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("gamification")


class AchievementType(Enum):
    """Types of achievements."""
    STREAK = "streak"
    CARDS_REVIEWED = "cards_reviewed"
    QUIZZES_COMPLETED = "quizzes_completed"
    PERFECT_QUIZ = "perfect_quiz"
    STUDY_TIME = "study_time"
    NOTES_CREATED = "notes_created"
    LEVEL_UP = "level_up"


@dataclass
class Achievement:
    """Represents an unlockable achievement."""
    id: str
    name: str
    description: str
    icon: str
    xp_reward: int
    requirement: int
    type: AchievementType
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "xp_reward": self.xp_reward,
            "requirement": self.requirement,
            "type": self.type.value,
            "unlocked": self.unlocked,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Achievement':
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            icon=data["icon"],
            xp_reward=data["xp_reward"],
            requirement=data["requirement"],
            type=AchievementType(data["type"]),
            unlocked=data.get("unlocked", False),
            unlocked_at=datetime.fromisoformat(data["unlocked_at"]) if data.get("unlocked_at") else None
        )


# Default achievements
DEFAULT_ACHIEVEMENTS = [
    Achievement("first_steps", "First Steps", "Complete your first study session", "🎯", 50, 1, AchievementType.CARDS_REVIEWED),
    Achievement("card_novice", "Card Novice", "Review 50 flashcards", "📚", 100, 50, AchievementType.CARDS_REVIEWED),
    Achievement("card_master", "Card Master", "Review 500 flashcards", "🏆", 500, 500, AchievementType.CARDS_REVIEWED),
    Achievement("card_legend", "Card Legend", "Review 2000 flashcards", "👑", 1000, 2000, AchievementType.CARDS_REVIEWED),
    
    Achievement("quiz_starter", "Quiz Starter", "Complete 5 quizzes", "✏️", 75, 5, AchievementType.QUIZZES_COMPLETED),
    Achievement("quiz_champion", "Quiz Champion", "Complete 50 quizzes", "🎓", 300, 50, AchievementType.QUIZZES_COMPLETED),
    Achievement("perfectionist", "Perfectionist", "Get 100% on a quiz", "💯", 150, 1, AchievementType.PERFECT_QUIZ),
    Achievement("perfect_streak", "Perfect Streak", "Get 100% on 5 quizzes", "⭐", 500, 5, AchievementType.PERFECT_QUIZ),
    
    Achievement("streak_3", "On Fire", "Maintain a 3-day streak", "🔥", 100, 3, AchievementType.STREAK),
    Achievement("streak_7", "Week Warrior", "Maintain a 7-day streak", "💪", 250, 7, AchievementType.STREAK),
    Achievement("streak_30", "Monthly Master", "Maintain a 30-day streak", "🌟", 1000, 30, AchievementType.STREAK),
    Achievement("streak_100", "Century Legend", "Maintain a 100-day streak", "🏅", 5000, 100, AchievementType.STREAK),
    
    Achievement("dedicated_1h", "Dedicated Learner", "Study for 1 hour total", "⏰", 100, 60, AchievementType.STUDY_TIME),
    Achievement("dedicated_10h", "Study Enthusiast", "Study for 10 hours total", "📖", 500, 600, AchievementType.STUDY_TIME),
    Achievement("dedicated_100h", "Knowledge Seeker", "Study for 100 hours total", "🧠", 2000, 6000, AchievementType.STUDY_TIME),
    
    Achievement("note_creator", "Note Creator", "Create 10 notes", "📝", 100, 10, AchievementType.NOTES_CREATED),
    Achievement("library_builder", "Library Builder", "Create 50 notes", "🏛️", 400, 50, AchievementType.NOTES_CREATED),
]


@dataclass
class UserProgress:
    """Tracks user's gamification progress."""
    xp: int = 0
    level: int = 1
    total_cards_reviewed: int = 0
    total_quizzes_completed: int = 0
    perfect_quizzes: int = 0
    total_study_minutes: int = 0
    notes_created: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    last_study_date: Optional[datetime] = None
    achievements: List[Achievement] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "xp": self.xp,
            "level": self.level,
            "total_cards_reviewed": self.total_cards_reviewed,
            "total_quizzes_completed": self.total_quizzes_completed,
            "perfect_quizzes": self.perfect_quizzes,
            "total_study_minutes": self.total_study_minutes,
            "notes_created": self.notes_created,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "last_study_date": self.last_study_date.isoformat() if self.last_study_date else None,
            "achievements": [a.to_dict() for a in self.achievements]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProgress':
        achievements = [Achievement.from_dict(a) for a in data.get("achievements", [])]
        return cls(
            xp=data.get("xp", 0),
            level=data.get("level", 1),
            total_cards_reviewed=data.get("total_cards_reviewed", 0),
            total_quizzes_completed=data.get("total_quizzes_completed", 0),
            perfect_quizzes=data.get("perfect_quizzes", 0),
            total_study_minutes=data.get("total_study_minutes", 0),
            notes_created=data.get("notes_created", 0),
            current_streak=data.get("current_streak", 0),
            longest_streak=data.get("longest_streak", 0),
            last_study_date=datetime.fromisoformat(data["last_study_date"]) if data.get("last_study_date") else None,
            achievements=achievements
        )


class GamificationService:
    """
    Service for managing user gamification.
    
    Example:
        >>> game = GamificationService()
        >>> game.award_xp(50, "Completed flashcard review")
        >>> game.record_cards_reviewed(10)
    """
    
    # XP required per level (exponential scaling)
    @staticmethod
    def xp_for_level(level: int) -> int:
        return int(100 * (level ** 1.5))
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.progress_file = self.data_dir / "user_progress.json"
        self.progress = self._load_progress()
        
        # Initialize default achievements if empty
        if not self.progress.achievements:
            self.progress.achievements = [
                Achievement(a.id, a.name, a.description, a.icon, 
                           a.xp_reward, a.requirement, a.type)
                for a in DEFAULT_ACHIEVEMENTS
            ]
        
        logger.info(f"GamificationService initialized - Level {self.progress.level}, XP: {self.progress.xp}")
    
    def _load_progress(self) -> UserProgress:
        """Load user progress from file."""
        try:
            if self.progress_file.exists():
                with open(self.progress_file) as f:
                    return UserProgress.from_dict(json.load(f))
        except Exception as e:
            logger.warning(f"Could not load progress: {e}")
        return UserProgress()
    
    def _save_progress(self):
        """Save user progress to file."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save progress: {e}")
    
    def award_xp(self, amount: int, reason: str = "") -> Optional[int]:
        """
        Award XP to the user.
        
        Returns:
            New level if user leveled up, None otherwise
        """
        old_level = self.progress.level
        self.progress.xp += amount
        logger.info(f"Awarded {amount} XP: {reason}")
        
        # Check for level up
        while self.progress.xp >= self.xp_for_level(self.progress.level):
            self.progress.xp -= self.xp_for_level(self.progress.level)
            self.progress.level += 1
            logger.info(f"Level up! Now level {self.progress.level}")
        
        self._save_progress()
        
        if self.progress.level > old_level:
            return self.progress.level
        return None
    
    def record_study_session(self, minutes: int):
        """Record a study session and update streak."""
        today = datetime.now().date()
        
        # Update streak
        if self.progress.last_study_date:
            last_date = self.progress.last_study_date.date()
            if last_date == today - timedelta(days=1):
                # Consecutive day
                self.progress.current_streak += 1
                if self.progress.current_streak > self.progress.longest_streak:
                    self.progress.longest_streak = self.progress.current_streak
            elif last_date != today:
                # Streak broken
                self.progress.current_streak = 1
        else:
            self.progress.current_streak = 1
        
        self.progress.last_study_date = datetime.now()
        self.progress.total_study_minutes += minutes
        
        # Award XP for study time
        xp_earned = minutes * 2  # 2 XP per minute
        self.award_xp(xp_earned, f"Study session ({minutes} min)")
        
        # Check streak achievements
        self._check_achievements(AchievementType.STREAK, self.progress.current_streak)
        self._check_achievements(AchievementType.STUDY_TIME, self.progress.total_study_minutes)
    
    def record_cards_reviewed(self, count: int):
        """Record flashcard reviews."""
        self.progress.total_cards_reviewed += count
        self.award_xp(count * 5, f"Reviewed {count} cards")
        self._check_achievements(AchievementType.CARDS_REVIEWED, self.progress.total_cards_reviewed)
    
    def record_quiz_completed(self, score_percent: float):
        """Record quiz completion."""
        self.progress.total_quizzes_completed += 1
        
        # Bonus XP for high scores
        base_xp = 25
        if score_percent == 100:
            self.progress.perfect_quizzes += 1
            self.award_xp(base_xp * 2, "Perfect quiz score!")
            self._check_achievements(AchievementType.PERFECT_QUIZ, self.progress.perfect_quizzes)
        elif score_percent >= 80:
            self.award_xp(int(base_xp * 1.5), f"Quiz completed ({score_percent:.0f}%)")
        else:
            self.award_xp(base_xp, f"Quiz completed ({score_percent:.0f}%)")
        
        self._check_achievements(AchievementType.QUIZZES_COMPLETED, self.progress.total_quizzes_completed)
    
    def record_note_created(self):
        """Record note creation."""
        self.progress.notes_created += 1
        self.award_xp(10, "Created note")
        self._check_achievements(AchievementType.NOTES_CREATED, self.progress.notes_created)
    
    def _check_achievements(self, achievement_type: AchievementType, current_value: int) -> List[Achievement]:
        """Check and unlock any new achievements."""
        newly_unlocked = []
        
        for achievement in self.progress.achievements:
            if achievement.type == achievement_type and not achievement.unlocked:
                if current_value >= achievement.requirement:
                    achievement.unlocked = True
                    achievement.unlocked_at = datetime.now()
                    newly_unlocked.append(achievement)
                    self.award_xp(achievement.xp_reward, f"Achievement: {achievement.name}")
                    logger.info(f"Achievement unlocked: {achievement.name}")
        
        if newly_unlocked:
            self._save_progress()
        
        return newly_unlocked
    
    def get_level_progress(self) -> tuple:
        """
        Get current level progress.
        
        Returns:
            (current_xp, xp_needed, progress_percent)
        """
        xp_needed = self.xp_for_level(self.progress.level)
        progress = (self.progress.xp / xp_needed) * 100 if xp_needed > 0 else 100
        return (self.progress.xp, xp_needed, progress)
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get list of unlocked achievements."""
        return [a for a in self.progress.achievements if a.unlocked]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """Get list of locked achievements."""
        return [a for a in self.progress.achievements if not a.unlocked]
    
    def get_stats_summary(self) -> Dict:
        """Get a summary of user stats for display."""
        xp, xp_needed, progress = self.get_level_progress()
        return {
            "level": self.progress.level,
            "xp": xp,
            "xp_needed": xp_needed,
            "level_progress": progress,
            "total_xp": sum(self.xp_for_level(l) for l in range(1, self.progress.level)) + xp,
            "current_streak": self.progress.current_streak,
            "longest_streak": self.progress.longest_streak,
            "cards_reviewed": self.progress.total_cards_reviewed,
            "quizzes_completed": self.progress.total_quizzes_completed,
            "study_hours": self.progress.total_study_minutes / 60,
            "achievements_unlocked": len(self.get_unlocked_achievements()),
            "achievements_total": len(self.progress.achievements)
        }


# Global instance
_gamification_service: Optional[GamificationService] = None

def get_gamification_service() -> GamificationService:
    """Get the global gamification service instance."""
    global _gamification_service
    if _gamification_service is None:
        _gamification_service = GamificationService()
    return _gamification_service
