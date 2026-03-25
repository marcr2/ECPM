"""Add data_source to industry_concentration and cik to firm_market_share.

Tracks whether concentration metrics come from SEC EDGAR firm revenue,
Census Economic Census, or establishment-count estimates.

Revision ID: 005
Revises: 004
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add data provenance columns."""
    # Track where concentration metrics came from:
    # "edgar" = real firm revenue from SEC filings
    # "census" = Census Economic Census RCPTOT
    # "estimated" = heuristic from establishment counts
    op.add_column(
        "industry_concentration",
        sa.Column(
            "data_source",
            sa.String(20),
            nullable=True,
            server_default="estimated",
        ),
    )

    # Store SEC EDGAR CIK for firm traceability
    op.add_column(
        "firm_market_share",
        sa.Column("cik", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Remove data provenance columns."""
    op.drop_column("firm_market_share", "cik")
    op.drop_column("industry_concentration", "data_source")
