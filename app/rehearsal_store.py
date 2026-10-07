"""리허설 세션 저장 (서버가 재시작돼도 이어서 진행 가능하도록 SQLite 사용)."""
import json
import sqlite3
import time
import uuid
from pathlib import Path


class RehearsalStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS rehearsals (
                    id TEXT PRIMARY KEY, scenario_id TEXT, contact_id INTEGER,
                    status TEXT, report TEXT, created REAL
                );
                CREATE TABLE IF NOT EXISTS rehearsal_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT, role TEXT, content TEXT, created REAL
                );
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def create(self, scenario_id: str, contact_id: int | None) -> str:
        session_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute("INSERT INTO rehearsals VALUES (?,?,?,?,?,?)",
                       (session_id, scenario_id, contact_id, "active", None, time.time()))
        return session_id

    def get(self, session_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM rehearsals WHERE id=?", (session_id,)).fetchone()
        if row is None:
            return None
        session = dict(row)
        session["report"] = json.loads(session["report"]) if session["report"] else None
        return session

    def add_turn(self, session_id: str, role: str, content: str):
        with self._connect() as db:
            db.execute("INSERT INTO rehearsal_turns(session_id, role, content, created) VALUES (?,?,?,?)",
                       (session_id, role, content, time.time()))

    def turns(self, session_id: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT role, content FROM rehearsal_turns WHERE session_id=? ORDER BY id",
                              (session_id,))
            return [dict(r) for r in rows]

    def finish(self, session_id: str, report: dict):
        with self._connect() as db:
            db.execute("UPDATE rehearsals SET status='ended', report=? WHERE id=?",
                       (json.dumps(report, ensure_ascii=False), session_id))
