"""API PDF-отчётов: формирование, список, ссылка, деградация без site (T34c)."""

from datetime import UTC, datetime

from lct_common import UpstreamError

from tests.conftest import DEMO_OBJECT_ID

BASE = "/api/v1/analysis/reports"


async def test_отчёт_по_умолчанию_за_неделю_до_дня_анализа(client, analyzed, upstream):
    response = await client.post(BASE, json={"object_id": DEMO_OBJECT_ID})

    assert response.status_code == 201, response.text
    body = response.json()
    # as_of 22.10 12:00 UTC — 22.10 по Москве; неделя — с 16.10 по 22.10 включительно.
    assert (body["period_from"], body["period_to"]) == ("2026-10-16", "2026-10-22")
    assert body["key"] == f"{DEMO_OBJECT_ID}/{body['generated_on']}-2026-10-16_2026-10-22.pdf"
    assert body["as_of"] == "2026-10-22T12:00:00Z"
    assert body["summary_generated_by"] == "TEMPLATE"
    assert body["evidence_images"] >= 1 and body["evidence_missing"] == 0
    assert body["url"].startswith("http://localhost:9000/reports/")
    # Факты — за местные сутки периода, в UTC.
    _, since, until = upstream.site.calls[-1]
    assert (since, until) == (
        datetime(2026, 10, 15, 21, tzinfo=UTC),
        datetime(2026, 10, 22, 21, tzinfo=UTC),
    )
    content, _ = upstream.storage.files[body["key"]]
    assert content.startswith(b"%PDF") and body["size_bytes"] == len(content)


async def test_список_и_ссылка_на_отчёт(client, analyzed):
    created = (
        await client.post(
            BASE,
            json={
                "object_id": DEMO_OBJECT_ID,
                "period_from": "2026-10-20",
                "period_to": "2026-10-20",
            },
        )
    ).json()

    page = (await client.get(BASE, params={"object_id": DEMO_OBJECT_ID})).json()
    link = await client.get(f"{BASE}/{created['key']}")

    assert page["total"] == 1 and page["items"][0]["key"] == created["key"]
    assert link.status_code == 200 and link.json()["url"] == created["url"]
    missing = await client.get(f"{BASE}/{DEMO_OBJECT_ID}/2026-01-01-2026-01-01_2026-01-02.pdf")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "REPORT_NOT_FOUND"


async def test_без_site_отчёт_выходит_и_говорит_о_пробелах(client, analyzed, upstream):
    upstream.site.error = UpstreamError("site-service недоступен")

    response = await client.post(BASE, json={"object_id": DEMO_OBJECT_ID})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["evidence_images"] == 0 and body["evidence_missing"] >= 1


async def test_период_без_наблюдений(client, analyzed):
    response = await client.post(
        BASE,
        json={"object_id": DEMO_OBJECT_ID, "period_from": "2026-10-01", "period_to": "2026-10-05"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NO_DATA_FOR_PERIOD"


async def test_перевёрнутый_период_и_объект_без_анализа(client, analyzed):
    reversed_period = await client.post(
        BASE,
        json={"object_id": DEMO_OBJECT_ID, "period_from": "2026-10-22", "period_to": "2026-10-19"},
    )
    not_analyzed = await client.post(
        BASE, json={"object_id": "00000000-0000-4000-8000-000000000000"}
    )

    assert reversed_period.status_code == 400
    assert not_analyzed.status_code == 404
    assert not_analyzed.json()["error"]["code"] == "OBJECT_NOT_ANALYZED"
