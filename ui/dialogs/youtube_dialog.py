# ui/dialogs/youtube_dialog.py
"""
Dialog for importing and processing YouTube videos.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QMessageBox, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import requests

from core.youtube import YouTubeService
from utils.logger import get_logger

logger = get_logger("youtube_dialog")

# Dark theme constants
BG = "#0d1b2a"
BG_CARD = "#1b2838"
BG_INPUT = "#213043"
BORDER = "#1e3044"
TEXT = "#e8edf3"
TEXT_MUTED = "#7b8fa3"
ACCENT = "#00d4aa"
ACCENT_BLUE = "#0984e3"

class TranscriptWorker(QThread):
    """Worker thread to fetch transcript."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    transcript_ready = pyqtSignal(str)

    def __init__(self, video_id):
        super().__init__()
        self.video_id = video_id

    def run(self):
        try:
            transcript = YouTubeService.get_transcript(self.video_id)
            if transcript:
                self.transcript_ready.emit(transcript)
            else:
                self.error.emit("Could not fetch transcript. The video might not have captions enabled.")
        except Exception as e:
            self.error.emit(str(e))

class YouTubeDialog(QDialog):
    """Dialog to import a YouTube video for study."""
    
    process_content = pyqtSignal(str, str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import from YouTube 📹")
        self.setFixedSize(620, 520)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG};
                color: {TEXT};
            }}
            QLabel {{
                color: {TEXT};
                background: transparent;
            }}
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
            QTextEdit {{
                padding: 10px;
                border: 1px solid {BORDER};
                border-radius: 10px;
                background: {BG_INPUT};
                color: {TEXT};
                font-size: 12px;
            }}
        """)
        
        self.video_id = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 28, 28, 28)

        # Header
        header = QLabel("📹 YouTube Smart Import")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {ACCENT};")
        layout.addWidget(header)

        sub = QLabel("Enter a video URL to generate notes and flashcards.")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(sub)

        # Input Area
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.textChanged.connect(self._validate_url)
        input_layout.addWidget(self.url_input)

        self.preview_btn = QPushButton("🔍 Load")
        self.preview_btn.setStyleSheet(f"""
            QPushButton {{
                background: #e53e3e; color: white; border: none;
                padding: 10px 18px; border-radius: 10px; font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background: #c53030; }}
            QPushButton:disabled {{ background: {BG_INPUT}; color: {TEXT_MUTED}; }}
        """)
        self.preview_btn.clicked.connect(self._load_preview)
        self.preview_btn.setEnabled(False)
        input_layout.addWidget(self.preview_btn)
        
        layout.addLayout(input_layout)

        # Preview Area
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        self.preview_frame.hide()
        preview_layout = QHBoxLayout(self.preview_frame)
        
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(120, 90)
        self.thumb_label.setStyleSheet(f"background: {BG_INPUT}; border-radius: 6px;")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.thumb_label)
        
        self.vid_info_label = QLabel("Video found!")
        self.vid_info_label.setStyleSheet(f"color: {ACCENT};")
        preview_layout.addWidget(self.vid_info_label)
        
        layout.addWidget(self.preview_frame)

        # Transcript Area
        t_label = QLabel("Transcript Preview:")
        t_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(t_label)
        self.transcript_edit = QTextEdit()
        self.transcript_edit.setPlaceholderText("Transcript will appear here...")
        self.transcript_edit.setReadOnly(True)
        layout.addWidget(self.transcript_edit)

        # Progress
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)

        # Actions
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD}; color: {TEXT}; border: 1px solid {BORDER};
                padding: 10px 24px; border-radius: 10px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {BG_INPUT}; }}
        """)
        
        self.process_btn = QPushButton("✨ Process Content")
        self.process_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_BLUE});
                color: white; border: none; padding: 10px 24px; border-radius: 10px;
                font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background: {ACCENT}; }}
            QPushButton:disabled {{ background: {BG_INPUT}; color: {TEXT_MUTED}; }}
        """)
        self.process_btn.clicked.connect(self._process_transcript)
        self.process_btn.setEnabled(False)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.process_btn)
        layout.addLayout(btn_layout)

    def _validate_url(self, text):
        vid = YouTubeService.extract_video_id(text)
        self.preview_btn.setEnabled(bool(vid))
        if not vid:
            self.preview_frame.hide()

    def _load_preview(self):
        url = self.url_input.text()
        self.video_id = YouTubeService.extract_video_id(url)
        if not self.video_id:
            return

        self.url_input.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        self.worker = TranscriptWorker(self.video_id)
        self.worker.transcript_ready.connect(self._on_transcript_ready)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(lambda: self.progress.hide())
        self.worker.start()

        try:
            info = YouTubeService.get_video_info(self.video_id)
            resp = requests.get(info['thumbnail_url'])
            pixmap = QPixmap()
            pixmap.loadFromData(resp.content)
            self.thumb_label.setPixmap(pixmap.scaled(120, 90, Qt.AspectRatioMode.KeepAspectRatioByExpanding))
            self.preview_frame.show()
        except Exception:
            pass

    def _on_transcript_ready(self, text):
        self.transcript_edit.setText(text)
        self.url_input.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self.progress.hide()

    def _on_error(self, msg):
        QMessageBox.warning(self, "Error", msg)
        self.url_input.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.progress.hide()

    def _process_transcript(self):
        text = self.transcript_edit.toPlainText()
        if not text:
            return
        
        title = f"YouTube Summary - {self.video_id}" 
        self.process_content.emit(text, title)
        self.accept()
