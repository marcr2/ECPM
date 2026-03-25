"""Authentication API endpoint for JWT token issuance."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from ecpm.auth.jwt import create_access_token, verify_password
from ecpm.auth.models import Token
from ecpm.config import get_settings
from ecpm.middleware.rate_limit import RATE_AUTH, limiter

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/token", response_model=Token)
@limiter.limit(RATE_AUTH)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Issue a JWT access token in exchange for valid credentials.

    Uses OAuth2 password flow: username + password via form-encoded body.
    Currently validates against the single admin user defined in settings.
    """
    settings = get_settings()

    if not settings.admin_password_hash:
        logger.error("auth.no_admin_password_configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured",
        )

    if form_data.username != settings.admin_username:
        logger.warning("auth.invalid_username", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, settings.admin_password_hash):
        logger.warning("auth.invalid_password", username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=form_data.username)
    logger.info("auth.token_issued", username=form_data.username)
    return Token(access_token=access_token)
