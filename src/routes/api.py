# src/routes/api.py
from flask import Blueprint, request, jsonify, Response
from datetime import datetime, timezone
from ..db import get_db
from ..utils import utc_now_iso, parse_iso
from ..config import DEFAULT_LIMIT

bp = Blueprint("api", __name__, url_prefix="/api/v1")

@bp.get("/health")
def health():
    return {"status": "ok", "time": utc_now_iso()}

@bp.post("/devices/<device_id>/readings")
def ingest(device_id):
    """
    Espera JSON:
    {
      "ts": "2025-08-11T16:20:00Z",  # opcional: se ausente, servidor carimba
      "temperature_c": 24.7,         # obrigatório
      "humidity_percent": 61,        # opcional
      "battery_v": 3.72,             # opcional
      "rssi": -58                    # opcional
    }
    """
    data = request.get_json(silent=True) or {}
    ts = data.get("ts") or utc_now_iso()
    temperature = data.get("temperature_c")
    if temperature is None:
        return jsonify({"error": "temperature_c is required"}), 400
    if not parse_iso(ts):
        return jsonify({"error": "ts must be ISO-8601 (ex: 2025-08-11T16:20:00Z)"}), 400

    humidity = data.get("humidity_percent")
    battery_v = data.get("battery_v")
    rssi = data.get("signal_rssi") or data.get("rssi")

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO readings(device_id, ts, temperature_c, humidity_percent, battery_v, rssi)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (device_id, ts, float(temperature),
          float(humidity) if humidity is not None else None,
          float(battery_v) if battery_v is not None else None,
          int(rssi) if rssi is not None else None))
    db.commit()
    created = (cur.rowcount == 1)
    return jsonify({"status": "ok", "device_id": device_id, "ts": ts, "created": created}), (201 if created else 200)

@bp.get("/devices/<device_id>/readings")
def list_readings(device_id):
    """
    Query params:
      - limit (int, default 120)
      - since (ISO-8601) opcional
      - until (ISO-8601) opcional
    """
    limit = int(request.args.get("limit", 120))
    since = parse_iso(request.args.get("since"))
    until = parse_iso(request.args.get("until"))

    clauses = ["device_id = ?"]
    params = [device_id]
    if since:
        clauses.append("ts >= ?")
        params.append(since.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"))
    if until:
        clauses.append("ts <= ?")
        params.append(until.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"))
    where = " AND ".join(clauses)

    rows = get_db().execute(
        f"SELECT ts, temperature_c, humidity_percent, battery_v, rssi "
        f"FROM readings WHERE {where} ORDER BY ts ASC LIMIT ?",
        (*params, limit)
    ).fetchall()

    return jsonify([dict(r) for r in rows])

@bp.get("/readings/aggregate")
def readings_aggregate():
    """
    Retorna série única agregada por timestamp (média),
    com epoch_ms para facilitar plotagem.
    ?limit=N (padrão DEFAULT_LIMIT) -> últimos N pontos
    """
    limit = int(request.args.get("limit", DEFAULT_LIMIT))
    rows = get_db().execute(
        "SELECT ts, AVG(temperature_c) AS temperature_c, COUNT(*) AS n "
        "FROM readings GROUP BY ts ORDER BY ts DESC LIMIT ?",
        (limit,)
    ).fetchall()

    out = []
    for r in rows[::-1]:  # inverter para ordem cronológica ascendente
        ts_iso = r["ts"]
        try:
            ts_dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
            epoch_ms = int(ts_dt.timestamp() * 1000)
        except Exception:
            epoch_ms = None
        out.append({
            "ts": ts_iso,
            "epoch_ms": epoch_ms,
            "temperature_c": float(r["temperature_c"]) if r["temperature_c"] is not None else None,
            "n": int(r["n"])
        })
    return jsonify(out)

@bp.get("/readings/latest")
def readings_latest():
    row = get_db().execute(
        "SELECT ts, temperature_c, device_id FROM readings ORDER BY ts DESC LIMIT 1"
    ).fetchone()
    return jsonify({} if not row else dict(row))

@bp.get("/export.csv")
def export_csv():
    rows = get_db().execute(
        "SELECT device_id, ts, temperature_c, humidity_percent, battery_v, rssi "
        "FROM readings ORDER BY ts ASC"
    ).fetchall()

    def generate():
        yield "device_id,ts,temperature_c,humidity_percent,battery_v,rssi\n"
        for r in rows:
            yield f'{r["device_id"]},{r["ts"]},{r["temperature_c"]},{r["humidity_percent"] or ""},{r["battery_v"] or ""},{r["rssi"] or ""}\n'

    return Response(generate(), mimetype="text/csv")
