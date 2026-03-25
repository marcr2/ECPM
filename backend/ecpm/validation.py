"""Input validation utilities for API parameters.

Provides strict validation for user-supplied identifiers and search terms
to prevent injection attacks and unexpected input.
"""

import re

_SERIES_ID_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_SEARCH_PATTERN = re.compile(r"^[A-Za-z0-9 \-_.,()&/]{0,200}$")
_NAICS_PATTERN = re.compile(r"^[0-9]{2,6}$")


def validate_series_id(series_id: str) -> str:
    """Validate a series ID is alphanumeric with limited special chars."""
    if not _SERIES_ID_PATTERN.match(series_id):
        raise ValueError(
            f"Invalid series ID format: must be 1-64 alphanumeric characters, hyphens, or underscores"
        )
    return series_id


def validate_search_query(query: str) -> str:
    """Validate a search query contains only safe characters."""
    if not _SEARCH_PATTERN.match(query):
        raise ValueError(
            "Invalid search query: contains disallowed characters"
        )
    return query


def validate_naics_code(code: str) -> str:
    """Validate a NAICS industry code."""
    if not _NAICS_PATTERN.match(code):
        raise ValueError(
            "Invalid NAICS code: must be 2-6 digits"
        )
    return code


def validate_pagination(limit: int, offset: int, max_limit: int = 1000) -> tuple[int, int]:
    """Validate and clamp pagination parameters."""
    limit = max(1, min(limit, max_limit))
    offset = max(0, offset)
    return limit, offset
