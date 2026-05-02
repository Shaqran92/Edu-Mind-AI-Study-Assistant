# core/youtube.py
"""
YouTube integration for EduMind.
Fetches transcripts from YouTube videos for summarization.
Supports multiple fallback strategies for transcript retrieval.
"""

import re
from typing import Optional, List, Dict
from urllib.parse import urlparse, parse_qs

from utils.logger import get_logger

logger = get_logger("youtube")

HAS_YOUTUBE_API = False
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YOUTUBE_API = True
except ImportError:
    logger.warning("youtube_transcript_api not installed. YouTube features limited.")

class YouTubeService:
    """Service for handling YouTube content."""
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        try:
            # Handle direct video IDs (11 chars)
            url = url.strip()
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                return url
            
            parsed = urlparse(url)
            if parsed.hostname == 'youtu.be':
                return parsed.path[1:]
            if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
                if parsed.path == '/watch':
                    return parse_qs(parsed.query).get('v', [None])[0]
                if parsed.path.startswith('/embed/'):
                    return parsed.path.split('/')[2]
                if parsed.path.startswith('/v/'):
                    return parsed.path.split('/')[2]
                if parsed.path.startswith('/shorts/'):
                    return parsed.path.split('/')[2]
            return None
        except Exception:
            return None

    @staticmethod
    def get_transcript(video_id: str) -> Optional[str]:
        """
        Fetch transcript for a video with multiple fallback strategies.
        Handles both old and new versions of youtube_transcript_api.
        Returns the full text of the transcript.
        """
        if not HAS_YOUTUBE_API:
            raise ImportError("youtube_transcript_api module is required. Please install it: pip install youtube-transcript-api")

        # ─── Strategy 1: Try new API format (v0.6.3+) ───
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.fetch(video_id)
            # New API returns a FetchedTranscript object
            if hasattr(transcript_list, 'snippets'):
                full_text = " ".join([item.text for item in transcript_list.snippets])
            else:
                # Try treating as iterable of dicts
                full_text = " ".join([item.get('text', '') if isinstance(item, dict) else str(getattr(item, 'text', item)) for item in transcript_list])
            if full_text.strip():
                return full_text.strip()
        except Exception as e1:
            logger.debug(f"New API format failed: {e1}")

        # ─── Strategy 2: Try old API format (pre-0.6.3) ───
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([item['text'] for item in transcript_list])
            if full_text.strip():
                return full_text.strip()
        except Exception as e2:
            logger.debug(f"Old API format failed: {e2}")

        # ─── Strategy 3: Try with language fallbacks ───
        languages_to_try = ['en', 'en-US', 'en-GB', 'auto']
        for lang in languages_to_try:
            try:
                # New API
                ytt_api = YouTubeTranscriptApi()
                transcript_list = ytt_api.fetch(video_id, languages=[lang])
                if hasattr(transcript_list, 'snippets'):
                    full_text = " ".join([item.text for item in transcript_list.snippets])
                else:
                    full_text = " ".join([item.get('text', '') if isinstance(item, dict) else str(getattr(item, 'text', item)) for item in transcript_list])
                if full_text.strip():
                    return full_text.strip()
            except Exception:
                pass
            
            try:
                # Old API
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                full_text = " ".join([item['text'] for item in transcript_list])
                if full_text.strip():
                    return full_text.strip()
            except Exception:
                pass

        # ─── Strategy 4: List available transcripts and pick the first one ───
        try:
            # New API
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)
            # Try fetching any available transcript
            for t in transcript_list:
                try:
                    fetched = t.fetch()
                    if hasattr(fetched, 'snippets'):
                        full_text = " ".join([item.text for item in fetched.snippets])
                    else:
                        full_text = " ".join([item.get('text', '') if isinstance(item, dict) else str(getattr(item, 'text', item)) for item in fetched])
                    if full_text.strip():
                        return full_text.strip()
                except Exception:
                    continue
        except Exception as e4:
            logger.debug(f"List transcripts failed: {e4}")

        try:
            # Old API: list_transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            for t in transcript_list:
                try:
                    fetched = t.fetch()
                    full_text = " ".join([item['text'] for item in fetched])
                    if full_text.strip():
                        return full_text.strip()
                except Exception:
                    continue
        except Exception as e5:
            logger.debug(f"Old list_transcripts failed: {e5}")

        logger.error(f"All transcript strategies failed for video: {video_id}")
        return None

    @staticmethod
    def get_video_info(video_id: str) -> Dict[str, str]:
        """
        Get basic video info (thumbnail, title placeholder).
        """
        return {
            "id": video_id,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
            "url": f"https://www.youtube.com/watch?v={video_id}"
        }
