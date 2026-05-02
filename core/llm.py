# core/llm.py
from typing import Tuple, List, Dict, Any
import re
import json
import collections
import random
from config import settings
from prompts import (
    MULTI_TASK_PROMPT, MODE_INSTRUCTIONS, LENGTH_INSTRUCTIONS,
    QUIZ_PROMPT, FLASHCARDS_PROMPT, CONCEPT_MAP_PROMPT, CHAT_PROMPT
)
from utils import safe_json_loads

# Optional imports for online providers
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class LLMProvider:
    """
    Abstract base class defining the interface for all AI providers.
    Every provider MUST implement all of these methods.
    """
    def summarize(self, text: str, mode: str, length: str, language: str) -> Dict[str, Any]:
        raise NotImplementedError
        
    def answer(self, prompt: str, context_chunks: List[str]) -> str:
        raise NotImplementedError

    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        raise NotImplementedError
        
    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """Provider for OpenAI's models (e.g., ChatGPT)."""
    def __init__(self):
        if not OpenAI: raise RuntimeError("OpenAI package not installed.")
        if not settings.openai_api_key: raise RuntimeError("OPENAI_API_KEY not set.")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.model_openai

    def _chat(self, user_prompt: str, max_tokens: int = 2048) -> str:
        """Sends a prompt to the OpenAI Chat API."""
        return self.client.chat.completions.create(
            model=self.model, temperature=0.3, max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that always returns valid, complete JSON as requested."},
                {"role": "user", "content": user_prompt}
            ]
        ).choices[0].message.content

    def summarize(self, text: str, mode: str, length: str, language: str) -> Dict[str, Any]:
        max_tokens_map = {"short": 2000, "medium": 3000, "long": 4096}
        prompt = MULTI_TASK_PROMPT.format(
            content=text[:12000], mode=mode.title(),
            mode_instructions=MODE_INSTRUCTIONS.get(mode.lower(), ""),
            length=length.title(), length_instructions=LENGTH_INSTRUCTIONS.get(length.lower(), ""),
            language=language.title()
        )
        response_text = self._chat(prompt, max_tokens=max_tokens_map.get(length, 3000))
        data = safe_json_loads(response_text)
        if data and isinstance(data, dict) and "summary" in data:
            return {
                "summary": data.get("summary", "No summary generated."),
                "key_points": data.get("key_points", []),
                "flashcards": data.get("flashcards", [])
            }
        return {"summary": response_text, "key_points": [], "flashcards": []}

    def answer(self, prompt: str, context_chunks: List[str]) -> str:
        return self._chat(prompt, max_tokens=1000)

    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        prompt = QUIZ_PROMPT.format(summary=summary_text)
        response_text = self._chat(prompt, max_tokens=4096)
        
        data = safe_json_loads(response_text)
        
        if data and isinstance(data, list):
            print(f"      - Successfully parsed {len(data)} questions from OpenAI.")
            return [q for q in data if isinstance(q, dict) and q.get("question")]
        
        print("      - ⚠️ OpenAI response for quiz was not a valid list, even after robust parsing.")
        return []

    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        prompt = FLASHCARDS_PROMPT.format(summary=summary_text)
        response_text = self._chat(prompt, max_tokens=2000)
        data = safe_json_loads(response_text)
        return data if isinstance(data, list) else []
        
    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        prompt = CONCEPT_MAP_PROMPT.format(summary=summary_text)
        response_text = self._chat(prompt, max_tokens=1024)
        data = safe_json_loads(response_text)
        if data and isinstance(data, dict) and "nodes" in data and "edges" in data:
            return data
        return {"nodes": [], "edges": []}

