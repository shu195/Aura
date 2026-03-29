from datetime import UTC, datetime
import json
from typing import List

from app.models.schemas import AuditEvent
from app.storage import SQLiteStore


class ObservabilityService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def emit(self, event_type: str, user_id: str | None = None, details: dict[str, str] | None = None) -> None:
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            details=details or {},
            created_at=datetime.now(UTC),
        )
        conn = self.store.connect()
        try:
            conn.execute(
                """
                INSERT INTO audit_events (event_type, user_id, details_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (event.event_type, event.user_id, json.dumps(event.details), event.created_at.isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def list_events(self, limit: int = 100) -> List[AuditEvent]:
        conn = self.store.connect()
        try:
            rows = conn.execute(
                """
                SELECT event_type, user_id, details_json, created_at
                FROM audit_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()

        return [
            AuditEvent(
                event_type=row["event_type"],
                user_id=row["user_id"],
                details=json.loads(row["details_json"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]
