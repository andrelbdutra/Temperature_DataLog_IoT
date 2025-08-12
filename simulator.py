from __future__ import annotations
import time, random, argparse, json
from datetime import datetime, timezone
import requests

def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def rnd_walk(prev: float, step=0.3, low=20.0, high=32.0) -> float:
    """Passeio aleatório suave, limitado em [low, high]."""
    val = prev + random.uniform(-step, step)
    return max(low, min(high, val))

def main():
    ap = argparse.ArgumentParser(description="ESP32 Simulator (DHT11)")
    ap.add_argument("--device-id", default="ESP32_SIM")
    ap.add_argument("--api", default="http://127.0.0.1:5000")
    ap.add_argument("--interval", type=int, default=60, help="segundos entre leituras (padrão 60)")
    ap.add_argument("--token", default="", help="Bearer token (opcional)")
    ap.add_argument("--print-only", action="store_true", help="não postar, apenas imprimir JSON")
    args = ap.parse_args()

    temp = 26.0
    hum  = 55.0

    headers = {"Content-Type": "application/json"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    endpoint = f"{args.api}/api/v1/devices/{args.device_id}/readings"

    print(f"Simulando {args.device_id} → {endpoint} (intervalo {args.interval}s)")
    while True:
        temp = rnd_walk(temp)
        hum  = max(30.0, min(80.0, hum + random.uniform(-1.0, 1.0)))

        payload = {
            "ts": utc_now_iso(),
            "temperature_c": round(temp, 1),  
            "humidity_percent": int(round(hum))
        }
        print("Payload:", json.dumps(payload))

        if not args.print_only:
            try:
                r = requests.post(endpoint, headers=headers, json=payload, timeout=10)
                print("HTTP", r.status_code, r.text)
            except Exception as e:
                print("POST erro:", e)

        time.sleep(args.interval)

if __name__ == "__main__":
    main()
