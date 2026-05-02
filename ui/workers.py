# ui/workers.py
"""
Background workers for EduMind — runs AI operations off the UI thread.
Prevents the UI from freezing during long AI API calls.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Any, Callable, Optional


class AIWorker(QThread):
    """
    Generic background worker for AI operations.
    Runs any callable in a separate thread and emits result/error signals.
    
    Usage:
        worker = AIWorker(provider.quiz, summary_text)
        worker.finished_with_result.connect(on_quiz_done)
        worker.error_occurred.connect(on_error)
        worker.start()
    """
    
    finished_with_result = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(
        self,
        func: Callable,
        *args,
        task_name: str = "AI Task",
        parent=None,
        **kwargs
    ):
        super().__init__(parent)
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._task_name = task_name
    
    def run(self):
        """Execute the function in a background thread."""
        try:
            self.progress_update.emit(f"{self._task_name} in progress...")
            result = self._func(*self._args, **self._kwargs)
            self.finished_with_result.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"{self._task_name} failed: {str(e)}")


class SummaryWorker(AIWorker):
    """Worker for generating summaries."""
    def __init__(self, provider, text, mode, length, language, parent=None):
        super().__init__(
            provider.summarize, text, mode, length, language,
            task_name="Summary Generation",
            parent=parent
        )


class QuizWorker(AIWorker):
    """Worker for generating quizzes."""
    def __init__(self, provider, summary_text, parent=None):
        super().__init__(
            provider.quiz, summary_text,
            task_name="Quiz Generation",
            parent=parent
        )


class FlashcardWorker(AIWorker):
    """Worker for generating flashcards."""
    def __init__(self, provider, summary_text, parent=None):
        super().__init__(
            provider.flashcards, summary_text,
            task_name="Flashcard Generation",
            parent=parent
        )


class ConceptMapWorker(QThread):
    """Worker for generating concept maps (needs special handling for file output)."""
    finished_with_result = pyqtSignal(str)  # Path to saved image
    error_occurred = pyqtSignal(str)
    
    def __init__(self, summary_text: str, output_path: str, parent=None):
        super().__init__(parent)
        self._summary_text = summary_text
        self._output_path = output_path
    
    def run(self):
        try:
            from core.concept_map import generate_and_visualize_concept_map
            result = generate_and_visualize_concept_map(
                self._summary_text, self._output_path
            )
            self.finished_with_result.emit(result or "")
        except Exception as e:
            self.error_occurred.emit(f"Concept map failed: {str(e)}")
