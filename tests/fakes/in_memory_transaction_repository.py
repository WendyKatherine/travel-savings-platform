"""
in_memory_transaction_repository.py — In-memory fake of TransactionRepository.

Test double that implements the persistence port backed by a plain
append-only list, mirroring the ledger semantics of the domain.
It lets the use case run in tests without a database, and proves the
dependency-inversion point: the same use case works with this fake today
and with Postgres tomorrow, unchanged.
"""

from app.application.ports.transaction_repository import TransactionRepository
from app.domain.entities.transaction import Transaction


class InMemoryTransactionRepository(TransactionRepository):
    """In-memory TransactionRepository for tests. Stores transactions in a list."""

    def __init__(self) -> None:
        """Start with an empty ledger."""
        self._transactions: list[Transaction] = []

    async def save(self, transaction: Transaction) -> None:
        """Append the ledger entry to the in-memory store."""
        self._transactions.append(transaction)

    @property
    def saved(self) -> list[Transaction]:
        """All transactions stored so far (test inspection)."""
        return self._transactions
