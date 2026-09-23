"""Конфигурация plan-service. Единственное место чтения окружения."""

from lct_common import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "plan-service"

    # База сервиса. Роль plan_user имеет права только на plandb (ADR-0003).
    plan_db_dsn: str = "postgresql+asyncpg://plan_user:plan@postgres:5432/plandb"
    db_echo: bool = False

    # Календарь по умолчанию для новых объектов.
    default_calendar: str = "moscow-6day"

    # Справочные файлы контрактов, смонтированные только для чтения: классы техники
    # (equipment_classes.yaml) и перечисления (enums.yaml). ADR-0014.
    contracts_dir: str = "/contracts"


settings = Settings()
