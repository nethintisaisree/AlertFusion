# app/__init__.py

from flask import Flask
from app.routes import test_bp
from app.config import Config


def create_app():

    app = Flask(__name__)

    # Load all config from Config class (reads from .env via config.py)
    # SECRET_KEY, DB_CONFIG etc. all come from here
    # DO NOT hardcode SECRET_KEY here — it overrides the .env value
    app.config.from_object(Config)

    app.register_blueprint(test_bp)

    return app