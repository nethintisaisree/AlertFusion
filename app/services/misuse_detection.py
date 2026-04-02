# app/services/misuse_detection.py

"""
MISUSE DETECTION ENGINE
Soft-Prevention Layer Core
--------------------------

Purpose:
    Detect prank / fake / misuse messages without
    permanently blocking the user.

Soft-Prevention Principle:
    - Never hard-block a user
    - Flag suspicious reports for review
    - Allow genuine emergencies even from low-trust users
    - Severity levels: CONFIRMED / SUSPECTED / CLEAR
"""

import re

# ======================================================
# STRONG MISUSE KEYWORDS
# Checked with word boundaries to avoid false positives
# e.g. "test" won't match "protest" or "attestation"
# ======================================================

STRONG_MISUSE_KEYWORDS = [
    r"\bfake\b",
    r"\bprank\b",
    r"\bjust testing\b",
    r"\bfor fun\b",
    r"\btimepass\b",
    r"\bjoking\b",
    r"\bthis is a test\b",
    r"\bnot real\b",
    r"\bnot an emergency\b"
]

# ======================================================
# WEAK MISUSE SIGNALS
# These alone don't confirm misuse — used as support signals
# ======================================================

WEAK_MISUSE_SIGNALS = [
    r"\btest\b",
    r"\btesting\b",
    r"\blol\b",
    r"\bhaha\b",
    r"\bhehe\b",
    r"\blmao\b",
    r"\bfunny\b",
    r"\bjoke\b"
]


def detect_misuse(
    message: str,
    credibility: int,
    trust_score: int,
    risk_score: int,
    misuse_count: int = 0
):
    """
    Returns:
        (bool, str) — (is_misuse, reason)

    Logic:
        CONFIRMED misuse  → strong keyword present + low risk
        SUSPECTED misuse  → multiple weak signals + low credibility/trust
        REPEAT offender   → misuse_count >= 5 + low credibility
        CLEAR             → no misuse signals
    """

    try:
        message      = (message or "").lower()
        credibility  = max(0, min(100, int(credibility  or 0)))
        trust_score  = max(0, min(100, int(trust_score  or 0)))
        risk_score   = max(0, min(100, int(risk_score   or 0)))
        misuse_count = max(0, int(misuse_count or 0))

        # ======================================================
        # CHECK 1 — STRONG MISUSE KEYWORD + LOW RISK
        # Confirmed misuse: explicit prank/fake language + no real risk
        # ======================================================

        strong_hit = any(re.search(pattern, message) for pattern in STRONG_MISUSE_KEYWORDS)

        if strong_hit and risk_score < 30:
            return True, "Explicit misuse language detected with low risk score"

        # ======================================================
        # CHECK 2 — WEAK SIGNALS + LOW CREDIBILITY/TRUST
        # Multiple weak signals together = suspected misuse
        # But NOT if risk is high — "lol there's a fire" is still treated as real
        # ======================================================

        weak_hits = sum(1 for pattern in WEAK_MISUSE_SIGNALS if re.search(pattern, message))

        if weak_hits >= 2 and credibility < 40 and trust_score < 50 and risk_score < 35:
            return True, "Multiple misuse signals with low credibility and trust"

        # ======================================================
        # CHECK 3 — REPEAT OFFENDER + VERY LOW CREDIBILITY
        # User with many misuse reports + poor credibility
        # ======================================================

        if misuse_count >= 5 and credibility < 35 and risk_score < 40:
            return True, "Repeat misuse history with low credibility"

        # ======================================================
        # CLEAR — no misuse detected
        # ======================================================

        return False, "No misuse detected"

    except Exception:
        return False, "Detection error — defaulting to no misuse"