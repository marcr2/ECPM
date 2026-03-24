"""SQLAlchemy models for Input-Output table storage.

Stores I-O coefficient data in a normalized format with metadata
tracking and individual cell values for efficient querying.
"""

import datetime as dt
from typing import Optional

from sqlalchemy import Float, Integer, String, DateTime, func, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ecpm.models import Base


class IOMetadata(Base):
    """Metadata for stored Input-Output tables.

    Tracks which I-O tables have been fetched and stored, including
    year, table type, source, and update timestamps.
    """

    __tablename__ = "io_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    table_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "use", "make", "coefficients"
    table_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # BEA TableID
    num_industries: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # e.g., 71 for summary-level
    last_updated: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    source: Mapped[str] = mapped_column(
        String(100), default="BEA InputOutput", nullable=False
    )

    __table_args__ = (
        UniqueConstraint("year", "table_type", name="uq_io_metadata_year_type"),
        Index("ix_io_metadata_year_type", "year", "table_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<IOMetadata(year={self.year}, table_type={self.table_type!r}, "
            f"num_industries={self.num_industries})>"
        )


class IOCell(Base):
    """Individual cell of an Input-Output table.

    Stores each cell value with row/column codes and descriptions.
    Designed for efficient querying by year, row, or column.
    """

    __tablename__ = "io_cells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    row_code: Mapped[str] = mapped_column(String(20), nullable=False)
    col_code: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    row_description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    col_description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    table_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "coefficients", "use", "make"

    __table_args__ = (
        Index("ix_io_cells_year_row", "year", "row_code"),
        Index("ix_io_cells_year_col", "year", "col_code"),
        Index("ix_io_cells_year_type", "year", "table_type"),
        # Composite index for full cell lookup
        Index("ix_io_cells_year_type_row_col", "year", "table_type", "row_code", "col_code"),
    )

    def __repr__(self) -> str:
        return (
            f"<IOCell(year={self.year}, row={self.row_code!r}, "
            f"col={self.col_code!r}, value={self.value})>"
        )
