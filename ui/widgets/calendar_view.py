# ui/widgets/calendar_view.py
"""
Calendar widget for tracking study sessions and reminders.
Dark-themed to match Battery Optimizer aesthetic.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QCalendarWidget, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QBrush, QPainter

from core.reminders import get_reminder_service


class EduCalendar(QCalendarWidget):
    """Custom dark-themed calendar with event markers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.study_dates = set()  # Dates with study sessions
        self.setStyleSheet("""
            QCalendarWidget {
                background: #0d1b2a;
            }
            QCalendarWidget QWidget {
                background: #0d1b2a;
                color: #c0ccda;
            }
            QCalendarWidget QTableView {
                background: #1b2838;
                alternate-background-color: #213043;
                selection-background-color: #00d4aa;
                selection-color: white;
                gridline-color: #1e3044;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton {
                color: #e8edf3;
                background: #1b2838;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QCalendarWidget QToolButton:hover {
                background: #213043;
            }
            QCalendarWidget #qt_calendar_navigationbar {
                background: #1b2838;
                border-bottom: 1px solid #1e3044;
                padding: 4px;
            }
            QCalendarWidget QMenu {
                background: #1b2838;
                color: #e8edf3;
                border: 1px solid #1e3044;
            }
            QCalendarWidget QMenu::item:selected {
                background: #00d4aa;
            }
            QCalendarWidget QSpinBox {
                background: #213043;
                color: #e8edf3;
                border: 1px solid #1e3044;
                border-radius: 4px;
            }
        """)
        
    def mark_study_date(self, date):
        """Mark a date as having study activity."""
        self.study_dates.add(date)
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor("#00d4aa")))
        fmt.setForeground(QBrush(QColor("white")))
        self.setDateTextFormat(date, fmt)
    
    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        # Draw a small dot indicator for study dates
        if date in self.study_dates:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor("#00d4aa")))
            painter.setPen(Qt.PenStyle.NoPen)
            dot_size = 5
            x = rect.center().x() - dot_size // 2
            y = rect.bottom() - dot_size - 2
            painter.drawEllipse(x, y, dot_size, dot_size)
            painter.restore()


class CalendarTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.reminder_service = get_reminder_service()
        self._mark_recent_study_dates()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Left: Calendar
        cal_frame = QFrame()
        cal_frame.setStyleSheet("QFrame { background: #1b2838; border-radius: 12px; border: 1px solid #1e3044; }")
        cal_layout = QVBoxLayout(cal_frame)
        cal_layout.setContentsMargins(12, 12, 12, 12)
        
        cal_title = QLabel("📅 Study Calendar")
        cal_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00d4aa; background: transparent;")
        cal_layout.addWidget(cal_title)
        
        self.calendar = EduCalendar()
        self.calendar.clicked.connect(self._on_date_selected)
        cal_layout.addWidget(self.calendar)
        
        layout.addWidget(cal_frame, 2)
        
        # Right: Info Panel
        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background: #1b2838; border-radius: 12px; border: 1px solid #1e3044; }")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(12)
        
        self.date_label = QLabel(QDate.currentDate().toString("dddd, MMMM d"))
        self.date_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.date_label.setStyleSheet("color: #e8edf3; background: transparent;")
        info_layout.addWidget(self.date_label)
        
        # Daily summary card
        summary_card = QFrame()
        summary_card.setStyleSheet("QFrame { background: #213043; border-radius: 8px; border: 1px solid #1e3044; }")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(12, 10, 12, 10)
        
        self.summary_label = QLabel("📊 No study data for today")
        self.summary_label.setStyleSheet("color: #7b8fa3; background: transparent; font-size: 12px;")
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label)
        info_layout.addWidget(summary_card)
        
        events_header = QLabel("🔔 Scheduled Study")
        events_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #00d4aa; background: transparent;")
        info_layout.addWidget(events_header)
        
        self.events_list = QListWidget()
        self.events_list.setStyleSheet("""
            QListWidget { border: none; background: #0d1b2a; border-radius: 8px; padding: 4px; }
            QListWidget::item { padding: 8px; margin: 2px 0; background: #1b2838; border-radius: 6px; color: #c0ccda; border-left: 3px solid #00d4aa; }
            QListWidget::item:selected { background: #00d4aa; color: white; }
        """)
        info_layout.addWidget(self.events_list)
        
        layout.addWidget(info_frame, 1)

    def _on_date_selected(self, date):
        self.date_label.setText(date.toString("dddd, MMMM d"))
        self.events_list.clear()
        
        # Check if it's today
        is_today = date == QDate.currentDate()
        if is_today:
            self.summary_label.setText("📊 Today • Keep up the study momentum!")
            self.summary_label.setStyleSheet("color: #00d4aa; background: transparent; font-size: 12px;")
        elif date in self.calendar.study_dates:
            self.summary_label.setText("📊 Study session completed this day ✅")
            self.summary_label.setStyleSheet("color: #00d4aa; background: transparent; font-size: 12px;")
        else:
            self.summary_label.setText("📊 No study data for this day")
            self.summary_label.setStyleSheet("color: #7b8fa3; background: transparent; font-size: 12px;")
        
        # Check reminders for this day
        day_idx = date.dayOfWeek() - 1  # Mon=0
        reminders = self.reminder_service.reminders
        
        found = False
        for r in reminders:
            if day_idx in r.days and r.enabled:
                item = QListWidgetItem(f"🔔 {r.time} — {r.message}")
                self.events_list.addItem(item)
                found = True
                
        if not found:
            self.events_list.addItem("No sessions scheduled for this day.")
    
    def _mark_recent_study_dates(self):
        """Mark recent dates that had study activity."""
        try:
            from core.db import get_stats
            stats = dict(get_stats())
            streak = stats.get('streak', 0)
            today = QDate.currentDate()
            # Mark streak days
            for i in range(min(streak, 30)):
                d = today.addDays(-i)
                self.calendar.mark_study_date(d)
        except Exception:
            pass
