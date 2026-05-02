# tests/unit/test_json_parser.py
"""
Unit tests for the JSON parser utilities.
"""

import pytest
from utils.json_parser import (
    safe_json_loads,
    extract_quiz_json,
    extract_flashcards_json,
    extract_concept_map_json
)


class TestSafeJsonLoads:
    """Tests for the safe_json_loads function."""
    
    def test_valid_json_object(self):
        """Test parsing a valid JSON object."""
        result = safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_valid_json_array(self):
        """Test parsing a valid JSON array."""
        result = safe_json_loads('[1, 2, 3]')
        assert result == [1, 2, 3]
    
    def test_json_with_surrounding_text(self):
        """Test extracting JSON from surrounding text."""
        result = safe_json_loads('Here is the result: {"key": "value"} as you can see.')
        assert result == {"key": "value"}
    
    def test_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        result = safe_json_loads('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}
    
    def test_trailing_comma(self):
        """Test handling trailing commas."""
        result = safe_json_loads('{"key": "value",}')
        assert result == {"key": "value"}
    
    def test_array_trailing_comma(self):
        """Test handling trailing commas in arrays."""
        result = safe_json_loads('[1, 2, 3,]')
        assert result == [1, 2, 3]
    
    def test_empty_string(self):
        """Test handling empty string."""
        result = safe_json_loads('')
        assert result is None
    
    def test_non_string_input(self):
        """Test handling non-string input."""
        result = safe_json_loads(123)
        assert result is None
    
    def test_invalid_json(self):
        """Test handling completely invalid JSON."""
        result = safe_json_loads('not json at all')
        assert result is None
    
    def test_expected_type_dict(self):
        """Test type validation for dict."""
        result = safe_json_loads('[1, 2]', expected_type=dict)
        assert result is None
    
    def test_expected_type_list(self):
        """Test type validation for list."""
        result = safe_json_loads('{"key": "value"}', expected_type=list)
        assert result is None
    
    def test_default_value(self):
        """Test returning default value on failure."""
        result = safe_json_loads('invalid', default=[])
        assert result == []
    
    def test_nested_json(self):
        """Test parsing nested JSON."""
        json_str = '{"outer": {"inner": [1, 2, 3]}}'
        result = safe_json_loads(json_str)
        assert result == {"outer": {"inner": [1, 2, 3]}}


class TestExtractQuizJson:
    """Tests for quiz JSON extraction."""
    
    def test_valid_quiz(self, sample_quiz_json):
        """Test extracting valid quiz JSON."""
        result = extract_quiz_json(sample_quiz_json)
        assert len(result) == 1
        assert result[0]["question"] == "What is machine learning?"
        assert result[0]["answer"] == "B"
    
    def test_quiz_with_wrapper_text(self, sample_quiz_json):
        """Test extracting quiz from wrapped text."""
        wrapped = f"Here is your quiz:\n{sample_quiz_json}\nGood luck!"
        result = extract_quiz_json(wrapped)
        assert len(result) == 1
    
    def test_invalid_quiz_item(self):
        """Test filtering invalid quiz items."""
        json_str = '[{"question": "Q1"}, {"question": "Q2", "options": [], "answer": "A"}]'
        result = extract_quiz_json(json_str)
        assert len(result) == 1  # Only valid item
    
    def test_empty_input(self):
        """Test empty input returns empty list."""
        result = extract_quiz_json('')
        assert result == []


class TestExtractFlashcardsJson:
    """Tests for flashcard JSON extraction."""
    
    def test_valid_flashcards(self, sample_flashcards_json):
        """Test extracting valid flashcards."""
        result = extract_flashcards_json(sample_flashcards_json)
        assert len(result) == 2
        assert result[0]["q"] == "What is supervised learning?"
    
    def test_alternate_format(self):
        """Test flashcards with full 'question'/'answer' keys."""
        json_str = '[{"question": "Q1", "answer": "A1"}]'
        result = extract_flashcards_json(json_str)
        assert len(result) == 1
        assert result[0]["q"] == "Q1"
        assert result[0]["a"] == "A1"
    
    def test_empty_input(self):
        """Test empty input returns empty list."""
        result = extract_flashcards_json('')
        assert result == []


class TestExtractConceptMapJson:
    """Tests for concept map JSON extraction."""
    
    def test_valid_concept_map(self):
        """Test extracting valid concept map."""
        json_str = '{"nodes": ["A", "B", "C"], "edges": [["A", "B", "connects"]]}'
        result = extract_concept_map_json(json_str)
        assert len(result["nodes"]) == 3
        assert len(result["edges"]) == 1
    
    def test_missing_edges(self):
        """Test handling missing edges."""
        json_str = '{"nodes": ["A", "B"]}'
        result = extract_concept_map_json(json_str)
        assert result["nodes"] == ["A", "B"]
        assert result["edges"] == []
    
    def test_empty_input(self):
        """Test empty input returns empty structure."""
        result = extract_concept_map_json('')
        assert result == {"nodes": [], "edges": []}
