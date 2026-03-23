"""Tests for MethodologyRegistry plugin pattern -- FEAT-01.

Verifies that the registry correctly stores, retrieves, and manages
methodology mapper implementations. All tests use a DummyMapper
(not real Shaikh/Tonak) and reset the registry between tests.
"""

from __future__ import annotations

import pandas as pd
import pytest

from ecpm.indicators.base import IndicatorDoc, MethodologyMapper, NIPAMapping
from ecpm.indicators.registry import MethodologyRegistry


class DummyMapper(MethodologyMapper):
    """Minimal concrete mapper for testing the registry."""

    @property
    def name(self) -> str:
        return "Dummy Methodology"

    @property
    def slug(self) -> str:
        return "dummy"

    def compute_rate_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        return pd.Series([0.0])

    def compute_occ(self, data: dict[str, pd.Series]) -> pd.Series:
        return pd.Series([0.0])

    def compute_rate_of_surplus_value(self, data: dict[str, pd.Series]) -> pd.Series:
        return pd.Series([0.0])

    def compute_mass_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        return pd.Series([0.0])

    def get_required_series(self) -> list[str]:
        return ["DUMMY_SERIES"]

    def get_documentation(self) -> list[IndicatorDoc]:
        return [
            IndicatorDoc(
                name="Dummy Rate",
                slug="dummy_rate",
                formula_latex=r"r = \frac{S}{C+V}",
                interpretation="Test indicator",
                mappings=[],
                citations=[],
            )
        ]


class ShaikhTonakDummy(DummyMapper):
    """Dummy mapper with shaikh-tonak slug for default() tests."""

    @property
    def name(self) -> str:
        return "Shaikh/Tonak"

    @property
    def slug(self) -> str:
        return "shaikh-tonak"


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the MethodologyRegistry before each test for isolation."""
    MethodologyRegistry.reset()
    yield
    MethodologyRegistry.reset()


class TestMethodologyRegistry:
    """Tests for MethodologyRegistry register/get/list_all/default/reset."""

    def test_register_and_get_by_slug(self) -> None:
        """Register a mock mapper, retrieve by slug, verify same instance."""
        mapper = DummyMapper()
        MethodologyRegistry.register(mapper)

        retrieved = MethodologyRegistry.get("dummy")
        assert retrieved is mapper
        assert retrieved.name == "Dummy Methodology"
        assert retrieved.slug == "dummy"

    def test_list_all_returns_all_registered(self) -> None:
        """list_all returns all registered mappers."""
        mapper1 = DummyMapper()
        mapper2 = ShaikhTonakDummy()
        MethodologyRegistry.register(mapper1)
        MethodologyRegistry.register(mapper2)

        all_mappers = MethodologyRegistry.list_all()
        assert len(all_mappers) == 2
        slugs = {m.slug for m in all_mappers}
        assert slugs == {"dummy", "shaikh-tonak"}

    def test_get_unknown_slug_raises_key_error(self) -> None:
        """get() with unknown slug raises KeyError."""
        with pytest.raises(KeyError, match="Unknown methodology: nonexistent"):
            MethodologyRegistry.get("nonexistent")

    def test_default_returns_shaikh_tonak(self) -> None:
        """default() returns shaikh-tonak mapper after registration."""
        mapper = ShaikhTonakDummy()
        MethodologyRegistry.register(mapper)

        default = MethodologyRegistry.default()
        assert default is mapper
        assert default.slug == "shaikh-tonak"

    def test_reset_clears_all_mappers(self) -> None:
        """reset() clears all registered mappers."""
        MethodologyRegistry.register(DummyMapper())
        MethodologyRegistry.register(ShaikhTonakDummy())
        assert len(MethodologyRegistry.list_all()) == 2

        MethodologyRegistry.reset()
        assert len(MethodologyRegistry.list_all()) == 0

        with pytest.raises(KeyError):
            MethodologyRegistry.get("dummy")
