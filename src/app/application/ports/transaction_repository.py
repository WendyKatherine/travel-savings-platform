"""
transaction_repository.py — Port for Transaction persistence.

Contract that the application layer needs to persist ledger entries.
It defines WHAT can be done, never HOW: implementations live in
infrastructure (in-memory fake for tests, async SQLAlchemy/Postgres
in production).
"""

from abc import ABC, abstractmethod

from app.domain.entities.transaction import Transaction


class TransactionRepository(ABC):
    """Persistence contract for Transaction, agnostic to the storage technology."""

    @abstractmethod
    async def save(self, transaction: Transaction) -> None:
        """
        Persist a ledger entry.

        Receives a fully constructed Transaction (invariants already
        validated by the domain) and stores it. Returns nothing.
        """
        ...

    # Future (not needed by this slice): list_by_goal(goal_id) -> Sequence[Transaction]
    # Required later to compute balances from the ledger.
