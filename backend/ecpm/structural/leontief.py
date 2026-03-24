"""Core Leontief matrix computation functions.

Implements technical coefficient computation, Leontief inverse with
stability checks (Hawkins-Simon conditions, spectral radius, condition
number), and output multiplier extraction.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def compute_technical_coefficients(
    use_matrix: np.ndarray,
    total_output: np.ndarray,
) -> np.ndarray:
    """Compute technical coefficient matrix A.

    A[i,j] = use_matrix[i,j] / total_output[j] represents the amount
    of input from industry i required per unit of output from industry j.

    Args:
        use_matrix: n x n intermediate use matrix (Z).
        total_output: n-vector of total industry output (X).

    Returns:
        n x n technical coefficient matrix A.
    """
    # Avoid division by zero for industries with zero output
    safe_output = np.where(total_output > 0, total_output, 1.0)

    # A[i,j] = Z[i,j] / X[j] (column-wise division)
    A = use_matrix / safe_output[np.newaxis, :]

    return A


def compute_leontief_inverse(
    A: np.ndarray,
) -> tuple[Optional[np.ndarray], dict]:
    """Compute Leontief inverse L = (I - A)^-1 with stability checks.

    Performs comprehensive stability analysis before and after inversion,
    including Hawkins-Simon conditions, condition number, and spectral radius.

    Args:
        A: n x n technical coefficient matrix.

    Returns:
        Tuple of (Leontief inverse matrix or None, diagnostics dict).
        Returns (None, diagnostics) if matrix is singular or unstable.
    """
    n = A.shape[0]
    I = np.eye(n)
    B = I - A  # The matrix to invert

    diagnostics: dict = {}

    # Check Hawkins-Simon conditions: all leading principal minors of (I-A) > 0
    diagnostics["hawkins_simon"] = True
    diagnostics["hawkins_simon_failure_at"] = None

    for k in range(1, n + 1):
        minor_det = np.linalg.det(B[:k, :k])
        if minor_det <= 0:
            diagnostics["hawkins_simon"] = False
            diagnostics["hawkins_simon_failure_at"] = k
            break

    # Condition number check
    try:
        cond = np.linalg.cond(B)
        diagnostics["condition_number"] = float(cond)
        diagnostics["well_conditioned"] = cond < 1e10
    except Exception:
        diagnostics["condition_number"] = float("inf")
        diagnostics["well_conditioned"] = False

    # Spectral radius of A must be < 1 for convergence
    try:
        eigenvalues = np.linalg.eigvals(A)
        spectral_radius = float(np.max(np.abs(eigenvalues)))
        diagnostics["spectral_radius"] = spectral_radius
        diagnostics["convergent"] = spectral_radius < 1.0
    except Exception:
        diagnostics["spectral_radius"] = float("inf")
        diagnostics["convergent"] = False

    # Attempt matrix inversion
    try:
        L = np.linalg.inv(B)
        diagnostics["success"] = True

        # Sanity check: Leontief inverse should have non-negative entries
        # (negative entries indicate model problems)
        if np.any(L < -1e-10):
            diagnostics["has_negative_entries"] = True
        else:
            diagnostics["has_negative_entries"] = False

        return L, diagnostics

    except np.linalg.LinAlgError:
        diagnostics["success"] = False
        return None, diagnostics


def check_stability(A: np.ndarray) -> dict:
    """Check stability of technical coefficient matrix without full inversion.

    Provides quick stability assessment for validation and monitoring.

    Args:
        A: n x n technical coefficient matrix.

    Returns:
        Dict with stability metrics:
        - is_stable: bool overall stability assessment
        - max_eigenvalue: float spectral radius
        - condition_number: float of (I - A)
        - hawkins_simon: bool leading minors condition
    """
    n = A.shape[0]
    I = np.eye(n)
    B = I - A

    result: dict = {}

    # Spectral radius
    try:
        eigenvalues = np.linalg.eigvals(A)
        max_eigenvalue = float(np.max(np.abs(eigenvalues)))
        result["max_eigenvalue"] = max_eigenvalue
    except Exception:
        result["max_eigenvalue"] = float("inf")

    # Condition number
    try:
        cond = np.linalg.cond(B)
        result["condition_number"] = float(cond)
    except Exception:
        result["condition_number"] = float("inf")

    # Hawkins-Simon (just check first two for speed in quick check)
    result["hawkins_simon"] = True
    for k in range(1, min(n + 1, 3)):  # Check first 2 minors
        minor_det = np.linalg.det(B[:k, :k])
        if minor_det <= 0:
            result["hawkins_simon"] = False
            break

    # Full Hawkins-Simon check if first pass succeeded
    if result["hawkins_simon"] and n > 2:
        for k in range(3, n + 1):
            minor_det = np.linalg.det(B[:k, :k])
            if minor_det <= 0:
                result["hawkins_simon"] = False
                break

    # Overall stability assessment
    result["is_stable"] = (
        result["max_eigenvalue"] < 1.0
        and result["condition_number"] < 1e10
        and result["hawkins_simon"]
    )

    return result


def get_multipliers(L: np.ndarray) -> np.ndarray:
    """Extract output multipliers from Leontief inverse.

    Output multipliers are column sums of L, representing the total
    output increase across all industries per unit final demand increase
    in each industry.

    Args:
        L: n x n Leontief inverse matrix.

    Returns:
        n-vector of output multipliers.
    """
    return L.sum(axis=0)


def get_output_multipliers(
    L: np.ndarray,
    sector_codes: list[str],
) -> pd.Series:
    """Get output multipliers as a labeled Series, sorted descending.

    Args:
        L: n x n Leontief inverse matrix.
        sector_codes: List of sector code labels.

    Returns:
        pd.Series indexed by sector code, sorted by multiplier value descending.
    """
    multipliers = get_multipliers(L)
    series = pd.Series(multipliers, index=sector_codes)
    return series.sort_values(ascending=False)


def compute_total_requirements(L: np.ndarray) -> np.ndarray:
    """Compute total requirements matrix from Leontief inverse.

    The total requirements matrix shows total direct and indirect
    inputs required from each industry per unit of final demand.

    Args:
        L: n x n Leontief inverse matrix.

    Returns:
        n x n total requirements matrix.
    """
    # Total requirements is simply the Leontief inverse itself
    # Each L[i,j] shows total requirements from industry i
    # per unit of final demand for industry j's output
    return L


def compute_direct_requirements(A: np.ndarray) -> np.ndarray:
    """Return direct requirements matrix (same as technical coefficients).

    Direct requirements show only first-round inputs, without the
    cascade of indirect effects captured in the Leontief inverse.

    Args:
        A: n x n technical coefficient matrix.

    Returns:
        n x n direct requirements matrix (same as A).
    """
    return A
