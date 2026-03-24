"""Structural analysis module for Input-Output computations.

Provides Leontief matrix computations, shock propagation simulation,
and Department I/II reproduction schema analysis using BEA I-O tables.
"""

from ecpm.structural.bea_io_client import BEAIOClient

__all__ = [
    "BEAIOClient",
]
