"""
create_goal.py — Use case that orchestrates the creation of a TravelGoal.

Sits between the interface layer (endpoint, tomorrow) and the persistence
port. It owns the boundary: generates the entity's identity and timestamp,
delegates construction to the domain, and persists through the port.
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.application.ports.travel_goal_repository import TravelGoalRepository
from app.domain.entities.travel_goal import TravelGoal
from app.domain.value_objects.money import Money


class CreateGoalUseCase:
    """
    Creates a TravelGoal and persists it.

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

    async def execute(self, owner_id: str, destination: str, target: Money) -> TravelGoal:
        """
        Create and persist a new travel goal.

        Generates the identity and creation timestamp at the boundary,
        builds the TravelGoal via the domain factory (which validates
        the invariants) and saves it through the port.

        Args:
            owner_id:     Id of the user who owns the goal.
            destination:  Travel destination or package name.
            target:       Target amount, already built as a Money.

        Returns:
            The created TravelGoal.

        Raises:
            ValueError:   Propagated from the entity when a domain
                          invariant is violated (e.g. empty destination
                          or non-positive target).
        """
        goal_id = uuid4()
        created_at = datetime.now(UTC)

        goal = TravelGoal.create(
            id=goal_id,
            owner_id=owner_id,
            destination=destination,
            target=target,
            created_at=created_at,
        )

        await self.goal_port.save(goal)
        return goal
