"""
transaction_repository.py — Postgres-backed TransactionRepository.

Translates between the domain and the ORM worlds: Transaction (domain)
in, TransactionModel (ORM) out. The ORM never escapes this class.

The repository joins the session but never closes it: the caller owns
the transaction boundary (Unit of Work), exactly like
PostgresTravelGoalRepository.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.transaction_repository import TransactionRepository
from app.domain.entities.transaction import Transaction
from app.infrastructure.persistence.transaction import TransactionModel


class PostgresTransactionRepository(TransactionRepository):
    """TransactionRepository implementation backed by async SQLAlchemy/Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, transaction: Transaction) -> None:
        """Translate domain -> ORM and register the row on the session (no commit)."""
        model = TransactionModel(
            id=transaction.id,
            goal_id=transaction.goal_id,
            amount_value=transaction.amount.amount,
            amount_currency=transaction.amount.currency,
            kind=transaction.kind.value,
            recorded_at=transaction.recorded_at,
            recorded_by=transaction.recorded_by,
        )
        self._session.add(model)
