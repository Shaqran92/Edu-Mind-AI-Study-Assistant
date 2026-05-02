# ui/widgets/pomodoro_timer.py
"""
Pomodoro Focus Timer for EduMind.
25-minute study sessions with 5-minute breaks.
Tracks sessions in the database.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QProgressBar, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from utils.logger import get_logger

logger = get_logger("pomodoro")


class PomodoroTimer(QWidget):
    """
    Pomodoro technique timer with configurable work/break durations.
    Tracks completed sessions and records them to the database.
    """
    
    session_completed = pyqtSignal(int)  # Emits duration in minutes
    
    # Colors
    ACCENT = "#00d4aa"
    BG_CARD = "#1b2838"
    BG_TERTIARY = "#213043"
    BORDER = "#1e3044"
    TEXT = "#c0ccda"
    TEXT_MUTED = "#7b8fa3"
    
    # Phases
    PHASE_WORK = "work"
    PHASE_BREAK = "break"
    PHASE_LONG_BREAK = "long_break"
    
    PHASE_LABELS = {
        "work": "🎯 Focus Time",
        "break": "☕ Short Break",
        "long_break": "🌴 Long Break"
    }
    
    PHASE_COLORS = {
        "work": "#00d4aa",
        "break": "#f6ad55",
        "long_break": "#63b3ed"
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Defaults
        self._work_mins = 25
        self._break_mins = 5
        self._long_break_mins = 15
        self._sessions_before_long = 4
        
        self._current_phase = self.PHASE_WORK
        self._remaining_seconds = self._work_mins * 60
        self._is_running = False
        self._completed_sessions = 0
        
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Phase indicator
        self._phase_label = QLabel(self.PHASE_LABELS[self._current_phase])
        self._phase_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._phase_label.setStyleSheet(f"color: {self.ACCENT}; background: transparent;")
        layout.addWidget(self._phase_label)
        
        # Large timer display
        self._time_display = QLabel(self._format_time(self._remaining_seconds))
        self._time_display.setFont(QFont("Consolas", 48, QFont.Weight.Bold))
        self._time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_display.setStyleSheet(f"""
            color: white;
            background: {self.BG_TERTIARY};
            border: 2px solid {self.BORDER};
            border-radius: 16px;
            padding: 20px;
            margin: 10px 40px;
        """)
        layout.addWidget(self._time_display)
        
        # Progress bar
        self._progress = QProgressBar()
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: {self.BG_TERTIARY};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {self.ACCENT};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self._progress)
        
        # Session counter
        self._session_label = QLabel(f"Sessions: {self._completed_sessions} / {self._sessions_before_long}")
        self._session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._session_label.setStyleSheet(f"color: {self.TEXT_MUTED}; font-size: 12px; background: transparent;")
        layout.addWidget(self._session_label)
        
        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(10)
        
        btn_style = f"""
            QPushButton {{
                padding: 12px 28px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                min-width: 100px;
            }}
        """
        
        self._start_btn = QPushButton("▶ Start")
        self._start_btn.setStyleSheet(btn_style + f"""
            QPushButton {{ background: {self.ACCENT}; color: #0d1b2a; }}
            QPushButton:hover {{ background: #00e6b8; }}
        """)
        self._start_btn.clicked.connect(self._toggle)
        
        self._reset_btn = QPushButton("↺ Reset")
        self._reset_btn.setStyleSheet(btn_style + f"""
            QPushButton {{ background: {self.BG_TERTIARY}; color: {self.TEXT}; border: 1px solid {self.BORDER}; }}
            QPushButton:hover {{ background: #2a3f55; }}
        """)
        self._reset_btn.clicked.connect(self._reset)
        
        self._skip_btn = QPushButton("⏭ Skip")
        self._skip_btn.setStyleSheet(btn_style + f"""
            QPushButton {{ background: {self.BG_TERTIARY}; color: {self.TEXT}; border: 1px solid {self.BORDER}; }}
            QPushButton:hover {{ background: #2a3f55; }}
        """)
        self._skip_btn.clicked.connect(self._skip_phase)
        
        controls.addStretch()
        controls.addWidget(self._start_btn)
        controls.addWidget(self._reset_btn)
        controls.addWidget(self._skip_btn)
        controls.addStretch()
        layout.addLayout(controls)
        
        # Settings row
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"""
            QFrame {{ 
                background: {self.BG_TERTIARY}; 
                border: 1px solid {self.BORDER}; 
                border-radius: 10px; 
                padding: 10px; 
            }}
        """)
        settings_layout = QHBoxLayout(settings_frame)
        
        for label_text, default, attr in [
            ("Work", self._work_mins, "_work_spin"),
            ("Break", self._break_mins, "_break_spin"),
            ("Long Break", self._long_break_mins, "_long_break_spin"),
        ]:
            lbl = QLabel(f"{label_text}:")
            lbl.setStyleSheet(f"color: {self.TEXT_MUTED}; font-size: 11px; background: transparent;")
            spin = QSpinBox()
            spin.setRange(1, 120)
            spin.setValue(default)
            spin.setSuffix(" min")
            spin.setStyleSheet(f"""
                QSpinBox {{
                    background: {self.BG_CARD};
                    color: {self.TEXT};
                    border: 1px solid {self.BORDER};
                    border-radius: 6px;
                    padding: 4px 8px;
                    min-width: 70px;
                }}
            """)
            spin.valueChanged.connect(self._update_settings)
            setattr(self, attr, spin)
            settings_layout.addWidget(lbl)
            settings_layout.addWidget(spin)
        
        layout.addWidget(settings_frame)
        layout.addStretch()
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        m, s = divmod(max(0, seconds), 60)
        return f"{m:02d}:{s:02d}"
    
    def _get_total_seconds(self) -> int:
        if self._current_phase == self.PHASE_WORK:
            return self._work_mins * 60
        elif self._current_phase == self.PHASE_BREAK:
            return self._break_mins * 60
        else:
            return self._long_break_mins * 60
    
    def _toggle(self):
        if self._is_running:
            self._pause()
        else:
            self._start()
    
    def _start(self):
        self._is_running = True
        self._start_btn.setText("⏸ Pause")
        self._timer.start()
    
    def _pause(self):
        self._is_running = False
        self._start_btn.setText("▶ Resume")
        self._timer.stop()
    
    def _reset(self):
        self._timer.stop()
        self._is_running = False
        self._remaining_seconds = self._get_total_seconds()
        self._time_display.setText(self._format_time(self._remaining_seconds))
        self._progress.setValue(0)
        self._start_btn.setText("▶ Start")
    
    def _skip_phase(self):
        self._timer.stop()
        self._is_running = False
        self._phase_complete()
    
    def _update_settings(self):
        self._work_mins = self._work_spin.value()
        self._break_mins = self._break_spin.value()
        self._long_break_mins = self._long_break_spin.value()
        if not self._is_running:
            self._remaining_seconds = self._get_total_seconds()
            self._time_display.setText(self._format_time(self._remaining_seconds))
            self._progress.setValue(0)
    
    def _tick(self):
        self._remaining_seconds -= 1
        
        # Update display
        self._time_display.setText(self._format_time(self._remaining_seconds))
        
        # Update progress
        total = self._get_total_seconds()
        elapsed = total - self._remaining_seconds
        pct = int((elapsed / max(1, total)) * 100)
        self._progress.setValue(pct)
        
        # Update color based on phase
        color = self.PHASE_COLORS.get(self._current_phase, self.ACCENT)
        self._time_display.setStyleSheet(f"""
            color: {color};
            background: {self.BG_TERTIARY};
            border: 2px solid {color};
            border-radius: 16px;
            padding: 20px;
            margin: 10px 40px;
        """)
        
        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._is_running = False
            self._phase_complete()
    
    def _phase_complete(self):
        """Handle phase completion and switch to next phase."""
        if self._current_phase == self.PHASE_WORK:
            self._completed_sessions += 1
            self.session_completed.emit(self._work_mins)
            
            # Record to database
            self._record_session(self._work_mins)
            
            # Determine next phase
            if self._completed_sessions % self._sessions_before_long == 0:
                self._current_phase = self.PHASE_LONG_BREAK
            else:
                self._current_phase = self.PHASE_BREAK
        else:
            self._current_phase = self.PHASE_WORK
        
        # Update UI
        self._remaining_seconds = self._get_total_seconds()
        self._time_display.setText(self._format_time(self._remaining_seconds))
        self._phase_label.setText(self.PHASE_LABELS[self._current_phase])
        color = self.PHASE_COLORS.get(self._current_phase, self.ACCENT)
        self._phase_label.setStyleSheet(f"color: {color}; font-size: 14px; background: transparent;")
        self._progress.setValue(0)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background: {self.BG_TERTIARY}; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}
        """)
        self._session_label.setText(
            f"Sessions: {self._completed_sessions} / {self._sessions_before_long}"
        )
        self._start_btn.setText("▶ Start")
    
    def _record_session(self, duration_mins: int):
        """Save study session to database."""
        try:
            from data.db import get_conn
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO study_sessions (duration_minutes, focus_score) VALUES (?, ?)",
                    (duration_mins, 100)
                )
                conn.commit()
            logger.info(f"Recorded Pomodoro session: {duration_mins} minutes")
        except Exception as e:
            logger.error(f"Failed to record session: {e}")
