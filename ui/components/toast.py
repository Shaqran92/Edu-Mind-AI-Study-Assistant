# ui/components/toast.py
"""
Toast notification component for non-blocking user feedback.
"""

from enum import Enum
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QPushButton,
    QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor


class ToastType(Enum):
    """Toast notification types with associated colors and icons."""
    SUCCESS = ("#48bb78", "✅")
    ERROR = ("#f56565", "❌")
    WARNING = ("#ed8936", "⚠️")
    INFO = ("#4299e1", "ℹ️")


class Toast(QWidget):
    """
    A non-blocking toast notification that appears and fades away.
    
    Features:
    - Auto-dismiss after configurable duration
    - Fade in/out animations
    - Different types (success, error, warning, info)
    - Optional action button
    
    Example:
        >>> Toast.show_message("File saved successfully!", ToastType.SUCCESS)
    """
    
    _current_toast: Optional['Toast'] = None
    _toast_queue: list = []
    
    def __init__(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
        action_text: str = "",
        action_callback=None,
        parent=None
    ):
        # Use main window as parent if none provided
        if parent is None:
            parent = QApplication.activeWindow()
        
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        self.action_text = action_text
        self.action_callback = action_callback
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()
        self._setup_animation()
    
    def _setup_ui(self):
        """Create the toast layout."""
        color, icon = self.toast_type.value
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Container with background
        self.setStyleSheet(f"""
            Toast {{
                background: {color};
                border-radius: 10px;
            }}
        """)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                background: transparent;
            }
        """)
        layout.addWidget(icon_label)
        
        # Message
        msg_label = QLabel(self.message)
        msg_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }
        """)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)
        
        # Action button (optional)
        if self.action_text and self.action_callback:
            action_btn = QPushButton(self.action_text)
            action_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
            """)
            action_btn.clicked.connect(self._on_action)
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(action_btn)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 20px;
                font-weight: bold;
                padding: 0 4px;
            }
            QPushButton:hover {
                color: rgba(255, 255, 255, 0.7);
            }
        """)
        close_btn.clicked.connect(self._dismiss)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(close_btn)
        
        self.adjustSize()
    
    def _setup_animation(self):
        """Set up fade animations."""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out.finished.connect(self._on_fade_out_complete)
        
        # Auto-dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self._dismiss)
    
    def _position_toast(self):
        """Position the toast at the bottom center of the parent."""
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - 30
            self.move(x, y)
    
    def show_toast(self):
        """Display the toast with animation."""
        self._position_toast()
        self.show()
        self.fade_in.start()
        self.dismiss_timer.start(self.duration)
    
    def _dismiss(self):
        """Start the dismiss animation."""
        self.dismiss_timer.stop()
        self.fade_out.start()
    
    def _on_fade_out_complete(self):
        """Clean up after fade out."""
        self.hide()
        self.deleteLater()
        Toast._current_toast = None
        
        # Show next queued toast
        if Toast._toast_queue:
            next_toast = Toast._toast_queue.pop(0)
            Toast._show_toast(next_toast)
    
    def _on_action(self):
        """Handle action button click."""
        if self.action_callback:
            self.action_callback()
        self._dismiss()
    
    @classmethod
    def _show_toast(cls, toast: 'Toast'):
        """Internal method to show a toast."""
        cls._current_toast = toast
        toast.show_toast()
    
    @classmethod
    def show_message(
        cls,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
        action_text: str = "",
        action_callback=None,
        parent=None
    ):
        """
        Show a toast notification message.
        
        Args:
            message: Message to display
            toast_type: Type of toast (SUCCESS, ERROR, WARNING, INFO)
            duration: How long to show in milliseconds
            action_text: Optional action button text
            action_callback: Optional callback for action button
            parent: Parent widget
        
        Example:
            >>> Toast.show_message("Saved!", ToastType.SUCCESS)
            >>> Toast.show_message("Error occurred", ToastType.ERROR, duration=5000)
        """
        toast = cls(
            message=message,
            toast_type=toast_type,
            duration=duration,
            action_text=action_text,
            action_callback=action_callback,
            parent=parent
        )
        
        if cls._current_toast is not None:
            # Queue the toast
            cls._toast_queue.append(toast)
        else:
            cls._show_toast(toast)
    
    @classmethod
    def success(cls, message: str, **kwargs):
        """Convenience method for success toast."""
        cls.show_message(message, ToastType.SUCCESS, **kwargs)
    
    @classmethod
    def error(cls, message: str, **kwargs):
        """Convenience method for error toast."""
        cls.show_message(message, ToastType.ERROR, **kwargs)
    
    @classmethod
    def warning(cls, message: str, **kwargs):
        """Convenience method for warning toast."""
        cls.show_message(message, ToastType.WARNING, **kwargs)
    
    @classmethod
    def info(cls, message: str, **kwargs):
        """Convenience method for info toast."""
        cls.show_message(message, ToastType.INFO, **kwargs)