class GeminiProvider(LLMProvider):
    """Provider for Google's Gemini models.
    
    Auto-detects the best available model for the installed SDK version,
    and distinguishes 404 (wrong model) from 429 (rate limit) errors.
    """

    # Models tried in priority order — newest / highest-quota first
    _MODEL_CANDIDATES = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-1.0-pro",
    ]

    def __init__(self):
        if not genai:
            raise RuntimeError("google-generativeai package not installed.")
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not set.")

        genai.configure(api_key=settings.gemini_api_key)
        self._last_call_time = 0.0

        # Use configured model if set, otherwise auto-detect
        preferred = getattr(settings, "model_gemini", "").strip()
        if preferred:
            self.model_name = preferred
            self.model = genai.GenerativeModel(preferred)
            print(f"   🤖 Gemini provider using configured model: {preferred}")
        else:
            self.model_name, self.model = self._detect_model()

    def _detect_model(self):
        """Try each candidate model with a cheap ping to find what works."""
        import time
        ping = "Say OK"
        for name in self._MODEL_CANDIDATES:
            try:
                m = genai.GenerativeModel(name)
                resp = m.generate_content(ping)
                _ = resp.text   # force evaluation
                print(f"   ✅ Gemini auto-detected working model: {name}")
                return name, m
            except Exception as e:
                err = str(e)
                if "404" in err or "not found" in err.lower():
                    continue          # try next model
                # Any other error (rate limit etc.) — still use this model
                print(f"   ⚠️  Model {name} errored on ping ({e}), using it anyway.")
                return name, genai.GenerativeModel(name)
        raise RuntimeError(
            "No Gemini model available. Check your API key and google-generativeai version."
        )

    @staticmethod
    def _classify_error(e: Exception):
        """Return ('rate_limit' | 'not_found' | 'other', message)."""
        err = str(e).lower()
        if "429" in err or "resource_exhausted" in err or "quota" in err:
            return "rate_limit", str(e)
        if "404" in err or "not found" in err or "not supported" in err:
            return "not_found", str(e)
        return "other", str(e)

    def _gen(self, prompt: str, max_tokens: int = 8192) -> str:
        """Generate content with smart retry (rate-limits only, not 404s)."""
        import time

        # Throttle: free tier allows ~15 RPM → 1 req / 4 s
        elapsed = time.time() - self._last_call_time
        if elapsed < 4.0:
            time.sleep(4.0 - elapsed)

        max_retries = 3
        base_delay  = 20   # seconds

        for attempt in range(max_retries):
            try:
                self._last_call_time = time.time()
                try:
                    cfg = genai.types.GenerationConfig(
                        temperature=0.3, max_output_tokens=max_tokens
                    )
                    resp = self.model.generate_content(prompt, generation_config=cfg)
                except (AttributeError, TypeError):
                    resp = self.model.generate_content(prompt)
                return resp.text

            except Exception as e:
                kind, msg = self._classify_error(e)

                if kind == "not_found":
                    # Model not available — re-detect and retry once
                    print(f"   ❌ Model '{self.model_name}' not found. Re-detecting…")
                    try:
                        self.model_name, self.model = self._detect_model()
                        continue   # retry with new model
                    except RuntimeError as re:
                        raise RuntimeError(str(re)) from e

                if kind == "rate_limit" and attempt < max_retries - 1:
                    wait = base_delay * (2 ** attempt)   # 20 → 40 → 80 s
                    print(f"   ⚠️  Gemini rate limit. Waiting {wait}s "
                          f"(retry {attempt + 1}/{max_retries - 1})…")
                    time.sleep(wait)
                    continue

                print(f"   ❌ Gemini error [{kind}]: {msg}")
                raise RuntimeError(f"Gemini API error: {msg}") from e

        return ""



    def summarize(self, text: str, mode: str, length: str, language: str) -> Dict[str, Any]:
        try:
            prompt = MULTI_TASK_PROMPT.format(
                content=text[:12000], mode=mode.title(),
                mode_instructions=MODE_INSTRUCTIONS.get(mode.lower(), ""),
                length=length.title(), length_instructions=LENGTH_INSTRUCTIONS.get(length.lower(), ""),
                language=language.title()
            )
            response_text = self._gen(prompt)
            data = safe_json_loads(response_text)
            if data and isinstance(data, dict) and "summary" in data:
                return {
                    "summary": data.get("summary", "No summary generated."),
                    "key_points": data.get("key_points", []),
                    "flashcards": data.get("flashcards", [])
                }
            return {"summary": response_text, "key_points": [], "flashcards": []}
        except RuntimeError as e:
            print(f"   ⚠️  Gemini quota exhausted, using offline fallback. ({e})")
            return OfflineProvider().summarize(text, mode, length, language)

    def answer(self, prompt: str, context_chunks: List[str]) -> str:
        try:
            return self._gen(prompt)
        except RuntimeError as e:
            print(f"   ⚠️  Gemini quota exhausted, using offline fallback. ({e})")
            return OfflineProvider().answer(prompt, context_chunks)

    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        try:
            prompt = QUIZ_PROMPT.format(summary=summary_text)
            response_text = self._gen(prompt)
            print(f"      - Raw Gemini quiz response length: {len(response_text)} chars")
            data = safe_json_loads(response_text)
            if data and isinstance(data, list):
                print(f"      - Successfully parsed {len(data)} questions from Gemini.")
                return [q for q in data if isinstance(q, dict) and q.get("question")]
            if data and isinstance(data, dict):
                for key in ("questions", "quiz", "data", "items", "results"):
                    if key in data and isinstance(data[key], list):
                        questions = [q for q in data[key] if isinstance(q, dict) and q.get("question")]
                        if questions:
                            print(f"      - Parsed {len(questions)} questions from Gemini (key: '{key}').")
                            return questions
                for key, val in data.items():
                    if isinstance(val, list) and val and isinstance(val[0], dict) and val[0].get("question"):
                        questions = [q for q in val if isinstance(q, dict) and q.get("question")]
                        print(f"      - Parsed {len(questions)} questions from Gemini (key: '{key}').")
                        return questions
            print("      - Warning: Gemini quiz response not parseable, using offline fallback.")
            return OfflineProvider().quiz(summary_text)
        except RuntimeError as e:
            print(f"   ⚠️  Gemini quota exhausted for quiz, using offline fallback. ({e})")
            return OfflineProvider().quiz(summary_text)

    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        try:
            prompt = FLASHCARDS_PROMPT.format(summary=summary_text)
            response_text = self._gen(prompt)
            data = safe_json_loads(response_text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ("flashcards", "cards", "data", "items"):
                    if key in data and isinstance(data[key], list):
                        return data[key]
            return OfflineProvider().flashcards(summary_text)
        except RuntimeError as e:
            print(f"   ⚠️  Gemini quota exhausted for flashcards, using offline fallback. ({e})")
            return OfflineProvider().flashcards(summary_text)

    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        try:
            prompt = CONCEPT_MAP_PROMPT.format(summary=summary_text)
            response_text = self._gen(prompt)
            data = safe_json_loads(response_text)
            if data and isinstance(data, dict) and "nodes" in data and "edges" in data:
                return data
            if data and isinstance(data, dict):
                for key in ("concept_map", "map", "data"):
                    if key in data and isinstance(data[key], dict):
                        inner = data[key]
                        if "nodes" in inner and "edges" in inner:
                            return inner
            return OfflineProvider().concept_map(summary_text)
        except RuntimeError as e:
            print(f"   ⚠️  Gemini quota exhausted for concept map, using offline fallback. ({e})")
            return OfflineProvider().concept_map(summary_text)

class OfflineProvider(LLMProvider):
    """A self-contained, offline provider with advanced NLP-based functionality."""
    
    def summarize(self, text: str, mode: str, length: str, language: str) -> Dict[str, Any]:
        print("   - Using OFFLINE summarization and flashcard engine.")
        summary, key_points = self._offline_summarize_logic(text, length)
        flashcards = self._offline_flashcard_logic(summary)
        return {"summary": summary, "key_points": key_points, "flashcards": flashcards}

    def _offline_summarize_logic(self, text, length):
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        length_map = {"short": 0.2, "medium": 0.4, "long": 0.6}
        target_count = max(3, int(len(sentences) * length_map.get(length, 0.4)))
        words = re.findall(r'\b\w{4,}\b', text.lower())
        stop_words = set("a an and the of in on is are was were to for with by this that from as at it be has have had do does did will would could should may might can shall not but or nor so yet also very too much many more most some any all each every both few several only just even still already often never always sometimes usually".split())
        freqs = collections.Counter(w for w in words if w not in stop_words)
        scores = [(sum(freqs.get(w, 0) for w in re.findall(r'\b\w{4,}\b', s.lower())), i, s) for i, s in enumerate(sentences)]
        scores.sort(reverse=True)
        top_sentences = sorted(scores[:target_count], key=lambda x: x[1])
        summary = " ".join(s for _, _, s in top_sentences)
        key_points = [f"• {w.capitalize()}" for w, _ in freqs.most_common(8)]
        return summary, key_points
    
    def _offline_flashcard_logic(self, summary_text):
        sentences = re.split(r'(?<=[.!?])\s+', summary_text.strip())
        cards = []
        for s in sentences:
            words = s.split()
            if len(words) > 8:
                keyword_index = len(words) // 2
                keyword = words[keyword_index]
                if len(keyword) > 4 and keyword.lower() not in ["this", "that", "however", "which", "their", "these"]:
                    question = s.replace(keyword, "______", 1)
                    cards.append({"q": question, "a": keyword})
        return cards[:10]

    def answer(self, prompt: str, context_chunks: List[str]) -> str:
        """Enhanced offline chat that searches context chunks for relevant info."""
        if context_chunks:
            # Simple keyword matching for offline mode
            prompt_lower = prompt.lower()
            keywords = [w for w in re.findall(r'\b\w{4,}\b', prompt_lower) 
                       if w not in {"what", "when", "where", "which", "that", "this", "does", "have"}]
            
            best_chunk = ""
            best_score = 0
            for chunk in context_chunks:
                score = sum(1 for kw in keywords if kw in chunk.lower())
                if score > best_score:
                    best_score = score
                    best_chunk = chunk
            
            if best_chunk:
                return f"Based on your notes, here's what I found:\n\n{best_chunk[:800]}\n\n*Note: This is an offline response. Connect an AI provider for more detailed answers.*"
        
        return ("I'm currently running in offline mode, which limits my ability to generate detailed answers. "
                "To enable full AI-powered responses, please configure an API key in Settings → API Configuration.\n\n"
                "**Available offline features:** Summarization, Flashcard generation, Quiz generation, and Concept maps.")
    
    def quiz(self, summary_text: str) -> List[Dict[str, Any]]:
        """Generate quiz questions offline using NLP-based extraction."""
        print("   - Using OFFLINE quiz generator.")
        
        sentences = re.split(r'(?<=[.!?])\s+', summary_text.strip())
        if len(sentences) < 3:
            print("   - Not enough content for quiz generation.")
            return []
        
        # Extract key terms and their context
        stop_words = set("a an and the of in on is are was were to for with by this that from as at it be has have had do does did will would could should may might can shall not but or nor so yet also very too much many more most some any all each every both few several only just even still already often never always sometimes usually".split())
        
        words = re.findall(r'\b\w{4,}\b', summary_text.lower())
        freqs = collections.Counter(w for w in words if w not in stop_words)
        top_terms = [w for w, _ in freqs.most_common(20)]
        
        quiz_questions = []
        used_sentences = set()
        
        for sentence in sentences:
            if len(quiz_questions) >= 8:
                break
            
            sentence = sentence.strip()
            if len(sentence) < 30 or sentence in used_sentences:
                continue
            
            # Find key terms in this sentence
            sentence_words = re.findall(r'\b\w{4,}\b', sentence.lower())
            key_terms_in_sentence = [w for w in sentence_words if w in top_terms[:15] and w not in stop_words]
            
            if not key_terms_in_sentence:
                continue
            
            # Pick the most important term as the answer
            answer_term = key_terms_in_sentence[0]
            
            # Create a fill-in-the-blank question
            question_text = re.sub(
                r'\b' + re.escape(answer_term) + r'\b',
                "______",
                sentence,
                count=1,
                flags=re.IGNORECASE
            )
            
            if "______" not in question_text:
                continue
            
            question_text = f"Fill in the blank: {question_text}"
            
            # Generate distractors from other top terms
            distractors = [t for t in top_terms if t != answer_term][:3]
            while len(distractors) < 3:
                distractors.append(f"option_{len(distractors)+1}")
            
            # Create options with random placement of correct answer
            options = [answer_term.capitalize()] + [d.capitalize() for d in distractors[:3]]
            random.shuffle(options)
            correct_idx = options.index(answer_term.capitalize())
            correct_letter = chr(65 + correct_idx)  # A, B, C, D
            
            labeled_options = [f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)]
            
            quiz_questions.append({
                "question": question_text,
                "options": labeled_options,
                "answer": correct_letter,
                "explanation": f"The correct answer is '{answer_term.capitalize()}' as mentioned in the study material."
            })
            used_sentences.add(sentence)
        
        print(f"   - Generated {len(quiz_questions)} offline quiz questions.")
        return quiz_questions

    def flashcards(self, summary_text: str) -> List[Dict[str, str]]:
        print("   - Using OFFLINE flashcard generator.")
        return self._offline_flashcard_logic(summary_text)

    def concept_map(self, summary_text: str) -> Dict[str, Any]:
        """Enhanced offline concept map generation using NLP."""
        print("   - Using OFFLINE concept map generator.")
        
        stop_words = set("a an and the of in on is are was were to for with by this that from as at it be has have had do does did will would could should may might can shall not but or nor so yet also very too much many more most some any all each every both few several only just even still already often never always sometimes usually about after before between through during which their there these those being been would could should might".split())
        
        # Extract capitalized terms (likely proper nouns / key concepts)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', summary_text)
        cap_freqs = collections.Counter(capitalized)
        
        # Also extract frequent significant words
        all_words = re.findall(r'\b[a-zA-Z]{5,}\b', summary_text.lower())
        word_freqs = collections.Counter(w for w in all_words if w not in stop_words)
        
        # Combine: prioritize capitalized terms, fill with frequent words
        nodes = []
        seen = set()
        for w, _ in cap_freqs.most_common(8):
            if w.lower() not in seen:
                nodes.append(w)
                seen.add(w.lower())
        for w, _ in word_freqs.most_common(15):
            if w not in seen and len(nodes) < 12:
                nodes.append(w.capitalize())
                seen.add(w)
        
        if len(nodes) < 3:
            nodes = [w.capitalize() for w, _ in word_freqs.most_common(10)]
        
        nodes = nodes[:12]
        
        # Generate edges based on co-occurrence in sentences
        sentences = re.split(r'(?<=[.!?])\s+', summary_text.strip())
        edges = []
        edge_set = set()
        
        relationship_verbs = ["relates to", "influences", "is part of", "connects to", "leads to", "supports", "enables"]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            nodes_in_sentence = [n for n in nodes if n.lower() in sentence_lower]
            
            for i in range(len(nodes_in_sentence)):
                for j in range(i+1, len(nodes_in_sentence)):
                    edge_key = (nodes_in_sentence[i], nodes_in_sentence[j])
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        rel = random.choice(relationship_verbs)
                        edges.append([nodes_in_sentence[i], nodes_in_sentence[j], rel])
        
        # If no natural edges found, create sequential ones
        if not edges and len(nodes) > 1:
            for i in range(len(nodes) - 1):
                edges.append([nodes[i], nodes[i+1], "related to"])
        
        return {"nodes": nodes, "edges": edges}

# ── Singleton provider cache ──────────────────────────────────────────
# Avoids re-initialising (and re-running model-detect ping) on every call.
_provider_cache: dict = {}

def get_provider() -> LLMProvider:
    """Return the configured AI provider, creating it only once per session."""
    provider_name = settings.provider
    if provider_name not in _provider_cache:
        if provider_name == "openai":
            try:
                _provider_cache[provider_name] = OpenAIProvider()
            except Exception as e:
                print(f"   - ❌ OpenAI failed: {e}. Falling back to offline.")
                _provider_cache[provider_name] = OfflineProvider()
        elif provider_name == "gemini":
            try:
                _provider_cache[provider_name] = GeminiProvider()
            except Exception as e:
                print(f"   - ❌ Gemini failed: {e}. Falling back to offline.")
                _provider_cache[provider_name] = OfflineProvider()
        else:
            _provider_cache[provider_name] = OfflineProvider()
    return _provider_cache[provider_name]


def reset_provider_cache():
    """Force re-initialisation of the provider (e.g. after settings change)."""
    _provider_cache.clear()