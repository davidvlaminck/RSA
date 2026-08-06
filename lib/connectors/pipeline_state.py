import os
import sqlite3
from datetime import datetime, timezone


class PipelineState:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def ensure(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_state (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    phase TEXT,
                    status TEXT,
                    updated_at DATETIME,
                    message TEXT
                )
            """)
            conn.execute(
                "INSERT OR IGNORE INTO pipeline_state (id, phase, status, updated_at, message) VALUES (?, ?, ?, ?, ?)",
                (1, "idle", "completed", _now(), ""),
            )
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_state_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phase TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at DATETIME NOT NULL,
                    message TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pipeline_history_phase_status
                ON pipeline_state_history(phase, status, updated_at DESC)
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_pipeline_state_history
                AFTER UPDATE ON pipeline_state
                FOR EACH ROW
                WHEN OLD.phase != NEW.phase OR OLD.status != NEW.status
                BEGIN
                    INSERT INTO pipeline_state_history (phase, status, updated_at, message)
                    VALUES (OLD.phase, OLD.status, OLD.updated_at, OLD.message);
                END
            """)
            conn.commit()

    def get(self) -> dict | None:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT phase, status, updated_at, message FROM pipeline_state WHERE id = 1"
            ).fetchone()
            return dict(row) if row else None

    def update(self, phase: str, status: str, message: str = ""):
        with self._conn() as conn:
            conn.execute(
                "UPDATE pipeline_state SET phase = ?, status = ?, updated_at = ?, message = ? WHERE id = 1",
                (phase, status, _now(), message),
            )
            conn.commit()

    def get_history(self, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT phase, status, updated_at, message FROM pipeline_state_history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
