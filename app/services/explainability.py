# app/services/explainability.py

"""
EXPLAINABILITY ENGINE
Intelligent Emergency Alert System
------------------------------------

Generates a human-readable explanation for every decision
made by the system. Used in result.html and audit logs.
"""


# ======================================================
# SCORE LEVEL HELPER
# ======================================================

def level(score: int) -> str:
    """Converts numeric score to human-readable level."""
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MODERATE"
    else:
        return "LOW"


# ======================================================
# KEYWORD DETECTION
# Expanded and fixed — removed generic false-positive words
# ======================================================

def detect_keywords(message: str):
    """
    Detects and categorizes keywords found in the message.
    Returns list of human-readable trigger strings.
    """

    message = (message or "").lower()
    triggers = []

    critical = [
        "fire", "gun", "shoot", "bleeding", "explosion",
        "bomb", "knife", "stab", "stabbed", "unconscious",
        "not breathing", "heart attack", "dying", "suicide",
        "drowning", "choking", "overdose", "flames", "collapsed"
    ]

    threat = [
        "following me", "chasing me", "stalking",
        "someone watching", "suspicious person",
        "being followed", "unknown person outside"
    ]

    misuse = [
        "fake", "prank", "just testing",
        "not real", "for fun", "timepass"
    ]

    for word in critical:
        if word in message:
            triggers.append(f"Critical keyword detected: '{word}'")

    for phrase in threat:
        if phrase in message:
            triggers.append(f"Threat signal detected: '{phrase}'")

    for word in misuse:
        if word in message:
            triggers.append(f"Possible misuse indicator: '{word}'")

    if "help" in message:
        triggers.append("Help request signal detected")

    if "danger" in message:
        triggers.append("Danger signal detected")

    if "urgent" in message or "immediately" in message:
        triggers.append("Urgency signal detected")

    if "trapped" in message or "stuck" in message:
        triggers.append("Entrapment signal detected")

    return triggers


# ======================================================
# MAIN EXPLANATION GENERATOR
# ======================================================

def generate_explanation(
    decision: str,
    priority: int,
    credibility: int,
    trust_score: int,
    risk_score: int,
    message: str,
    ml_label: str,
    ml_conf: float
) -> str:
    """
    Generates a structured, human-readable explanation
    for the system's decision on a given alert.
    """

    message = (message or "").strip()

    # Truncate very long messages for display
    display_message = message if len(message) <= 200 else message[:200] + "..."

    explanation = f"""USER MESSAGE:
"{display_message}"

FINAL DECISION: {decision.replace("_", " ")}

==============================
SCORE ANALYSIS
==============================
• Risk Score:        {risk_score}/100  [{level(risk_score)}]
• Priority Score:    {priority}/100    [{level(priority)}]
• Credibility Score: {credibility}/100 [{level(credibility)}]
• Trust Score:       {trust_score}/100 [{level(trust_score)}]
"""

    # --------------------------------------------------
    # KEY SIGNALS
    # --------------------------------------------------

    triggers = detect_keywords(message)

    explanation += "\n==============================\n"
    explanation += "KEY SIGNALS DETECTED\n"
    explanation += "==============================\n"

    if triggers:
        for t in triggers:
            explanation += f"• {t}\n"
    else:
        explanation += "• No strong emergency keywords detected in message\n"

    # --------------------------------------------------
    # ML ANALYSIS
    # --------------------------------------------------

    explanation += "\n==============================\n"
    explanation += "ML MODEL ANALYSIS\n"
    explanation += "==============================\n"

    if ml_label and ml_label not in ("UNKNOWN", "OVERRIDDEN"):
        if ml_conf >= 0.75:
            explanation += f"• Strong ML prediction: {ml_label.replace('_', ' ')} (confidence: {ml_conf:.0%})\n"
        elif ml_conf >= 0.4:
            explanation += f"• Moderate ML indication: {ml_label.replace('_', ' ')} (confidence: {ml_conf:.0%})\n"
        else:
            explanation += f"• Weak ML signal: {ml_label.replace('_', ' ')} (confidence: {ml_conf:.0%}) — rule-based logic used\n"
    elif ml_label == "OVERRIDDEN":
        explanation += "• ML output overridden — misuse detected before classification\n"
    else:
        explanation += "• ML model could not classify this message confidently\n"
        explanation += "• Decision derived from AI semantic + rule-based logic\n"

    # --------------------------------------------------
    # DECISION REASONING
    # --------------------------------------------------

    explanation += "\n==============================\n"
    explanation += "DECISION REASONING\n"
    explanation += "==============================\n"

    if decision == "IMMEDIATE_ESCALATION":
        explanation += "• IMMEDIATE ESCALATION triggered\n"
        if risk_score >= 70:
            explanation += f"  → Risk score ({risk_score}) exceeded critical threshold (70)\n"
        if any(k in message.lower() for k in ["not breathing", "unconscious", "heart attack", "dying", "bleeding"]):
            explanation += "  → Life-critical keyword detected in message\n"
        explanation += "  → Immediate emergency response recommended\n"

    elif decision == "CONDITIONAL_ESCALATION":
        explanation += "• CONDITIONAL ESCALATION triggered\n"
        if risk_score >= 40:
            explanation += f"  → Risk score ({risk_score}) indicates potential danger\n"
        explanation += "  → Escalation recommended pending human verification\n"

    elif decision == "REVIEW_REQUIRED":
        explanation += "• REVIEW REQUIRED\n"
        explanation += f"  → Situation is ambiguous — scores are moderate\n"
        explanation += "  → Human review needed before any action is taken\n"

    elif decision == "LOG_AND_MONITOR":
        explanation += "• LOG AND MONITOR\n"
        explanation += f"  → Risk score ({risk_score}) is below action threshold\n"
        explanation += "  → No immediate danger detected — report logged for monitoring\n"

    elif decision == "SUSPECTED_MISUSE":
        explanation += "• SUSPECTED MISUSE FLAGGED\n"
        explanation += "  → User has NOT been blocked (Soft-Prevention Policy)\n"
        explanation += "  → Trust score reduced — future reports monitored more closely\n"
        explanation += "  → If this was a genuine emergency, please resubmit with clear details\n"

    # --------------------------------------------------
    # SYSTEM BASIS
    # --------------------------------------------------

    explanation += "\n==============================\n"
    explanation += "SYSTEM DECISION BASIS\n"
    explanation += "==============================\n"
    explanation += "• Hybrid AI + ML + Rule-based evaluation pipeline\n"
    explanation += "• AI Semantic Engine: spaCy NLP similarity analysis\n"
    explanation += "• ML Classifier: TF-IDF + Logistic Regression model\n"
    explanation += "• Rule Engine: Keyword + score threshold logic\n"
    explanation += "• Soft-Prevention Layer: Trust and misuse tracking\n"

    return explanation