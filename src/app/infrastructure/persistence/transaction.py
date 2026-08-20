"""
transaction.py — ORM model for the ``transactions`` table.

Pure SQLAlchemy mapping: it stores what the domain says, it does not
validate business rules (that is ``Transaction``'s job in the domain layer).

Design rules (same as TravelGoalModel):
- No defaults here: ``id``, ``recorded_at`` and ``idempotency_key`` are
  generated at the application boundary and only stored by this table.
- ``goal_id`` is a FK to ``travel_goals.id`` — the first relation between
  tables; ledger entries always reference an existing goal.
- ``idempotency_key`` is UNIQUE: Postgres is the arbiter. Two rows with
  the same key are physically impossible — that constraint is the
  foundation of durable idempotency (a retried request carries the same
  key, and the database rejects the duplicate instead of the app having
  to guess).
- This module must never import from ``app.domain``: the repository
  (infrastructure) is the only bridge between the two worlds.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


class TransactionModel(Base):
    """Persistence counterpart of the domain ``Transaction``.

    Maps a ledger entry to the ``transactions`` table:

    - ``id``: UUID (native Postgres type), primary key.
    - ``goal_id``: FK to ``travel_goals.id`` — ledger entries always
      reference an existing goal.
    - ``idempotency_key``: UNIQUE key that makes a deposit retry-safe —
      the boundary generates it and Postgres rejects a second row with
      the same key (the durable idempotency guarantee).
    - ``amount_value``: numeric part of the Money, ``Numeric(18, 2)`` —
      money is never a float.
    - ``amount_currency``: ISO 4217 code, fixed 3 characters.
    - ``kind``: string form of ``Kind`` (e.g. ``"DEPOSIT"``).
    - ``recorded_at``: timezone-aware timestamp (never naive).
    - ``recorded_by``: editor id who registered the movement (audit trail).

    Design rules (same as TravelGoalModel):
    - No defaults here: ``id`` and ``recorded_at`` come from the boundary.
    - Never import from ``app.domain``: the repository is the only bridge.
    """

    __tablename__ = "transactions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    goal_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("travel_goals.id"))
    idempotency_key: Mapped[UUID] = mapped_column(Uuid, unique=True, nullable=False)
    amount_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    amount_currency: Mapped[str] = mapped_column(String(3))
    kind: Mapped[str]
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[str]
