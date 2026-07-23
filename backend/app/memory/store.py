import sqlite3
import os
from datetime import datetime


class MemoryStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "data", "memory.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                session_id TEXT PRIMARY KEY,
                summary TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.conn.commit()

    def save_message(self, session_id: str, role: str, content: str, metadata: str = None):
        self.conn.execute(
            "INSERT INTO conversations (session_id, role, content, metadata) VALUES (?, ?, ?, ?)",
            (session_id, role, content, metadata),
        )
        self.conn.commit()

    def get_recent(self, session_id: str, k: int = 20):
        cursor = self.conn.execute(
            "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, k),
        )
        rows = cursor.fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def get_all_sessions(self):
        cursor = self.conn.execute(
            "SELECT DISTINCT session_id FROM conversations ORDER BY session_id"
        )
        return [row[0] for row in cursor.fetchall()]

    def save_summary(self, session_id: str, summary: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO summaries (session_id, summary, updated_at) VALUES (?, ?, ?)",
            (session_id, summary, datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_summary(self, session_id: str):
        cursor = self.conn.execute(
            "SELECT summary FROM summaries WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def clear_session(self, session_id: str):
        self.conn.execute(
            "DELETE FROM conversations WHERE session_id = ?", (session_id,)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
