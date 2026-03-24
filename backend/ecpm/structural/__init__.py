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
from ecpm.structural.shock import (
    simulate_shock,
    simulate_multi_sector_shock,
    find_critical_sectors,
    compute_backward_linkages,
    compute_forward_linkages,
    find_weakest_link,
)
from ecpm.structural.departments import (
    DEPT_I_CODES,
    classify_departments,
    aggregate_by_department,
    check_proportionality,
    compute_reproduction_flows,
)

__all__ = [
    # BEA Client
    "BEAIOClient",
    # Leontief
    "compute_technical_coefficients",
    "compute_leontief_inverse",
    "check_stability",
    "get_multipliers",
    "get_output_multipliers",
    # Shock propagation
    "simulate_shock",
    "simulate_multi_sector_shock",
    "find_critical_sectors",
    "compute_backward_linkages",
    "compute_forward_linkages",
    "find_weakest_link",
    # Departments
    "DEPT_I_CODES",
    "classify_departments",
    "aggregate_by_department",
    "check_proportionality",
    "compute_reproduction_flows",
]
