import json
import random
from pathlib import Path

LESSONS_PATH = Path(__file__).parent.parent / "rules" / "lessons.json"

with open(LESSONS_PATH, encoding="utf-8") as f:
    DATA = json.load(f)

def get_lessons(language):
    """Return lessons localized to `language`. For each lesson, a random quiz
    is chosen from its pool and its options are shuffled (with the answer index
    remapped), so questions and answer positions vary on every request."""
    out = []
    for lesson in DATA["lessons"]:
        quiz = random.choice(lesson["quizzes"])
        options = list(enumerate(quiz["options"][language]))  # (original_index, text)
        random.shuffle(options)
        shuffled = [text for _, text in options]
        new_answer = next(i for i, (orig, _) in enumerate(options)
                          if orig == quiz["answer"])
        out.append({
            "id": lesson["id"],
            "title": lesson["title"][language],
            "body": lesson["body"][language],
            "quiz": {
                "question": quiz["question"][language],
                "options": shuffled,
                "answer": new_answer,
                "explain": quiz["explain"][language],
            },
        })
    return out