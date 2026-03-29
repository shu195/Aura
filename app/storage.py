import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    retention_days INTEGER NOT NULL,
                    purpose TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS consents (
                    user_id TEXT PRIMARY KEY,
                    gpc_enabled INTEGER NOT NULL,
                    one_click_opt_out INTEGER NOT NULL,
                    voice_enabled INTEGER NOT NULL,
                    vision_enabled INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_embeddings (
                    record_id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(record_id) REFERENCES memory_records(id) ON DELETE CASCADE
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_embeddings_user_id ON memory_embeddings(user_id)")
            conn.commit()
        finally:
            conn.close()

    def connect(self) -> sqlite3.Connection:
        return self._connect()
