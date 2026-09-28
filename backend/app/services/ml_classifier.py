"""Loads the trained ML scam model and exposes a scam-probability function.
Fails gracefully: if the model file or scikit-learn is missing, the backend
still runs on rules alone (MODEL_AVAILABLE stays False)."""
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[3] / "ai" / "models" / "scam_model.joblib"
_model = None
MODEL_AVAILABLE = False

try:
    import joblib
    if MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
        MODEL_AVAILABLE = True
except Exception:
    _model = None
    MODEL_AVAILABLE = False

def scam_probability(text):
    """Return P(scam) in [0,1], or None if the model isn't available."""
    if not MODEL_AVAILABLE:
        return None
    return float(_model.predict_proba([text])[0][1])