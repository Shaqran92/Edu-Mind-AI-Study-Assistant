# ui/widgets/study_streak.py
"""
Study Streak & Daily Goals widget for the dashboard.
Shows current streak, daily XP progress, and study goals.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from utils.logger import get_logger

logger = get_logger("study_streak")


class StudyStreakWidget(QWidget):
    """
    Compact widget showing study streak, daily XP, and progress toward goals.
    """
    
    ACCENT = "#00d4aa"
    BG_CARD = "#1b2838"
    BORDER = "#1e3044"
    TEXT = "#c0ccda"
    TEXT_MUTED = "#7b8fa3"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()
        
        # Auto-refresh every 60 seconds
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60000)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Streak card
        streak_card = QFrame()
        streak_card.setStyleSheet(f"""
            QFrame {{
                background: {self.BG_CARD};
                border: 1px solid {self.BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        streak_layout = QHBoxLayout(streak_card)
        
        # Fire icon
        fire = QLabel("🔥")
        fire.setFont(QFont("Segoe UI Emoji", 32))
        fire.setFixedWidth(60)
        fire.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fire.setStyleSheet("background: transparent;")
        streak_layout.addWidget(fire)
        
        # Streak info
        info = QVBoxLayout()
        self._streak_label = QLabel("0 Day Streak")
        self._streak_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._streak_label.setStyleSheet(f"color: {self.ACCENT}; background: transparent;")
        info.addWidget(self._streak_label)
        
        self._streak_sub = QLabel("Study every day to keep your streak!")
        self._streak_sub.setStyleSheet(f"color: {self.TEXT_MUTED}; font-size: 11px; background: transparent;")
        info.addWidget(self._streak_sub)
        
        streak_layout.addLayout(info)
        streak_layout.addStretch()
        layout.addWidget(streak_card)
        
        # Stats row
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.BG_CARD};
                border: 1px solid {self.BORDER};
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        self._stat_cards = {}
        for icon, label, key in [
            ("⚡", "Today's XP", "daily_xp"),
            ("📚", "Notes", "total_notes"),
            ("🧠", "Quizzes", "total_quizzes"),
            ("⏱", "Study Time", "study_time"),
        ]:
            card = self._create_stat_mini(icon, "0", label)
            self._stat_cards[key] = card['value_label']
            stats_layout.addWidget(card['widget'])
        
        layout.addWidget(stats_frame)
        
        # Daily goal progress
        goal_card = QFrame()
        goal_card.setStyleSheet(f"""
            QFrame {{
                background: {self.BG_CARD};
                border: 1px solid {self.BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        goal_layout = QVBoxLayout(goal_card)
        
        goal_header = QHBoxLayout()
        goal_title = QLabel("🎯 Daily Goal")
        goal_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        goal_title.setStyleSheet(f"color: {self.TEXT}; background: transparent;")
        goal_header.addWidget(goal_title)
        
        self._goal_pct = QLabel("0%")
        self._goal_pct.setStyleSheet(f"color: {self.ACCENT}; font-size: 14px; font-weight: bold; background: transparent;")
        goal_header.addWidget(self._goal_pct, 0, Qt.AlignmentFlag.AlignRight)
        goal_layout.addLayout(goal_header)
        
        self._goal_bar = QProgressBar()
        self._goal_bar.setMaximum(100)
        self._goal_bar.setValue(0)
        self._goal_bar.setTextVisible(False)
        self._goal_bar.setFixedHeight(10)
        self._goal_bar.setStyleSheet(f"""
            QProgressBar {{
                background: #213043;
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.ACCENT}, stop:1 #0984e3);
                border-radius: 5px;
            }}
        """)
        goal_layout.addWidget(self._goal_bar)
        
        self._goal_desc = QLabel("Study for 30 minutes to complete your daily goal")
        self._goal_desc.setStyleSheet(f"color: {self.TEXT_MUTED}; font-size: 11px; background: transparent;")
        goal_layout.addWidget(self._goal_desc)
        
        layout.addWidget(goal_card)
    
    def _create_stat_mini(self, icon: str, value: str, label: str) -> dict:
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background: #213043;
                border-radius: 8px;
                padding: 10px;
                border: none;
            }}
        """)
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 6, 8, 6)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 16))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(icon_lbl)
        
        value_lbl = QLabel(value)
        value_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_lbl.setStyleSheet(f"color: white; background: transparent;")
        layout.addWidget(value_lbl)
        
        label_lbl = QLabel(label)
        label_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_lbl.setStyleSheet(f"color: {self.TEXT_MUTED}; font-size: 10px; background: transparent;")
        layout.addWidget(label_lbl)
        
        return {'widget': widget, 'value_label': value_lbl}
    
    def refresh(self):
        """Refresh all stats from the database."""
        try:
            from data.db import get_conn
            with get_conn() as conn:
                cursor = conn.cursor()
                
                # Streak (consecutive days with study_sessions)
                cursor.execute("""
                    SELECT COUNT(DISTINCT DATE(start_time)) as streak
                    FROM study_sessions
                    WHERE DATE(start_time) >= DATE('now', '-30 days')
                """)
                row = cursor.fetchone()
                streak = row['streak'] if row else 0
                
                # Today's study time
                cursor.execute("""
                    SELECT COALESCE(SUM(duration_minutes), 0) as mins
                    FROM study_sessions
                    WHERE DATE(start_time) = DATE('now')
                """)
                row = cursor.fetchone()
                today_mins = row['mins'] if row else 0
                
                # Total notes
                cursor.execute("SELECT COUNT(*) as c FROM notes")
                row = cursor.fetchone()
                total_notes = row['c'] if row else 0
                
                # Total quizzes
                cursor.execute("SELECT COUNT(*) as c FROM quiz_history")
                row = cursor.fetchone()
                total_quizzes = row['c'] if row else 0
                
                # Today's XP (from stats table if exists)
                try:
                    cursor.execute("SELECT COALESCE(xp, 0) as xp FROM stats LIMIT 1")
                    row = cursor.fetchone()
                    total_xp = row['xp'] if row else 0
                except:
                    total_xp = 0
                
            # Update UI
            self._streak_label.setText(f"{streak} Day Streak")
            if streak > 0:
                self._streak_sub.setText(f"🎉 Great job! Keep it going!")
            
            self._stat_cards['daily_xp'].setText(str(total_xp))
            self._stat_cards['total_notes'].setText(str(total_notes))
            self._stat_cards['total_quizzes'].setText(str(total_quizzes))
            self._stat_cards['study_time'].setText(f"{today_mins}m")
            
            # Daily goal: 30 minutes of study
            goal_mins = 30
            pct = min(100, int((today_mins / goal_mins) * 100))
            self._goal_bar.setValue(pct)
            self._goal_pct.setText(f"{pct}%")
            if pct >= 100:
                self._goal_desc.setText("🎉 Daily goal completed! Amazing work!")
                self._goal_desc.setStyleSheet(f"color: {self.ACCENT}; font-size: 11px; background: transparent;")
            else:
                remaining = goal_mins - today_mins
                self._goal_desc.setText(f"Study for {remaining} more minutes to complete your goal")
                
        except Exception as e:
            logger.error(f"Failed to refresh streak: {e}")
