"""Конфигурация plan-service. Единственное место чтения окружения."""

from lct_common import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "plan-service"

    # База сервиса. Роль plan_user имеет права только на plandb (ADR-0003).
    plan_db_dsn: str = "postgresql+asyncpg://plan_user:plan@postgres:5432/plandb"
    db_echo: bool = False

    # Нормативный расчётчик ПОС. Недоступен — генерация графика отвечает 503,
    # импорт из CSV/XLSX при этом продолжает работать.
    pos_url: str = "http://pos-engine:8000"
    pos_timeout_s: float = 20.0

    # Календарь по умолчанию для новых объектов.
    default_calendar: str = "moscow-6day"


settings = Settings()
