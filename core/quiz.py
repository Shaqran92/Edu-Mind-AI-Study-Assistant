from typing import List, Dict, Any
from core.llm import get_provider

def generate_quiz(summary_text: str) -> List[Dict[str, Any]]:
    return get_provider().quiz(summary_text)

def grade_quiz(quiz: List[Dict[str, Any]], answers: List[str]):
    correct = 0
    details = []
    for i, q in enumerate(quiz):
        user = answers[i] if i < len(answers) else ""
        ok = (user.strip().upper() == q.get("answer","").strip().upper())
        correct += int(ok)
        details.append({"q": q.get("question",""), "correct": ok, "your": user, "answer": q.get("answer",""), "explanation": q.get("explanation","")})
    score = int(100 * correct / max(1,len(quiz)))
    return score, details