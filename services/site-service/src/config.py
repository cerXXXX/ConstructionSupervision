"""Конфигурация site-service. Единственное место чтения окружения."""

from lct_common import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "site-service"

    # База сервиса. Роль site_user имеет права только на sitedb (ADR-0003).
    site_db_dsn: str = "postgresql+asyncpg://site_user:site@postgres:5432/sitedb"
    db_echo: bool = False

    # Справочные файлы контрактов, смонтированные только для чтения: enums.yaml (типы и роли
    # зон, статусы видимости).
    contracts_dir: str = "/contracts"

    # Длина окна сессии наблюдения: состав техники считается по сессии, а не по
    # кадру, иначе одна машина в двух камерах была бы посчитана дважды.
    session_window_minutes: int = 30


settings = Settings()
