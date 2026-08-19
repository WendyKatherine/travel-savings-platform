"""
goals.py — HTTP endpoints for travel goals.

POST /goals is the entry point of the vertical slice: it translates the
validated JSON into domain types (Money), assembles the Postgres
repository and the CreateGoalUseCase, and returns the public
GoalResponse. GET /goals/{goal_id} reuses the same wiring for reads, and
POST /goals/{goal_id}/deposits records a ledger entry against a goal.
Business rules live in the use cases, never here.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.create_goal import CreateGoalUseCase
from app.application.use_cases.get_goal import GetGoalUseCase
from app.application.use_cases.record_deposit import RecordDepositUseCase
from app.domain.value_objects.money import Money
from app.infrastructure.persistence.transaction_repository import PostgresTransactionRepository
from app.infrastructure.persistence.travel_goal_repository import PostgresTravelGoalRepository
from app.interface.api.dependencies import get_db_session
from app.interface.schemas.goals import CreateGoalRequest, GoalResponse
from app.interface.schemas.transactions import CreateDepositRequest, DepositResponse

router = APIRouter(prefix="/goals", tags=["goals"])
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("", status_code=201, response_model=GoalResponse)
async def create_goal(payload: CreateGoalRequest, session: SessionDep) -> GoalResponse:
    """
    Create a new travel goal.

    Translates the request into a Money (the only place where that
    translation happens), wires the repository and the use case, and
    returns the created goal as the public API contract.

    Raises:
        DomainError: propagated to the app-level exception handler,
            which maps domain rejections to HTTP 400.
    """
    target = Money(payload.target_amount, payload.currency)
    repo = PostgresTravelGoalRepository(session)
    use_case = CreateGoalUseCase(goal_port=repo)
    goal = await use_case.execute(
        owner_id=payload.owner_id,
        destination=payload.destination,
        target=target,
    )
    return GoalResponse.from_goal(goal)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: UUID, session: SessionDep) -> GoalResponse:
    """
    Retrieve a single travel goal by its id.

    Args:
        goal_id: UUID of the goal, taken from the path. FastAPI rejects
            a malformed id with 422 before this function runs.

    Returns:
        The goal as the public GoalResponse contract.

    Raises:
        HTTPException: 404 when no goal exists with the given id.
    """
    repo = PostgresTravelGoalRepository(session)
    use_case = GetGoalUseCase(goal_port=repo)
    goal = await use_case.execute(goal_id=goal_id)

    if goal is None:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")

    return GoalResponse.from_goal(goal)


@router.post("/{goal_id}/deposits", status_code=201, response_model=DepositResponse)
async def record_deposit(
    goal_id: UUID, payload: CreateDepositRequest, session: SessionDep
) -> DepositResponse:
    """
    Record a deposit against an existing goal (append-only ledger entry).

    Translates the request into a Money at the boundary, wires both
    Postgres repositories and the RecordDepositUseCase, and returns the
    created ledger entry as the public API contract.

    Raises:
        HTTPException: 404 when no goal exists with the given id.
        DomainError: propagated to the app-level exception handler,
            which maps domain rejections to HTTP 400.
    """
    amount = Money(payload.amount, payload.currency)
    goal_repo = PostgresTravelGoalRepository(session)
    txn_repo = PostgresTransactionRepository(session)
    use_case = RecordDepositUseCase(goal_port=goal_repo, transaction_port=txn_repo)
    transaction = await use_case.execute(
        goal_id=goal_id,
        amount=amount,
        recorded_by=payload.recorded_by,
    )

    if transaction is None:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")

    return DepositResponse.from_transaction(transaction)
