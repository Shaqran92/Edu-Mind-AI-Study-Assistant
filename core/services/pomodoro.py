# core/services/pomodoro.py
"""
Pomodoro timer service for focused study sessions.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Callable
import time
import threading

from utils.logger import get_logger

logger = get_logger("pomodoro")


class PomodoroPhase(Enum):
    """Phases in the Pomodoro technique."""
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    IDLE = "idle"


@dataclass
class PomodoroConfig:
    """Configuration for Pomodoro timer."""
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    pomodoros_until_long_break: int = 4
    auto_start_breaks: bool = True
    auto_start_work: bool = False


class PomodoroTimer:
    """
    Pomodoro timer implementation.
    
    Features:
    - Configurable work/break durations
    - Automatic phase transitions
    - Callback notifications
    - Pause/resume support
    
    Example:
        >>> timer = PomodoroTimer()
        >>> timer.on_tick = lambda remaining: print(f"{remaining}s left")
        >>> timer.on_phase_complete = lambda phase: print(f"{phase} done!")
        >>> timer.start()
    """
    
    def __init__(self, config: Optional[PomodoroConfig] = None):
        self.config = config or PomodoroConfig()
        self._phase = PomodoroPhase.IDLE
        self._remaining_seconds = 0
        self._is_running = False
        self._is_paused = False
        self._completed_pomodoros = 0
        self._total_work_seconds = 0
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self.on_tick: Optional[Callable[[int], None]] = None
        self.on_phase_complete: Optional[Callable[[PomodoroPhase], None]] = None
        self.on_phase_start: Optional[Callable[[PomodoroPhase], None]] = None
        
        logger.info("Pomodoro timer initialized")
    
    @property
    def phase(self) -> PomodoroPhase:
        return self._phase
    
    @property
    def remaining_seconds(self) -> int:
        return self._remaining_seconds
    
    @property
    def remaining_formatted(self) -> str:
        """Get remaining time in MM:SS format."""
        minutes = self._remaining_seconds // 60
        seconds = self._remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def is_running(self) -> bool:
        return self._is_running and not self._is_paused
    
    @property
    def is_paused(self) -> bool:
        return self._is_paused
    
    @property
    def completed_pomodoros(self) -> int:
        return self._completed_pomodoros
    
    @property
    def total_work_minutes(self) -> int:
        return self._total_work_seconds // 60
    
    def start(self, phase: Optional[PomodoroPhase] = None):
        """Start the timer."""
        if self._is_running:
            return
        
        # Determine phase
        if phase is None:
            if self._phase == PomodoroPhase.IDLE:
                phase = PomodoroPhase.WORK
            else:
                phase = self._phase
        
        self._phase = phase
        self._remaining_seconds = self._get_phase_duration(phase)
        self._is_running = True
        self._is_paused = False
        self._stop_event.clear()
        
        # Notify phase start
        if self.on_phase_start:
            self.on_phase_start(phase)
        
        # Start timer thread
        self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self._timer_thread.start()
        
        logger.info(f"Started {phase.value} phase ({self._remaining_seconds}s)")
    
    def pause(self):
        """Pause the timer."""
        if self._is_running and not self._is_paused:
            self._is_paused = True
            logger.info("Timer paused")
    
    def resume(self):
        """Resume the timer."""
        if self._is_running and self._is_paused:
            self._is_paused = False
            logger.info("Timer resumed")
    
    def stop(self):
        """Stop the timer."""
        self._stop_event.set()
        self._is_running = False
        self._is_paused = False
        self._phase = PomodoroPhase.IDLE
        logger.info("Timer stopped")
    
    def skip(self):
        """Skip to the next phase."""
        if not self._is_running:
            return
        
        self._complete_phase()
    
    def reset(self):
        """Reset the timer to initial state."""
        self.stop()
        self._completed_pomodoros = 0
        self._total_work_seconds = 0
        logger.info("Timer reset")
    
    def _run_timer(self):
        """Timer thread loop."""
        while not self._stop_event.is_set() and self._remaining_seconds > 0:
            if not self._is_paused:
                time.sleep(1)
                
                if self._stop_event.is_set():
                    break
                
                self._remaining_seconds -= 1
                
                # Track work time
                if self._phase == PomodoroPhase.WORK:
                    self._total_work_seconds += 1
                
                # Notify tick
                if self.on_tick:
                    self.on_tick(self._remaining_seconds)
            else:
                time.sleep(0.1)  # Small sleep while paused
        
        if not self._stop_event.is_set() and self._remaining_seconds <= 0:
            self._complete_phase()
    
    def _complete_phase(self):
        """Handle phase completion."""
        completed_phase = self._phase
        
        # Notify completion
        if self.on_phase_complete:
            self.on_phase_complete(completed_phase)
        
        # Update state based on completed phase
        if completed_phase == PomodoroPhase.WORK:
            self._completed_pomodoros += 1
            
            # Determine break type
            if self._completed_pomodoros % self.config.pomodoros_until_long_break == 0:
                next_phase = PomodoroPhase.LONG_BREAK
            else:
                next_phase = PomodoroPhase.SHORT_BREAK
            
            if self.config.auto_start_breaks:
                self._is_running = False
                self.start(next_phase)
            else:
                self._phase = next_phase
                self._is_running = False
        
        elif completed_phase in (PomodoroPhase.SHORT_BREAK, PomodoroPhase.LONG_BREAK):
            if self.config.auto_start_work:
                self._is_running = False
                self.start(PomodoroPhase.WORK)
            else:
                self._phase = PomodoroPhase.WORK
                self._is_running = False
        
        logger.info(f"Completed {completed_phase.value} phase. "
                   f"Total pomodoros: {self._completed_pomodoros}")
    
    def _get_phase_duration(self, phase: PomodoroPhase) -> int:
        """Get phase duration in seconds."""
        if phase == PomodoroPhase.WORK:
            return self.config.work_minutes * 60
        elif phase == PomodoroPhase.SHORT_BREAK:
            return self.config.short_break_minutes * 60
        elif phase == PomodoroPhase.LONG_BREAK:
            return self.config.long_break_minutes * 60
        return 0
    
    def get_phase_name(self) -> str:
        """Get human-readable phase name."""
        names = {
            PomodoroPhase.WORK: "🍅 Focus Time",
            PomodoroPhase.SHORT_BREAK: "☕ Short Break",
            PomodoroPhase.LONG_BREAK: "🌴 Long Break",
            PomodoroPhase.IDLE: "⏸️ Ready"
        }
        return names.get(self._phase, "Unknown")
