# ui/widgets/toast_notification.py
"""
Non-blocking toast notifications for EduMind.
Slides in from the top-right corner and auto-dismisses.
"""

from PyQt6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSequentialAnimationGroup
)
from PyQt6.QtGui import QFont


# Toast types and their styling
TOAST_STYLES = {
    "success": {
        "bg": "#00d4aa",
        "text": "#0d1b2a",
        "icon": "✅",
        "border": "#00b894"
    },
    "error": {
        "bg": "#fc8181",
        "text": "#0d1b2a",
        "icon": "❌",
        "border": "#e53e3e"
    },
    "warning": {
        "bg": "#f6ad55",
        "text": "#0d1b2a",
        "icon": "⚠️",
        "border": "#dd6b20"
    },
    "info": {
        "bg": "#63b3ed",
        "text": "#0d1b2a",
        "icon": "ℹ️",
        "border": "#3182ce"
    }
}


class ToastNotification(QLabel):
    """
    A non-blocking toast notification that slides in and auto-dismisses.
    
    Usage:
        toast = ToastNotification(parent_widget)
        toast.show_toast("File saved successfully!", "success")
    """
    
    # Track active toasts for stacking
    _active_toasts = []

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)
        self.setFixedWidth(360)
        self.setMinimumHeight(50)
        self.setFont(QFont("Segoe UI", 11))
        
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._slide_out)

    def show_toast(self, message: str, toast_type: str = "info", duration_ms: int = 3000):
        """Show a toast notification."""
        style = TOAST_STYLES.get(toast_type, TOAST_STYLES["info"])
        
        self.setText(f"  {style['icon']}  {message}")
        self.setStyleSheet(f"""
            QLabel {{
                background: {style['bg']};
                color: {style['text']};
                border: 2px solid {style['border']};
                border-radius: 10px;
                padding: 14px 20px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        
        self.adjustSize()
        self.setFixedWidth(360)

        # Position: top-right of parent
        if self.parent():
            parent_rect = self.parent().geometry()
            # Stack below other active toasts
            y_offset = 20
            for t in ToastNotification._active_toasts:
                if t is not self and t.isVisible():
                    y_offset += t.height() + 8
            
            start_x = parent_rect.width()
            end_x = parent_rect.width() - self.width() - 20
            self._start_pos = QPoint(start_x, y_offset)
            self._end_pos = QPoint(end_x, y_offset)
        else:
            self._start_pos = QPoint(400, 20)
            self._end_pos = QPoint(20, 20)
        
        self.move(self._start_pos)
        
        # Track active toasts
        if self not in ToastNotification._active_toasts:
            ToastNotification._active_toasts.append(self)
        
        self.show()
        self.raise_()
        
        # Slide in animation
        self._slide_in = QPropertyAnimation(self, b"pos")
        self._slide_in.setDuration(300)
        self._slide_in.setStartValue(self._start_pos)
        self._slide_in.setEndValue(self._end_pos)
        self._slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_in.start()
        
        # Auto-dismiss
        self._dismiss_timer.start(duration_ms)
    
    def _slide_out(self):
        """Slide out and destroy."""
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(250)
        anim.setStartValue(self.pos())
        anim.setEndValue(self._start_pos)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._cleanup)
        anim.start()
        self._slide_out_anim = anim  # prevent GC

    def _cleanup(self):
        if self in ToastNotification._active_toasts:
            ToastNotification._active_toasts.remove(self)
        self.hide()
        self.deleteLater()

    def mousePressEvent(self, event):
        """Click to dismiss."""
        self._dismiss_timer.stop()
        self._slide_out()
