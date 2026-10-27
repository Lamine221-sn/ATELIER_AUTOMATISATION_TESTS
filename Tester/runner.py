"""Exécute les tests, calcule les métriques QoS et retourne un run."""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from .client import ApiClient
from .tests import TESTS, Context

API_NAME = "Frankfurter"
LATENCY_SAMPLES = 5          # appels supplémentaires pour avg/p95
LATENCY_WARN_MS = 800        # seuils d'interprétation
ERROR_RATE_WARN = 0.2


def p95(values):
    """Percentile 95 (méthode du rang le plus proche)."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def run_all(client=None):
    client = client or ApiClient()
    ctx = Context(client)
    results = []
    for fn in TESTS:
        name = fn.__name__.removeprefix("test_")
        try:
            resp = fn(ctx)
            results.append({"name": name, "status": "PASS",
                            "latency_ms": resp["latency_ms"], "details": ""})
        except AssertionError as exc:
            results.append({"name": name, "status": "FAIL",
                            "latency_ms": None, "details": str(exc)})
        except Exception as exc:  # bug inattendu : on l'enregistre, on ne plante pas
            results.append({"name": name, "status": "ERROR",
                            "latency_ms": None, "details": f"{type(exc).__name__}: {exc}"})

    for _ in range(LATENCY_SAMPLES):  # échantillon pour la QoS
        client.get("/latest", {"from": "EUR", "to": "USD"})

    lat = [c["latency_ms"] for c in client.calls if c["error"] is None]
    total = len(results)
    failed = sum(1 for t in results if t["status"] != "PASS")
    bad_calls = [c for c in client.calls
                 if c["error"] or c["status"] == 429 or (c["status"] or 0) >= 500]
    summary = {
        "passed": total - failed,
        "failed": failed,
        "error_rate": round(failed / total, 3) if total else 0,
        "http_error_rate": round(len(bad_calls) / len(client.calls), 3) if client.calls else 1,
        "latency_ms_avg": round(sum(lat) / len(lat), 1) if lat else None,
        "latency_ms_p95": round(p95(lat), 1) if lat else None,
        "requests": len(client.calls),
        "available": any(c["error"] is None and (c["status"] or 0) < 500 for c in client.calls),
    }
    summary["verdict"] = interpret(summary)
    return {
        "api": API_NAME,
        "timestamp": datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds"),
        "summary": summary,
        "tests": results,
    }


def interpret(s):
    """Interprétation lisible des métriques QoS."""
    if not s["available"]:
        return "API indisponible lors de ce run."
    notes = []
    if s["failed"]:
        notes.append(f"{s['failed']} test(s) en échec : contrat à vérifier")
    if s["http_error_rate"] > 0:
        notes.append("erreurs réseau / 5xx / 429 observées")
    if s["latency_ms_p95"] and s["latency_ms_p95"] > LATENCY_WARN_MS:
        notes.append(f"latence p95 élevée (> {LATENCY_WARN_MS} ms)")
    if s["error_rate"] > ERROR_RATE_WARN:
        notes.append("taux d'échec élevé")
    return "Service sain : contrat respecté, latence correcte." if not notes else "; ".join(notes) + "."
