"""Вехи графика: список объекта и ручная правка дат, участка, длительности и стадии по фото."""

from uuid import UUID

from lct_common import NotFoundError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.stages import StageUpdate
from src.clients.analysis_client import AnalysisClient
from src.core.stages import StageDatesError, StageError, check_stage
from src.dal.models import Stage, StageRule
from src.dal.repositories.rules import RuleRepository
from src.dal.repositories.stages import StageRepository
from src.reference import reference
from src.services.objects import ObjectService
from src.services.plan_version import PlanVersion

# Поля, которые можно явно обнулить; остальные null в правке означает «не менять».
NULLABLE = frozenset({"visual_stage"})


class StageNotFound(NotFoundError):
    code = "STAGE_NOT_FOUND"

    def __init__(self, stage_id: UUID) -> None:
        super().__init__("Веха не найдена", stage_id=str(stage_id))


class InvalidDateRange(ValidationError):
    code = "INVALID_DATE_RANGE"


class InvalidZoneType(ValidationError):
    code = "INVALID_ZONE_TYPE"


class StageService:
    def __init__(self, session: AsyncSession, signal: AnalysisClient) -> None:
        self._session = session
        self._repo = StageRepository(session)
        self._rules = RuleRepository(session)
        self._plan_version = PlanVersion(session, signal)

    async def get(self, stage_id: UUID) -> Stage:
        stage = await self._repo.get(stage_id)
        if stage is None:
            raise StageNotFound(stage_id)
        return stage

    async def rule_of(self, stage: Stage) -> StageRule | None:
        return await self._rules.by_stage(stage.id)

    async def list_for_object(
        self, object_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Stage], int, dict[UUID, StageRule]]:
        """Страница вех, общее число и правила этих вех по id вехи."""
        await ObjectService(self._session).get(object_id)
        stages, total = await self._repo.list_for_object(object_id, limit=limit, offset=offset)
        return stages, total, await self._rules.by_stages([s.id for s in stages])

    async def update(self, stage_id: UUID, payload: StageUpdate) -> Stage:
        """Правка вехи. Критический путь пересчитывается в T19 вместе с core/cpm.py."""
        stage = await self.get(stage_id)
        changes = {
            k: v
            for k, v in payload.model_dump(exclude_unset=True).items()
            if v is not None or k in NULLABLE
        }
        try:
            check_stage(
                changes.get("plan_start", stage.plan_start),
                changes.get("plan_end", stage.plan_end),
                changes.get("zone_type", stage.zone_type),
                reference().zone_roles,
            )
        except StageDatesError as exc:
            raise InvalidDateRange(str(exc), stage_id=str(stage_id)) from exc
        except StageError as exc:
            raise InvalidZoneType(str(exc), stage_id=str(stage_id)) from exc

        for field, value in changes.items():
            setattr(stage, field, value)
        stage = await self._repo.save(stage)
        if changes:
            await self._plan_version.changed([stage.object_id])
        return stage
