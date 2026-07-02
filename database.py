import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

DB_FILE = DB_DIR / "voreenth.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_FILE)


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                prompt TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                severity TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                decision TEXT NOT NULL,
                categories TEXT NOT NULL,
                reasons TEXT NOT NULL,
                model_used TEXT,
                response_preview TEXT
            )
            """
        )


def insert_request(
    prompt: str,
    risk_score: int,
    severity: str,
    risk_level: str,
    decision: str,
    categories: str,
    reasons: str,
    model_used: str = "",
    response_preview: str = "",
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO requests
            (prompt, risk_score, severity, risk_level, decision, categories, reasons, model_used, response_preview)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt,
                risk_score,
                severity,
                risk_level,
                decision,
                categories,
                reasons,
                model_used,
                response_preview,
            ),
        )


def get_request_history(limit: int = 100) -> List[Tuple]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                timestamp,
                prompt,
                risk_score,
                severity,
                risk_level,
                decision,
                categories,
                reasons,
                model_used,
                response_preview
            FROM requests
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows


def get_dashboard_metrics() -> Dict[str, float]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        allowed = conn.execute("SELECT COUNT(*) FROM requests WHERE decision='ALLOW'").fetchone()[0]
        blocked = conn.execute("SELECT COUNT(*) FROM requests WHERE decision='BLOCK'").fetchone()[0]
        avg_risk = conn.execute("SELECT COALESCE(AVG(risk_score), 0) FROM requests").fetchone()[0]
        critical = conn.execute("SELECT COUNT(*) FROM requests WHERE risk_level='Critical'").fetchone()[0]

    return {
        "total": total,
        "allowed": allowed,
        "blocked": blocked,
        "avg_risk": round(avg_risk, 1),
        "critical": critical,
    }


def reset_history() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM requests")
