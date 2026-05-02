# core/voice_service.py
"""
Voice Interaction Service for EduMind.
Handles Text-to-Speech (TTS) and Speech-to-Text (STT).
"""

import threading
import queue
from typing import Optional, Callable
from utils.logger import get_logger

logger = get_logger("voice")

HAS_TTS = False
HAS_STT = False

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    logger.warning("pyttsx3 not installed. TTS disabled.")

try:
    import speech_recognition as sr
    HAS_STT = True
except ImportError:
    logger.warning("speech_recognition not installed. STT disabled.")

class VoiceService:
    """
    Handles voice input and output.
    """
    
    def __init__(self):
        self.tts_engine = None
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self._init_engine()

    def _init_engine(self):
        if HAS_TTS:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 170) # Slightly faster than default
            except Exception as e:
                logger.error(f"Failed to init TTS: {e}")
        
        if HAS_STT:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception as e:
                logger.error(f"Failed to init STT: {e}")

    def speak(self, text: str):
        """Speak text using TTS (non-blocking)."""
        if not self.tts_engine:
            return
            
        def _speak():
            try:
                # Re-init in thread if needed (pyttsx3 loop issue)
                # Ideally, we use the engine loop properly. 
                # For simplicity in PyQt, we just runAndWait in a thread.
                engine = pyttsx3.init() 
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS Error: {e}")

        threading.Thread(target=_speak, daemon=True).start()

    def start_listening(self, callback: Callable[[str], None], error_callback: Callable[[str], None]):
        """
        Start listening for one phrase.
        """
        if not self.recognizer or not self.microphone:
            error_callback("Microphone not available.")
            return

        def _listen():
            self.is_listening = True
            try:
                with self.microphone as source:
                    # noise adjustment
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    logger.info("Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                logger.info("Processing speech...")
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Heard: {text}")
                callback(text)
                
            except sr.WaitTimeoutError:
                error_callback("No speech detected.")
            except sr.UnknownValueError:
                error_callback("Could not understand audio.")
            except sr.RequestError as e:
                error_callback(f"Speech service error: {e}")
            except Exception as e:
                error_callback(str(e))
            finally:
                self.is_listening = False

        threading.Thread(target=_listen, daemon=True).start()

# Global Instance
_voice_service = None

def get_voice_service():
    global _voice_service
    if not _voice_service:
        _voice_service = VoiceService()
    return _voice_service
