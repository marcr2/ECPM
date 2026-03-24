"""Input-Output tables: io_metadata and io_cells.

Revision ID: 003
Revises: 001
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "003"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create io_metadata and io_cells tables with indexes."""
    # io_metadata -- stores metadata about I-O tables
    op.create_table(
        "io_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("table_type", sa.String(20), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=True),
        sa.Column("num_industries", sa.Integer(), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "source",
            sa.String(100),
            nullable=False,
            server_default="BEA InputOutput",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "table_type", name="uq_io_metadata_year_type"),
    )

    # Indexes for io_metadata
    op.create_index("ix_io_metadata_year", "io_metadata", ["year"])
    op.create_index("ix_io_metadata_year_type", "io_metadata", ["year", "table_type"])

    # io_cells -- stores individual cell values
    op.create_table(
        "io_cells",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("row_code", sa.String(20), nullable=False),
        sa.Column("col_code", sa.String(20), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("row_description", sa.String(200), nullable=True),
        sa.Column("col_description", sa.String(200), nullable=True),
        sa.Column("table_type", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for io_cells
    op.create_index("ix_io_cells_year_row", "io_cells", ["year", "row_code"])
    op.create_index("ix_io_cells_year_col", "io_cells", ["year", "col_code"])
    op.create_index("ix_io_cells_year_type", "io_cells", ["year", "table_type"])
    op.create_index(
        "ix_io_cells_year_type_row_col",
        "io_cells",
        ["year", "table_type", "row_code", "col_code"],
    )


def downgrade() -> None:
    """Drop io_cells and io_metadata tables."""
    op.drop_table("io_cells")
    op.drop_table("io_metadata")
