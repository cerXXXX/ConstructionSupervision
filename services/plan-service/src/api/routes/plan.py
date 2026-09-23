"""«Весь план» объекта — межсервисный контракт 1 (interservice.md, раздел 1)."""

from uuid import UUID

from fastapi import APIRouter

from src.api.deps import SessionDep
from src.api.schemas.plan import Plan
from src.services.plan import PlanService

router = APIRouter(prefix="/objects/{object_id}/plan", tags=["График"])


@router.get(
    "",
    response_model=Plan,
    summary="Весь план объекта",
    description="Вехи по `seq`, связи, правила, календарь и классы техники одним ответом. "
    "Объект без вех — не ошибка: `stages: []`. Выключенное правило приходит как `rule: null`.",
)
async def get_plan(object_id: UUID, session: SessionDep):
    return await PlanService(session).get_plan(object_id)
