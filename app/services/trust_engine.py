# app/services/trust_engine.py

"""
TRUST ENGINE
Intelligent Emergency Alert System
------------------------------------

Purpose:
    Calculate USER TRUST SCORE based on:
      • Credibility Score (identity + message quality)
      • Past Misuse Count (behavioral history)
      • Legitimate report bonus (positive behavior)
      • Soft-Prevention Layer logic

Trust Score Range: 0 to 100

Soft-Prevention Principle:
    • Never permanently block a user
    • Reduce trust gradually for misuse
    • Allow trust recovery through legitimate reports
    • High trust → faster escalation
    • Low trust  → conditional / review / monitor
"""

# ======================================================
# BASE TRUST FOR NEW USERS
# New users start at 60 — not 0.
# They haven't earned high trust yet, but they haven't
# done anything wrong either.
# ======================================================

BASE_TRUST = 60


# ======================================================
# MAIN FUNCTION
# ======================================================

def calculate_trust_score(
    credibility_score: int,
    misuse_count: int = 0
) -> int:
    """
    Calculates trust score using credibility + misuse history.

    Args:
        credibility_score : int  — 0 to 100, from scoring_engine
        misuse_count      : int  — number of past misuse flags

    Returns:
        int — trust score 0 to 100
    """

    try:
        credibility_score = max(0, min(100, int(credibility_score or 0)))
        misuse_count      = max(0, int(misuse_count or 0))

        # --------------------------------------------------------
        # BASE TRUST
        # Blend of fixed baseline + credibility score
        # New user with no info: starts at BASE_TRUST (60)
        # Fully credible user: starts higher
        # --------------------------------------------------------

        trust_score = int((BASE_TRUST * 0.4) + (credibility_score * 0.6))

        # --------------------------------------------------------
        # MISUSE PENALTY — gradual, not a cliff
        # Each misuse level adds progressively more penalty
        # --------------------------------------------------------

        if misuse_count >= 7:
            trust_score -= 50
        elif misuse_count >= 5:
            trust_score -= 40
        elif misuse_count >= 3:
            trust_score -= 25
        elif misuse_count >= 2:
            trust_score -= 15
        elif misuse_count >= 1:
            trust_score -= 8

        # --------------------------------------------------------
        # BONUS FOR HIGH CREDIBILITY + CLEAN HISTORY
        # Rewards users who consistently provide complete reports
        # and have never misused the system
        # --------------------------------------------------------

        if credibility_score >= 80 and misuse_count == 0:
            trust_score += 10

        # --------------------------------------------------------
        # PARTIAL RECOVERY BONUS
        # If misuse_count is low (1-2) but credibility is high,
        # user shows corrective behavior — small trust recovery
        # --------------------------------------------------------

        if misuse_count in (1, 2) and credibility_score >= 70:
            trust_score += 5   # partial recovery for high-credibility low-misuse users

        # --------------------------------------------------------
        # NORMALIZE
        # --------------------------------------------------------

        return max(0, min(100, trust_score))

    except Exception:
        return BASE_TRUST   # safe default for new users on error


# ======================================================
# TRUST LEVEL LABEL
# Used in result.html and admin dashboard
# ======================================================

def get_trust_level(trust_score: int) -> str:
    """
    Converts numeric trust score to human-readable level.
    Used in result.html trust badge and admin views.
    """

    try:
        trust_score = int(trust_score or 0)

        if trust_score >= 80:
            return "HIGH"
        elif trust_score >= 60:
            return "GOOD"
        elif trust_score >= 40:
            return "MODERATE"
        elif trust_score >= 20:
            return "LOW"
        else:
            return "VERY LOW"

    except Exception:
        return "UNKNOWN"