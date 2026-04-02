# app/models.py

"""
DATABASE CONNECTION MANAGER
Intelligent Emergency Alert System
------------------------------------

Handles MySQL connection with:
  • Named logger (no duplicate log entries)
  • Lazy config loading (reads after .env is loaded)
  • Single retry on failure (handles startup race conditions)
  • Timeout protection (5 seconds)
"""

import mysql.connector
import logging

logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Returns a live MySQL connection or None if connection fails.

    Attempts connection twice — handles temporary DB unavailability
    during app startup without crashing.
    """

    # Lazy import — reads config after dotenv has loaded
    from app.config import Config

    attempts = 2

    for attempt in range(1, attempts + 1):
        try:
            connection = mysql.connector.connect(
                **Config.DB_CONFIG,
                connection_timeout=5
            )

            if connection.is_connected():
                return connection

        except mysql.connector.Error as err:
            if attempt < attempts:
                logger.warning(f"DB connection attempt {attempt} failed — retrying... ({err})")
            else:
                logger.error(f"Database connection failed after {attempts} attempts: {err}")

    return None