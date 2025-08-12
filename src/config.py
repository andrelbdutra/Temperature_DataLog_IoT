# src/config.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH      = PROJECT_ROOT / "datalog.db"
STATIC_DIR   = PROJECT_ROOT / "static"

DEFAULT_LIMIT = 240  # pontos no gráfico (últimos N timestamps)
