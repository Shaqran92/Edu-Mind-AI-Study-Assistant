# ui/accessibility.py
"""
Accessibility features for EduMind.
Provides keyboard shortcuts, screen reader support, and high contrast modes.
"""

from typing import Dict, Callable, Optional, List
from PyQt6.QtWidgets import QWidget, QApplication, QMainWindow
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QFont, QShortcut

from utils.logger import get_logger

logger = get_logger("accessibility")


class KeyboardShortcutManager:
    """
    Manages keyboard shortcuts for the application.
    
    Example:
        >>> manager = KeyboardShortcutManager(main_window)
        >>> manager.register("Ctrl+S", save_function, "Save current work")
        >>> manager.register("Ctrl+N", new_function, "Create new note")
    """
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.shortcuts: Dict[str, QShortcut] = {}
        self.descriptions: Dict[str, str] = {}
        logger.info("KeyboardShortcutManager initialized")
    
    def register(self, key_sequence: str, callback: Callable, description: str = ""):
        """
        Register a keyboard shortcut.
        
        Args:
            key_sequence: Key combination (e.g., "Ctrl+S", "F5")
            callback: Function to call when shortcut is pressed
            description: Human-readable description for help dialog
        """
        if key_sequence in self.shortcuts:
            logger.warning(f"Overwriting existing shortcut: {key_sequence}")
        
        shortcut = QShortcut(QKeySequence(key_sequence), self.parent)
        shortcut.activated.connect(callback)
        
        self.shortcuts[key_sequence] = shortcut
        self.descriptions[key_sequence] = description
        
        logger.debug(f"Registered shortcut: {key_sequence} -> {description}")
    
    def unregister(self, key_sequence: str):
        """Remove a keyboard shortcut."""
        if key_sequence in self.shortcuts:
            self.shortcuts[key_sequence].deleteLater()
            del self.shortcuts[key_sequence]
            del self.descriptions[key_sequence]
    
    def get_all_shortcuts(self) -> List[Dict[str, str]]:
        """Get list of all registered shortcuts with descriptions."""
        return [
            {"key": key, "description": desc}
            for key, desc in self.descriptions.items()
        ]
    
    def setup_default_shortcuts(
        self,
        on_new: Optional[Callable] = None,
        on_save: Optional[Callable] = None,
        on_open: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_help: Optional[Callable] = None,
        on_search: Optional[Callable] = None,
        on_quit: Optional[Callable] = None
    ):
        """
        Set up common application shortcuts.
        """
        default_shortcuts = [
            ("Ctrl+N", on_new, "New note"),
            ("Ctrl+S", on_save, "Save current work"),
            ("Ctrl+O", on_open, "Open file"),
            ("Ctrl+,", on_settings, "Open settings"),
            ("F1", on_help, "Show help"),
            ("Ctrl+F", on_search, "Search"),
            ("Ctrl+Q", on_quit, "Quit application"),
            ("Ctrl+D", None, "Toggle dark mode"),  # Placeholder
            ("Ctrl+Tab", None, "Next tab"),
            ("Ctrl+Shift+Tab", None, "Previous tab"),
            ("Escape", None, "Close dialog/Cancel"),
        ]
        
        for key, callback, desc in default_shortcuts:
            if callback:
                self.register(key, callback, desc)


class AccessibilityHelper:
    """
    Helper class for accessibility features.
    """
    
    @staticmethod
    def set_accessible_name(widget: QWidget, name: str):
        """Set accessible name for screen readers."""
        widget.setAccessibleName(name)
    
    @staticmethod
    def set_accessible_description(widget: QWidget, description: str):
        """Set accessible description for screen readers."""
        widget.setAccessibleDescription(description)
    
    @staticmethod
    def make_focusable(widget: QWidget):
        """Make a widget focusable via keyboard."""
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    @staticmethod
    def set_tab_order(widgets: List[QWidget]):
        """Set the tab order for a list of widgets."""
        for i in range(len(widgets) - 1):
            QWidget.setTabOrder(widgets[i], widgets[i + 1])
    
    @staticmethod
    def apply_large_text(app: QApplication, scale: float = 1.25):
        """Apply larger text for readability."""
        font = app.font()
        font.setPointSizeF(font.pointSizeF() * scale)
        app.setFont(font)
    
    @staticmethod
    def apply_high_contrast(app: QApplication):
        """Apply high contrast color scheme."""
        from PyQt6.QtGui import QPalette, QColor
        
        palette = QPalette()
        
        # High contrast colors
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 255, 0))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        
        app.setPalette(palette)
        logger.info("High contrast mode applied")


class FocusIndicator(QObject):
    """
    Visual focus indicator for accessibility.
    Shows a visible ring around focused elements.
    """
    
    focus_changed = pyqtSignal(QWidget)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._enabled = True
        
        # Connect to application focus changes
        app = QApplication.instance()
        if app:
            app.focusChanged.connect(self._on_focus_changed)
    
    def _on_focus_changed(self, old: Optional[QWidget], new: Optional[QWidget]):
        """Handle focus change events."""
        if not self._enabled:
            return
        
        # Remove styling from old widget
        if old and hasattr(old, '_original_style'):
            old.setStyleSheet(old._original_style)
        
        # Add focus ring to new widget
        if new:
            self.focus_changed.emit(new)
    
    def enable(self):
        """Enable focus indicators."""
        self._enabled = True
    
    def disable(self):
        """Disable focus indicators."""
        self._enabled = False


# Predefined color schemes for accessibility
HIGH_CONTRAST_STYLESHEET = """
    * {
        background-color: #000000;
        color: #ffffff;
        border-color: #ffffff;
    }
    
    QPushButton {
        background-color: #333333;
        border: 2px solid #ffffff;
        padding: 8px 16px;
        min-height: 40px;
    }
    
    QPushButton:focus {
        border: 3px solid #ffff00;
        outline: 2px solid #ffff00;
    }
    
    QPushButton:hover {
        background-color: #555555;
    }
    
    QLineEdit, QTextEdit {
        background-color: #111111;
        border: 2px solid #ffffff;
        padding: 8px;
    }
    
    QLineEdit:focus, QTextEdit:focus {
        border: 3px solid #ffff00;
    }
    
    QListWidget::item:selected {
        background-color: #ffff00;
        color: #000000;
    }
    
    QTabBar::tab:selected {
        background-color: #ffff00;
        color: #000000;
    }
"""

REDUCED_MOTION_STYLESHEET = """
    * {
        /* Disable all transitions and animations */
        transition: none !important;
        animation: none !important;
    }
"""
