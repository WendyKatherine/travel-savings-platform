"""
travel_goal.py - ORM model for the ``travel_goals`` table.

Pure SQLAlchemy mapping: it stores what the domain says, it does not
validate business rules (that is ``TravelGoal``'s job in the domain layer).

Design rules:
- No defaults here: ``id`` and ``created_at`` are generated at the
  application boundary (CreateGoalUseCase) and only stored by this table.
- No relationships or foreign keys yet - the ledger (transactions) comes later.
- This module must never import from ``app.domain``: the repository
  (infrastructure) is the only bridge between the two worlds.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base

class TravelGoalModel(Base):
    """Persistence counterpart of the domain ``TravelGoal``.

    Maps the aggregate root to the ``travel_goals`` table:

    - ``id``: UUID (native Postgres type), primary key.
    - ``owner_id``: reference to the owning user.
    - ``destination``: travel destination or package name.
    - ``target_amount``: target as ``Numeric(18, 2)`` - money is never a
      float; the scale matches Money's 2-decimal invariant.
    - ``target_currency``: ISO 4217 code, fixed 3 characters.
    - ``created_at``: timezone-aware timestamp (never naive).
    - ``status``: string form of ``Status`` (e.g. ``"ACTIVE"``); the
      repository maps it back to the enum.
    """
    __tablename__="travel_goals"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    owner_id: Mapped[str] 
    destination: Mapped[str]
    target_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    target_currency: Mapped[str] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str]
    