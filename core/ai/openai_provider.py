# core/ai/openai_provider.py
"""
OpenAI API provider implementation.
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

logger = get_logger("ai.openai")

# Optional import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed")


class OpenAIProvider(LLMProvider):
    """
    Provider for OpenAI's models (e.g., GPT-4, GPT-4o-mini).
    
    Requires the openai package and a valid API key.
    """
    
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI package not installed. Run: pip install openai")
        
        self.api_key = settings.openai_api_key
        self.model = settings.model_openai
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI provider initialized with model: {self.model}")
        else:
            self.client = None
            logger.warning("OpenAI API key not configured")
    
    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key)
    
    def get_model_name(self) -> str:
        return self.model
    
    def _chat(self, user_prompt: str, max_tokens: int = 2048) -> str:
        """Send a prompt to the OpenAI Chat API."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")
        
        logger.debug(f"Sending request to OpenAI ({len(user_prompt)} chars)")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
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
        
        response = self._chat(prompt, max_tokens=3000)
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
        
        return self._chat(full_prompt, max_tokens=1500)
    
    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        """Generate a quiz from the summary."""
        logger.info("Generating quiz")
        
        prompt = QUIZ_PROMPT.format(summary=summary_text)
        response = self._chat(prompt, max_tokens=2500)
        
        questions = extract_quiz_json(response)
        logger.info(f"Generated {len(questions)} quiz questions")
        return questions
    
    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        """Generate flashcards from the summary."""
        logger.info("Generating flashcards")
        
        prompt = FLASHCARDS_PROMPT.format(summary=summary_text)
        response = self._chat(prompt, max_tokens=2000)
        
        cards = extract_flashcards_json(response)
        logger.info(f"Generated {len(cards)} flashcards")
        return cards
    
    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        """Generate concept map data."""
        logger.info("Generating concept map")
        
        prompt = CONCEPT_MAP_PROMPT.format(summary=summary_text)
        response = self._chat(prompt, max_tokens=1500)
        
        data = extract_concept_map_json(response)
        logger.info(f"Generated concept map: {len(data.get('nodes', []))} nodes, "
                   f"{len(data.get('edges', []))} edges")
        return data
