# run.py

"""
APPLICATION ENTRY POINT
Intelligent Emergency Alert System
------------------------------------

Start the app with:
    python run.py

Environment variables (set in .env):
    FLASK_DEBUG=true    — enables debug mode (development only)
    FLASK_PORT=5000     — port to run on (default 5000)
"""

import os
import logging

# ======================================================
# LOGGING CONFIGURATION
# Configured once here — applies to entire application
# All modules use logging.getLogger(__name__)
# ======================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# ======================================================
# LOAD .env BEFORE ANYTHING ELSE
# ======================================================

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ======================================================
# CREATE AND RUN APP
# ======================================================

from app import create_app

app = create_app()

if __name__ == "__main__":

    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port       = int(os.getenv("FLASK_PORT", "5000"))

    logger.info(f"Starting Intelligent Emergency Alert System")
    logger.info(f"Debug mode : {debug_mode}")
    logger.info(f"Port       : {port}")
    logger.info(f"URL        : http://localhost:{port}")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )