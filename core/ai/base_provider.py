# core/ai/base_provider.py
"""
Abstract base class for AI providers.
Defines the interface that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple


class LLMProvider(ABC):
    """
    Abstract base class defining the interface for all AI providers.
    Every provider MUST implement all of these methods.
    
    Example implementation:
        class MyProvider(LLMProvider):
            def summarize(self, text, mode, length, language):
                # Implementation here
                return {"summary": "...", "key_points": [...], "flashcards": [...]}
    """
    
    @abstractmethod
    def summarize(
        self, 
        text: str, 
        mode: str = "concise",
        length: str = "medium",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate a complete study package from the input text.
        
        Args:
            text: The source text to summarize
            mode: Summary mode (concise, detailed, academic, simple)
            length: Target length (short, medium, long)
            language: Output language code
        
        Returns:
            Dictionary containing:
                - summary: str - The generated summary
                - key_points: List[str] - Key points extracted
                - flashcards: List[Dict] - Generated flashcards with 'q' and 'a' keys
        """
        pass
    
    @abstractmethod
    def answer(self, prompt: str, context_chunks: List[str]) -> str:
        """
        Answer a question, optionally using context from notes.
        
        Args:
            prompt: The user's question or prompt
            context_chunks: Relevant text chunks for context (RAG)
        
        Returns:
            The AI's response as a string
        """
        pass
    
    @abstractmethod
    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        """
        Generate a multiple-choice quiz from the summary.
        
        Args:
            summary_text: The summary to generate questions from
        
        Returns:
            List of question dictionaries, each containing:
                - question: str
                - options: List[str] (4 options, prefixed with A), B), etc.)
                - answer: str (correct option letter)
                - explanation: str
        """
        pass
    
    @abstractmethod
    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        """
        Generate flashcards from the summary.
        
        Args:
            summary_text: The summary to generate flashcards from
        
        Returns:
            List of flashcard dictionaries with 'q' and 'a' keys
        """
        pass
    
    @abstractmethod
    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        """
        Generate concept map data from the summary.
        
        Args:
            summary_text: The summary to analyze
        
        Returns:
            Dictionary with:
                - nodes: List[str] - Concept names
                - edges: List[List] - [[source, target, label], ...]
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if the provider is available (API key set, etc.).
        
        Returns:
            True if provider can be used, False otherwise
        """
        return True
    
    def get_model_name(self) -> str:
        """
        Get the name of the model being used.
        
        Returns:
            Model identifier string
        """
        return "unknown"
