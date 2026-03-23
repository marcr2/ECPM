"""Pydantic v2 response models for indicator API endpoints.

Defines the API contract for indicator data, overview summaries,
and methodology documentation endpoints.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict


class IndicatorDataPoint(BaseModel):
    """A single data point in an indicator time-series."""

    model_config = ConfigDict(from_attributes=True)

    date: dt.datetime
    value: float


class IndicatorResponse(BaseModel):
    """Full time-series response for a single indicator."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    units: str
    methodology: str
    frequency: str
    data: list[IndicatorDataPoint]
    latest_value: Optional[float] = None
    latest_date: Optional[dt.datetime] = None


class IndicatorSummary(BaseModel):
    """Summary card data for one indicator on the overview page."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    units: str
    latest_value: Optional[float] = None
    latest_date: Optional[dt.datetime] = None
    trend: Optional[str] = None  # "rising", "falling", "flat"
    sparkline: list[float] = []  # last N values for overview card


class IndicatorOverviewResponse(BaseModel):
    """Overview page response: all indicator summaries under one methodology."""

    model_config = ConfigDict(from_attributes=True)

    methodology: str
    indicators: list[IndicatorSummary]


class NIPAMappingDoc(BaseModel):
    """Documentation for one NIPA-to-Marx mapping."""

    model_config = ConfigDict(from_attributes=True)

    marx_category: str
    nipa_table: str
    nipa_line: int
    nipa_description: str
    operation: str
    notes: str = ""


class IndicatorMethodologyDoc(BaseModel):
    """Documentation for one indicator under a specific methodology."""

    model_config = ConfigDict(from_attributes=True)

    indicator_slug: str
    indicator_name: str
    formula_latex: str
    interpretation: str
    mappings: list[NIPAMappingDoc]
    citations: list[str]


class MethodologyDocResponse(BaseModel):
    """Full methodology documentation: all indicators under one methodology."""

    model_config = ConfigDict(from_attributes=True)

    methodology_slug: str
    methodology_name: str
    indicators: list[IndicatorMethodologyDoc]
