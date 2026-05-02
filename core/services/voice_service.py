# core/services/voice_service.py
"""
Voice services for text-to-speech and speech recognition.
"""

import threading
from typing import Optional, Callable
from queue import Queue

from utils.logger import get_logger

logger = get_logger("voice_service")

# Optional imports
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not installed - text-to-speech unavailable")


class TextToSpeechService:
    """
    Text-to-speech service using pyttsx3.
    
    Features:
    - Asynchronous speech
    - Speed and volume control
    - Voice selection
    - Queue management
    
    Example:
        >>> tts = TextToSpeechService()
        >>> tts.speak("Hello, world!")
        >>> tts.speak_async("This runs in background")
    """
    
    def __init__(self):
        self._engine = None
        self._is_speaking = False
        self._speech_queue: Queue = Queue()
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = False
        
        if TTS_AVAILABLE:
            try:
                self._engine = pyttsx3.init()
                self._configure_defaults()
                logger.info("Text-to-speech service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize TTS: {e}")
                self._engine = None
    
    def _configure_defaults(self):
        """Configure default TTS settings."""
        if not self._engine:
            return
        
        # Set default rate (words per minute)
        self._engine.setProperty('rate', 175)
        
        # Set default volume (0.0 to 1.0)
        self._engine.setProperty('volume', 0.9)
    
    @property
    def is_available(self) -> bool:
        return self._engine is not None
    
    @property
    def is_speaking(self) -> bool:
        return self._is_speaking
    
    def get_voices(self) -> list:
        """Get available voices."""
        if not self._engine:
            return []
        
        voices = self._engine.getProperty('voices')
        return [{
            'id': v.id,
            'name': v.name,
            'languages': v.languages
        } for v in voices]
    
    def set_voice(self, voice_id: str):
        """Set the voice by ID."""
        if self._engine:
            self._engine.setProperty('voice', voice_id)
            logger.debug(f"Voice set to: {voice_id}")
    
    def set_rate(self, rate: int):
        """Set speaking rate (words per minute). Default is ~175."""
        if self._engine:
            rate = max(50, min(400, rate))  # Clamp to reasonable range
            self._engine.setProperty('rate', rate)
            logger.debug(f"Rate set to: {rate}")
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        if self._engine:
            volume = max(0.0, min(1.0, volume))
            self._engine.setProperty('volume', volume)
            logger.debug(f"Volume set to: {volume}")
    
    def speak(self, text: str, wait: bool = True):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            wait: Whether to wait for speech to complete
        """
        if not self._engine:
            logger.warning("TTS not available")
            return
        
        if not text.strip():
            return
        
        logger.debug(f"Speaking: {text[:50]}...")
        self._is_speaking = True
        
        try:
            self._engine.say(text)
            if wait:
                self._engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self._is_speaking = False
    
    def speak_async(self, text: str, on_complete: Optional[Callable] = None):
        """
        Speak text asynchronously in a background thread.
        
        Args:
            text: Text to speak
            on_complete: Optional callback when speech completes
        """
        if not self._engine:
            if on_complete:
                on_complete()
            return
        
        def _speak():
            self.speak(text, wait=True)
            if on_complete:
                on_complete()
        
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
    
    def queue_speech(self, text: str):
        """Add text to the speech queue."""
        self._speech_queue.put(text)
        
        # Start queue processor if not running
        if self._thread is None or not self._thread.is_alive():
            self._stop_flag = False
            self._thread = threading.Thread(target=self._process_queue, daemon=True)
            self._thread.start()
    
    def _process_queue(self):
        """Process queued speech items."""
        while not self._stop_flag:
            try:
                text = self._speech_queue.get(timeout=0.5)
                self.speak(text, wait=True)
                self._speech_queue.task_done()
            except:
                if self._speech_queue.empty():
                    break
    
    def stop(self):
        """Stop current speech and clear queue."""
        self._stop_flag = True
        
        if self._engine:
            try:
                self._engine.stop()
            except:
                pass
        
        # Clear queue
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
            except:
                break
        
        self._is_speaking = False
        logger.debug("Speech stopped")
    
    def speak_summary(self, summary: str, chunk_size: int = 500):
        """
        Speak a long summary in chunks.
        
        Args:
            summary: The summary text
            chunk_size: Maximum characters per chunk
        """
        if not summary:
            return
        
        # Split into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', summary)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size:
                if current_chunk:
                    self.queue_speech(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            self.queue_speech(current_chunk)


# Global instance
_tts: Optional[TextToSpeechService] = None

def get_tts() -> TextToSpeechService:
    """Get the global TTS service instance."""
    global _tts
    if _tts is None:
        _tts = TextToSpeechService()
    return _tts
