"""DTO вехи графика. Поля совпадают с вехой в контракте «весь план» (interservice.md, раздел 1)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.api.schemas.common import (
    ConstructionPhase,
    DependencyType,
    StageLabel,
    StageSource,
    ZoneType,
)


class PredecessorRead(BaseModel):
    stage_id: UUID
    type: DependencyType
    lag_days: int = Field(description="Лаг в рабочих днях")


class StageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    object_id: UUID
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
    source: StageSource
    basis: str | None
    created_at: datetime
    updated_at: datetime


class StageUpdate(BaseModel):
    """Частичное изменение. Связи и критический путь здесь не правятся (T19)."""

    plan_start: date | None = None
    plan_end: date | None = Field(default=None, description="Включительно")
    zone_type: ZoneType | None = Field(default=None, description="Только тип с ролью WORK")
    visual_stage: StageLabel | None = Field(default=None, description="null — снять стадию")
    norm_duration_days: int | None = Field(
        default=None, gt=0, description="Нормативная длительность в рабочих днях"
    )
