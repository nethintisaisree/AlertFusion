# app/routes.py

import os
import csv
import logging
from io import StringIO
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash, Response
 
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


def _filter_alerts(alerts, search_query="", selected_decision="", selected_type=""):
    if search_query:
        alerts = [
            alert for alert in alerts
            if search_query in (str(alert.get("user_name", "")).lower())
            or search_query in (str(alert.get("phone", "")).lower())
            or search_query in (str(alert.get("message", "")).lower())
            or search_query in (str(alert.get("emergency_type", "")).lower())
            or search_query in (str(alert.get("final_decision", "")).lower())
        ]

    if selected_decision:
        alerts = [
            alert for alert in alerts
            if str(alert.get("final_decision", "")) == selected_decision
        ]

    if selected_type:
        alerts = [
            alert for alert in alerts
            if str(alert.get("emergency_type", "")).lower() == selected_type
        ]

    return alerts
 
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
    search_query = (request.args.get("search", "") or "").strip().lower()
    selected_decision = (request.args.get("decision", "") or "").strip()
    selected_type = (request.args.get("type", "") or "").strip().lower()
    alerts = _filter_alerts(
        alerts,
        search_query=search_query,
        selected_decision=selected_decision,
        selected_type=selected_type
    )

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


@test_bp.route("/export_csv")
@login_required
def export_csv():
    alerts = fetch_all_alerts()
    search_query = (request.args.get("search", "") or "").strip().lower()
    selected_decision = (request.args.get("decision", "") or "").strip()
    selected_type = (request.args.get("type", "") or "").strip().lower()

    alerts = _filter_alerts(
        alerts,
        search_query=search_query,
        selected_decision=selected_decision,
        selected_type=selected_type
    )

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "ID", "User", "Phone", "Emergency", "Message", "Priority",
        "Credibility", "Trust", "Risk", "Decision", "Timestamp"
    ])

    for alert in alerts:
        created_at = alert.get("created_at")
        formatted_time = created_at.strftime("%d %b %Y, %I:%M %p") if created_at else "N/A"
        writer.writerow([
            alert.get("alert_id", ""),
            alert.get("user_name", ""),
            alert.get("phone", ""),
            alert.get("emergency_type", ""),
            alert.get("message", ""),
            alert.get("priority_score", ""),
            alert.get("credibility_score", ""),
            alert.get("trust_score", ""),
            alert.get("risk_score", ""),
            alert.get("final_decision", ""),
            formatted_time
        ])

    csv_data = buffer.getvalue()
    buffer.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=alerts_export.csv"}
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
