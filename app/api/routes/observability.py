from fastapi import APIRouter, Depends

from app.dependencies import observability_service
from app.models.schemas import AuditEvent
from app.security import require_scopes

router = APIRouter(
    prefix="/v1/observability",
    tags=["observability"],
    dependencies=[Depends(require_scopes(["observability:read"]))],
)


@router.get("/events", response_model=list[AuditEvent])
def list_events(limit: int = 100) -> list[AuditEvent]:
    return observability_service.list_events(limit=limit)
