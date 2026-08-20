"""add idempotency_key to transactions

Revision ID: 2e96737bf2e0
Revises: 0b24096b2e58
Create Date: 2026-08-19 19:56:20.672074
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2e96737bf2e0"
down_revision: str | None = "0b24096b2e58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the UNIQUE idempotency_key column (the durable idempotency guarantee)."""
    op.add_column("transactions", sa.Column("idempotency_key", sa.Uuid(), nullable=False))
    op.create_unique_constraint(
        op.f("uq_transactions_idempotency_key"), "transactions", ["idempotency_key"]
    )


def downgrade() -> None:
    """Drop the constraint first, then the column (order matters)."""
    op.drop_constraint(op.f("uq_transactions_idempotency_key"), "transactions", type_="unique")
    op.drop_column("transactions", "idempotency_key")
