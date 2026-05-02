# utils/json_parser.py
"""
Robust JSON parsing utilities for handling messy LLM outputs.
Implements multiple fallback strategies to maximize parse success rate.
"""

import json
import re
from typing import Any, Optional, Union, List, Dict

from utils.logger import get_logger

logger = get_logger("json_parser")


def safe_json_loads(
    s: str,
    expected_type: Optional[type] = None,
    default: Any = None
) -> Optional[Union[Dict, List]]:
    """
    A highly robust and forgiving JSON parser for handling messy LLM outputs.
    Implements multiple strategies to find and parse valid JSON.
    
    Args:
        s: String to parse
        expected_type: Optional expected type (dict or list) for validation
        default: Default value to return if parsing fails
    
    Returns:
        Parsed JSON object/array, or default value on failure
    
    Example:
        >>> result = safe_json_loads('Here is JSON: {"key": "value"}')
        >>> result
        {'key': 'value'}
    """
    if not isinstance(s, str):
        logger.warning(f"Input is not a string: {type(s)}")
        return default
    
    if not s.strip():
        logger.warning("Empty input string")
        return default
    
    # Track attempted strategies for debugging
    strategies_tried = []
    
    # --- Strategy 1: Direct parse (optimistic) ---
    strategies_tried.append("direct_parse")
    try:
        result = json.loads(s)
        if _validate_type(result, expected_type):
            logger.debug("Parsed JSON using direct parse")
            return result
    except json.JSONDecodeError:
        pass
    
    # --- Strategy 2: Clean markdown code blocks ---
    strategies_tried.append("clean_markdown")
    cleaned = re.sub(r'```(?:json|JSON)?\s*', '', s).strip()
    if cleaned != s.strip():
        try:
            result = json.loads(cleaned)
            if _validate_type(result, expected_type):
                logger.debug("Parsed JSON after removing markdown blocks")
                return result
        except json.JSONDecodeError:
            pass
    
    # --- Strategy 3: Extract JSON array [...] ---
    # Try arrays BEFORE objects (quiz/flashcard responses are arrays containing objects)
    strategies_tried.append("extract_array")
    match = re.search(r'\[[\s\S]*\]', s, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            if _validate_type(result, expected_type):
                logger.debug("Parsed JSON by extracting array")
                return result
        except json.JSONDecodeError:
            pass
    
    # --- Strategy 4: Extract JSON object {...} ---
    strategies_tried.append("extract_object")
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', s, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            if _validate_type(result, expected_type):
                logger.debug("Parsed JSON by extracting object")
                return result
        except json.JSONDecodeError:
            pass
    
    # --- Strategy 5: Fix trailing commas ---
    strategies_tried.append("fix_trailing_commas")
    # Remove comma before } or ]
    fixed = re.sub(r',\s*([}\]])', r'\1', s)
    try:
        result = json.loads(fixed)
        if _validate_type(result, expected_type):
            logger.debug("Parsed JSON after fixing trailing commas")
            return result
    except json.JSONDecodeError:
        pass
    
    # --- Strategy 6: Fix single quotes ---
    strategies_tried.append("fix_single_quotes")
    # Replace single quotes with double quotes (naive approach)
    fixed = s.replace("'", '"')
    try:
        result = json.loads(fixed)
        if _validate_type(result, expected_type):
            logger.debug("Parsed JSON after replacing single quotes")
            return result
    except json.JSONDecodeError:
        pass
    
    # --- Strategy 7: Extract from nested markdown ---
    strategies_tried.append("nested_markdown")
    # Sometimes AI wraps JSON like: ```json\n{...}\n```
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', s)
    if match:
        try:
            result = json.loads(match.group(1))
            if _validate_type(result, expected_type):
                logger.debug("Parsed JSON from nested markdown block")
                return result
        except json.JSONDecodeError:
            pass
    
    # --- Strategy 8: Aggressive bracket matching ---
    strategies_tried.append("aggressive_brackets")
    # Find the first { and last }, or first [ and last ]
    first_brace = s.find('{')
    last_brace = s.rfind('}')
    first_bracket = s.find('[')
    last_bracket = s.rfind(']')
    
    candidates = []
    if first_brace != -1 and last_brace > first_brace:
        candidates.append(s[first_brace:last_brace + 1])
    if first_bracket != -1 and last_bracket > first_bracket:
        candidates.append(s[first_bracket:last_bracket + 1])
    
    for candidate in candidates:
        # Apply trailing comma fix
        fixed_candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
        try:
            result = json.loads(fixed_candidate)
            if _validate_type(result, expected_type):
                logger.debug("Parsed JSON using aggressive bracket matching")
                return result
        except json.JSONDecodeError:
            pass
    
    # --- Strategy 9: Combined fixes (markdown + trailing commas + single quotes) ---
    strategies_tried.append("combined_fixes")
    combined = re.sub(r'```(?:json|JSON)?\s*', '', s).strip()
    combined = re.sub(r',\s*([}\]])', r'\1', combined)
    combined = combined.replace("'", '"')
    # Fix unescaped newlines inside strings
    combined = re.sub(r'(?<=": ")(.*?)(?=")', lambda m: m.group(0).replace('\n', '\\n'), combined)
    try:
        result = json.loads(combined)
        if _validate_type(result, expected_type):
            logger.debug("Parsed JSON using combined fixes")
            return result
    except json.JSONDecodeError:
        pass
    
    # Also try array/object extraction on combined
    for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
        match = re.search(pattern, combined, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
                if _validate_type(result, expected_type):
                    logger.debug("Parsed JSON from combined fixes + extraction")
                    return result
            except json.JSONDecodeError:
                pass

    # --- Strategy 10: Line-by-line JSON repair ---
    strategies_tried.append("line_repair")
    # Remove lines that are clearly not JSON (common AI preambles)
    lines = s.split('\n')
    json_lines = []
    in_json = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('[', '{', '"')) or in_json:
            json_lines.append(line)
            in_json = True
        if stripped.endswith((']', '}')):
            # Check if brackets balance
            joined = '\n'.join(json_lines)
            if joined.count('[') <= joined.count(']') and joined.count('{') <= joined.count('}'):
                in_json = False
    
    if json_lines:
        repaired = '\n'.join(json_lines)
        repaired = re.sub(r',\s*([}\]])', r'\1', repaired)
        try:
            result = json.loads(repaired)
            if _validate_type(result, expected_type):
                logger.debug("Parsed JSON using line-by-line repair")
                return result
        except json.JSONDecodeError:
            pass

    # --- Strategy 11: Per-object extraction (find individual {...} and make array) ---
    strategies_tried.append("per_object_extraction")
    objects = []
    depth = 0
    start = -1
    for i, ch in enumerate(s):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start != -1:
                obj_str = s[start:i+1]
                obj_str = re.sub(r',\s*([}\]])', r'\1', obj_str)
                try:
                    obj = json.loads(obj_str)
                    if isinstance(obj, dict):
                        objects.append(obj)
                except json.JSONDecodeError:
                    pass
                start = -1
    
    if objects:
        # If we found quiz-like objects, return as array
        if any('question' in obj for obj in objects):
            logger.debug(f"Extracted {len(objects)} individual JSON objects")
            return objects
        # If single object with expected keys, return it
        if len(objects) == 1:
            return objects[0]

    # --- Strategy 12: Fix escape characters ---
    strategies_tried.append("fix_escapes")
    escaped = s.replace('\\\n', '\\n').replace('\t', '\\t')
    escaped = re.sub(r'```(?:json|JSON)?\s*', '', escaped).strip()
    match = re.search(r'[\[{][\s\S]*[\]}]', escaped, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            if _validate_type(result, expected_type):
                logger.debug("Parsed JSON after fixing escape characters")
                return result
        except json.JSONDecodeError:
            pass
    
    # --- All strategies failed ---
    logger.error(f"Failed to parse JSON after trying: {strategies_tried}")
    logger.warning(f"Raw input (first 1000 chars): {s[:1000]}")
    
    return default


def _validate_type(result: Any, expected_type: Optional[type]) -> bool:
    """Validate that result matches expected type."""
    if expected_type is None:
        return True
    return isinstance(result, expected_type)


def extract_quiz_json(s: str) -> List[Dict]:
    """
    Specialized parser for quiz JSON output.
    Expects an array of question objects.
    
    Args:
        s: Raw LLM output containing quiz JSON
    
    Returns:
        List of quiz question dictionaries
    """
    result = safe_json_loads(s, expected_type=list, default=[])
    
    if not result:
        return []
    
    # Validate quiz structure
    valid_questions = []
    for i, q in enumerate(result):
        if not isinstance(q, dict):
            logger.warning(f"Quiz item {i} is not a dict, skipping")
            continue
        
        # Check required fields
        required = ['question', 'options', 'answer']
        if all(key in q for key in required):
            valid_questions.append(q)
        else:
            missing = [k for k in required if k not in q]
            logger.warning(f"Quiz item {i} missing fields: {missing}")
    
    logger.info(f"Extracted {len(valid_questions)} valid quiz questions from {len(result)} items")
    return valid_questions


def extract_flashcards_json(s: str) -> List[Dict]:
    """
    Specialized parser for flashcard JSON output.
    Expects an array of {q, a} objects.
    
    Args:
        s: Raw LLM output containing flashcard JSON
    
    Returns:
        List of flashcard dictionaries
    """
    result = safe_json_loads(s, expected_type=list, default=[])
    
    if not result:
        return []
    
    # Validate flashcard structure
    valid_cards = []
    for i, card in enumerate(result):
        if not isinstance(card, dict):
            continue
        
        # Accept both 'q'/'a' and 'question'/'answer' formats
        question = card.get('q') or card.get('question')
        answer = card.get('a') or card.get('answer')
        
        if question and answer:
            valid_cards.append({'q': question, 'a': answer})
        else:
            logger.debug(f"Flashcard {i} missing q or a field")
    
    logger.info(f"Extracted {len(valid_cards)} valid flashcards from {len(result)} items")
    return valid_cards


def extract_concept_map_json(s: str) -> Dict:
    """
    Specialized parser for concept map JSON output.
    Expects {nodes: [...], edges: [...]}.
    
    Args:
        s: Raw LLM output containing concept map JSON
    
    Returns:
        Dict with nodes and edges lists
    """
    result = safe_json_loads(s, expected_type=dict, default={})
    
    if not result:
        return {'nodes': [], 'edges': []}
    
    # Validate structure
    nodes = result.get('nodes', [])
    edges = result.get('edges', [])
    
    # Ensure nodes is a list of strings
    if not isinstance(nodes, list):
        nodes = []
    nodes = [str(n) for n in nodes if n]
    
    # Ensure edges is a list of lists/tuples
    if not isinstance(edges, list):
        edges = []
    valid_edges = []
    for edge in edges:
        if isinstance(edge, (list, tuple)) and len(edge) >= 2:
            valid_edges.append(list(edge))
    
    logger.info(f"Extracted concept map with {len(nodes)} nodes and {len(valid_edges)} edges")
    return {'nodes': nodes, 'edges': valid_edges}


if __name__ == "__main__":
    # Test cases
    test_cases = [
        '{"key": "value"}',
        'Here is JSON: {"key": "value"} more text',
        '```json\n{"key": "value"}\n```',
        '{"key": "value",}',  # Trailing comma
        "[{'q': 'question', 'a': 'answer'}]",  # Single quotes
        'The answer is: [{"q": "What?", "a": "Answer"}]',
    ]
    
    for test in test_cases:
        print(f"\nInput: {test[:50]}...")
        result = safe_json_loads(test)
        print(f"Result: {result}")
