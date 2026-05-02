# core/summary.py
from typing import Dict, Any
from core.llm import get_provider, OfflineProvider

def generate_full_study_package(text: str, mode: str, length: str, language: str) -> Dict[str, Any]:
    """
    Generates a complete study package (summary, key points, flashcards) by
    calling the configured AI provider and gracefully falling back if needed.
    This function now returns a dictionary.
    """
    if not text or not text.strip():
        print("⚠️ Warning: Content for generation is empty.")
        return {"summary": "No content provided.", "key_points": [], "flashcards": []}
        
    print(f"-> Starting full study package generation...")
    print(f"   - Desired Mode: {mode}, Length: {length}, Language: {language}")

    provider = get_provider()
    
    try:
        # --- THIS IS THE FIX ---
        # The provider.summarize method now returns a single dictionary object.
        study_package = provider.summarize(text, mode, length, language)
        
        # We no longer need to unpack it into two variables.
        # We just validate that the dictionary is valid.
        if not study_package or not study_package.get("summary"):
            raise ValueError("AI returned an empty or invalid study package.")
            
        print("   - ✅ Successfully generated study package using AI.")
        return study_package

    except Exception as e:
        print(f"   - ❌ An error occurred during AI processing: {e}. Falling back.")
        # The OfflineProvider also returns a dictionary, so the return type is consistent.
        offline_provider = OfflineProvider()
        return offline_provider.summarize(text, mode, length, language)