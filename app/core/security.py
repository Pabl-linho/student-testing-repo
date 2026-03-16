import os

import jwt
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.users.models import User

ALGORITHM = "HS256"
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key-change-me-please-use-env-32",
).strip()

bearer_scheme = HTTPBearer(auto_error=False)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    raw_user_id = payload.get("sub", payload.get("user_id"))
    if raw_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user identity",
        )

    try:
        return int(raw_user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject must be a valid user id",
        ) from exc


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> int:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header with Bearer token is required",
        )

    user_id = decode_access_token(credentials.credentials)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user does not exist or is inactive",
        )

    return user_id


async def get_current_ws_user_id(websocket: WebSocket, db: AsyncSession) -> int:
    auth_header = websocket.headers.get("authorization")
    token = None

    if auth_header:
        scheme, _, value = auth_header.partition(" ")
        if scheme.lower() == "bearer" and value:
            token = value.strip()

    if not token:
        token = websocket.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="WebSocket token is required",
        )

    user_id = decode_access_token(token)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user does not exist or is inactive",
        )

    return user_id
