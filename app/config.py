# app/config.py

"""
APPLICATION CONFIGURATION
Intelligent Emergency Alert System
------------------------------------

Loads settings from environment variables.
Falls back to safe defaults for development.

"""

import os

# Load .env file if it exists
# Install with: pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed — falls back to os.getenv defaults


def _safe_int(value: str, default: int) -> int:
    """Safely converts string to int. Returns default if invalid."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class Config:

    # Flask secret key — used for session signing
    # Set this to a strong random value in your .env file
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )

    # Database configuration
    # All values read from environment variables or .env file
    # Password has empty default — must be set in .env
    DB_CONFIG = {
        "host":     os.getenv("DB_HOST",     "localhost"),
        "user":     os.getenv("DB_USER",     "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME",     "emergency_alert_db"),
        "port":     _safe_int(os.getenv("DB_PORT", "3306"), 3306),
    }