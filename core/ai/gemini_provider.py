# core/ai/gemini_provider.py
"""
Google Gemini API provider implementation.
"""

from typing import List, Dict, Any
from core.ai.base_provider import LLMProvider
from config import settings
from utils.logger import get_logger
from utils.json_parser import safe_json_loads, extract_quiz_json, extract_flashcards_json, extract_concept_map_json
from prompts import (
    MULTI_TASK_PROMPT, MODE_INSTRUCTIONS, LENGTH_INSTRUCTIONS,
    QUIZ_PROMPT, FLASHCARDS_PROMPT, CONCEPT_MAP_PROMPT, CHAT_PROMPT
)

logger = get_logger("ai.gemini")

# Optional import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai package not installed")


class GeminiProvider(LLMProvider):
    """
    Provider for Google's Gemini models.
    
    Requires the google-generativeai package and a valid API key.
    """
    
    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")
        
        self.api_key = settings.gemini_api_key
        self.model_name = settings.model_gemini
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini provider initialized with model: {self.model_name}")
        else:
            self.model = None
            logger.warning("Gemini API key not configured")
    
    def is_available(self) -> bool:
        return self.model is not None and bool(self.api_key)
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def _generate(self, prompt: str) -> str:
        """Send a prompt to the Gemini API."""
        if not self.is_available():
            raise RuntimeError("Gemini provider not available")
        
        logger.debug(f"Sending request to Gemini ({len(prompt)} chars)")
        
        response = self.model.generate_content(prompt)
        content = response.text
        
        logger.debug(f"Received response ({len(content)} chars)")
        return content
    
    def summarize(
        self, 
        text: str, 
        mode: str = "concise",
        length: str = "medium",
        language: str = "en"
    ) -> Dict[str, Any]:
        """Generate a complete study package using the multi-task prompt."""
        logger.info(f"Generating study package (mode={mode}, length={length}, lang={language})")
        
        prompt = MULTI_TASK_PROMPT.format(
            mode=mode,
            mode_instructions=MODE_INSTRUCTIONS.get(mode, ""),
            length=length,
            length_instructions=LENGTH_INSTRUCTIONS.get(length, ""),
            language=language,
            content=text[:8000]  # Truncate to avoid token limits
        )
        
        response = self._generate(prompt)
        result = safe_json_loads(response, expected_type=dict)
        
        if result:
            logger.info(f"Generated package: {len(result.get('summary', ''))} char summary, "
                       f"{len(result.get('key_points', []))} key points, "
                       f"{len(result.get('flashcards', []))} flashcards")
            return {
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", []),
                "flashcards": result.get("flashcards", [])
            }
        
        logger.error("Failed to parse study package response")
        return {"summary": response, "key_points": [], "flashcards": []}
    
    def answer(self, prompt: str, context_chunks: List[str]) -> str:
        """Answer a question using optional context."""
        if context_chunks:
            chunks_text = "\n---\n".join(context_chunks)
            full_prompt = CHAT_PROMPT.format(chunks=chunks_text, question=prompt)
        else:
            full_prompt = prompt
        
        return self._generate(full_prompt)
    
    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        """Generate a quiz from the summary."""
        logger.info("Generating quiz")
        
        prompt = QUIZ_PROMPT.format(summary=summary_text)
        response = self._generate(prompt)
        
        questions = extract_quiz_json(response)
        logger.info(f"Generated {len(questions)} quiz questions")
        return questions
    
    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        """Generate flashcards from the summary."""
        logger.info("Generating flashcards")
        
        prompt = FLASHCARDS_PROMPT.format(summary=summary_text)
        response = self._generate(prompt)
        
        cards = extract_flashcards_json(response)
        logger.info(f"Generated {len(cards)} flashcards")
        return cards
    
    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        """Generate concept map data."""
        logger.info("Generating concept map")
        
        prompt = CONCEPT_MAP_PROMPT.format(summary=summary_text)
        response = self._generate(prompt)
        
        data = extract_concept_map_json(response)
        logger.info(f"Generated concept map: {len(data.get('nodes', []))} nodes, "
                   f"{len(data.get('edges', []))} edges")
        return data
