"""Клиент нормативного расчётчика ПОС.

Единственное место, откуда plan-service ходит в pos-engine. Методы названы
по смыслу, а не по URL; решения на основе ответа принимает вызывающий слой.
"""

from typing import Any

from lct_common import ServiceClient, UpstreamError


class PosEngineUnavailable(UpstreamError):
    code = "POS_ENGINE_UNAVAILABLE"


class PosClient:
    def __init__(self, base_url: str, api_key: str, timeout_s: float) -> None:
        # Ретраев нет: генерация графика небыстрая и неидемпотентная по стоимости,
        # повтор лишь увеличит время ожидания пользователя.
        self._client = ServiceClient(
            base_url,
            service="pos-engine",
            api_key=api_key,
            timeout_s=timeout_s,
            retries=0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def ping(self) -> None:
        await self._client.ping()

    async def generate_plan(
        self,
        object_name: str,
        *,
        start_date: str | None = None,
        tep_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Наименование объекта → нормативный график с матрицей техники.

        Контракт — services/pos-engine/README.md, раздел 4. Ответ сохраняется
        plan-service как редактируемая истина: дальше оператор правит даты
        и правила в интерфейсе, и pos-engine об этом уже ничего не знает.
        """
        payload: dict[str, Any] = {"object_name": object_name}
        if start_date:
            payload["start_date"] = start_date
        if tep_overrides:
            payload["tep_overrides"] = tep_overrides

        try:
            return await self._client.post("/api/v1/pos/generate", json=payload)
        except UpstreamError as exc:
            raise PosEngineUnavailable(
                "Нормативный расчётчик недоступен, график можно импортировать из файла",
                **exc.details,
            ) from exc
