# tests/conftest.py
"""
Pytest configuration and shared fixtures for EduMind tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_text():
    """Sample text for testing summarization and extraction."""
    return """
    Machine learning is a subset of artificial intelligence that enables systems 
    to learn and improve from experience without being explicitly programmed. 
    It focuses on developing computer programs that can access data and use it 
    to learn for themselves.
    
    The process of learning begins with observations or data, such as examples, 
    direct experience, or instruction. It looks for patterns in data and makes 
    better decisions in the future based on the examples provided.
    
    The primary aim is to allow computers to learn automatically without human 
    intervention and adjust actions accordingly. There are three main types of 
    machine learning: supervised learning, unsupervised learning, and reinforcement 
    learning.
    
    Supervised learning uses labeled datasets to train algorithms to classify 
    data or predict outcomes accurately. Unsupervised learning uses unlabeled 
    data to discover hidden patterns. Reinforcement learning is based on 
    reward-driven behavior.
    """.strip()


@pytest.fixture
def sample_summary():
    """Sample summary text for testing quiz and flashcard generation."""
    return """
    Machine learning enables systems to learn from experience without explicit 
    programming. It's a subset of AI that focuses on pattern recognition and 
    decision-making.
    
    Key concepts:
    - Supervised learning uses labeled data for classification
    - Unsupervised learning discovers hidden patterns in unlabeled data  
    - Reinforcement learning uses reward-based training
    
    The goal is automatic learning without human intervention.
    """.strip()


@pytest.fixture
def sample_quiz_json():
    """Sample quiz JSON for testing parsing."""
    return '''[
        {
            "question": "What is machine learning?",
            "options": [
                "A) A type of database",
                "B) A subset of artificial intelligence",
                "C) A programming language",
                "D) A hardware component"
            ],
            "answer": "B",
            "explanation": "Machine learning is a subset of AI that enables systems to learn from data."
        }
    ]'''


@pytest.fixture
def sample_flashcards_json():
    """Sample flashcards JSON for testing parsing."""
    return '''[
        {"q": "What is supervised learning?", "a": "Learning from labeled datasets"},
        {"q": "What is unsupervised learning?", "a": "Discovering patterns in unlabeled data"}
    ]'''


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    os.environ["EDUMIND_DB_PATH"] = str(db_path)
    return db_path


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider for testing."""
    from unittest.mock import MagicMock
    from core.ai.base_provider import LLMProvider
    
    mock = MagicMock(spec=LLMProvider)
    mock.is_available.return_value = True
    mock.get_model_name.return_value = "mock-model"
    mock.summarize.return_value = {
        "summary": "Test summary",
        "key_points": ["Point 1", "Point 2"],
        "flashcards": [{"q": "Q1", "a": "A1"}]
    }
    mock.quiz.return_value = [{
        "question": "Test?",
        "options": ["A) Yes", "B) No", "C) Maybe", "D) Unknown"],
        "answer": "A",
        "explanation": "Test explanation"
    }]
    mock.flashcards.return_value = [{"q": "Q1", "a": "A1"}]
    mock.concept_map.return_value = {"nodes": ["A", "B"], "edges": [["A", "B", "connects"]]}
    
    return mock
