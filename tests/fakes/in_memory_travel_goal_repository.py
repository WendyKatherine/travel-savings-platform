"""
in_memory_travel_goal_repository.py — In-memory fake of TravelGoalRepository.

Test double that implements the persistence port backed by a plain dict.
It lets the use case run in tests without a database, and proves the
dependency-inversion point: the same use case works with this fake today
and with Postgres tomorrow, unchanged.
"""

from uuid import UUID

from app.application.ports.travel_goal_repository import TravelGoalRepository
from app.domain.entities.travel_goal import TravelGoal


class InMemoryTravelGoalRepository(TravelGoalRepository):
    """In-memory TravelGoalRepository for tests. Stores goals in a dict."""

    def __init__(self) -> None:
        """Start with an empty store: goal id -> TravelGoal."""
        self._goals: dict[UUID, TravelGoal] = {}

    async def save(self, goal: TravelGoal) -> None:
        """
        Persist a travel goal in memory.

        Stores the goal keyed by its id (upsert: a repeated id overwrites).
        """
        self._goals[goal.id] = goal

    async def get_by_id(self, goal_id: UUID) -> TravelGoal | None:
        """
        Retrieve a travel goal by id.

        Returns the goal if present, otherwise None.
        """
        return self._goals.get(goal_id)
