"""«Весь план» объекта — межсервисный контракт 1 (packages/contracts/interservice.md, раздел 1).

Форма ответа — строго по контракту: analysis-service разбирает его своей моделью.
Поля можно только добавлять (AGENTS.md, правило 9).
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.api.schemas.calendars import WorkHours
from src.api.schemas.common import (
    ConstructionPhase,
    EquipmentGroup,
    ObjectType,
    StageLabel,
    ZoneType,
)
from src.api.schemas.rules import RequiredGroup, Signature
from src.api.schemas.stages import PredecessorRead


class PlanObject(BaseModel):
    id: UUID
    name: str
    object_type: ObjectType
    plan_start: date | None


class PlanCalendar(BaseModel):
    code: str
    timezone: str
    weekend_days: list[int]
    holidays: list[date]
    work_hours: WorkHours


class PlanEquipmentClass(BaseModel):
    code: str
    name_ru: str
    group: EquipmentGroup
    transient: bool


class PlanRule(BaseModel):
    id: UUID
    version: int
    required: list[RequiredGroup]
    allowed: list[str]
    signature: Signature
    min_sessions: int


class PlanStage(BaseModel):
    id: UUID
    code: str
    name: str
    phase: ConstructionPhase
    seq: int
    work_codes: list[str]
    zone_type: ZoneType
    visual_stage: StageLabel | None
    plan_start: date
    plan_end: date = Field(description="Последний рабочий день вехи, включительно")
    norm_duration_days: int
    predecessors: list[PredecessorRead]
    is_critical: bool
    total_float_days: int
    basis: str | None
    rule: PlanRule | None = Field(
        default=None,
        description="null — правила нет или оно выключено: D1, D2, D8, D9 по вехе не проверяются",
    )


class PlanImportResult(BaseModel):
    object_id: UUID
    plan_version: int
    stages: int = Field(description="Сколько вех в новом графике")
    rules: int = Field(description="Сколько вех получили правило из шаблона")
    critical_stages: int = Field(description="Сколько вех на критическом пути")


class Plan(BaseModel):
    object: PlanObject
    plan_version: int
    calendar: PlanCalendar
    equipment_classes: list[PlanEquipmentClass]
    stages: list[PlanStage] = Field(description="Все вехи объекта по seq")
