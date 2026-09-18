"""Начальная схема plandb: объекты, справочники, вехи, правила, ревизии

Соответствует docs/data-model.md, раздел 1. Перечисления — text + CHECK:
добавление значения не должно требовать миграции.

Revision ID: 0001
Revises:
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)
NEW_UUID = sa.text("gen_random_uuid()")
NOW = sa.text("now()")


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "work_calendar",
        sa.Column("id", UUID, primary_key=True, server_default=NEW_UUID),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("weekend_days", JSONB, server_default=sa.text("'[6, 7]'::jsonb"), nullable=False),
        sa.Column("holidays", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column(
            "work_hours",
            JSONB,
            server_default=sa.text("""'{"start": "07:00", "end": "23:00"}'::jsonb"""),
            nullable=False,
        ),
        *_timestamps(),
    )

    op.create_table(
        "object",
        sa.Column("id", UUID, primary_key=True, server_default=NEW_UUID),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("object_type", sa.String(32), nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("tep", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("plan_start", sa.Date),
        sa.Column("calendar_id", UUID, sa.ForeignKey("work_calendar.id")),
        sa.Column("status", sa.String(16), server_default=sa.text("'DRAFT'"), nullable=False),
        sa.Column("current_revision", sa.Integer, server_default=sa.text("0"), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "object_type IN ('RESIDENTIAL_MONOLITH', 'RESIDENTIAL_PANEL', "
            "'PUBLIC_BUILDING', 'ROAD')",
            name="ck_object_type",
        ),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')", name="ck_object_status"),
    )
    op.create_index("ix_object_status", "object", ["status"])
    op.create_index("ix_object_object_type", "object", ["object_type"])

    op.create_table(
        "work_type",
        sa.Column("code", sa.String(32), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("parent_code", sa.String(32)),
        sa.Column("applicable", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("source", sa.Text),
        sa.CheckConstraint("level BETWEEN 1 AND 4", name="ck_work_type_level"),
    )
    op.create_index("ix_work_type_parent_code", "work_type", ["parent_code"])

    op.create_table(
        "equipment_class",
        sa.Column("code", sa.String(64), primary_key=True),
        sa.Column("name_ru", sa.String(200), nullable=False),
        sa.Column("group_code", sa.String(32), nullable=False),
        sa.Column("aliases", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("icon", sa.String(64)),
        *_timestamps(),
        sa.CheckConstraint(
            "group_code IN ('EARTHWORKS', 'LIFTING', 'CONCRETE', 'TRANSPORT', 'ROAD', 'OTHER')",
            name="ck_equipment_group",
        ),
    )

    op.create_table(
        "stage",
        sa.Column("id", UUID, primary_key=True, server_default=NEW_UUID),
        sa.Column(
            "object_id", UUID, sa.ForeignKey("object.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("work_codes", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("phase", sa.String(32), nullable=False),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("zone_type", sa.String(32), nullable=False),
        sa.Column("plan_start", sa.Date, nullable=False),
        sa.Column("plan_end", sa.Date, nullable=False),
        sa.Column("norm_duration_days", sa.Integer, nullable=False),
        sa.Column("predecessors", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("is_critical", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("total_float_days", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("free_float_days", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("shifts_per_day", sa.Integer, server_default=sa.text("2"), nullable=False),
        sa.Column("source", sa.String(16), server_default=sa.text("'POS_ENGINE'"), nullable=False),
        sa.Column("regulatory_basis", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "phase IN ('PREPARATORY', 'SUBSTRUCTURE', 'SUPERSTRUCTURE', "
            "'ENVELOPE_ROOF', 'NETWORKS', 'LANDSCAPING')",
            name="ck_stage_phase",
        ),
        sa.CheckConstraint(
            "zone_type IN ('PIT', 'BUILDING_FOOTPRINT', 'PERIMETER', 'ENTRY_GATE', "
            "'STORAGE', 'DANGER', 'ROAD')",
            name="ck_stage_zone_type",
        ),
        sa.CheckConstraint("source IN ('POS_ENGINE', 'IMPORT', 'MANUAL')", name="ck_stage_source"),
        sa.CheckConstraint("plan_end >= plan_start", name="ck_stage_dates"),
    )
    op.create_index("ix_stage_object_plan_start", "stage", ["object_id", "plan_start"])
    op.create_index("ix_stage_object_seq", "stage", ["object_id", "seq"])

    op.create_table(
        "stage_rule",
        sa.Column("id", UUID, primary_key=True, server_default=NEW_UUID),
        sa.Column("stage_id", UUID, sa.ForeignKey("stage.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_type", sa.String(32), nullable=False),
        sa.Column("required", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("allowed", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("signature", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("min_sessions", sa.Integer, server_default=sa.text("2"), nullable=False),
        sa.Column("version", sa.Integer, server_default=sa.text("1"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "zone_type IN ('PIT', 'BUILDING_FOOTPRINT', 'PERIMETER', 'ENTRY_GATE', "
            "'STORAGE', 'DANGER', 'ROAD')",
            name="ck_rule_zone_type",
        ),
        sa.CheckConstraint("min_sessions >= 1", name="ck_rule_min_sessions"),
    )
    op.create_index("ix_stage_rule_stage_id", "stage_rule", ["stage_id"])

    op.create_table(
        "plan_revision",
        sa.Column("id", UUID, primary_key=True, server_default=NEW_UUID),
        sa.Column(
            "object_id", UUID, sa.ForeignKey("object.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("number", sa.Integer, nullable=False),
        sa.Column("author", sa.String(200)),
        sa.Column("reason", sa.Text),
        sa.Column("snapshot", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("object_id", "number", name="uq_revision_number"),
    )
    op.create_index("ix_plan_revision_object_id", "plan_revision", ["object_id"])

    # Календарь по умолчанию: шестидневка, как на большинстве московских площадок.
    op.execute(
        """
        INSERT INTO work_calendar (code, name, weekend_days, work_hours)
        VALUES (
            'moscow-6day',
            'Москва, шестидневная рабочая неделя',
            '[7]'::jsonb,
            '{"start": "07:00", "end": "23:00"}'::jsonb
        )
        """
    )


def downgrade() -> None:
    op.drop_table("plan_revision")
    op.drop_table("stage_rule")
    op.drop_table("stage")
    op.drop_table("equipment_class")
    op.drop_table("work_type")
    op.drop_table("object")
    op.drop_table("work_calendar")
