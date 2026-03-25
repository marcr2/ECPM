"""Initial schema: series_metadata and observations tables.

Revision ID: 001
Revises:
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create series_metadata table, observations table, hypertable, and indexes."""
    # series_metadata -- regular PostgreSQL table
    op.create_table(
        "series_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("series_id", sa.String(50), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("source_detail", sa.JSON(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("units", sa.String(100), nullable=True),
        sa.Column("frequency", sa.String(1), nullable=False),
        sa.Column("seasonal_adjustment", sa.String(50), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_fetched", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observation_count", sa.Integer(), server_default="0"),
        sa.Column("fetch_status", sa.String(20), server_default="'pending'"),
        sa.Column("fetch_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("series_id"),
    )

    # Index on source for filtering by FRED/BEA
    op.create_index("ix_series_metadata_source", "series_metadata", ["source"])
    # Index on fetch_status for monitoring
    op.create_index(
        "ix_series_metadata_fetch_status", "series_metadata", ["fetch_status"]
    )

    # observations -- will become TimescaleDB hypertable
    op.create_table(
        "observations",
        sa.Column("observation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("series_id", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("vintage_date", sa.Date(), nullable=True),
        sa.Column("gap_flag", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("observation_date", "series_id"),
        sa.ForeignKeyConstraint(
            ["series_id"],
            ["series_metadata.series_id"],
            name="fk_observations_series_id",
        ),
    )

    # Convert to TimescaleDB hypertable with 1-year chunks to keep chunk count
    # manageable for multi-decade data (avoids max_locks_per_transaction exhaustion)
    op.execute(
        "SELECT create_hypertable('observations', 'observation_date', "
        "if_not_exists => TRUE, migrate_data => TRUE, "
        "chunk_time_interval => INTERVAL '1 year')"
    )

    # Index on series_id for per-series queries
    op.create_index("ix_observations_series_id", "observations", ["series_id"])

    # Composite index for series + date range lookups
    op.create_index(
        "ix_observations_series_date",
        "observations",
        ["series_id", "observation_date"],
    )

    # Partial unique index for vintage tracking:
    # When vintage_date is set, enforce uniqueness of (series_id, observation_date, vintage_date)
    op.execute(
        "CREATE UNIQUE INDEX ix_observations_vintage "
        "ON observations (series_id, observation_date, vintage_date) "
        "WHERE vintage_date IS NOT NULL"
    )


def downgrade() -> None:
    """Drop observations and series_metadata tables."""
    op.drop_table("observations")
    op.drop_table("series_metadata")
