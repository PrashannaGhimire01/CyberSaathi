"""Test a saved model on a small set of OBVIOUS, hand-written messages it never
saw, in natural varied styles. A real scam detector should score these easily.
If it scores near 0.5, the model learned dataset-style, not scam-ness."""
from pathlib import Path
import joblib

MODEL = Path(__file__).parent / "models" / "scam_model.joblib"
model = joblib.load(MODEL)

# (message, true_label)  -- all are unambiguous to a human
PROBES = [
    ("Congratulations! You won Rs 50,000 in our lucky draw. Send your OTP to claim.", "scam"),
    ("Tapai le lottery jitnu bhayo! Rs 1 lakh paunus, yo link kholnus bit.ly/win", "scam"),
    ("तपाईंको खाता बन्द हुँदैछ, तुरुन्तै OTP पठाउनुहोस्।", "scam"),
    ("Your account is suspended. Verify at http://esewa-secure.xyz to unlock now.", "scam"),
    ("Urgent! Send Rs 2000 to this number to receive your prize money.", "scam"),
    ("Job in Dubai, no experience needed. Pay Rs 5000 registration to confirm.", "scam"),
    ("Click here to claim your free government relief fund immediately.", "scam"),
    ("Mummy I lost my phone, send money urgently to this new number.", "scam"),
    ("Hey, are we still on for lunch tomorrow at 1pm?", "legit"),
    ("Your OTP is 552013. Do not share this with anyone.", "legit"),
    ("भोलि बिहान ८ बजे भेटौं है।", "legit"),
    ("Rs 500 debited from your account. Balance Rs 12,300.", "legit"),
    ("Thanks for your payment. Your order will arrive Tuesday.", "legit"),
    ("Ma ghar aaipuge, khana khayeu?", "legit"),
    ("Reminder: your electricity bill is due on the 30th.", "legit"),
    ("Happy Dashain to you and your family!", "legit"),
]

correct = 0
print("  prob  | pred  | true  | message")
print("  ------+-------+-------+--------")
for text, true in PROBES:
    p = model.predict_proba([text])[0][1]
    pred = "scam" if p >= 0.5 else "legit"
    ok = "OK " if pred == true else "XX "
    correct += pred == true
    print(f"  {p:.2f}  | {pred:5} | {true:5} | {ok} {text[:45]}")

print(f"\n  External accuracy: {correct}/{len(PROBES)} = {100*correct/len(PROBES):.0f}%")
print("  (near 100% = generalises well; near 50% = learned dataset-style only)")