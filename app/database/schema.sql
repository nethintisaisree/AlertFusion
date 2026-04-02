-- =====================================================
-- INTELLIGENT EMERGENCY ALERT SYSTEM
-- DATABASE SCHEMA
-- =====================================================
-- Run this file once to set up all tables.
-- Safe to re-run — uses CREATE TABLE IF NOT EXISTS.
-- =====================================================


-- =====================================================
-- ALERTS TABLE
-- Main record of every emergency report submitted.
-- =====================================================

CREATE TABLE IF NOT EXISTS alerts (
    alert_id          INT           AUTO_INCREMENT PRIMARY KEY,
    user_name         VARCHAR(100),
    phone             VARCHAR(20),
    location          VARCHAR(100),
    emergency_type    VARCHAR(50),
    message           TEXT,
    priority_score    INT,
    credibility_score INT,
    trust_score       INT,
    risk_score        INT,
    confidence_score  DECIMAL(5,2),         -- float precision (e.g. 87.50)
    final_decision    VARCHAR(50),
    explanation       TEXT,
    ml_label          VARCHAR(50),           -- ML model prediction label
    ai_label          VARCHAR(50),           -- AI semantic engine label
    prevention_flag   VARCHAR(20) DEFAULT 'ALLOW',  -- ALLOW / FLAG / MONITOR
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for faster lookups
    INDEX idx_alerts_phone          (phone),
    INDEX idx_alerts_final_decision (final_decision),
    INDEX idx_alerts_created_at     (created_at)
);


-- =====================================================
-- AUDIT TABLE
-- Full traceability record for every processed alert.
-- Linked to alerts via alert_id foreign key.
-- =====================================================

CREATE TABLE IF NOT EXISTS alert_audit (
    audit_id          INT  AUTO_INCREMENT PRIMARY KEY,
    alert_id          INT,
    priority_score    INT,
    credibility_score INT,
    trust_score       INT,
    risk_score        INT,
    confidence_score  DECIMAL(5,2),         -- float precision
    final_decision    VARCHAR(50),
    explanation       TEXT,
    ml_label          VARCHAR(50),           -- ML prediction stored for audit
    user_name         VARCHAR(100),
    phone             VARCHAR(20),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key to alerts table
    FOREIGN KEY (alert_id)
        REFERENCES alerts(alert_id)
        ON DELETE CASCADE,

    -- Indexes for dashboard performance
    INDEX idx_audit_final_decision (final_decision),
    INDEX idx_audit_phone          (phone),
    INDEX idx_audit_alert_id       (alert_id)
);


-- =====================================================
-- USER TRUST TABLE
-- Tracks trust score and misuse count per phone number.
-- Base trust aligned with trust_engine.py BASE_TRUST = 60
-- =====================================================

CREATE TABLE IF NOT EXISTS user_trust (
    phone         VARCHAR(20)  PRIMARY KEY,
    trust_score   INT          DEFAULT 60,   -- matches BASE_TRUST in trust_engine.py
    misuse_count  INT          DEFAULT 0,
    last_updated  TIMESTAMP
                  DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP
);