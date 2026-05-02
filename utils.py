# utils.py
import json
import re
from datetime import datetime

def safe_json_loads(s: str):
    """
    A highly robust and forgiving JSON parser for handling messy LLM outputs.
    It attempts multiple strategies to find and parse a valid JSON object or array.
    """
    if not isinstance(s, str):
        return None

    # --- Strategy 1: Strip markdown code blocks first (most common LLM pattern) ---
    # Remove ```json ... ``` or ``` ... ``` wrapping - handle \r\n and \n
    cleaned = re.sub(r'```(?:json|JSON)?\s*', '', s).strip()
    
    # Try direct parse on cleaned string
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # --- Strategy 2: Extract JSON array or object from the string ---
    # Try array first (quiz/flashcard responses), then object
    for pattern in [r'\[.*\]', r'\{.*\}']:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

    # --- Strategy 3: Fix trailing commas (common AI mistake) ---
    fixed = re.sub(r',\s*([\}\]])', r'\1', cleaned)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # --- Strategy 4: Try original string directly ---
    try:
        return json.loads(s.strip())
    except json.JSONDecodeError:
        pass

    print(f"   - Warning: Could not parse JSON from AI response (first 300 chars): {s[:300]}")
    return None


def chunk_text(text: str, max_chars: int):
    """Splits a long text into smaller chunks of a specified max character size."""
    if not text:
        return []
    
    text = text.strip()
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        end_pos = min(current_pos + max_chars, len(text))
        
        # Try to find a natural break (paragraph or sentence) before the hard limit
        break_pos = text.rfind('\n\n', current_pos, end_pos)
        if break_pos == -1:
            break_pos = text.rfind('. ', current_pos, end_pos)
        
        if break_pos != -1 and (break_pos - current_pos) > (max_chars * 0.5):
            end_pos = break_pos + 1
        
        chunks.append(text[current_pos:end_pos].strip())
        current_pos = end_pos
        
    return [c for c in chunks if c]


def now_iso():
    """Returns the current UTC time in ISO 8601 format."""
    return datetime.utcnow().isoformat(timespec='seconds') + "Z"