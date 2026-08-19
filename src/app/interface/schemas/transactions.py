"""
transactions.py — API schemas for ledger transactions (deposits).

These Pydantic models are the public contract of the deposit endpoint,
kept separate from the Transaction domain entity: CreateDepositRequest
validates the raw JSON shape, and DepositResponse serializes the created
ledger entry so the API surface stays stable even if the domain internals
change. The Money value object is built at the endpoint boundary, never
inside the schema.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.transaction import Transaction


class CreateDepositRequest(BaseModel):
    """
    Input contract for POST /goals/{goal_id}/deposits.

    Only validates the shape and types of the raw JSON. amount stays a
    string to preserve exact decimal precision (no float round-trips),
    exactly like CreateGoalRequest.target_amount.
    """

    amount: str
    currency: str
    recorded_by: str


class DepositResponse(BaseModel):
    """
    Output contract for POST /goals/{goal_id}/deposits.

    The public shape of a created ledger entry. Never returns the
    Transaction domain entity directly: if the entity changes, the API
    does not break.
    """

    id: UUID
    goal_id: UUID
    amount: str
    kind: str
    recorded_at: datetime
    recorded_by: str

    @classmethod
    def from_transaction(cls, transaction: Transaction) -> "DepositResponse":
        """
        Build the API response from a domain Transaction.

        Formats the Money amount as a string (e.g. "COP 50,000.00") and
        serializes the kind enum to its plain value.
        """
        return cls(
            id=transaction.id,
            goal_id=transaction.goal_id,
            amount=str(transaction.amount),
            kind=transaction.kind.value,
            recorded_at=transaction.recorded_at,
            recorded_by=transaction.recorded_by,
        )
