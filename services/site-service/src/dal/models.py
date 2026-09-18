"""Модели sitedb. Описание полей и их смысла — docs/data-model.md, раздел 2.

Перечисления хранятся как text + CHECK, а не как postgres enum: добавление
значения не должно требовать миграции. Ссылки на данные других сервисов
(`object_id`, `equipment_class`) — значения без внешних ключей: чужой базы
здесь нет и быть не может.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

ZONE_TYPES = ("PIT", "BUILDING_FOOTPRINT", "PERIMETER", "ENTRY_GATE", "STORAGE", "DANGER", "ROAD")
IMAGE_STATUSES = ("NEEDS_TIME", "PENDING", "PROCESSING", "ANALYZED", "FAILED")
IMAGE_SOURCES = ("UPLOAD", "API", "FOLDER_IMPORT")
TIME_SOURCES = ("EXIF", "FILENAME", "MANUAL", "UNKNOWN")
SESSION_STATUSES = ("OPEN", "CLOSED", "AGGREGATED")
DETECTION_STATES = ("WORKING", "IDLE", "OUT_OF_ZONE", "UNKNOWN")
STAGE_LABELS = ("PIT", "PILES", "FOUNDATION", "FRAME", "FACADE", "LANDSCAPING")
VISIBILITY_STATUSES = ("OK", "PARTIAL", "BLIND")
VISIBILITY_REASONS = ("NO_IMAGES", "DARK", "OCCLUDED", "BLURRED")


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


class Camera(Base, TimestampMixin):
    """Камера объекта. `code` совпадает с именем папки при пакетной загрузке."""

    __tablename__ = "camera"
    __table_args__ = (UniqueConstraint("object_id", "code", name="uq_camera_object_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID] = mapped_column(index=True)  # внешняя ссылка на plandb.object
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    # Эталонный кадр — основа разметки зон: полигоны нормированы по его размеру.
    reference_frame_key: Mapped[str | None] = mapped_column(Text)
    # Высота подвеса, азимут, ИК-подсветка: исходные данные для рекомендаций по камерам.
    install_meta: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class Zone(Base, TimestampMixin):
    """Рабочая зона, размеченная на кадре камеры.

    Полигон хранится в нормированных координатах 0…1 от размера кадра и потому
    не зависит от разрешения камеры (ADR-0006).
    """

    __tablename__ = "zone"
    __table_args__ = (CheckConstraint(_in("zone_type", ZONE_TYPES), name="ck_zone_type"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID] = mapped_column(index=True)  # внешняя ссылка
    camera_id: Mapped[UUID] = mapped_column(ForeignKey("camera.id", ondelete="CASCADE"))
    zone_type: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(200))
    polygon: Mapped[list] = mapped_column(JSONB)
    # Зоны других камер, накрывающие ту же физическую область: по ним идёт
    # дедупликация техники между камерами при агрегации сессии.
    overlaps_with: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    # Растёт при правке полигона и попадает в analysis_run: прогон воспроизводим.
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class ObservationSession(Base, TimestampMixin):
    """Окно наблюдения по объекту (по умолчанию 30 минут).

    Состав техники считается по сессии, а не по кадру: одна машина, попавшая
    в две камеры, иначе была бы посчитана дважды.
    """

    __tablename__ = "session"
    __table_args__ = (
        UniqueConstraint("object_id", "window_start", name="uq_session_object_window"),
        CheckConstraint(_in("status", SESSION_STATUSES), name="ck_session_status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID] = mapped_column(index=True)  # внешняя ссылка
    window_start: Mapped[datetime]
    window_end: Mapped[datetime]
    # Нерабочее время не порождает отклонений: пустая площадка ночью — норма.
    is_working_time: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    image_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    camera_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'OPEN'"), index=True)


class Image(Base, TimestampMixin):
    """Снимок камеры — первичное доказательство в системе."""

    __tablename__ = "image"
    __table_args__ = (
        # Повторная загрузка того же файла не создаёт второй снимок и не удваивает
        # технику в сессии; клиенту возвращается ID существующего.
        UniqueConstraint("object_id", "checksum", name="uq_image_object_checksum"),
        CheckConstraint(_in("status", IMAGE_STATUSES), name="ck_image_status"),
        CheckConstraint(_in("source", IMAGE_SOURCES), name="ck_image_source"),
        CheckConstraint(_in("captured_at_source", TIME_SOURCES), name="ck_image_time_source"),
        Index("ix_image_object_captured_at", "object_id", "captured_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID]  # внешняя ссылка
    camera_id: Mapped[UUID] = mapped_column(ForeignKey("camera.id", ondelete="CASCADE"))
    # Время съёмки может быть неизвестно: снимок остаётся в статусе NEEDS_TIME,
    # но не теряется — источник времени хранится рядом со значением.
    captured_at: Mapped[datetime | None]
    captured_at_source: Mapped[str] = mapped_column(String(16), server_default=text("'UNKNOWN'"))
    received_at: Mapped[datetime] = mapped_column(server_default=func.now())
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("session.id", ondelete="SET NULL"), index=True
    )
    storage_key: Mapped[str] = mapped_column(Text)
    thumb_key: Mapped[str | None] = mapped_column(Text)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(16), server_default=text("'UPLOAD'"))
    exif: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    # Яркость, размытие, перекрытие от vision-service: непригодный кадр
    # не превращается в вывод «техники нет», а помечает зону как невидимую.
    quality: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'PENDING'"), index=True)
    error: Mapped[str | None] = mapped_column(Text)


class Detection(Base):
    """Единица техники, найденная на снимке."""

    __tablename__ = "detection"
    __table_args__ = (
        CheckConstraint(_in("state", DETECTION_STATES), name="ck_detection_state"),
        Index("ix_detection_session_class", "session_id", "equipment_class"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    image_id: Mapped[UUID] = mapped_column(ForeignKey("image.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("session.id", ondelete="SET NULL"))
    # Код класса совпадает с plandb.equipment_class.code — связь по значению.
    equipment_class: Mapped[str] = mapped_column(String(64))
    bbox: Mapped[list] = mapped_column(JSONB)
    conf: Mapped[float] = mapped_column(Float)
    # Нижняя середина рамки: точка контакта с землёй, по ней идёт привязка к зоне.
    anchor: Mapped[list] = mapped_column(JSONB)
    zone_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("zone.id", ondelete="SET NULL"), index=True
    )
    state: Mapped[str] = mapped_column(String(16), server_default=text("'UNKNOWN'"))
    # Человекочитаемое обоснование статуса: попадает в объяснение отклонения.
    state_reason: Mapped[str | None] = mapped_column(Text)
    # Версия модели у каждой детекции: вывод воспроизводим после смены весов.
    model_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class StageObservation(Base):
    """Стадия объекта, определённая по обзорному снимку."""

    __tablename__ = "stage_observation"
    __table_args__ = (
        CheckConstraint(_in("stage_label", STAGE_LABELS), name="ck_stage_observation_label"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    image_id: Mapped[UUID] = mapped_column(ForeignKey("image.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("session.id", ondelete="SET NULL"))
    stage_label: Mapped[str] = mapped_column(String(32))
    conf: Mapped[float] = mapped_column(Float)
    floors_estimate: Mapped[int | None] = mapped_column(Integer)
    # Все вероятности, а не только победившая: без них вывод нечем объяснить.
    scores: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ZoneVisibility(Base):
    """Видимость зоны в сессии — основание для D10 «зона вне контроля ИИ»."""

    __tablename__ = "zone_visibility"
    __table_args__ = (
        CheckConstraint(_in("status", VISIBILITY_STATUSES), name="ck_visibility_status"),
        CheckConstraint(
            f"reason IS NULL OR {_in('reason', VISIBILITY_REASONS)}", name="ck_visibility_reason"
        ),
    )

    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), primary_key=True
    )
    zone_id: Mapped[UUID] = mapped_column(
        ForeignKey("zone.id", ondelete="CASCADE"), primary_key=True
    )
    coverage: Mapped[float] = mapped_column(Float, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'OK'"))
    reason: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SessionFact(Base):
    """Агрегат сессии: зона × класс техники × количество.

    Материализуется при закрытии сессии и пересчитывается при правке зон —
    это то, что читает analysis-service, и единственный контракт факта.
    """

    __tablename__ = "session_fact"

    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), primary_key=True
    )
    zone_id: Mapped[UUID] = mapped_column(
        ForeignKey("zone.id", ondelete="CASCADE"), primary_key=True
    )
    equipment_class: Mapped[str] = mapped_column(String(64), primary_key=True)
    # Максимум по камере, а не сумма: зоны камер пересекаются, иначе двойной счёт.
    count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    working_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    idle_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    # Снимки и детекции, на которые опирается число: без них факт неотличим от мнения.
    evidence: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
