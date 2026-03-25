"""Authentication data models."""

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2-compatible token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT payload."""

    username: str
    scopes: list[str] = []
