# core/study_planner.py
"""
AI-powered study planner for EduMind.
Creates personalized study schedules based on goals and deadlines.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict
from enum import Enum
import json
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("study_planner")


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


@dataclass
class StudyGoal:
    """Represents a study goal with deadline."""
    id: str
    title: str
    description: str
    deadline: datetime
    priority: Priority
    estimated_hours: float
    hours_completed: float = 0.0
    status: TaskStatus = TaskStatus.NOT_STARTED
    subtasks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def progress_percent(self) -> float:
        if self.estimated_hours == 0:
            return 100.0 if self.status == TaskStatus.COMPLETED else 0.0
        return min(100, (self.hours_completed / self.estimated_hours) * 100)
    
    @property
    def days_until_deadline(self) -> int:
        return (self.deadline.date() - date.today()).days
    
    @property
    def is_overdue(self) -> bool:
        return self.deadline < datetime.now() and self.status != TaskStatus.COMPLETED
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat(),
            "priority": self.priority.value,
            "estimated_hours": self.estimated_hours,
            "hours_completed": self.hours_completed,
            "status": self.status.value,
            "subtasks": self.subtasks,
            "tags": self.tags,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StudyGoal':
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            deadline=datetime.fromisoformat(data["deadline"]),
            priority=Priority(data["priority"]),
            estimated_hours=data["estimated_hours"],
            hours_completed=data.get("hours_completed", 0),
            status=TaskStatus(data.get("status", "not_started")),
            subtasks=data.get("subtasks", []),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )


@dataclass
class StudySession:
    """Represents a scheduled study session."""
    goal_id: str
    start_time: datetime
    duration_minutes: int
    topic: str
    completed: bool = False
    notes: str = ""


class StudyPlanner:
    """
    AI-powered study planner service.
    
    Features:
    - Goal and deadline management
    - Smart schedule generation
    - Progress tracking
    - Daily/weekly views
    
    Example:
        >>> planner = StudyPlanner()
        >>> planner.add_goal("Math Exam", "Study for calculus final", 
        ...                  deadline=datetime(2024, 2, 1), hours=20)
        >>> schedule = planner.generate_schedule()
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.goals_file = self.data_dir / "study_goals.json"
        self.goals: List[StudyGoal] = []
        self._load_goals()
        logger.info(f"StudyPlanner initialized with {len(self.goals)} goals")
    
    def _load_goals(self):
        """Load goals from file."""
        try:
            if self.goals_file.exists():
                with open(self.goals_file) as f:
                    data = json.load(f)
                    self.goals = [StudyGoal.from_dict(g) for g in data.get("goals", [])]
        except Exception as e:
            logger.warning(f"Could not load goals: {e}")
    
    def _save_goals(self):
        """Save goals to file."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.goals_file, 'w') as f:
                json.dump({"goals": [g.to_dict() for g in self.goals]}, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save goals: {e}")
    
    def add_goal(
        self,
        title: str,
        description: str,
        deadline: datetime,
        estimated_hours: float,
        priority: Priority = Priority.MEDIUM,
        subtasks: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> StudyGoal:
        """Add a new study goal."""
        goal_id = f"goal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.goals)}"
        
        goal = StudyGoal(
            id=goal_id,
            title=title,
            description=description,
            deadline=deadline,
            priority=priority,
            estimated_hours=estimated_hours,
            subtasks=subtasks or [],
            tags=tags or []
        )
        
        self.goals.append(goal)
        self._save_goals()
        logger.info(f"Added goal: {title}")
        return goal
    
    def update_goal(self, goal_id: str, **updates) -> Optional[StudyGoal]:
        """Update an existing goal."""
        for goal in self.goals:
            if goal.id == goal_id:
                for key, value in updates.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)
                self._save_goals()
                return goal
        return None
    
    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal."""
        for i, goal in enumerate(self.goals):
            if goal.id == goal_id:
                del self.goals[i]
                self._save_goals()
                return True
        return False
    
    def log_study_time(self, goal_id: str, hours: float):
        """Log study time for a goal."""
        for goal in self.goals:
            if goal.id == goal_id:
                goal.hours_completed += hours
                if goal.status == TaskStatus.NOT_STARTED:
                    goal.status = TaskStatus.IN_PROGRESS
                if goal.hours_completed >= goal.estimated_hours:
                    goal.status = TaskStatus.COMPLETED
                self._save_goals()
                logger.info(f"Logged {hours}h for goal: {goal.title}")
                return
    
    def get_today_schedule(self) -> List[Dict]:
        """Get recommended study schedule for today."""
        today = date.today()
        schedule = []
        
        # Sort goals by priority and deadline
        active_goals = [g for g in self.goals if g.status != TaskStatus.COMPLETED]
        active_goals.sort(key=lambda g: (-g.priority.value, g.deadline))
        
        # Allocate time (assume 4-6 hours available)
        available_hours = 5
        allocated = 0
        
        for goal in active_goals:
            if allocated >= available_hours:
                break
            
            remaining_hours = goal.estimated_hours - goal.hours_completed
            days_left = max(1, goal.days_until_deadline)
            
            # Calculate recommended daily hours
            hours_per_day = remaining_hours / days_left
            hours_today = min(2, max(0.5, hours_per_day))  # 30 min to 2 hours per session
            
            if allocated + hours_today <= available_hours:
                schedule.append({
                    "goal": goal,
                    "hours": hours_today,
                    "priority": goal.priority.name,
                    "deadline": goal.deadline,
                    "progress": goal.progress_percent
                })
                allocated += hours_today
        
        return schedule
    
    def get_weekly_overview(self) -> Dict:
        """Get weekly study overview."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        # Goals due this week
        week_end = week_start + timedelta(days=6)
        due_this_week = [
            g for g in self.goals 
            if week_start <= g.deadline.date() <= week_end and g.status != TaskStatus.COMPLETED
        ]
        
        # Calculate total hours needed
        total_remaining = sum(g.estimated_hours - g.hours_completed for g in due_this_week)
        
        return {
            "goals_due": len(due_this_week),
            "hours_remaining": total_remaining,
            "hours_per_day": total_remaining / max(1, (week_end - today).days + 1),
            "overdue": len([g for g in self.goals if g.is_overdue]),
            "completed_this_week": len([
                g for g in self.goals 
                if g.status == TaskStatus.COMPLETED and 
                hasattr(g, 'completed_at') and 
                week_start <= getattr(g, 'completed_at', today).date() <= week_end
            ])
        }
    
    def get_smart_suggestions(self) -> List[str]:
        """Generate AI-powered study suggestions."""
        suggestions = []
        
        # Check for overdue goals
        overdue = [g for g in self.goals if g.is_overdue]
        if overdue:
            suggestions.append(f"⚠️ You have {len(overdue)} overdue goal(s). Consider adjusting deadlines or prioritizing these.")
        
        # Check for goals due soon
        urgent = [g for g in self.goals if 0 < g.days_until_deadline <= 3 and g.status != TaskStatus.COMPLETED]
        if urgent:
            suggestions.append(f"🚨 {len(urgent)} goal(s) due within 3 days. Focus on these today!")
        
        # Check for unbalanced workload
        weekly = self.get_weekly_overview()
        if weekly["hours_per_day"] > 4:
            suggestions.append("📈 Your workload is heavy this week. Consider extending some deadlines.")
        
        # Encourage consistency
        if not overdue and not urgent:
            suggestions.append("🎯 You're on track! Keep up the consistent study habits.")
        
        # Suggest breaks
        suggestions.append("💡 Remember to take regular breaks. Try the Pomodoro technique!")
        
        return suggestions
    
    def get_progress_summary(self) -> Dict:
        """Get overall progress summary."""
        total = len(self.goals)
        completed = len([g for g in self.goals if g.status == TaskStatus.COMPLETED])
        in_progress = len([g for g in self.goals if g.status == TaskStatus.IN_PROGRESS])
        overdue = len([g for g in self.goals if g.is_overdue])
        
        total_hours_estimated = sum(g.estimated_hours for g in self.goals)
        total_hours_completed = sum(g.hours_completed for g in self.goals)
        
        return {
            "total_goals": total,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total - completed - in_progress,
            "overdue": overdue,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "hours_estimated": total_hours_estimated,
            "hours_completed": total_hours_completed,
            "hours_progress": (total_hours_completed / total_hours_estimated * 100) if total_hours_estimated > 0 else 0
        }


# Global instance
_study_planner: Optional[StudyPlanner] = None

def get_study_planner() -> StudyPlanner:
    """Get the global study planner instance."""
    global _study_planner
    if _study_planner is None:
        _study_planner = StudyPlanner()
    return _study_planner
