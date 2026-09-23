"""Правка вехи: даты включительно, работы только на рабочем участке."""

from datetime import date

import pytest
from src.core.stages import StageDatesError, StageZoneError, check_stage, work_zone_types

ROLES = {"PIT": "WORK", "ENTRY_GATE": "SERVICE", "DANGER": "SAFETY", "ROAD": "WORK"}
START = date(2026, 10, 15)


def test_веха_в_один_день_допустима():
    check_stage(START, START, "PIT", ROLES)


def test_конец_раньше_начала_отклоняется():
    with pytest.raises(StageDatesError, match="2026-10-14"):
        check_stage(START, date(2026, 10, 14), "PIT", ROLES)


@pytest.mark.parametrize("zone_type", ["ENTRY_GATE", "DANGER", "SPACEPORT"])
def test_веха_не_бывает_на_служебном_опасном_или_неизвестном_участке(zone_type):
    with pytest.raises(StageZoneError, match="PIT"):
        check_stage(START, START, zone_type, ROLES)


def test_рабочие_типы_в_порядке_справочника():
    assert work_zone_types(ROLES) == ("PIT", "ROAD")
