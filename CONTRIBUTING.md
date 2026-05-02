# CONTRIBUTING.md
# Contributing to EduMind

Thank you for your interest in contributing to EduMind! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to create a welcoming environment for everyone.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your feature or fix

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/EduMind.git
cd EduMind

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests to verify setup
pytest tests/ -v
```

### Running the Application

```bash
python app.py
```

## Making Changes

### Branch Naming

- `feature/` - New features (e.g., `feature/voice-input`)
- `fix/` - Bug fixes (e.g., `fix/quiz-scoring`)
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(flashcards): add spaced repetition algorithm`
- `fix(ui): correct theme toggle behavior`
- `docs: update installation instructions`

## Pull Request Process

1. **Ensure tests pass**: `pytest tests/ -v`
2. **Run linting**: `ruff check .`
3. **Update documentation** if needed
4. **Create PR** with clear description
5. **Address review feedback**

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Follows style guide
- [ ] Clear commit messages

## Style Guide

### Python

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Maximum line length: 100 characters

### Example

```python
def calculate_score(answers: List[str], correct: List[str]) -> float:
    """
    Calculate the quiz score as a percentage.
    
    Args:
        answers: List of user answers
        correct: List of correct answers
    
    Returns:
        Score as a percentage (0-100)
    
    Example:
        >>> calculate_score(['A', 'B'], ['A', 'C'])
        50.0
    """
    if not answers:
        return 0.0
    
    correct_count = sum(a == c for a, c in zip(answers, correct))
    return (correct_count / len(answers)) * 100
```

### Testing

- Write tests for new features
- Aim for high coverage on core modules
- Use pytest fixtures for common setup

```python
def test_spaced_repetition_first_review():
    """First correct review should set interval to 1 day."""
    service = SpacedRepetitionService()
    card = CardReview(card_id=1)
    
    service.review_card(card, ReviewQuality.GOOD)
    
    assert card.interval == 1
    assert card.repetitions == 1
```

## Questions?

Open an issue or reach out to the maintainers. We're happy to help!
