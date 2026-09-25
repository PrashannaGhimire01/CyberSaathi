# CyberSaathi — Development Log

This log records the development of CyberSaathi, an AI-assisted, offline-first
personal cybersecurity companion for non-technical users in Nepal. Each entry
documents the goal, work completed, problems encountered, design decisions,
evidence, known limitations and next steps.

---

## 2026-09-24 to 2026-09-25 — v0.1: Rule-based scam and link detector

### Goal
Build a working minimum viable product (MVP): a user submits a suspicious
message or link and receives a risk level, reasons and recommended actions in
English or Nepali, plus emergency guidance for users who have already been
scammed.

### Work completed
- Set up the development environment: Ubuntu on WSL2, Python virtual
  environment, Git with SSH authentication to a private GitHub repository.
- Built a FastAPI backend with three endpoints: `/analyze/message`,
  `/analyze/url` and `/emergency`.
- Implemented a rule-based message analyzer supporting English, Romanized
  Nepali and Nepali (Devanagari), with rules stored as JSON data.
- Implemented a static URL analyzer detecting brand impersonation, the "@"
  redirection trick, suspicious TLDs, URL shorteners, raw IP addresses,
  punycode and malformed links. Links are never visited.
- Implemented a risk engine that combines signals, avoids double-counting,
  and applies an evasion-resistant safety-advice discount.
- Built a bilingual explanation layer (headline, reasons, actions, disclaimer)
  using human-written templates.
- Built an emergency guide that produces urgency-ordered, de-duplicated steps
  based on what the user shared.
- Built a web interface (HTML, CSS, JavaScript) served by FastAPI.
- Wrote 26 automated tests with pytest.

### Architecture
Message/URL → Analyzers (evidence) → Risk engine (decision) →
Explanation layer (bilingual advice) → Web interface

### Problems encountered and solutions

| Problem | Cause | Solution | Lesson |
|---|---|---|---|
| Genuine eSewa OTP messages were flagged as MEDIUM risk (false positive) | Rule triggered on the word "OTP" alone | Credential requests now require a request word (e.g. "send", "pathaunuhos"); added a safety-advice signal | Mentioning a credential is different from requesting it |
| Attackers could add "do not share" to scams to lower the score (evasion) | Safety discount applied unconditionally | Discount applies only when no other warning signs are present | Design rules assuming attackers will adapt to them |
| Keywords matched inside unrelated words (e.g. "pin" in "shopping") | Simple substring matching | Word-boundary regex for Latin-script keywords | Naive matching creates false positives |
| Scam domains ending in an official name (e.g. `evil-esewa.com.np`) could pass as official | Suffix check without a leading dot | Check `host == domain` or `host.endswith("." + domain)` | One missing character can create a security bypass |
| A test passed while testing the wrong thing; a sentence was accepted as a valid URL | Test case placed in the wrong file; no validation of URL structure | Moved test; URLs with spaces or no host are now flagged as malformed | A passing test only proves what it actually checks; fail safe on unparseable input |
| `ModuleNotFoundError` when running tests | pytest run from the wrong directory, so `pytest.ini` was not loaded | Run tests from `backend/` | Compare broken output with working output to find the difference |
| `IndentationError` in `url_analyzer.py` | Inconsistent indentation after pasting code | Corrected to 4-space indentation; enabled whitespace rendering in VS Code | Read error messages from the last line upward |

### Key design decisions
1. **Rule-based baseline before machine learning.** No labelled dataset exists
   yet, rules are fully explainable, and they provide a baseline for later
   comparison with ML models.
2. **Rules and text stored as JSON, separate from code.** Allows updating
   detection rules without code changes, and prepares for offline use on the
   phone and signed rule updates.
3. **Detection separated from decision.** Analyzers only report evidence; the
   risk engine alone decides the risk level.
4. **Template-based explanations instead of an LLM.** Templates cannot invent
   false reasons, work offline, and can be reviewed by native speakers.
5. **"LOW" instead of "SAFE".** The system never claims a message is safe,
   because all detection has limitations.
6. **Static URL analysis only.** Visiting links could alert attackers, reveal
   the user's location, or expose the device to malicious content.
7. **Security enforced on the server.** Input validation (length limits,
   allowed values, link limits) is enforced in the backend; browser-side
   limits are for convenience only.
8. **Output rendered with `textContent`.** Prevents cross-site scripting
   (XSS) from attacker-controlled content.

### Evidence
- 26 automated tests passing (message detection, URL detection, explanations,
  emergency guide, input validation, rule data completeness, web interface).
- Git tag `v0.1` on commit `f1f3280`.

### Known limitations
- Keyword rules can be evaded by spelling variations (e.g. "0TP", "o.t.p").
- Rule weights and thresholds are based on judgement, not yet on data.
- Only a small number of test messages; no real-world evaluation yet.
- Brand impersonation covers only three brands.
- Explanations available in English and Nepali (Devanagari), not yet in
  Romanized Nepali.
- No rate limiting; the system runs locally only.

### Next steps
- Begin collecting and labelling a privacy-safe dataset of real scam and
  legitimate messages.
- v0.2: train a first machine-learning model and compare it with the
  rule-based baseline using precision, recall and false-positive rate.