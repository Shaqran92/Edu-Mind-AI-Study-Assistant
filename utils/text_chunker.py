# utils/text_chunker.py
"""
Text chunking utilities for processing large documents.
Implements intelligent splitting with natural break detection.
"""

import re
from typing import List, Optional
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger("text_chunker")


@dataclass
class ChunkConfig:
    """Configuration for text chunking behavior."""
    max_chars: int = 1800
    min_chunk_ratio: float = 0.5  # Minimum chunk size as ratio of max
    overlap_chars: int = 100  # Character overlap between chunks
    preserve_sentences: bool = True
    preserve_paragraphs: bool = True


def chunk_text(
    text: str,
    max_chars: int = 1800,
    config: Optional[ChunkConfig] = None
) -> List[str]:
    """
    Split a long text into smaller chunks suitable for LLM processing.
    
    Uses intelligent splitting that respects natural boundaries:
    1. Paragraph breaks (\\n\\n)
    2. Sentence endings (. ! ?)
    3. Clause boundaries (, ; :)
    
    Args:
        text: The text to split
        max_chars: Maximum characters per chunk
        config: Optional configuration object
    
    Returns:
        List of text chunks
    
    Example:
        >>> text = "Long document..." * 1000
        >>> chunks = chunk_text(text, max_chars=2000)
        >>> all(len(c) <= 2000 for c in chunks)
        True
    """
    if config is None:
        config = ChunkConfig(max_chars=max_chars)
    
    if not text:
        logger.warning("Empty text provided for chunking")
        return []
    
    text = text.strip()
    
    # Check again after stripping
    if not text:
        logger.warning("Only whitespace provided for chunking")
        return []
    
    # If text fits in one chunk, return it
    if len(text) <= config.max_chars:
        logger.debug(f"Text fits in single chunk ({len(text)} chars)")
        return [text]
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        # Calculate end position
        end_pos = min(current_pos + config.max_chars, len(text))
        
        # If we're not at the end, find a good break point
        if end_pos < len(text):
            break_pos = _find_break_point(
                text, 
                current_pos, 
                end_pos,
                config
            )
            if break_pos > current_pos:
                end_pos = break_pos
        
        # Extract chunk
        chunk = text[current_pos:end_pos].strip()
        
        if chunk:
            chunks.append(chunk)
            logger.debug(f"Created chunk {len(chunks)}: {len(chunk)} chars")
        
        # Move to next position (with optional overlap)
        if config.overlap_chars > 0 and end_pos < len(text):
            current_pos = max(end_pos - config.overlap_chars, current_pos + 1)
        else:
            current_pos = end_pos
    
    logger.info(f"Split text into {len(chunks)} chunks (avg: {sum(len(c) for c in chunks) // len(chunks)} chars)")
    return chunks


def _find_break_point(
    text: str,
    start: int,
    end: int,
    config: ChunkConfig
) -> int:
    """
    Find the best break point within the given range.
    Prioritizes natural boundaries.
    """
    min_pos = start + int((end - start) * config.min_chunk_ratio)
    search_text = text[start:end]
    
    # Priority 1: Paragraph break
    if config.preserve_paragraphs:
        break_pos = search_text.rfind('\n\n')
        if break_pos != -1 and start + break_pos >= min_pos:
            return start + break_pos + 2  # Include the newlines
    
    # Priority 2: Single line break
    break_pos = search_text.rfind('\n')
    if break_pos != -1 and start + break_pos >= min_pos:
        return start + break_pos + 1
    
    # Priority 3: Sentence ending
    if config.preserve_sentences:
        # Look for sentence endings followed by space
        for pattern in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
            break_pos = search_text.rfind(pattern)
            if break_pos != -1 and start + break_pos >= min_pos:
                return start + break_pos + len(pattern)
    
    # Priority 4: Clause boundaries
    for pattern in ['; ', ': ', ', ']:
        break_pos = search_text.rfind(pattern)
        if break_pos != -1 and start + break_pos >= min_pos:
            return start + break_pos + len(pattern)
    
    # Priority 5: Word boundary (space)
    break_pos = search_text.rfind(' ')
    if break_pos != -1 and start + break_pos >= min_pos:
        return start + break_pos + 1
    
    # Fallback: hard break at end position
    return end


def chunk_by_sections(
    text: str,
    section_pattern: str = r'^#{1,3}\s+',
    max_chars: int = 3000
) -> List[str]:
    """
    Split text by markdown-style section headers.
    
    Args:
        text: Text with markdown headers
        section_pattern: Regex pattern for section headers
        max_chars: Maximum chars per section
    
    Returns:
        List of sections (may be further chunked if too large)
    """
    # Split by headers
    sections = re.split(f'({section_pattern}.*)', text, flags=re.MULTILINE)
    
    # Recombine headers with content
    combined = []
    current = ""
    
    for part in sections:
        if re.match(section_pattern, part):
            if current.strip():
                combined.append(current.strip())
            current = part
        else:
            current += part
    
    if current.strip():
        combined.append(current.strip())
    
    # Further chunk large sections
    result = []
    for section in combined:
        if len(section) <= max_chars:
            result.append(section)
        else:
            result.extend(chunk_text(section, max_chars))
    
    logger.info(f"Split into {len(result)} sections")
    return result


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.
    Uses approximate ratio of 4 characters per token.
    
    Args:
        text: Text to estimate tokens for
    
    Returns:
        Estimated token count
    """
    # Simple estimation: ~4 chars per token for English
    # This is a rough approximation
    chars = len(text)
    words = len(text.split())
    
    # Use average of char-based and word-based estimates
    char_estimate = chars / 4
    word_estimate = words * 1.3  # Words tend to be ~1.3 tokens on average
    
    return int((char_estimate + word_estimate) / 2)


if __name__ == "__main__":
    # Test chunking
    test_text = """
    # Chapter 1: Introduction
    
    This is the first paragraph of the introduction. It contains some important information 
    that readers should understand before proceeding.
    
    The second paragraph builds on the first, adding more context and detail.
    
    ## Section 1.1: Background
    
    Here we provide historical context. The field has evolved significantly over the past 
    decade, with major breakthroughs in 2015, 2018, and 2021.
    
    Key milestones include:
    - First major discovery
    - Second breakthrough
    - Third advancement
    
    ## Section 1.2: Methodology
    
    Our approach combines traditional methods with modern techniques. We analyzed data 
    from multiple sources and applied rigorous statistical tests.
    """ * 10  # Make it longer
    
    print(f"Original length: {len(test_text)} chars")
    
    chunks = chunk_text(test_text, max_chars=500)
    print(f"\nChunked into {len(chunks)} parts:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i+1} ({len(chunk)} chars) ---")
        print(chunk[:200] + "...")
    
    print(f"\nEstimated tokens: {estimate_tokens(test_text)}")
