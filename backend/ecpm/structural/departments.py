"""Department I/II classification and proportionality conditions.

Implements Marx's reproduction schema with Department I (means of production)
and Department II (means of consumption) classification based on NAICS codes.
"""

from __future__ import annotations

import numpy as np


# Department I: Industries producing means of production
# Based on NAICS codes at BEA summary level (71 industries)
DEPT_I_CODES: set[str] = {
    # Mining
    "211",   # Oil and gas extraction
    "212",   # Mining (except oil and gas)
    "213",   # Support activities for mining
    # Utilities (power generation infrastructure)
    "22",    # Utilities
    # Construction
    "23",    # Construction
    # Manufacturing - durable goods (machinery, equipment, metals)
    "321",   # Wood products
    "327",   # Nonmetallic mineral products
    "331",   # Primary metals
    "332",   # Fabricated metal products
    "333",   # Machinery
    "334",   # Computer and electronic products
    "335",   # Electrical equipment, appliances
    "336",   # Transportation equipment
    # Manufacturing - chemicals, plastics (industrial inputs)
    "325",   # Chemical products
    "326",   # Plastics and rubber products
    # Wholesale trade (intermediate distribution)
    "42",    # Wholesale trade
    # Transportation and warehousing (means of circulation)
    "481",   # Air transportation
    "482",   # Rail transportation
    "483",   # Water transportation
    "484",   # Truck transportation
    "485",   # Transit and ground passenger
    "486",   # Pipeline transportation
    "487OS", # Other transportation and support
    "493",   # Warehousing and storage
    # Information (telecommunications infrastructure)
    "511",   # Publishing industries
    "512",   # Motion picture and sound
    "513",   # Broadcasting and telecommunications
    "514",   # Data processing, internet
}

# Department II: Everything not in Department I
# Consumer-facing services, retail, food, healthcare, education, etc.


def classify_departments(naics_codes: list[str]) -> dict[str, str]:
    """Classify NAICS codes into Department I or Department II.

    Department I: Means of production (capital goods, raw materials,
    machinery, industrial inputs).
    Department II: Means of consumption (consumer goods and services).

    Args:
        naics_codes: List of NAICS codes to classify.

    Returns:
        Dict mapping each code to "Dept_I" or "Dept_II".
    """
    result = {}
    for code in naics_codes:
        # Check exact match first
        if code in DEPT_I_CODES:
            result[code] = "Dept_I"
        # Check prefix match (e.g., "211A" matches "211")
        elif any(code.startswith(prefix) for prefix in DEPT_I_CODES):
            result[code] = "Dept_I"
        else:
            result[code] = "Dept_II"
    return result


def aggregate_by_department(
    use_matrix: np.ndarray,
    classification: dict[str, str],
    sector_codes: list[str],
) -> np.ndarray:
    """Aggregate I-O matrix by department.

    Sums rows and columns belonging to each department to produce
    a 2x2 matrix: [[Dept_I->Dept_I, Dept_I->Dept_II],
                   [Dept_II->Dept_I, Dept_II->Dept_II]]

    Args:
        use_matrix: n x n intermediate use matrix.
        classification: Dict mapping sector codes to "Dept_I" or "Dept_II".
        sector_codes: List of sector codes (order matches matrix indices).

    Returns:
        2x2 numpy array of inter-department flows.
    """
    n = use_matrix.shape[0]

    # Create boolean masks for each department
    dept_i_mask = np.array(
        [classification.get(code, "Dept_II") == "Dept_I" for code in sector_codes[:n]]
    )
    dept_ii_mask = ~dept_i_mask

    # Aggregate: sum flows between department pairs
    # [i->i, i->ii]
    # [ii->i, ii->ii]
    result = np.array(
        [
            [
                use_matrix[np.ix_(dept_i_mask, dept_i_mask)].sum(),
                use_matrix[np.ix_(dept_i_mask, dept_ii_mask)].sum(),
            ],
            [
                use_matrix[np.ix_(dept_ii_mask, dept_i_mask)].sum(),
                use_matrix[np.ix_(dept_ii_mask, dept_ii_mask)].sum(),
            ],
        ]
    )

    return result


