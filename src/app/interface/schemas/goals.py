"""
goals.py — API schemas for travel goals.

These Pydantic models are the public contract of the API, kept separate
from the TravelGoal domain entity: CreateGoalRequest validates the raw
JSON shape, and GoalResponse serializes the created goal so the API
surface stays stable even if the domain internals change.
"""

from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.travel_goal import TravelGoal


class CreateGoalRequest(BaseModel):
    """
    Input contract for POST /goals.

    Only validates the shape and types of the raw JSON. The Money value
    object is built later, at the endpoint boundary: target_amount stays
    a string to preserve exact decimal precision (no float round-trips).
    """

    owner_id: str
    destination: str
    target_amount: str
    currency: str


class GoalResponse(BaseModel):
    """
    Output contract for POST /goals.

    The public shape of a created goal. Never returns the TravelGoal
    domain entity directly: if the entity changes, the API does not break.
    """

    id: UUID
    destination: str
    target: str
    status: str

    @classmethod
    def from_goal(cls, goal: TravelGoal) -> "GoalResponse":
        """
        Build the API response from a domain TravelGoal.

        Formats the Money target as a string (e.g. "COP 1,500,000.00")
        and serializes the status enum to its plain value.
        """
        return cls(
            id=goal.id,
            destination=goal.destination,
            target=str(goal.target),
            status=goal.status.value,
        )
