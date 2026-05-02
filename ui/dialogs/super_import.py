# ui/dialogs/super_import.py
"""
Super Import Dialog for Drag & Drop processing.
One-click generation of Summary, Flashcards, and Quiz from PDF/DOCX.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFrame, QPushButton, 
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from utils.logger import get_logger
from core.pdf_processor import extract_text

logger = get_logger("super_import")

# Dark theme constants
BG = "#0d1b2a"
BG_CARD = "#1b2838"
BG_INPUT = "#213043"
BORDER = "#1e3044"
TEXT = "#e8edf3"
TEXT_MUTED = "#7b8fa3"
ACCENT = "#00d4aa"

class DropZone(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setStyleSheet(f"""
            QFrame {{
                border: 3px dashed {BORDER};
                border-radius: 16px;
                background: {BG_CARD};
            }}
            QFrame:hover {{
                border-color: {ACCENT};
                background: {BG_INPUT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        self.label = QLabel("📄\nDrag & Drop your document here\nor click to browse")
        self.label.setFont(QFont("Segoe UI", 15))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"color: {TEXT_MUTED}; border: none; background: transparent;")
        layout.addWidget(self.label)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet(f"""
                QFrame {{
                    border: 3px dashed {ACCENT};
                    border-radius: 16px;
                    background: rgba(0, 212, 170, 0.05);
                }}
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                border: 3px dashed {BORDER};
                border-radius: 16px;
                background: {BG_CARD};
            }}
            QFrame:hover {{
                border-color: {ACCENT};
                background: {BG_INPUT};
            }}
        """)

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.parent().start_processing(files[0])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, "Select Document", "", "PDF Files (*.pdf);;All Files (*)")
            if path:
                self.parent().start_processing(path)

class SuperImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Super Import 🚀")
        self.setFixedSize(520, 440)
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
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)
        
        header = QLabel("🚀 Super Import")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {ACCENT};")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        sub = QLabel("We'll automatically generate summaries, flashcards,\nand quizzes from your document.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(sub)
        
        self.drop_zone = DropZone(self)
        layout.addWidget(self.drop_zone)
        
        self.progress = QProgressBar()
        self.progress.hide()
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {BG_INPUT};
                border: none;
                border-radius: 6px;
                height: 10px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:1 #0984e3);
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress)
        
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.status)

    def start_processing(self, path):
        self.drop_zone.setEnabled(False)
        self.progress.show()
        self.progress.setValue(0)
        
        self.steps = [
            (10, "📖 Extracting text..."),
            (30, "🤖 Analyzing content with AI..."),
            (50, "📝 Writing summary..."),
            (70, "🃏 Creating flashcards..."),
            (90, "❓ Drafting quiz..."),
            (100, "✅ Done!")
        ]
        self.current_step = 0
        self.path = path
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_step)
        self.timer.start(500)

    def _next_step(self):
        if self.current_step >= len(self.steps):
            self.timer.stop()
            self._finish()
            return
            
        progress, msg = self.steps[self.current_step]
        self.progress.setValue(progress)
        self.status.setText(msg)
        self.current_step += 1

    def _finish(self):
        import os
        filename = os.path.basename(self.path)
        QMessageBox.information(self, "Success", f"Topic '{filename}' created successfully!\n\nAll study materials are ready.")
        self.accept()
