"""Базовые настройки сервиса. Единственное место чтения окружения."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Поля, одинаковые у всех сервисов.

    Сервис наследуется от этого класса и добавляет своё. Обращение к os.environ
    где-либо ещё — ошибка: конфигурация должна быть видна в одном месте.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    service_name: str = "service"
    version: str = "0.1.0"
    env: str = "dev"
    log_level: str = "INFO"

    # Ключ проверяется каждым сервисом самостоятельно, в том числе при вызове
    # изнутри сети compose: доверия «по сети» у нас нет (ADR-0010).
    api_key: str = "dev-key-change-me"

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"
