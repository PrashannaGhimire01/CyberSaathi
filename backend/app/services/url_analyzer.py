import ipaddress
import json
from pathlib import Path
from urllib.parse import urlparse

RULES_PATH = Path(__file__).parent.parent / "rules" / "url_rules.json"
TRAILING_JUNK = ".,!?;:)\"'"

with open(RULES_PATH, encoding="utf-8") as f:
    RULES = json.load(f)

def make_signal(name, matched, brand=None):
    rule = RULES[name]
    reasons = {"en": rule["reason_en"], "ne": rule["reason_ne"]}
    if brand:
        reasons = {lang: text.format(brand=brand) for lang, text in reasons.items()}
    return {"signal": name, "weight": rule["weight"], "reasons": reasons, "matched": matched}

def is_ip_address(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False

def is_official(host, official_domains):
    return any(host == d or host.endswith("." + d) for d in official_domains)

def analyze_url(raw_url):
    url = raw_url.strip().rstrip(TRAILING_JUNK)
    has_scheme = url.lower().startswith(("http://", "https://"))
    try:
        parsed = urlparse(url if has_scheme else "http://" + url)
        host = parsed.hostname or ""
    except ValueError:
        return [make_signal("malformed", [raw_url])]
    if not host or any(ch.isspace() for ch in url):
        return [make_signal("malformed", [raw_url])]
       
    signals = []
    if url.lower().startswith("http://"):
        signals.append(make_signal("no_https", [url]))
    if "@" in parsed.netloc:
        signals.append(make_signal("at_symbol", [url]))
    if is_ip_address(host):
        signals.append(make_signal("ip_address", [host]))
    if "xn--" in host:
        signals.append(make_signal("punycode", [host]))
    tld = host.rsplit(".", 1)[-1]
    if tld in RULES["suspicious_tld"]["values"]:
        signals.append(make_signal("suspicious_tld", [tld]))
    if host in RULES["shortener"]["values"]:
        signals.append(make_signal("shortener", [host]))

    brand_rule = RULES["brand_impersonation"]
    for brand, official in brand_rule["values"].items():
        if brand in host and not is_official(host, official):
            signals.append(make_signal("brand_impersonation", [host], brand=brand))
    return signals