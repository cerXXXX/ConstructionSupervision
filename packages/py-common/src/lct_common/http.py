"""HTTP-клиент к другим сервисам: единственное место, где сервис ходит наружу.

Клиент переводит чужой конверт ошибки в наши исключения, пробрасывает
идентификатор запроса и ключ, и повторяет вызов ТОЛЬКО для идемпотентных
методов — повтор POST без ключа идемпотентности может создать дубль.
"""

import asyncio
from typing import Any

import httpx

from lct_common.auth import API_KEY_HEADER
from lct_common.errors import DomainError, UpstreamError
from lct_common.logging import get_logger
from lct_common.request_id import REQUEST_ID_HEADER, current_request_id

log = get_logger(__name__)

IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "PUT", "DELETE", "OPTIONS"})


class ServiceClient:
    """Клиент одного вышестоящего сервиса.

    На сервис — один класс-наследник в `src/clients/`, с методами по смыслу
    (`get_active_stages`), а не по URL. Решения на основе ответа принимает
    вызывающий слой, а не клиент.
    """

    def __init__(
        self,
        base_url: str,
        *,
        service: str,
        api_key: str,
        timeout_s: float = 10.0,
        retries: int = 2,
        backoff_s: float = 0.2,
    ) -> None:
        self._service = service
        self._retries = retries
        self._backoff_s = backoff_s
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_s,
            headers={API_KEY_HEADER: api_key},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Выполняет запрос и возвращает разобранный JSON.

        Ретраи применяются только к идемпотентным методам и только к сетевым
        сбоям и 5xx: повторять 4xx бессмысленно, ответ не изменится.
        """
        attempts = self._retries + 1 if method.upper() in IDEMPOTENT_METHODS else 1
        headers = {REQUEST_ID_HEADER: current_request_id()}
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                response = await self._client.request(method, path, headers=headers, **kwargs)
            except httpx.HTTPError as exc:
                last_error = exc
                log.warning(
                    "upstream.network_error",
                    upstream=self._service,
                    path=path,
                    attempt=attempt + 1,
                    error=type(exc).__name__,
                )
            else:
                if response.status_code < 400:
                    return response.json() if response.content else None
                if response.status_code < 500:
                    raise self._to_domain_error(response)
                last_error = UpstreamError(
                    f"Сервис {self._service} ответил ошибкой",
                    upstream=self._service,
                    status=response.status_code,
                )
                log.warning(
                    "upstream.server_error",
                    upstream=self._service,
                    path=path,
                    status=response.status_code,
                    attempt=attempt + 1,
                )

            if attempt < attempts - 1:
                await asyncio.sleep(self._backoff_s * (2**attempt))

        raise UpstreamError(
            f"Сервис {self._service} недоступен",
            upstream=self._service,
            cause=type(last_error).__name__ if last_error else "unknown",
        )

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    def _to_domain_error(self, response: httpx.Response) -> DomainError:
        """Разворачивает чужой конверт {"error": {...}} в наше исключение.

        Чужой код ошибки сохраняется в details: он нужен при разборе инцидента,
        но наружу мы отдаём собственный — иначе контракт сервиса протекал бы.
        """
        code, message = "UPSTREAM_REJECTED", f"Сервис {self._service} отклонил запрос"
        try:
            payload = response.json().get("error", {})
            code = payload.get("code", code)
            message = payload.get("message", message)
        except Exception:  # noqa: BLE001 — чужой ответ мог оказаться не JSON
            pass

        error = UpstreamError(
            message, upstream=self._service, upstream_code=code, status=response.status_code
        )
        error.http_status = 502 if response.status_code != 404 else 404
        return error

    async def ping(self) -> None:
        """Проверка для /health/ready вызывающего сервиса."""
        response = await self._client.get("/health", timeout=3.0)
        response.raise_for_status()
