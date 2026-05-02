# ui/themes/theme_manager.py
"""
Theme management system for EduMind.
Supports light/dark themes with system preference detection.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import json
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QSettings


class Theme(Enum):
    """Available theme options."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class ThemeColors:
    """Color scheme for a theme."""
    # Backgrounds
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    
    # Text
    text_primary: str
    text_secondary: str
    text_muted: str
    
    # Brand
    accent_primary: str
    accent_secondary: str
    
    # Semantic
    success: str
    warning: str
    error: str
    info: str
    
    # Borders
    border_light: str
    border_medium: str
    
    # Shadows
    shadow_color: str
    shadow_opacity: float


# Light theme colors
LIGHT_THEME = ThemeColors(
    bg_primary="#ffffff",
    bg_secondary="#f7fafc",
    bg_tertiary="#edf2f7",
    text_primary="#1a202c",
    text_secondary="#2d3748",
    text_muted="#718096",
    accent_primary="#667eea",
    accent_secondary="#764ba2",
    success="#48bb78",
    warning="#ed8936",
    error="#f56565",
    info="#4299e1",
    border_light="#e2e8f0",
    border_medium="#cbd5e0",
    shadow_color="#000000",
    shadow_opacity=0.1
)

# Dark theme colors — Battery Optimizer navy palette
DARK_THEME = ThemeColors(
    bg_primary="#0d1b2a",
    bg_secondary="#1b2838",
    bg_tertiary="#213043",
    text_primary="#e8edf3",
    text_secondary="#c0ccda",
    text_muted="#7b8fa3",
    accent_primary="#00d4aa",
    accent_secondary="#00b894",
    success="#00d4aa",
    warning="#f6ad55",
    error="#fc8181",
    info="#63b3ed",
    border_light="#1e3044",
    border_medium="#2a4058",
    shadow_color="#000000",
    shadow_opacity=0.4
)


