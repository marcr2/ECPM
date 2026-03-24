"""Shock propagation simulation through Leontief inverse.

Implements single-sector and multi-sector shock simulation, critical
sector identification, and backward/forward linkage computation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_shock(
    L: np.ndarray,
    shock_industry_idx: int,
    shock_magnitude: float,
    sector_codes: list[str],
) -> dict:
    """Simulate shock propagation from a single sector.

    Computes the economy-wide impact of a demand shock to one industry
    by applying the Leontief inverse.

    Args:
        L: n x n Leontief inverse matrix.
        shock_industry_idx: Index of the shocked industry (0-based).
        shock_magnitude: Magnitude of demand shock (positive = expansion).
        sector_codes: List of sector code labels.

    Returns:
        Dict with:
        - impact_vector: list of impacts on each sector
        - ranked_impacts: list of dicts sorted by absolute impact
        - total_impact: sum of all sector impacts
    """
    n = L.shape[0]

    # Create shock vector: zeros except at shocked industry
    shock_vector = np.zeros(n)
    shock_vector[shock_industry_idx] = shock_magnitude

    # Compute impact through Leontief inverse
    impact = L @ shock_vector

    # Rank by absolute impact (largest first)
    ranked_indices = np.argsort(np.abs(impact))[::-1]
    ranked_impacts = [
        {
            "sector": sector_codes[i] if i < len(sector_codes) else f"S{i}",
            "code": sector_codes[i] if i < len(sector_codes) else f"S{i}",
            "impact": float(impact[i]),
        }
        for i in ranked_indices
    ]

    return {
        "impact_vector": impact.tolist(),
        "ranked_impacts": ranked_impacts,
        "total_impact": float(np.sum(impact)),
    }


def simulate_multi_sector_shock(
    L: np.ndarray,
    shocks: dict[int, float],
    sector_codes: list[str],
) -> dict:
    """Simulate shock propagation from multiple sectors.

    Uses superposition: combined impact is the sum of individual impacts.

    Args:
        L: n x n Leontief inverse matrix.
        shocks: Dict mapping sector indices to shock magnitudes.
        sector_codes: List of sector code labels.

    Returns:
        Dict with same structure as simulate_shock.
    """
    n = L.shape[0]

    # Build combined shock vector
    shock_vector = np.zeros(n)
    for idx, magnitude in shocks.items():
        if 0 <= idx < n:
            shock_vector[idx] = magnitude

    # Compute impact through Leontief inverse
    impact = L @ shock_vector

    # Rank by absolute impact (largest first)
    ranked_indices = np.argsort(np.abs(impact))[::-1]
    ranked_impacts = [
        {
            "sector": sector_codes[i] if i < len(sector_codes) else f"S{i}",
            "code": sector_codes[i] if i < len(sector_codes) else f"S{i}",
            "impact": float(impact[i]),
        }
        for i in ranked_indices
    ]

    return {
        "impact_vector": impact.tolist(),
        "ranked_impacts": ranked_impacts,
        "total_impact": float(np.sum(impact)),
    }


def find_critical_sectors(
    L: np.ndarray,
    sector_codes: list[str],
    threshold: float = 0.1,
) -> list[dict]:
    """Identify critical sectors based on Leontief multipliers.

    A sector is considered critical if its output multiplier exceeds
    the threshold proportion of the average multiplier.

    Args:
        L: n x n Leontief inverse matrix.
        sector_codes: List of sector code labels.
        threshold: Proportion of average multiplier to be considered critical.

    Returns:
        List of dicts with sector info and critical flag.
    """
    # Output multipliers (column sums)
    multipliers = L.sum(axis=0)
    avg_multiplier = np.mean(multipliers)

    # Critical threshold: multiplier > (1 + threshold) * average
    critical_threshold = (1 + threshold) * avg_multiplier

    results = []
    for i, code in enumerate(sector_codes):
        if i >= len(multipliers):
            break

        results.append(
            {
                "code": code,
                "name": code,  # Would be populated from descriptions
                "multiplier": float(multipliers[i]),
                "critical": bool(multipliers[i] > critical_threshold),
            }
        )

    # Sort by multiplier descending
    results.sort(key=lambda x: x["multiplier"], reverse=True)

    return results


def compute_backward_linkages(
    L: np.ndarray,
    sector_codes: list[str],
) -> pd.Series:
    """Compute backward linkages from Leontief inverse.

    Backward linkage = column sum of L = how much a sector pulls
    from other sectors when its final demand increases.

    Args:
        L: n x n Leontief inverse matrix.
        sector_codes: List of sector code labels.

    Returns:
        pd.Series indexed by sector code.
    """
    backward = L.sum(axis=0)
    return pd.Series(backward, index=sector_codes[: len(backward)])


def compute_forward_linkages(
    L: np.ndarray,
    sector_codes: list[str],
) -> pd.Series:
    """Compute forward linkages from Leontief inverse.

    Forward linkage = row sum of L = how much a sector pushes
    to other sectors when economy-wide demand increases.

    Args:
        L: n x n Leontief inverse matrix.
        sector_codes: List of sector code labels.

    Returns:
        pd.Series indexed by sector code.
    """
    forward = L.sum(axis=1)
    return pd.Series(forward, index=sector_codes[: len(forward)])


def find_weakest_link(
    L: np.ndarray,
    sector_codes: list[str],
    sector_names: list[str],
) -> dict:
    """Identify the most vulnerable sector via Leontief inverse multipliers.

    The sector with the highest output multiplier propagates shocks
    most widely through the production network.

    Args:
        L: n x n Leontief inverse matrix.
        sector_codes: List of sector code labels.
        sector_names: List of sector name descriptions.

    Returns:
        Dict with weakest sector info and explanation.
    """
    # Output multipliers (column sums)
    multipliers = L.sum(axis=0)

    # Backward linkages (column sums) and forward linkages (row sums)
    backward_linkage = L.sum(axis=0)
    forward_linkage = L.sum(axis=1)

    # Find sector with highest multiplier
    vulnerability_ranking = np.argsort(multipliers)[::-1]
    weakest_idx = vulnerability_ranking[0]

    # Count dependencies (how many sectors depend on this one significantly)
    dependency_count = int(np.sum(L[:, weakest_idx] > 0.01))

    return {
        "weakest_sector": (
            sector_names[weakest_idx] if weakest_idx < len(sector_names) else f"S{weakest_idx}"
        ),
        "weakest_index": int(weakest_idx),
        "multiplier": float(multipliers[weakest_idx]),
        "explanation": {
            "output_multiplier": float(multipliers[weakest_idx]),
            "backward_linkage": float(backward_linkage[weakest_idx]),
            "forward_linkage": float(forward_linkage[weakest_idx]),
            "dependency_count": dependency_count,
        },
        "vulnerability_ranking": [
            {
                "sector": (
                    sector_names[i] if i < len(sector_names) else f"S{i}"
                ),
                "code": (
                    sector_codes[i] if i < len(sector_codes) else f"S{i}"
                ),
                "multiplier": float(multipliers[i]),
            }
            for i in vulnerability_ranking[:10]  # Top 10 most vulnerable
        ],
    }
