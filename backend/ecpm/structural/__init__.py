"""Structural analysis module for Input-Output computations.

Provides Leontief matrix computations, shock propagation simulation,
and Department I/II reproduction schema analysis using BEA I-O tables.
"""

from ecpm.structural.bea_io_client import BEAIOClient
from ecpm.structural.leontief import (
    compute_technical_coefficients,
    compute_leontief_inverse,
    check_stability,
    get_multipliers,
    get_output_multipliers,
)

__all__ = [
    "BEAIOClient",
    "compute_technical_coefficients",
    "compute_leontief_inverse",
    "check_stability",
    "get_multipliers",
    "get_output_multipliers",
]
