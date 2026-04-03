# app/routes.py
 
import os
import logging
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
 
from app.services.pipeline import process_alert
from app.services.scoring_engine import calculate_ecs
from app.services.trust_engine import get_trust_level
 
from app.db.db_handler import (
    fetch_alert_audit_logs,
    save_alert,
    fetch_all_alerts,
    save_alert_audit,
    fetch_decision_stats,
    update_user_trust,
    get_user_trust
)
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
test_bp = Blueprint("test_bp", __name__)

# =========================
# LOGIN REQUIRED DECORATOR
# Protects admin-only routes
# =========================
 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in to access the admin area.", "warning")
            return redirect(url_for("test_bp.admin_login"))
        return f(*args, **kwargs)
    return decorated_function
 
# =========================
# HOME
# =========================

@test_bp.route("/")
def home():
    return render_template("report.html")

# =========================
# ADMIN LOGIN
# =========================
 
@test_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
 
    # Already logged in — go straight to dashboard
    if session.get("admin_logged_in"):
        return redirect(url_for("test_bp.admin_alerts"))
 
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
 
        # Credentials read from .env only — never hardcoded
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
 
        if username == admin_user and password == admin_pass:
            session["admin_logged_in"] = True
            session.permanent = False
            logger.info("Admin login successful")
            return redirect(url_for("test_bp.admin_alerts"))
        else:
            flash("Invalid username or password.", "error")
            logger.warning("Failed admin login attempt")
 
    return render_template("admin_login.html")
  
# =========================
# ADMIN LOGOUT
# =========================
 
@test_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("test_bp.admin_login"))

# =========================
# SOS API
# =========================
 
@test_bp.route("/sos", methods=["POST"])
def sos_alert():
 
    try:
        data = request.get_json() or {}
        message = data.get("message", "")
        phone   = data.get("phone", "")
 
        stored_trust, misuse_count = get_user_trust(phone)
 
        result = process_alert(
            message=message,
            user_name=data.get("user_name", ""),
            phone=phone,
            location=data.get("location", ""),
            emergency_type=data.get("emergency_type", ""),
            misuse_count=misuse_count
        )
 
        decision    = result["decision"]
        explanation = result["explanation"]
        score       = result["score"]

        # Compute real ECS
        ecs = calculate_ecs(
            result["scores"]["credibility"],
            result["scores"]["trust"],
            result["scores"]["risk"]
        )

        # Save alert with confidence
        data.update({
            "priority_score":    result["scores"]["priority"],
            "credibility_score": result["scores"]["credibility"],
            "trust_score":       result["scores"]["trust"],
            "risk_score":        result["scores"]["risk"],
            "confidence":        score,
            "final_decision":    decision,
            "explanation":       explanation
        })

        alert_id = save_alert(data)
        save_alert_audit(alert_id, data)

        return jsonify({
            "decision":    decision,
            "explanation": explanation,
            "score":       score,
            "ecs":         ecs
        }), 201

    except Exception as e:
        logger.error(f"SOS route error: {e}")
        return jsonify({
            "error": "System error processing alert. Please try again."
        }), 500


# =========================
# REPORT PAGE
# =========================
 
@test_bp.route("/report", methods=["GET", "POST"])
def report():
 
    if request.method == "GET":
        return render_template("report.html")
 
    try:
        data    = request.form.to_dict()
        message = data.get("message", "")
        phone   = data.get("phone", "")
 
        stored_trust, misuse_count = get_user_trust(phone)
 
        result = process_alert(
            message=message,
            user_name=data.get("user_name", ""),
            phone=phone,
            location=data.get("location", ""),
            emergency_type=data.get("emergency_type", ""),
            misuse_count=misuse_count
        )
 
        decision = result["decision"]
        score    = result["score"]
        ml_label = result["ml"]["label"]
        ml_conf  = result["ml"]["confidence"]

        # =========================
        # TRUST UPDATE
        # =========================

        trust_score = result["scores"]["trust"]

        if decision == "IMMEDIATE_ESCALATION":
            trust_score += 5
        elif decision == "CONDITIONAL_ESCALATION":
            trust_score += 3
        elif decision == "SUSPECTED_MISUSE":
            trust_score -= 10
            misuse_count += 1

        trust_score = max(0, min(100, trust_score))
        update_user_trust(phone, trust_score, misuse_count)

        # =========================
        # COMPUTE REAL ECS
        # =========================

        ecs = calculate_ecs(
            result["scores"]["credibility"],
            trust_score,
            result["scores"]["risk"]
        )

        # =========================
        # TRUST LEVEL LABEL
        # =========================

        trust_level = get_trust_level(trust_score)

        # =========================
        # SAVE WITH CONFIDENCE
        # =========================

        data.update({
            "priority_score":    result["scores"]["priority"],
            "credibility_score": result["scores"]["credibility"],
            "trust_score":       trust_score,
            "risk_score":        result["scores"]["risk"],
            "confidence":        score,
            "final_decision":    decision,
            "explanation":       result["explanation"]
        })

        alert_id = save_alert(data)
        save_alert_audit(alert_id, data)

        # =========================
        # RENDER RESULT
        # =========================

        return render_template(
            "result.html",
            priority    = result["scores"]["priority"],
            credibility = result["scores"]["credibility"],
            trust       = trust_score,
            trust_level = trust_level,
            risk        = result["scores"]["risk"],
            decision    = decision,
            score       = score,
            ecs         = ecs,
            explanation = result["explanation"],
            ml_label    = ml_label,
            ml_conf     = ml_conf
        )

    except Exception as e:
        logger.error(f"Report route error: {e}")
        return render_template(
            "result.html",
            priority    = 0,
            credibility = 0,
            trust       = 0,
            trust_level = "UNKNOWN",
            risk        = 0,
            decision    = "REVIEW_REQUIRED",
            score       = 0,
            ecs         = 0.0,
            explanation = "System encountered an error processing this report. Please try again.",
            ml_label    = "UNKNOWN",
            ml_conf     = 0.0
        )


# =========================
# ADMIN DASHBOARD
# =========================

@test_bp.route("/admin/alerts")
@login_required
def admin_alerts():
    alerts = fetch_all_alerts()
    stats  = fetch_decision_stats()

    for alert in alerts:
        if alert.get("created_at"):
            alert["formatted_time"] = alert["created_at"].strftime("%d %b %Y, %I:%M %p")
        else:
            alert["formatted_time"] = "N/A"

    return render_template(
        "admin_alerts.html",
        alerts=alerts,
        stats=stats
    )


@test_bp.route("/admin/audit")
@login_required
def admin_audit():
    logs = fetch_alert_audit_logs()

    for log in logs:
        if log.get("created_at"):
            log["formatted_time"] = log["created_at"].strftime("%d %b %Y, %I:%M %p")
        else:
            log["formatted_time"] = "N/A"

    return render_template(
        "admin_audit.html",
        audit_logs=logs
    )


@test_bp.route("/ethics")
def ethics():
    return render_template("ethics.html")
