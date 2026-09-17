"""DTO объекта строительства. Это контракт наружу, а не модель БД."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.api.schemas.common import ObjectLifecycle, ObjectType


class ObjectCreate(BaseModel):
    """Создание объекта.

    Тип можно не указывать: pos-engine распознаёт его из наименования при
    генерации графика. Явное значение — принудительное переопределение.
    """

    name: str = Field(
        min_length=5,
        max_length=1000,
        examples=["Строительство монолитного жилого дома 17 этажей, г. Москва"],
    )
    object_type: ObjectType | None = None
    address: str | None = Field(default=None, max_length=1000)
    plan_start: date | None = Field(default=None, description="Плановая дата начала СМР")
    tep: dict = Field(default_factory=dict, description="Переопределение ТЭП, если требуется")


class ObjectUpdate(BaseModel):
    """Частичное изменение: передаются только меняемые поля."""

    name: str | None = Field(default=None, min_length=5, max_length=1000)
    object_type: ObjectType | None = None
    address: str | None = Field(default=None, max_length=1000)
    plan_start: date | None = None
    tep: dict | None = None
    status: ObjectLifecycle | None = None


class ObjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    object_type: ObjectType
    address: str | None
    tep: dict
    plan_start: date | None
    status: ObjectLifecycle
    current_revision: int = Field(description="Номер текущей ревизии плана; 0 — план не построен")
    created_at: datetime
    updated_at: datetime
