# app/services/pipeline.py

import logging
from datetime import datetime

from app.services.decision_engine import make_decision
from app.services.ml_engine import classify_message_ml
from app.services.ai_engine import analyze_message_semantics
from app.services.explainability import generate_explanation

from app.services.risk_engine import calculate_risk_score
from app.services.trust_engine import calculate_trust_score
from app.services.scoring_engine import calculate_priority, calculate_credibility

from app.services.misuse_detection import detect_misuse

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_alert(
    message: str,
    user_name: str = "",
    phone: str = "",
    location: str = "",
    emergency_type: str = "other",
    misuse_count: int = 0
):

    # ======================================================
    # STEP 1 — SANITIZE & PREPARE DATA
    # ======================================================

    message        = (message or "").strip()
    user_name      = (user_name or "").strip()
    phone          = (phone or "").strip()
    location       = (location or "").strip()
    emergency_type = (emergency_type or "other").strip().lower()
    misuse_count   = max(0, int(misuse_count or 0))

    data = {
        "message":        message,
        "user_name":      user_name,
        "phone":          phone,
        "location":       location,
        "emergency_type": emergency_type
    }

    # ======================================================
    # STEP 2 — SCORES
    # ======================================================

    try:
        risk_score        = calculate_risk_score(message)
        credibility_score = calculate_credibility(data)
        priority_score    = calculate_priority(data)
        trust_score       = calculate_trust_score(credibility_score, misuse_count)
    except Exception as e:
        logger.error(f"Score calculation failed: {e}")
        risk_score = credibility_score = priority_score = trust_score = 0

    # ======================================================
    # STEP 3 — MISUSE DETECTION
    # ======================================================

    try:
        is_misuse, misuse_reason = detect_misuse(
            message, credibility_score, trust_score, risk_score
        )
    except Exception as e:
        logger.error(f"Misuse detection failed: {e}")
        is_misuse, misuse_reason = False, ""

    # Hard override — only if LOW risk
    if is_misuse and risk_score < 40:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.warning(f"MISUSE DETECTED | Reason: {misuse_reason} | Message: {message}")

        return {
            "decision":    "SUSPECTED_MISUSE",
            "reason":      misuse_reason,
            "score":       0,
            "timestamp":   timestamp,
            "scores": {
                "priority":    priority_score,
                "credibility": credibility_score,
                "trust":       trust_score,
                "risk":        risk_score
            },
            "ml": {
                "label":      "OVERRIDDEN",
                "confidence": 1.0
            },
            "ai": {
                "semantic_score": 0
            },
            "explanation": f"MISUSE DETECTED\n\nReason: {misuse_reason}\n\nMessage: {message}"
        }

    # ======================================================
    # STEP 4 — ML CLASSIFICATION
    # ======================================================

    try:
        ml_output = classify_message_ml(message)
        ml_label  = ml_output.get("label", "UNKNOWN") if ml_output else "UNKNOWN"
        ml_conf   = ml_output.get("confidence", 0.0)  if ml_output else 0.0
    except Exception as e:
        logger.error(f"ML classification failed: {e}")
        ml_label = "UNKNOWN"
        ml_conf  = 0.0

    # ======================================================
    # STEP 4.5 — AI SEMANTIC ENGINE
    # ======================================================

    try:
        # analyze_message_semantics returns int score 0–100
        ai_semantic_score = analyze_message_semantics(message)
    except Exception as e:
        logger.warning(f"AI engine failed, using 0: {e}")
        ai_semantic_score = 0

    # ======================================================
    # STEP 5 — DECISION
    # ======================================================

    try:
        decision, reason, score, timestamp = make_decision(
            priority_score,
            credibility_score,
            trust_score,
            risk_score,
            message,
            misuse_count,
            ml_label,
            ml_conf
        )
    except Exception as e:
        logger.error(f"Decision engine failed: {e}")
        decision  = "REVIEW_REQUIRED"
        reason    = "System error during decision"
        score     = 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(
        f"ALERT PROCESSED | Decision: {decision} | "
        f"ML: {ml_label} ({ml_conf:.2f}) | "
        f"AI Semantic: {ai_semantic_score} | "
        f"Risk: {risk_score} | Priority: {priority_score} | "
        f"Credibility: {credibility_score} | Trust: {trust_score}"
    )

    # ======================================================
    # STEP 6 — EXPLANATION
    # ======================================================

    try:
        explanation = generate_explanation(
            decision,
            priority_score,
            credibility_score,
            trust_score,
            risk_score,
            message,
            ml_label,
            ml_conf
        )
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        explanation = f"Decision: {decision}. Reason: {reason}"

    # ======================================================
    # FINAL OUTPUT
    # ======================================================

    return {
        "decision":  decision,
        "reason":    reason,
        "score":     score,
        "timestamp": timestamp,
        "scores": {
            "priority":    priority_score,
            "credibility": credibility_score,
            "trust":       trust_score,
            "risk":        risk_score
        },
        "ml": {
            "label":      ml_label,
            "confidence": ml_conf
        },
        "ai": {
            "semantic_score": ai_semantic_score
        },
        "explanation": explanation
    }