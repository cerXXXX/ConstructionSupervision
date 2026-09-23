"""Запросы к analysis_run. Единственное место, где есть SQL по прогонам."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.dal.models import AnalysisRun


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, run: AnalysisRun) -> AnalysisRun:
        self._session.add(run)
        await self._session.flush()
        # id, статус и время задаёт база: перечитываем, чтобы отдать их в ответе.
        await self._session.refresh(run)
        return run

    async def get(self, run_id: UUID) -> AnalysisRun | None:
        return await self._session.get(AnalysisRun, run_id)
