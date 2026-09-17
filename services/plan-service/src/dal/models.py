"""Модели plandb. Описание полей и их смысла — docs/data-model.md, раздел 1.

Перечисления хранятся как text + CHECK, а не как postgres enum: добавление
значения не должно требовать миграции. Ссылки на данные других сервисов —
только UUID без внешних ключей.
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

OBJECT_TYPES = ("RESIDENTIAL_MONOLITH", "RESIDENTIAL_PANEL", "PUBLIC_BUILDING", "ROAD")
OBJECT_LIFECYCLE = ("DRAFT", "ACTIVE", "ARCHIVED")
PHASES = (
    "PREPARATORY",
    "SUBSTRUCTURE",
    "SUPERSTRUCTURE",
    "ENVELOPE_ROOF",
    "NETWORKS",
    "LANDSCAPING",
)
ZONE_TYPES = ("PIT", "BUILDING_FOOTPRINT", "PERIMETER", "ENTRY_GATE", "STORAGE", "DANGER", "ROAD")
STAGE_SOURCES = ("POS_ENGINE", "IMPORT", "MANUAL")
EQUIPMENT_GROUPS = ("EARTHWORKS", "LIFTING", "CONCRETE", "TRANSPORT", "ROAD", "OTHER")


def _in(column: str, values: tuple[str, ...]) -> str:
    """CHECK-ограничение «значение из списка»."""
    allowed = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({allowed})"


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WorkCalendar(Base, TimestampMixin):
    """Рабочий календарь: выходные, праздники, рабочее время.

    Рабочее время влияет на D1 и D4: отклонения не строятся по сессиям,
    попавшим в нерабочие часы.
    """

    __tablename__ = "work_calendar"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    weekend_days: Mapped[list] = mapped_column(JSONB, server_default=text("'[6, 7]'::jsonb"))
    holidays: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    work_hours: Mapped[dict] = mapped_column(
        JSONB, server_default=text("""'{"start": "07:00", "end": "23:00"}'::jsonb""")
    )


class ConstructionObject(Base, TimestampMixin):
    """Объект капитального строительства — корневая сущность системы."""

    __tablename__ = "object"
    __table_args__ = (
        CheckConstraint(_in("object_type", OBJECT_TYPES), name="ck_object_type"),
        CheckConstraint(_in("status", OBJECT_LIFECYCLE), name="ck_object_status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(Text)
    object_type: Mapped[str] = mapped_column(String(32), index=True)
    address: Mapped[str | None] = mapped_column(Text)
    # Технико-экономические показатели в том виде, в каком их вернул pos-engine.
    tep: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    plan_start: Mapped[date | None] = mapped_column(Date)
    calendar_id: Mapped[UUID | None] = mapped_column(ForeignKey("work_calendar.id"))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'DRAFT'"), index=True)
    current_revision: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class WorkType(Base):
    """Справочник строительных работ, 4 уровня.

    Загружается парсером XLSX заказчика. В source пишется файл, лист и номер
    строки: любое значение должно быть проверяемо по первоисточнику.
    """

    __tablename__ = "work_type"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer)
    parent_code: Mapped[str | None] = mapped_column(String(32), index=True)
    # Флаги обязательности по типам объектов: {"RESIDENTIAL": true, "ROAD": false}
    applicable: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    source: Mapped[str | None] = mapped_column(Text)


class EquipmentClass(Base, TimestampMixin):
    """Класс техники. Добавление нового класса — строка здесь, без правки кода."""

    __tablename__ = "equipment_class"
    __table_args__ = (
        CheckConstraint(_in("group_code", EQUIPMENT_GROUPS), name="ck_equipment_group"),
    )

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_ru: Mapped[str] = mapped_column(String(200))
    group_code: Mapped[str] = mapped_column(String(32))
    # Метки внешних датасетов и текстовые промпты для open-vocabulary детектора.
    aliases: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    icon: Mapped[str | None] = mapped_column(String(64))


class Stage(Base, TimestampMixin):
    """Веха календарного графика: укрупнённый этап работ с плановыми датами."""

    __tablename__ = "stage"
    __table_args__ = (
        CheckConstraint(_in("phase", PHASES), name="ck_stage_phase"),
        CheckConstraint(_in("zone_type", ZONE_TYPES), name="ck_stage_zone_type"),
        CheckConstraint(_in("source", STAGE_SOURCES), name="ck_stage_source"),
        CheckConstraint("plan_end >= plan_start", name="ck_stage_dates"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID] = mapped_column(ForeignKey("object.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    work_codes: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    name: Mapped[str] = mapped_column(Text)
    phase: Mapped[str] = mapped_column(String(32))
    seq: Mapped[int] = mapped_column(Integer)
    zone_type: Mapped[str] = mapped_column(String(32))
    plan_start: Mapped[date] = mapped_column(Date, index=True)
    plan_end: Mapped[date] = mapped_column(Date)
    norm_duration_days: Mapped[int] = mapped_column(Integer)
    # [{"stage_id": "...", "type": "FS", "lag_days": 0}]
    predecessors: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    is_critical: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    total_float_days: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    free_float_days: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    shifts_per_day: Mapped[int] = mapped_column(Integer, server_default=text("2"))
    source: Mapped[str] = mapped_column(String(16), server_default=text("'POS_ENGINE'"))
    regulatory_basis: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))


class StageRule(Base, TimestampMixin):
    """Правило «веха → техника»: обязательная, допустимая и сигнатурная.

    Создаётся из матрицы техники pos-engine, дальше редактируется оператором
    в интерфейсе. Версия растёт при каждой правке и попадает в прогон анализа,
    чтобы вывод оставался воспроизводимым.
    """

    __tablename__ = "stage_rule"
    __table_args__ = (CheckConstraint(_in("zone_type", ZONE_TYPES), name="ck_rule_zone_type"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    stage_id: Mapped[UUID] = mapped_column(ForeignKey("stage.id", ondelete="CASCADE"), index=True)
    zone_type: Mapped[str] = mapped_column(String(32))
    # {"excavator": 1, "dump_truck": 2}
    required: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    allowed: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    signature: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    min_sessions: Mapped[int] = mapped_column(Integer, server_default=text("2"))
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class PlanRevision(Base):
    """Слепок графика и правил на момент правки.

    Бюджетный городской объект требует аудита: кто, когда и почему подвинул срок.
    """

    __tablename__ = "plan_revision"
    __table_args__ = (UniqueConstraint("object_id", "number", name="uq_revision_number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID] = mapped_column(ForeignKey("object.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    author: Mapped[str | None] = mapped_column(String(200))
    reason: Mapped[str | None] = mapped_column(Text)
    snapshot: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
