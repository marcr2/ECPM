"""Concentration tables: industry_concentration, firm_market_share, concentration_trend.

Revision ID: 004
Revises: 003
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create concentration tables with indexes."""
    # industry_concentration -- stores CR4/CR8/HHI by industry and year
    op.create_table(
        "industry_concentration",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("naics_code", sa.String(10), nullable=False),
        sa.Column("naics_name", sa.String(200), nullable=True),
        sa.Column("cr4", sa.Float(), nullable=False),
        sa.Column("cr8", sa.Float(), nullable=False),
        sa.Column("hhi", sa.Float(), nullable=False),
        sa.Column("num_firms", sa.Integer(), nullable=False),
        sa.Column("total_revenue", sa.Float(), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("year", "naics_code"),
    )

    # Indexes for industry_concentration
    op.create_index(
        "ix_industry_concentration_year", "industry_concentration", ["year"]
    )
    op.create_index(
        "ix_industry_concentration_naics", "industry_concentration", ["naics_code"]
    )
    op.create_index(
        "ix_industry_concentration_year_naics",
        "industry_concentration",
        ["year", "naics_code"],
    )
    op.create_index(
        "ix_industry_concentration_naics_year",
        "industry_concentration",
        ["naics_code", "year"],
    )

    # firm_market_share -- stores individual firm market shares
    op.create_table(
        "firm_market_share",
        sa.Column("firm_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("naics_code", sa.String(10), nullable=False),
        sa.Column("firm_name", sa.String(200), nullable=False),
        sa.Column("parent_company", sa.String(200), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("market_share_pct", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("firm_id"),
    )

    # Indexes for firm_market_share
    op.create_index("ix_firm_market_share_year", "firm_market_share", ["year"])
    op.create_index("ix_firm_market_share_naics", "firm_market_share", ["naics_code"])
    op.create_index(
        "ix_firm_market_share_year_naics", "firm_market_share", ["year", "naics_code"]
    )
    op.create_index(
        "ix_firm_market_share_naics_year", "firm_market_share", ["naics_code", "year"]
    )
    op.create_index(
        "ix_firm_market_share_parent", "firm_market_share", ["parent_company"]
    )
    op.create_index(
        "ix_firm_market_share_rank", "firm_market_share", ["year", "naics_code", "rank"]
    )

    # concentration_trend -- stores trend analysis
    op.create_table(
        "concentration_trend",
        sa.Column("naics_code", sa.String(10), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=False),
        sa.Column("end_year", sa.Integer(), nullable=False),
        sa.Column("trend_slope", sa.Float(), nullable=False),
        sa.Column("trend_direction", sa.String(20), nullable=False),
        sa.Column("r_squared", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("naics_code", "start_year"),
    )

    # Indexes for concentration_trend
    op.create_index(
        "ix_concentration_trend_naics", "concentration_trend", ["naics_code"]
    )
    op.create_index(
        "ix_concentration_trend_direction", "concentration_trend", ["trend_direction"]
    )


def downgrade() -> None:
    """Drop concentration tables."""
    op.drop_table("concentration_trend")
    op.drop_table("firm_market_share")
    op.drop_table("industry_concentration")
