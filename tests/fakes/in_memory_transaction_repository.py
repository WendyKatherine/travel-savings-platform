"""
in_memory_transaction_repository.py — In-memory fake of TransactionRepository.

Test double that implements the persistence port backed by a dict keyed
by ``idempotency_key``, mirroring the UNIQUE constraint of the real
database. It lets the use case run in tests without a database, and
proves the dependency-inversion point: the same use case works with this
fake today and with Postgres tomorrow, unchanged.

Honest limitation: the fake has no real unique constraint, so the
IntegrityError branch of the idempotent flow cannot be exercised here —
that part is covered by integration tests against real Postgres.
"""

from uuid import UUID

from app.application.ports.transaction_repository import TransactionRepository
from app.domain.entities.transaction import Transaction


class InMemoryTransactionRepository(TransactionRepository):
    """In-memory TransactionRepository for tests, keyed by idempotency_key."""

    def __init__(self) -> None:
        """Start with an empty ledger."""
        self._by_key: dict[UUID, Transaction] = {}

    async def save(self, transaction: Transaction, idempotency_key: UUID) -> None:
        """Store the ledger entry indexed by its idempotency key."""
        self._by_key[idempotency_key] = transaction

    async def get_by_idempotency_key(self, key: UUID) -> Transaction | None:
        """Return the entry stored under the key, or None when there is none."""
        return self._by_key.get(key)

    @property
    def saved(self) -> list[Transaction]:
        """All transactions stored so far (test inspection)."""
        return list(self._by_key.values())
