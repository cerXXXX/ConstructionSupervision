"""Зависимости FastAPI: проверка ключа.

Сессии БД здесь нет и не будет: сервис не хранит состояние.
"""

from lct_common import make_api_key_dependency

from src.config import settings

require_api_key = make_api_key_dependency(settings.api_key)
