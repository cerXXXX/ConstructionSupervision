"""API выводов по объекту: статус, прогресс вех, загрузка техники (T16a)."""

import pytest

from tests.factories import load_facts, make_facts

OBJECT_ID = "0f3a6c1e-8d4b-4c2a-9e71-5b0d2f6a8c31"
BASE = f"/api/v1/analysis/objects/{OBJECT_ID}"
PIT_STAGE_ID = "7c1e9f03-b5a2-4d78-8e46-c3f0a1b7d926"
DAYS = ["facts_normal_day.json", "facts_day1.json", "facts_day2.json", "facts_day3.json"]


@pytest.fixture
async def analyzed(client, upstream):
    """Объект после прогона по четырём демо-дням (19–22.10)."""
    upstream.site.facts = make_facts(*(s for n in DAYS for s in load_facts(n).sessions))
    response = await client.post(
        "/api/v1/analysis/runs", json={"object_id": OBJECT_ID}, params={"wait": True}
    )
    assert response.status_code == 200


async def test_статус_объекта_для_дашборда(client, analyzed):
    response = await client.get(f"{BASE}/status")

    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["delay_days"], body["confidence"]) == ("DELAY", 14, "MEDIUM")
    assert body["as_of"] == "2026-10-22T12:00:00Z"
    # Все серьёзности — с нулями: дашборду не нужно гадать, какие ключи бывают.
    assert body["deviations"] == {"INFO": 1, "LOW": 1, "MEDIUM": 0, "HIGH": 0}
    assert body["blind_areas"] == 1
    assert body["stages"]["total"] == 3
    assert [s["name"] for s in body["stages_at_risk"]] == [
        "Разработка котлована",
        "Фундаментная плита",
    ]
    assert body["facts"]["observation_days"] == 4


async def test_без_прогона_статуса_нет(client):
    response = await client.get(f"{BASE}/status")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OBJECT_NOT_ANALYZED"


async def test_прогресс_вех_с_активностью_по_дням(client, analyzed):
    body = (await client.get(f"{BASE}/progress")).json()

    assert body["as_of"] == "2026-10-22T12:00:00Z"
    assert len(body["stages"]) == 3
    pit = next(s for s in body["stages"] if s["stage_id"] == PIT_STAGE_ID)
    assert pit["actual_start"] == "2026-10-19" and pit["status"] == "LATE"
    assert pit["forecast_end"] == "2026-12-07" and pit["delay_days"] == 14
    # День 1 (20.10) без самосвалов: комплект неполный, активность ноль.
    assert [(a["date"], a["activity_index"]) for a in pit["activity"]] == [
        ("2026-10-19", 1.0),
        ("2026-10-20", 0.0),
        ("2026-10-21", 1.0),
        ("2026-10-22", 1.0),
    ]


async def test_загрузка_техники_по_дням(client, analyzed):
    body = (await client.get(f"{BASE}/equipment")).json()

    excavator = [i for i in body["items"] if i["equipment_class"] == "excavator"]
    assert [i["date"] for i in excavator] == [
        "2026-10-19",
        "2026-10-20",
        "2026-10-21",
        "2026-10-22",
    ]


async def test_загрузка_техники_за_полуинтервал_дат(client, analyzed):
    body = (
        await client.get(f"{BASE}/equipment", params={"from": "2026-10-22", "to": "2026-10-23"})
    ).json()

    assert {i["date"] for i in body["items"]} == {"2026-10-22"}
    # День 3: экскаватор в котловане и второй — у въезда.
    excavator = next(i for i in body["items"] if i["equipment_class"] == "excavator")
    assert excavator["max_count"] == 2


async def test_без_прогона_загрузки_нет(client):
    response = await client.get(f"{BASE}/equipment")

    assert response.status_code == 404
