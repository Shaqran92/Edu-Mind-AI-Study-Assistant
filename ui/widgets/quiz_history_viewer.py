# ui/widgets/quiz_history_viewer.py
"""
Quiz History Viewer for EduMind.
Shows past quiz attempts with scores and detailed results.
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from utils.logger import get_logger

logger = get_logger("quiz_history")


class QuizHistoryViewer(QWidget):
    """
    Displays past quiz attempts in a scrollable list with scores and expandable details.
    """
    
    ACCENT = "#00d4aa"
    BG_CARD = "#1b2838"
    BG_TERTIARY = "#213043"
    BORDER = "#1e3044"
    TEXT = "#c0ccda"
    TEXT_MUTED = "#7b8fa3"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📊 Quiz History")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.ACCENT}; background: transparent;")
        header.addWidget(title)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.BG_TERTIARY};
                color: {self.TEXT};
                border: 1px solid {self.BORDER};
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: #2a4058; }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)
        
        # Score summary
        self._summary_label = QLabel("No quizzes taken yet")
        self._summary_label.setStyleSheet(f"color: {self.TEXT_MUTED}; font-size: 12px; background: transparent;")
        layout.addWidget(self._summary_label)
        
        # Scrollable history
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)
        
        self._container = QWidget()
        self._history_layout = QVBoxLayout(self._container)
        self._history_layout.setSpacing(8)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.addStretch()
        scroll.setWidget(self._container)
        layout.addWidget(scroll)
    
    def refresh(self):
        """Reload quiz history from database."""
        # Clear existing items
        while self._history_layout.count() > 1:  # Keep the stretch
            child = self._history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        try:
            from data.db import get_conn
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, score, total_questions, correct_answers, details_json, created_at
                    FROM quiz_history
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                rows = cursor.fetchall()
            
            if not rows:
                self._summary_label.setText("No quizzes taken yet. Generate a quiz to see your history!")
                return
            
            # Summary stats
            total_quizzes = len(rows)
            avg_score = sum(r['score'] for r in rows) / total_quizzes
            best_score = max(r['score'] for r in rows)
            self._summary_label.setText(
                f"📈 {total_quizzes} quizzes taken  •  Average: {avg_score:.0f}%  •  Best: {best_score}%"
            )
            
            # Add history cards
            for row in rows:
                card = self._create_history_card(row)
                # Insert before the stretch
                self._history_layout.insertWidget(self._history_layout.count() - 1, card)
                
        except Exception as e:
            logger.error(f"Failed to load quiz history: {e}")
            self._summary_label.setText(f"Error loading history: {e}")
    
    def _create_history_card(self, row) -> QFrame:
        """Create a card for a single quiz attempt."""
        card = QFrame()
        score = row['score']
        
        # Color based on score
        if score >= 80:
            score_color = "#00d4aa"
            grade = "A"
        elif score >= 60:
            score_color = "#f6ad55"
            grade = "B"
        elif score >= 40:
            score_color = "#fc8181"
            grade = "C"
        else:
            score_color = "#e53e3e"
            grade = "D"
        
        card.setStyleSheet(f"""
            QFrame {{
                background: {self.BG_CARD};
                border: 1px solid {self.BORDER};
                border-left: 4px solid {score_color};
                border-radius: 10px;
                padding: 14px;
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setSpacing(16)
        
        # Score circle
        score_lbl = QLabel(f"{score}%")
        score_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        score_lbl.setFixedWidth(80)
        score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_lbl.setStyleSheet(f"""
            color: {score_color};
            background: {self.BG_TERTIARY};
            border-radius: 10px;
            padding: 8px;
        """)
        layout.addWidget(score_lbl)
        
        # Details
        details = QVBoxLayout()
        
        correct = row['correct_answers']
        total = row['total_questions']
        date_str = str(row['created_at'])[:16] if row['created_at'] else "Unknown"
        
        title = QLabel(f"Grade {grade} — {correct}/{total} correct")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.TEXT}; background: transparent;")
        details.addWidget(title)
        
        date = QLabel(f"📅 {date_str}")
        date.setStyleSheet(f"color: {self.TEXT_MUTED}; font-size: 11px; background: transparent;")
        details.addWidget(date)
        
        # Show wrong answers if any
        try:
            quiz_details = json.loads(row['details_json']) if row['details_json'] else []
            wrong = [d for d in quiz_details if not d.get('correct', True)]
            if wrong:
                wrong_text = f"❌ Missed: {', '.join(d.get('q', '?')[:50] for d in wrong[:3])}"
                if len(wrong) > 3:
                    wrong_text += f" +{len(wrong)-3} more"
                wrong_lbl = QLabel(wrong_text)
                wrong_lbl.setStyleSheet(f"color: #fc8181; font-size: 10px; background: transparent;")
                wrong_lbl.setWordWrap(True)
                details.addWidget(wrong_lbl)
        except:
            pass
        
        layout.addLayout(details, 1)
        
        return card
