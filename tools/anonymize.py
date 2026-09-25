import re

URL_START = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
MOBILE = re.compile(r"(?<!\d)(\+?977-?)?9[678]\d{8}(?!\d)")
LANDLINE = re.compile(r"(?<!\d)0\d{1,2}-?\d{6,7}(?!\d)")
LONG_NUMBER = re.compile(r"\b\d{9,}\b")

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