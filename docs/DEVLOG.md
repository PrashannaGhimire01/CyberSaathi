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


---

## 2026-09-28 to 2026-09-29 — v0.3: Android app and hybrid backend integration

### Goal
Turn CyberSaathi into a working Android app on a real phone, backed by a
backend that serves the hybrid (rule-based + ML) detector, covering the four
pillars: protect, explain, educate and include (bilingual).

### Work completed
- Integrated the ML model and hybrid logic into the FastAPI backend
  (`ml_classifier.py`, `hybrid.py`); `/analyze/message` now returns the hybrid
  verdict with an ML-based reason when the model contributes. Falls back to
  rules alone if the model file is absent.
- Built a Flutter app and ran it on a physical Android phone (Realme, Android 9)
  over USB, with `adb reverse` bridging the phone to the WSL backend.
- App features: Check Message, Check Link, "I already clicked" emergency flow,
  and a Learn tab with bilingual lessons and quizzes — all wired to the backend
  endpoints, with a live Nepali/English toggle.
- Implemented Share-to-CyberSaathi via an Android platform channel (Kotlin
  `MainActivity` + intent-filter): sharing a message from another app opens
  CyberSaathi, fills the message, and auto-checks it.
- Added a `/lessons` endpoint serving localized lessons from JSON.
- Backed up the app to a separate GitHub repository (CyberSaathi-mobile).

### Architecture
Phone (Flutter) → adb reverse → FastAPI backend → hybrid engine
(rules + ML) → localized response → app UI. Backend and app are two repos:
CyberSaathi (brain) and CyberSaathi-mobile (face).

### Problems encountered and solutions

| Problem | Cause | Solution | Lesson |
|---|---|---|---|
| Android build failed: NDK 28.2.13676358 not found; `sdkmanager` crashed | Auto-installer for the NDK crashed on new SDK tooling | Installed the NDK manually via Android Studio SDK Manager | Pre-install native deps to avoid fragile auto-installers |
| `INSTALL_FAILED_VERIFICATION_FAILURE` on the phone | Play Protect / "verify apps over USB" blocking sideloads | Disabled "Verify apps over USB" and Play Protect scanning | Realme/ColorOS devices need install verification relaxed for dev |
| App installed but `adb` "device not found" mid-build | Phone slept and dropped USB during the build | Enabled "Stay awake" in Developer options | Keep the device awake during long builds |
| Server failed to start (`ModuleNotFoundError: app`) | uvicorn run from repo root, not `backend/` | Run the server from `backend/` | Working directory matters for imports |
| Android blocked the app's HTTP calls | Cleartext HTTP disabled by default | Added `usesCleartextTraffic="true"` for local development | Dev-only; production uses HTTPS |

### Key design decisions
1. **Complete the backend "brain" before the app UI.** The app calls a hybrid
   endpoint from its first screen instead of the weaker rule-only detector.
2. **Explainability preserved in the hybrid.** Rules produce the reasons; ML
   adds recall; an ML reason is shown when the model is the one that flagged.
3. **adb reverse for development.** The app targets `localhost:8000`, bridged to
   the WSL backend; a deployed backend will remove this dependency later.
4. **Backend-served lessons.** Education content lives in the backend (JSON), so
   it can be updated without rebuilding the app, and it prepares for offline sync.
5. **Native platform channel for Share.** Avoids external-package version risk
   and teaches Flutter↔Android communication directly.

### Known limitations
- Requires USB (or wireless adb) and a running local backend during development.
- Cleartext HTTP is enabled for local dev only.
- Lessons are a small starter set; Nepali wording to be reviewed by a native
  speaker.
- The app is not yet offline (v0.4) and the backend is not yet deployed.

### Next steps
- v0.4: run detection on-device (export model to TFLite/ONNX) for offline use,
  and design signed rule/lesson updates.
- Deploy the backend so the app works without a cable or laptop.
- Review Nepali lesson content; expand lessons and add progress tracking.

## v0.4 — Offline-first detection (2026-09-30)

**Goal:** Make the entire app usable with no internet — delivering the
"Include" pillar and direct evidence for RQ3 (offline protection).

