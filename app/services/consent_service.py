from datetime import UTC, datetime

from app.models.schemas import ConsentStatusResponse, ConsentUpdateRequest
from app.storage import SQLiteStore


class ConsentService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def get(self, user_id: str) -> ConsentStatusResponse:
        conn = self.store.connect()
        try:
            row = conn.execute(
                """
                SELECT user_id, gpc_enabled, one_click_opt_out, voice_enabled, vision_enabled, updated_at
                FROM consents
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

            if row:
                return ConsentStatusResponse(
                    user_id=row["user_id"],
                    gpc_enabled=bool(row["gpc_enabled"]),
                    one_click_opt_out=bool(row["one_click_opt_out"]),
                    voice_enabled=bool(row["voice_enabled"]),
                    vision_enabled=bool(row["vision_enabled"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )

            default = ConsentStatusResponse(
                user_id=user_id,
                gpc_enabled=False,
                one_click_opt_out=False,
                voice_enabled=True,
                vision_enabled=False,
                updated_at=datetime.now(UTC),
            )
            self._upsert(default)
            return default
        finally:
            conn.close()

    def update(self, payload: ConsentUpdateRequest) -> ConsentStatusResponse:
        updated = ConsentStatusResponse(
            user_id=payload.user_id,
            gpc_enabled=payload.gpc_enabled,
            one_click_opt_out=payload.one_click_opt_out,
            voice_enabled=payload.voice_enabled,
            vision_enabled=payload.vision_enabled,
            updated_at=datetime.now(UTC),
        )
        self._upsert(updated)
        return updated

    def _upsert(self, status: ConsentStatusResponse) -> None:
        conn = self.store.connect()
        try:
            conn.execute(
                """
                INSERT INTO consents (user_id, gpc_enabled, one_click_opt_out, voice_enabled, vision_enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    gpc_enabled = excluded.gpc_enabled,
                    one_click_opt_out = excluded.one_click_opt_out,
                    voice_enabled = excluded.voice_enabled,
                    vision_enabled = excluded.vision_enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    status.user_id,
                    int(status.gpc_enabled),
                    int(status.one_click_opt_out),
                    int(status.voice_enabled),
                    int(status.vision_enabled),
                    status.updated_at.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
