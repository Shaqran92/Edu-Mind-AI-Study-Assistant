# tests/unit/test_spaced_repetition.py
"""
Unit tests for the spaced repetition service.
"""

import pytest
from datetime import datetime, timedelta
from core.services.spaced_repetition import (
    SpacedRepetitionService, CardReview, ReviewQuality,
    quality_from_button, get_button_intervals
)


class TestCardReview:
    """Tests for CardReview dataclass."""
    
    def test_default_values(self):
        """Test default initialization values."""
        card = CardReview(card_id=1)
        assert card.ease_factor == 2.5
        assert card.interval == 1
        assert card.repetitions == 0
        assert card.next_review is not None
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        card = CardReview(card_id=42, ease_factor=2.3, interval=6)
        data = card.to_dict()
        assert data["card_id"] == 42
        assert data["ease_factor"] == 2.3
        assert data["interval"] == 6
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "card_id": 42,
            "ease_factor": 2.3,
            "interval": 6,
            "repetitions": 3,
            "next_review": "2024-01-15T10:00:00",
            "last_review": None,
            "total_reviews": 5
        }
        card = CardReview.from_dict(data)
        assert card.card_id == 42
        assert card.ease_factor == 2.3
        assert card.interval == 6
        assert card.repetitions == 3
        assert card.total_reviews == 5


class TestSpacedRepetitionService:
    """Tests for the SM-2 algorithm implementation."""
    
    @pytest.fixture
    def service(self):
        return SpacedRepetitionService()
    
    @pytest.fixture
    def new_card(self):
        return CardReview(card_id=1)
    
    def test_first_correct_review(self, service, new_card):
        """First correct review should set interval to 1."""
        service.review_card(new_card, ReviewQuality.GOOD)
        assert new_card.interval == 1
        assert new_card.repetitions == 1
    
    def test_second_correct_review(self, service, new_card):
        """Second correct review should set interval to 6."""
        service.review_card(new_card, ReviewQuality.GOOD)
        service.review_card(new_card, ReviewQuality.GOOD)
        assert new_card.interval == 6
        assert new_card.repetitions == 2
    
    def test_third_correct_review(self, service, new_card):
        """Third review uses ease factor for interval."""
        service.review_card(new_card, ReviewQuality.GOOD)  # interval = 1
        service.review_card(new_card, ReviewQuality.GOOD)  # interval = 6
        service.review_card(new_card, ReviewQuality.GOOD)  # interval = 6 * EF
        assert new_card.interval == round(6 * new_card.ease_factor)
        assert new_card.repetitions == 3
    
    def test_failed_review_resets(self, service, new_card):
        """Failed review should reset progress."""
        # First succeed a few times
        service.review_card(new_card, ReviewQuality.GOOD)
        service.review_card(new_card, ReviewQuality.GOOD)
        assert new_card.interval == 6
        
        # Then fail
        service.review_card(new_card, ReviewQuality.INCORRECT)
        assert new_card.interval == 1
        assert new_card.repetitions == 0
    
    def test_ease_factor_increases_with_perfect(self, service, new_card):
        """Ease factor should increase with perfect reviews."""
        initial_ef = new_card.ease_factor
        service.review_card(new_card, ReviewQuality.PERFECT)
        assert new_card.ease_factor > initial_ef
    
    def test_ease_factor_decreases_with_hard(self, service, new_card):
        """Ease factor should decrease with difficult reviews."""
        initial_ef = new_card.ease_factor
        service.review_card(new_card, ReviewQuality.DIFFICULT)
        assert new_card.ease_factor < initial_ef
    
    def test_ease_factor_minimum(self, service, new_card):
        """Ease factor should not go below minimum."""
        # Many hard reviews
        for _ in range(20):
            service.review_card(new_card, ReviewQuality.DIFFICULT)
        
        assert new_card.ease_factor >= service.MIN_EASE_FACTOR
    
    def test_next_review_date_set(self, service, new_card):
        """Next review date should be set correctly."""
        service.review_card(new_card, ReviewQuality.GOOD)
        expected = datetime.now() + timedelta(days=1)
        assert new_card.next_review.date() == expected.date()
    
    def test_get_due_cards(self, service):
        """Should correctly identify due cards."""
        # Create cards with different due dates
        card1 = CardReview(card_id=1, next_review=datetime.now() - timedelta(days=1))
        card2 = CardReview(card_id=2, next_review=datetime.now() + timedelta(days=1))
        card3 = CardReview(card_id=3, next_review=datetime.now() - timedelta(hours=1))
        
        due = service.get_due_cards([card1, card2, card3])
        
        assert len(due) == 2
        assert card1 in due
        assert card3 in due
        assert card2 not in due
    
    def test_review_stats(self, service):
        """Should calculate review statistics correctly."""
        cards = [
            CardReview(card_id=1, interval=30, repetitions=5),  # Mastered
            CardReview(card_id=2, interval=6, repetitions=2),   # Learning
            CardReview(card_id=3, interval=1, repetitions=0),   # New
        ]
        
        stats = service.get_review_stats(cards)
        
        assert stats["total"] == 3
        assert stats["mastered"] == 1
        assert stats["learning"] == 1
        assert stats["new"] == 1


class TestQualityHelpers:
    """Tests for quality rating helper functions."""
    
    def test_quality_from_button(self):
        """Test button text to quality conversion."""
        assert quality_from_button("again") == ReviewQuality.BLACKOUT
        assert quality_from_button("hard") == ReviewQuality.DIFFICULT
        assert quality_from_button("good") == ReviewQuality.GOOD
        assert quality_from_button("easy") == ReviewQuality.PERFECT
        assert quality_from_button("GOOD") == ReviewQuality.GOOD  # Case insensitive
    
    def test_get_button_intervals(self):
        """Test interval preview for buttons."""
        card = CardReview(card_id=1, ease_factor=2.5, interval=6, repetitions=2)
        intervals = get_button_intervals(card)
        
        assert "blackout" in intervals
        assert "difficult" in intervals
        assert "good" in intervals
        assert "perfect" in intervals
        assert intervals["blackout"] == 1  # Reset on fail
