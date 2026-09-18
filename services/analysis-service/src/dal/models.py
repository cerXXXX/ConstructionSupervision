"""Модели analysisdb. Описание полей и их смысла — docs/data-model.md, раздел 3.

Здесь нет первичных данных: план и факт сервис читает по API, а хранит только
выводы. Любая строка этих таблиц пересчитывается прогоном с нуля, поэтому
внешних ключей на чужие сущности нет — только UUID-значения.
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

RUN_TRIGGERS = ("SESSION_CLOSED", "PLAN_CHANGED", "RULES_CHANGED", "MANUAL")
RUN_STATUSES = ("RUNNING", "DONE", "FAILED")
SEVERITIES = ("INFO", "LOW", "MEDIUM", "HIGH")
DEVIATION_STATUSES = ("NEW", "CONFIRMED", "REJECTED", "RESOLVED")
STAGE_FACT_STATUSES = ("NOT_STARTED", "IN_PROGRESS", "DONE", "LATE", "AHEAD")
CONFIDENCE = ("LOW", "MEDIUM", "HIGH")
OBJECT_STATUSES = ("ON_TRACK", "DELAY", "AHEAD", "UNKNOWN")
VERDICTS = ("CONFIRMED", "FALSE_POSITIVE")


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


class AnalysisRun(Base, TimestampMixin):
    """Один прогон сверки.

    Версии входных данных фиксируются в строке: по ним прогон воспроизводится
    и объясняется задним числом, даже если план с тех пор правили.
    """

    __tablename__ = "analysis_run"
    __table_args__ = (
        CheckConstraint(_in("triggered_by", RUN_TRIGGERS), name="ck_run_trigger"),
        CheckConstraint(_in("status", RUN_STATUSES), name="ck_run_status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID] = mapped_column(index=True)  # внешняя ссылка на plandb.object
    triggered_by: Mapped[str] = mapped_column(String(32), server_default=text("'MANUAL'"))
    period_from: Mapped[date]
    period_to: Mapped[date]
    plan_revision: Mapped[int | None] = mapped_column(Integer)
    rules_version: Mapped[int | None] = mapped_column(Integer)
    zones_version: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), server_default=text("'RUNNING'"))
    # Сколько сессий обработано, сколько отклонений открыто и закрыто.
    stats: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))


class Deviation(Base, TimestampMixin):
    """Отклонение: то, что видит пользователь, и то, за что нас оценивают.

    Строка бессмысленна без `facts` и `evidence`: число без объяснения мы
    не показываем (AGENTS.md, правило 4).
    """

    __tablename__ = "deviation"
    __table_args__ = (
        CheckConstraint(_in("severity", SEVERITIES), name="ck_deviation_severity"),
        CheckConstraint(_in("status", DEVIATION_STATUSES), name="ck_deviation_status"),
        # Открытое отклонение единственно в разрезе «объект + веха + зона + код»:
        # повторный прогон обновляет строку, а не плодит дубли. NULLS NOT DISTINCT
        # обязателен — у отклонения уровня объекта нет ни вехи, ни зоны, и без
        # него два NULL считались бы разными значениями.
        Index(
            "uq_deviation_open",
            "object_id",
            "stage_id",
            "zone_id",
            "code",
            unique=True,
            postgresql_where=text("status IN ('NEW', 'CONFIRMED')"),
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_deviation_object_code", "object_id", "code"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    object_id: Mapped[UUID]  # внешняя ссылка
    stage_id: Mapped[UUID | None]  # внешняя ссылка на plandb.stage
    zone_id: Mapped[UUID | None]  # внешняя ссылка на sitedb.zone
    session_id: Mapped[UUID | None]  # внешняя ссылка на sitedb.session
    code: Mapped[str] = mapped_column(String(8))
    severity: Mapped[str] = mapped_column(String(8), index=True)
    title: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text)
    # Все числа, на которых построен вывод: основа объяснимости и /explain.
    facts: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    rule_ref: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    evidence: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'NEW'"), index=True)
    first_seen_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Сколько сессий подряд условие выполнялось: одиночный кадр не повод для тревоги.
    occurrences: Mapped[int] = mapped_column(Integer, server_default=text("1"))


class DeviationRule(Base, TimestampMixin):
    """Настройка правила D1–D10: пороги и текст живут в данных, а не в коде.

    Новый тип отклонения с существующим предикатом добавляется строкой в эту
    таблицу — без правки кода и без развёртывания (AGENTS.md, раздел 12).
    """

    __tablename__ = "deviation_rule"
    __table_args__ = (CheckConstraint(_in("severity", SEVERITIES), name="ck_rule_severity"),)

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    # Имя предиката из реестра core/predicates.py.
    predicate: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    severity: Mapped[str] = mapped_column(String(8))
    params: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    message_template: Mapped[str] = mapped_column(Text)


class StageFact(Base, TimestampMixin):
    """Вывод по одной вехе: прогресс, SPI, прогноз, задержка.

    `confidence` не украшение: при двух сессиях и слепой зоне уверенный прогноз
    вводит в заблуждение, и об этом обязан знать интерфейс.
    """

    __tablename__ = "stage_fact"
    __table_args__ = (
        CheckConstraint(_in("status", STAGE_FACT_STATUSES), name="ck_stage_fact_status"),
        CheckConstraint(_in("confidence", CONFIDENCE), name="ck_stage_fact_confidence"),
    )

    object_id: Mapped[UUID] = mapped_column(primary_key=True)  # внешняя ссылка
    stage_id: Mapped[UUID] = mapped_column(primary_key=True)  # внешняя ссылка
    actual_start: Mapped[date | None] = mapped_column(Date)
    last_activity_at: Mapped[datetime | None]
    # Сумма индексов активности: календарные дни без техники темпа не дают.
    effective_days: Mapped[float] = mapped_column(Float, server_default=text("0"))
    progress: Mapped[float] = mapped_column(Float, server_default=text("0"))
    planned_progress: Mapped[float] = mapped_column(Float, server_default=text("0"))
    spi: Mapped[float | None] = mapped_column(Float)
    forecast_end: Mapped[date | None] = mapped_column(Date)
    delay_days: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), server_default=text("'NOT_STARTED'"))
    confidence: Mapped[str] = mapped_column(String(8), server_default=text("'LOW'"))


class DailyActivity(Base):
    """Активность по вехе за день — вход прогноза и доказательство темпа."""

    __tablename__ = "daily_activity"

    stage_id: Mapped[UUID] = mapped_column(primary_key=True)  # внешняя ссылка
    # Колонка названа `date` (docs/data-model.md, п. 3.5), атрибут — `day`:
    # иначе имя перекрыло бы тип `datetime.date` в теле класса.
    day: Mapped[date] = mapped_column("date", Date, primary_key=True)
    sessions_total: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    sessions_working: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    activity_index: Mapped[float] = mapped_column(Float, server_default=text("0"))
    # Слепые сессии не штрафуют индекс, а снижают уверенность: «не видно»
    # и «не работают» — разные утверждения.
    blind_sessions: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ObjectStatus(Base):
    """Сводный статус объекта для дашборда — последний посчитанный срез."""

    __tablename__ = "object_status"
    __table_args__ = (CheckConstraint(_in("status", OBJECT_STATUSES), name="ck_object_status"),)

    object_id: Mapped[UUID] = mapped_column(primary_key=True)  # внешняя ссылка
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    status: Mapped[str] = mapped_column(String(16), server_default=text("'UNKNOWN'"))
    delay_days: Mapped[int | None] = mapped_column(Integer)
    spi: Mapped[float | None] = mapped_column(Float)
    counters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    milestones_at_risk: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))


class DeviationFeedback(Base):
    """Вердикт оператора по отклонению.

    Помимо UX это выборка для калибровки порогов: доля ложных срабатываний
    измеряется, а не оценивается на глаз.
    """

    __tablename__ = "deviation_feedback"
    __table_args__ = (CheckConstraint(_in("verdict", VERDICTS), name="ck_feedback_verdict"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    deviation_id: Mapped[UUID] = mapped_column(
        ForeignKey("deviation.id", ondelete="CASCADE"), index=True
    )
    verdict: Mapped[str] = mapped_column(String(16))
    comment: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
