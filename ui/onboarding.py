# ui/onboarding.py
"""
Onboarding Wizard for first-time users.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QLineEdit, QRadioButton, QButtonGroup, QFrame, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from core.auth.user_model import UserProfile
from ui.themes.theme_manager import get_theme_manager, Theme

class OnboardingWizard(QDialog):
    """
    Multi-step wizard for setting up EduMind.
    """
    finished_success = pyqtSignal(dict) # Returns dict of user preferences
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to EduMind 🎓")
        self.setFixedSize(800, 600)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background: white; border-radius: 20px;")
        
        self.user_data = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked pages
        self.stack = QStackedWidget()
        
        # Page 1: Welcome
        self.stack.addWidget(self._create_welcome_page())
        
        # Page 2: Name & Role
        self.stack.addWidget(self._create_profile_page())
        
        # Page 3: Study Goals
        self.stack.addWidget(self._create_goals_page())
        
        # Page 4: Theme
        self.stack.addWidget(self._create_theme_page())
        
        layout.addWidget(self.stack)
        
        # Navigation Bar
        nav_bar = QFrame()
        nav_bar.setStyleSheet("background: #f7fafc; border-top: 1px solid #e2e8f0; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(30, 20, 30, 20)
        
        self.dots = QLabel("• ○ ○ ○")
        self.dots.setStyleSheet("color: #cbd5e0; font-size: 24px; font-weight: bold;")
        self.dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_btn = QPushButton("Get Started")
        self.next_btn.setStyleSheet("""
            background: #667eea; color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: bold; font-size: 14px;
        """)
        self.next_btn.clicked.connect(self._next_page)
        
        self.back_btn = QPushButton("Back")
        self.back_btn.setStyleSheet("color: #718096; border: none; font-weight: bold;")
        self.back_btn.clicked.connect(self._prev_page)
        self.back_btn.hide()
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.dots)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        
        layout.addWidget(nav_bar)

    def _create_page_container(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(50, 50, 50, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        return page, layout

    def _create_welcome_page(self):
        page, layout = self._create_page_container()
        layout.addStretch()
        
        emoji = QLabel("👋")
        emoji.setFont(QFont("Segoe UI Emoji", 64))
        emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(emoji)
        
        title = QLabel("Welcome to EduMind")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        sub = QLabel("Let's set up your personal AI study companion.\nThis will only take a minute.")
        sub.setFont(QFont("Segoe UI", 14))
        sub.setStyleSheet("color: #718096;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        
        layout.addStretch()
        return page

    def _create_profile_page(self):
        page, layout = self._create_page_container()
        
        title = QLabel("Tell us about you")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("What should we call you?")
        self.name_input.setStyleSheet("padding: 15px; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 16px;")
        layout.addWidget(self.name_input)
        
        layout.addSpacing(20)
        layout.addWidget(QLabel("I am a..."))
        
        self.role_group = QButtonGroup()
        roles = ["High School Student", "College Student", "Lifelong Learner", "Professional"]
        for i, role in enumerate(roles):
            rb = QRadioButton(role)
            rb.setStyleSheet("font-size: 14px; padding: 5px;")
            self.role_group.addButton(rb, i)
            layout.addWidget(rb)
        self.role_group.button(0).setChecked(True)
        
        layout.addStretch()
        return page

    def _create_goals_page(self):
        page, layout = self._create_page_container()
        
        title = QLabel("What are your goals?")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        layout.addWidget(title)
        layout.addWidget(QLabel("Select all that apply"))
        
        layout.addSpacing(20)
        
        self.goals = []
        options = [
            "Prepare for exams",
            "Learn a new language",
            "Master a specific skill",
            "Improve focus & productivity",
            "Organize my notes"
        ]
        
        for opt in options:
            cb = QCheckBox(opt)
            cb.setStyleSheet("font-size: 14px; padding: 8px; margin-bottom: 5px;")
            self.goals.append(cb)
            layout.addWidget(cb)
            
        layout.addStretch()
        return page

    def _create_theme_page(self):
        page, layout = self._create_page_container()
        
        title = QLabel("Choose your look")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addSpacing(30)
        
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(20)
        
        # Light Option
        light_frame = QFrame()
        light_frame.setStyleSheet("""
            QFrame { background: white; border: 2px solid #e2e8f0; border-radius: 15px; }
            QFrame:hover { border-color: #667eea; }
        """)
        light_frame.setFixedSize(200, 150)
        lf_layout = QVBoxLayout(light_frame)
        lf_layout.addWidget(QLabel("☀️ Light Mode", alignment=Qt.AlignmentFlag.AlignCenter))
        
        # Dark Option
        dark_frame = QFrame()
        dark_frame.setStyleSheet("""
            QFrame { background: #2d3748; border: 2px solid #4a5568; border-radius: 15px; }
            QFrame:hover { border-color: #667eea; }
            QLabel { color: white; }
        """)
        dark_frame.setFixedSize(200, 150)
        df_layout = QVBoxLayout(dark_frame)
        df_layout.addWidget(QLabel("🌙 Dark Mode", alignment=Qt.AlignmentFlag.AlignCenter))
        
        theme_layout.addStretch()
        theme_layout.addWidget(light_frame)
        theme_layout.addWidget(dark_frame)
        theme_layout.addStretch()
        
        layout.addLayout(theme_layout)
        
        # Simple radio buttons to capture selection logic cleanly
        layout.addSpacing(20)
        self.theme_group = QButtonGroup()
        
        rb_light = QRadioButton("Light Mode")
        rb_dark = QRadioButton("Dark Mode")
        rb_light.setChecked(True)
        
        self.theme_group.addButton(rb_light, 0)
        self.theme_group.addButton(rb_dark, 1)
        
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(rb_light)
        h_layout.addWidget(rb_dark)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        layout.addStretch()
        return page

    def _update_nav(self):
        idx = self.stack.currentIndex()
        
        # Dots
        dots_str = ["○"] * 4
        dots_str[idx] = "•"
        self.dots.setText(" ".join(dots_str))
        
        # Buttons
        if idx == 0:
            self.back_btn.hide()
            self.next_btn.setText("Get Started")
        else:
            self.back_btn.show()
            self.next_btn.setText("Next" if idx < 3 else "Finish")

    def _next_page(self):
        idx = self.stack.currentIndex()
        if idx < 3:
            self.stack.setCurrentIndex(idx + 1)
            self._update_nav()
        else:
            self._finish()

    def _prev_page(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._update_nav()

    def _finish(self):
        # Collect data
        data = {
            "name": self.name_input.text(),
            "role": self.role_group.checkedButton().text(),
            "goals": [cb.text() for cb in self.goals if cb.isChecked()],
            "theme": "dark" if self.theme_group.checkedId() == 1 else "light"
        }
        
        # Apply theme immediately
        tm = get_theme_manager()
        if data['theme'] == 'dark':
            tm.set_theme(Theme.DARK)
        else:
            tm.set_theme(Theme.LIGHT)
            
        self.finished_success.emit(data)
        self.accept()
