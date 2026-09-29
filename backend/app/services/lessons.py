import json
from pathlib import Path

LESSONS_PATH = Path(__file__).parent.parent / "rules" / "lessons.json"

with open(LESSONS_PATH, encoding="utf-8") as f:
    DATA = json.load(f)

def get_lessons(language):
    """Return the lessons localized to one language (en or ne)."""
    out = []
    for lesson in DATA["lessons"]:
        quiz = lesson["quiz"]
        out.append({
            "id": lesson["id"],
            "title": lesson["title"][language],
            "body": lesson["body"][language],
            "quiz": {
                "question": quiz["question"][language],
                "options": quiz["options"][language],
                "answer": quiz["answer"],
                "explain": quiz["explain"][language],
            },
        })
    return out