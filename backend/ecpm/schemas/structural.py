"""Pydantic v2 response models for structural analysis API endpoints.

Defines the API contract for I-O matrix data, shock simulation,
reproduction schema, and critical sector analysis.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class MatrixResponse(BaseModel):
    """Response containing an I-O matrix with labels and diagnostics."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    matrix: list[list[float]]
    row_labels: list[str]
    col_labels: list[str]
    matrix_type: str  # "coefficients", "inverse", "flows"
    diagnostics: Optional[dict] = None
    # BEA descriptions from ingestion (per axis code); empty if unavailable.
    row_display_labels: list[str] = Field(default_factory=list)
    col_display_labels: list[str] = Field(default_factory=list)


class ShockRequest(BaseModel):
    """Request body for shock simulation."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    shocks: dict[str, float]  # sector_code -> magnitude
    shock_type: Literal["supply", "demand"] = "demand"


class ShockImpact(BaseModel):
    """Individual sector impact from shock simulation."""

    model_config = ConfigDict(from_attributes=True)

    sector: str
    code: str
    impact: float


class ShockResultResponse(BaseModel):
    """Response from shock simulation."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    impacts: list[ShockImpact]
    total_impact: float
    shocked_sectors: list[str]


class DepartmentValues(BaseModel):
    """C/V/S values for one department."""

    model_config = ConfigDict(from_attributes=True)

    c: float  # Constant capital (see ReproductionResponse.constant_capital_unit)
    v: float  # Variable capital (see ReproductionResponse.labor_and_surplus_unit)
    s: float  # Surplus value


class ProportionalityCheck(BaseModel):
    """Result of Marx's reproduction proportionality check."""

    model_config = ConfigDict(from_attributes=True)

    i_v_plus_s: float
    ii_c: float
    simple_reproduction_holds: bool
    expanded_reproduction_holds: bool
    surplus_ratio: Optional[float] = None
    formula_display: str
    condition_met: bool


class SankeyNode(BaseModel):
    """Node in Sankey diagram."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    label: Optional[str] = None


class SankeyLink(BaseModel):
    """Link in Sankey diagram."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    target: str
    value: float
    color: Optional[str] = None  # green/red based on proportionality


class SankeyData(BaseModel):
    """Data structure for Sankey diagram visualization."""

    model_config = ConfigDict(from_attributes=True)

    nodes: list[SankeyNode]
    links: list[SankeyLink]


class ReproductionResponse(BaseModel):
    """Response for reproduction schema endpoint."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    dept_i: DepartmentValues
    dept_ii: DepartmentValues
    flows: list[list[float]]  # 2x2 inter-department flow matrix
    proportionality: ProportionalityCheck
    sankey_data: Optional[SankeyData] = None
    # c is only in millions_of_dollars when the BEA dollar Use table is used;
    # otherwise it is a dimensionless aggregate of technical coefficients.
    constant_capital_unit: str = "millions_of_dollars"
    # v/s follow FRED national totals: millions if paired with dollar Use, else billions.
    labor_and_surplus_unit: str = "millions_of_dollars"


class CriticalSector(BaseModel):
    """Critical sector with linkage metrics."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: Optional[str] = None
    backward_linkage: float
    forward_linkage: float
    multiplier: Optional[float] = None
    critical: bool


class CriticalSectorsResponse(BaseModel):
    """Response for critical sectors endpoint."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    sectors: list[CriticalSector]
    threshold: float


class YearsResponse(BaseModel):
    """Response listing available I-O table years."""

    model_config = ConfigDict(from_attributes=True)

    years: list[int]
