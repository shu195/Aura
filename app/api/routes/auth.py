from fastapi import APIRouter, HTTPException, status

from app.models.schemas import TokenRequest, TokenResponse
from app.security import authenticate_user, create_access_token

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def issue_token(payload: TokenRequest) -> TokenResponse:
    scopes = authenticate_user(payload.username, payload.password)
    if scopes is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, expires_in = create_access_token(subject=payload.username, scopes=scopes)
    return TokenResponse(access_token=token, expires_in=expires_in, scopes=scopes)
