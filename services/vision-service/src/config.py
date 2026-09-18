"""Конфигурация vision-service. Единственное место чтения окружения."""

from lct_common import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "vision-service"

    # Устройство инференса. На демо-стенде — cuda, запасной путь при непробро-
    # шенной карте — cpu (docs/roadmap.md, раздел 5: это зафиксированный риск).
    vision_device: str = "cuda"


settings = Settings()