**What was built**
- `lib/local_engine.dart`: a Dart port of the backend rule engine. It loads
  the *same* rule JSON files (bundled as app assets) and runs entirely
  on-device: message keyword analysis, URL analysis (brand impersonation,
  @-trick, IP host, punycode, suspicious TLD, shorteners, malformed/fail-safe),
  weighted risk scoring with the safety-advice discount, and bilingual
  explanations.
- Offline fallback in all four tabs: each tries the backend first and, on any
  network failure, falls back to the on-device engine and shows a
  "⚡ Offline (rule-based)" badge.
- Emergency guide ported (`emergencyPlan`) — mirrors `build_emergency_plan`:
  first steps → situation-specific steps in priority order → last steps,
  de-duplicated while preserving order.
- Lessons ported (`lessons`) — mirrors `get_lessons`: a random quiz per
  lesson, options shuffled, correct-answer index remapped to its new position.

**JSON-as-data parity:** phone and server read identical rule files, so offline
verdicts match online. No detection logic is hard-coded in Dart beyond what
faithfully mirrors the Python.

**How it was validated**
- Message and URL cases cross-checked against the backend before translation.
- Tested on a physical device (Realme RMX1941) in airplane mode: all four tabs
  produce correct results with no connection.
- Online path confirmed working via `adb reverse tcp:8000 tcp:8000` to the WSL
  backend.

**Engineering lessons recorded**
- Never swallow exceptions: a `catch (_)` hid the real "Unable to load asset"
  error; surfacing it (log the detail, show the user a calm message) found the
  bug in one step.
- Flutter assets must be *uncommented* in pubspec and picked up with
  `flutter clean` after changes.
- Brace discipline: a method must live inside the class body, above its final `}`.

**Security notes (development-only)**
- `usesCleartextTraffic=true` and the `localhost` backend are for development
  only; production requires an HTTPS backend.
- In offline mode no user data leaves the device; the bundled rule JSONs contain
  no secrets.

**Limitations / next**
- Offline detection is rule-based only; the ML classifier remains server-side.
  Optional stretch: export TF-IDF + logistic-regression weights to JSON for
  on-device inference.
- Backend still runs locally; cloud deployment would remove the USB/adb dependency.

## v0.4.1 — False-positive reduction (2026-09-30)

Problem: the ML model flagged benign everyday messages (e.g. "hi i love you
claude ai") as MEDIUM risk. Cause: all 200 legit training examples were formal
/ transactional (bank notices, OTPs, delivery updates) — the model had never
seen casual human conversation labelled safe, so anything conversational looked
foreign and scored scam-ish.

Fix: added 48 casual benign messages (new "personal" category; en / ne / roman
/ mixed) and retrained. The ML flag threshold was already 0.5 and left unchanged
(a probability of 0.62-legit should never be flagged).

Result — honest held-out eval on raw messages: accuracy 95.6%, scam recall 0.967
(missed 1 of 30), legit false-alarm rate 3/60. The benign test message dropped
from ~0.51 to 0.377 probability → now correctly LOW, with scam detection
preserved. Deployed live on Render.


## v0.7 (part) — Transformer baseline comparison for RQ2 (2026-09-30)

Compared the lightweight TF-IDF + LogisticRegression model against a modern
multilingual transformer (paraphrase-multilingual-MiniLM-L12-v2) embeddings +
LogisticRegression, on the SAME honest held-out test set (90 raw messages,
identical leakage guard as train_eval.py).

Result: TF-IDF + LR — accuracy 95.6%, scam F1 0.935, 3 false alarms.
Transformer embeddings + LR — accuracy 64.4%, scam F1 0.644, 31 false alarms
(precision 0.48). The lightweight model won clearly.

Interpretation: character n-grams capture the surface cues that mark scams
(links, "verify", "OTP", suspicious TLDs); frozen semantic embeddings capture
topic, so genuine and fake bank messages look alike and the classifier
over-flags. Supports the offline-first design: the smaller, on-device model is
also the more accurate here.

Caveat: this tested FROZEN embeddings, not a fine-tuned transformer. A fine-tuned
model was not evaluated and might narrow the gap, but would lose the on-device
advantage. Noted as future work.

Script: ai/compare_transformer.py (CPU-only torch).