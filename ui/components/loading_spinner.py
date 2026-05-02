# ui/components/loading_spinner.py
"""
Loading indicator components for async operations.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen


class LoadingSpinner(QWidget):
    """
    An animated loading spinner widget.
    
    Features:
    - Smooth rotation animation
    - Customizable size and color
    - Optional text label
    
    Example:
        >>> spinner = LoadingSpinner("Loading...", color="#667eea")
        >>> spinner.start()
    """
    
    def __init__(
        self,
        text: str = "",
        size: int = 48,
        color: str = "#667eea",
        parent=None
    ):
        super().__init__(parent)
        self.text = text
        self.spinner_size = size
        self.spinner_color = QColor(color)
        self._angle = 0
        self._num_dots = 8
        
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        """Create the spinner layout."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Spinner canvas
        self.spinner_canvas = QWidget()
        self.spinner_canvas.setFixedSize(self.spinner_size, self.spinner_size)
        self.spinner_canvas.paintEvent = self._paint_spinner
        
        layout.addWidget(self.spinner_canvas, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Text label
        if self.text:
            self.label = QLabel(self.text)
            self.label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #718096;
                    margin-top: 10px;
                }
            """)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.label)
    
    def _setup_timer(self):
        """Set up the animation timer."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        self.timer.setInterval(80)  # ~12 fps rotation
    
    def _paint_spinner(self, event):
        """Paint the spinner dots."""
        painter = QPainter(self.spinner_canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.spinner_size / 2
        center_y = self.spinner_size / 2
        radius = self.spinner_size / 2 - 8
        dot_radius = 4
        
        for i in range(self._num_dots):
            # Calculate position
            angle = (360 / self._num_dots * i + self._angle) * 3.14159 / 180
            x = center_x + radius * 0.8 * __import__('math').cos(angle)
            y = center_y + radius * 0.8 * __import__('math').sin(angle)
            
            # Calculate opacity (fade based on position)
            opacity = (i + 1) / self._num_dots
            color = QColor(self.spinner_color)
            color.setAlphaF(opacity)
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(x - dot_radius),
                int(y - dot_radius),
                int(dot_radius * 2),
                int(dot_radius * 2)
            )
        
        painter.end()
    
    def _rotate(self):
        """Rotate the spinner."""
        self._angle = (self._angle + 45) % 360
        self.spinner_canvas.update()
    
    def start(self):
        """Start the spinner animation."""
        self.timer.start()
        self.show()
    
    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
        self.hide()
    
    def set_text(self, text: str):
        """Update the loading text."""
        self.text = text
        if hasattr(self, 'label'):
            self.label.setText(text)


class ProgressSpinner(QWidget):
    """
    A progress indicator with percentage display.
    
    Example:
        >>> progress = ProgressSpinner("Processing...")
        >>> progress.set_progress(50)
    """
    
    def __init__(
        self,
        text: str = "Loading...",
        parent=None
    ):
        super().__init__(parent)
        self.text = text
        self._progress = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the progress layout."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
        # Text label
        self.label = QLabel(self.text)
        self.label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #2d3748;
            }
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background: #e2e8f0;
                height: 16px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }
        """)
        self.progress_bar.setFixedWidth(300)
        
        # Percentage label
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }
        """)
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.percent_label)
    
    def set_progress(self, value: int):
        """
        Set the progress value (0-100).
        
        Args:
            value: Progress percentage
        """
        self._progress = max(0, min(100, value))
        self.progress_bar.setValue(self._progress)
        self.percent_label.setText(f"{self._progress}%")
    
    def set_text(self, text: str):
        """Update the progress text."""
        self.text = text
        self.label.setText(text)
    
    @property
    def progress(self) -> int:
        return self._progress


class SkeletonLoader(QWidget):
    """
    A skeleton loading placeholder that shows while content loads.
    Creates a shimmer effect to indicate loading.
    
    Example:
        >>> skeleton = SkeletonLoader(height=100)
        >>> # Replace with actual content when loaded
        >>> skeleton.hide()
    """
    
    def __init__(
        self,
        width: int = 300,
        height: int = 60,
        border_radius: int = 8,
        parent=None
    ):
        super().__init__(parent)
        self.setFixedSize(width, height)
        
        self.setStyleSheet(f"""
            SkeletonLoader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e2e8f0, 
                    stop:0.5 #edf2f7, 
                    stop:1 #e2e8f0);
                border-radius: {border_radius}px;
            }}
        """)
