"""Импорт календарного графика из файла (ТЗ, п. 3; F11).

Импорт заменяет график объекта целиком. Поверх существующего графика — только с `force`:
иначе одна загрузка файла молча стёрла бы ручные правки дат и правил.
"""

from dataclasses import asdict
from typing import Any
from uuid import UUID, uuid4

from lct_common import ConflictError, ValidationError, get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.analysis_client import AnalysisClient
from src.config import settings
from src.core.plan_import import ImportedStage, PlanImportError, parse_schedule, read_table
from src.dal.models import Stage, StageRule
from src.dal.repositories.stages import StageRepository
from src.services.critical_path import calendar_of, refresh_critical_path, to_work_calendar
from src.services.objects import ObjectService
from src.services.plan_version import PlanVersion
from src.templates import template_for, vocabulary

log = get_logger(__name__)


class PlanImportInvalid(ValidationError):
    code = "PLAN_IMPORT_INVALID"


class PlanAlreadyExists(ConflictError):
    code = "PLAN_ALREADY_EXISTS"


class PlanImportService:
    def __init__(self, session: AsyncSession, signal: AnalysisClient) -> None:
        self._session = session
        self._objects = ObjectService(session)
        self._stages = StageRepository(session)
        self._plan_version = PlanVersion(session, signal)

    async def import_file(
        self, object_id: UUID, filename: str, content: bytes, *, force: bool, actor: str | None
    ) -> dict[str, Any]:
        obj = await self._objects.get(object_id)
        if len(content) > settings.plan_import_max_mb * 1024 * 1024:
            raise PlanImportInvalid(
                f"Файл больше {settings.plan_import_max_mb} МБ",
                limit_mb=settings.plan_import_max_mb,
            )
        if await self._stages.all_for_object(object_id) and not force:
            raise PlanAlreadyExists(
                "У объекта уже есть график: импорт заменит его целиком, передайте force=true",
                object_id=str(object_id),
            )
        calendar = to_work_calendar(await calendar_of(self._session, obj))
        try:
            parsed = parse_schedule(
                read_table(filename, content), template_for(obj.object_type), vocabulary(), calendar
            )
        except PlanImportError as exc:
            raise PlanImportInvalid(
                str(exc), errors=[asdict(issue) for issue in exc.issues]
            ) from exc

        stages, rules = _rows(object_id, parsed)
        await self._stages.replace_for_object(object_id, stages)
        self._session.add_all(rules)
        if obj.plan_start is None:
            # Начало СМР — от него analysis запрашивает факты (interservice.md, раздел 1).
            obj.plan_start = min(s.plan_start for s in parsed)
        await self._session.flush()
        await refresh_critical_path(self._session, [object_id])
        critical = sum(1 for s in stages if s.is_critical)
        await self._plan_version.changed([object_id])
        await self._session.refresh(obj)
        log.info("plan.imported", object_id=str(object_id), stages=len(stages), actor=actor)
        return {
            "object_id": object_id,
            "plan_version": obj.plan_version,
            "stages": len(stages),
            "rules": len(rules),
            "critical_stages": critical,
        }


def _rows(object_id: UUID, parsed: list[ImportedStage]) -> tuple[list[Stage], list[StageRule]]:
    """Строки базы: id вех задаются заранее, чтобы связи ссылались на них по UUID."""
    ids = {s.code: uuid4() for s in parsed}
    stages, rules = [], []
    for item in parsed:
        stages.append(
            Stage(
                id=ids[item.code],
                object_id=object_id,
                code=item.code,
                work_codes=list(item.work_codes),
                name=item.name,
                phase=item.phase,
                seq=item.seq,
                zone_type=item.zone_type,
                visual_stage=item.visual_stage,
                plan_start=item.plan_start,
                plan_end=item.plan_end,
                norm_duration_days=item.norm_duration_days,
                predecessors=[
                    {"stage_id": str(ids[p.code]), "type": p.type, "lag_days": p.lag_days}
                    for p in item.predecessors
                ],
                source="IMPORT",
                basis=item.basis,
            )
        )
        if item.rule is not None:
            signature = item.rule.get("signature") or {}
            rules.append(
                StageRule(
                    stage_id=ids[item.code],
                    required=item.rule.get("required") or [],
                    allowed=item.rule.get("allowed") or [],
                    signature={
                        "equipment": signature.get("equipment") or [],
                        "stage_label": signature.get("stage_label"),
                    },
                )
            )
    return stages, rules
