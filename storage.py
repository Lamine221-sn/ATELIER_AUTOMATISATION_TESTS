"""Stockage SQLite de l'historique des runs."""
import json
import os
import sqlite3

DB_PATH = os.environ.get("RUNS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs.db"))


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        api TEXT NOT NULL,
        passed INTEGER, failed INTEGER,
        error_rate REAL, latency_avg REAL, latency_p95 REAL,
        available INTEGER,
        payload TEXT NOT NULL)""")
    return conn


def save_run(run):
    s = run["summary"]
    with _conn() as c:
        c.execute("""INSERT INTO runs (timestamp, api, passed, failed, error_rate,
                     latency_avg, latency_p95, available, payload)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (run["timestamp"], run["api"], s["passed"], s["failed"], s["error_rate"],
                   s["latency_ms_avg"], s["latency_ms_p95"], int(s["available"]),
                   json.dumps(run)))


def list_runs(limit=50):
    """Les `limit` derniers runs, du plus récent au plus ancien (JSON complet)."""
    with _conn() as c:
        rows = c.execute("SELECT payload FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(r["payload"]) for r in rows]


def last_run():
    runs = list_runs(1)
    return runs[0] if runs else None
