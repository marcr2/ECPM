"""Pydantic v2 response models for concentration analysis API endpoints.

Defines the API contract for industry concentration data, correlations,
trend analysis, and department-level aggregations.
"""

from __future__ import annotations

from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict


class IndustryListItem(BaseModel):
    """Summary item for an industry in a list."""

    model_config = ConfigDict(from_attributes=True)

    naics: str
    name: str
    cr4: float
    hhi: float
    level: str  # "monopoly", "highly_concentrated", "moderately_concentrated", "competitive"
    trend_direction: str  # "increasing", "decreasing", "stable"


class IndustriesResponse(BaseModel):
    """Response listing industries with concentration metrics."""

    model_config = ConfigDict(from_attributes=True)

    industries: list[IndustryListItem]


class ConcentrationDataPoint(BaseModel):
    """Single data point in concentration time series."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    cr4: float
    cr8: float
    hhi: float


class TrendInfo(BaseModel):
    """Trend analysis results."""

    model_config = ConfigDict(from_attributes=True)

    slope: float
    direction: str  # "increasing", "decreasing", "stable"
    r_squared: float


class ConcentrationHistoryResponse(BaseModel):
    """Response with concentration history for an industry."""

    model_config = ConfigDict(from_attributes=True)

    naics: str
    name: str
    data: list[ConcentrationDataPoint]
    trend: TrendInfo


class FirmInfo(BaseModel):
    """Information about a firm's market position."""

    model_config = ConfigDict(from_attributes=True)

    rank: int
    name: str
    parent: Optional[str] = None
    market_share: float
    revenue: Optional[float] = None


class FirmsResponse(BaseModel):
    """Response with firm market share data."""

    model_config = ConfigDict(from_attributes=True)

    naics: str
    year: int
    firms: list[FirmInfo]


class CorrelationInfo(BaseModel):
    """Correlation between concentration and an indicator."""

    model_config = ConfigDict(from_attributes=True)

    indicator_slug: str
    indicator_name: str
    correlation: float
    confidence: float  # 0-100
    lag_months: int
    relationship: Literal["positive", "negative", "none"]


class CorrelationsResponse(BaseModel):
    """Response with correlations for an industry."""

    model_config = ConfigDict(from_attributes=True)

    naics: str
    name: str
    correlations: list[CorrelationInfo]


class TopCorrelationItem(BaseModel):
    """Top correlation entry across all industries."""

    model_config = ConfigDict(from_attributes=True)

    naics: str
    industry: str
    indicator_slug: str
    indicator_name: str
    correlation: float
    confidence: float


class TopCorrelationsResponse(BaseModel):
    """Response with strongest correlations across industries."""

    model_config = ConfigDict(from_attributes=True)

    correlations: list[TopCorrelationItem]


class DeptConcentration(BaseModel):
    """Concentration metrics for a Marxist department."""

    model_config = ConfigDict(from_attributes=True)

    cr4: float
    hhi: float
    trend_direction: str  # "increasing", "decreasing", "stable"


class OverviewResponse(BaseModel):
    """Overview response with department-level and highlight data."""

    model_config = ConfigDict(from_attributes=True)

    dept_i: DeptConcentration
    dept_ii: DeptConcentration
    most_concentrated: list[IndustryListItem]
    fastest_increasing: list[IndustryListItem]
