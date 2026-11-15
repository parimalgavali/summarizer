"""API key authentication applied to every backend route."""

import secrets
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from .config import settings

API_KEY_HEADER = "X-API-Key"

_api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def require_api_key(api_key: Optional[str] = Security(_api_key_header)) -> None:
    """Reject requests without a valid key.

    With no API_KEY configured, auth is off only in DEVELOPMENT/TEST;
    PRODUCTION fails closed.
    """
    if not settings.API_KEY:
        if settings.ENV == "PRODUCTION":
            raise HTTPException(
                status_code=503, detail="API_KEY is not configured on the server"
            )
        return

    if not api_key or not secrets.compare_digest(
        api_key.encode(), settings.API_KEY.encode()
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
