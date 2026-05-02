# core/reports.py
"""
Weekly progress reporting for EduMind.
"""

from datetime import datetime
from typing import Dict

class ReportGenerator:
    """Generates study reports."""
    
    @staticmethod
    def generate_weekly_report(user_profile: Dict, stats: Dict) -> str:
        """
        Generate a text-based weekly report.
        """
        now = datetime.now()
        report = f"""
EduMind Weekly Progress Report
==============================
Date: {now.strftime("%Y-%m-%d")}
User: {user_profile.get('display_name', 'Student')}

SUMMARY
-------
Total XP Gained: {stats.get('xp', 0)}
Study Streak: {stats.get('streak', 0)} days
Focus Sessions: {stats.get('sessions_count', 0)}

DETAILED BREAKDOWN
------------------
• Flashcards Reviewed: {stats.get('cards_reviewed', 0)}
• Quizzes Completed: {stats.get('quizzes_completed', 0)}
• Study Time: {stats.get('study_minutes', 0)} minutes

RECOMMENDATIONS
---------------
Based on your activity, we recommend:
1. Review older flashcards to maintain retention.
2. Try a 25-minute focus session for your next topic.

Keep up the great work!
- Your EduMind AI
        """
        return report.strip()
