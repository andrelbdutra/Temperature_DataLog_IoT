# src/db.py
from flask import g
from .config import DB_PATH
from typing import Optional
import sqlite3

def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect_db()
    return g.db

def close_db(_exc: Optional[BaseException] = None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def ensure_schema():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ts TEXT NOT NULL,                    -- ISO 8601 UTC (ex: 2025-08-11T16:20:00Z)
            temperature_c REAL NOT NULL,
            humidity_percent REAL,
            battery_v REAL,
            rssi INTEGER,
            UNIQUE (device_id, ts)
        );
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_readings_device_ts ON readings(device_id, ts);")
    db.commit()
    db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    ensure_schema()
