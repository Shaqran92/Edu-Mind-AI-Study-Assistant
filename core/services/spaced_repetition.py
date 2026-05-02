# core/services/spaced_repetition.py
"""
Spaced Repetition System using the SM-2 algorithm.
Implements intelligent flashcard scheduling for optimal retention.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from enum import Enum
import json

from utils.logger import get_logger

logger = get_logger("spaced_repetition")


class ReviewQuality(Enum):
    """
    Quality ratings for flashcard reviews.
    Based on the SM-2 algorithm scale (0-5).
    """
    BLACKOUT = 0      # Complete failure to recall
    INCORRECT = 1     # Incorrect response, but recognized upon seeing answer
    HARD = 2          # Incorrect response, but easy to recall once shown
    DIFFICULT = 3     # Correct response with significant difficulty
    GOOD = 4          # Correct response after hesitation
    PERFECT = 5       # Perfect response with no hesitation


@dataclass
class CardReview:
    """
    Represents a flashcard's review state in the spaced repetition system.
    """
    card_id: int
    ease_factor: float = 2.5       # EF starts at 2.5
    interval: int = 1              # Days until next review
    repetitions: int = 0           # Consecutive correct reviews
    next_review: Optional[datetime] = None
    last_review: Optional[datetime] = None
    total_reviews: int = 0
    
    def __post_init__(self):
        if self.next_review is None:
            self.next_review = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "card_id": self.card_id,
            "ease_factor": self.ease_factor,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "total_reviews": self.total_reviews
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CardReview':
        """Create from dictionary."""
        return cls(
            card_id=data["card_id"],
            ease_factor=data.get("ease_factor", 2.5),
            interval=data.get("interval", 1),
            repetitions=data.get("repetitions", 0),
            next_review=datetime.fromisoformat(data["next_review"]) if data.get("next_review") else None,
            last_review=datetime.fromisoformat(data["last_review"]) if data.get("last_review") else None,
            total_reviews=data.get("total_reviews", 0)
        )


class SpacedRepetitionService:
    """
    Service implementing the SM-2 (SuperMemo 2) algorithm for spaced repetition.
    
    The SM-2 algorithm schedules flashcard reviews based on:
    - Quality of recall (0-5 scale)
    - Ease factor (how easy the card is)
    - Interval (days between reviews)
    
    Example:
        >>> service = SpacedRepetitionService()
        >>> card = CardReview(card_id=1)
        >>> service.review_card(card, ReviewQuality.GOOD)
        >>> print(card.interval)  # Days until next review
        1
        >>> print(card.next_review)  # Actual next review date
    """
    
    # SM-2 Constants
    MIN_EASE_FACTOR = 1.3
    INITIAL_EASE_FACTOR = 2.5
    
    def __init__(self):
        self._cards: dict[int, CardReview] = {}
        logger.info("Spaced Repetition Service initialized")
    
    def get_or_create_card(self, card_id: int) -> CardReview:
        """Get existing card review data or create new."""
        if card_id not in self._cards:
            self._cards[card_id] = CardReview(card_id=card_id)
        return self._cards[card_id]
    
    def review_card(self, card: CardReview, quality: ReviewQuality) -> CardReview:
        """
        Process a card review and update its scheduling.
        
        Args:
            card: The card being reviewed
            quality: Quality of the recall (ReviewQuality enum)
        
        Returns:
            Updated CardReview with new interval and next_review date
        """
        q = quality.value
        logger.debug(f"Reviewing card {card.card_id} with quality {q}")
        
        # Update last review time
        card.last_review = datetime.now()
        card.total_reviews += 1
        
        if q < 3:
            # Failed review - reset the card
            card.repetitions = 0
            card.interval = 1
            logger.debug(f"Card {card.card_id} failed, resetting to interval 1")
        else:
            # Successful review - update interval
            if card.repetitions == 0:
                card.interval = 1
            elif card.repetitions == 1:
                card.interval = 6
            else:
                card.interval = round(card.interval * card.ease_factor)
            
            card.repetitions += 1
        
        # Update ease factor using SM-2 formula
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        card.ease_factor = card.ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        card.ease_factor = max(self.MIN_EASE_FACTOR, card.ease_factor)
        
        # Calculate next review date
        card.next_review = datetime.now() + timedelta(days=card.interval)
        
        # Store updated card
        self._cards[card.card_id] = card
        
        logger.info(f"Card {card.card_id}: interval={card.interval}d, EF={card.ease_factor:.2f}, "
                   f"next review={card.next_review.strftime('%Y-%m-%d')}")
        
        return card
    
    def get_due_cards(self, all_cards: List[CardReview]) -> List[CardReview]:
        """
        Get cards that are due for review.
        
        Args:
            all_cards: List of all cards to check
        
        Returns:
            List of cards due for review, sorted by priority
        """
        now = datetime.now()
        due = [c for c in all_cards if c.next_review and c.next_review <= now]
        
        # Sort by: overdue first, then by ease factor (harder cards first)
        due.sort(key=lambda c: (c.next_review, c.ease_factor))
        
        logger.info(f"Found {len(due)} cards due for review")
        return due
    
    def get_review_stats(self, cards: List[CardReview]) -> dict:
        """
        Get statistics about review progress.
        
        Returns:
            Dictionary with review statistics
        """
        now = datetime.now()
        
        due_today = sum(1 for c in cards if c.next_review and c.next_review.date() <= now.date())
        mastered = sum(1 for c in cards if c.interval >= 21)  # 3+ weeks interval
        learning = sum(1 for c in cards if c.repetitions > 0 and c.interval < 21)
        new = sum(1 for c in cards if c.repetitions == 0)
        
        return {
            "total": len(cards),
            "due_today": due_today,
            "mastered": mastered,
            "learning": learning,
            "new": new,
            "mastery_rate": (mastered / len(cards) * 100) if cards else 0
        }
    
    def get_optimal_study_order(self, cards: List[CardReview]) -> List[CardReview]:
        """
        Get cards in optimal study order.
        
        Order priority:
        1. Overdue cards (most overdue first)
        2. New cards (interleaved)
        3. Cards due today
        """
        now = datetime.now()
        
        overdue = []
        due_today = []
        new_cards = []
        
        for card in cards:
            if card.repetitions == 0:
                new_cards.append(card)
            elif card.next_review and card.next_review < now:
                overdue.append(card)
            elif card.next_review and card.next_review.date() == now.date():
                due_today.append(card)
        
        # Sort overdue by how overdue they are
        overdue.sort(key=lambda c: c.next_review or now)
        
        # Interleave new cards with review cards (1 new per 3 reviews)
        result = []
        review_cards = overdue + due_today
        new_idx = 0
        
        for i, card in enumerate(review_cards):
            result.append(card)
            if (i + 1) % 3 == 0 and new_idx < len(new_cards):
                result.append(new_cards[new_idx])
                new_idx += 1
        
        # Add remaining new cards
        result.extend(new_cards[new_idx:])
        
        return result
    
    def save_state(self, filepath: str):
        """Save review state to a JSON file."""
        data = {
            "cards": [card.to_dict() for card in self._cards.values()],
            "saved_at": datetime.now().isoformat()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self._cards)} card states to {filepath}")
    
    def load_state(self, filepath: str):
        """Load review state from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for card_data in data.get("cards", []):
                card = CardReview.from_dict(card_data)
                self._cards[card.card_id] = card
            
            logger.info(f"Loaded {len(self._cards)} card states from {filepath}")
        except FileNotFoundError:
            logger.warning(f"No saved state found at {filepath}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")


# Convenience functions for quality ratings
def quality_from_button(button_text: str) -> ReviewQuality:
    """Convert button text to ReviewQuality."""
    mapping = {
        "again": ReviewQuality.BLACKOUT,
        "hard": ReviewQuality.DIFFICULT,
        "good": ReviewQuality.GOOD,
        "easy": ReviewQuality.PERFECT
    }
    return mapping.get(button_text.lower(), ReviewQuality.GOOD)


def get_button_intervals(card: CardReview) -> dict:
    """
    Get the intervals that would result from each button press.
    Useful for showing users what each button will do.
    """
    service = SpacedRepetitionService()
    
    # Calculate intervals for each quality
    results = {}
    for quality in [ReviewQuality.BLACKOUT, ReviewQuality.DIFFICULT, 
                    ReviewQuality.GOOD, ReviewQuality.PERFECT]:
        # Create a copy to simulate
        test_card = CardReview(
            card_id=card.card_id,
            ease_factor=card.ease_factor,
            interval=card.interval,
            repetitions=card.repetitions
        )
        service.review_card(test_card, quality)
        results[quality.name.lower()] = test_card.interval
    
    return results