class ThemeManager:
    """
    Manages application themes with persistence and system preference detection.
    
    Example:
        >>> theme_manager = ThemeManager()
        >>> theme_manager.set_theme(Theme.DARK)
        >>> colors = theme_manager.colors
        >>> print(colors.bg_primary)
        '#1a202c'
    """
    
    _instance: Optional['ThemeManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._current_theme = Theme.DARK
        self._colors = DARK_THEME
        self._settings = QSettings("EduMind", "EduMind")
        self._apply_theme()
        self._initialized = True
    
    def _load_saved_theme(self):
        """Load the saved theme preference."""
        saved = self._settings.value("theme", Theme.SYSTEM.value)
        try:
            self._current_theme = Theme(saved)
        except ValueError:
            self._current_theme = Theme.SYSTEM
        
        self._apply_theme()
    
    def _detect_system_theme(self) -> Theme:
        """Detect the system's color scheme preference."""
        app = QApplication.instance()
        if app:
            palette = app.palette()
            # Check if background is dark
            bg_color = palette.color(QPalette.ColorRole.Window)
            # Luminance calculation
            luminance = (0.299 * bg_color.red() + 
                        0.587 * bg_color.green() + 
                        0.114 * bg_color.blue()) / 255
            return Theme.DARK if luminance < 0.5 else Theme.LIGHT
        return Theme.LIGHT
    
    def _apply_theme(self):
        """Apply dark theme — always dark."""
        self._current_theme = Theme.DARK
        self._colors = DARK_THEME
    
    @property
    def current_theme(self) -> Theme:
        """Get the current theme setting."""
        return self._current_theme
    
    @property
    def colors(self) -> ThemeColors:
        """Get the current theme colors."""
        return self._colors
    
    @property
    def is_dark(self) -> bool:
        """Check if the current effective theme is dark."""
        if self._current_theme == Theme.SYSTEM:
            return self._detect_system_theme() == Theme.DARK
        return self._current_theme == Theme.DARK
    
    def set_theme(self, theme: Theme):
        """
        Set the application theme.
        
        Args:
            theme: The theme to apply (LIGHT, DARK, or SYSTEM)
        """
        self._current_theme = theme
        self._settings.setValue("theme", theme.value)
        self._apply_theme()
    
    def toggle_theme(self):
        """Theme toggle — always stays dark."""
        pass  # Dark only
    
    def get_stylesheet(self) -> str:
        """
        Generate the complete application stylesheet.
        
        Returns:
            CSS stylesheet string for the entire application
        """
        c = self._colors
        
        return f"""
            /* ===== Global Styles ===== */
            QWidget {{
                background-color: {c.bg_primary};
                color: {c.text_primary};
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            
            /* ===== Main Window ===== */
            QMainWindow {{
                background-color: {c.bg_secondary};
            }}
            
            /* ===== Labels ===== */
            QLabel {{
                color: {c.text_primary};
                background: transparent;
            }}
            
            QLabel[class="muted"] {{
                color: {c.text_muted};
            }}
            
            QLabel[class="heading"] {{
                font-size: 18px;
                font-weight: bold;
            }}
            
            /* ===== Buttons ===== */
            QPushButton {{
                background-color: {c.accent_primary};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background-color: {c.accent_secondary};
            }}
            
            QPushButton:pressed {{
                background-color: {self._darken(c.accent_primary)};
            }}
            
            QPushButton:disabled {{
                background-color: {c.border_medium};
                color: {c.text_muted};
            }}
            
            /* ===== Input Fields ===== */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {c.bg_primary};
                color: {c.text_primary};
                border: 2px solid {c.border_light};
                border-radius: 8px;
                padding: 10px;
                selection-background-color: {c.accent_primary};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {c.accent_primary};
            }}
            
            /* ===== Lists ===== */
            QListWidget {{
                background-color: {c.bg_primary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 8px;
                padding: 5px;
            }}
            
            QListWidget::item {{
                padding: 10px;
                margin: 3px 0;
                border-radius: 6px;
                border-left: 3px solid {c.accent_primary};
                background-color: {c.bg_secondary};
            }}
            
            QListWidget::item:selected {{
                background-color: {c.accent_primary};
                color: white;
            }}
            
            QListWidget::item:hover {{
                background-color: {c.bg_tertiary};
            }}
            
            /* ===== Tabs ===== */
            QTabWidget::pane {{
                border: 2px solid {c.border_light};
                border-radius: 10px;
                background-color: {c.bg_primary};
                padding: 10px;
            }}
            
            QTabBar::tab {{
                background-color: {c.bg_secondary};
                color: {c.text_secondary};
                border: 2px solid {c.border_light};
                padding: 10px 20px;
                margin: 2px;
                border-radius: 8px 8px 0 0;
                font-weight: 600;
            }}
            
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c.accent_primary}, stop:1 {c.accent_secondary});
                color: white;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {c.bg_tertiary};
                border-color: {c.accent_primary};
            }}
            
            /* ===== Scroll Bars ===== */
            QScrollBar:vertical {{
                border: none;
                background: {c.bg_secondary};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {c.accent_primary};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {c.accent_secondary};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                border: none;
                background: {c.bg_secondary};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {c.accent_primary};
                border-radius: 6px;
                min-width: 20px;
            }}
            
            /* ===== Combo Box ===== */
            QComboBox {{
                background-color: {c.bg_primary};
                color: {c.text_primary};
                border: 2px solid {c.border_light};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }}
            
            QComboBox:focus {{
                border-color: {c.accent_primary};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {c.bg_primary};
                color: {c.text_primary};
                selection-background-color: {c.accent_primary};
                selection-color: white;
                border: 1px solid {c.border_light};
                border-radius: 8px;
            }}
            
            /* ===== Group Box ===== */
            QGroupBox {{
                font-weight: bold;
                color: {c.text_primary};
                border: 2px solid {c.border_light};
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 15px;
                background: {c.bg_secondary};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: {c.accent_primary};
            }}
            
            /* ===== Progress Bar ===== */
            QProgressBar {{
                border: none;
                border-radius: 8px;
                background: {c.bg_tertiary};
                height: 16px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c.accent_primary}, stop:1 {c.accent_secondary});
                border-radius: 8px;
            }}
            
            /* ===== Frames ===== */
            QFrame {{
                background-color: {c.bg_primary};
            }}
            
            QFrame[class="card"] {{
                background-color: {c.bg_primary};
                border: 2px solid {c.border_light};
                border-radius: 12px;
            }}
            
            /* ===== Message Box ===== */
            QMessageBox {{
                background-color: {c.bg_primary};
            }}
            
            QMessageBox QLabel {{
                color: {c.text_primary};
            }}
            
            /* ===== Tool Tips ===== */
            QToolTip {{
                background-color: {c.bg_tertiary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 6px;
                padding: 6px;
            }}
            
            /* ===== Menu Bar ===== */
            QMenuBar {{
                background: {c.bg_secondary};
                color: {c.text_primary};
                border-bottom: 1px solid {c.border_light};
                padding: 4px;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 6px 12px;
                border-radius: 6px;
            }}
            QMenuBar::item:selected {{
                background: {c.bg_tertiary};
            }}
            QMenu {{
                background: {c.bg_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {c.accent_primary};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background: {c.border_light};
                margin: 4px 8px;
            }}
            
            /* ===== Check Box / Radio ===== */
            QCheckBox, QRadioButton {{
                color: {c.text_primary};
                spacing: 8px;
            }}
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {c.border_medium};
                border-radius: 4px;
                background: {c.bg_primary};
            }}
            QCheckBox::indicator:checked {{
                background: {c.accent_primary};
                border-color: {c.accent_primary};
            }}
            QRadioButton::indicator {{
                border-radius: 9px;
            }}
            QRadioButton::indicator:checked {{
                background: {c.accent_primary};
                border-color: {c.accent_primary};
            }}
            
            /* ===== Spin Box ===== */
            QSpinBox, QDoubleSpinBox {{
                background: {c.bg_primary};
                color: {c.text_primary};
                border: 2px solid {c.border_light};
                border-radius: 8px;
                padding: 6px;
            }}
            
            /* ===== Status Bar ===== */
            QStatusBar {{
                background: {c.bg_secondary};
                color: {c.text_muted};
                border-top: 1px solid {c.border_light};
            }}
            
            /* ===== Dialog (all dialogs) ===== */
            QDialog {{
                background: {c.bg_primary};
                color: {c.text_primary};
            }}
            
            /* ===== Message Box (alerts, confirmations) ===== */
            QMessageBox {{
                background: {c.bg_primary};
                color: {c.text_primary};
            }}
            QMessageBox QLabel {{
                color: {c.text_primary};
                font-size: 13px;
                padding: 8px;
                background: transparent;
            }}
            QMessageBox QPushButton {{
                background: {c.bg_tertiary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 8px;
                padding: 8px 24px;
                min-width: 80px;
                font-size: 13px;
                font-weight: 500;
            }}
            QMessageBox QPushButton:hover {{
                background: {c.accent_primary};
                color: white;
                border-color: {c.accent_primary};
            }}
            QMessageBox QPushButton:pressed {{
                background: {c.accent_secondary};
            }}
            QMessageBox QPushButton:default {{
                background: {c.accent_primary};
                color: white;
                border-color: {c.accent_primary};
            }}
            
            /* ===== Input Dialog ===== */
            QInputDialog {{
                background: {c.bg_primary};
                color: {c.text_primary};
            }}
            QInputDialog QLabel {{
                color: {c.text_primary};
                font-size: 13px;
                background: transparent;
            }}
            QInputDialog QLineEdit {{
                background: {c.bg_tertiary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                selection-background-color: {c.accent_primary};
            }}
            QInputDialog QLineEdit:focus {{
                border-color: {c.accent_primary};
            }}
            QInputDialog QPushButton {{
                background: {c.bg_tertiary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 8px;
                padding: 8px 24px;
                min-width: 80px;
                font-size: 13px;
            }}
            QInputDialog QPushButton:hover {{
                background: {c.accent_primary};
                color: white;
            }}
            
            /* ===== Tab Widget (consistent across all tabs) ===== */
            QTabWidget {{
                background: {c.bg_primary};
                border: none;
            }}
            QTabWidget::pane {{
                background: {c.bg_primary};
                border: none;
                border-top: 2px solid {c.border_light};
            }}
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {c.text_muted};
                padding: 10px 20px;
                margin: 0 2px;
                border: none;
                border-bottom: 3px solid transparent;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                color: {c.accent_primary};
                border-bottom: 3px solid {c.accent_primary};
                background: transparent;
            }}
            QTabBar::tab:hover {{
                color: {c.text_primary};
                background: rgba(255, 255, 255, 0.03);
            }}
            
            /* ===== Group Box ===== */
            QGroupBox {{
                background: {c.bg_secondary};
                border: 1px solid {c.border_light};
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 20px;
                font-weight: bold;
                color: {c.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: {c.accent_primary};
            }}
            
            /* ===== Tool Tips ===== */
            QToolTip {{
                background: {c.bg_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            
            /* ===== Progress Bar ===== */
            QProgressBar {{
                background: {c.bg_tertiary};
                border: 1px solid {c.border_light};
                border-radius: 8px;
                text-align: center;
                color: white;
                font-size: 11px;
                min-height: 18px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c.accent_primary}, stop:1 {c.accent_secondary});
                border-radius: 7px;
            }}

            /* ===== File Dialog ===== */
            QFileDialog {{
                background: {c.bg_primary};
                color: {c.text_primary};
            }}
            QFileDialog QLabel {{
                color: {c.text_primary};
            }}
            QFileDialog QTreeView {{
                background: {c.bg_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
                border-radius: 6px;
            }}
            QFileDialog QTreeView::item:selected {{
                background: {c.accent_primary};
                color: white;
            }}
            QFileDialog QListView {{
                background: {c.bg_secondary};
                color: {c.text_primary};
                border: 1px solid {c.border_light};
            }}
            QFileDialog QListView::item:selected {{
                background: {c.accent_primary};
                color: white;
            }}

            /* ===== Calendar ===== */
            QCalendarWidget {{
                background: {c.bg_primary};
            }}
            QCalendarWidget QWidget {{
                background: {c.bg_primary};
                color: {c.text_primary};
            }}
            QCalendarWidget QTableView {{
                background: {c.bg_secondary};
                alternate-background-color: {c.bg_tertiary};
                selection-background-color: {c.accent_primary};
                selection-color: white;
                gridline-color: {c.border_light};
            }}
            QCalendarWidget QToolButton {{
                color: {c.text_primary};
                background: {c.bg_secondary};
                border: none;
                border-radius: 6px;
                padding: 6px;
            }}
            QCalendarWidget QToolButton:hover {{
                background: {c.bg_tertiary};
            }}
            QCalendarWidget #qt_calendar_navigationbar {{
                background: {c.bg_secondary};
                border-bottom: 1px solid {c.border_light};
            }}
        """
    
    def _darken(self, hex_color: str, factor: float = 0.85) -> str:
        """Darken a hex color."""
        color = QColor(hex_color)
        return QColor(
            int(color.red() * factor),
            int(color.green() * factor),
            int(color.blue() * factor)
        ).name()
    
    def apply_to_app(self, app: QApplication):
        """
        Apply the current theme stylesheet to the application.
        
        Args:
            app: The QApplication instance
        """
        app.setStyleSheet(self.get_stylesheet())


# Module-level helper function
_theme_manager: Optional[ThemeManager] = None

def get_theme_manager() -> ThemeManager:
    """
    Get the global ThemeManager singleton instance.
    
    Returns:
        The ThemeManager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
