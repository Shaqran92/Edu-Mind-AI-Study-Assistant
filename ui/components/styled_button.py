# ui/components/styled_button.py
"""
Styled button component with gradient backgrounds and hover effects.
"""

from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor


class StyledButton(QPushButton):
    """
    A modern styled button with gradient background and hover effects.
    
    Features:
    - Gradient background with customizable colors
    - Hover animation
    - Drop shadow effect
    - Loading state support
    
    Example:
        >>> btn = StyledButton("Click Me", "#667eea", "#764ba2")
        >>> btn.clicked.connect(my_handler)
    """
    
    def __init__(
        self, 
        text: str, 
        color: str = "#667eea", 
        hover_color: str = "#764ba2",
        parent=None
    ):
        super().__init__(text, parent)
        self.primary_color = color
        self.secondary_color = hover_color
        self._is_loading = False
        self._original_text = text
        
        self._setup_style()
        self._setup_shadow()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_style(self):
        """Apply the base stylesheet."""
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {self.primary_color}, stop:1 {self.secondary_color});
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {self.secondary_color}, stop:1 {self.primary_color});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {self._darken(self.primary_color)}, 
                    stop:1 {self._darken(self.secondary_color)});
            }}
            QPushButton:disabled {{
                background: #a0aec0;
                color: #e2e8f0;
            }}
        """)
    
    def _setup_shadow(self):
        """Add drop shadow effect."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
    
    def _darken(self, hex_color: str, factor: float = 0.85) -> str:
        """Darken a hex color."""
        color = QColor(hex_color)
        return QColor(
            int(color.red() * factor),
            int(color.green() * factor),
            int(color.blue() * factor)
        ).name()
    
    def set_loading(self, loading: bool):
        """
        Set the button to a loading state.
        
        Args:
            loading: True to show loading, False to restore
        """
        self._is_loading = loading
        if loading:
            self._original_text = self.text()
            self.setText("⏳ Loading...")
            self.setEnabled(False)
        else:
            self.setText(self._original_text)
            self.setEnabled(True)
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
    
    def set_success_style(self):
        """Change to green success style."""
        self.primary_color = "#48bb78"
        self.secondary_color = "#38a169"
        self._setup_style()
    
    def set_danger_style(self):
        """Change to red danger style."""
        self.primary_color = "#f56565"
        self.secondary_color = "#e53e3e"
        self._setup_style()
    
    def set_warning_style(self):
        """Change to orange warning style."""
        self.primary_color = "#ed8936"
        self.secondary_color = "#dd6b20"
        self._setup_style()


class IconButton(QPushButton):
    """
    A circular icon button for toolbar actions.
    
    Example:
        >>> btn = IconButton("🔄", tooltip="Refresh")
    """
    
    def __init__(
        self, 
        icon: str,
        tooltip: str = "",
        size: int = 40,
        color: str = "#667eea",
        parent=None
    ):
        super().__init__(icon, parent)
        self.setFixedSize(size, size)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: {size // 2}px;
                font-size: {size // 2}px;
            }}
            QPushButton:hover {{
                background: {self._lighten(color)};
            }}
            QPushButton:pressed {{
                background: {self._darken(color)};
            }}
        """)
    
    def _lighten(self, hex_color: str, factor: float = 1.15) -> str:
        color = QColor(hex_color)
        return QColor(
            min(255, int(color.red() * factor)),
            min(255, int(color.green() * factor)),
            min(255, int(color.blue() * factor))
        ).name()
    
    def _darken(self, hex_color: str, factor: float = 0.85) -> str:
        color = QColor(hex_color)
        return QColor(
            int(color.red() * factor),
            int(color.green() * factor),
            int(color.blue() * factor)
        ).name()
