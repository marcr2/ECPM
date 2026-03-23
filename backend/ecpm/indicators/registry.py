"""MethodologyRegistry for discovering and retrieving methodology mappers.

Provides a class-level registry that stores methodology implementations
keyed by slug. Endpoints look up methodologies by slug at request time.
"""

from __future__ import annotations

from ecpm.indicators.base import MethodologyMapper


class MethodologyRegistry:
    """Registry for methodology mapper implementations.

    Class-level storage: all instances share the same mapper dict.
    Use ``reset()`` in tests to ensure isolation between test cases.
    """

    _mappers: dict[str, MethodologyMapper] = {}

    @classmethod
    def register(cls, mapper: MethodologyMapper) -> None:
        """Register a methodology mapper by its slug.

        Args:
            mapper: A concrete MethodologyMapper instance.
        """
        cls._mappers[mapper.slug] = mapper

    @classmethod
    def get(cls, slug: str) -> MethodologyMapper:
        """Retrieve a mapper by slug.

        Args:
            slug: URL-safe identifier (e.g., 'shaikh-tonak').

        Raises:
            KeyError: If no mapper is registered with the given slug.
        """
        if slug not in cls._mappers:
            raise KeyError(f"Unknown methodology: {slug}")
        return cls._mappers[slug]

    @classmethod
    def list_all(cls) -> list[MethodologyMapper]:
        """Return all registered mappers."""
        return list(cls._mappers.values())

    @classmethod
    def default(cls) -> MethodologyMapper:
        """Return the default methodology (Shaikh/Tonak).

        Raises:
            KeyError: If 'shaikh-tonak' is not registered.
        """
        return cls.get("shaikh-tonak")

    @classmethod
    def reset(cls) -> None:
        """Clear all registered mappers. Use in tests for isolation."""
        cls._mappers = {}
