from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import orchestrator
from app.models.schemas import ConversationRequest, ConversationResponse
from app.security import require_scopes

router = APIRouter(
    prefix="/v1/conversation",
    tags=["conversation"],
    dependencies=[Depends(require_scopes(["conversation:write"]))],
)


@router.post("/turn", response_model=ConversationResponse)
def conversation_turn(payload: ConversationRequest) -> ConversationResponse:
    try:
        return orchestrator.handle_turn(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
