"""API прогона: запуск, запись выводов, сверка ленты, ошибки зависимостей (T15a)."""

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from src.clients.plan_client import ObjectNotFound, PlanServiceUnavailable
from src.clients.site_client import SiteServiceUnavailable
from src.dal.models import AnalysisRun, Deviation, DeviationRule, ObjectStatus, StageFact

from tests.factories import load_facts, make_facts

BASE = "/api/v1/analysis/runs"
OBJECT_ID = "0f3a6c1e-8d4b-4c2a-9e71-5b0d2f6a8c31"
DAYS = ["facts_normal_day.json", "facts_day1.json", "facts_day2.json", "facts_day3.json"]


def _all_days():
    return make_facts(*(s for name in DAYS for s in load_facts(name).sessions))


async def _run(client, as_of=None, wait=True):
    body = {"object_id": OBJECT_ID, "triggered_by": "FACTS_UPDATED", "as_of": as_of}
    return await client.post(BASE, json=body, params={"wait": wait})


async def _deviations(session_factory):
    async with session_factory() as session:
        rows = await session.scalars(select(Deviation).order_by(Deviation.first_seen_at))
        return [(r.code, r.status) for r in rows]


async def _count(session_factory, model):
    async with session_factory() as session:
        return await session.scalar(select(func.count()).select_from(model))


async def test_прогон_с_ожиданием_пишет_d2_дня_1(client, upstream, session_factory):
    upstream.site.facts = load_facts("facts_day1.json")

    response = await _run(client)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DONE" and body["error"] is None
    assert (body["plan_version"], body["zones_version"]) == (7, 4)
    assert body["as_of"] == "2026-10-20T12:00:00Z"
    assert body["stats"]["deviations_opened"] == 1 and body["stats"]["deviations_open"] == 1
    assert body["finished_at"] is not None
    assert await _deviations(session_factory) == [("D2", "NEW")]


async def test_результат_читается_по_номеру_прогона(client, upstream):
    upstream.site.facts = load_facts("facts_day1.json")
    run = (await _run(client)).json()

    response = await client.get(f"{BASE}/{run['run_id']}")

    assert response.status_code == 200 and response.json() == run


async def test_повторный_прогон_не_плодит_дублей(client, upstream, session_factory):
    upstream.site.facts = load_facts("facts_day1.json")
    await _run(client)

    second = (await _run(client)).json()

    assert second["stats"]["deviations_opened"] == 0
    assert await _deviations(session_factory) == [("D2", "NEW")]
    assert await _count(session_factory, StageFact) == 3
    assert await _count(session_factory, ObjectStatus) == 1


async def test_лента_по_дням_закрывает_прошедшее_и_открывает_новое(
    client, upstream, session_factory
):
    upstream.site.facts = _all_days()
    await _run(client, as_of="2026-10-20T12:00:00Z")

    body = (await _run(client, as_of="2026-10-22T12:00:00Z")).json()

    assert await _deviations(session_factory) == [
        ("D2", "RESOLVED"),
        ("D3", "RESOLVED"),
        ("D10", "NEW"),
        ("D4", "NEW"),
    ]
    assert body["stats"]["deviations_resolved"] == 1
    assert body["stats"]["deviations_opened"] == 2
    assert body["stats"]["deviations_open"] == 2


async def test_отклонённое_оператором_не_открывается_заново(client, upstream, session_factory):
    upstream.site.facts = load_facts("facts_day1.json")
    await _run(client)
    async with session_factory() as session, session.begin():
        await session.execute(update(Deviation).values(status="REJECTED"))

    await _run(client)

    assert await _deviations(session_factory) == [("D2", "REJECTED")]


async def test_правила_заполняются_из_yaml_и_правки_не_затираются(
    client, upstream, session_factory
):
    upstream.site.facts = load_facts("facts_day1.json")
    await _run(client)
    async with session_factory() as session, session.begin():
        await session.execute(
            update(DeviationRule).where(DeviationRule.code == "D2").values(enabled=False)
        )

    await _run(client)

    assert await _count(session_factory, DeviationRule) == 10
    # D2 выключен оператором — открытая строка закрылась, а не открылась снова.
    assert await _deviations(session_factory) == [("D2", "RESOLVED")]


async def test_факты_запрашиваются_с_местной_полуночи_начала_смр(client, upstream):
    upstream.site.facts = load_facts("facts_day1.json")

    await _run(client, as_of="2026-10-20T12:00:00Z")

    (_, period_from, period_to) = upstream.site.calls[0]
    # 21.09.2026 00:00 по Москве.
    assert period_from == datetime(2026, 9, 20, 21, tzinfo=UTC)
    assert period_to == datetime(2026, 10, 20, 12, tzinfo=UTC)


async def test_без_ожидания_прогон_идёт_в_фоне(client, upstream):
    upstream.site.facts = load_facts("facts_day1.json")

    response = await _run(client, wait=False)

    assert response.status_code == 202
    accepted = response.json()
    assert accepted["coalesced"] is False and accepted["status"] == "RUNNING"
    # ASGITransport дожидается фоновых задач, поэтому прогон уже завершён.
    assert (await client.get(f"{BASE}/{accepted['run_id']}")).json()["status"] == "DONE"


async def test_недоступный_plan_service_это_503_и_failed(client, upstream, session_factory):
    upstream.plan.error = PlanServiceUnavailable("plan-service недоступен")

    response = await _run(client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PLAN_SERVICE_UNAVAILABLE"
    async with session_factory() as session:
        (run,) = await session.scalars(select(AnalysisRun))
    assert (run.status, run.error["code"]) == ("FAILED", "PLAN_SERVICE_UNAVAILABLE")
    # Частичных выводов нет: лента и срезы не тронуты.
    assert await _count(session_factory, ObjectStatus) == 0


async def test_недоступный_site_service_это_503(client, upstream):
    upstream.site.error = SiteServiceUnavailable("site-service недоступен")

    response = await _run(client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SITE_SERVICE_UNAVAILABLE"


async def test_неизвестный_объект_это_404(client, upstream):
    upstream.plan.error = ObjectNotFound(OBJECT_ID)

    response = await _run(client)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OBJECT_NOT_FOUND"


async def test_неизвестный_источник_прогона_отклоняется(client):
    response = await client.post(BASE, json={"object_id": OBJECT_ID, "triggered_by": "CRON"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_несуществующий_прогон_это_404(client):
    response = await client.get(f"{BASE}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RUN_NOT_FOUND"


async def test_факты_чужого_объекта_не_считаются(client, upstream):
    upstream.site.facts = load_facts("facts_day1.json").model_copy(
        update={"object_id": "11111111-1111-4111-8111-111111111111"}
    )

    response = await _run(client)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ANALYSIS_INPUT_INVALID"
