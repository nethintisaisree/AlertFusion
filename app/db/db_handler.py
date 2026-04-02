# app/db/db_handler.py

import logging
from app.models import get_db_connection
from app.services.trust_engine import BASE_TRUST

logger = logging.getLogger(__name__)


# =========================================================
# CONNECTION SAFETY
# =========================================================

def _get_connection_or_raise():
    conn = get_db_connection()

    if conn is None:
        logger.error("Database connection failed")
        raise ConnectionError("Database connection failed.")

    return conn


# =========================================================
# SAVE ALERT
# =========================================================

def save_alert(data):
    conn = _get_connection_or_raise()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO alerts (
                user_name,
                phone,
                location,
                emergency_type,
                message,
                priority_score,
                credibility_score,
                trust_score,
                risk_score,
                confidence_score,
                final_decision,
                explanation
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            data.get("user_name"),
            data.get("phone"),
            data.get("location"),
            data.get("emergency_type"),
            data.get("message"),
            data.get("priority_score"),
            data.get("credibility_score"),
            data.get("trust_score"),
            data.get("risk_score"),
            data.get("confidence"),
            data.get("final_decision"),
            data.get("explanation"),
        )

        cursor.execute(query, values)
        conn.commit()

        alert_id = cursor.lastrowid
        logger.info(f"Alert saved — ID: {alert_id}")
        return alert_id

    finally:
        cursor.close()
        conn.close()


# =========================================================
# SAVE AUDIT LOG
# =========================================================

def save_alert_audit(alert_id, data):
    conn = _get_connection_or_raise()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO alert_audit (
                alert_id,
                priority_score,
                credibility_score,
                trust_score,
                risk_score,
                confidence_score,
                final_decision,
                explanation,
                user_name,
                phone
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            alert_id,
            data.get("priority_score"),
            data.get("credibility_score"),
            data.get("trust_score"),
            data.get("risk_score"),
            data.get("confidence"),
            data.get("final_decision"),
            data.get("explanation"),
            data.get("user_name"),
            data.get("phone"),
        )

        cursor.execute(query, values)
        conn.commit()
        logger.info(f"Audit saved for alert ID: {alert_id}")

    finally:
        cursor.close()
        conn.close()


# =========================================================
# TRUST FETCH
# Now uses BASE_TRUST from trust_engine for consistency
# Added try/except — no more crash on DB failure
# Uses INSERT IGNORE to handle duplicate phone safely
# =========================================================

def get_user_trust(phone):
    try:
        connection = _get_connection_or_raise()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT trust_score, misuse_count FROM user_trust WHERE phone = %s",
                (phone,)
            )
            result = cursor.fetchone()

            if result:
                return result["trust_score"], result["misuse_count"]

            # New user — INSERT IGNORE handles race condition safely
            cursor.execute(
                "INSERT IGNORE INTO user_trust (phone, trust_score, misuse_count) VALUES (%s, %s, %s)",
                (phone, BASE_TRUST, 0)
            )
            connection.commit()
            return BASE_TRUST, 0

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        logger.error(f"get_user_trust failed for phone {phone}: {e}")
        return BASE_TRUST, 0   # safe fallback — never crash the route


# =========================================================
# TRUST UPDATE
# Added try/except — no more crash on DB failure
# =========================================================

def update_user_trust(phone, trust_score, misuse_count):
    try:
        connection = _get_connection_or_raise()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                UPDATE user_trust
                SET trust_score  = %s,
                    misuse_count = %s
                WHERE phone = %s
                """,
                (trust_score, misuse_count, phone)
            )
            connection.commit()
            logger.info(f"Trust updated for {phone}: score={trust_score}, misuse={misuse_count}")

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        logger.error(f"update_user_trust failed for phone {phone}: {e}")


# =========================================================
# FETCH ALL ALERTS
# =========================================================

def fetch_all_alerts():
    conn = _get_connection_or_raise()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# =========================================================
# FETCH AUDIT LOGS
# =========================================================

def fetch_alert_audit_logs():
    conn = _get_connection_or_raise()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM alert_audit ORDER BY audit_id DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# =========================================================
# FETCH DECISION STATS
# Fixed: unknown labels no longer crash with KeyError
# =========================================================

def fetch_decision_stats():
    conn = _get_connection_or_raise()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT final_decision, COUNT(*) as count
            FROM alert_audit
            GROUP BY final_decision
            """
        )
        result = cursor.fetchall()

        # Default all to 0
        stats = {
            "IMMEDIATE_ESCALATION":   0,
            "CONDITIONAL_ESCALATION": 0,
            "REVIEW_REQUIRED":        0,
            "LOG_AND_MONITOR":        0,
            "SUSPECTED_MISUSE":       0
        }

        for row in result:
            label = row["final_decision"]
            if label in stats:
                stats[label] = row["count"]
            else:
                # Unknown label — log it but don't crash
                logger.warning(f"Unknown decision label in DB: {label}")

        return stats

    finally:
        cursor.close()
        conn.close()