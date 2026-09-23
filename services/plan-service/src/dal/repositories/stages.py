"""Запросы к таблице stage."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dal.models import Stage


class StageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, stage_id: UUID) -> Stage | None:
        return await self._session.get(Stage, stage_id)

    async def list_for_object(
        self, object_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Stage], int]:
        """Вехи объекта в порядке графика (seq)."""
        query = select(Stage).where(Stage.object_id == object_id)
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self._session.scalars(
            query.order_by(Stage.seq, Stage.plan_start).limit(limit).offset(offset)
        )
        return list(rows), int(total or 0)

    async def save(self, stage: Stage) -> Stage:
        await self._session.flush()
        await self._session.refresh(stage)
        return stage
