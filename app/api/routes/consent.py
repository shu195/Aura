from fastapi import APIRouter, Depends

from app.dependencies import consent_service, observability_service
from app.models.schemas import ConsentStatusResponse, ConsentUpdateRequest
from app.security import require_scopes

router = APIRouter(
    prefix="/v1/consent",
    tags=["consent"],
    dependencies=[Depends(require_scopes(["consent:write"]))],
)


@router.get("/{user_id}", response_model=ConsentStatusResponse)
def get_consent(user_id: str) -> ConsentStatusResponse:
    status = consent_service.get(user_id)
    observability_service.emit("consent.read", user_id)
    return status


@router.post("/update", response_model=ConsentStatusResponse)
def update_consent(payload: ConsentUpdateRequest) -> ConsentStatusResponse:
    status = consent_service.update(payload)
    observability_service.emit(
        "consent.updated",
        payload.user_id,
        {
            "gpc": str(payload.gpc_enabled).lower(),
            "opt_out": str(payload.one_click_opt_out).lower(),
            "voice": str(payload.voice_enabled).lower(),
            "vision": str(payload.vision_enabled).lower(),
        },
    )
    return status
