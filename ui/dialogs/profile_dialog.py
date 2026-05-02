# ui/dialogs/profile_dialog.py
"""
User profile dialog for EduMind.
Allows users to view and edit their profile information.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTextEdit, QComboBox, QFileDialog, QMessageBox, QWidget,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from utils.logger import get_logger

logger = get_logger("profile_dialog")

# Dark theme constants
BG = "#0d1b2a"
BG_CARD = "#1b2838"
BG_INPUT = "#213043"
BORDER = "#1e3044"
TEXT = "#e8edf3"
TEXT_MUTED = "#7b8fa3"
ACCENT = "#00d4aa"


class ProfileDialog(QDialog):
    """User profile viewing and editing dialog."""
    
    profile_updated = pyqtSignal()
    
    def __init__(self, user, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("My Profile")
        self.setFixedSize(700, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG};
                color: {TEXT};
            }}
            QLabel {{
                color: {TEXT};
                background: transparent;
            }}
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)
        
        # Header with avatar
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:1 #0984e3);
                border-radius: 15px;
                padding: 28px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        
        # Avatar
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(90, 90)
        avatar_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.15);
                border-radius: 45px;
            }}
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        avatar_label = QLabel("👤")
        avatar_label.setFont(QFont("Segoe UI Emoji", 40))
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setStyleSheet("background: transparent;")
        avatar_layout.addWidget(avatar_label)
        
        header_layout.addWidget(avatar_frame)
        
        # User info
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.user.profile.display_name or self.user.username)
        name_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        name_label.setStyleSheet("color: white; background: transparent;")
        info_layout.addWidget(name_label)
        
        email_label = QLabel(self.user.email)
        email_label.setStyleSheet("color: rgba(255,255,255,0.8); background: transparent; font-size: 13px;")
        info_layout.addWidget(email_label)
        
        stats_layout = QHBoxLayout()
        stats = [
            ("📅", f"Joined {self.user.created_at.strftime('%b %Y')}"),
            ("🔐", self.user.auth_provider.value.title())
        ]
        for icon, text in stats:
            stat = QLabel(f"{icon} {text}")
            stat.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent; margin-right: 15px; font-size: 12px;")
            stats_layout.addWidget(stat)
        stats_layout.addStretch()
        info_layout.addLayout(stats_layout)
        
        header_layout.addLayout(info_layout, stretch=1)
        layout.addWidget(header)
        
        # Form
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        
        form_widget = QWidget()
        form_widget.setStyleSheet(f"background: transparent;")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(14)
        
        # Personal Info Section
        form_layout.addWidget(self._create_section_header("Personal Information"))
        
        grid = QGridLayout()
        grid.setSpacing(12)
        
        grid.addWidget(self._create_field_label("Display Name"), 0, 0)
        self._display_name = self._create_input(self.user.profile.display_name)
        grid.addWidget(self._display_name, 0, 1)
        
        grid.addWidget(self._create_field_label("Username"), 1, 0)
        self._username = self._create_input(self.user.username)
        self._username.setEnabled(False)
        grid.addWidget(self._username, 1, 1)
        
        grid.addWidget(self._create_field_label("Email"), 2, 0)
        self._email = self._create_input(self.user.email)
        self._email.setEnabled(False)
        grid.addWidget(self._email, 2, 1)
        
        form_layout.addLayout(grid)
        
        # Education Section
        form_layout.addWidget(self._create_section_header("Education"))
        
        edu_grid = QGridLayout()
        edu_grid.setSpacing(12)
        
        edu_grid.addWidget(self._create_field_label("School/University"), 0, 0)
        self._school = self._create_input(self.user.profile.school)
        edu_grid.addWidget(self._school, 0, 1)
        
        edu_grid.addWidget(self._create_field_label("Grade/Year"), 1, 0)
        self._grade = QComboBox()
        self._grade.addItems([
            "High School Freshman", "High School Sophomore", 
            "High School Junior", "High School Senior",
            "College Freshman", "College Sophomore",
            "College Junior", "College Senior",
            "Graduate Student", "Other"
        ])
        self._grade.setCurrentText(self.user.profile.grade_level or "Other")
        self._grade.setStyleSheet(f"""
            QComboBox {{
                padding: 10px 14px;
                border: 1px solid {BORDER};
                border-radius: 10px;
                background: {BG_INPUT};
                color: {TEXT};
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                selection-color: #0d1b2a;
            }}
        """)
        edu_grid.addWidget(self._grade, 1, 1)
        
        form_layout.addLayout(edu_grid)
        
        # Bio Section
        form_layout.addWidget(self._create_section_header("About Me"))
        
        self._bio = QTextEdit()
        self._bio.setPlaceholderText("Tell us about yourself and your learning goals...")
        self._bio.setText(self.user.profile.bio)
        self._bio.setMaximumHeight(100)
        self._bio.setStyleSheet(f"""
            QTextEdit {{
                padding: 10px 14px;
                border: 1px solid {BORDER};
                border-radius: 10px;
                background: {BG_INPUT};
                color: {TEXT};
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border-color: {ACCENT};
            }}
        """)
        form_layout.addWidget(self._bio)
        
        form_layout.addStretch()
        form_scroll.setWidget(form_widget)
        layout.addWidget(form_scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD}; color: {TEXT}; border: 1px solid {BORDER};
                padding: 12px 28px; border-radius: 10px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {BG_INPUT}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✅ Save Changes")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:1 #0984e3);
                color: white; border: none; padding: 12px 28px;
                border-radius: 10px; font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background: {ACCENT}; }}
        """)
        save_btn.clicked.connect(self._save_profile)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_section_header(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {ACCENT}; margin-top: 8px;")
        return label
    
    def _create_field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        return label
    
    def _create_input(self, value: str = "") -> QLineEdit:
        input_field = QLineEdit(value or "")
        input_field.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px 14px;
                border: 1px solid {BORDER};
                border-radius: 10px;
                background: {BG_INPUT};
                color: {TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
            QLineEdit:disabled {{
                background: {BG_CARD};
                color: {TEXT_MUTED};
            }}
        """)
        return input_field
    
    def _save_profile(self):
        from core.auth import get_auth_service
        from core.auth.user_model import UserProfile
        
        profile = UserProfile(
            display_name=self._display_name.text().strip(),
            school=self._school.text().strip(),
            grade_level=self._grade.currentText(),
            bio=self._bio.toPlainText().strip(),
            avatar_url=self.user.profile.avatar_url,
            subjects=self.user.profile.subjects,
            study_goals=self.user.profile.study_goals,
            timezone=self.user.profile.timezone,
            language=self.user.profile.language
        )
        
        auth = get_auth_service()
        if auth.update_profile(self.user.id, profile):
            QMessageBox.information(self, "Success", "Profile updated successfully!")
            self.profile_updated.emit()
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not update profile")
