"""
transaction_repository.py — Port for Transaction persistence.

Contract that the application layer needs to persist ledger entries.
It defines WHAT can be done, never HOW: implementations live in
infrastructure (in-memory fake for tests, async SQLAlchemy/Postgres
in production).
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.transaction import Transaction


class TransactionRepository(ABC):
    """Persistence contract for Transaction, agnostic to the storage technology."""

    @abstractmethod
    async def save(self, transaction: Transaction, idempotency_key: UUID) -> None:
        """
        Persist a ledger entry bound to its idempotency key.

        Receives a fully constructed Transaction (invariants already
        validated by the domain) plus the idempotency key of the request
        that produced it. The key is a persistence detail, not a domain
        one: it is attached to the row here, at the port boundary, and
        the storage implementation is responsible for enforcing its
        uniqueness (the durable idempotency guarantee).

        The implementation must make the insert collide eagerly (flush)
        so a repeated key surfaces immediately as an error the caller
        can react to (the replay path). Returns nothing.
        """
        ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: UUID) -> Transaction | None:
        """
        Fetch the ledger entry previously stored under an idempotency key.

        This is the "replay" lookup: when the insert collides with the
        UNIQUE constraint (durable idempotency), the caller retrieves the
        entry that already exists and returns it instead of failing.

        Args:
            key: The idempotency key of the original request.

        Returns:
            The existing Transaction, or None when no entry was stored
            under that key yet.
        """
        ...

    # Future (not needed by this slice): list_by_goal(goal_id) -> Sequence[Transaction]
    # Required later to compute balances from the ledger.
