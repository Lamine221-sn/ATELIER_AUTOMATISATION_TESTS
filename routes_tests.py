"""Blueprint : /run, /dashboard, /health, /export.json.
À brancher dans flask_app.py (2 lignes, voir README)."""
from datetime import datetime

from flask import Blueprint, jsonify, render_template

import storage
from tester.runner import run_all

bp = Blueprint("tests_api", __name__)
MIN_INTERVAL_S = 300  # anti-spam : 1 run toutes les 5 minutes maximum


def _age_seconds(run):
    return (datetime.now(datetime.fromisoformat(run["timestamp"]).tzinfo)
            - datetime.fromisoformat(run["timestamp"])).total_seconds()


@bp.get("/run")
def run_tests():
    last = storage.last_run()
    if last and _age_seconds(last) < MIN_INTERVAL_S:
        wait = int(MIN_INTERVAL_S - _age_seconds(last))
        response = jsonify({"error": "trop de runs", "retry_after_s": wait})
        response.status_code = 429
        response.headers["Retry-After"] = str(wait)
        return response
    run = run_all()
    storage.save_run(run)
    return jsonify(run)


def _trend_points(runs, key, width=600, height=120):
    """Points SVG (polyline) d'une métrique, du plus ancien au plus récent."""
    values = [r["summary"][key] for r in reversed(runs) if r["summary"][key] is not None]
    if len(values) < 2:
        return ""
    top = max(values) or 1
    step = width / (len(values) - 1)
    return " ".join(f"{i * step:.1f},{height - (v / top) * (height - 10) - 5:.1f}"
                    for i, v in enumerate(values))


@bp.get("/dashboard")
def dashboard():
    runs = storage.list_runs(30)
    return render_template(
        "dashboard.html",
        last=runs[0] if runs else None,
        runs=runs,
        latency_trend=_trend_points(runs, "latency_ms_p95"),
        error_trend=_trend_points(runs, "error_rate"),
    )


@bp.get("/health")
def health():
    last = storage.last_run()
    return jsonify({
        "status": "ok",
        "db": True,
        "last_run": last["timestamp"] if last else None,
        "last_run_available": last["summary"]["available"] if last else None,
    })


@bp.get("/export.json")
def export_json():
    response = jsonify(storage.list_runs(200))
    response.headers["Content-Disposition"] = "attachment; filename=runs.json"
    return response
