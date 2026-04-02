# app/services/scoring_engine.py

"""
SCORING ENGINE
Intelligent Emergency Alert System
-----------------------------------

Calculates:
  • Priority Score     — urgency of emergency type + message keywords
  • Credibility Score  — quality of user identity + message detail
  • ECS               — Emergency Credibility Score (0.0 to 1.0)

These scores form the foundation of the decision pipeline.
"""


# ============================================================
# PRIORITY SCORE
# ============================================================

def calculate_priority(data: dict) -> int:
    """
    Evaluates emergency type weight + message keyword severity.
    Returns int 0–100.
    """

    message        = str(data.get("message", "")).lower()
    emergency_type = str(data.get("emergency_type", "")).lower()

    score = 0

    # --------------------------------------------------------
    # EMERGENCY TYPE WEIGHT
    # --------------------------------------------------------

    type_weights = {
        "medical":  40,
        "fire":     45,
        "crime":    45,
        "accident": 35,
        "other":    10
    }

    score += type_weights.get(emergency_type, 10)

    # --------------------------------------------------------
    # CRITICAL KEYWORDS — capped at 30 (one match is enough)
    # --------------------------------------------------------

    critical_keywords = [
        "not breathing", "unconscious", "heart attack",
        "dying", "bleeding", "gun", "fire",
        "explosion", "suicide", "stabbed", "drowning"
    ]

    critical_hits = sum(1 for word in critical_keywords if word in message)
    score += min(critical_hits * 30, 30)   # cap: one critical keyword = max bonus

    # --------------------------------------------------------
    # MODERATE KEYWORDS — capped at 30
    # --------------------------------------------------------

    moderate_keywords = [
        "injured", "accident", "ambulance", "emergency",
        "threat", "help", "urgent", "danger", "trapped"
    ]

    moderate_hits = sum(1 for word in moderate_keywords if word in message)
    score += min(moderate_hits * 15, 30)   # cap: two moderate keywords = max bonus

    return min(score, 100)


# ============================================================
# CREDIBILITY SCORE
# ============================================================

def calculate_credibility(data: dict) -> int:
    """
    Evaluates user identity completeness + message quality.
    Returns int 0–100.
    """

    score = 0

    user_name = str(data.get("user_name", "")).strip()
    phone     = str(data.get("phone", "")).strip()
    location  = str(data.get("location", "")).strip()
    message   = str(data.get("message", "")).strip()

    # --------------------------------------------------------
    # USER IDENTITY — minimum length checks added
    # --------------------------------------------------------

    if len(user_name) >= 3:     # reject single letters like "a"
        score += 25

    if len(phone) >= 10 and phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
        score += 25             # must be numeric, not just any 10 chars

    if len(location) >= 3:      # reject single characters
        score += 20

    # --------------------------------------------------------
    # MESSAGE QUALITY
    # --------------------------------------------------------

    word_count = len(message.split())

    if word_count >= 8:
        score += 20
    elif word_count >= 4:
        score += 10

    # --------------------------------------------------------
    # MISUSE WORD PENALTY
    # --------------------------------------------------------

    misuse_words = [
        "test", "testing", "lol", "haha",
        "fake", "prank", "joke", "timepass"
    ]

    if any(word in message.lower() for word in misuse_words):
        score -= 40

    return max(0, min(score, 100))


# ============================================================
# EMERGENCY CREDIBILITY SCORE (ECS)
# ============================================================

def calculate_ecs(credibility_score: int, trust_score: int, risk_score: int) -> float:
    """
    ECS (0.0–1.0 scale) measures the probability of a genuine emergency.
    Combines credibility, trust, and contextual risk into a single score.

    Used in result.html as a percentage (multiplied by 100 in template).
    """

    try:
        # Clamp all inputs to valid range
        credibility_score = max(0, min(100, int(credibility_score or 0)))
        trust_score       = max(0, min(100, int(trust_score or 0)))
        risk_score        = max(0, min(100, int(risk_score or 0)))

        # --------------------------------------------------------
        # CONTEXT ALIGNMENT — smooth curve instead of cliff jumps
        # --------------------------------------------------------

        if risk_score >= 70:
            context_alignment = 95
        elif risk_score >= 50:
            context_alignment = 80
        elif risk_score >= 30:
            context_alignment = 60
        elif risk_score >= 10:
            context_alignment = 40
        else:
            context_alignment = 20

        ecs_raw = (
            credibility_score * 0.40 +
            trust_score       * 0.30 +
            context_alignment * 0.30
        )

        return round(ecs_raw / 100, 2)

    except Exception:
        return 0.0