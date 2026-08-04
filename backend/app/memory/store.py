import sqlite3
import os
import json
import threading
from datetime import datetime


class MemoryStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            _backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(_backend_root, "data", "memory.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # check_same_thread=False позволяет использовать соединение из разных потоков
        # (AgentLoop создаётся в потоке event loop, а run() выполняется в пуле потоков
        # через asyncio.run_in_executor). Доступ сериализуется через self._lock.
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        # WAL-режим улучшает конкурентность при смешанных нагрузках чтения/записи
        try:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA busy_timeout=5000")
        except Exception:
            pass
        self._init_db()

    def _init_db(self):
        with self._lock:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT 'Новый чат',
                    model TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    session_id TEXT PRIMARY KEY,
                    summary TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cross_session_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def create_session(self, session_id: str, name: str = None, model: str = "") -> dict:
        if name is None:
            name = "Новый чат"
        now = datetime.now().isoformat()
        with self._lock:
            self.conn.execute(
                "INSERT OR IGNORE INTO sessions (id, name, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, name, model, now, now),
            )
            self.conn.commit()
        return {"id": session_id, "name": name, "model": model, "created_at": now}

    def rename_session(self, session_id: str, new_name: str):
        with self._lock:
            self.conn.execute(
                "UPDATE sessions SET name = ?, updated_at = ? WHERE id = ?",
                (new_name, datetime.now().isoformat(), session_id),
            )
            self.conn.commit()

    def delete_session(self, session_id: str):
        with self._lock:
            self.conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            self.conn.execute("DELETE FROM summaries WHERE session_id = ?", (session_id,))
            self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            self.conn.commit()

    def get_all_sessions(self):
        with self._lock:
            cursor = self.conn.execute(
                "SELECT id, name, model, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
            )
            rows = [dict(r) for r in cursor.fetchall()]
            if not rows:
                cursor = self.conn.execute("SELECT DISTINCT session_id FROM conversations ORDER BY session_id")
                old_ids = [r[0] for r in cursor.fetchall()]
                for sid in old_ids:
                    if sid != "default":
                        # вызываем без lock (create_session сам берёт lock)
                        pass
                # создаём сессии для старых записей вне текущей транзакции
                for sid in old_ids:
                    if sid != "default":
                        self.create_session(sid, name=sid)
                if old_ids:
                    cursor = self.conn.execute(
                        "SELECT id, name, model, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
                    )
                    rows = [dict(r) for r in cursor.fetchall()]
        return rows

    def get_session_info(self, session_id: str):
        with self._lock:
            cursor = self.conn.execute(
                "SELECT id, name, model, created_at, updated_at FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_message(self, session_id: str, role: str, content: str, metadata: str = None):
        with self._lock:
            self.conn.execute(
                "INSERT INTO conversations (session_id, role, content, metadata) VALUES (?, ?, ?, ?)",
                (session_id, role, content, metadata),
            )
            self.conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id),
            )
            self.conn.commit()

    def get_recent(self, session_id: str, k: int = 20):
        with self._lock:
            cursor = self.conn.execute(
                "SELECT role, content, metadata FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, k),
            )
            rows = cursor.fetchall()
        result = []
        for r in reversed(rows):
            item = {"role": r[0], "content": r[1]}
            if r[2]:
                try:
                    item["metadata"] = json.loads(r[2])
                except Exception:
                    pass
            result.append(item)
        return result

    def save_summary(self, session_id: str, summary: str):
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO summaries (session_id, summary, updated_at) VALUES (?, ?, ?)",
                (session_id, summary, datetime.now().isoformat()),
            )
            self.conn.commit()

    def get_summary(self, session_id: str):
        with self._lock:
            cursor = self.conn.execute(
                "SELECT summary FROM summaries WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def save_cross_session_memory(self, session_id: str, content: str):
        with self._lock:
            self.conn.execute(
                "INSERT INTO cross_session_memory (session_id, content) VALUES (?, ?)",
                (session_id, content),
            )
            self.conn.commit()

    def get_cross_session_memory(self, exclude_session_id: str = None, k: int = 10):
        with self._lock:
            if exclude_session_id:
                cursor = self.conn.execute(
                    """
                    SELECT session_id, content, created_at FROM cross_session_memory
                    WHERE session_id != ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (exclude_session_id, k),
                )
            else:
                cursor = self.conn.execute(
                    """
                    SELECT session_id, content, created_at FROM cross_session_memory
                    ORDER BY id DESC LIMIT ?
                    """,
                    (k,),
                )
            rows = cursor.fetchall()
        return [{"session_id": r[0], "content": r[1], "created_at": r[2]} for r in rows]

    def get_unindexed_conversations(self, last_indexed_id: int = 0):
        with self._lock:
            cursor = self.conn.execute(
                "SELECT id, session_id, role, content FROM conversations WHERE id > ? ORDER BY id",
                (last_indexed_id,),
            )
            return cursor.fetchall()

    def get_last_conversation_id(self):
        with self._lock:
            cursor = self.conn.execute("SELECT MAX(id) FROM conversations")
            row = cursor.fetchone()
            return row[0] if row and row[0] else 0

    def clear_session(self, session_id: str):
        with self._lock:
            self.conn.execute(
                "DELETE FROM conversations WHERE session_id = ?", (session_id,)
            )
            self.conn.commit()

    def close(self):
        with self._lock:
            self.conn.close()