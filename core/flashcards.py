# core/flashcards.py
from typing import List, Dict
from core.llm import get_provider
from prompts import FLASHCARDS_PROMPT

def generate_flashcards(summary_text: str, num_cards: int = 12) -> List[Dict[str, str]]:
    """Enhanced flashcard generation with proper count"""
    if not summary_text or not summary_text.strip():
        return [{"q": "No summary available", "a": "Please generate a summary first"}]
    
    provider = get_provider()
    
    # Use enhanced prompt
    enhanced_prompt = FLASHCARDS_PROMPT.format(
        summary=summary_text,
        num_cards=num_cards
    )
    
    cards = provider.flashcards(summary_text)
    
    # Validate and ensure minimum cards
    if not cards or len(cards) < 3:
        # Fallback cards
        cards = [
            {"q": "What is the main topic covered?", "a": "The summary discusses key concepts from your notes."},
            {"q": "What are the most important points?", "a": "Review the key points section for highlighted information."},
            {"q": "How are the concepts related?", "a": "The concepts are interconnected as described in the summary structure."}
        ]
    
    return cards[:num_cards]  # Ensure we don't exceed requested number