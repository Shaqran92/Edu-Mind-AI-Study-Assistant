# ui/widgets/plotly_charts.py
"""Dynamic interactive charts using Plotly for EduMind analytics."""

import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame
from PyQt6.QtCore import Qt, QTimer, QUrl
from utils.logger import get_logger

logger = get_logger("plotly_charts")

BG = '#0d1b2a'
BG_CARD = '#1b2838'
BORDER = '#1e3044'
TEXT = '#c0ccda'
ACCENT = '#00d4aa'

HAS_PLOTLY = False
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    pass

HAS_WEBVIEW = False
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBVIEW = True
except ImportError:
    pass


def _query_db(query, params=()):
    try:
        from data.db import get_conn
        with get_conn() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]
    except Exception as e:
        logger.error(f"DB error: {e}")
        return []


class PlotlyChartsWidget(QWidget):
    """Interactive analytics dashboard using Plotly."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(30000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("📊 Interactive Analytics")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ACCENT}; background: transparent;")
        header.addWidget(title)

        self._range = QComboBox()
        self._range.addItems(["Last 7 Days", "Last 30 Days", "Last 90 Days"])
        self._range.currentIndexChanged.connect(self._refresh)
        self._range.setStyleSheet(f"padding: 6px; border-radius: 8px; background: {BG_CARD}; color: {TEXT}; border: 1px solid {BORDER};")
        header.addStretch()
        header.addWidget(self._range)
        layout.addLayout(header)

        if not HAS_PLOTLY:
            lbl = QLabel("Install plotly for interactive charts:\npip install plotly")
            lbl.setStyleSheet(f"color: {TEXT}; font-size: 14px; padding: 40px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)
            return

        if HAS_WEBVIEW:
            self._web = QWebEngineView()
            self._web.setMinimumHeight(600)
            layout.addWidget(self._web)
        else:
            # Fallback: save as HTML and show a label
            self._web = None
            self._fallback = QLabel("Charts generated as HTML files in assets/")
            self._fallback.setStyleSheet(f"color: {TEXT}; padding: 20px;")
            layout.addWidget(self._fallback)

        self._refresh()

    def _days(self):
        return [7, 30, 90][self._range.currentIndex()]

    def _refresh(self):
        if not HAS_PLOTLY:
            return
        days = self._days()
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Quiz Score Trend", "Study Activity", "Notes Created", "Overall Progress"),
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "pie"}]]
        )

        # 1) Quiz scores
        scores = _query_db(
            "SELECT created_at, score FROM quiz_history WHERE created_at >= ? ORDER BY created_at", (cutoff,)
        )
        if scores:
            dates = [s.get('created_at', '')[:10] for s in scores]
            vals = [s.get('score', 0) for s in scores]
            fig.add_trace(go.Scatter(x=dates, y=vals, mode='lines+markers',
                                     line=dict(color='#f6ad55', width=3),
                                     marker=dict(size=8, color='#f6ad55'),
                                     name='Quiz Score'), row=1, col=1)
        else:
            fig.add_annotation(text="No quiz data yet", xref="x1", yref="y1",
                               x=0.5, y=0.5, showarrow=False, font=dict(color=TEXT, size=14))

        # 2) Activity (notes + quizzes per day)
        notes_data = _query_db(
            "SELECT date(created_at) as day, COUNT(*) as cnt FROM notes WHERE created_at >= ? GROUP BY day", (cutoff,)
        )
        quiz_data = _query_db(
            "SELECT date(created_at) as day, COUNT(*) as cnt FROM quiz_history WHERE created_at >= ? GROUP BY day", (cutoff,)
        )
        if notes_data:
            fig.add_trace(go.Bar(x=[r['day'] for r in notes_data], y=[r['cnt'] for r in notes_data],
                                 name='Notes', marker_color='#4299e1'), row=1, col=2)
        if quiz_data:
            fig.add_trace(go.Bar(x=[r['day'] for r in quiz_data], y=[r['cnt'] for r in quiz_data],
                                 name='Quizzes', marker_color='#f6ad55'), row=1, col=2)

        # 3) Cumulative notes
        all_notes = _query_db("SELECT date(created_at) as day, COUNT(*) as cnt FROM notes GROUP BY day ORDER BY day")
        if all_notes:
            cumulative = []
            total = 0
            for r in all_notes:
                total += r['cnt']
                cumulative.append(total)
            fig.add_trace(go.Scatter(x=[r['day'] for r in all_notes], y=cumulative,
                                     fill='tozeroy', line=dict(color=ACCENT, width=2),
                                     name='Total Notes'), row=2, col=1)

        # 4) Overall stats pie
        stats = _query_db("SELECT * FROM stats WHERE id=1")
        if stats:
            s = stats[0]
            labels = ['Notes', 'Quizzes', 'XP/10']
            values = [s.get('total_notes', 0) or 1, s.get('total_quizzes', 0) or 1, max(1, (s.get('xp', 0) or 0) // 10)]
            fig.add_trace(go.Pie(labels=labels, values=values,
                                 marker=dict(colors=['#4299e1', '#f6ad55', ACCENT]),
                                 textinfo='label+value'), row=2, col=2)

        fig.update_layout(
            height=600, showlegend=True,
            paper_bgcolor=BG, plot_bgcolor=BG_CARD,
            font=dict(color=TEXT, size=11),
            legend=dict(bgcolor=BG_CARD, bordercolor=BORDER),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER)
        fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER)

        html = fig.to_html(include_plotlyjs='cdn', full_html=True)

        if self._web and HAS_WEBVIEW:
            self._web.setHtml(html)
        else:
            path = os.path.join("assets", "analytics_chart.html")
            os.makedirs("assets", exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
