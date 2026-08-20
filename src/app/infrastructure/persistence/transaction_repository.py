"""
transaction_repository.py — Postgres-backed TransactionRepository.

Translates between the domain and the ORM worlds: Transaction (domain)
in, TransactionModel (ORM) out. The ORM never escapes this class.

The repository joins the session but never closes it: the caller owns
the transaction boundary (Unit of Work), exactly like
PostgresTravelGoalRepository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.transaction_repository import TransactionRepository
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money
from app.infrastructure.persistence.transaction import TransactionModel


class PostgresTransactionRepository(TransactionRepository):
    """TransactionRepository implementation backed by async SQLAlchemy/Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, transaction: Transaction, idempotency_key: UUID) -> None:
        """Translate domain -> ORM and register the row on the session (no commit)."""
        model = TransactionModel(
            id=transaction.id,
            goal_id=transaction.goal_id,
            idempotency_key=idempotency_key,
            amount_value=transaction.amount.amount,
            amount_currency=transaction.amount.currency,
            kind=transaction.kind.value,
            recorded_at=transaction.recorded_at,
            recorded_by=transaction.recorded_by,
        )
        self._session.add(model)

        try:
            await self._session.flush()  # the collision surfaces here, inside save
        except IntegrityError:
            await self._session.rollback()  # leave the session usable for the replay
            raise  # re-raise: the use case decides (replay or real error)

    async def get_by_idempotency_key(self, key: UUID) -> Transaction | None:
        """Translate ORM -> domain for the row stored under the key (or None)."""
        result = await self._session.execute(
            select(TransactionModel).where(TransactionModel.idempotency_key == key)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Transaction(
            id=model.id,
            goal_id=model.goal_id,
            amount=Money(model.amount_value, model.amount_currency),
            recorded_at=model.recorded_at,
            recorded_by=model.recorded_by,
        )
