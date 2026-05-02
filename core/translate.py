from core.llm import get_provider

def translate_text(text: str, target_lang: str) -> str:
    return get_provider().translate(text, target_lang)