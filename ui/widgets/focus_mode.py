# ui/widgets/focus_mode.py
"""
Focus Mode widget for distraction-free studying.
Includes integrated Pomodoro timer and session goals.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QSpinBox, QStackedWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from utils.logger import get_logger

logger = get_logger("focus_mode")


class FocusModeWidget(QWidget):
    """
    Focus mode widget with Pomodoro timer and distraction-free UI.
    
    Signals:
        session_started: Emitted when a focus session starts
        session_ended: Emitted when a focus session ends (with duration in minutes)
        break_started: Emitted when a break begins
    """
    
    session_started = pyqtSignal()
    session_ended = pyqtSignal(int)  # Duration in minutes
    break_started = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Timer state
        self._is_active = False
        self._is_break = False
        self._remaining_seconds = 0
        self._total_seconds = 0
        self._sessions_completed = 0
        
        # Default settings
        self._work_minutes = 25
        self._break_minutes = 5
        self._long_break_minutes = 15
        self._sessions_until_long_break = 4
        
        # Timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        
        self._setup_ui()
        logger.info("FocusModeWidget initialized")
    
    def _setup_ui(self):
        """Set up the focus mode UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Main container — dark navy card
        container = QFrame()
        container.setObjectName("focusContainer")
        container.setStyleSheet("""
            #focusContainer {
                background: #1b2838;
                border: 1px solid #1e3044;
                border-radius: 16px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(40, 30, 40, 30)
        
        # Title
        title = QLabel("Focus Mode")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #00d4aa; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)
        
        # Timer display
        self._timer_label = QLabel("25:00")
        self._timer_label.setFont(QFont("Segoe UI", 64, QFont.Weight.Bold))
        self._timer_label.setStyleSheet("color: #e8edf3; background: transparent;")
        self._timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self._timer_label)
        
        # Status label
        self._status_label = QLabel("Ready to focus")
        self._status_label.setFont(QFont("Segoe UI", 13))
        self._status_label.setStyleSheet("color: #7b8fa3; background: transparent;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self._status_label)
        
        # Progress bar
        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        self._progress.setStyleSheet("""
            QProgressBar {
                background: #213043;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4aa, stop:1 #0984e3);
                border-radius: 4px;
            }
        """)
        self._progress.setValue(100)
        container_layout.addWidget(self._progress)
        
        # Session counter
        self._session_label = QLabel("Sessions: 0  |  Streak: 0")
        self._session_label.setFont(QFont("Segoe UI", 11))
        self._session_label.setStyleSheet("color: #4a5e73; background: transparent;")
        self._session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self._session_label)
        
        container_layout.addSpacing(10)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self._start_btn = QPushButton("Start Focus")
        self._start_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4aa, stop:1 #0984e3);
                color: white;
                border: none;
                padding: 14px 40px;
                border-radius: 10px;
                min-width: 160px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0984e3, stop:1 #00d4aa);
            }
        """)
        self._start_btn.clicked.connect(self._toggle_timer)
        button_layout.addWidget(self._start_btn)
        
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.setFont(QFont("Segoe UI", 13))
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #7b8fa3;
                border: 1px solid #1e3044;
                padding: 14px 30px;
                border-radius: 10px;
            }
            QPushButton:hover {
                border-color: #00d4aa;
                color: #00d4aa;
            }
        """)
        self._reset_btn.clicked.connect(self._reset_timer)
        button_layout.addWidget(self._reset_btn)
        
        container_layout.addLayout(button_layout)
        
        container_layout.addSpacing(10)
        
        # Settings section
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(16)
        
        spin_style = """
            QSpinBox {
                background: #213043;
                color: #e8edf3;
                border: 1px solid #1e3044;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 90px;
                font-size: 13px;
            }
            QSpinBox:hover { border-color: #00d4aa; }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #1e3044;
                border: none;
                width: 20px;
            }
        """
        
        # Work duration
        work_layout = QVBoxLayout()
        work_label = QLabel("Work")
        work_label.setStyleSheet("color: #7b8fa3; font-size: 12px; background: transparent;")
        work_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._work_spin = QSpinBox()
        self._work_spin.setRange(1, 60)
        self._work_spin.setValue(25)
        self._work_spin.setSuffix(" min")
        self._work_spin.setStyleSheet(spin_style)
        self._work_spin.valueChanged.connect(lambda v: self._update_setting("work", v))
        work_layout.addWidget(work_label)
        work_layout.addWidget(self._work_spin)
        settings_layout.addLayout(work_layout)
        
        # Break duration
        break_layout = QVBoxLayout()
        break_label = QLabel("Break")
        break_label.setStyleSheet("color: #7b8fa3; font-size: 12px; background: transparent;")
        break_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._break_spin = QSpinBox()
        self._break_spin.setRange(1, 30)
        self._break_spin.setValue(5)
        self._break_spin.setSuffix(" min")
        self._break_spin.setStyleSheet(spin_style)
        self._break_spin.valueChanged.connect(lambda v: self._update_setting("break", v))
        break_layout.addWidget(break_label)
        break_layout.addWidget(self._break_spin)
        settings_layout.addLayout(break_layout)
        
        container_layout.addLayout(settings_layout)
        
        layout.addWidget(container)
        
        # Tip
        tips = QLabel("Press Ctrl+F to toggle focus mode")
        tips.setStyleSheet("color: #4a5e73; font-size: 11px; background: transparent;")
        tips.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tips)
    
    def _update_setting(self, setting: str, value: int):
        """Update timer settings."""
        if setting == "work":
            self._work_minutes = value
            if not self._is_active:
                self._remaining_seconds = value * 60
                self._update_display()
        elif setting == "break":
            self._break_minutes = value
    
    def _toggle_timer(self):
        """Start or pause the timer."""
        if self._is_active:
            self._pause_timer()
        else:
            self._start_timer()
    
    def _start_timer(self):
        """Start the focus timer."""
        if self._remaining_seconds == 0:
            self._remaining_seconds = self._work_minutes * 60
            self._total_seconds = self._remaining_seconds
        
        self._is_active = True
        self._timer.start(1000)
        
        self._start_btn.setText("Pause")
        if not self._is_break:
            self._status_label.setText("Stay focused!")
        else:
            self._status_label.setText("Take a break")
        
        if not self._is_break:
            self.session_started.emit()
        else:
            self.break_started.emit()
        
        logger.info("Focus timer started")
    
    def _pause_timer(self):
        """Pause the timer."""
        self._is_active = False
        self._timer.stop()
        self._start_btn.setText("Resume")
        self._status_label.setText("Paused")
    
    def _reset_timer(self):
        """Reset the timer."""
        self._timer.stop()
        self._is_active = False
        self._is_break = False
        self._remaining_seconds = self._work_minutes * 60
        self._total_seconds = self._remaining_seconds
        
        self._start_btn.setText("Start Focus")
        self._status_label.setText("Ready to focus")
        self._update_display()
    
    def _tick(self):
        """Timer tick handler."""
        self._remaining_seconds -= 1
        self._update_display()
        
        if self._remaining_seconds <= 0:
            self._timer_complete()
    
    def _timer_complete(self):
        """Handle timer completion."""
        self._timer.stop()
        self._is_active = False
        
        if not self._is_break:
            # Work session complete
            self._sessions_completed += 1
            self.session_ended.emit(self._work_minutes)
            
            # Check if long break
            if self._sessions_completed % self._sessions_until_long_break == 0:
                self._remaining_seconds = self._long_break_minutes * 60
                self._status_label.setText("Great work! Take a long break")
            else:
                self._remaining_seconds = self._break_minutes * 60
                self._status_label.setText("Session complete! Take a break")
            
            self._is_break = True
            self._session_label.setText(f"Sessions: {self._sessions_completed}  |  Streak: {self._sessions_completed}")
        else:
            # Break complete
            self._remaining_seconds = self._work_minutes * 60
            self._is_break = False
            self._status_label.setText("Break over! Ready for next session")
        
        self._total_seconds = self._remaining_seconds
        self._start_btn.setText("Start")
        self._update_display()
    
    def _update_display(self):
        """Update the timer display."""
        minutes = self._remaining_seconds // 60
        seconds = self._remaining_seconds % 60
        self._timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        if self._total_seconds > 0:
            progress = int((self._remaining_seconds / self._total_seconds) * 100)
            self._progress.setValue(progress)
    
    @property
    def is_active(self) -> bool:
        """Check if focus mode is active."""
        return self._is_active
    
    @property
    def sessions_completed(self) -> int:
        """Get number of completed sessions."""
        return self._sessions_completed
