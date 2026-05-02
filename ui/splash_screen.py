# ui/splash_screen.py
"""
Animated splash screen for EduMind start-up.
"""

from PyQt6.QtWidgets import (
    QSplashScreen, QProgressBar, QVBoxLayout, QLabel, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter, QLinearGradient

class SplashScreen(QSplashScreen):
    """
    Modern gradient splash screen with loading progress.
    """
    
    def __init__(self):
        # Create a blank pixmap for the base
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.GlobalColor.transparent)
        super().__init__(pixmap)
        
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main Frame with Gradient
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 20px;
            }
        """)
        self.frame.setFixedSize(580, 380)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.setSpacing(20)
        
        # Logo
        logo = QLabel("🎓")
        logo.setFont(QFont("Segoe UI Emoji", 72))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        frame_layout.addWidget(logo)
        
        # Title
        title = QLabel("EduMind")
        title.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title)
        
        # Tagline
        tagline = QLabel("Your AI-Powered Study Assistant")
        tagline.setFont(QFont("Segoe UI", 16))
        tagline.setStyleSheet("color: rgba(255,255,255,0.9); background: transparent;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(tagline)
        
        frame_layout.addSpacing(30)
        
        # Status Label
        self.status = QLabel("Initializing...")
        self.status.setFont(QFont("Segoe UI", 10))
        self.status.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent;")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.status)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setFixedWidth(400)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: rgba(255,255,255,0.2);
                height: 6px;
                border-radius: 3px;
                text-align: center; 
            }
            QProgressBar::chunk {
                background: white;
                border-radius: 3px;
            }
        """)
        self.progress.setTextVisible(False)
        frame_layout.addWidget(self.progress)
        
        layout.addWidget(self.frame)

    def update_progress(self, value, message=None):
        self.progress.setValue(value)
        if message:
            self.status.setText(message)