def check_proportionality(
    dept_i_c: float,
    dept_i_v: float,
    dept_i_s: float,
    dept_ii_c: float,
    dept_ii_v: float,
    dept_ii_s: float,
) -> dict:
    """Check Marx's reproduction schema proportionality conditions.

    Simple reproduction condition: I(v + s) = II(c)
    Department I's newly created value must equal Department II's
    demand for means of production.

    Expanded reproduction condition: I(v + s) > II(c)
    Department I must produce excess means of production for
    capital accumulation (growth).

    Args:
        dept_i_c: Department I constant capital (consumed means of production).
        dept_i_v: Department I variable capital (wages).
        dept_i_s: Department I surplus value.
        dept_ii_c: Department II constant capital.
        dept_ii_v: Department II variable capital.
        dept_ii_s: Department II surplus value.

    Returns:
        Dict with proportionality check results.
    """
    i_v_plus_s = dept_i_v + dept_i_s
    ii_c = dept_ii_c

    # Simple reproduction: I(v+s) = II(c) (within 5% tolerance)
    simple_holds = abs(i_v_plus_s - ii_c) / max(ii_c, 1e-10) < 0.05

    # Expanded reproduction: I(v+s) > II(c)
    expanded_holds = i_v_plus_s > ii_c

    # Surplus ratio
    surplus_ratio = i_v_plus_s / ii_c if ii_c > 0 else None

    return {
        "i_v_plus_s": float(i_v_plus_s),
        "ii_c": float(ii_c),
        "simple_reproduction_holds": simple_holds,
        "expanded_reproduction_holds": expanded_holds,
        "surplus_ratio": float(surplus_ratio) if surplus_ratio is not None else None,
        "formula_display": f"I(v+s) = {i_v_plus_s:.1f}, II(c) = {ii_c:.1f}",
        "condition_met": i_v_plus_s >= ii_c,
    }


def compute_reproduction_flows(
    use_matrix: np.ndarray,
    value_added: np.ndarray,
    classification: dict[str, str],
    sector_codes: list[str],
    *,
    is_dollar_flows: bool = False,
) -> dict:
    """Compute full reproduction schema flows.

    Combines aggregation with c/v/s decomposition to produce
    Department I and II values for proportionality analysis.

    c (constant capital) = intermediate inputs consumed (dollar value)
    v (variable capital) = compensation of employees (approximated)
    s (surplus value) = gross operating surplus (approximated)

    When ``is_dollar_flows`` is True the *use_matrix* contains the raw
    BEA Use table in millions of dollars and ``value_added`` must also
    be expressed in millions of dollars.  When False the matrix is the
    technical-coefficient matrix (dimensionless) and values will be
    labelled accordingly.

    Args:
        use_matrix: n x n intermediate use matrix (dollar flows or coefficients).
        value_added: n-vector of value added by industry (same unit as use_matrix).
        classification: Dict mapping sector codes to "Dept_I" or "Dept_II".
        sector_codes: List of sector codes.
        is_dollar_flows: Whether use_matrix contains dollar-flow data.

    Returns:
        Dict with ``matrix_kind`` (``"dollar_flows"`` or ``"coefficients"``),
        dept_i / dept_ii c/v/s values, flows, and proportionality.
    """
    n = use_matrix.shape[0]

    # Create boolean masks
    dept_i_mask = np.array(
        [classification.get(code, "Dept_II") == "Dept_I" for code in sector_codes[:n]]
    )
    dept_ii_mask = ~dept_i_mask

    # Aggregate inter-department flows
    flows = aggregate_by_department(use_matrix, classification, sector_codes)

    # c (constant capital) = intermediate inputs consumed by each department
    dept_i_c = float(use_matrix[:, dept_i_mask].sum())
    dept_ii_c = float(use_matrix[:, dept_ii_mask].sum())

    # Approximate v and s from value added (60/40 labour/surplus split)
    dept_i_va = float(value_added[dept_i_mask].sum()) if len(value_added) >= n else 0.0
    dept_ii_va = float(value_added[dept_ii_mask].sum()) if len(value_added) >= n else 0.0

    labor_share = 0.6
    dept_i_v = labor_share * dept_i_va
    dept_i_s = (1 - labor_share) * dept_i_va
    dept_ii_v = labor_share * dept_ii_va
    dept_ii_s = (1 - labor_share) * dept_ii_va

    matrix_kind = "dollar_flows" if is_dollar_flows else "coefficients"

    # Check proportionality
    proportionality = check_proportionality(
        dept_i_c, dept_i_v, dept_i_s, dept_ii_c, dept_ii_v, dept_ii_s
    )

    return {
        "matrix_kind": matrix_kind,
        "dept_i": {
            "c": dept_i_c,
            "v": dept_i_v,
            "s": dept_i_s,
        },
        "dept_ii": {
            "c": dept_ii_c,
            "v": dept_ii_v,
            "s": dept_ii_s,
        },
        "flows": flows.tolist(),
        "proportionality": proportionality,
    }
