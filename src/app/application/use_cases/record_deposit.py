"""
record_deposit.py — Use case that orchestrates recording a deposit.

Sits between the interface layer (endpoint) and the persistence ports.
It owns the boundary: generates the transaction's identity and timestamp,
receives the idempotency key from the caller, delegates validation to the
domain aggregate, and persists the ledger entry through the ports.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.application.ports.transaction_repository import TransactionRepository
from app.application.ports.travel_goal_repository import TravelGoalRepository
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money


class RecordDepositUseCase:
    """
    Records a deposit against an existing travel goal.

    Depends on two persistence ports (constructor injection), never on
    concrete storage implementations. Knows nothing about HTTP, JSON or
    SQL — only domain types and the ports.
    """

    def __init__(
        self, goal_port: TravelGoalRepository, transaction_port: TransactionRepository
    ) -> None:
        """
        Inject the two persistence contracts.

        The use case stores the interfaces, not implementations: the same
        use case works with the in-memory fakes (tests) and with Postgres
        (production).
        """
        self.goal_port = goal_port
        self.transaction_port = transaction_port

    async def execute(
        self,
        goal_id: UUID,
        amount: Money,
        recorded_by: str,
        idempotency_key: UUID,
    ) -> Transaction | None:
        """
        Record a deposit and persist it as a ledger entry.

        Args:
            goal_id:         Id of the goal receiving the deposit.
            amount:          Positive Money amount to deposit.
            recorded_by:     Editor id who registered the deposit (audit trail).
            idempotency_key: Key that makes the deposit retry-safe. On a
                replay (same key twice) the stored entry is returned
                instead of inserting a duplicate.

        Returns:
            The created Transaction (kind DEPOSIT), or None when no goal
            exists with the given id (the interface layer maps that to 404).

        Raises:
            TravelGoalError: Propagated from the aggregate when a domain
                invariant is violated (non-active goal, currency mismatch).
        """
        goal = await self.goal_port.get_by_id(goal_id)
        if goal is None:
            return None

        transaction_id = uuid4()
        recorded_at = datetime.now(UTC)

        transaction = goal.record_deposit(
            amount,
            id=transaction_id,
            recorded_at=recorded_at,
            recorded_by=recorded_by,
        )
        try:
            await self.transaction_port.save(transaction, idempotency_key)
        except IntegrityError:
            return await self.transaction_port.get_by_idempotency_key(idempotency_key)

        return transaction
