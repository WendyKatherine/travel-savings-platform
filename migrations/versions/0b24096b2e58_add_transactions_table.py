"""add transactions table

Revision ID: 0b24096b2e58
Revises: 65f9c24ceff1
Create Date: 2026-08-18 23:15:45.761131
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0b24096b2e58"
down_revision: str | None = "65f9c24ceff1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the ``transactions`` ledger table with its FK to travel_goals.

    Written by hand: autogenerate proposed dropping ``travel_goals``
    because the ORM models were not registered on ``Base.metadata``
    (migrations/env.py now imports them).
    """
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("amount_value", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("amount_currency", sa.String(length=3), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.ForeignKeyConstraint(
            ["goal_id"],
            ["travel_goals.id"],
            name=op.f("fk_transactions_goal_id_travel_goals"),
        ),
    )


def downgrade() -> None:
    """Drop the ``transactions`` table (FK goes away with it)."""
    op.drop_table("transactions")
