"""Активные вехи и плановая визуальная стадия на местную дату."""

from datetime import date

from src.core.plan_on_date import active_stages, planned_visual_stage

from tests.factories import load_plan, make_plan, make_stage

PLAN = load_plan()


def _names(day: date) -> list[str]:
    return [s.name for s in active_stages(PLAN, day)]


def test_в_демо_дни_активен_котлован():
    assert _names(date(2026, 10, 20)) == ["Разработка котлована"]


def test_даты_вехи_включительно_с_обеих_сторон():
    assert _names(date(2026, 10, 14)) == ["Подготовка территории"]
    assert _names(date(2026, 10, 15)) == ["Разработка котлована"]
    assert _names(date(2026, 11, 20)) == ["Разработка котлована"]
    assert _names(date(2026, 11, 21)) == ["Фундаментная плита"]


def test_до_начала_и_после_конца_графика_вех_нет():
    assert _names(date(2026, 9, 20)) == []
    assert _names(date(2026, 12, 19)) == []


def test_параллельные_вехи_идут_по_порядку_графика():
    plan = make_plan(
        make_stage("Сваи", date(2026, 10, 1), date(2026, 10, 31), seq=2, visual_stage="PILES"),
        make_stage("Котлован", date(2026, 10, 1), date(2026, 10, 20), seq=1, visual_stage="PIT"),
    )

    assert [s.name for s in active_stages(plan, date(2026, 10, 10))] == ["Котлован", "Сваи"]


def test_плановая_стадия_берётся_у_более_поздней_вехи():
    plan = make_plan(
        make_stage("Котлован", date(2026, 10, 1), date(2026, 10, 20), seq=1, visual_stage="PIT"),
        make_stage("Сваи", date(2026, 10, 1), date(2026, 10, 31), seq=2, visual_stage="PILES"),
        make_stage("Сети", date(2026, 10, 1), date(2026, 10, 31), seq=3, visual_stage=None),
    )

    assert planned_visual_stage(plan, date(2026, 10, 10)) == "PILES"


def test_без_стадии_у_активных_вех_плановой_стадии_нет():
    assert planned_visual_stage(PLAN, date(2026, 10, 1)) is None
    assert planned_visual_stage(PLAN, date(2026, 10, 20)) == "PIT"
