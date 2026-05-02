# ui/widgets/smart_dashboard.py
"""
Smart Study Dashboard widget for EduMind.
Shows today's tasks, streak, and AI-powered suggestions.
"""

from typing import Optional, List, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from utils.logger import get_logger

logger = get_logger("smart_dashboard")


class StatCard(QFrame):
    """A card displaying a single statistic."""
    
    def __init__(
        self,
        icon: str,
        title: str,
        value: str,
        subtitle: str = "",
        color: str = "#667eea",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._setup_ui(icon, title, value, subtitle, color)
    
    def _setup_ui(self, icon: str, title: str, value: str, subtitle: str, color: str):
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self._lighten(color)});
                border-radius: 15px;
                padding: 20px;
            }}
        """)
        self.setMinimumSize(200, 120)
        
        layout = QVBoxLayout(self)
        
        # Icon and title row
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 12px; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        # Value
        self._value_label = QLabel(value)
        self._value_label.setStyleSheet("color: white; font-size: 32px; font-weight: bold; background: transparent;")
        layout.addWidget(self._value_label)
        
        # Subtitle
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px; background: transparent;")
            layout.addWidget(sub_label)
    
    def _lighten(self, hex_color: str) -> str:
        """Lighten a hex color."""
        c = hex_color.lstrip('#')
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        lighter = tuple(min(255, int(v + (255 - v) * 0.3)) for v in rgb)
        return f"#{lighter[0]:02x}{lighter[1]:02x}{lighter[2]:02x}"
    
    def update_value(self, value: str, subtitle: str = ""):
        """Update the displayed value."""
        self._value_label.setText(value)


class TaskItem(QFrame):
    """A single task/goal item in the dashboard."""
    
    clicked = pyqtSignal(str)  # Emits goal ID
    
    def __init__(
        self,
        goal_id: str,
        title: str,
        hours: float,
        priority: str,
        deadline: str,
        progress: float,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.goal_id = goal_id
        self._setup_ui(title, hours, priority, deadline, progress)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_ui(self, title: str, hours: float, priority: str, deadline: str, progress: float):
        priority_colors = {
            "LOW": "#48bb78",
            "MEDIUM": "#4299e1",
            "HIGH": "#ed8936",
            "CRITICAL": "#f56565"
        }
        color = priority_colors.get(priority, "#4299e1")
        
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid #e2e8f0;
                border-left: 4px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
            QFrame:hover {{
                background: #f7fafc;
                border-color: {color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title row
        title_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #2d3748; font-size: 14px;")
        title_layout.addWidget(title_label)
        
        priority_badge = QLabel(priority)
        priority_badge.setStyleSheet(f"""
            background: {color}20;
            color: {color};
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        """)
        title_layout.addWidget(priority_badge)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Details row
        details = QLabel(f"⏱️ {hours:.1f}h today  •  📅 {deadline}")
        details.setStyleSheet("color: #718096; font-size: 12px;")
        layout.addWidget(details)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setValue(int(progress))
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: #e2e8f0;
                border: none;
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(progress_bar)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.goal_id)


class SmartDashboardWidget(QWidget):
    """
    Smart dashboard showing study overview and recommendations.
    
    Features:
    - Today's study schedule
    - Stats overview (streak, XP, cards due)
    - AI-powered suggestions
    - Quick action buttons
    """
    
    start_focus_clicked = pyqtSignal()
    view_analytics_clicked = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        greeting = QLabel(self._get_greeting())
        greeting.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a202c;")
        header.addWidget(greeting)
        header.addStretch()
        
        # Quick actions
        focus_btn = QPushButton("🎯 Start Focus")
        focus_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        focus_btn.clicked.connect(self.start_focus_clicked.emit)
        header.addWidget(focus_btn)
        layout.addLayout(header)
        
        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self._streak_card = StatCard("🔥", "Study Streak", "0 days", "Keep it up!", "#ed8936")
        stats_layout.addWidget(self._streak_card)
        
        self._xp_card = StatCard("⭐", "Total XP", "0", "Level 1", "#667eea")
        stats_layout.addWidget(self._xp_card)
        
        self._cards_card = StatCard("📚", "Cards Due", "0", "Ready to review", "#48bb78")
        stats_layout.addWidget(self._cards_card)
        
        self._quiz_card = StatCard("✅", "Quizzes", "0", "Completed", "#4299e1")
        stats_layout.addWidget(self._quiz_card)
        
        layout.addLayout(stats_layout)
        
        # Main content split
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Today's tasks
        tasks_frame = QFrame()
        tasks_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 15px;
            }
        """)
        tasks_layout = QVBoxLayout(tasks_frame)
        tasks_layout.setContentsMargins(20, 20, 20, 20)
        
        tasks_header = QLabel("📋 Today's Study Plan")
        tasks_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d3748;")
        tasks_layout.addWidget(tasks_header)
        
        self._tasks_container = QVBoxLayout()
        self._tasks_container.setSpacing(10)
        tasks_layout.addLayout(self._tasks_container)
        
        # Placeholder
        no_tasks = QLabel("No study sessions scheduled for today.\nAdd goals in the Study Planner!")
        no_tasks.setStyleSheet("color: #718096; padding: 30px;")
        no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tasks_container.addWidget(no_tasks)
        
        tasks_layout.addStretch()
        content_layout.addWidget(tasks_frame, stretch=2)
        
        # AI Tips sidebar
        tips_frame = QFrame()
        tips_frame.setStyleSheet("""
            QFrame {
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 15px;
            }
        """)
        tips_layout = QVBoxLayout(tips_frame)
        tips_layout.setContentsMargins(20, 20, 20, 20)
        
        tips_header = QLabel("💡 AI Study Tips")
        tips_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d3748;")
        tips_layout.addWidget(tips_header)
        
        self._tips_container = QVBoxLayout()
        self._tips_container.setSpacing(10)
        tips_layout.addLayout(self._tips_container)
        
        # Default tips
        default_tips = [
            "🎯 Focus on one topic at a time",
            "⏰ Take breaks every 25 minutes",
            "📝 Review flashcards daily",
            "🧠 Teach concepts to reinforce learning",
            "😴 Get enough sleep for memory consolidation"
        ]
        for tip in default_tips:
            tip_label = QLabel(tip)
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("""
                background: white;
                padding: 12px;
                border-radius: 8px;
                color: #4a5568;
                font-size: 13px;
            """)
            self._tips_container.addWidget(tip_label)
        
        tips_layout.addStretch()
        
        analytics_btn = QPushButton("📊 View Full Analytics")
        analytics_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #667eea;
                border: 2px solid #667eea;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #667eea10;
            }
        """)
        analytics_btn.clicked.connect(self.view_analytics_clicked.emit)
        tips_layout.addWidget(analytics_btn)
        
        content_layout.addWidget(tips_frame, stretch=1)
        
        layout.addLayout(content_layout)
    
    def _get_greeting(self) -> str:
        """Get time-appropriate greeting."""
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning! ☀️"
        elif hour < 17:
            return "Good afternoon! 🌤️"
        else:
            return "Good evening! 🌙"
    
    def update_stats(self, stats: Dict):
        """Update the stats cards with real data."""
        if "streak" in stats:
            self._streak_card.update_value(f"{stats['streak']} days")
        if "xp" in stats:
            self._xp_card.update_value(f"{stats['xp']:,}")
        if "cards_due" in stats:
            self._cards_card.update_value(str(stats['cards_due']))
        if "quizzes" in stats:
            self._quiz_card.update_value(str(stats['quizzes']))
    
    def update_tasks(self, tasks: List[Dict]):
        """Update today's task list."""
        # Clear existing
        while self._tasks_container.count():
            child = self._tasks_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not tasks:
            no_tasks = QLabel("No study sessions scheduled.\nAdd goals in the Study Planner!")
            no_tasks.setStyleSheet("color: #718096; padding: 30px;")
            no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._tasks_container.addWidget(no_tasks)
            return
        
        for task in tasks:
            item = TaskItem(
                goal_id=task.get("id", ""),
                title=task.get("title", ""),
                hours=task.get("hours", 0),
                priority=task.get("priority", "MEDIUM"),
                deadline=task.get("deadline", ""),
                progress=task.get("progress", 0)
            )
            self._tasks_container.addWidget(item)
    
    def update_tips(self, tips: List[str]):
        """Update AI tips."""
        # Clear existing
        while self._tips_container.count():
            child = self._tips_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("""
                background: white;
                padding: 12px;
                border-radius: 8px;
                color: #4a5568;
                font-size: 13px;
            """)
            self._tips_container.addWidget(tip_label)
