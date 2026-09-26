import csv
import re
import sys
from pathlib import Path

LABELS = {"scam", "legit"}
# Accept a single unified category vocabulary for BOTH labels (used only to
# locate column boundaries during repair; the checker judges label/category fit).
ALL_CATEGORIES = {
    "prize", "bank_wallet", "otp_request", "job", "loan", "delivery",
    "impersonation", "other", "otp", "transaction_alert", "promotion",
    "personal", "service",
}
LANGUAGES = {"en", "ne", "roman", "mixed"}
SOURCES = {"sms", "viber", "whatsapp", "messenger", "email", "other"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FIELDS = ["id", "text", "label", "category", "language", "source", "date_added"]

D = r"[0-9०-९]"  # ASCII + Devanagari digits
PHONE = re.compile(rf"(?<!{D})(?:\+?(?:977|३७७)[- ]?)?[9९]{D}{{9}}(?!{D})")
LONG_NUMBER = re.compile(rf"(?<!{D}){D}{{9,}}(?!{D})")

def anonymize(text):
    text = PHONE.sub("[PHONE]", text)
    text = LONG_NUMBER.sub("[NUMBER]", text)
    return text

def valid_tail(fields):
    if len(fields) < 7:
        return False
    label, category, language, source, date = fields[-5:]
    return (label in LABELS and category in ALL_CATEGORIES
            and language in LANGUAGES and source in SOURCES and bool(DATE.match(date)))

def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/dataset.csv")
    out = src.with_name("dataset_clean.csv")
    review = src.with_name("dataset_needs_review.csv")

    with open(src, encoding="utf-8", newline="") as f:
        raw_rows = list(csv.reader(f))

    clean, needs_review = [], []
    for fields in raw_rows[1:]:
        if not any(f.strip() for f in fields):
            continue
        if len(fields) == 7 and valid_tail(fields):
            row = list(fields)
        elif len(fields) > 7 and valid_tail(fields):
            row = [fields[0], ",".join(fields[1:-5])] + list(fields[-5:])
        else:
            needs_review.append(fields)
            continue
        row[1] = anonymize(row[1])
        clean.append(row)

    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerows(clean)
    if needs_review:
        with open(review, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(needs_review)

    print(f"Repaired rows written: {len(clean)}  ->  {out.name}")
    print(f"Rows needing manual review: {len(needs_review)}" +
          (f"  ->  {review.name}" if needs_review else ""))

if __name__ == "__main__":
    main()