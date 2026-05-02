# core/analytics/study_analytics.py
"""
Study analytics service for generating insights and tracking progress.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import json

from utils.logger import get_logger
from utils.helpers import get_data_dir

logger = get_logger("analytics")


@dataclass
class StudyInsight:
    """A single insight or recommendation."""
    category: str       # 'strength', 'weakness', 'recommendation', 'milestone'
    icon: str           # Emoji icon
    title: str          # Short title
    description: str    # Detailed description
    metric: Optional[float] = None
    action: Optional[str] = None  # Suggested action


@dataclass
class TopicPerformance:
    """Performance metrics for a specific topic."""
    topic: str
    total_cards: int = 0
    mastered_cards: int = 0
    accuracy: float = 0.0
    avg_ease_factor: float = 2.5
    study_time_minutes: int = 0
    
    @property
    def mastery_rate(self) -> float:
        if self.total_cards == 0:
            return 0.0
        return (self.mastered_cards / self.total_cards) * 100


class StudyAnalytics:
    """
    Analytics service for generating study insights and progress reports.
    
    Features:
    - Strength/weakness identification
    - Study habit analysis
    - Progress tracking
    - Personalized recommendations
    
    Example:
        >>> analytics = StudyAnalytics()
        >>> insights = analytics.get_insights()
        >>> for insight in insights:
        >>>     print(f"{insight.icon} {insight.title}")
    """
    
    def __init__(self):
        self._data_file = get_data_dir() / "analytics.json"
        self._study_data: Dict[str, Any] = self._load_data()
        logger.info("StudyAnalytics initialized")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load analytics data from file."""
        try:
            if self._data_file.exists():
                with open(self._data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading analytics data: {e}")
        
        return {
            "sessions": [],
            "topic_performance": {},
            "daily_stats": {},
            "milestones": [],
            "last_updated": None
        }
    
    def _save_data(self):
        """Save analytics data to file."""
        try:
            self._study_data["last_updated"] = datetime.now().isoformat()
            with open(self._data_file, 'w') as f:
                json.dump(self._study_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving analytics data: {e}")
    
    def record_session(
        self,
        duration_minutes: int,
        flashcards_reviewed: int,
        flashcards_correct: int,
        quiz_score: Optional[float] = None,
        topics: Optional[List[str]] = None
    ):
        """Record a study session for analytics."""
        session = {
            "date": datetime.now().isoformat(),
            "duration": duration_minutes,
            "flashcards": flashcards_reviewed,
            "correct": flashcards_correct,
            "quiz_score": quiz_score,
            "topics": topics or []
        }
        
        self._study_data["sessions"].append(session)
        
        # Update daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self._study_data["daily_stats"]:
            self._study_data["daily_stats"][today] = {
                "total_minutes": 0,
                "cards_reviewed": 0,
                "cards_correct": 0
            }
        
        daily = self._study_data["daily_stats"][today]
        daily["total_minutes"] += duration_minutes
        daily["cards_reviewed"] += flashcards_reviewed
        daily["cards_correct"] += flashcards_correct
        
        # Check for milestones
        self._check_milestones()
        self._save_data()
    
    def record_topic_performance(
        self,
        topic: str,
        cards_reviewed: int,
        cards_correct: int,
        avg_ease: float
    ):
        """Record performance for a specific topic."""
        if topic not in self._study_data["topic_performance"]:
            self._study_data["topic_performance"][topic] = {
                "total_reviews": 0,
                "correct": 0,
                "ease_factors": []
            }
        
        tp = self._study_data["topic_performance"][topic]
        tp["total_reviews"] += cards_reviewed
        tp["correct"] += cards_correct
        tp["ease_factors"].append(avg_ease)
        
        # Keep only last 20 ease factors
        tp["ease_factors"] = tp["ease_factors"][-20:]
        self._save_data()
    
    def _check_milestones(self):
        """Check and record new milestones."""
        total_sessions = len(self._study_data["sessions"])
        total_cards = sum(s.get("flashcards", 0) for s in self._study_data["sessions"])
        
        milestones = self._study_data.get("milestones", [])
        achieved = set(milestones)
        
        new_milestones = []
        
        # Session milestones
        session_milestones = [10, 25, 50, 100, 250, 500]
        for m in session_milestones:
            key = f"sessions_{m}"
            if total_sessions >= m and key not in achieved:
                new_milestones.append({
                    "key": key,
                    "title": f"🎯 {m} Study Sessions",
                    "date": datetime.now().isoformat()
                })
                achieved.add(key)
        
        # Flashcard milestones
        card_milestones = [100, 500, 1000, 5000, 10000]
        for m in card_milestones:
            key = f"cards_{m}"
            if total_cards >= m and key not in achieved:
                new_milestones.append({
                    "key": key,
                    "title": f"📚 {m} Flashcards Reviewed",
                    "date": datetime.now().isoformat()
                })
                achieved.add(key)
        
        if new_milestones:
            self._study_data["milestones"] = list(achieved)
            logger.info(f"New milestones achieved: {[m['title'] for m in new_milestones]}")
    
    def get_insights(self) -> List[StudyInsight]:
        """Generate personalized study insights."""
        insights = []
        
        # Get recent data
        sessions = self._study_data.get("sessions", [])[-30:]  # Last 30 sessions
        daily_stats = self._study_data.get("daily_stats", {})
        topic_perf = self._study_data.get("topic_performance", {})
        
        if not sessions:
            insights.append(StudyInsight(
                category="recommendation",
                icon="🚀",
                title="Get Started",
                description="Start your first study session to see personalized insights!",
                action="Upload a document to begin"
            ))
            return insights
        
        # Calculate overall accuracy
        total_cards = sum(s.get("flashcards", 0) for s in sessions)
        total_correct = sum(s.get("correct", 0) for s in sessions)
        overall_accuracy = (total_correct / total_cards * 100) if total_cards > 0 else 0
        
        # Accuracy insight
        if overall_accuracy >= 90:
            insights.append(StudyInsight(
                category="strength",
                icon="🌟",
                title="Excellent Retention",
                description=f"Your accuracy is {overall_accuracy:.1f}%! You're retaining information exceptionally well.",
                metric=overall_accuracy
            ))
        elif overall_accuracy >= 70:
            insights.append(StudyInsight(
                category="strength",
                icon="👍",
                title="Good Progress",
                description=f"Your accuracy is {overall_accuracy:.1f}%. Keep it up!",
                metric=overall_accuracy
            ))
        else:
            insights.append(StudyInsight(
                category="weakness",
                icon="📈",
                title="Room for Improvement",
                description=f"Your accuracy is {overall_accuracy:.1f}%. Consider reviewing difficult cards more frequently.",
                metric=overall_accuracy,
                action="Focus on spaced repetition"
            ))
        
        # Study consistency
        week_dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        days_studied = sum(1 for d in week_dates if d in daily_stats)
        
        if days_studied >= 6:
            insights.append(StudyInsight(
                category="strength",
                icon="🔥",
                title="Amazing Consistency",
                description=f"You studied {days_studied} days this week! Your dedication is impressive.",
                metric=days_studied
            ))
        elif days_studied >= 4:
            insights.append(StudyInsight(
                category="strength",
                icon="💪",
                title="Good Habit",
                description=f"You studied {days_studied} days this week. Try to add one more day!",
                metric=days_studied
            ))
        else:
            insights.append(StudyInsight(
                category="recommendation",
                icon="📅",
                title="Build Consistency",
                description=f"You studied only {days_studied} days this week. Consistent daily study improves retention.",
                metric=days_studied,
                action="Set a daily study reminder"
            ))
        
        # Topic analysis
        if topic_perf:
            # Find strongest topic
            strongest = max(topic_perf.items(), 
                          key=lambda x: x[1].get("correct", 0) / max(x[1].get("total_reviews", 1), 1))
            strongest_acc = (strongest[1]["correct"] / strongest[1]["total_reviews"] * 100) if strongest[1]["total_reviews"] > 0 else 0
            
            insights.append(StudyInsight(
                category="strength",
                icon="⭐",
                title=f"Strong in: {strongest[0]}",
                description=f"You have {strongest_acc:.0f}% accuracy in this topic!",
                metric=strongest_acc
            ))
            
            # Find weakest topic
            if len(topic_perf) > 1:
                weakest = min(topic_perf.items(),
                            key=lambda x: x[1].get("correct", 0) / max(x[1].get("total_reviews", 1), 1))
                weakest_acc = (weakest[1]["correct"] / weakest[1]["total_reviews"] * 100) if weakest[1]["total_reviews"] > 0 else 0
                
                if weakest_acc < 70:
                    insights.append(StudyInsight(
                        category="weakness",
                        icon="📚",
                        title=f"Focus on: {weakest[0]}",
                        description=f"Your accuracy is {weakest_acc:.0f}% here. Consider extra review.",
                        metric=weakest_acc,
                        action=f"Review {weakest[0]} cards"
                    ))
        
        # Study time recommendation
        total_minutes = sum(s.get("duration", 0) for s in sessions)
        avg_session = total_minutes / len(sessions) if sessions else 0
        
        if avg_session < 15:
            insights.append(StudyInsight(
                category="recommendation",
                icon="⏰",
                title="Longer Sessions",
                description=f"Your average session is {avg_session:.0f} minutes. Try 25-minute Pomodoro sessions.",
                metric=avg_session,
                action="Try the Pomodoro timer"
            ))
        elif avg_session >= 45:
            insights.append(StudyInsight(
                category="recommendation",
                icon="☕",
                title="Take Breaks",
                description=f"Your average session is {avg_session:.0f} minutes. Remember to take breaks!",
                metric=avg_session
            ))
        
        return insights
    
    def get_weekly_report(self) -> Dict[str, Any]:
        """Generate a weekly summary report."""
        daily_stats = self._study_data.get("daily_stats", {})
        
        # Get last 7 days
        report = {
            "days": [],
            "total_minutes": 0,
            "total_cards": 0,
            "total_correct": 0,
            "streak": 0
        }
        
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_name = (datetime.now() - timedelta(days=i)).strftime("%a")
            
            if date in daily_stats:
                day_data = daily_stats[date]
                report["days"].append({
                    "date": date,
                    "day": day_name,
                    "minutes": day_data.get("total_minutes", 0),
                    "cards": day_data.get("cards_reviewed", 0),
                    "accuracy": (day_data.get("cards_correct", 0) / 
                               max(day_data.get("cards_reviewed", 1), 1) * 100)
                })
                report["total_minutes"] += day_data.get("total_minutes", 0)
                report["total_cards"] += day_data.get("cards_reviewed", 0)
                report["total_correct"] += day_data.get("cards_correct", 0)
            else:
                report["days"].append({
                    "date": date,
                    "day": day_name,
                    "minutes": 0,
                    "cards": 0,
                    "accuracy": 0
                })
        
        # Calculate streak
        today = datetime.now().date()
        streak = 0
        for i in range(365):  # Max 1 year
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in daily_stats:
                streak += 1
            else:
                break
        
        report["streak"] = streak
        report["overall_accuracy"] = (report["total_correct"] / 
                                     max(report["total_cards"], 1) * 100)
        
        return report
    
    def get_topic_rankings(self) -> List[TopicPerformance]:
        """Get topics ranked by performance."""
        topic_perf = self._study_data.get("topic_performance", {})
        
        rankings = []
        for topic, data in topic_perf.items():
            total = data.get("total_reviews", 0)
            correct = data.get("correct", 0)
            ease_factors = data.get("ease_factors", [2.5])
            
            rankings.append(TopicPerformance(
                topic=topic,
                total_cards=total,
                mastered_cards=correct,
                accuracy=(correct / total * 100) if total > 0 else 0,
                avg_ease_factor=sum(ease_factors) / len(ease_factors) if ease_factors else 2.5
            ))
        
        # Sort by accuracy (descending)
        rankings.sort(key=lambda x: x.accuracy, reverse=True)
        return rankings


# Global instance
_analytics: Optional[StudyAnalytics] = None

def get_analytics() -> StudyAnalytics:
    """Get the global analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = StudyAnalytics()
    return _analytics
