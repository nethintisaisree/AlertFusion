# app/services/risk_engine.py

"""
RISK ENGINE WITH AI INTEGRATION

- Keyword scoring (Critical / Moderate / Low / Intensity)
- Per-category score cap to prevent stacking explosion
- AI semantic score integration
- Returns normalized risk score [0-100]
"""

import re
from app.services.ai_engine import analyze_message_semantics


# ======================================================
# KEYWORD SETS
# Moved 'hurt' and 'pain' to MODERATE — too generic for CRITICAL
# Removed 'follow' and 'breaking' — too many false positives
# ======================================================

CRITICAL_KEYWORDS = {
    "gun", "knife", "shoot", "fire", "explosion",
    "bomb", "bleeding", "not breathing",
    "unconscious", "heart attack", "dying",
    "suicide", "kill", "murder", "stab",
    "stabbed", "stabbing", "collapsed",
    "faint", "unresponsive", "flames", "drowning",
    "choking", "overdose"
}

MODERATE_KEYWORDS = {
    "accident", "injured", "crash", "ambulance",
    "threat", "attack", "emergency", "help",
    "danger", "robbery", "theft", "break in",
    "intruder", "burglar", "trespass", "forced entry",
    "hurt", "pain", "trapped", "stuck"
}

LOW_KEYWORDS = {
    "suspicious", "unknown person", "being followed",
    "stalk", "stalking", "unsafe", "strange activity",
    "someone watching", "someone outside"
}

INTENSITY_WORDS = {
    "severe", "major", "critical", "urgent",
    "immediately", "serious", "right now", "please hurry"
}


def calculate_risk_score(message: str) -> int:

    if not message:
        return 0

    msg = message.lower()

    keyword_score = 0

    # ======================================================
    # CRITICAL — cap at 80 to prevent stacking explosion
    # ======================================================

    critical_hits = sum(1 for word in CRITICAL_KEYWORDS if word in msg)
    keyword_score += min(critical_hits * 40, 80)

    # ======================================================
    # MODERATE — cap at 50
    # ======================================================

    moderate_hits = sum(1 for word in MODERATE_KEYWORDS if word in msg)
    keyword_score += min(moderate_hits * 25, 50)

    # ======================================================
    # LOW — cap at 20
    # ======================================================

    low_hits = sum(1 for word in LOW_KEYWORDS if word in msg)
    keyword_score += min(low_hits * 10, 20)

    # ======================================================
    # INTENSITY WORDS — cap at 30
    # ======================================================

    intensity_hits = sum(1 for word in INTENSITY_WORDS if word in msg)
    keyword_score += min(intensity_hits * 15, 30)

    # ======================================================
    # MULTIPLE PEOPLE INVOLVED
    # ======================================================

    if re.search(r"\bpeople\b|\bpersons\b|\bmultiple\b|\beveryone\b", msg):
        keyword_score += 15

    # Cap raw keyword score at 100 before blending
    keyword_score = min(keyword_score, 100)

    # ======================================================
    # AI SEMANTIC SCORE INTEGRATION
    # ======================================================

    try:
        semantic_score = analyze_message_semantics(msg)
    except Exception:
        semantic_score = 0

    # Blend: 50% keyword logic + 50% AI semantic understanding
    final_score = min(int((semantic_score * 0.5) + (keyword_score * 0.5)), 100)

    return final_score