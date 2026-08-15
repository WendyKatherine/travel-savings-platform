"""
travel_goal_repository.py - Postgres-backed TravelGoalRepository.

Translates between the domain and the ORM worlds: TravelGoal (domain)
in, TravelGoalModel (ORM) out. The ORM never escapes this class.

The repository joins transactions but never closes them: the caller
owns the session and decides when to commit (Unit of Work seed).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.travel_goal_repository import TravelGoalRepository
from app.domain.entities.travel_goal import Status, TravelGoal
from app.domain.value_objects.money import Money
from app.infrastructure.persistence.travel_goal import TravelGoalModel


class PostgresTravelGoalRepository(TravelGoalRepository):
    """TravelGoalRepository implementation backed by async SQLAlchemy/Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, goal: TravelGoal) -> None:
        """Translate domain -> ORM and register the row on the session (no commit)."""
        model = TravelGoalModel(
            id=goal.id,
            owner_id=goal.owner_id,
            destination=goal.destination,
            target_amount=goal.target.amount,
            target_currency=goal.target.currency,
            created_at=goal.created_at,
            status=goal.status.value,
        )
        self._session.add(model)

    async def get_by_id(self, goal_id: UUID) -> TravelGoal | None:
        """Translate ORM -> domain. Returns None when the goal does not exist."""
        result = await self._session.execute(
            select(TravelGoalModel).where(TravelGoalModel.id == goal_id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return TravelGoal(
            id=model.id,
            owner_id=model.owner_id,
            destination=model.destination,
            target=Money(model.target_amount, model.target_currency),
            created_at=model.created_at,
            status=Status(model.status),
        )
