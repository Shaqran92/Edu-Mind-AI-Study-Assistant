# tests/unit/test_text_chunker.py
"""
Unit tests for the text chunker utilities.
"""

import pytest
from utils.text_chunker import chunk_text, estimate_tokens, ChunkConfig


class TestChunkText:
    """Tests for the chunk_text function."""
    
    def test_short_text_single_chunk(self):
        """Short text should return single chunk."""
        text = "This is a short text."
        chunks = chunk_text(text, max_chars=100)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_empty_text(self):
        """Empty text should return empty list."""
        chunks = chunk_text("", max_chars=100)
        assert chunks == []
    
    def test_whitespace_text(self):
        """Whitespace-only text should return empty list."""
        chunks = chunk_text("   \n\n  ", max_chars=100)
        assert chunks == []
    
    def test_long_text_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        text = "This is a sentence. " * 50  # ~1000 chars
        chunks = chunk_text(text, max_chars=200)
        assert len(chunks) > 1
        assert all(len(c) <= 250 for c in chunks)  # Allow some flexibility
    
    def test_respects_sentence_boundaries(self):
        """Chunks should end at sentence boundaries when possible."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_text(text, max_chars=40)
        # Chunks should end with complete sentences
        for chunk in chunks:
            assert chunk.endswith('.') or chunk == chunks[-1]
    
    def test_respects_paragraph_boundaries(self):
        """Chunks should prefer paragraph breaks."""
        text = "Paragraph one with content.\n\nParagraph two with content.\n\nParagraph three."
        chunks = chunk_text(text, max_chars=50)
        # Should split at paragraph breaks
        assert len(chunks) >= 2
    
    def test_handles_no_natural_breaks(self):
        """Should handle text without natural breaks."""
        text = "word " * 100  # No sentences
        chunks = chunk_text(text, max_chars=50)
        assert len(chunks) > 1
    
    def test_custom_config(self):
        """Should respect custom configuration."""
        config = ChunkConfig(max_chars=100, min_chunk_ratio=0.3)
        text = "This is text. " * 20
        chunks = chunk_text(text, config=config)
        assert len(chunks) > 1


class TestEstimateTokens:
    """Tests for the estimate_tokens function."""
    
    def test_empty_text(self):
        """Empty text should have ~0 tokens."""
        assert estimate_tokens("") == 0
    
    def test_short_text(self):
        """Short text token estimation."""
        text = "Hello world"
        tokens = estimate_tokens(text)
        assert 2 <= tokens <= 5  # Roughly 2-3 tokens
    
    def test_longer_text(self):
        """Longer text token estimation."""
        text = "This is a longer piece of text that contains multiple sentences. " * 10
        tokens = estimate_tokens(text)
        # ~600 chars, ~100 words, estimate ~150-200 tokens
        assert 100 <= tokens <= 300
