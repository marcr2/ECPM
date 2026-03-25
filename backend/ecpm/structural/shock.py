"""Shock propagation simulation through Leontief inverse.

Implements single-sector and multi-sector shock simulation, critical
sector identification, and backward/forward linkage computation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BEA_SECTOR_NAMES: dict[str, str] = {
    "111CA": "Farms",
    "113FF": "Forestry, fishing & related",
    "211": "Oil & gas extraction",
    "212": "Mining (except oil & gas)",
    "213": "Support activities for mining",
    "22": "Utilities",
    "23": "Construction",
    "321": "Wood products",
    "327": "Nonmetallic mineral products",
    "331": "Primary metals",
    "332": "Fabricated metal products",
    "333": "Machinery",
    "334": "Computer & electronic products",
    "335": "Electrical equipment & appliances",
    "3361MV": "Motor vehicles & parts",
    "3364OT": "Other transportation equipment",
    "337": "Furniture & related products",
    "339": "Miscellaneous manufacturing",
    "311FT": "Food, beverage & tobacco",
    "313TT": "Textile mills & products",
    "315AL": "Apparel & leather",
    "322": "Paper products",
    "323": "Printing & related support",
    "324": "Petroleum & coal products",
    "325": "Chemical products",
    "326": "Plastics & rubber products",
    "42": "Wholesale trade",
    "441": "Motor vehicle & parts dealers",
    "445": "Food & beverage stores",
    "452": "General merchandise stores",
    "4A0": "Other retail",
    "481": "Air transportation",
    "482": "Rail transportation",
    "483": "Water transportation",
    "484": "Truck transportation",
    "485": "Transit & ground passenger transport",
    "486": "Pipeline transportation",
    "487OS": "Other transportation & support",
    "493": "Warehousing & storage",
    "511": "Publishing industries",
    "512": "Motion picture & sound recording",
    "513": "Broadcasting & telecommunications",
    "514": "Data processing & internet services",
    "521CI": "Banking & credit intermediation",
    "523": "Securities & investments",
    "524": "Insurance carriers & related",
    "525": "Funds, trusts & other financial vehicles",
    "HS": "Housing",
    "ORE": "Other real estate",
    "532RL": "Rental & leasing services",
    "5411": "Legal services",
    "5415": "Computer systems design",
    "5412OP": "Professional, scientific & tech services",
    "55": "Management of companies & enterprises",
    "561": "Administrative & support services",
    "562": "Waste management & remediation",
    "61": "Educational services",
    "621": "Ambulatory health care",
    "622": "Hospitals",
    "623": "Nursing & residential care",
    "624": "Social assistance",
    "711AS": "Arts, entertainment & recreation",
    "713": "Amusements, gambling & recreation",
    "721": "Accommodation",
    "722": "Food services & drinking places",
    "81": "Other services (except government)",
    "GFGD": "Federal govt. (defense)",
    "GFGN": "Federal govt. (nondefense)",
    "GFE": "Federal govt. enterprises",
    "GSLG": "State & local govt.",
    "GSLE": "State & local govt. enterprises",
    "Used": "Scrap, used & secondhand goods",
    "Other": "Noncomparable imports & rest of world",
}


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
                "name": BEA_SECTOR_NAMES.get(code, code),
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
