# src/__init__.py
from flask import Flask
from .config import STATIC_DIR, DB_PATH
from .db import init_app as init_db
from .routes.api import bp as api_bp
from .routes.web import bp as web_bp

def create_app():
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

    # DB (schema + teardown)
    init_db(app)

    # Blueprints (API e páginas)
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    print(f"DB em: {DB_PATH.resolve()}")
    return app
