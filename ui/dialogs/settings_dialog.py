# ui/dialogs/settings_dialog.py
"""
Settings dialog for EduMind configuration.
Handles API keys, theme selection, and user preferences.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTabWidget, QWidget, QGroupBox,
    QFormLayout, QCheckBox, QSpinBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.components.styled_button import StyledButton
from ui.themes.theme_manager import ThemeManager, Theme
from config import settings
from utils.logger import get_logger

logger = get_logger("settings_dialog")

# Try to import keyring for secure storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    keyring = None
    KEYRING_AVAILABLE = False
    logger.warning("keyring not available, API keys will not be stored securely")


class SettingsDialog(QDialog):
    """
    Settings dialog for configuring EduMind.
    
    Features:
    - API key configuration (secure storage)
    - Theme selection (light/dark/system)
    - Language preferences
    - Auto-save settings
    
    Signals:
        settings_changed: Emitted when settings are saved
        theme_changed: Emitted when theme is changed
    """
    
    settings_changed = pyqtSignal()
    theme_changed = pyqtSignal(Theme)
    
    SERVICE_NAME = "EduMind"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.setWindowTitle("⚙️ Settings")
        self.setMinimumSize(500, 450)
        self.setModal(True)
        
        self._setup_ui()
        self._load_settings()
        self._apply_theme()
    
    def _setup_ui(self):
        """Create the settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("⚙️ EduMind Settings")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_ai_tab(), "🤖 AI Provider")
        tabs.addTab(self._create_appearance_tab(), "🎨 Appearance")
        tabs.addTab(self._create_study_tab(), "📚 Study")
        tabs.addTab(self._create_about_tab(), "ℹ️ About")
        layout.addWidget(tabs)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = StyledButton("Cancel", "#718096", "#4a5568")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = StyledButton("Save Settings", "#48bb78", "#38a169")
        save_btn.clicked.connect(self._save_settings)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
    
    def _create_ai_tab(self) -> QWidget:
        """Create AI provider configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Provider selection
        provider_group = QGroupBox("AI Provider")
        provider_layout = QFormLayout(provider_group)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI (GPT-4)", "Google Gemini", "Offline Mode"])
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addRow("Provider:", self.provider_combo)
        
        layout.addWidget(provider_group)
        
        # API Key section
        self.api_key_group = QGroupBox("API Configuration")
        api_layout = QFormLayout(self.api_key_group)
        
        # OpenAI key
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        api_layout.addRow("OpenAI API Key:", self.openai_key_input)
        
        # Gemini key
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setPlaceholderText("Enter Gemini API key...")
        api_layout.addRow("Gemini API Key:", self.gemini_key_input)
        
        # Show/hide button
        self.show_keys_btn = QPushButton("👁 Show Keys")
        self.show_keys_btn.setCheckable(True)
        self.show_keys_btn.clicked.connect(self._toggle_key_visibility)
        api_layout.addRow("", self.show_keys_btn)
        
        # Security note
        if KEYRING_AVAILABLE:
            note = QLabel("🔒 Keys are stored securely in your system keychain")
        else:
            note = QLabel("⚠️ Install 'keyring' package for secure key storage")
        note.setStyleSheet("color: #718096; font-size: 11px;")
        api_layout.addRow("", note)
        
        layout.addWidget(self.api_key_group)
        
        # Model selection
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout(model_group)
        
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems(["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        model_layout.addRow("OpenAI Model:", self.openai_model_combo)
        
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.addItems(["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"])
        model_layout.addRow("Gemini Model:", self.gemini_model_combo)
        
        layout.addWidget(model_group)
        layout.addStretch()
        
        return widget
    
    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addRow("Color Theme:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Font settings
        font_group = QGroupBox("Fonts")
        font_layout = QFormLayout(font_group)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        self.font_size_spin.setValue(14)
        font_layout.addRow("Base Font Size:", self.font_size_spin)
        
        layout.addWidget(font_group)
        
        # Animation settings
        anim_group = QGroupBox("Animations")
        anim_layout = QVBoxLayout(anim_group)
        
        self.animations_check = QCheckBox("Enable animations and transitions")
        self.animations_check.setChecked(True)
        anim_layout.addWidget(self.animations_check)
        
        self.reduced_motion_check = QCheckBox("Reduce motion (accessibility)")
        anim_layout.addWidget(self.reduced_motion_check)
        
        layout.addWidget(anim_group)
        layout.addStretch()
        
        return widget
    
    def _create_study_tab(self) -> QWidget:
        """Create study settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Auto-save settings
        save_group = QGroupBox("Auto-Save")
        save_layout = QFormLayout(save_group)
        
        self.autosave_check = QCheckBox("Enable auto-save")
        self.autosave_check.setChecked(True)
        save_layout.addRow("", self.autosave_check)
        
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 30)
        self.autosave_interval.setValue(5)
        self.autosave_interval.setSuffix(" minutes")
        save_layout.addRow("Interval:", self.autosave_interval)
        
        layout.addWidget(save_group)
        
        # Flashcard settings
        flashcard_group = QGroupBox("Flashcards")
        flashcard_layout = QFormLayout(flashcard_group)
        
        self.new_cards_per_day = QSpinBox()
        self.new_cards_per_day.setRange(5, 100)
        self.new_cards_per_day.setValue(20)
        flashcard_layout.addRow("New cards per day:", self.new_cards_per_day)
        
        self.review_cards_per_day = QSpinBox()
        self.review_cards_per_day.setRange(10, 500)
        self.review_cards_per_day.setValue(100)
        flashcard_layout.addRow("Reviews per day:", self.review_cards_per_day)
        
        layout.addWidget(flashcard_group)
        
        # Language settings
        lang_group = QGroupBox("Language")
        lang_layout = QFormLayout(lang_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German", "Chinese", "Japanese"])
        lang_layout.addRow("Default Output:", self.language_combo)
        
        layout.addWidget(lang_group)
        layout.addStretch()
        
        return widget
    
    def _create_about_tab(self) -> QWidget:
        """Create about tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Logo/icon
        icon = QLabel("🎓")
        icon.setStyleSheet("font-size: 64px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        # App name
        name = QLabel("EduMind")
        name.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name)
        
        # Version
        version = QLabel("Version 1.0.0")
        version.setStyleSheet("color: #718096;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        # Description
        desc = QLabel("AI-Powered Study Assistant\nTransform your notes into interactive learning experiences")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Credits
        credits = QLabel("Made with ❤️ by CodeCrafters Team")
        credits.setStyleSheet("color: #718096; margin-top: 20px;")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)
        
        layout.addStretch()
        return widget
    
    def _on_provider_changed(self, index: int):
        """Handle provider selection change."""
        # Show/hide API key fields based on selection
        is_offline = index == 2
        self.api_key_group.setEnabled(not is_offline)
    
    def _toggle_key_visibility(self, checked: bool):
        """Toggle API key visibility."""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.openai_key_input.setEchoMode(mode)
        self.gemini_key_input.setEchoMode(mode)
        self.show_keys_btn.setText("🔒 Hide Keys" if checked else "👁 Show Keys")
    
    def _load_settings(self):
        """Load current settings."""
        # Provider
        provider = settings.provider.lower()
        if provider == "openai":
            self.provider_combo.setCurrentIndex(0)
        elif provider == "gemini":
            self.provider_combo.setCurrentIndex(1)
        else:
            self.provider_combo.setCurrentIndex(2)
        
        # Load API keys from keyring if available
        if KEYRING_AVAILABLE:
            try:
                openai_key = keyring.get_password(self.SERVICE_NAME, "openai_api_key")
                if openai_key:
                    self.openai_key_input.setText(openai_key)
                
                gemini_key = keyring.get_password(self.SERVICE_NAME, "gemini_api_key")
                if gemini_key:
                    self.gemini_key_input.setText(gemini_key)
            except Exception as e:
                logger.error(f"Error loading keys from keyring: {e}")
        else:
            # Fall back to environment variables
            if settings.openai_api_key:
                self.openai_key_input.setText(settings.openai_api_key)
            if settings.gemini_api_key:
                self.gemini_key_input.setText(settings.gemini_api_key)
        
        # Theme
        current_theme = self.theme_manager.current_theme
        if current_theme == Theme.LIGHT:
            self.theme_combo.setCurrentIndex(0)
        elif current_theme == Theme.DARK:
            self.theme_combo.setCurrentIndex(1)
        else:
            self.theme_combo.setCurrentIndex(2)
    
    def _save_settings(self):
        """Save settings."""
        try:
            # Save API keys securely
            if KEYRING_AVAILABLE:
                openai_key = self.openai_key_input.text().strip()
                if openai_key:
                    keyring.set_password(self.SERVICE_NAME, "openai_api_key", openai_key)
                
                gemini_key = self.gemini_key_input.text().strip()
                if gemini_key:
                    keyring.set_password(self.SERVICE_NAME, "gemini_api_key", gemini_key)
            
            # Apply theme
            theme_index = self.theme_combo.currentIndex()
            themes = [Theme.LIGHT, Theme.DARK, Theme.SYSTEM]
            new_theme = themes[theme_index]
            
            if new_theme != self.theme_manager.current_theme:
                self.theme_manager.set_theme(new_theme)
                self.theme_changed.emit(new_theme)
            
            logger.info("Settings saved successfully")
            self.settings_changed.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def _apply_theme(self):
        """Apply current theme to dialog."""
        colors = self.theme_manager.colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.bg_primary};
                color: {colors.text_primary};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {colors.border_light};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QLineEdit, QComboBox, QSpinBox {{
                padding: 8px;
                border: 2px solid {colors.border_light};
                border-radius: 6px;
                background: {colors.bg_secondary};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border-color: {colors.accent_primary};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors.border_light};
                border-radius: 8px;
            }}
        """)
