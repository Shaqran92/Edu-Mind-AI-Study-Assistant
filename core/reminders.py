# core/reminders.py
"""
Advanced study reminder system for EduMind.
Supports recurring reminders, spaced repetition alerts, and break notifications.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field

from utils.logger import get_logger

logger = get_logger("reminders")

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

@dataclass
class Reminder:
    id: str
    time: str  # HH:MM format
    days: List[int]  # 0=Mon, 6=Sun
    message: str
    enabled: bool = True
    reminder_type: str = "study"  # "study", "break", "review", "custom"
    repeat: bool = True
    created_at: str = ""
    last_triggered: str = ""

    def get_days_display(self) -> str:
        if len(self.days) == 7:
            return "Every day"
        if self.days == [0, 1, 2, 3, 4]:
            return "Weekdays"
        if self.days == [5, 6]:
            return "Weekends"
        return ", ".join(DAY_NAMES[d] for d in sorted(self.days))

    def get_type_emoji(self) -> str:
        return {"study": "📚", "break": "☕", "review": "🔄", "custom": "🔔"}.get(self.reminder_type, "🔔")


class ReminderService:
    def __init__(self, data_file="reminders.json"):
        self.data_file = data_file
        self.reminders: List[Reminder] = []
        self._load()

    def _load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.reminders = []
                    for r in data:
                        try:
                            self.reminders.append(Reminder(**r))
                        except TypeError:
                            # Handle old format without new fields
                            self.reminders.append(Reminder(
                                id=r.get('id', str(uuid.uuid4())),
                                time=r.get('time', '09:00'),
                                days=r.get('days', [0,1,2,3,4]),
                                message=r.get('message', 'Study time!'),
                                enabled=r.get('enabled', True)
                            ))
            except Exception as e:
                logger.error(f"Failed to load reminders: {e}")

    def save(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump([asdict(r) for r in self.reminders], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save reminders: {e}")

    def add_reminder(self, time_str: str, days: List[int], message: str,
                     reminder_type: str = "study") -> Reminder:
        rem = Reminder(
            id=str(uuid.uuid4()),
            time=time_str,
            days=days,
            message=message,
            reminder_type=reminder_type,
            created_at=datetime.now().isoformat()
        )
        self.reminders.append(rem)
        self.save()
        return rem

    def remove_reminder(self, reminder_id: str) -> bool:
        before = len(self.reminders)
        self.reminders = [r for r in self.reminders if r.id != reminder_id]
        if len(self.reminders) < before:
            self.save()
            return True
        return False

    def toggle_reminder(self, reminder_id: str) -> Optional[bool]:
        for r in self.reminders:
            if r.id == reminder_id:
                r.enabled = not r.enabled
                self.save()
                return r.enabled
        return None

    def update_reminder(self, reminder_id: str, **kwargs) -> bool:
        for r in self.reminders:
            if r.id == reminder_id:
                for key, value in kwargs.items():
                    if hasattr(r, key):
                        setattr(r, key, value)
                self.save()
                return True
        return False

    def check_reminders(self) -> List[Reminder]:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.weekday()

        triggered = []
        for r in self.reminders:
            if r.enabled and r.time == current_time and current_day in r.days:
                # Prevent double-triggering within same minute
                if r.last_triggered != current_time + "_" + now.strftime("%Y-%m-%d"):
                    r.last_triggered = current_time + "_" + now.strftime("%Y-%m-%d")
                    triggered.append(r)

        if triggered:
            self.save()
        return triggered

    def get_upcoming(self, count: int = 5) -> List[Dict]:
        """Get next upcoming reminders."""
        now = datetime.now()
        upcoming = []
        for r in self.reminders:
            if not r.enabled:
                continue
            for offset in range(7):
                check_day = (now.weekday() + offset) % 7
                if check_day in r.days:
                    h, m = map(int, r.time.split(':'))
                    next_time = now.replace(hour=h, minute=m, second=0) + timedelta(days=offset)
                    if next_time > now:
                        upcoming.append({
                            "reminder": r,
                            "next_time": next_time,
                            "display": f"{r.get_type_emoji()} {r.message} — {next_time.strftime('%a %H:%M')}"
                        })
                        break
        upcoming.sort(key=lambda x: x['next_time'])
        return upcoming[:count]

    def add_preset(self, preset: str) -> Reminder:
        """Add a preset reminder configuration."""
        presets = {
            "morning_study": ("08:00", [0,1,2,3,4], "🌅 Morning study session!", "study"),
            "afternoon_review": ("14:00", [0,1,2,3,4], "📖 Time for afternoon review!", "review"),
            "evening_flashcards": ("19:00", [0,1,2,3,4,5,6], "🃏 Review your flashcards!", "review"),
            "break_reminder": ("10:30", [0,1,2,3,4], "☕ Take a short break!", "break"),
            "weekend_study": ("10:00", [5,6], "📚 Weekend study session!", "study"),
        }
        if preset in presets:
            t, d, m, rt = presets[preset]
            return self.add_reminder(t, d, m, rt)
        return self.add_reminder("09:00", [0,1,2,3,4], "Study time!", "study")


_reminder_service = None
def get_reminder_service():
    global _reminder_service
    if not _reminder_service:
        _reminder_service = ReminderService()
    return _reminder_service
