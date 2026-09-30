import re

URL_START = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# digits in BOTH scripts: ASCII 0-9 and Devanagari ० (U+0966) .. ९ (U+096F)
D = r"[0-9०-९]"
NINE = r"[9९]"          # 9 or ९
ZERO = r"[0०]"          # 0 or ०

# Nepali mobile: optional +977 / ९७७, then 10 digits starting 9/९
MOBILE = re.compile(rf"(?<!{D})(?:\+?(?:977|३७७)[- ]?)?{NINE}{D}{{9}}(?!{D})")
# Landline: 0/० + 1-2 digits + optional dash + 6-7 digits
LANDLINE = re.compile(rf"(?<!{D}){ZERO}{D}{{1,2}}-?{D}{{6,7}}(?!{D})")
# Any remaining long number (accounts, cards): 9+ digits
LONG_NUMBER = re.compile(rf"(?<!{D}){D}{{9,}}(?!{D})")

def clean_url(token):
    parts = re.split(r"[?#]", token, maxsplit=1)
    token = parts[0] + "?[REMOVED]" if len(parts) > 1 else token
    return MOBILE.sub("[PHONE]", token)

def clean_text(token):
    token = EMAIL.sub("[EMAIL]", token)
    token = MOBILE.sub("[PHONE]", token)
    token = LANDLINE.sub("[PHONE]", token)
    return LONG_NUMBER.sub("[NUMBER]", token)

def anonymize(text):
    parts = re.split(r"(\s+)", text.strip())
    return "".join(clean_url(p) if URL_START.match(p) else clean_text(p) for p in parts)