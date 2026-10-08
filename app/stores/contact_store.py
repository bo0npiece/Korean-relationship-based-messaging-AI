"""관계 메모리 저장소: 상대(contacts)와 지난 대화 기록(interactions)을 SQLite에 저장."""
import sqlite3
import time
from pathlib import Path

CONTACT_FIELDS = ("name", "relation", "profile")


class ContactStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, relation TEXT, profile TEXT,
                    created REAL, updated REAL
                );
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL, feature TEXT,
                    input TEXT, output TEXT, created REAL
                );
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    # ---------- contacts ----------

    def list_contacts(self) -> list[dict]:
        with self._connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM contacts ORDER BY updated DESC")]

    def get_contact(self, contact_id: int) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM contacts WHERE id=?", (contact_id,)).fetchone()
        return dict(row) if row else None

    def create_contact(self, name: str, relation: str | None = None, profile: str | None = None) -> dict:
        now = time.time()
        with self._connect() as db:
            cur = db.execute("INSERT INTO contacts(name, relation, profile, created, updated) VALUES (?,?,?,?,?)",
                             (name, relation, profile, now, now))
        return self.get_contact(cur.lastrowid)

    def update_contact(self, contact_id: int, **fields) -> dict | None:
        fields = {k: v for k, v in fields.items() if k in CONTACT_FIELDS and v is not None}
        if fields:
            sets = ", ".join(f"{k}=?" for k in fields)
            with self._connect() as db:
                db.execute(f"UPDATE contacts SET {sets}, updated=? WHERE id=?",
                           (*fields.values(), time.time(), contact_id))
        return self.get_contact(contact_id)

    def delete_contact(self, contact_id: int) -> bool:
        with self._connect() as db:
            db.execute("DELETE FROM interactions WHERE contact_id=?", (contact_id,))
            return db.execute("DELETE FROM contacts WHERE id=?", (contact_id,)).rowcount > 0

    # ---------- interactions ----------

    def add_interaction(self, contact_id: int, feature: str, input_text: str, output_text: str):
        now = time.time()
        with self._connect() as db:
            db.execute("INSERT INTO interactions(contact_id, feature, input, output, created) VALUES (?,?,?,?,?)",
                       (contact_id, feature, input_text, output_text, now))
            db.execute("UPDATE contacts SET updated=? WHERE id=?", (now, contact_id))

    def list_interactions(self, contact_id: int, limit: int = 20) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM interactions WHERE contact_id=? ORDER BY id DESC LIMIT ?",
                              (contact_id, limit))
            return [dict(r) for r in rows]

    def memory_text(self, contact: dict, relation_label: str, recent: int = 3) -> str:
        """프롬프트 {memory}에 넣을 글: 프로필 + 최근 기록."""
        lines = [f"이름: {contact['name']}", f"관계: {relation_label}"]
        if contact.get("profile"):
            lines.append(f"메모: {contact['profile']}")
        history = self.list_interactions(contact["id"], recent)
        if history:
            lines.append("최근 기록:")
            for item in reversed(history):  # 오래된 것부터
                lines.append(f"- [{item['feature']}] {_short(item['input'])} → {_short(item['output'])}")
        return "\n".join(lines)


def _short(text: str | None, limit: int = 150) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit] + "…"
