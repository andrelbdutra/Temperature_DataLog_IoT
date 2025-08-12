# src/routes/web.py
from flask import Blueprint, send_from_directory
from ..config import STATIC_DIR

bp = Blueprint("web", __name__)

@bp.get("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")

# evitar 404 de favicon nos logs
@bp.get("/favicon.ico")
def favicon():
    return "", 204
