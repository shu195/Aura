import json
import math
from datetime import UTC, datetime
from typing import List

from app.models.schemas import MemoryRecord
from app.services.embedding_service import EmbeddingService
from app.storage import SQLiteStore


class MemoryService:
    def __init__(self, store: SQLiteStore, embedding_service: EmbeddingService) -> None:
        self.store = store
        self.embedding_service = embedding_service

    def add(self, record: MemoryRecord) -> None:
        conn = self.store.connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO memory_records (
                    user_id, session_id, role, content, retention_days, purpose, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.user_id,
                    record.session_id,
                    record.role,
                    record.content,
                    record.retention_days,
                    record.purpose,
                    record.created_at.isoformat(),
                ),
            )
            record_id = cur.lastrowid

            embedding = self.embedding_service.embed(record.content)
            conn.execute(
                """
                INSERT OR REPLACE INTO memory_embeddings (record_id, user_id, embedding_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (record_id, record.user_id, json.dumps(embedding), datetime.now(UTC).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def search(self, user_id: str, query: str, limit: int = 5) -> List[str]:
        query_embedding = self.embedding_service.embed(query)
        conn = self.store.connect()
        try:
            rows = conn.execute(
                """
                SELECT r.id, r.content, e.embedding_json
                FROM memory_records r
                JOIN memory_embeddings e ON e.record_id = r.id
                WHERE r.user_id = ?
                ORDER BY r.id DESC
                LIMIT 500
                """,
                (user_id,),
            ).fetchall()

            if not rows:
                return []

            scored: List[tuple[float, str]] = []
            for row in rows:
                db_vec = json.loads(row["embedding_json"])
                similarity = self._cosine_similarity(query_embedding, db_vec)
                scored.append((similarity, row["content"]))

            scored.sort(key=lambda item: item[0], reverse=True)
            return [content for score, content in scored[:limit] if score > 0]
        finally:
            conn.close()

    def summarize_recent(self, user_id: str, limit: int = 10) -> str:
        conn = self.store.connect()
        try:
            rows = conn.execute(
                """
                SELECT role, content
                FROM memory_records
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return "No prior context."
        user_rows = [row for row in reversed(rows) if row["role"] == "user"]
        if not user_rows:
            return "No prior context."
        snippets = [f"user: {row['content'][:80]}" for row in user_rows[-3:]]
        return " | ".join(snippets)

    def purge_user(self, user_id: str) -> int:
        conn = self.store.connect()
        try:
            conn.execute(
                "DELETE FROM memory_embeddings WHERE user_id = ?",
                (user_id,),
            )
            cur = conn.execute("DELETE FROM memory_records WHERE user_id = ?", (user_id,))
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def enforce_retention(self) -> int:
        now = datetime.now(UTC)
        conn = self.store.connect()
        try:
            rows = conn.execute("SELECT id, created_at, retention_days FROM memory_records").fetchall()
            to_delete = []
            for row in rows:
                created_at = datetime.fromisoformat(row["created_at"])
                age_days = (now - created_at).days
                if age_days > row["retention_days"]:
                    to_delete.append(row["id"])

            if not to_delete:
                return 0

            placeholders = ",".join(["?"] * len(to_delete))
            conn.execute(f"DELETE FROM memory_embeddings WHERE record_id IN ({placeholders})", to_delete)
            cur = conn.execute(f"DELETE FROM memory_records WHERE id IN ({placeholders})", to_delete)
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0

        size = min(len(a), len(b))
        dot = sum(a[i] * b[i] for i in range(size))
        norm_a = math.sqrt(sum(v * v for v in a[:size]))
        norm_b = math.sqrt(sum(v * v for v in b[:size]))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
