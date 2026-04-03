# app/services/decision_engine.py

from datetime import datetime
import time

# ======================================================
# DECISION LABELS
# ======================================================

IMMEDIATE_ESCALATION   = "IMMEDIATE_ESCALATION"
CONDITIONAL_ESCALATION = "CONDITIONAL_ESCALATION"
REVIEW_REQUIRED        = "REVIEW_REQUIRED"
LOG_AND_MONITOR        = "LOG_AND_MONITOR"
SUSPECTED_MISUSE       = "SUSPECTED_MISUSE"


# ======================================================
# KEYWORD SETS
# ======================================================

CRITICAL_KEYWORDS = {
    "fire", "gun", "shoot", "bleeding", "unconscious",
    "not breathing", "heart attack", "armed",
    "explosion", "dying", "suicide", "stab", "knife",
    "drowning", "choking", "overdose", "poisoning", "kidnapping",
    "robbery", "robber", "burglar", "burglary", "intruder",
    "thief inside", "still inside", "trapped inside"
}

SAFETY_OVERRIDE_KEYWORDS = {
    "smoke", "burning", "collapsed", "fainted",
    "injured", "blood", "fight", "screaming", "accident"
}

MISUSE_KEYWORDS = {
    "test", "testing", "fake", "prank", "joke",
    "lol", "haha", "hehe", "lmao", "joking"
}

# Local negation list — no external import needed
NEGATIONS = ["not", "no", "never", "isn't", "can't", "cannot", "unable"]


# ======================================================
# HELPERS
# ======================================================

def _now() -> str:
    """Returns current timestamp as formatted string — consistent across codebase."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def detect_threat_intent(message: str) -> bool:
    """
    Detects stalking / following / surveillance threat patterns.
    Removed 'outside' — too generic and caused false positives.
    """
    message = (message or "").lower()

    threat_keywords = [
        "following me", "chasing me", "stalking",
        "watching me", "tracking me",
        "suspicious person", "unknown person",
        "someone following", "being followed"
    ]

    return any(phrase in message for phrase in threat_keywords)


# ======================================================
# MAIN DECISION FUNCTION
# ======================================================

def make_decision(
    priority_score: int,
    credibility_score: int,
    trust_score: int,
    risk_score: int,
    message: str = "",
    misuse_count: int = 0,
    ml_label: str = "UNKNOWN",
    ml_conf: float = 0.0
):
    message = (message or "").lower()
    words   = message.split()

    # ================= LIFE-CRITICAL: BREATHING DETECTION =================
    # Checks for negation near "breath" word — e.g. "not breathing", "can't breathe"

    for i, word in enumerate(words):
        if "breath" in word:
            window = words[max(0, i - 3):i + 1]
            if any(neg in w for w in window for neg in NEGATIONS):
                return (
                    IMMEDIATE_ESCALATION,
                    "Detected breathing failure with negation",
                    100,
                    _now()
                )

    # ================= ML CRITICAL OVERRIDE =================
    # ML strongly predicts IMMEDIATE + risk is high enough to trust it

    if ml_label == "IMMEDIATE_ESCALATION" and ml_conf > 0.75 and risk_score >= 40:
        return (
            IMMEDIATE_ESCALATION,
            "ML strongly detected emergency with supporting risk",
            95,
            _now()
        )

    # ================= ML SCORE CONTRIBUTION =================

    ml_weight = {
        "IMMEDIATE_ESCALATION":   0.5,
        "CONDITIONAL_ESCALATION": 0.3,
        "REVIEW_REQUIRED":        0.2,
        "SUSPECTED_MISUSE":       0.0,
        "UNKNOWN":                0.1
    }

    ml_score = ml_weight.get(ml_label, 0.1) * ml_conf * 100

    # ================= MISUSE PENALTY =================

    misuse_penalty = 0

    if any(keyword in message for keyword in MISUSE_KEYWORDS):
        misuse_penalty += 40

    if credibility_score < 30 and trust_score < 30:
        misuse_penalty += 30

    if misuse_count >= 3:
        misuse_penalty += 30

    # Strong ML misuse override
    if ml_label == "SUSPECTED_MISUSE" and ml_conf > 0.7:
        return (
            SUSPECTED_MISUSE,
            "ML strongly detected misuse",
            0,
            _now()
        )

    # ================= CRITICAL KEYWORDS =================
    # Intentional: critical keywords bypass misuse penalty.
    # A message with "fire" + "lol" is still treated as potential emergency.

    if any(keyword in message for keyword in CRITICAL_KEYWORDS):
        if risk_score >= 50:
            return (
                IMMEDIATE_ESCALATION,
                "Critical emergency keyword with high risk score",
                95,
                _now()
            )
        return (
            CONDITIONAL_ESCALATION,
            "Critical emergency keyword detected",
            75,
            _now()
        )

    # ================= HIGH RISK SCORE =================

    if risk_score >= 70:
        return (
            IMMEDIATE_ESCALATION,
            "High risk score detected",
            90,
            _now()
        )

    if risk_score >= 50:
        return (
            CONDITIONAL_ESCALATION,
            "Moderate risk score detected",
            70,
            _now()
        )

    # ================= THREAT INTENT =================

    if detect_threat_intent(message):

        adjusted_risk = risk_score + 30

        if ml_label in ["CONDITIONAL_ESCALATION", "IMMEDIATE_ESCALATION"]:
            adjusted_risk += 10

        if adjusted_risk >= 45:
            return (
                CONDITIONAL_ESCALATION,
                "Threat intent detected with contextual risk",
                70,
                _now()
            )

        return (
            REVIEW_REQUIRED,
            "Suspicious activity detected — needs review",
            50,
            _now()
        )

    # ================= SAFETY KEYWORDS =================

    if any(k in message for k in SAFETY_OVERRIDE_KEYWORDS):
        if risk_score >= 40:
            return (
                CONDITIONAL_ESCALATION,
                "Safety issue detected",
                65,
                _now()
            )
        return (
            REVIEW_REQUIRED,
            "Safety concern requires review",
            50,
            _now()
        )

    # ================= LOW INFO =================

    if len(words) <= 2 and risk_score < 40:
        return (
            LOG_AND_MONITOR,
            "Insufficient information provided",
            20,
            _now()
        )

    # ================= GLOBAL EMERGENCY SIGNAL =================

    emergency_signal = (
        risk_score >= 20 or
        "help"      in message or
        "danger"    in message or
        "emergency" in message
    )

    if not emergency_signal:
        return (
            LOG_AND_MONITOR,
            "No emergency indicators detected",
            10,
            _now()
        )

    # ================= WEIGHTED FINAL SCORE =================

    emergency_score = int(
        priority_score    * 0.20 +
        credibility_score * 0.15 +
        trust_score       * 0.15 +
        risk_score        * 0.30 +
        ml_score          * 0.20
    )

    emergency_score -= misuse_penalty
    emergency_score  = max(0, min(100, emergency_score))

    # ================= FINAL DECISION =================

    if emergency_score >= 80:
        return (IMMEDIATE_ESCALATION,   "High emergency score",           emergency_score, _now())

    if emergency_score >= 60:
        return (CONDITIONAL_ESCALATION, "Moderate emergency probability",  emergency_score, _now())

    if emergency_score >= 40:
        return (REVIEW_REQUIRED,        "Requires human review",           emergency_score, _now())

    return     (LOG_AND_MONITOR,        "Low emergency probability",       emergency_score, _now())