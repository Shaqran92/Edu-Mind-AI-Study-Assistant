import os
import sys
import json
from typing import List, Dict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTextEdit, QLineEdit, QComboBox, QTabWidget,
    QListWidget, QListWidgetItem, QMessageBox, QFrame, QSplitter, 
    QProgressBar, QScrollArea, QGridLayout, QGroupBox, QStackedWidget,
    QRadioButton, QButtonGroup, QGraphicsOpacityEffect, QCheckBox, QSpinBox,
    QSystemTrayIcon, QDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QPropertyAnimation, QEasingCurve, QMetaObject, Q_ARG
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor, QIcon, QAction, QKeySequence, QShortcut
from ui.widgets.toast_notification import ToastNotification
from ui.workers import AIWorker, QuizWorker, ConceptMapWorker

from data.db import (
    add_xp, get_conn, init_db, add_note, list_notes, get_note, create_new_quiz, 
    get_or_create_flashcards, create_new_quiz, get_stats
)
from core.text_extraction import extract_text
from core.summary import generate_full_study_package
from core.flashcards import generate_flashcards
from core.quiz import generate_quiz, grade_quiz
from core.concept_map import generate_and_visualize_concept_map
from core.voice import speak_text
from core.xp import award
from config import settings
import re
from core.pdf_generator import create_study_guide_pdf
from core.chatbot import EduMindChatbot
from core.chat import NotesChatRetriever

try:
    from core.chatbot import EduMindChatbot
    CHATBOT_AVAILABLE = True
    print("✅ Advanced chatbot (EduMindChatbot) loaded successfully.")
except ImportError as e:
    CHATBOT_AVAILABLE = False
    print(f"⚠️ Could not load advanced chatbot: {e}. Falling back to basic NotesChat.")
    # Define a placeholder if the class is missing entirely, to prevent other errors
    class EduMindChatbot:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Advanced chatbot module is not available.")

