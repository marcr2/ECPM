"""Indicator computation engine: ABC, registry, and definitions.

Public API for the indicators package. Import from here in application code.
"""

from ecpm.indicators.base import IndicatorDoc, MethodologyMapper, NIPAMapping
from ecpm.indicators.definitions import INDICATOR_DEFS, IndicatorSlug
from ecpm.indicators.registry import MethodologyRegistry

__all__ = [
    "IndicatorDoc",
    "IndicatorSlug",
    "INDICATOR_DEFS",
    "MethodologyMapper",
    "MethodologyRegistry",
    "NIPAMapping",
]
