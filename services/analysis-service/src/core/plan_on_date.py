"""План на дату: какие вехи активны и как объект должен выглядеть на фото.

Активная веха — «по плану»: местная дата сессии лежит в [plan_start, plan_end], обе
даты включительно (docs/methodology.md, раздел 2). Отдельного запроса «план на дату»
к plan-service нет: analysis решает это сам по всему плану.
"""

from datetime import date

from src.core.inputs import Plan, Stage


def active_stages(plan: Plan, day: date) -> tuple[Stage, ...]:
    """Вехи, активные на местную дату, по порядку графика."""
    active = [s for s in plan.stages if s.plan_start <= day <= s.plan_end]
    return tuple(sorted(active, key=lambda s: s.seq))


def visual_milestone(plan: Plan, day: date) -> Stage | None:
    """Веха, задающая плановую визуальную стадию на дату (docs/methodology.md, раздел 8).

    Это активная веха с заданным `visual_stage` и наибольшим `seq`: если параллельно
    идут котлован и сваи, объект на фото должен выглядеть по более поздней.
    """
    with_stage = [s for s in active_stages(plan, day) if s.visual_stage is not None]
    return with_stage[-1] if with_stage else None


def planned_visual_stage(plan: Plan, day: date) -> str | None:
    """Плановая визуальная стадия на дату; None — на дату нет вехи со стадией, D7 не с чем."""
    stage = visual_milestone(plan, day)
    return stage.visual_stage if stage else None
