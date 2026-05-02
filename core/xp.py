from data.db import add_xp

ACTION_POINTS = {
    "import_note": 10,
    "generate_summary": 15,
    "generate_quiz": 15,
    "complete_quiz": 20,
    "generate_flashcards": 10,
    "ask_chat": 5
}

def award(action: str):
    add_xp(ACTION_POINTS.get(action, 1))