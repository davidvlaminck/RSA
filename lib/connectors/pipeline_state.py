import sqlite3
from datetime import datetime, timezone


class PipelineState:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def get(self) -> dict | None:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT phase, status, updated_at, message FROM pipeline_state WHERE id = 1"
            ).fetchone()
            return dict(row) if row else None

    def get_history(self, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT phase, status, updated_at, message FROM pipeline_state_history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
