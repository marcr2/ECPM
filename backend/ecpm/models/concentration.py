"""SQLAlchemy models for corporate concentration data storage.

Stores concentration metrics (CR4, CR8, HHI) by NAICS sector,
individual firm market shares, and concentration trends over time.
"""

import datetime as dt
from typing import Optional

from sqlalchemy import Float, Integer, String, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from ecpm.models import Base


class IndustryConcentration(Base):
    """Concentration metrics for an industry in a given year.

    Stores CR4, CR8, HHI, and related metrics computed from
    Census Bureau Economic Census data.
    """

    __tablename__ = "industry_concentration"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    naics_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    naics_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cr4: Mapped[float] = mapped_column(Float, nullable=False)  # Top 4 firms share (0-100)
    cr8: Mapped[float] = mapped_column(Float, nullable=False)  # Top 8 firms share (0-100)
    hhi: Mapped[float] = mapped_column(Float, nullable=False)  # Herfindahl-Hirschman (0-10000)
    num_firms: Mapped[int] = mapped_column(Integer, nullable=False)
    total_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_updated: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_industry_concentration_year", "year"),
        Index("ix_industry_concentration_naics", "naics_code"),
        Index("ix_industry_concentration_year_naics", "year", "naics_code"),
        Index("ix_industry_concentration_naics_year", "naics_code", "year"),
    )

    def __repr__(self) -> str:
        return (
            f"<IndustryConcentration(year={self.year}, naics={self.naics_code!r}, "
            f"cr4={self.cr4:.1f}, hhi={self.hhi:.0f})>"
        )


class FirmMarketShare(Base):
    """Individual firm market share within an industry.

    Tracks top firms by market share for CR4 calculation
    and competitive analysis.
    """

    __tablename__ = "firm_market_share"

    firm_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    naics_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    firm_name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_share_pct: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_firm_market_share_year_naics", "year", "naics_code"),
        Index("ix_firm_market_share_naics_year", "naics_code", "year"),
        Index("ix_firm_market_share_parent", "parent_company"),
        Index("ix_firm_market_share_rank", "year", "naics_code", "rank"),
    )

    def __repr__(self) -> str:
        return (
            f"<FirmMarketShare(firm={self.firm_name!r}, year={self.year}, "
            f"share={self.market_share_pct:.1f}%)>"
        )


class ConcentrationTrend(Base):
    """Concentration trend analysis over a time period.

    Stores trend slope and direction for industries based on
    linear regression of concentration metrics over time.
    """

    __tablename__ = "concentration_trend"

    naics_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    start_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    trend_slope: Mapped[float] = mapped_column(Float, nullable=False)  # CR4 change per year
    trend_direction: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "increasing", "decreasing", "stable"
    r_squared: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_concentration_trend_naics", "naics_code"),
        Index("ix_concentration_trend_direction", "trend_direction"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConcentrationTrend(naics={self.naics_code!r}, "
            f"{self.start_year}-{self.end_year}, direction={self.trend_direction!r})>"
        )
