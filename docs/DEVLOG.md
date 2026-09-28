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


  
---

## 2026-09-26 to 2026-09-28 — v0.2: Machine-learning scam classifier and hybrid model

### Goal
Add a machine-learning scam/legit classifier, evaluate it honestly against the rule-based baseline on real held-out data, and answer RQ2 (can a localised system accurately detect Nepali scam/phishing messages?).

### Work completed
- Built a privacy-safe dataset pipeline: a collection tool, an anonymiser, a dataset validator (`check_dataset.py`), and a repair tool (`repair_dataset.py`).
- Assembled a training set of 397 collected messages (labelling assisted by AI) and an independent test set of 90 raw, unedited messages (30 scam, 60 legit).
- Trained a TF-IDF (character n-gram) + logistic-regression classifier with scikit-learn.
- Built an honest evaluation: trained on the AI-assisted set, tested on the raw set, with automatic removal of training rows overlapping the test set.
- Compared three systems on the same 90 raw messages: rule-based, ML, and a hybrid (ML for recall + a rule-based legit-override for precision).

### Results (scam class, on 90 raw held-out messages)

| System | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|
| Rule-based | 1.00 | 0.37 | 0.54 | 0.79 |
| ML (TF-IDF char n-grams + LogReg) | 0.86 | 1.00 | 0.92 | 0.94 |
| Hybrid (ML + rule-based override) | 0.97 | 1.00 | 0.98 | 0.99 |

**Finding:** the rule-based and ML approaches have complementary strengths.
Rules are precise (they assess domain legitimacy) but low-recall (they only fire on predefined patterns, missing subtle social-engineering scams). ML has
high recall (it generalises from language) but lower precision (it treats any link as suspicious). The hybrid combines both and outperforms either alone.

### Problems encountered and solutions

| Problem | Cause | Solution | Lesson |
|---|---|---|---|
| Dataset rows misaligned; text fragments appeared as labels | Message text containing commas (e.g. `Rs 1,000`) was not quoted in the CSV | Repair tool reconstructs each row from the known trailing fields and re-quotes properly | CSV integrity: any field with a comma must be quoted |
| Real phone numbers in Devanagari digits were not anonymised | Anonymiser matched only ASCII digits; the phone pattern anchored on ASCII `9` | Extended anonymiser to Devanagari digits (U+0966–U+096F); added tests | A privacy filter must cover every script in the data |
| First model scored 100% accuracy | Evaluation tested on the same AI-assisted distribution it trained on | Built a held-out test set of raw messages; measured on that instead | A perfect score is a warning sign, not a success |
| Concern the model learned dataset "style" rather than scam features | Training text had been rewritten by AI, risking style homogenisation | External-probe test (16 hand-written messages) confirmed the model generalises | Validate generalisation on out-of-distribution examples |
| Hybrid still flagged one legit "QR payment" message | Override blocked because "payment" contains the substring "pay" | Left uncorrected on purpose; documented as future work (word-boundary fix) | Do not tune to fix visible test-set errors — that overfits the test set |

### Key design decisions
1. **AI-assisted labelling, with a raw held-out test set.** Labelling 400
   messages by hand was impractical, so AI assisted; but all headline results are measured on raw, unedited messages the model never saw, to keep the
   evaluation authentic.
2. **Character n-gram features.** Chosen over word      features to handle Romanized Nepali spelling variation and mixed scripts without a Nepali dictionary.
3. **Leakage removal before evaluation.** Training rows highly similar to any test message are dropped, so the test set measures generalisation, not memory.
4. **Hybrid = ML recall + rule-based precision.** ML detects scams broadly; the rule engine's domain check suppresses false positives on legitimate messages containing official-domain links.
5. **No further tuning to the test set.** The single remaining false positive is reported honestly rather than engineered away.

### Evidence
- Rule/ML/hybrid comparison reproducible via `ai/compare.py` and `ai/hybrid_eval.py`.
- Dataset passes `check_dataset.py` (balance, valid labels, no privacy leaks).

### Known limitations
- Test set is small (90 messages, 30 scam); each scam miss shifts recall by ~3%.
- Training text was AI-rewritten, which may homogenise style; only the raw test set is fully authentic.
- Labels assigned with AI assistance; a human spot-check of a labelled sample is still to be done and reported.
- The hybrid's official-domain whitelist must be verified against official sources and is not exhaustive.
- Single annotator; no inter-annotator agreement measured