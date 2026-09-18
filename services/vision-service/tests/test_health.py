"""Сервис обязан отвечать на проверки здоровья.

Тест дешёвый, но ловит самое дорогое: приложение, которое не импортируется
или не поднимается. Внешних зависимостей у vision-service нет, поэтому
проверка работает без докера и без базы.
"""

from httpx import ASGITransport, AsyncClient
from src.main import app


async def test_живой_и_готовый():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        alive = await client.get("/health")
        ready = await client.get("/health/ready")

    assert alive.status_code == 200
    assert alive.json()["service"] == "vision-service"
    assert ready.status_code == 200
    assert ready.json()["status"] == "healthy"
