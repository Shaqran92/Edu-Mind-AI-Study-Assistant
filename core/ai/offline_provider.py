# core/ai/offline_provider.py
"""
Offline provider using extractive summarization and rule-based generation.
Works without any API calls for basic functionality.
"""

import random
import re
from typing import List, Dict, Any
from collections import Counter
from core.ai.base_provider import LLMProvider
from utils.logger import get_logger

logger = get_logger("ai.offline")


class OfflineProvider(LLMProvider):
    """
    A self-contained, offline provider with basic extractive summarization.
    
    Uses TF-IDF-like scoring to extract important sentences.
    No API calls required - works completely offline.
    """
    
    def __init__(self):
        logger.info("Offline provider initialized")
    
    def is_available(self) -> bool:
        return True
    
    def get_model_name(self) -> str:
        return "offline-extractive"
    
    def summarize(
        self, 
        text: str, 
        mode: str = "concise",
        length: str = "medium",
        language: str = "en"
    ) -> Dict[str, Any]:
        """Generate summary using extractive methods."""
        logger.info(f"Generating offline summary (mode={mode}, length={length})")
        
        summary = self._extractive_summarize(text, length)
        key_points = self._extract_key_points(text)
        flashcards = self._generate_basic_flashcards(key_points)
        
        logger.info(f"Generated offline package: {len(summary)} char summary, "
                   f"{len(key_points)} key points, {len(flashcards)} flashcards")
        
        return {
            "summary": summary,
            "key_points": key_points,
            "flashcards": flashcards
        }
    
    def _extractive_summarize(self, text: str, length: str) -> str:
        """Extract important sentences to form a summary."""
        # Determine number of sentences based on length
        num_sentences = {
            "short": 3,
            "medium": 6,
            "long": 10
        }.get(length, 5)
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        if len(sentences) <= num_sentences:
            return " ".join(sentences)
        
        # Score sentences by word importance
        word_freq = self._calculate_word_frequency(text)
        
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            words = self._tokenize(sentence)
            score = sum(word_freq.get(w, 0) for w in words)
            # Boost earlier sentences (often contain thesis/intro)
            position_boost = 1.0 + (0.5 if i < 3 else 0)
            scored_sentences.append((sentence, score * position_boost, i))
        
        # Select top sentences and sort by original position
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:num_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: x[2])
        
        return " ".join(s[0] for s in top_sentences)
    
    def _extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key points from text."""
        sentences = self._split_sentences(text)
        
        # Filter for sentences that look like key points
        # (contain key phrases or are of medium length)
        key_phrases = ["important", "key", "main", "significant", "essential", 
                      "note that", "remember", "crucial", "primarily"]
        
        scored = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = 0
            
            # Check for key phrases
            for phrase in key_phrases:
                if phrase in sentence_lower:
                    score += 2
            
            # Prefer medium-length sentences
            words = len(sentence.split())
            if 10 <= words <= 30:
                score += 1
            
            scored.append((sentence, score))
        
        # Get top scoring sentences
        top = sorted(scored, key=lambda x: x[1], reverse=True)[:num_points]
        
        return [s[0].strip() for s in top if len(s[0].strip()) > 20]
    
    def _generate_basic_flashcards(self, key_points: List[str]) -> List[Dict[str, str]]:
        """Generate simple flashcards from key points."""
        flashcards = []
        
        for i, point in enumerate(key_points[:10]):
            # Try to split into question/answer
            if ":" in point:
                parts = point.split(":", 1)
                q = f"What is {parts[0].strip()}?"
                a = parts[1].strip()
            elif " is " in point.lower():
                # Convert "X is Y" to "What is X?" -> "Y"
                parts = re.split(r'\s+is\s+', point, 1, re.IGNORECASE)
                if len(parts) == 2:
                    q = f"What is {parts[0].strip()}?"
                    a = parts[1].strip()
                else:
                    q = f"Explain point #{i+1}"
                    a = point
            else:
                q = f"Explain: {point[:50]}..."
                a = point
            
            flashcards.append({"q": q, "a": a})
        
        return flashcards
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Basic sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _tokenize(self, text: str) -> List[str]:
        """Basic tokenization."""
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        # Filter stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                    'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
                    'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                    'this', 'that', 'these', 'those', 'it', 'its'}
        
        return [w for w in words if w not in stopwords and len(w) > 2]
    
    def _calculate_word_frequency(self, text: str) -> Dict[str, float]:
        """Calculate normalized word frequencies."""
        words = self._tokenize(text)
        freq = Counter(words)
        max_freq = max(freq.values()) if freq else 1
        return {word: count / max_freq for word, count in freq.items()}
    
    def answer(self, prompt: str, context_chunks: List[str]) -> str:
        """Provide a basic answer based on context."""
        if context_chunks:
            # Find most relevant chunk
            prompt_words = set(self._tokenize(prompt))
            
            best_chunk = None
            best_score = 0
            
            for chunk in context_chunks:
                chunk_words = set(self._tokenize(chunk))
                overlap = len(prompt_words & chunk_words)
                if overlap > best_score:
                    best_score = overlap
                    best_chunk = chunk
            
            if best_chunk:
                return (f"Based on your notes, here's what I found:\n\n"
                       f"{best_chunk[:500]}...\n\n"
                       f"*Note: This is an offline response based on keyword matching. "
                       f"For more accurate answers, configure an AI provider.*")
        
        return ("I'm currently in offline mode and can't generate detailed answers. "
               "Please configure an OpenAI or Gemini API key for full functionality.")
    
    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        """Generate a basic quiz."""
        logger.info("Generating offline quiz")
        
        sentences = self._split_sentences(summary_text)
        questions = []
        
        for i, sentence in enumerate(sentences[:5]):
            words = self._tokenize(sentence)
            if len(words) >= 3:
                # Pick a word to blank out
                target_word = random.choice(words)
                
                # Create a fill-in-the-blank style question
                question = sentence.replace(target_word, "_____")
                
                questions.append({
                    "question": f"Fill in the blank: {question}",
                    "options": [
                        f"A) {target_word}",
                        f"B) {random.choice(['concept', 'process', 'element', 'factor'])}",
                        f"C) {random.choice(['method', 'approach', 'system', 'model'])}",
                        f"D) {random.choice(['theory', 'principle', 'idea', 'notion'])}"
                    ],
                    "answer": "A",
                    "explanation": f"The correct answer is '{target_word}' as stated in the original text."
                })
        
        logger.info(f"Generated {len(questions)} offline quiz questions")
        return questions
    
    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        """Generate basic flashcards."""
        key_points = self._extract_key_points(summary_text)
        return self._generate_basic_flashcards(key_points)
    
    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        """Generate basic concept map data."""
        logger.info("Generating offline concept map")
        
        # Extract noun phrases as nodes
        words = self._tokenize(summary_text)
        word_freq = Counter(words)
        
        # Get top words as nodes
        nodes = [word for word, _ in word_freq.most_common(10)]
        
        # Create simple edges based on co-occurrence
        sentences = self._split_sentences(summary_text)
        edges = []
        
        for sentence in sentences:
            sentence_words = set(self._tokenize(sentence))
            sentence_nodes = [n for n in nodes if n in sentence_words]
            
            for i, node1 in enumerate(sentence_nodes):
                for node2 in sentence_nodes[i+1:]:
                    edges.append([node1, node2, "relates to"])
        
        # Remove duplicate edges
        unique_edges = list({tuple(e) for e in edges})
        
        logger.info(f"Generated offline concept map: {len(nodes)} nodes, {len(unique_edges)} edges")
        return {"nodes": nodes, "edges": [list(e) for e in unique_edges[:15]]}
