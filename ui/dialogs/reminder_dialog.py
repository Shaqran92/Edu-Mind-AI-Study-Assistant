# ui/dialogs/reminder_dialog.py
"""Advanced study reminder management dialog for EduMind."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QListWidget, QListWidgetItem, QComboBox, QCheckBox,
    QTimeEdit, QGridLayout, QMessageBox, QScrollArea, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QFont

from core.reminders import get_reminder_service, DAY_NAMES

BG = "#0d1b2a"
BG_CARD = "#1b2838"
BG_INPUT = "#213043"
BORDER = "#1e3044"
TEXT = "#e8edf3"
TEXT_MUTED = "#7b8fa3"
ACCENT = "#00d4aa"
ACCENT_BLUE = "#0984e3"

class ReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔔 Study Reminders")
        self.setMinimumSize(650, 580)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG}; color: {TEXT}; }}
            QLabel {{ color: {TEXT}; background: transparent; }}
            QLineEdit {{ padding: 8px 12px; border: 1px solid {BORDER}; border-radius: 8px;
                background: {BG_INPUT}; color: {TEXT}; font-size: 13px; }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """)
        self.service = get_reminder_service()
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QLabel("🔔 Study Reminders")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {ACCENT};")
        layout.addWidget(header)

        sub = QLabel("Never miss a study session. Set smart reminders to build consistent habits.")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(sub)

        # Quick presets
        presets_frame = QFrame()
        presets_frame.setStyleSheet(f"QFrame {{ background: {BG_CARD}; border-radius: 10px; padding: 10px; border: 1px solid {BORDER}; }}")
        presets_layout = QVBoxLayout(presets_frame)
        presets_label = QLabel("⚡ Quick Presets")
        presets_label.setStyleSheet(f"font-weight: bold; color: {ACCENT}; font-size: 13px;")
        presets_layout.addWidget(presets_label)

        preset_btns = QHBoxLayout()
        presets = [
            ("🌅 Morning Study", "morning_study"),
            ("📖 Afternoon Review", "afternoon_review"),
            ("🃏 Evening Flashcards", "evening_flashcards"),
            ("☕ Break Reminder", "break_reminder"),
            ("📚 Weekend Study", "weekend_study"),
        ]
        for label, preset_id in presets:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {BG_INPUT}; color: {TEXT}; border: 1px solid {BORDER};
                    padding: 6px 12px; border-radius: 8px; font-size: 11px; }}
                QPushButton:hover {{ border-color: {ACCENT}; background: {BG_CARD}; }}
            """)
            btn.clicked.connect(lambda _, p=preset_id: self._add_preset(p))
            preset_btns.addWidget(btn)
        presets_layout.addLayout(preset_btns)
        layout.addWidget(presets_frame)

        # Add custom reminder
        add_frame = QGroupBox("Add Custom Reminder")
        add_frame.setStyleSheet(f"""
            QGroupBox {{ font-weight: bold; color: {ACCENT}; border: 1px solid {BORDER};
                border-radius: 10px; margin-top: 10px; padding-top: 18px; background: {BG_CARD}; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 8px; }}
        """)
        add_layout = QGridLayout(add_frame)
        add_layout.setSpacing(10)

        add_layout.addWidget(QLabel("Time:"), 0, 0)
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setStyleSheet(f"padding: 8px; border: 1px solid {BORDER}; border-radius: 8px; background: {BG_INPUT}; color: {TEXT};")
        add_layout.addWidget(self.time_edit, 0, 1)

        add_layout.addWidget(QLabel("Type:"), 0, 2)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["📚 Study", "☕ Break", "🔄 Review", "🔔 Custom"])
        self.type_combo.setStyleSheet(f"padding: 6px; border: 1px solid {BORDER}; border-radius: 8px; background: {BG_INPUT}; color: {TEXT};")
        add_layout.addWidget(self.type_combo, 0, 3)

        add_layout.addWidget(QLabel("Message:"), 1, 0)
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("e.g., Time to study biology!")
        add_layout.addWidget(self.msg_input, 1, 1, 1, 3)

        add_layout.addWidget(QLabel("Days:"), 2, 0)
        days_layout = QHBoxLayout()
        self.day_checks = []
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            cb = QCheckBox(name)
            cb.setStyleSheet(f"color: {TEXT}; spacing: 4px;")
            if i < 5:
                cb.setChecked(True)
            self.day_checks.append(cb)
            days_layout.addWidget(cb)
        add_layout.addLayout(days_layout, 2, 1, 1, 3)

        add_btn = QPushButton("➕ Add Reminder")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_BLUE});
                color: white; border: none; padding: 10px 24px; border-radius: 10px; font-weight: bold; font-size: 13px; }}
            QPushButton:hover {{ background: {ACCENT}; }}
        """)
        add_btn.clicked.connect(self._add_custom)
        add_layout.addWidget(add_btn, 3, 0, 1, 4)
        layout.addWidget(add_frame)

        # Reminders list
        list_label = QLabel("📋 Active Reminders")
        list_label.setStyleSheet(f"font-weight: bold; color: {ACCENT}; font-size: 14px;")
        layout.addWidget(list_label)

        self.reminder_list = QListWidget()
        self.reminder_list.setStyleSheet(f"""
            QListWidget {{ border: 1px solid {BORDER}; border-radius: 10px; background: {BG_CARD}; padding: 4px; }}
            QListWidget::item {{ padding: 10px; margin: 3px 0; background: {BG_INPUT}; border-radius: 8px;
                border-left: 3px solid {ACCENT}; color: {TEXT}; }}
            QListWidget::item:selected {{ background: {ACCENT}; color: white; }}
        """)
        layout.addWidget(self.reminder_list)

        # Action buttons
        btn_layout = QHBoxLayout()
        toggle_btn = QPushButton("⏯ Toggle")
        toggle_btn.clicked.connect(self._toggle_selected)
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.clicked.connect(self._delete_selected)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        for btn in [toggle_btn, delete_btn, close_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {BG_CARD}; color: {TEXT}; border: 1px solid {BORDER};
                    padding: 8px 20px; border-radius: 8px; font-size: 12px; }}
                QPushButton:hover {{ border-color: {ACCENT}; }}
            """)
        btn_layout.addWidget(toggle_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _refresh_list(self):
        self.reminder_list.clear()
        for r in self.service.reminders:
            status = "✅" if r.enabled else "⏸️"
            text = f"{status} {r.get_type_emoji()} {r.time} — {r.message}\n     {r.get_days_display()}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, r.id)
            self.reminder_list.addItem(item)

    def _add_preset(self, preset_id):
        self.service.add_preset(preset_id)
        self._refresh_list()

    def _add_custom(self):
        time_str = self.time_edit.time().toString("HH:mm")
        msg = self.msg_input.text().strip() or "Study time!"
        days = [i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
        if not days:
            QMessageBox.warning(self, "No Days", "Please select at least one day.")
            return
        type_map = {"📚 Study": "study", "☕ Break": "break", "🔄 Review": "review", "🔔 Custom": "custom"}
        rtype = type_map.get(self.type_combo.currentText(), "custom")
        self.service.add_reminder(time_str, days, msg, rtype)
        self.msg_input.clear()
        self._refresh_list()

    def _toggle_selected(self):
        item = self.reminder_list.currentItem()
        if item:
            rid = item.data(Qt.ItemDataRole.UserRole)
            self.service.toggle_reminder(rid)
            self._refresh_list()

    def _delete_selected(self):
        item = self.reminder_list.currentItem()
        if item:
            rid = item.data(Qt.ItemDataRole.UserRole)
            self.service.remove_reminder(rid)
            self._refresh_list()
