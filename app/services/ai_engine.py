# app/services/ai_engine.py

"""
AI SEMANTIC ENGINE
Intelligent Emergency Alert System
------------------------------------

Functions:
  • analyze_message_semantics(message) → int (0–100)
      Used by risk_engine.py for semantic risk scoring.

  • analyze_with_ai(message, emergency_type, ml_label) → dict
      Used by pipeline.py as the AI decision layer.
      Returns { "label": str, "confidence": float }

Improvements in this version:
  - Removed overly generic concepts (follow, running, hurt, pain)
  - Tightened similarity threshold (0.45 → 0.55)
  - Phrase score capped to prevent explosion
  - Stronger negation handling
  - Added analyze_with_ai() wrapper for pipeline integration
"""

import spacy

# Load once at module level (performance)
nlp = spacy.load("en_core_web_md")

# Preload reference doc (performance boost)
EMERGENCY_REFERENCE = nlp(
    "Someone is in danger and needs urgent help due to an emergency situation"
)

# ======================================================
# EMERGENCY CONCEPTS
# Removed: "follow", "running", "hurt", "pain" — too generic
# These were causing false positives on non-emergency messages
# ======================================================

EMERGENCY_CONCEPTS = {
    "collapse":    40,
    "faint":       40,
    "unresponsive":50,
    "help":        20,
    "danger":      30,
    "attack":      35,
    "emergency":   40,
    "ambulance":   40,
    "fire":        50,
    "accident":    35,
    "injury":      35,
    "bleed":       50,
    "stalk":       35,
    "threat":      35,
    "chase":       35,
    "trapped":     40,
    "unconscious": 50,
    "drowning":    50,
    "explosion":   50,
}

# ======================================================
# PHRASE PATTERNS — strong emergency signals
# ======================================================

PHRASE_PATTERNS = [
    "someone is following me",
    "someone is chasing me",
    "he is after me",
    "she is after me",
    "i am in danger",
    "please help me",
    "i need help",
    "not breathing",
    "passed out",
    "serious accident",
    "i am trapped",
    "cannot escape",
    "send help",
    "call ambulance",
    "call police"
]

# ======================================================
# NEGATION WORDS
# ======================================================

NEGATIONS = {"not", "no", "never", "nothing", "nobody", "nowhere"}


# ======================================================
# CORE SEMANTIC SCORING FUNCTION
# Used by risk_engine.py
# ======================================================

def analyze_message_semantics(message: str) -> int:
    """
    Returns semantic emergency score (0–100).
    Higher score = more likely a genuine emergency.
    """

    if not message:
        return 0

    try:
        msg = message.lower()
        doc = nlp(msg)

        score = 0

        # --------------------------------------------------
        # 1. PHRASE DETECTION — capped at 60
        # --------------------------------------------------

        phrase_score = 0
        for phrase in PHRASE_PATTERNS:
            if phrase in msg:
                phrase_score += 30

        score += min(phrase_score, 60)   # cap: max 2 phrase matches count

        # --------------------------------------------------
        # 2. TOKEN / LEMMA ANALYSIS
        # --------------------------------------------------

        seen_tokens  = set()
        negation_count = 0

        for token in doc:
            lemma = token.lemma_

            if lemma in seen_tokens:
                continue

            # Count negations — applied as penalty after loop
            if token.text in NEGATIONS:
                negation_count += 1

            if lemma in EMERGENCY_CONCEPTS:
                score += EMERGENCY_CONCEPTS[lemma]
                seen_tokens.add(lemma)

        # Apply negation penalty — each negation reduces score more meaningfully
        score -= negation_count * 20

        # --------------------------------------------------
        # 3. SEMANTIC SIMILARITY
        # Tightened threshold: 0.45 → 0.55 to reduce false positives
        # --------------------------------------------------

        similarity = doc.similarity(EMERGENCY_REFERENCE)

        if similarity > 0.80:
            score += 30
        elif similarity > 0.70:
            score += 20
        elif similarity > 0.55:      # was 0.45 — tightened to reduce noise
            score += 10

        # --------------------------------------------------
        # 4. NORMALIZE
        # --------------------------------------------------

        return max(0, min(score, 100))

    except Exception:
        return 0


# ======================================================
# AI DECISION WRAPPER
# Used by pipeline.py — returns label + confidence
# ======================================================

def analyze_with_ai(
    message: str,
    emergency_type: str = "other",
    ml_label: str = "UNKNOWN"
) -> dict:
    """
    Wraps analyze_message_semantics() into a label + confidence output.
    Used as the AI layer in the pipeline alongside the ML classifier.

    Returns:
    {
        "label":      str,   — one of the 5 decision categories
        "confidence": float  — 0.0 to 1.0
    }
    """

    try:
        semantic_score = analyze_message_semantics(message)

        # Emergency type boost
        type_boost = {
            "medical":  15,
            "fire":     15,
            "crime":    15,
            "accident": 10,
            "other":    0
        }

        boosted_score = min(
            semantic_score + type_boost.get((emergency_type or "other").lower(), 0),
            100
        )

        # Map score to decision label
        if boosted_score >= 75:
            label      = "IMMEDIATE_ESCALATION"
            confidence = round(boosted_score / 100, 2)

        elif boosted_score >= 55:
            label      = "CONDITIONAL_ESCALATION"
            confidence = round(boosted_score / 100, 2)

        elif boosted_score >= 35:
            label      = "REVIEW_REQUIRED"
            confidence = round(boosted_score / 100, 2)

        elif boosted_score >= 15:
            label      = "LOG_AND_MONITOR"
            confidence = round(boosted_score / 100, 2)

        else:
            label      = "LOG_AND_MONITOR"
            confidence = 0.1

        return {
            "label":          label,
            "confidence":     confidence,
            "semantic_score": boosted_score
        }

    except Exception:
        return {
            "label":          ml_label or "UNKNOWN",
            "confidence":     0.0,
            "semantic_score": 0
        }