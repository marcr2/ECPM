"""Centralized exception classes and safe error response builder.

All user-facing error responses go through create_error_response() to ensure
no internal details (tracebacks, SQL, file paths) leak to clients.
"""

from fastapi.responses import JSONResponse


class ECPMError(Exception):
    """Base exception for ECPM application errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ECPMError):
    def __init__(self, resource: str, identifier: str = ""):
        detail = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        super().__init__(detail, status_code=404)


class ValidationError(ECPMError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class ServiceUnavailableError(ECPMError):
    def __init__(self, service: str):
        super().__init__(f"{service} is currently unavailable", status_code=503)


def create_error_response(status_code: int, message: str) -> JSONResponse:
    """Build a sanitized JSON error response with no internal details."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": message},
    )
