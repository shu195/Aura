from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.dependencies import memory_service, observability_service
from app.models.schemas import MemoryRecord, MemorySearchRequest, MemorySearchResponse, PurgeRequest, PurgeResponse
from app.security import require_scopes

router = APIRouter(
    prefix="/v1/memory",
    tags=["memory"],
    dependencies=[Depends(require_scopes(["memory:write"]))],
)


@router.post("/store")
def store_memory(payload: MemoryRecord) -> dict[str, str]:
    memory_service.add(payload)
    observability_service.emit("memory.stored", payload.user_id, {"session_id": payload.session_id})
    return {"status": "stored"}


@router.post("/search", response_model=MemorySearchResponse)
def search_memory(payload: MemorySearchRequest) -> MemorySearchResponse:
    hits = memory_service.search(payload.user_id, payload.query)
    observability_service.emit("memory.searched", payload.user_id, {"query": payload.query[:80]})
    return MemorySearchResponse(user_id=payload.user_id, query=payload.query, hits=hits)


@router.post("/purge", response_model=PurgeResponse)
def purge_user_data(payload: PurgeRequest) -> PurgeResponse:
    deleted = memory_service.purge_user(payload.user_id)
    receipt_id = f"purge-{payload.user_id}-{int(datetime.now(UTC).timestamp())}"
    observability_service.emit("memory.purged", payload.user_id, {"reason": payload.reason, "receipt_id": receipt_id})
    return PurgeResponse(
        user_id=payload.user_id,
        deleted_records=deleted,
        receipt_id=receipt_id,
        deleted_at=datetime.now(UTC),
    )