class StyledButton(QPushButton):
    def __init__(self, text, color="#667eea", hover_color="#764ba2"):
        super().__init__(text)
        self.color = color
        self.hover_color = hover_color
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {color}, stop:1 {hover_color});
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
                    stop:0 {hover_color}, stop:1 {color});
            }}
            QPushButton:pressed {{
                background: #5a67d8;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

# Replace the DashboardTab class with this updated version

class DashboardTab(QWidget):
    # Navigation signals
    navigate_to_upload = pyqtSignal()
    navigate_to_summary = pyqtSignal()
    navigate_to_quiz = pyqtSignal()
    navigate_to_flashcards = pyqtSignal()
    navigate_to_concept_map = pyqtSignal()
    navigate_to_chat = pyqtSignal()
    navigate_to_pomodoro = pyqtSignal()
    navigate_to_export = pyqtSignal()
    navigate_to_analytics = pyqtSignal()
    navigate_to_quiz_history = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh()
        
        # Auto-refresh every 30 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(30000)

    def _dark_msg(self, title, text, icon="info"):
        """Show a dark-themed message."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        icons = {"info": QMessageBox.Icon.Information, "warning": QMessageBox.Icon.Warning}
        msg.setIcon(icons.get(icon, QMessageBox.Icon.Information))
        msg.setStyleSheet("""
            QMessageBox { background: #0d1b2a; color: #e8edf3; }
            QMessageBox QLabel { color: #e8edf3; background: transparent; font-size: 13px; }
            QPushButton { background: #00d4aa; color: #0d1b2a; border: none; padding: 8px 24px;
                border-radius: 8px; font-weight: bold; min-width: 80px; }
            QPushButton:hover { background: #00e6b8; }
        """)
        msg.exec()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header
        header_frame = QFrame()
        header_frame.setFixedHeight(68)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00d4aa, stop:0.5 #00b894, stop:1 #0984e3);
                border-radius: 12px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header = QLabel("🎓 EduMind Dashboard")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background: transparent;")
        subtitle = QLabel("Your AI-Powered Learning Hub")
        subtitle.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.85); background: transparent;")
        header_left = QVBoxLayout()
        header_left.setSpacing(2)
        header_left.addWidget(header)
        header_left.addWidget(subtitle)
        header_layout.addLayout(header_left)
        header_layout.addStretch()
        
        # Date label on right
        from datetime import datetime
        date_lbl = QLabel(datetime.now().strftime("📅 %b %d, %Y"))
        date_lbl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;")
        header_layout.addWidget(date_lbl)
        layout.addWidget(header_frame)

        # Stats Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)

        self.stats_widgets = {}
        self.stat_value_labels = {}
        stats_data = [
            ("📝", "Total Notes",   "total_notes",   "#4299e1"),
            ("📊", "Quizzes Done",  "total_quizzes", "#00d4aa"),
            ("🔥", "Streak",        "streak",        "#f6ad55"),
            ("⚡", "Total XP",      "xp",            "#a78bfa"),
            ("✅", "Success Rate",  "success_rate",  "#38b2ac"),
            ("🎯", "Daily Goal",   "daily_goal",    "#fc8181"),
        ]

        for i, (icon, title, key, accent) in enumerate(stats_data):
            card, val_label = self.create_stat_widget(icon, title, "0", accent)
            self.stats_widgets[key] = card
            self.stat_value_labels[key] = val_label
            stats_grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(stats_grid)

        # Study streak progress bar
        streak_frame = QFrame()
        streak_frame.setFixedHeight(50)
        streak_frame.setStyleSheet("QFrame { background: #1b2838; border-radius: 10px; border: 1px solid #1e3044; }")
        streak_layout = QHBoxLayout(streak_frame)
        streak_layout.setContentsMargins(14, 8, 14, 8)
        streak_icon = QLabel("🔥")
        streak_icon.setStyleSheet("font-size: 18px; background: transparent;")
        streak_layout.addWidget(streak_icon)
        self._streak_text = QLabel("0 day streak")
        self._streak_text.setStyleSheet("color: #f6ad55; font-weight: bold; font-size: 12px; background: transparent;")
        streak_layout.addWidget(self._streak_text)
        self._streak_bar = QProgressBar()
        self._streak_bar.setMaximum(7)
        self._streak_bar.setValue(0)
        self._streak_bar.setTextVisible(False)
        self._streak_bar.setFixedHeight(8)
        self._streak_bar.setStyleSheet("""
            QProgressBar { background: #213043; border: none; border-radius: 4px; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #f6ad55, stop:1 #00d4aa); border-radius: 4px; }
        """)
        streak_layout.addWidget(self._streak_bar, 1)
        self._streak_goal = QLabel("Goal: 7 days")
        self._streak_goal.setStyleSheet("color: #7b8fa3; font-size: 10px; background: transparent;")
        streak_layout.addWidget(self._streak_goal)
        layout.addWidget(streak_frame)

        # Recent Activity & Quick Actions splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Recent Notes
        recent_frame = QFrame()
        recent_frame.setStyleSheet("QFrame { background: #1b2838; border-radius: 12px; border: 1px solid #1e3044; }")
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setContentsMargins(14, 14, 14, 14)
        recent_layout.setSpacing(8)
        
        recent_title = QLabel("📋 Recent Notes")
        recent_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d4aa; background: transparent;")
        
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("""
            QListWidget { border: none; border-radius: 8px; background: #0d1b2a; padding: 4px; }
            QListWidget::item { padding: 10px; margin: 2px 0; border-left: 3px solid #00d4aa; background: #1b2838; border-radius: 6px; color: #c0ccda; }
            QListWidget::item:selected { background: #00d4aa; color: white; border-left: 3px solid #0984e3; }
            QListWidget::item:hover { background: #213043; }
        """)
        self.recent_list.itemDoubleClicked.connect(self.on_note_selected)

        recent_layout.addWidget(recent_title)
        recent_layout.addWidget(self.recent_list)

        # Quick Actions
        actions_frame = QFrame()
        actions_frame.setStyleSheet("QFrame { background: #1b2838; border-radius: 12px; border: 1px solid #1e3044; }")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(14, 14, 14, 14)
        actions_layout.setSpacing(8)
        
        actions_title = QLabel("⚡ Quick Actions")
        actions_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00d4aa; background: transparent;")
        actions_layout.addWidget(actions_title)

        actions_data = [
            ("📤 Upload",      self.on_upload_clicked,        "#4299e1", "#3182ce"),
            ("📝 Summarize",   self.on_summarize_clicked,     "#a78bfa", "#805ad5"),
            ("❓ Quiz",         self.on_quiz_clicked,          "#f6ad55", "#dd6b20"),
            ("🃏 Flashcards",  self.on_flashcards_clicked,    "#00d4aa", "#00b894"),
            ("🧠 Concept Map", self.on_concept_map_clicked,   "#38b2ac", "#319795"),
            ("🤖 AI Tutor",    self.on_chat_clicked,          "#fc8181", "#e53e3e"),
            ("⏱ Pomodoro",     self.on_pomodoro_clicked,      "#e056a0", "#c44569"),
            ("📊 Analytics",   self.on_analytics_clicked,     "#0984e3", "#0766b8"),
        ]

        actions_grid = QGridLayout()
        actions_grid.setSpacing(8)
        for idx, (text, slot, c1, c2) in enumerate(actions_data):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(42)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c1}, stop:1 {c2});
                    color: white; border: none; padding: 8px 6px; border-radius: 10px;
                    font-weight: bold; font-size: 12px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c2}, stop:1 {c1});
                }}
            """)
            btn.clicked.connect(slot)
            actions_grid.addWidget(btn, idx // 2, idx % 2)
        
        actions_layout.addLayout(actions_grid)
        actions_layout.addStretch()

        content_splitter.addWidget(recent_frame)
        content_splitter.addWidget(actions_frame)
        content_splitter.setSizes([450, 350])

        layout.addWidget(content_splitter)
        
        scroll.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def create_stat_widget(self, icon, title, value, accent):
        widget = QFrame()
        widget.setFixedHeight(75)
        widget.setStyleSheet(f"""
            QFrame {{ background: #1b2838; border-radius: 10px; border: 1px solid #1e3044; }}
            QFrame:hover {{ border-color: {accent}; }}
        """)
        
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(12, 8, 12, 8)
        h_layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setFixedSize(34, 34)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"QLabel {{ background: {accent}; border-radius: 17px; font-size: 15px; }}")
        h_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 10px; color: #7b8fa3; background: transparent;")
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {accent}; background: transparent;")
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        h_layout.addLayout(text_layout)
        h_layout.addStretch()
        
        return widget, value_label

    def refresh(self):
        stats = get_stats()
        self.stat_value_labels['total_notes'].setText(str(stats['total_notes']))
        self.stat_value_labels['total_quizzes'].setText(str(stats['total_quizzes']))
        self.stat_value_labels['streak'].setText(f"{stats['streak']}")
        self.stat_value_labels['xp'].setText(str(stats['xp']))
        
        success_rate = min(95, stats['xp'] // 10)
        self.stat_value_labels['success_rate'].setText(f"{success_rate}%")
        self.stat_value_labels['daily_goal'].setText(f"{min(100, stats['streak'] * 15)}%")

        # Update streak bar
        streak = stats['streak']
        self._streak_bar.setValue(min(7, streak))
        self._streak_text.setText(f"{streak} day streak")
        if streak >= 7:
            self._streak_goal.setText("🎉 Goal reached!")
            self._streak_goal.setStyleSheet("color: #00d4aa; font-size: 10px; font-weight: bold; background: transparent;")

        # Refresh recent notes
        self.recent_list.clear()
        notes = list_notes()[:8]
        for note in notes:
            item = QListWidgetItem(f"📄 {note['title']}")
            item.setData(Qt.ItemDataRole.UserRole, note['id'])
            self.recent_list.addItem(item)

    def on_note_selected(self, item):
        self.navigate_to_summary.emit()

    def on_upload_clicked(self):
        self.navigate_to_upload.emit()

    def _check_notes(self, action_name):
        notes = list_notes()
        if not notes:
            self._dark_msg("No Notes Available",
                f"Please upload a note first before {action_name}.\n\nClick '📤 Upload' to get started!")
            return False
        return True

    def on_summarize_clicked(self):
        if self._check_notes("generating a summary"):
            self.navigate_to_summary.emit()

    def on_quiz_clicked(self):
        if self._check_notes("creating a quiz"):
            self.navigate_to_quiz.emit()

    def on_flashcards_clicked(self):
        if self._check_notes("making flashcards"):
            self.navigate_to_flashcards.emit()

    def on_concept_map_clicked(self):
        if self._check_notes("generating a concept map"):
            self.navigate_to_concept_map.emit()

    def on_chat_clicked(self):
        if self._check_notes("chatting with AI"):
            self.navigate_to_chat.emit()

    def on_pomodoro_clicked(self):
        self.navigate_to_pomodoro.emit()

    def on_analytics_clicked(self):
        self.navigate_to_analytics.emit()

class StudyAssistantTab(QWidget):
    def __init__(self):
        super().__init__()
        self.current_note_id = None
        self.current_summary_id = None
        self.quiz_question_widgets = []
        
        # FIX: Initialize all UI attributes
        self.summary_view = None
        self.keypoints_view = None
        self.flashcard_label = None
        self.concept_label = None
        self.chat_display = None
        self.chatbot = None # For the new chatbot
        self._all_notes = []  # Cache for filtering

        self.setup_ui()
        
        # Enable drag-and-drop
        self.setAcceptDrops(True)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Left sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setStyleSheet("""
            QFrame {
                background: #1b2838;
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #1e3044;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)

        # Notes list
        notes_label = QLabel("Your Notes")
        notes_label.setStyleSheet("""
            QLabel {
                font-size: 18px; 
                font-weight: bold; 
                color: #00d4aa;
                padding: 8px;
                background: transparent;
                border-radius: 8px;
            }
        """)
        
        # Search box for filtering notes
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #1e3044;
                border-radius: 18px;
                padding: 8px 15px;
                background: #213043;
                color: #e8edf3;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00d4aa;
            }
        """)
        self.search_input.setToolTip("Type to filter your notes by title")
        self.search_input.textChanged.connect(self._filter_notes)
        
        self.notes_list = QListWidget()
        self.notes_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #1e3044;
                border-radius: 8px;
                padding: 5px;
                background: #0d1b2a;
            }
            QListWidget::item {
                padding: 10px;
                margin: 4px 0;
                background: #1b2838;
                border-radius: 6px;
                border-left: 3px solid #00d4aa;
                color: #c0ccda;
                font-weight: 500;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4aa, stop:1 #0984e3);
                color: white;
                border-left: 3px solid #00d4aa;
            }
            QListWidget::item:hover {
                background: #213043;
                border-left: 3px solid #00d4aa;
            }
        """)
        self.notes_list.itemSelectionChanged.connect(self.on_note_selected)

        # Upload section
        upload_group = QGroupBox("Upload Notes")
        upload_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #c0ccda;
                border: 1px solid #1e3044;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 15px;
                background: #0d1b2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #00d4aa;
                font-size: 14px;
            }
        """)
        upload_layout = QVBoxLayout(upload_group)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("""
            QLabel {
                color: #7b8fa3; 
                font-size: 12px;
                padding: 8px;
                background: #1b2838;
                border-radius: 6px;
                border: 1px dashed #1e3044;
            }
        """)
        
        upload_btn = StyledButton("Choose File", "#48bb78", "#38a169")
        upload_btn.clicked.connect(self.choose_file)
        upload_btn.setToolTip("📤 Select a PDF, DOCX, TXT, or MD file to import")
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter note title...")
        self.title_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #1e3044;
                border-radius: 8px;
                padding: 10px;
                background: #213043;
                color: #e8edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00d4aa;
            }
        """)
        
        import_btn = StyledButton("Import Note", "#667eea", "#764ba2")
        import_btn.clicked.connect(self.import_note)
        import_btn.setToolTip("📥 Import the selected file into your study library")

        upload_layout.addWidget(self.file_label)
        upload_layout.addWidget(upload_btn)
        title_label = QLabel("Title:")
        title_label.setStyleSheet("color: #c0ccda; font-weight: 600;")
        upload_layout.addWidget(title_label)
        upload_layout.addWidget(self.title_input)
        upload_layout.addWidget(import_btn)

        # Word count / reading time indicator
        self.note_info_label = QLabel("")
        self.note_info_label.setStyleSheet("""
            QLabel {
                color: #7b8fa3;
                font-size: 11px;
                padding: 4px 8px;
                background: #213043;
                border-radius: 4px;
            }
        """)
        self.note_info_label.hide()
        self.note_info_label.setToolTip("Word count and estimated reading time for the selected note")

        sidebar_layout.addWidget(notes_label)
        sidebar_layout.addWidget(self.search_input)
        sidebar_layout.addWidget(self.notes_list)
        sidebar_layout.addWidget(self.note_info_label)
        sidebar_layout.addWidget(upload_group)
        sidebar_layout.addStretch()

        # Main content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background: #0d1b2a;
                border-radius: 12px;
                border: 1px solid #1e3044;
            }
        """)
        
        # Welcome screen
        welcome_widget = self.create_welcome_screen()
        self.content_stack.addWidget(welcome_widget)
        
        # Study tools screen
        self.study_tools_widget = self.create_study_tools_screen()
        self.content_stack.addWidget(self.study_tools_widget)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_stack)

        self.refresh_notes()

    def create_welcome_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Animated welcome with icons
        icon_label = QLabel("")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 64px;
                background: transparent;
            }
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_label = QLabel("Welcome to EduMind!")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 36px; 
                font-weight: bold; 
                color: #00d4aa;
                margin: 20px;
                background: transparent;
            }
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        instruction_label = QLabel("Select a note from the sidebar to get started\nwith AI-powered study tools!")
        instruction_label.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                color: #7b8fa3;
                background: transparent;
                line-height: 1.5;
            }
        """)
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setWordWrap(True)
        
        # Feature highlights
        features_frame = QFrame()
        features_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1b2838, stop:1 #213043);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 50px;
                border: 1px solid #1e3044;
            }
        """)
        features_layout = QHBoxLayout(features_frame)
        
        features = ["Smart Summaries", "Flashcards", "Quizzes", "AI Chat"]
        for feat in features:
            feat_label = QLabel(feat)
            feat_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #00d4aa;
                    font-weight: 600;
                    background: transparent;
                }
            """)
            features_layout.addWidget(feat_label)
        
        layout.addWidget(icon_label)
        layout.addWidget(welcome_label)
        layout.addWidget(instruction_label)
        layout.addWidget(features_frame)
        
        return widget

    def create_study_tools_screen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # Tool selection tabs
        self.tools_tabs = QTabWidget()
        self.tools_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1e3044;
                border-radius: 10px;
                background: #0d1b2a;
                padding: 10px;
            }
            QTabBar::tab {
                background: #1b2838;
                border: 1px solid #1e3044;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 8px 8px 0 0;
                color: #7b8fa3;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4aa, stop:1 #0984e3);
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #213043;
                border-color: #00d4aa;
            }
        """)
        
        # Summary Tab
        self.summary_tab = self.create_summary_tab()
        self.tools_tabs.addTab(self.summary_tab, "Summary")
        
        # Flashcards Tab
        self.flashcards_tab = self.create_flashcards_tab()
        self.tools_tabs.addTab(self.flashcards_tab, "Flashcards")
        
        # Quiz Tab
        self.quiz_tab = self.create_quiz_tab()
        self.tools_tabs.addTab(self.quiz_tab, "Quiz")
        
        # Concept Map Tab
        self.concept_tab = self.create_concept_map_tab()
        self.tools_tabs.addTab(self.concept_tab, "Concept Map")
        
        # AI Chat Tab
        self.chat_tab = self.create_chat_tab()
        self.tools_tabs.addTab(self.chat_tab, "AI Tutor")

        layout.addWidget(self.tools_tabs)
        export_pdf_btn = StyledButton("Download Full Study Guide as PDF", "#38b2ac", "#319795")
        export_pdf_btn.clicked.connect(self.export_to_pdf)
        layout.addWidget(export_pdf_btn, 0, Qt.AlignmentFlag.AlignCenter)
    
        return widget

    def export_to_pdf(self):
        """Multi-format export: PDF, Markdown, Text, HTML."""
        try:
            if not self.current_note_id:
                self.show_styled_message("warning", "No Note Selected", "Please select a note and generate content before exporting.")
                return

            note = get_note(self.current_note_id)
            base_name = note['title'].replace(' ', '_')
            
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "Export Study Guide", f"EduMind_Guide_{base_name}",
                "PDF Files (*.pdf);;Markdown Files (*.md);;Text Files (*.txt);;HTML Files (*.html)"
            )

            if not file_path:
                return

            data_to_export = {
                'title': note['title'],
                'summary': self.summary_view.toPlainText(),
                'key_points': [p.strip() for p in self.keypoints_view.toPlainText().replace('•', '').split('\n') if p.strip()],
                'quiz': getattr(self, 'current_quiz', None),
                'concept_map_path': os.path.join(settings.assets_dir or "assets", f"concept_map_{self.current_note_id}.png")
            }

            if not data_to_export['summary'] and not data_to_export['quiz']:
                self.show_styled_message("warning", "No Content", "Please generate at least a summary or a quiz before exporting.")
                return
            
            # Route to appropriate export function
            success = False
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.md':
                from core.export_service import export_to_markdown
                success = export_to_markdown(data_to_export, file_path)
            elif ext == '.txt':
                from core.export_service import export_to_text
                success = export_to_text(data_to_export, file_path)
            elif ext == '.html':
                from core.export_service import export_to_html
                success = export_to_html(data_to_export, file_path)
            else:
                success = create_study_guide_pdf(file_path, data_to_export)

            if success:
                self.show_styled_message("info", "Success!", f"Study guide exported to:\n{file_path}")
            else:
                self.show_styled_message("critical", "Error", "Export failed. The file format may not be supported or there was an error generating the file.")
        except Exception as e:
            self.show_styled_message("critical", "Export Error", f"An error occurred during export:\n{str(e)}")

    def create_summary_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Controls - Fixed layout to prevent overlapping
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background: #1b2838;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        controls_main_layout = QVBoxLayout(controls_frame)
        controls_main_layout.setSpacing(10)
        
        # First row - Dropdowns
        dropdown_layout = QHBoxLayout()
        dropdown_layout.setSpacing(10)
        
        label_style = "color: #c0ccda; font-weight: 600; font-size: 13px;"
        combo_style = """
            QComboBox {
                border: 1px solid #1e3044;
                border-radius: 6px;
                padding: 8px;
                background: #213043;
                color: #e8edf3;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #00d4aa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #1b2838;
                color: #e8edf3;
                selection-background-color: #00d4aa;
            }
        """
        
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet(label_style)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Concise", "Detailed", "Academic", "Simple"])
        self.mode_combo.setStyleSheet(combo_style)
        
        length_label = QLabel("Length:")
        length_label.setStyleSheet(label_style)
        self.length_combo = QComboBox()
        self.length_combo.addItems(["Short", "Medium", "Long"])
        self.length_combo.setStyleSheet(combo_style)
        
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet(label_style)
        self.lang_combo = QComboBox()
        languages = ["English", "Spanish", "French", "German", "Italian",
                    "Portuguese", "Chinese", "Japanese", "Korean", "Arabic", 
                    "Hindi", "Russian"]
        self.lang_combo.addItems(languages)
        self.lang_combo.setStyleSheet(combo_style)
        
        dropdown_layout.addWidget(mode_label)
        dropdown_layout.addWidget(self.mode_combo)
        dropdown_layout.addWidget(length_label)
        dropdown_layout.addWidget(self.length_combo)
        dropdown_layout.addWidget(lang_label)
        dropdown_layout.addWidget(self.lang_combo)
        dropdown_layout.addStretch()
        
        # Second row - Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        generate_btn = StyledButton("Generate Summary", "#667eea", "#764ba2")
        generate_btn.clicked.connect(self.generate_summary)
        
        speak_btn = StyledButton("🔊 Speak", "#48bb78", "#38a169")
        speak_btn.clicked.connect(self.speak_summary)

        button_layout.addWidget(generate_btn)
        button_layout.addWidget(speak_btn)
        button_layout.addStretch()

        controls_main_layout.addLayout(dropdown_layout)
        controls_main_layout.addLayout(button_layout)

        # Summary display
        summary_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Summary
        summary_group = QGroupBox("Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #00d4aa;
                border: 1px solid #1e3044;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """)
        summary_layout = QVBoxLayout(summary_group)
        self.summary_view = QTextEdit()
        self.summary_view.setStyleSheet("""
            QTextEdit {
                border: 1px solid #1e3044;
                border-radius: 8px;
                padding: 12px;
                background: #1b2838;
                color: #e8edf3;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        summary_layout.addWidget(self.summary_view)
        
        # Key Points
        points_group = QGroupBox("Key Points")
        points_group.setStyleSheet(summary_group.styleSheet())
        points_layout = QVBoxLayout(points_group)
        self.keypoints_view = QTextEdit()
        self.keypoints_view.setStyleSheet(self.summary_view.styleSheet())
        points_layout.addWidget(self.keypoints_view)

        summary_splitter.addWidget(summary_group)
        summary_splitter.addWidget(points_group)
        summary_splitter.setSizes([400, 200])

        layout.addWidget(controls_frame)
        layout.addWidget(summary_splitter)
        
        return widget

    def create_flashcards_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # --- Controls ---
        controls_layout = QGridLayout()
        controls_layout.setSpacing(10)
        
        generate_btn = StyledButton("Generate Flashcards", "#667eea", "#764ba2")
        generate_btn.clicked.connect(self.generate_flashcards)
        
        self.flip_btn = StyledButton("🔄 Flip Card", "#48bb78", "#38a169")
        self.flip_btn.clicked.connect(self.flip_flashcard)
        self.flip_btn.setEnabled(False)
        
        self.prev_btn = StyledButton("⬅ Previous", "#ed8936", "#dd6b20")
        self.prev_btn.clicked.connect(self.prev_flashcard)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = StyledButton("Next ➡", "#4299e1", "#3182ce")
        self.next_btn.clicked.connect(self.next_flashcard)
        self.next_btn.setEnabled(False)

        self.export_csv_btn = StyledButton("📥 Export CSV", "#805ad5", "#6b46c1")
        self.export_csv_btn.clicked.connect(self.export_flashcards_csv)
        self.export_csv_btn.setEnabled(False)

        self.speak_card_btn = StyledButton("🔊 Speak", "#48bb78", "#38a169")
        self.speak_card_btn.clicked.connect(self.speak_flashcard)
        self.speak_card_btn.setEnabled(False)

        controls_layout.addWidget(generate_btn, 0, 0, 1, 2)
        controls_layout.addWidget(self.prev_btn, 1, 0)
        controls_layout.addWidget(self.next_btn, 1, 1)
        controls_layout.addWidget(self.flip_btn, 0, 2, 2, 1)
        controls_layout.addWidget(self.export_csv_btn, 0, 3, 1, 1)
        controls_layout.addWidget(self.speak_card_btn, 1, 3, 1, 1)
        
        layout.addLayout(controls_layout)

        # --- Flashcard Display ---
        self.flashcard_frame = QFrame()
        self.flashcard_frame.setMinimumHeight(350)
        frame_layout = QHBoxLayout(self.flashcard_frame)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.flashcard_stack = QStackedWidget()
        frame_layout.addWidget(self.flashcard_stack)

        # --- Card Faces ---
        self.flashcards_data = []
        self.current_flashcard_idx = 0
        self.question_widget, self.question_content_label = self._create_card_face("Question", "#00d4aa", "#0984e3")
        self.flashcard_stack.addWidget(self.question_widget)

        self.answer_widget, self.answer_content_label = self._create_card_face("Answer", "#48bb78", "#38a169")
        self.flashcard_stack.addWidget(self.answer_widget)

        # --- Progress Label ---
        self.card_progress = QLabel("")
        self.card_progress.setStyleSheet("color: #7b8fa3; font-size: 14px; font-weight: 600; background: transparent;")
        self.card_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.flashcard_frame, 1)
        layout.addWidget(self.card_progress)

        # --- State Initialization ---
        # NO animation setup here. It's handled by the flip_flashcard method.
        # This is the key change that removes the error.
        self.flashcards = []
        self.current_card_index = 0
        self.showing_question = True
        
        return widget

    def _create_card_face(self, title_text, color1, color2):
        """Create a styled card face (Question or Answer) that expands to fit content."""
        card_face = QFrame()
        card_face.setMinimumSize(400, 250)
        card_face.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {color1}, stop:1 {color2});
                border-radius: 20px;
                padding: 25px;
            }}
        """)
        
        face_layout = QVBoxLayout(card_face)
        face_layout.setSpacing(15)
        face_layout.setContentsMargins(25, 20, 25, 20)

        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
                border-bottom: 2px solid rgba(255, 255, 255, 0.3);
                padding-bottom: 10px;
            }
        """)
        
        content_label = QLabel("Generate flashcards to begin!")
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                background: transparent;
                padding: 10px;
            }
        """)
        
        face_layout.addWidget(title_label)
        face_layout.addWidget(content_label, 1)
        
        return card_face, content_label

    def create_quiz_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Controls
        controls_layout = QHBoxLayout()
        generate_btn = StyledButton("Generate Quiz", "#667eea", "#764ba2")
        generate_btn.clicked.connect(self.generate_quiz)
        
        self.submit_quiz_btn = StyledButton("Submit Quiz", "#48bb78", "#38a169")
        self.submit_quiz_btn.clicked.connect(self.grade_quiz)
        self.submit_quiz_btn.setEnabled(False)
        
        controls_layout.addWidget(generate_btn)
        controls_layout.addWidget(self.submit_quiz_btn)
        controls_layout.addStretch()

        # Quiz area with scroll
        self.quiz_scroll = QScrollArea()
        self.quiz_scroll.setWidgetResizable(True)
        self.quiz_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #1e3044;
                border-radius: 10px;
                background: #0d1b2a;
            }
            QScrollBar:vertical {
                border: none;
                background: #1b2838;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #00d4aa;
                border-radius: 5px;
            }
        """)
        
        self.quiz_widget = QWidget()
        self.quiz_layout = QVBoxLayout(self.quiz_widget)
        self.quiz_layout.setSpacing(15)
        self.quiz_scroll.setWidget(self.quiz_widget)

        layout.addLayout(controls_layout)
        layout.addWidget(self.quiz_scroll)
        
        return widget

    def create_concept_map_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        generate_btn = StyledButton("Generate Concept Map", "#667eea", "#764ba2")
        generate_btn.clicked.connect(self.generate_concept_map)

        self.concept_label = QLabel("Concept map will appear here")
        self.concept_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.concept_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #1e3044;
                border-radius: 12px;
                padding: 50px;
                color: #7b8fa3;
                font-size: 18px;
                background: #1b2838;
            }
        """)

        layout.addWidget(generate_btn)
        layout.addWidget(self.concept_label)
        
        return widget

    def create_chat_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # -- Top Bar: Persona & Controls --
        controls_layout = QHBoxLayout()
        
        # Persona Selector
        controls_layout.addWidget(QLabel("Tutor:"))
        self.persona_combo = QComboBox()
        from core.personas import PERSONAS
        for pid, p in PERSONAS.items():
            self.persona_combo.addItem(f"{p.icon} {p.name}", pid)
        self.persona_combo.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #1e3044; background: #213043; color: #e8edf3;")
        controls_layout.addWidget(self.persona_combo)
        
        controls_layout.addStretch()
        
        # Speaker Toggle
        self.speak_check = QCheckBox("Read Aloud")
        self.speak_check.setStyleSheet("color: #c0ccda;")
        controls_layout.addWidget(self.speak_check)
        
        layout.addLayout(controls_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #1e3044;
                border-radius: 10px;
                padding: 15px;
                background: #1b2838;
                color: #e8edf3;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        self.chat_display.setReadOnly(True)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: #1b2838;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask anything about your notes...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #1e3044;
                border-radius: 20px;
                padding: 12px 20px;
                background: #213043;
                color: #e8edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        
        send_btn = StyledButton("Send", "#667eea", "#764ba2")
        send_btn.clicked.connect(self.send_chat_message)
        
        # Voice Button (Mic)
        self.mic_btn = StyledButton("🎤", "#48bb78", "#38a169")
        self.mic_btn.clicked.connect(self.start_voice_chat)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.mic_btn)
        input_layout.addWidget(send_btn)

        layout.addWidget(self.chat_display)
        layout.addWidget(input_frame)

        self.chat_index = None
        
        return widget

    def refresh_notes(self):
        self.notes_list.clear()
        self._all_notes = list_notes()
        for note in self._all_notes:
            item = QListWidgetItem(note['title'])
            item.setData(Qt.ItemDataRole.UserRole, note['id'])
            self.notes_list.addItem(item)
    
    def _filter_notes(self, search_text):
        """Filter notes list based on search text."""
        self.notes_list.clear()
        query = search_text.strip().lower()
        for note in self._all_notes:
            if not query or query in note['title'].lower():
                item = QListWidgetItem(f"📄 {note['title']}")
                item.setData(Qt.ItemDataRole.UserRole, note['id'])
                self.notes_list.addItem(item)

    def on_note_selected(self):
        selected_items = self.notes_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        self.current_note_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Switch to study tools view
        self.content_stack.setCurrentIndex(1)
        
        # Reset all views
        if self.summary_view: self.summary_view.clear()
        if self.keypoints_view: self.keypoints_view.clear()
        if self.flashcard_label: self.flashcard_label.setText("Select 'Generate Flashcards' to start!")
        self.clear_quiz_display()
        if self.concept_label: self.concept_label.setText("Click 'Generate Concept Map' to create visualization")
        
        # Safely clear chat and re-initialize
        if hasattr(self, 'chatbot') and self.chatbot:
            self.chatbot.clear_history()
        
        if hasattr(self, 'chat_display') and self.chat_display:
            self.chat_display.clear()
        
        # Initialize the chatbot OR the basic retriever for the selected note
        note = get_note(self.current_note_id)
        if note:
            # Update word count / reading time
            self._update_word_count(note['content'] if note['content'] else '')
            
            if CHATBOT_AVAILABLE:
                self.chatbot = EduMindChatbot(note["content"], note["title"])
                self.chat_display.append(f"<b style='color:#4299e1;'>🤖 AI Tutor ready for: {note['title']}</b><br/>Ask me anything!")
            else:
                # FIX IS HERE: Use the new class name NotesChatRetriever
                self.chat_index = NotesChatRetriever(note["content"])
                self.chat_display.append(f"📚 Ready to chat about: {note['title']}\n")
    
    def _update_word_count(self, content):
        """Show word count and estimated reading time."""
        if not content:
            self.note_info_label.hide()
            return
        words = len(content.split())
        reading_minutes = max(1, words // 200)  # avg 200 wpm
        self.note_info_label.setText(f"📝 {words:,} words · ⏱ ~{reading_minutes} min read")
        self.note_info_label.show()
    
    def dragEnterEvent(self, event):
        """Accept drag events for supported file types."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile().lower()
                if path.endswith(('.pdf', '.docx', '.txt', '.md')):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dropEvent(self, event):
        """Handle dropped files."""
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.pdf', '.docx', '.txt', '.md')):
                self.current_file_path = path
                self.file_label.setText(f"✅ {os.path.basename(path)}")
                self.file_label.setStyleSheet("""
                    QLabel {
                        color: #2d3748;
                        font-size: 12px;
                        font-weight: 600;
                        padding: 8px;
                        background: #c6f6d5;
                        border-radius: 6px;
                        border: 1px solid #48bb78;
                    }
                """)
                if not self.title_input.text():
                    self.title_input.setText(os.path.splitext(os.path.basename(path))[0])
                QMessageBox.information(self, "File Ready", f"📤 '{os.path.basename(path)}' dropped!\nClick 'Import Note' to add it.")
                break

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Study Material", "",
            "Documents (*.pdf *.docx *.txt *.md);;All Files (*)"
        )
        if path:
            self.current_file_path = path
            self.file_label.setText(f"✅ {os.path.basename(path)}")
            self.file_label.setStyleSheet("""
                QLabel {
                    color: #2d3748;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 8px;
                    background: #c6f6d5;
                    border-radius: 6px;
                    border: 1px solid #48bb78;
                }
            """)
            if not self.title_input.text():
                self.title_input.setText(os.path.splitext(os.path.basename(path))[0])

    def import_note(self):
        if not hasattr(self, 'current_file_path') or not self.current_file_path:
            QMessageBox.warning(self, "Warning", "Please choose a file first.")
            return
            
        title = self.title_input.text().strip() or os.path.basename(self.current_file_path)
        try:
            content, file_type = extract_text(self.current_file_path)
            if not content.strip():
                QMessageBox.warning(self, "Warning", "The file appears to be empty or couldn't be read.")
                return
                
            nid = add_note(title, self.current_file_path, content)
            award("import_note")
            QMessageBox.information(self, "Success", f"✅ Imported: {title}")
            
            # Reset form
            self.file_label.setText("No file selected")
            self.file_label.setStyleSheet("""
                QLabel {
                    color: #718096;
                    font-size: 12px;
                    padding: 8px;
                    background: white;
                    border-radius: 6px;
                    border: 1px dashed #cbd5e0;
                }
            """)
            self.title_input.clear()
            delattr(self, 'current_file_path')
            
            self.refresh_notes()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import: {str(e)}")

    def generate_summary(self):
        if not self.current_note_id:
            self.show_styled_message("warning", "No Note Selected", "Please select a note first.")
            return

        note = get_note(self.current_note_id)
        if not note or not note["content"]:
            self.show_styled_message("critical", "Empty Note", "The selected note has no content.")
            return

        mode     = self.mode_combo.currentText().lower()
        length   = self.length_combo.currentText().lower()
        language = self.lang_combo.currentText().lower()

        # UI feedback — non-blocking
        self.summary_view.setPlainText("⏳ Generating summary… please wait.")
        self.keypoints_view.setPlainText("")
        QApplication.processEvents()

        from core.summary import generate_full_study_package
        from core.llm import get_provider
        from ui.workers import AIWorker

        # Keep a reference so the worker isn't GC'd
        self._summary_worker = AIWorker(
            generate_full_study_package,
            note["content"], mode, length, language,
            task_name="Summary"
        )
        self._summary_worker.finished_with_result.connect(
            lambda pkg: self._on_summary_done(pkg, mode, length, language)
        )
        self._summary_worker.error_occurred.connect(
            lambda err: self.show_styled_message("critical", "Error", err)
        )
        self._summary_worker.start()

    def _on_summary_done(self, study_package: dict, mode: str, length: str, language: str):
        """Called from AIWorker signal when summary generation completes."""
        summary_text     = study_package.get("summary", "Error: No summary generated.")
        key_points_list  = study_package.get("key_points", [])
        flashcards_list  = study_package.get("flashcards", [])

        self.summary_view.setPlainText(summary_text)
        self.keypoints_view.setPlainText("\n".join(f"• {p}" for p in key_points_list))

        # Persist to DB (cache for quiz/flashcard use)
        try:
            from data.db import get_conn
            with get_conn() as conn:
                existing = conn.execute(
                    "SELECT id FROM summaries WHERE note_id=? AND mode=? AND length=? AND language=? LIMIT 1",
                    (self.current_note_id, mode, length, language)
                ).fetchone()
                if not existing:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO summaries(note_id,mode,length,language,text,key_points,created_at) "
                        "VALUES(?,?,?,?,?,?,datetime('now'))",
                        (self.current_note_id, mode, length, language,
                         summary_text, json.dumps(key_points_list))
                    )
                    self.current_summary_id = c.lastrowid
                    if flashcards_list:
                        c.execute(
                            "INSERT INTO flashcards(summary_id,cards_json,created_at) VALUES(?,?,datetime('now'))",
                            (self.current_summary_id, json.dumps(flashcards_list))
                        )
                    conn.commit()
                else:
                    self.current_summary_id = existing['id']
        except Exception as e:
            print(f"[DB] Failed to cache summary: {e}")

        award("generate_summary")
        # Auto-populate flashcards from the package (no extra AI call needed)
        if flashcards_list:
            self.flashcards = flashcards_list
            self.current_card_index  = 0
            self.showing_question    = True
            self.show_current_card()
            for btn in (self.flip_btn, self.prev_btn, self.next_btn, self.export_csv_btn, self.speak_card_btn):
                btn.setEnabled(True)
        self.show_styled_message(
            "info", "Done!",
            f"✅ Summary, key points and {len(flashcards_list)} flashcards generated!"
        )


    def speak_summary(self):
        text = self.summary_view.toPlainText()
        if text and text != "🔄 Generating summary...":
            speak_text(text[:500])

    def generate_flashcards(self):
        if not self.current_summary_id:
            QMessageBox.warning(self, "Warning", "Please generate a summary first.")
            return

        try:
            row = get_or_create_flashcards(self.current_summary_id, generate_flashcards)
            import json
            self.flashcards = json.loads(row["cards_json"])
            
            if self.flashcards:
                self.current_card_index = 0
                self.showing_question = True
                self.show_current_card()
                self.flip_btn.setEnabled(True)
                self.prev_btn.setEnabled(True)
                self.next_btn.setEnabled(True)
                self.export_csv_btn.setEnabled(True)
                self.speak_card_btn.setEnabled(True)
                award("generate_flashcards")
                QMessageBox.information(self, "Success", f"✅ Generated {len(self.flashcards)} flashcards!")
            else:
                QMessageBox.warning(self, "Warning", "No flashcards could be generated.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate flashcards: {str(e)}")


    def speak_flashcard(self):
        if hasattr(self, 'flashcards') and self.flashcards:
            card = self.flashcards[self.current_card_index]
            text = card.get("q", "") if self.showing_question else card.get("a", "")
            if text:
                speak_text(text)

    def export_flashcards_csv(self):
        if not hasattr(self, 'flashcards') or not self.flashcards:
            QMessageBox.warning(self, "No Data", "No flashcards available to export.")
            return
            
        import csv
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Flashcards to Anki CSV", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Anki uses front, back
                    for card in self.flashcards:
                        writer.writerow([card.get("q", ""), card.get("a", "")])
                QMessageBox.information(self, "Export Successful", f"Flashcards successfully exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export flashcards: {e}")

    def flip_flashcard(self):
        """
        Flips the card with a smooth fade-out, content-switch, and fade-in animation.
        This is a more robust alternative to geometry animation.
        """
        if not self.flashcards or hasattr(self, 'is_flipping') and self.is_flipping:
            return

        self.is_flipping = True
        self.flip_btn.setEnabled(False) # Disable button during flip

        # --- FADE OUT ANIMATION ---
        self.fade_out_effect = QGraphicsOpacityEffect(self.flashcard_stack)
        self.flashcard_stack.setGraphicsEffect(self.fade_out_effect)
        
        self.fade_out_anim = QPropertyAnimation(self.fade_out_effect, b"opacity")
        self.fade_out_anim.setDuration(150) # Fast fade out
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # When fade-out is done, switch content and start fade-in
        self.fade_out_anim.finished.connect(self._switch_and_fade_in)
        
        self.fade_out_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _switch_and_fade_in(self):
        """
        This method is called after the card has faded out.
        It switches the content and starts the fade-in animation.
        """
        # 1. Switch the card face
        self.showing_question = not self.showing_question
        new_index = 0 if self.showing_question else 1
        self.flashcard_stack.setCurrentIndex(new_index)
        
        # 2. --- FADE IN ANIMATION ---
        # The effect is still attached from the fade-out
        self.fade_in_anim = QPropertyAnimation(self.fade_out_effect, b"opacity")
        self.fade_in_anim.setDuration(250) # Slower, more deliberate fade in
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # When fade-in is done, clean up and re-enable the button
        self.fade_in_anim.finished.connect(self._on_flip_finished)
        
        self.fade_in_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    
    def _on_flip_finished(self):
        """Final cleanup after the flip animation is complete."""
        self.is_flipping = False
        self.flip_btn.setEnabled(True) # Re-enable the flip button
        self.flashcard_stack.setGraphicsEffect(None) # Remove the effect for performance

    def show_current_card(self):
        if not self.flashcards:
            return
            
        card = self.flashcards[self.current_card_index]
        
        # Set text for both question and answer faces
        self.question_content_label.setText(card.get('q', 'No question found.'))
        self.answer_content_label.setText(card.get('a', 'No answer found.'))
        
        # Reset to show the question face
        self.showing_question = True
        self.flashcard_stack.setCurrentIndex(0)
            
        self.card_progress.setText(f"Card {self.current_card_index + 1} of {len(self.flashcards)}")

    def prev_flashcard(self):
        if self.flashcards and self.current_card_index > 0:
            self.current_card_index -= 1
            self.show_current_card()

    def next_flashcard(self):
        if self.flashcards and self.current_card_index < len(self.flashcards) - 1:
            self.current_card_index += 1
            self.show_current_card()

    def generate_quiz(self):
        if not self.current_summary_id:
            self.show_styled_message(
                "warning", "Generate Summary First",
                "A summary is required before a quiz can be generated.\n"
                "Please click 'Generate Summary' first."
            )
            return

        # Immediate UI feedback
        self.clear_quiz_display()
        self.submit_quiz_btn.setEnabled(False)
        self._quiz_thinking_label = QLabel("⏳ AI is crafting your quiz…")
        self._quiz_thinking_label.setStyleSheet(
            "font-size: 14px; color: #00d4aa; font-style: italic; padding: 20px;"
        )
        self._quiz_thinking_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quiz_layout.addWidget(self._quiz_thinking_label)
        QApplication.processEvents()

        # Fetch summary text synchronously (fast DB read, not AI)
        try:
            from data.db import get_conn
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT text FROM summaries WHERE id=?", (self.current_summary_id,)
                ).fetchone()
            if not row or not row['text']:
                raise ValueError("Summary text not found in database.")
            summary_text = row['text']
        except Exception as e:
            self._quiz_thinking_label.deleteLater()
            self.show_styled_message("critical", "DB Error", str(e))
            return

        from core.llm import get_provider
        from ui.workers import AIWorker

        provider = get_provider()
        self._quiz_worker = AIWorker(provider.quiz, summary_text, task_name="Quiz")
        self._quiz_worker.finished_with_result.connect(self._on_quiz_done)
        self._quiz_worker.error_occurred.connect(
            lambda err: (
                self._quiz_thinking_label.deleteLater(),
                self.show_styled_message("critical", "Quiz Error", err)
            )
        )
        self._quiz_worker.start()

    def _on_quiz_done(self, quiz_data):
        """Called from AIWorker signal when quiz generation completes."""
        if hasattr(self, '_quiz_thinking_label'):
            self._quiz_thinking_label.deleteLater()

        if not quiz_data:
            self.show_styled_message(
                "warning", "Quiz Generation Failed",
                "The AI could not generate a quiz from this summary.\n"
                "Try using a longer 'Detailed' summary for better results."
            )
            return

        self.current_quiz = quiz_data
        self.display_quiz(self.current_quiz)
        self.submit_quiz_btn.setEnabled(True)
        award("generate_quiz")
        try:
            from data.db import get_conn
            with get_conn() as conn:
                conn.execute("UPDATE stats SET total_quizzes = total_quizzes + 1 WHERE id=1")
                conn.commit()
        except Exception:
            pass
        self.show_styled_message(
            "info", "Quiz Ready!",
            f"✅ Generated {len(self.current_quiz)} questions. Good luck!"
        )


    def display_quiz(self, quiz):
        self.clear_quiz_display()
        self.quiz_question_widgets = []
        
        for i, question in enumerate(quiz, 1):
            question_frame = QFrame()
            question_frame.setStyleSheet("""
                QFrame {
                    background: #1b2838;
                    border: 1px solid #1e3044;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 5px;
                }
            """)
            question_layout = QVBoxLayout(question_frame)
            question_layout.setSpacing(10)
            
            # Question text
            question_label = QLabel(f"<b style='color:#00d4aa; font-size: 15px;'>Question {i}:</b><br/><span style='color:#e8edf3; font-size: 14px;'>{question['question']}</span>")
            question_label.setWordWrap(True)
            question_label.setStyleSheet("padding: 10px; background: #213043; border-radius: 6px;")
            question_layout.addWidget(question_label)
            
            # Radio buttons for options
            radio_group = QButtonGroup(question_frame)
            
            for j, option in enumerate(question['options']):
                radio = QRadioButton(option)
                radio.setStyleSheet("""
                    QRadioButton {
                        color: #c0ccda;
                        padding: 8px;
                        font-size: 14px;
                        spacing: 10px;
                    }
                    QRadioButton::indicator {
                        width: 18px;
                        height: 18px;
                        border-radius: 9px;
                        border: 2px solid #1e3044;
                    }
                    QRadioButton::indicator:checked {
                        background-color: #00d4aa;
                        border: 2px solid #00d4aa;
                    }
                    QRadioButton:hover {
                        background-color: #213043;
                        border-radius: 6px;
                    }
                """)
                radio_group.addButton(radio, j)
                question_layout.addWidget(radio)
            
            # Store the radio group and correct answer
            question_frame.radio_group = radio_group
            question_frame.correct_answer = question['answer']
            question_frame.explanation = question['explanation']
            
            self.quiz_question_widgets.append(question_frame)
            self.quiz_layout.addWidget(question_frame)
        
        self.quiz_layout.addStretch()

    def clear_quiz_display(self):
        self.quiz_question_widgets = []
        while self.quiz_layout.count():
            child = self.quiz_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def grade_quiz(self):
        if not hasattr(self, 'current_quiz') or not self.current_quiz:
            QMessageBox.warning(self, "Warning", "Please generate a quiz first.")
            return
        
        score = 0
        total = len(self.current_quiz)
        results = []
        
        for i, question_widget in enumerate(self.quiz_question_widgets):
            selected_id = question_widget.radio_group.checkedId()
            
            if selected_id == -1:
                results.append({
                    'q': self.current_quiz[i]['question'],
                    'correct': False,
                    'your': 'Not answered',
                    'answer': question_widget.correct_answer,
                    'explanation': question_widget.explanation
                })
            else:
                # Get the selected option letter (A, B, C, D)
                selected_option = self.current_quiz[i]['options'][selected_id]
                selected_letter = selected_option[0]  # First character is the letter
                
                correct = selected_letter.upper() == question_widget.correct_answer.upper()
                if correct:
                    score += 1
                
                results.append({
                    'q': self.current_quiz[i]['question'],
                    'correct': correct,
                    'your': selected_letter,
                    'answer': question_widget.correct_answer,
                    'explanation': question_widget.explanation
                })
        
        percentage = int((score / total) * 100) if total > 0 else 0
        
        # Save quiz history to database
        try:
            from data.db import get_conn
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO quiz_history (summary_id, score, total_questions, correct_answers, details_json) VALUES (?, ?, ?, ?, ?)",
                    (self.current_summary_id, percentage, total, score, json.dumps(results))
                )
                conn.commit()
        except Exception as e:
            print(f"Failed to save quiz history: {e}")
        
        # Show results in scrollable dialog
        result_dialog = QDialog(self)
        result_dialog.setWindowTitle(f"Quiz Results — {score}/{total} ({percentage}%)")
        result_dialog.setMinimumSize(600, 500)
        result_dialog.setStyleSheet("""
            QDialog { background: #0d1b2a; color: #e8edf3; }
        """)
        dlg_layout = QVBoxLayout(result_dialog)
        dlg_layout.setContentsMargins(20, 20, 20, 20)
        dlg_layout.setSpacing(12)

        # Score header
        if percentage >= 80:
            grade_color = "#00d4aa"
            grade_emoji = "🏆"
        elif percentage >= 60:
            grade_color = "#f6ad55"
            grade_emoji = "👍"
        else:
            grade_color = "#fc8181"
            grade_emoji = "📚"

        score_label = QLabel(f"{grade_emoji}  {score}/{total}  ({percentage}%)")
        score_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_label.setStyleSheet(f"color: {grade_color}; background: #1b2838; border-radius: 12px; padding: 16px;")
        dlg_layout.addWidget(score_label)

        # Scrollable results
        results_view = QTextEdit()
        results_view.setReadOnly(True)
        results_view.setStyleSheet("""
            QTextEdit {
                background: #1b2838; color: #e8edf3; border: 1px solid #1e3044;
                border-radius: 10px; padding: 14px; font-size: 13px;
            }
        """)
        result_html = ""
        for i, detail in enumerate(results, 1):
            status = "✅" if detail['correct'] else "❌"
            result_html += f"<p><b style='font-size: 14px; color: #e8edf3;'>{status} Question {i}:</b> {detail['q']}<br/>"
            result_html += f"<span style='color:#7b8fa3;'>Your answer: <b>{detail['your']}</b> | "
            result_html += f"Correct: <b style='color:#00d4aa;'>{detail['answer']}</b></span><br/>"
            result_html += f"<i style='color:#7b8fa3;'>{detail['explanation']}</i></p><hr style='border-color:#1e3044;'/>"
        results_view.setHtml(result_html)
        dlg_layout.addWidget(results_view)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton { background: #00d4aa; color: #0d1b2a; border: none;
                padding: 10px 30px; border-radius: 10px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background: #00e6b8; }
        """)
        close_btn.clicked.connect(result_dialog.accept)
        dlg_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)

        result_dialog.exec()
        
        award("complete_quiz")
        
        # Bonus XP based on score
        if percentage >= 80:
            add_xp(20)
        elif percentage >= 60:
            add_xp(10)

    def generate_concept_map(self):
        if not self.current_summary_id:
            self.show_styled_message("warning", "Generate Summary First",
                                     "A summary is required to create a concept map.")
            return

        # Get summary text (fast DB read)
        try:
            from data.db import get_conn
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT text FROM summaries WHERE id=?", (self.current_summary_id,)
                ).fetchone()
            if not row or not row['text']:
                self.show_styled_message("critical", "Error", "Summary text not found.")
                return
            summary_text = row['text']
        except Exception as e:
            self.show_styled_message("critical", "Error", str(e))
            return

        # Async generation via worker
        self.concept_label.setText("🤖 Generating concept map… please wait.")
        QApplication.processEvents()

        output_path = os.path.join(settings.assets_dir, f"concept_map_{self.current_note_id}.png")
        from ui.workers import ConceptMapWorker
        self._concept_worker = ConceptMapWorker(summary_text, output_path)
        self._concept_worker.finished_with_result.connect(self._on_concept_map_done)
        self._concept_worker.error_occurred.connect(
            lambda err: (
                self.concept_label.setText("❌ Failed to generate concept map."),
                self.show_styled_message("critical", "Error", err)
            )
        )
        self._concept_worker.start()

    def _on_concept_map_done(self, image_path: str):
        """Called from ConceptMapWorker signal when map is ready."""
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.concept_label.setPixmap(
                pixmap.scaled(self.concept_label.size(),
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
            self.show_styled_message("info", "Done!", "✅ Concept map generated successfully!")
        else:
            self.concept_label.setText(
                "❌ Failed to generate concept map.\n"
                "Try a 'Detailed' summary for better results."
            )


    def send_chat_message(self):
        if not self.chatbot and not self.chat_index:
            self.show_styled_message("warning", "No Note Selected", "Please select a note to start chatting.")
            return
            
        question = self.chat_input.text().strip()
        if not question:
            return
            
        self.chat_display.append(f"<p><b style='color:#4299e1;'>👤 You:</b> {question}</p>")
        self.chat_input.clear()
        
        self.chat_display.append("<p><i style='color:#718096;'>🤔 AI is thinking...</i></p>")
        QApplication.processEvents()
        
        try:
            # Get selected persona
            from core.personas import get_persona
            pid = self.persona_combo.currentData()
            persona = get_persona(pid)
            
            # Use the new chatbot if available
            if self.chatbot:
                # Inject persona system prompt temporarily if possible
                # Creating a new turn with persona context
                # For now, we prepend it to the query to guide the model if system prompt update isn't exposed
                # But better: if chatbot supports system_instruction update
                if hasattr(self.chatbot, 'set_system_instruction'):
                    self.chatbot.set_system_instruction(persona.system_prompt)
                else:
                    # Soft injection
                    question = f"[SYSTEM: {persona.system_prompt}] User: {question}"
                
                answer = self.chatbot.chat(question)
            else: 
                answer = self.chat_index.ask(question)

            # Remove typing indicator
            current_text = self.chat_display.toPlainText()
            self.chat_display.setPlainText(current_text.rsplit("🤔 AI is thinking...", 1)[0].strip())
            
            # Format answer with markdown
            answer_html = answer.replace('\n', '<br>')
            answer_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', answer_html) # Bold
            answer_html = re.sub(r'## (.*?)(<br>|$)', r'<h3>\1</h3>', answer_html) # Headings

            self.chat_display.append(f"<p><b style='color:#48bb78;'>{persona.icon} {persona.name}:</b> {answer_html}</p><hr/>")
            award("ask_chat")
            
            # Read Aloud
            if self.speak_check.isChecked():
                from core.voice_service import get_voice_service
                get_voice_service().speak(answer)
                
        except Exception as e:
            self.chat_display.append(f"<p><b style='color:#f56565;'>❌ Error:</b> {str(e)}</p>")

    def start_voice_chat(self):
        """Handle voice input."""
        from core.voice_service import get_voice_service
        vs = get_voice_service()
        
        self.mic_btn.setText("👂...")
        self.mic_btn.setEnabled(False)
        self.chat_input.setPlaceholderText("Listening...")
        
        def _reset_mic():
            self.mic_btn.setText("🎤")
            self.mic_btn.setEnabled(True)
            self.chat_input.setPlaceholderText("Ask a question...")
        
        def on_speech(text):
            QTimer.singleShot(0, lambda: self.chat_input.setText(text))
            QTimer.singleShot(50, self.send_chat_message)
            QTimer.singleShot(100, _reset_mic)
            
        def on_error(msg):
            QTimer.singleShot(0, lambda: self.show_styled_message("warning", "Voice Error", msg))
            QTimer.singleShot(0, _reset_mic)

        vs.start_listening(on_speech, on_error)
    
    def show_styled_message(self, level, title, text):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        icon_map = {
            "info": QMessageBox.Icon.Information,
            "warning": QMessageBox.Icon.Warning,
            "critical": QMessageBox.Icon.Critical,
        }
        msg_box.setIcon(icon_map.get(level, QMessageBox.Icon.NoIcon))

        # FIX: Apply custom stylesheet to the popup
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                border: 2px solid #667eea;
                border-radius: 10px;
            }
            QMessageBox QLabel {
                color: #2d3748;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 8px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        msg_box.exec()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._force_quit = False  # For system tray close vs quit
        self.setWindowTitle("EduMind - AI Study Assistant")
        self.setGeometry(100, 100, 1500, 950)
        self.apply_styles()
        
        # Create central widget with tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1e3044;
                border-radius: 10px;
                background: #0d1b2a;
                padding: 8px;
            }
            QTabBar::tab {
                background: #1b2838;
                border: 1px solid #1e3044;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 8px 8px 0 0;
                color: #7b8fa3;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4aa, stop:1 #0984e3);
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #213043;
                border-color: #00d4aa;
            }
        """)
        
        self.dashboard = DashboardTab()
        self.study_tab = StudyAssistantTab()
        
        # Add core tabs
        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.study_tab, "Study Assistant")
        
        
        # Add Analytics tab (try Plotly first, fall back to matplotlib)
        try:
            from ui.widgets.plotly_charts import PlotlyChartsWidget, HAS_PLOTLY
            if HAS_PLOTLY:
                self.analytics_tab = PlotlyChartsWidget()
                self.tabs.addTab(self.analytics_tab, "Analytics")
            else:
                raise ImportError("Plotly not available")
        except ImportError:
            try:
                from ui.widgets.progress_charts import ProgressChartsWidget
                self.analytics_tab = ProgressChartsWidget()
                self.tabs.addTab(self.analytics_tab, "Analytics")
            except ImportError:
                pass

        # Add Calendar tab
        try:
            from ui.widgets.calendar_view import CalendarTab
            self.calendar_tab = CalendarTab()
            self.tabs.addTab(self.calendar_tab, "Calendar")
        except ImportError:
            pass

        # Add Pomodoro Timer tab
        try:
            from ui.widgets.pomodoro_timer import PomodoroTimer
            self.pomodoro_tab = PomodoroTimer()
            self.pomodoro_tab.session_completed.connect(self._on_focus_session_ended)
            self.tabs.addTab(self.pomodoro_tab, "Pomodoro")
        except ImportError:
            pass

        # Add Quiz History tab
        try:
            from ui.widgets.quiz_history_viewer import QuizHistoryViewer
            self.quiz_history_tab = QuizHistoryViewer()
            self.tabs.addTab(self.quiz_history_tab, "Quiz History")
        except ImportError:
            pass

        # Add AI Assistant tab
        if CHATBOT_AVAILABLE:
            self.general_ai_tab = self.create_general_ai_tab()
            self.tabs.addTab(self.general_ai_tab, "AI Assistant")
        
        self.setCentralWidget(self.tabs)
        
        # Create menu bar with user info
        self._create_menu_bar()
        
        # Setup system tray (inspired by Smart Battery Optimizer)
        self._init_system_tray()
        
        # Setup status bar
        self._init_status_bar()
        
        # Start on the dashboard
        self.tabs.setCurrentWidget(self.dashboard)
        
        # Connect dashboard button signals
        self.dashboard.navigate_to_upload.connect(self.go_to_upload)
        self.dashboard.navigate_to_summary.connect(self.go_to_summary)
        self.dashboard.navigate_to_quiz.connect(self.go_to_quiz)
        self.dashboard.navigate_to_flashcards.connect(self.go_to_flashcards)
        self.dashboard.navigate_to_concept_map.connect(self.go_to_concept_map)
        self.dashboard.navigate_to_chat.connect(self.go_to_chat)
        self.dashboard.navigate_to_pomodoro.connect(lambda: self._go_to_tab_by_name("Pomodoro"))
        self.dashboard.navigate_to_analytics.connect(lambda: self._go_to_tab_by_name("Analytics"))
        self.dashboard.navigate_to_quiz_history.connect(lambda: self._go_to_tab_by_name("Quiz History"))
        self.dashboard.navigate_to_export.connect(self.study_tab.export_to_pdf)
    
    def _go_to_tab_by_name(self, name):
        """Navigate to a tab by its title."""
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == name:
                self.tabs.setCurrentIndex(i)
                return
    
    def _init_system_tray(self):
        """Initialize system tray icon with context menu (Battery Optimizer pattern)."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("EduMind - AI Study Assistant")
        
        # Create a simple icon programmatically as fallback
        from PyQt6.QtGui import QPixmap, QPainter, QBrush, QLinearGradient
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 64, 64)
        gradient.setColorAt(0, QColor('#00d4aa'))
        gradient.setColorAt(1, QColor('#0984e3'))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, 56, 56, 14, 14)
        painter.setPen(QColor('white'))
        font = QFont('Segoe UI', 26, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, '🎓')
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        self.setWindowIcon(QIcon(pixmap))
        
        # Tray context menu
        from PyQt6.QtWidgets import QMenu
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background: #1b2838;
                border: 1px solid #1e3044;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
                color: #c0ccda;
            }
            QMenu::item:selected {
                background: #00d4aa;
                color: white;
            }
        """)
        
        show_action = tray_menu.addAction("🏠 Show EduMind")
        show_action.triggered.connect(self._tray_show)
        
        study_action = tray_menu.addAction("📚 Quick Study")
        study_action.triggered.connect(lambda: (self._tray_show(), self.tabs.setCurrentIndex(1)))
        
        tray_menu.addSeparator()
        
        theme_action = tray_menu.addAction("🌓 Toggle Theme")
        theme_action.triggered.connect(self.toggle_theme)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("❌ Quit")
        quit_action.triggered.connect(self._tray_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
    
    def _tray_show(self):
        """Restore window from tray."""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def _tray_quit(self):
        """Actually quit the application."""
        self._force_quit = True
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()
    
    def _on_tray_activated(self, reason):
        """Handle tray icon click."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._tray_show()
    
    def closeEvent(self, event):
        """Minimize to tray on close instead of quitting."""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible() and not self._force_quit:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "EduMind",
                "EduMind is still running in the system tray.\nDouble-click the tray icon to reopen.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        else:
            event.accept()
    
    def apply_styles(self):
        """Apply the current theme stylesheet to the application."""
        from ui.themes.theme_manager import get_theme_manager
        tm = get_theme_manager()
        QApplication.instance().setStyleSheet(tm.get_stylesheet())
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        from ui.themes.theme_manager import get_theme_manager
        tm = get_theme_manager()
        tm.toggle_theme()
        self.apply_styles()
    
    def open_settings(self):
        """Open settings dialog."""
        QMessageBox.information(self, "Settings", "Settings panel coming soon!")
    
    def _init_status_bar(self):
        """Initialize status bar with provider info and study streak."""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background: #1b2838;
                border-top: 1px solid #1e3044;
                padding: 4px 15px;
                font-size: 12px;
                color: #7b8fa3;
            }
            QStatusBar::item { border: none; }
        """)
        
        # AI Provider indicator
        provider_name = settings.provider.capitalize() if hasattr(settings, 'provider') else 'Offline'
        self.status_provider = QLabel(f"🤖 AI: {provider_name}")
        self.status_provider.setToolTip(f"Current AI provider: {provider_name}")
        status_bar.addPermanentWidget(self.status_provider)
        
        # Separator
        sep1 = QLabel("│")
        sep1.setStyleSheet("color: #1e3044;")
        status_bar.addPermanentWidget(sep1)
        
        # Study streak
        stats = dict(get_stats())
        self.status_streak = QLabel(f"🔥 Streak: {stats.get('streak', 0)} days")
        self.status_streak.setToolTip("Your consecutive study day streak")
        status_bar.addPermanentWidget(self.status_streak)
        
        # Separator
        sep2 = QLabel("│")
        sep2.setStyleSheet("color: #cbd5e0;")
        status_bar.addPermanentWidget(sep2)
        
        # XP
        self.status_xp = QLabel(f"⭐ XP: {stats.get('xp', 0)}")
        self.status_xp.setToolTip("Total experience points earned")
        status_bar.addPermanentWidget(self.status_xp)
        
        # Status message (left side)
        status_bar.showMessage("✅ EduMind ready - Select a note to begin studying")
    
    def _update_status_bar(self):
        """Refresh status bar data."""
        try:
            stats = dict(get_stats())
            self.status_streak.setText(f"🔥 Streak: {stats.get('streak', 0)} days")
            self.status_xp.setText(f"⭐ XP: {stats.get('xp', 0)}")
        except Exception:
            pass

    def _create_menu_bar(self):
        """Create menu bar with user profile and settings."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: #1b2838;
                padding: 4px;
                border-bottom: 1px solid #1e3044;
            }
            QMenuBar::item {
                padding: 6px 12px;
                border-radius: 6px;
                color: #c0ccda;
            }
            QMenuBar::item:selected {
                background: #00d4aa;
                color: white;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu("📁 File")
        action = file_menu.addAction("New Study Session")
        action.setShortcut(QKeySequence("Ctrl+N"))
        action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        action = file_menu.addAction("Import Notes")
        action.setShortcut(QKeySequence("Ctrl+I"))
        action.triggered.connect(lambda: self.study_tab.choose_file())
        file_menu.addSeparator()
        action = file_menu.addAction("Export to PDF")
        action.setShortcut(QKeySequence("Ctrl+E"))
        action.triggered.connect(lambda: self.study_tab.export_to_pdf())
        file_menu.addSeparator()
        action = file_menu.addAction("Exit")
        action.setShortcut(QKeySequence("Ctrl+Q"))
        action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu("👁 View")
        action = view_menu.addAction("Dashboard")
        action.setShortcut(QKeySequence("Ctrl+1"))
        action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        action = view_menu.addAction("Study Assistant")
        action.setShortcut(QKeySequence("Ctrl+2"))
        action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        action = view_menu.addAction("Focus Mode")
        action.setShortcut(QKeySequence("Ctrl+3"))
        action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        action = view_menu.addAction("Analytics")
        action.setShortcut(QKeySequence("Ctrl+4"))
        action.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        view_menu.addSeparator()
        action = view_menu.addAction("Toggle Theme")
        action.setShortcut(QKeySequence("Ctrl+D"))
        action.triggered.connect(self.toggle_theme)

        # Tools menu
        tools_menu = menubar.addMenu("🛠 Tools")
        action = tools_menu.addAction("📹 YouTube Import")
        action.setShortcut(QKeySequence("Ctrl+Y"))
        action.triggered.connect(self._open_youtube_import)
        action = tools_menu.addAction("🔔 Study Reminders")
        action.setShortcut(QKeySequence("Ctrl+R"))
        action.triggered.connect(self._open_reminders)
        tools_menu.addAction("📝 Weekly Report", self._generate_report)
        
        # Settings (right side)
        menubar.addMenu("").setEnabled(False)
        settings_menu = menubar.addMenu("⚙ Settings")
        action = settings_menu.addAction("Preferences")
        action.setShortcut(QKeySequence("Ctrl+,"))
        action.triggered.connect(self.open_settings)
    
    def _on_focus_session_ended(self, minutes: int):
        """Handle focus session completion - award XP."""
        try:
            from core.gamification import get_gamification_service
            game = get_gamification_service()
            game.record_study_session(minutes)
            # Refresh dashboard
            self.dashboard.refresh()
        except ImportError:
            pass
    
    # Auth/login removed — app runs without authentication

    # --- METHOD 1 TO ADD ---
    def create_general_ai_tab(self):
        """Creates the UI and logic for the general-purpose AI assistant tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Initialize the chatbot in 'general' mode
        self.general_chatbot = EduMindChatbot() 
        self.general_chatbot.set_mode('general')

        header = QLabel("🤖 General AI Assistant")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d4aa; background: transparent; margin-bottom: 10px;")
        layout.addWidget(header)

        self.general_chat_display = QTextEdit()
        self.general_chat_display.setReadOnly(True)
        self.general_chat_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #1e3044; border-radius: 10px;
                padding: 15px; background: #0d1b2a; color: #c0ccda;
                font-size: 14px;
            }
        """)
        self.general_chat_display.append("Hello! I'm your general AI assistant. Ask me anything about any topic!")
        layout.addWidget(self.general_chat_display)

        input_frame = QFrame()
        input_frame.setStyleSheet("background: #1b2838; border-radius: 10px; padding: 10px;")
        input_layout = QHBoxLayout(input_frame)
        
        self.general_chat_input = QLineEdit()
        self.general_chat_input.setPlaceholderText("Ask about science, history, programming, or anything else...")
        self.general_chat_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cbd5e0; border-radius: 18px;
                padding: 10px 15px; font-size: 14px;
            }
            QLineEdit:focus { border-color: #667eea; }
        """)
        self.general_chat_input.returnPressed.connect(self.send_general_chat_message)
        
        send_btn = StyledButton("Send", "#667eea", "#764ba2")
        send_btn.clicked.connect(self.send_general_chat_message)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #e2e8f0; color: #4a5568; border: none;
                padding: 10px 20px; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background: #cbd5e0; }
        """)
        clear_btn.clicked.connect(self.general_chat_display.clear)
        
        input_layout.addWidget(self.general_chat_input)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(clear_btn)
        layout.addWidget(input_frame)
        
        return widget

    # --- METHOD 2 TO ADD ---
    def send_general_chat_message(self):
        """Handles sending a message in the General AI tab."""
        question = self.general_chat_input.text().strip()
        if not question:
            return

        self.general_chat_display.append(f"<p><b style='color:#4299e1;'>👤 You:</b> {question}</p>")
        self.general_chat_input.clear()
        
        self.general_chat_display.append("<p><i style='color:#718096;'>🤔 AI is thinking...</i></p>")
        QApplication.processEvents()

        try:
            answer = self.general_chatbot.chat(question)
            
            current_text = self.general_chat_display.toPlainText()
            self.general_chat_display.setPlainText(current_text.rsplit("🤔 AI is thinking...", 1)[0].strip())
            
            answer_html = answer.replace('\n', '<br>')
            answer_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', answer_html)
            answer_html = re.sub(r'## (.*?)(<br>|$)', r'<h3>\1</h3>', answer_html)

            self.general_chat_display.append(f"<p><b style='color:#48bb78;'>🤖 EduMind AI:</b> {answer_html}</p><hr/>")

        except Exception as e:
            self.general_chat_display.append(f"<p><b style='color:#f56565;'>❌ Error:</b> An error occurred. Please try again.</p>")
            print(f"General AI Chat Error: {e}")

    def go_to_upload(self):
        """Switch to study assistant tab and guide user."""
        self.tabs.setCurrentWidget(self.study_tab)
        QMessageBox.information(
            self,
            "Upload Notes",
            "📁 Use the sidebar on the left to upload your study material."
        )

    def go_to_summary(self):
        """Switch to study assistant tab and activate summary."""
        self.tabs.setCurrentWidget(self.study_tab)
        self.study_tab.tools_tabs.setCurrentIndex(0) # Summary tab is at index 0
        
    def go_to_quiz(self):
        """Switch to study assistant tab and activate quiz."""
        self.tabs.setCurrentWidget(self.study_tab)
        self.study_tab.tools_tabs.setCurrentIndex(2) # Quiz tab is at index 2
        
    def go_to_flashcards(self):
        """Switch to study assistant tab and activate flashcards."""
        self.tabs.setCurrentWidget(self.study_tab)
        self.study_tab.tools_tabs.setCurrentIndex(1) # Flashcards tab is at index 1
        
    def go_to_concept_map(self):
        """Switch to study assistant tab and activate concept map."""
        self.tabs.setCurrentWidget(self.study_tab)
        self.study_tab.tools_tabs.setCurrentIndex(3) # Concept Map tab is at index 3
        
    def go_to_chat(self):
        """Switch to study assistant tab and activate AI chat."""
        self.tabs.setCurrentWidget(self.study_tab)
        self.study_tab.tools_tabs.setCurrentIndex(4) # AI Chat tab is at index 4

    # NOTE: apply_styles, toggle_theme, open_settings defined above (lines ~2221-2236)

    def _open_youtube_import(self):
        """Open YouTube import dialog."""
        from ui.dialogs.youtube_dialog import YouTubeDialog
        dialog = YouTubeDialog(self)
        dialog.process_content.connect(self._handle_youtube_content)
        dialog.exec()

    def _handle_youtube_content(self, text, title):
        """Handle content from YouTube dialog — import as a new note."""
        try:
            from data.db import add_note
            nid = add_note(title, "youtube", text)
            try:
                from core.xp import award
                award("import_note")
            except Exception:
                pass
            # Refresh the notes list if method exists
            if hasattr(self.study_tab, 'refresh_notes'):
                self.study_tab.refresh_notes()
            elif hasattr(self, 'dashboard'):
                self.dashboard.refresh()
            self.go_to_summary()
            QMessageBox.information(
                self,
                "Content Imported",
                f"Transcript for '{title}' imported as a note!\n\nSelect it and click 'Generate Summary' to study."
            )
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import YouTube content: {e}")

    def _open_reminders(self):
        """Open reminders dialog."""
        from ui.dialogs.reminder_dialog import ReminderDialog
        dialog = ReminderDialog(self)
        dialog.exec()

    def _generate_report(self):
        """Generate and show weekly report."""
        try:
            from core.reports import ReportGenerator
            from core.auth import get_auth_service
            
            # Gather stats (mock for now, or read from goal_service if available)
            stats = {
                "xp": 1250, 
                "streak": 5, 
                "sessions_count": 8,
                "cards_reviewed": 142,
                "quizzes_completed": 3,
                "study_minutes": 320
            }
            
            auth = get_auth_service()
            user = auth.get_current_user()
            user_data = {"display_name": user.username if user else "Student"}
            
            report = ReportGenerator.generate_weekly_report(user_data, stats)
            
            # Show in dialog
            from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton
            d = QDialog(self)
            d.setWindowTitle("Weekly Report 📊")
            d.setFixedSize(500, 600)
            l = QVBoxLayout(d)
            t = QTextEdit()
            t.setPlainText(report)
            t.setReadOnly(True)
            t.setStyleSheet("font-family: Consolas, monospace; font-size: 13px;")
            l.addWidget(t)
            b = QPushButton("Close")
            b.clicked.connect(d.accept)
            l.addWidget(b)
            d.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate report: {e}")

    def _run_sync(self):
        """Run cloud sync."""
        if not self.current_user:
            QMessageBox.warning(self, "Sync Error", "Please login to sync your data.")
            return

        from core.sync import CloudSyncService
        
        # Show progress
        progress = QMessageBox(self)
        progress.setWindowTitle("Cloud Sync")
        progress.setText("Syncing with cloud...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.show()
        
        def on_sync_complete(success, msg):
            progress.accept()
            if success:
                QMessageBox.information(self, "Sync Complete", msg)
            else:
                QMessageBox.warning(self, "Sync Failed", msg)
        
        # Start sync
        service = CloudSyncService(self.current_user.id)
        service.sync_now(callback=lambda s, m: QTimer.singleShot(0, lambda: on_sync_complete(s, m)))

def run_app():
    import sys
    import time
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont

    # Initialize database
    init_db()
    
    # Run migrations
    from core.migrations import run_migrations
    run_migrations()
    
    # Create assets directory
    os.makedirs(settings.assets_dir or "assets", exist_ok=True)
    
    # Set UTF-8 encoding for console output (skip in PyInstaller windowed mode where stdout is None)
    if sys.platform == 'win32' and sys.stdout is not None:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("[EduMind] Starting EduMind Application...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("EduMind")
    app.setApplicationVersion("1.5.0")
    
    # Apply theme
    from ui.themes.theme_manager import get_theme_manager
    theme_manager = get_theme_manager()
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # -- 3. MAIN WINDOW --
    window = MainWindow()
    
    # Setup keyboard shortcuts
    from ui.accessibility import KeyboardShortcutManager
    shortcuts = KeyboardShortcutManager(window)
    shortcuts.register("Ctrl+,", window.open_settings, "Open settings")
    shortcuts.register("Ctrl+D", window.toggle_theme, "Toggle dark/light theme")
    shortcuts.register("Ctrl+1", lambda: window.tabs.setCurrentIndex(0), "Go to Dashboard")
    shortcuts.register("Ctrl+2", lambda: window.tabs.setCurrentIndex(1), "Go to Study Assistant")
    shortcuts.register("Ctrl+3", lambda: window.tabs.setCurrentIndex(2), "Go to Focus Mode")
    shortcuts.register("Ctrl+4", lambda: window.tabs.setCurrentIndex(3), "Go to Analytics")
    shortcuts.register("F1", lambda: _show_help_dialog(window), "Show help")
    
    def _show_help_dialog(parent):
        """Show a styled keyboard shortcut reference card."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
        d = QDialog(parent)
        d.setWindowTitle("⌨️ EduMind Help & Shortcuts")
        d.setFixedSize(450, 500)
        d.setStyleSheet("""
            QDialog {
                background: #ffffff;
                border-radius: 12px;
            }
        """)
        l = QVBoxLayout(d)
        l.setContentsMargins(0, 0, 0, 15)
        
        t = QTextEdit()
        t.setReadOnly(True)
        t.setStyleSheet("border: none; background: white; padding: 15px;")
        t.setHtml("""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; border-radius: 0 0 12px 12px;">
                <h1 style="color: white; margin: 0;">🎓 EduMind</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">AI-Powered Study Assistant v1.5</p>
            </div>
            <div style="padding: 15px;">
                <h3 style="color: #667eea;">⌨️ Keyboard Shortcuts</h3>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="background: #f7fafc;"><td style="padding:8px; border-bottom:1px solid #e2e8f0;"><b>Ctrl+D</b></td><td style="padding:8px; border-bottom:1px solid #e2e8f0;">Toggle Dark/Light Theme</td></tr>
                    <tr><td style="padding:8px; border-bottom:1px solid #e2e8f0;"><b>Ctrl+,</b></td><td style="padding:8px; border-bottom:1px solid #e2e8f0;">Open Settings</td></tr>
                    <tr style="background: #f7fafc;"><td style="padding:8px; border-bottom:1px solid #e2e8f0;"><b>Ctrl+1</b></td><td style="padding:8px; border-bottom:1px solid #e2e8f0;">Go to Dashboard</td></tr>
                    <tr><td style="padding:8px; border-bottom:1px solid #e2e8f0;"><b>Ctrl+2</b></td><td style="padding:8px; border-bottom:1px solid #e2e8f0;">Go to Study Assistant</td></tr>
                    <tr style="background: #f7fafc;"><td style="padding:8px; border-bottom:1px solid #e2e8f0;"><b>Ctrl+3</b></td><td style="padding:8px; border-bottom:1px solid #e2e8f0;">Go to Focus Mode</td></tr>
                    <tr><td style="padding:8px; border-bottom:1px solid #e2e8f0;"><b>Ctrl+4</b></td><td style="padding:8px; border-bottom:1px solid #e2e8f0;">Go to Analytics</td></tr>
                    <tr style="background: #f7fafc;"><td style="padding:8px;"><b>F1</b></td><td style="padding:8px;">Show this Help</td></tr>
                </table>
                <h3 style="color: #667eea; margin-top: 15px;">💡 Tips</h3>
                <ul style="color: #4a5568;">
                    <li>Drag & drop files onto the Study Assistant tab</li>
                    <li>Use the search bar to filter your notes</li>
                    <li>Close the window to minimize to system tray</li>
                    <li>Right-click the tray icon for quick actions</li>
                </ul>
            </div>
        """)
        l.addWidget(t)
        
        close_btn = StyledButton("Got it!", "#667eea", "#764ba2")
        close_btn.clicked.connect(d.accept)
        l.addWidget(close_btn)
        d.exec()
    
    window.show()
    
    # Setup Timer for Reminders (Check every minute)
    from PyQt6.QtCore import QTimer
    from core.reminders import get_reminder_service
    
    reminder_timer = QTimer(window)
    reminder_service = get_reminder_service()
    
    def check_reminders():
        alerts = reminder_service.check_reminders()
        for alert in alerts:
            # Show non-intrusive notification or tray message
            # For now, a message box is safest on all OS without tray setup
            # But let's verify if window is active to avoid interruption
            # Using system tray would be better, but let's stick to status bar or simple dialog
            try:
                from PyQt6.QtWidgets import QSystemTrayIcon
                if QSystemTrayIcon.isSystemTrayAvailable():
                    tray = QSystemTrayIcon(window)
                    tray.show()
                    tray.showMessage("Time to Study! 🔔", alert.message, QSystemTrayIcon.MessageIcon.Information, 5000)
                else:
                    # Fallback
                    pass 
            except:
                pass

    reminder_timer.timeout.connect(check_reminders)
    reminder_timer.start(60000) # 1 minute
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()