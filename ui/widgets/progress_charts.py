# ui/widgets/progress_charts.py
"""
Real-time progress visualization charts for EduMind.
Pulls actual data from the database and auto-refreshes.
Stores direct label references (not fragile objectName lookups).
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import io
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage

from utils.logger import get_logger

logger = get_logger("progress_charts")

# Dark theme colors
BG_PRIMARY = '#0d1b2a'
BG_CARD = '#1b2838'
BG_TERTIARY = '#213043'
BORDER = '#1e3044'
TEXT = '#c0ccda'
TEXT_MUTED = '#7b8fa3'
ACCENT = '#00d4aa'

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available, charts disabled")


def _query_db(query: str, params=()) -> list:
    """Query the EduMind database safely."""
    try:
        from data.db import get_conn
        with get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"DB query error: {e}")
        return []


def _query_study_sessions(query: str, params=()) -> list:
    """Query the study_sessions table."""
    try:
        from core.db import get_db
        db = get_db()
        rows = db.fetch_all(query, params)
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Study sessions query error: {e}")
        return []


class ProgressChartsWidget(QWidget):
    """
    Real-time study analytics dashboard.
    Stores direct references to chart labels for reliable rendering.
    """

    CHART_DPI = 120
    CHART_FIGSIZE = (5.5, 3.2)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # Direct label references — no fragile objectName lookups
        self._chart_labels: Dict[str, QLabel] = {}
        self._setup_ui()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_charts)
        self._refresh_timer.start(30_000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("📊 Study Analytics")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {ACCENT}; background: transparent;"
        )
        header.addWidget(title)

        live_dot = QLabel("● LIVE")
        live_dot.setStyleSheet(
            "color: #00d4aa; font-size: 11px; font-weight: bold; background: transparent;"
        )
        header.addWidget(live_dot)

        self._range_combo = QComboBox()
        self._range_combo.addItems(["Last 7 Days", "Last 30 Days", "Last 3 Months"])
        self._range_combo.currentIndexChanged.connect(self._refresh_charts)
        self._range_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 12px; border-radius: 8px; min-width: 140px;
                background: {BG_TERTIARY}; color: {TEXT}; border: 1px solid {BORDER};
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD}; color: {TEXT}; border: 1px solid {BORDER};
            }}
        """)
        header.addStretch()
        header.addWidget(self._range_combo)
        layout.addLayout(header)

        if not MATPLOTLIB_AVAILABLE:
            no_charts = QLabel("Install matplotlib for charts:\npip install matplotlib numpy")
            no_charts.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 14px; padding: 40px;"
            )
            no_charts.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_charts)
            return

        # 2×2 charts grid
        charts_grid = QGridLayout()
        charts_grid.setSpacing(12)

        chart_defs = [
            ("study_time",  "⏱ Study Time",            0, 0),
            ("activity",    "📝 Notes & Quizzes",       0, 1),
            ("quiz_scores", "🎯 Quiz Score Trend",      1, 0),
            ("overall",     "🏆 Overall Progress",      1, 1),
        ]

        for key, title_text, row, col in chart_defs:
            frame, label = self._create_chart_frame(title_text)
            self._chart_labels[key] = label
            charts_grid.addWidget(frame, row, col)

        layout.addLayout(charts_grid)
        self._refresh_charts()

    def _create_chart_frame(self, title: str):
        """Create a card frame with a chart label. Returns (frame, label)."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{ border-color: {ACCENT}; }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-weight: bold; color: {ACCENT}; font-size: 13px; background: transparent;"
        )
        layout.addWidget(title_label)

        chart_label = QLabel()
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_label.setMinimumSize(340, 230)
        chart_label.setStyleSheet(f"background: {BG_CARD}; border-radius: 8px;")
        chart_label.setText("Loading…")
        layout.addWidget(chart_label)

        return frame, chart_label

    # ──────────────────── DATA FETCHING ────────────────────

    def _get_days_range(self) -> int:
        return [7, 30, 90][self._range_combo.currentIndex()]

    def _fill_date_range(self, data: dict, days: int):
        dates, values = [], []
        for i in range(days - 1, -1, -1):
            d = datetime.now() - timedelta(days=i)
            dates.append(d)
            values.append(data.get(d.strftime('%Y-%m-%d'), 0))
        return dates, values

    def _get_study_time_data(self, days: int) -> dict:
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = _query_study_sessions(
            "SELECT date(start_time) as day, SUM(duration_minutes) as total "
            "FROM study_sessions WHERE start_time >= ? GROUP BY day ORDER BY day",
            (cutoff,)
        )
        return {r['day']: r.get('total') or 0 for r in rows if r.get('day')}

    def _get_activity_data(self, days: int):
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        notes_rows = _query_db(
            "SELECT date(created_at) as day, COUNT(*) as cnt FROM notes "
            "WHERE created_at >= ? GROUP BY day ORDER BY day", (cutoff,)
        )
        quiz_rows = _query_db(
            "SELECT date(created_at) as day, COUNT(*) as cnt FROM quizzes "
            "WHERE created_at >= ? GROUP BY day ORDER BY day", (cutoff,)
        )
        return (
            {r['day']: r['cnt'] for r in notes_rows if r.get('day')},
            {r['day']: r['cnt'] for r in quiz_rows if r.get('day')},
        )

    def _get_quiz_scores(self, days: int) -> list:
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = _query_db(
            "SELECT created_at, score FROM quiz_history "
            "WHERE created_at >= ? ORDER BY created_at", (cutoff,)
        )
        # Also try the quizzes table
        if not rows:
            rows = _query_db(
                "SELECT created_at, quiz_json FROM quizzes "
                "WHERE created_at >= ? ORDER BY created_at", (cutoff,)
            )
            scores = []
            for r in rows:
                try:
                    data = json.loads(r['quiz_json']) if r.get('quiz_json') else []
                    if isinstance(data, list) and data:
                        total = len(data)
                        correct = sum(1 for q in data if q.get('correct', False))
                        pct = (correct / total * 100) if total else 0
                        scores.append({'date': (r.get('created_at') or '')[:10], 'score': pct})
                except Exception:
                    pass
            return scores
        return [{'date': (r.get('created_at') or '')[:10], 'score': r.get('score', 0)} for r in rows]

    def _get_overall_stats(self) -> dict:
        rows = _query_db("SELECT * FROM stats WHERE id=1")
        return dict(rows[0]) if rows else {'total_notes': 0, 'total_quizzes': 0, 'xp': 0, 'streak': 0}

    # ──────────────────── RENDERING ────────────────────

    def _refresh_charts(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        days = self._get_days_range()
        self._render_study_time(self._get_study_time_data(days), days)
        notes_d, quiz_d = self._get_activity_data(days)
        self._render_activity(notes_d, quiz_d, days)
        self._render_quiz_scores(self._get_quiz_scores(days), days)
        self._render_overall(self._get_overall_stats())

    def _dark_fig(self):
        fig, ax = plt.subplots(figsize=self.CHART_FIGSIZE, dpi=self.CHART_DPI)
        fig.patch.set_facecolor(BG_CARD)
        ax.set_facecolor(BG_CARD)
        ax.tick_params(colors=TEXT_MUTED, labelsize=7, length=3, width=0.5)
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        ax.spines['left'].set_color(BORDER)
        ax.spines['bottom'].set_color(BORDER)
        ax.grid(True, alpha=0.1, color=TEXT_MUTED, linewidth=0.4)
        return fig, ax

    def _push_to_label(self, fig, key: str):
        """Render figure into the named chart label."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor=fig.get_facecolor(),
                    edgecolor='none', dpi=self.CHART_DPI, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        label = self._chart_labels.get(key)
        if label is None:
            logger.warning(f"No chart label found for key '{key}'")
            return

        image = QImage.fromData(buf.getvalue())
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(scaled)
        label.setText("")

    def _fmt_date_axis(self, ax, days: int):
        if days <= 7:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))
        elif days <= 31:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 7)))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(ax.get_xticklabels(), rotation=28, ha='right', fontsize=7)

    def _render_study_time(self, data: dict, days: int):
        fig, ax = self._dark_fig()
        dates, values = self._fill_date_range(data, days)
        if any(v > 0 for v in values):
            ax.plot(dates, values, color=ACCENT, linewidth=2.5, alpha=0.95)
            ax.fill_between(dates, values, alpha=0.18, color=ACCENT)
        else:
            ax.text(0.5, 0.5, 'No study sessions yet\nUse Focus/Pomodoro to track time',
                    transform=ax.transAxes, ha='center', va='center',
                    color=TEXT_MUTED, fontsize=10)
        ax.set_ylabel("Minutes", fontsize=8, color=TEXT_MUTED, labelpad=6)
        self._fmt_date_axis(ax, days)
        fig.subplots_adjust(left=0.14, right=0.97, top=0.95, bottom=0.22)
        self._push_to_label(fig, "study_time")

    def _render_activity(self, notes_data: dict, quizzes_data: dict, days: int):
        fig, ax = self._dark_fig()
        dates, notes_vals = self._fill_date_range(notes_data, days)
        _, quizzes_vals = self._fill_date_range(quizzes_data, days)
        has_data = any(v > 0 for v in notes_vals) or any(v > 0 for v in quizzes_vals)
        if has_data:
            if len(dates) > 14:
                step = max(1, len(dates) // 14)
                dates = dates[::step]
                notes_vals = notes_vals[::step]
                quizzes_vals = quizzes_vals[::step]
            bar_w = 0.35 if len(dates) <= 1 else max(0.2, (dates[-1] - dates[0]).days / len(dates) * 0.4)
            ax.bar(dates, notes_vals, width=bar_w, color='#4299e1', alpha=0.85, label='Notes')
            ax.bar(dates, quizzes_vals, width=bar_w, bottom=notes_vals,
                   color='#f6ad55', alpha=0.85, label='Quizzes')
            ax.legend(fontsize=7, loc='upper left', framealpha=0.25,
                      labelcolor=TEXT, facecolor=BG_CARD, edgecolor=BORDER)
        else:
            ax.text(0.5, 0.5, 'No activity yet\nImport notes to get started',
                    transform=ax.transAxes, ha='center', va='center',
                    color=TEXT_MUTED, fontsize=10)
        ax.set_ylabel("Count", fontsize=8, color=TEXT_MUTED, labelpad=6)
        self._fmt_date_axis(ax, days)
        fig.subplots_adjust(left=0.14, right=0.97, top=0.95, bottom=0.22)
        self._push_to_label(fig, "activity")

    def _render_quiz_scores(self, scores: list, days: int):
        fig, ax = self._dark_fig()
        dates, vals = [], []
        for s in scores:
            try:
                dates.append(datetime.strptime(s['date'], '%Y-%m-%d'))
                vals.append(float(s['score']))
            except (ValueError, TypeError, KeyError):
                pass
        if dates:
            ax.plot(dates, vals, color='#f6ad55', linewidth=2.5, marker='o',
                    markersize=5, alpha=0.95)
            ax.fill_between(dates, vals, alpha=0.12, color='#f6ad55')
            ax.set_ylim(0, 105)
        else:
            ax.text(0.5, 0.5, 'No quiz scores yet\nComplete a quiz to see trends',
                    transform=ax.transAxes, ha='center', va='center',
                    color=TEXT_MUTED, fontsize=10)
        ax.set_ylabel("Score %", fontsize=8, color=TEXT_MUTED, labelpad=6)
        self._fmt_date_axis(ax, days)
        fig.subplots_adjust(left=0.14, right=0.97, top=0.95, bottom=0.22)
        self._push_to_label(fig, "quiz_scores")

    def _render_overall(self, stats: dict):
        fig, ax = plt.subplots(figsize=self.CHART_FIGSIZE, dpi=self.CHART_DPI)
        fig.patch.set_facecolor(BG_CARD)
        notes = stats.get('total_notes') or 0
        quizzes = stats.get('total_quizzes') or 0
        xp = stats.get('xp') or 0
        streak = stats.get('streak') or 0
        if notes + quizzes > 0:
            labels = [f'Notes ({notes})', f'Quizzes ({quizzes})']
            sizes = [max(notes, 1), max(quizzes, 1)]
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=['#4299e1', '#f6ad55'],
                autopct='%1.0f%%', startangle=90, pctdistance=0.75,
                wedgeprops=dict(width=0.4, edgecolor=BG_CARD, linewidth=2),
                textprops={'fontsize': 9, 'color': TEXT}
            )
            for at in autotexts:
                at.set_fontsize(8)
                at.set_color('white')
                at.set_fontweight('bold')
            ax.text(0, 0, f'{xp} XP\n{streak}d 🔥',
                    ha='center', va='center', fontsize=11,
                    fontweight='bold', color=ACCENT)
        else:
            ax.text(0.5, 0.5, f'XP: {xp}  |  Streak: {streak}d\n\nStart studying!',
                    transform=ax.transAxes, ha='center', va='center',
                    color=TEXT_MUTED, fontsize=12)
        ax.axis('equal')
        ax.set_facecolor(BG_CARD)
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self._push_to_label(fig, "overall")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if MATPLOTLIB_AVAILABLE and hasattr(self, '_range_combo'):
            self._refresh_charts()
