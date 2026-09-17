"""Проверка API-ключа.

Единственная точка расширения на OIDC/SSO: когда появится внешняя
аутентификация, меняется только реализация этой зависимости (ADR-0010).
"""

import secrets

from fastapi import Header

from lct_common.errors import UnauthorizedError

API_KEY_HEADER = "X-API-Key"


def make_api_key_dependency(expected_key: str):
    """Возвращает зависимость FastAPI, проверяющую заголовок X-API-Key.

    Сравнение постоянное по времени: наивное `==` на секретах — плохая привычка,
    даже когда угроза неактуальна.
    """

    async def require_api_key(x_api_key: str = Header(default="")) -> None:
        if not secrets.compare_digest(x_api_key, expected_key):
            raise UnauthorizedError("Неверный или отсутствующий API-ключ")

    return require_api_key
