from datetime import UTC, datetime, timedelta
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

http_bearer = HTTPBearer(auto_error=False)

USER_STORE = {
    "admin": {
        "password": "admin123",
        "scopes": ["conversation:write", "memory:write", "consent:write", "observability:read"],
    },
    "analyst": {
        "password": "analyst123",
        "scopes": ["conversation:write", "memory:write", "consent:write"],
    },
}


def authenticate_user(username: str, password: str) -> list[str] | None:
    user = USER_STORE.get(username)
    if not user or user["password"] != password:
        return None
    return user["scopes"]


def create_access_token(subject: str, scopes: list[str]) -> tuple[str, int]:
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {
        "sub": subject,
        "scopes": scopes,
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int(expires.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, settings.jwt_exp_minutes * 60


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def get_current_claims(
    creds: HTTPAuthorizationCredentials | None = Security(http_bearer),
) -> dict:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return decode_token(creds.credentials)


def require_scopes(required: list[str]) -> Callable[[dict], dict]:
    def _checker(claims: dict = Depends(get_current_claims)) -> dict:
        granted = set(claims.get("scopes", []))
        if any(scope not in granted for scope in required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return claims

    return _checker
