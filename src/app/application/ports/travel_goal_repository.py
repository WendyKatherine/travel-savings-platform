"""
travel_goal_repository.py — Port for TravelGoal persistence.

Contract that the application layer needs to persist and retrieve
travel goals. It defines WHAT can be done, never HOW:
implementations live in infrastructure (in-memory fake for tests,
async SQLAlchemy/Postgres in production).
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.travel_goal import TravelGoal


class TravelGoalRepository(ABC):
    """Persistence contract for TravelGoal, agnostic to the storage technology."""

    @abstractmethod
    async def save(self, goal: TravelGoal) -> None:
        """
        Persist a travel goal.

        Receives a fully constructed TravelGoal (identity and invariants
        already validated) and stores it. Returns nothing.
        """
        ...

    @abstractmethod
    async def get_by_id(self, goal_id: UUID) -> TravelGoal | None:
        """
        Retrieve a travel goal by its id.

        Returns the goal if it exists, otherwise None.
        """
        ...
