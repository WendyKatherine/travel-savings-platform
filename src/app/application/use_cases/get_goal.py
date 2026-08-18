"""
get_goal.py — Use case that retrieves a TravelGoal by its id.

Sits between the interface layer (endpoint) and the persistence port.
It is a pure read: it delegates the lookup to the repository port and
returns whatever comes back — the goal, or None when it does not exist.
"""

from uuid import UUID

from app.application.ports.travel_goal_repository import TravelGoalRepository
from app.domain.entities.travel_goal import TravelGoal


class GetGoalUseCase:
    """
    Retrieves a single TravelGoal by id.

    Depends on the TravelGoalRepository port (constructor injection),
    never on a concrete storage implementation. Knows nothing about
    HTTP, JSON or SQL — only domain types and the port.
    """

    def __init__(self, goal_port: TravelGoalRepository) -> None:
        """
        Inject the persistence contract.

        The use case stores the interface, not an implementation:
        the same use case works with the in-memory fake (tests) and
        with Postgres (production).
        """
        self.goal_port = goal_port

    async def execute(self, goal_id: UUID) -> TravelGoal | None:
        """
        Retrieve a goal by its id.

        Args:
            goal_id: Id of the goal to look up.

        Returns:
            The TravelGoal if it exists, otherwise None.
        """
        return await self.goal_port.get_by_id(goal_id)
