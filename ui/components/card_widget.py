# ui/components/card_widget.py
"""
Card container widget with shadow, rounded corners, and optional header.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QGraphicsDropShadowEffect, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class CardWidget(QFrame):
    """
    A card container with rounded corners, shadow, and optional header.
    
    Features:
    - Customizable background and border colors
    - Drop shadow effect
    - Optional colored header bar
    - Flexible content layout
    
    Example:
        >>> card = CardWidget("Settings", header_color="#667eea")
        >>> card.add_widget(my_content)
    """
    
    def __init__(
        self,
        title: str = "",
        header_color: str = "",
        background: str = "white",
        border_color: str = "#e2e8f0",
        border_radius: int = 12,
        parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.header_color = header_color
        self.background_color = background
        self.border_color = border_color
        self.border_radius = border_radius
        
        self._setup_ui()
        self._apply_style()
        self._setup_shadow()
    
    def _setup_ui(self):
        """Create the card layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header (if title or header_color provided)
        if self.title or self.header_color:
            self.header = QFrame()
            self.header.setObjectName("card-header")
            header_layout = QHBoxLayout(self.header)
            header_layout.setContentsMargins(15, 12, 15, 12)
            
            if self.title:
                title_label = QLabel(self.title)
                title_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        font-weight: bold;
                        color: white;
                        background: transparent;
                    }
                """)
                header_layout.addWidget(title_label)
                header_layout.addStretch()
            
            self.main_layout.addWidget(self.header)
        
        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(10)
        
        self.main_layout.addWidget(self.content_widget)
    
    def _apply_style(self):
        """Apply the card stylesheet."""
        header_style = ""
        if self.header_color:
            header_style = f"""
                QFrame#card-header {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.header_color}, stop:1 {self._shift_color(self.header_color)});
                    border-top-left-radius: {self.border_radius}px;
                    border-top-right-radius: {self.border_radius}px;
                }}
            """
        
        self.setStyleSheet(f"""
            CardWidget {{
                background: {self.background_color};
                border: 2px solid {self.border_color};
                border-radius: {self.border_radius}px;
            }}
            {header_style}
        """)
    
    def _setup_shadow(self):
        """Add drop shadow effect."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
    
    def _shift_color(self, hex_color: str) -> str:
        """Shift a color slightly for gradient effect."""
        color = QColor(hex_color)
        # Shift hue slightly
        h, s, l, a = color.getHsl()
        return QColor.fromHsl((h + 20) % 360, s, l, a).name()
    
    def add_widget(self, widget: QWidget):
        """Add a widget to the card content area."""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the card content area."""
        self.content_layout.addLayout(layout)
    
    def add_stretch(self):
        """Add stretch to content layout."""
        self.content_layout.addStretch()
    
    def set_content_margins(self, left: int, top: int, right: int, bottom: int):
        """Set the content area margins."""
        self.content_layout.setContentsMargins(left, top, right, bottom)


class StatCard(CardWidget):
    """
    A specialized card for displaying statistics with icon, value, and label.
    
    Example:
        >>> stat = StatCard("📚", "42", "Total Notes", "#4299e1")
    """
    
    def __init__(
        self,
        icon: str,
        value: str,
        label: str,
        color: str = "#667eea",
        parent=None
    ):
        super().__init__(parent=parent)
        self.icon = icon
        self.value = value
        self.label = label
        self.color = color
        
        self._setup_stat_content()
    
    def _setup_stat_content(self):
        """Create the stat display layout."""
        # Override default styling
        self.setStyleSheet(f"""
            StatCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.color}, stop:1 {self._darken(self.color)});
                border: none;
                border-radius: 12px;
                min-width: 150px;
                min-height: 120px;
            }}
        """)
        
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                background: transparent;
            }
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label
        label_widget = QLabel(self.label)
        label_widget.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.9);
                font-weight: 600;
                background: transparent;
            }
        """)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.add_widget(icon_label)
        self.add_widget(self.value_label)
        self.add_widget(label_widget)
    
    def _darken(self, hex_color: str, factor: float = 0.8) -> str:
        color = QColor(hex_color)
        return QColor(
            int(color.red() * factor),
            int(color.green() * factor),
            int(color.blue() * factor)
        ).name()
    
    def set_value(self, value: str):
        """Update the displayed value."""
        self.value = value
        self.value_label.setText(value)
