"""Конфигурация analysis-service. Единственное место чтения окружения."""

from lct_common import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "analysis-service"

    # База сервиса. Роль analysis_user имеет права только на analysisdb (ADR-0003).
    analysis_db_dsn: str = "postgresql+asyncpg://analysis_user:analysis@postgres:5432/analysisdb"
    db_echo: bool = False

    # Справочные файлы контрактов, смонтированные только для чтения: enums.yaml
    # задаёт роли типов зон и порядок стадий по фото.
    contracts_dir: str = "/contracts"


settings = Settings()
