import csv
import re
from datetime import date
from pathlib import Path
from anonymize import anonymize

ROOT = Path(__file__).parent.parent
INBOX = ROOT / "data" / "raw" / "inbox.txt"
DATASET = ROOT / "data" / "dataset.csv"
FIELDS = ["id", "text", "label", "category", "language", "source", "date_added"]
CATEGORIES = {
    "scam": ["prize", "bank_wallet", "otp_request", "job", "loan", "delivery", "impersonation", "other"],
    "legit": ["otp", "transaction_alert", "promotion", "personal", "service", "other"],
}
LANGUAGES = ["en", "ne", "roman", "mixed"]
SOURCES = ["sms", "viber", "whatsapp", "messenger", "email", "other"]

def choose(question, options):
    for number, option in enumerate(options, start=1):
        print(f"  {number}. {option}")
    while True:
        answer = input(question + " ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print("  Please type one of the numbers above.")

def load_dataset():
    if not DATASET.exists():
        return []
    with open(DATASET, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def append_row(row):
    is_new_file = not DATASET.exists()
    with open(DATASET, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new_file:
            writer.writeheader()
        writer.writerow(row)

def main():
    rows = load_dataset()
    known = {row["text"] for row in rows}
    raw = INBOX.read_text(encoding="utf-8") if INBOX.exists() else ""
    messages = [m.strip() for m in re.split(r"^\s*---\s*$", raw, flags=re.MULTILINE) if m.strip()]
    skipped = []

    for message in messages:
        text = anonymize(message)
        print("\n" + "=" * 60 + "\n" + text + "\n" + "=" * 60)
        if text in known:
            print("Already in the dataset, skipping.")
            continue
        answer = input("Keep it? No names or private details left? (y/n) ").strip().lower()
        if answer != "y":
            print("Kept in the inbox. Edit it there and run again.")
            skipped.append(message)
            continue
        label = choose("Label?", ["scam", "legit"])
        row = {
            "id": len(rows) + 1,
            "text": text,
            "label": label,
            "category": choose("Category?", CATEGORIES[label]),
            "language": choose("Language?", LANGUAGES),
            "source": choose("Source?", SOURCES),
            "date_added": date.today().isoformat(),
        }
        append_row(row)
        rows.append(row)
        known.add(text)

    INBOX.write_text("\n---\n".join(skipped), encoding="utf-8")
    print(f"\nDone. The dataset now has {len(rows)} messages.")

if __name__ == "__main__":
    main()