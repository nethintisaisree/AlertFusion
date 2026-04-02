# app/services/ml_engine.py

"""
ML ENGINE
Intelligent Emergency Alert System
------------------------------------

Loads a trained TF-IDF + Logistic Regression model and
classifies emergency messages into decision categories.

Model files:
    model/emergency_model.pkl  — trained LogisticRegression
    model/vectorizer.pkl       — fitted TfidfVectorizer

Safe loading:
    If model files are missing, functions return UNKNOWN
    gracefully instead of crashing the app on startup.
"""

import os
import logging
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================
# MODEL PATH — resolved relative to project root
# Works regardless of which directory app is run from
# ======================================================

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH     = os.path.join(BASE_DIR, "model", "emergency_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "model", "vectorizer.pkl")

# ======================================================
# SAFE MODEL LOADING
# App does not crash if files are missing — logs warning instead
# ======================================================

model      = None
vectorizer = None

try:
    model      = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    logger.info("ML model and vectorizer loaded successfully")
except FileNotFoundError:
    logger.warning(
        "ML model files not found. Run train_model.py first. "
        "ML classification will return UNKNOWN until models are loaded."
    )
except Exception as e:
    logger.error(f"Failed to load ML model: {e}")


# ======================================================
# MAIN CLASSIFICATION FUNCTION
# ======================================================

def classify_message_ml(message: str) -> dict:
    """
    Classifies a message using the trained ML model.

    Returns:
        {
            "label":      str,   — predicted decision category
            "confidence": float  — 0.0 to 1.0
        }

    Always returns a valid dict — never raises an exception.
    """

    # Model not loaded — return safe fallback
    if model is None or vectorizer is None:
        logger.warning("ML model not loaded — returning UNKNOWN")
        return {"label": "UNKNOWN", "confidence": 0.0}

    # Input validation
    if not message or len(message.strip()) < 3:
        return {"label": "UNKNOWN", "confidence": 0.0}

    try:
        msg = message.lower().strip()

        # Must match training format: "message [emergency_type]"
        # emergency_type is not available here, so we use a neutral tag
        
        combined = msg + " [other]"
        X = vectorizer.transform([combined])

        # No useful features in message
        if X.nnz == 0:
            return {"label": "UNKNOWN", "confidence": 0.0}

        # Predict label
        prediction = model.predict(X)[0]

        # Get confidence from class probabilities
        probabilities = model.predict_proba(X)[0]
        confidence    = float(max(probabilities))

        return {
            "label":      prediction,
            "confidence": confidence
        }

    except Exception as e:
        logger.error(f"ML classification error: {e}")
        return {"label": "UNKNOWN", "confidence": 0.0}


# ======================================================
# DEBUG HELPER
# Returns full probability breakdown for all classes
# Useful for explainability and testing
# ======================================================

def get_ml_debug_info(message: str) -> dict:
    """
    Returns detailed ML classification info for debugging.

    Returns:
        {
            "prediction":        str,
            "confidence":        float,
            "all_probabilities": dict  — {label: probability}
        }
    """

    if model is None or vectorizer is None:
        return {"error": "ML model not loaded"}

    if not message or len(message.strip()) < 3:
        return {"error": "Message too short"}

    try:
        msg = message.lower().strip()
        X   = vectorizer.transform([msg])

        if X.nnz == 0:
            return {"error": "No meaningful features detected"}

        prediction    = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        class_labels  = model.classes_

        prob_map = {
            class_labels[i]: round(float(probabilities[i]), 4)
            for i in range(len(class_labels))
        }

        return {
            "prediction":        prediction,
            "confidence":        round(float(max(probabilities)), 4),
            "all_probabilities": prob_map
        }

    except Exception as e:
        logger.error(f"ML debug info error: {e}")
        return {"error": str(e)}