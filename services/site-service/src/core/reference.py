"""Перечисления из packages/contracts/enums.yaml, нужные site-service.

Разбор и проверка уже прочитанного YAML: списков значений в коде нет (AGENTS.md, раздел 7).
Испорченный файл — ошибка старта сервиса, а не тихий пустой список. Тот же разбор есть в
plan-service: код сервисов не общий (AGENTS.md, раздел 6), а 30 строк дешевле общей библиотеки.
"""

from dataclasses import dataclass
from typing import Any

# Перечисления, без которых site-service не может проверить свой вход и выход.
REQUIRED_ENUMS = ("zone_type", "visibility_status", "visibility_reason", "stage_label")


class ReferenceDataError(ValueError):
    """Справочный файл испорчен: сервис с ним не стартует."""


@dataclass(frozen=True)
class Enums:
    values: dict[str, tuple[str, ...]]
    # Роль типа зоны: WORK, SERVICE или SAFETY (methodology.md, раздел 2).
    zone_roles: dict[str, str]

    @property
    def zone_types(self) -> tuple[str, ...]:
        return self.values["zone_type"]


def parse_enums(raw: Any) -> Enums:
    """Списки значений и роли типов зон; у каждого типа зоны должна быть роль."""
    if not isinstance(raw, dict):
        raise ReferenceDataError("enums.yaml: ожидался словарь перечислений")
    values = {
        str(k): tuple(str(v) for v in items) for k, items in raw.items() if isinstance(items, list)
    }
    missing = [name for name in REQUIRED_ENUMS if not values.get(name)]
    if missing:
        raise ReferenceDataError(f"enums.yaml: нет перечислений {missing}")
    roles = raw.get("zone_type_role")
    if not isinstance(roles, dict):
        raise ReferenceDataError("enums.yaml: нет словаря zone_type_role")
    without_role = [z for z in values["zone_type"] if z not in roles]
    if without_role:
        raise ReferenceDataError(f"enums.yaml: у типов зон нет роли: {without_role}")
    return Enums(values, {str(zone): str(role) for zone, role in roles.items()})
