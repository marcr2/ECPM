"""Composite Crisis Probability Index with learned mechanism weights.

Synthesizes TRPF (tendency of the rate of profit to fall), realization
crisis, and financial fragility sub-indices into a single 0-100
composite crisis probability index.

When a distance-to-crisis target is available (built from USREC), uses
L2-regularized logistic regression to learn mechanism weights from data.
Falls back to equal 1/3 weights when no target is provided.

Exports:
    compute                -- compute crisis index from indicator DataFrame
    compute_sub_indices    -- build the 3 normalised sub-index Series
    learn_weights          -- fit logistic regression on sub-indices vs target
    MECHANISM_INDICATORS   -- mapping of mechanisms to indicator slugs
    DEFAULT_WEIGHTS        -- fallback equal weights
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


MECHANISM_INDICATORS: dict[str, list[str]] = {
    "trpf": ["rate_of_profit", "occ", "rate_of_surplus_value", "mass_of_profit"],
    "realization": ["productivity_wage_gap"],
    "financial": ["credit_gdp_gap", "financial_real_ratio", "debt_service_ratio"],
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "trpf": 1 / 3,
    "realization": 1 / 3,
    "financial": 1 / 3,
}

# Higher values = higher crisis risk (no inversion)
_CRISIS_POSITIVE = {
    "occ",
    "mass_of_profit",
    "productivity_wage_gap",
    "credit_gdp_gap",
    "financial_real_ratio",
    "debt_service_ratio",
}

# Lower values = higher crisis risk (must invert)
_CRISIS_INVERTED = {
    "rate_of_profit",
    "rate_of_surplus_value",
}


def compute_sub_indices(data: pd.DataFrame) -> dict[str, pd.Series]:
    """Compute the three normalised mechanism sub-indices.

    Each indicator is mapped to [0, 1] via global percentile rank,
    crisis-inverted indicators are flipped, then sub-indices are the
    mean of their constituent indicators.

    Returns dict mapping mechanism name -> pd.Series in [0, 1].
    """
    stacked = data.stack()
    global_ranks = stacked.rank(pct=True)
    normalized = global_ranks.unstack()

    for col in data.columns:
        if col in _CRISIS_INVERTED:
            normalized[col] = 1.0 - normalized[col]

    mechanism_series: dict[str, pd.Series] = {}
    for mechanism, indicators in MECHANISM_INDICATORS.items():
        available_cols = [c for c in indicators if c in normalized.columns]
        if available_cols:
            mechanism_series[mechanism] = normalized[available_cols].mean(axis=1)
        else:
            logger.warning("mechanism_missing_indicators", mechanism=mechanism, expected=indicators)

    return mechanism_series


def learn_weights(
    sub_indices: dict[str, pd.Series],
    target: pd.Series,
    threshold: float = 0.25,
) -> dict:
    """Learn crisis mechanism weights via L2 logistic regression.

    Parameters
    ----------
    sub_indices : dict[str, pd.Series]
        Output from ``compute_sub_indices``.
    target : pd.Series
        Continuous crisis proximity in [0, 1] (from ``crisis_target``).
    threshold : float
        Value above which the target is labelled as "pre-crisis" for
        the binary classifier.

    Returns
    -------
    dict
        Keys: weights (dict[str, float]), coefficients (raw logit coefs),
        intercept, accuracy, n_train, cv_scores.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler

    mechanisms = sorted(sub_indices.keys())
    X_df = pd.DataFrame({m: sub_indices[m] for m in mechanisms})
    combined = pd.concat([X_df, target.rename("target")], axis=1).dropna()

    if len(combined) < 30:
        logger.warning("learn_weights_insufficient_data", n=len(combined))
        return {
            "weights": DEFAULT_WEIGHTS.copy(),
            "coefficients": {},
            "intercept": 0.0,
            "accuracy": 0.0,
            "n_train": len(combined),
            "cv_scores": [],
        }

    X = combined[mechanisms].values
    y = (combined["target"].values >= threshold).astype(int)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(
        penalty="l2",
        C=1.0,
        solver="lbfgs",
        max_iter=1000,
        class_weight="balanced",
    )
    model.fit(X_scaled, y)

    # Cross-validation score (5-fold, respecting time via KFold -- not
    # TimeSeriesSplit because we want all recessions represented)
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring="roc_auc")

    raw_coefs = dict(zip(mechanisms, model.coef_[0].tolist()))

    # Convert absolute coefficients to normalised weights in [0, 1]
    abs_coefs = np.abs(model.coef_[0])
    total = abs_coefs.sum()
    if total > 0:
        weights = {m: float(abs_coefs[i] / total) for i, m in enumerate(mechanisms)}
    else:
        weights = DEFAULT_WEIGHTS.copy()

    logger.info(
        "weights_learned",
        weights=weights,
        accuracy=float(np.mean(cv_scores)),
        n_train=len(combined),
    )

    return {
        "weights": weights,
        "coefficients": raw_coefs,
        "intercept": float(model.intercept_[0]),
        "accuracy": float(np.mean(cv_scores)),
        "n_train": len(combined),
        "cv_scores": cv_scores.tolist(),
    }


