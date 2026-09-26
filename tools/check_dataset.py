import csv
import re
import sys
from collections import Counter
from pathlib import Path

# --- what "valid" looks like (must match collect.py) ---
LABELS = {"scam", "legit"}
CATEGORIES = {
    "prize", "bank_wallet", "otp_request", "job", "loan", "delivery",
    "impersonation", "other", "otp", "transaction_alert", "promotion",
    "personal", "service",
}
LANGUAGES = {"en", "ne", "roman", "mixed"}
SOURCES = {"sms", "viber", "whatsapp", "messenger", "email", "other"}

# --- privacy leak patterns (things that should already be anonymized) ---
MOBILE = re.compile(r"(?<!\d)(\+?977-?)?9[678]\d{8}(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
LONG_NUMBER = re.compile(r"\b\d{9,}\b")

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/dataset.csv")
    if not path.exists():
        print(f"File not found: {path}")
        return
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"=== {path} ===")
    print(f"Total rows: {len(rows)}\n")

    problems = 0

    # 1. Balance
    labels = Counter(r["label"] for r in rows)
    print("By label:", dict(labels))

    # 2. Distributions
    print("By language:", dict(Counter(r["language"] for r in rows)))
    print("By source:  ", dict(Counter(r["source"] for r in rows)))
    print("By category:", dict(Counter(r["category"] for r in rows)))
    print("Scam by language: ", dict(Counter(r["language"] for r in rows if r["label"] == "scam")))
    print("Legit by language:", dict(Counter(r["language"] for r in rows if r["label"] == "legit")))
    print()

    # 3. Invalid values
    for i, r in enumerate(rows, start=2):  # row 2 = first data row (after header)
        if r["label"] not in LABELS:
            print(f"  [row {i}] bad label: {r['label']!r}"); problems += 1
        elif r["category"] not in CATEGORIES:
            print(f"  [row {i}] category {r['category']!r} not valid for label {r['label']!r}"); problems += 1
        if r["language"] not in LANGUAGES:
            print(f"  [row {i}] bad language: {r['language']!r}"); problems += 1
        if r["source"] not in SOURCES:
            print(f"  [row {i}] bad source: {r['source']!r}"); problems += 1
        if not r["text"].strip():
            print(f"  [row {i}] empty text"); problems += 1

    # 4. Duplicates
    texts = [r["text"].strip() for r in rows]
    dupes = [t for t, n in Counter(texts).items() if n > 1]
    if dupes:
        print(f"\n  {len(dupes)} duplicate message(s):")
        for d in dupes[:10]:
            print(f"    x{texts.count(d)}: {d[:70]}")
        problems += len(dupes)

    # 5. Privacy leaks
    print("\n--- privacy scan (these should already be replaced) ---")
    leaks = 0
    for i, r in enumerate(rows, start=2):
        t = r["text"]
        found = []
        if MOBILE.search(t): found.append("phone")
        if EMAIL.search(t): found.append("email")
        if LONG_NUMBER.search(t): found.append("long-number")
        if found:
            leaks += 1
            print(f"  [row {i}] possible {', '.join(found)}: {t[:70]}")
    if not leaks:
        print("  None found. Good.")
    problems += leaks

    # 6. Verdict
    print("\n" + "=" * 50)
    if problems == 0:
        print("PASSED. Dataset looks clean and ready.")
    else:
        print(f"{problems} issue(s) to review above before training.")

if __name__ == "__main__":
    main()