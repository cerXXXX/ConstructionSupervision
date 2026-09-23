"""Правка вехи: какие значения веха может принять (docs/data-model.md, раздел 1.4).

Даты вехи — обе включительно, поэтому веха в один день допустима, а конец раньше начала — нет.
Работы вехи идут на рабочем участке: въезд, склад и опасная зона вехой не бывают, иначе
правило вехи искало бы технику там, где она только ждёт.
"""

from collections.abc import Mapping
from datetime import date

# Роль типа зоны, на которой идут работы вех (enums.yaml: zone_type_role).
WORK_ROLE = "WORK"


class StageError(ValueError):
    """Веха в таком виде не имеет смысла и не сохраняется."""


class StageDatesError(StageError):
    """Плановый конец раньше планового начала."""


class StageZoneError(StageError):
    """Тип участка вехи — не рабочий."""


def work_zone_types(zone_roles: Mapping[str, str]) -> tuple[str, ...]:
    """Типы зон с ролью WORK — в порядке enums.yaml."""
    return tuple(zone for zone, role in zone_roles.items() if role == WORK_ROLE)


def check_stage(
    plan_start: date, plan_end: date, zone_type: str, zone_roles: Mapping[str, str]
) -> None:
    """Проверка вехи после правки: даты и тип участка."""
    if plan_end < plan_start:
        raise StageDatesError(
            f"Плановое окончание {plan_end.isoformat()} раньше начала {plan_start.isoformat()}"
        )
    if zone_roles.get(zone_type) != WORK_ROLE:
        raise StageZoneError(
            f"На участке типа {zone_type} работы вех не идут; "
            f"допустимо: {list(work_zone_types(zone_roles))}"
        )