def compute(
    data: pd.DataFrame,
    weights: dict[str, float] | None = None,
    crisis_target: pd.Series | None = None,
) -> dict:
    """Compute the Composite Crisis Probability Index.

    When *crisis_target* is provided, learns weights from data via
    logistic regression.  Otherwise uses *weights* (default: equal 1/3).

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with indicator columns.
    weights : dict or None
        Manual weights.  Ignored when *crisis_target* is given.
    crisis_target : pd.Series or None
        Continuous crisis proximity target from ``crisis_target`` module.

    Returns
    -------
    dict
        Keys: current_value, trpf_component, realization_component,
        financial_component, history, learned_weights (optional).
    """
    sub_indices = compute_sub_indices(data)

    learned_weights_info: dict | None = None
    if crisis_target is not None:
        learned_weights_info = learn_weights(sub_indices, crisis_target)
        weights = learned_weights_info["weights"]
    elif weights is None:
        weights = DEFAULT_WEIGHTS.copy()

    if not sub_indices:
        logger.error("no_mechanisms_available")
        return {
            "current_value": 0.0,
            "trpf_component": 0.0,
            "realization_component": 0.0,
            "financial_component": 0.0,
            "history": [],
            "learned_weights": None,
        }

    # Renormalize weights to available mechanisms
    available = {k: weights.get(k, 0.0) for k in sub_indices}
    total_weight = sum(available.values())
    if total_weight > 0:
        norm_weights = {k: v / total_weight for k, v in available.items()}
    else:
        norm_weights = {k: 1.0 / len(available) for k in available}

    composite = pd.Series(0.0, index=data.index)
    for mechanism, series in sub_indices.items():
        composite = composite + series * norm_weights.get(mechanism, 0.0)

    composite_100 = composite * 100
    trpf_100 = sub_indices.get("trpf", pd.Series(0.0, index=data.index)) * 100
    realization_100 = sub_indices.get("realization", pd.Series(0.0, index=data.index)) * 100
    financial_100 = sub_indices.get("financial", pd.Series(0.0, index=data.index)) * 100

    history = []
    for idx in data.index:
        entry: dict = {}
        entry["date"] = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
        entry["composite"] = float(composite_100.loc[idx])
        entry["trpf"] = float(trpf_100.loc[idx])
        entry["realization"] = float(realization_100.loc[idx])
        entry["financial"] = float(financial_100.loc[idx])
        history.append(entry)

    current_value = float(composite_100.iloc[-1])
    trpf_component = float(trpf_100.iloc[-1])
    realization_component = float(realization_100.iloc[-1])
    financial_component = float(financial_100.iloc[-1])

    logger.info(
        "crisis_index_computed",
        current_value=round(current_value, 2),
        trpf=round(trpf_component, 2),
        realization=round(realization_component, 2),
        financial=round(financial_component, 2),
        weights_source="learned" if learned_weights_info else "manual",
    )

    result = {
        "current_value": current_value,
        "trpf_component": trpf_component,
        "realization_component": realization_component,
        "financial_component": financial_component,
        "history": history,
    }

    if learned_weights_info:
        result["learned_weights"] = {
            "weights": learned_weights_info["weights"],
            "cv_auc": learned_weights_info["accuracy"],
            "n_train": learned_weights_info["n_train"],
        }

    return result
