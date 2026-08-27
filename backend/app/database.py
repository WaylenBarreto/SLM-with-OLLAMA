import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "benchmark.sqlite"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            config_json TEXT NOT NULL,
            hardware_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES runs(id),
            model TEXT NOT NULL,
            prompt_id TEXT NOT NULL,
            repetition INTEGER NOT NULL,
            response TEXT,
            status TEXT NOT NULL,
            error TEXT,
            metrics_json TEXT NOT NULL,
            evaluation_json TEXT NOT NULL
        );
        """)


def create_run(run_id: str, config: dict, hardware: dict) -> None:
    with connect() as db:
        db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?)", (run_id, "running", datetime.now(timezone.utc).isoformat(), json.dumps(config), json.dumps(hardware)))


def update_status(run_id: str, status: str) -> None:
    with connect() as db:
        db.execute("UPDATE runs SET status = ? WHERE id = ?", (status, run_id))


def add_result(run_id: str, result: dict) -> None:
    with connect() as db:
        db.execute("INSERT INTO results (run_id, model, prompt_id, repetition, response, status, error, metrics_json, evaluation_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (run_id, result["model"], result["prompt_id"], result["repetition"], result.get("response"), result["status"], result.get("error"), json.dumps(result.get("metrics", {})), json.dumps(result.get("evaluation", {}))))


def get_run(run_id: str) -> dict | None:
    with connect() as db:
        run = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            return None
        results = db.execute("SELECT * FROM results WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
        return {"id": run["id"], "status": run["status"], "created_at": run["created_at"], "config": json.loads(run["config_json"]), "hardware": json.loads(run["hardware_json"]), "results": [{**dict(item), "metrics": json.loads(item["metrics_json"]), "evaluation": json.loads(item["evaluation_json"])} for item in results]}


def list_runs() -> list[dict]:
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT id, status, created_at, config_json FROM runs ORDER BY created_at DESC").fetchall()]
