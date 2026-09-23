"""Сверка эпизодов прогона с лентой отклонений (docs/methodology.md, раздел 9)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.ledger import LedgerRow, reconcile
from src.core.predicates import Finding

T0 = datetime(2026, 10, 20, 6, tzinfo=UTC)
KEY = (None, "PIT:Котлован", "D2", None)


def _finding(start_h=0, end_h=2, *, active=True, key=KEY):
    stage_id, area, code, cls = key
    return Finding(
        code=code,
        severity="MEDIUM",
        stage_id=stage_id,
        area=area,
        equipment_class=cls,
        session_id=uuid4(),
        first_seen_at=T0 + timedelta(hours=start_h),
        last_seen_at=T0 + timedelta(hours=end_h),
        occurrences=4,
        active=active,
        facts={"n": 1},
        evidence=({"image_id": "x", "detection_ids": []},),
    )


def _row(status="NEW", start_h=0, end_h=1, key=KEY):
    return LedgerRow(
        id=uuid4(),
        key=key,
        status=status,
        first_seen_at=T0 + timedelta(hours=start_h),
        last_seen_at=T0 + timedelta(hours=end_h),
    )


def test_новый_эпизод_открывается():
    plan = reconcile([], [_finding()])

    assert [status for _, status in plan.insert] == ["NEW"] and plan.opened == 1


def test_закончившийся_эпизод_без_строки_попадает_в_историю_закрытым():
    plan = reconcile([], [_finding(active=False)])

    assert [status for _, status in plan.insert] == ["RESOLVED"] and plan.opened == 0


def test_повтор_обновляет_строку_а_не_плодит_дубль():
    row = _row()

    plan = reconcile([row], [_finding()])

    assert plan.insert == () and plan.resolve == ()
    assert [(i, s) for i, _, s in plan.update] == [(row.id, "NEW")]


def test_вердикт_оператора_сохраняется_пока_условие_держится():
    confirmed, rejected = _row("CONFIRMED"), _row("REJECTED", key=(None, "B", "D2", None))

    plan = reconcile([confirmed, rejected], [_finding(), _finding(key=(None, "B", "D2", None))])

    assert {(i, s) for i, _, s in plan.update} == {
        (confirmed.id, "CONFIRMED"),
        (rejected.id, "REJECTED"),
    }


def test_условие_пропало_строка_закрывается():
    row = _row()

    plan = reconcile([row], [_finding(active=False)])

    assert [(i, s) for i, _, s in plan.update] == [(row.id, "RESOLVED")]


def test_открытая_строка_без_эпизода_закрывается():
    row = _row()

    assert reconcile([row], []).resolve == (row.id,)


def test_отклонённое_после_перерыва_открывается_заново():
    rejected = _row("REJECTED", start_h=0, end_h=1)

    plan = reconcile([rejected], [_finding(0, 1, active=False), _finding(3, 5)])

    assert [(i, s) for i, _, s in plan.update] == [(rejected.id, "REJECTED")]
    assert [s for _, s in plan.insert] == ["NEW"]


def test_устаревшая_открытая_строка_закрывается_раньше_новой_по_тому_же_ключу():
    stale = _row("NEW", start_h=0, end_h=1)

    plan = reconcile([stale], [_finding(3, 5)])

    assert plan.resolve == (stale.id,)
    assert [s for _, s in plan.insert] == ["NEW"]


def test_закрытый_эпизод_снова_держится_открывается():
    resolved = _row("RESOLVED", start_h=0, end_h=1)

    plan = reconcile([resolved], [_finding(0, 3)])

    assert [(i, s) for i, _, s in plan.update] == [(resolved.id, "NEW")]
