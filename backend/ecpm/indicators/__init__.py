"""Indicator computation engine: ABC, registry, definitions, and mappers.

Public API for the indicators package. Import from here in application code.
Registers both built-in methodology mappers at import time.
"""

from ecpm.indicators.base import IndicatorDoc, MethodologyMapper, NIPAMapping
from ecpm.indicators.definitions import INDICATOR_DEFS, IndicatorSlug
from ecpm.indicators.kliman import KlimanMapper
from ecpm.indicators.registry import MethodologyRegistry
from ecpm.indicators.shaikh_tonak import ShaikhTonakMapper

# Register built-in methodology mappers
MethodologyRegistry.register(ShaikhTonakMapper())
MethodologyRegistry.register(KlimanMapper())

__all__ = [
    "IndicatorDoc",
    "IndicatorSlug",
    "INDICATOR_DEFS",
    "KlimanMapper",
    "MethodologyMapper",
    "MethodologyRegistry",
    "NIPAMapping",
    "ShaikhTonakMapper",
]
