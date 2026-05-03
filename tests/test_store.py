"""Round-trip tests for nudge JSON persistence."""

from datetime import datetime, timezone
from pathlib import Path

from nudges import (
    NudgeOutcome,
    NudgeState,
    advance,
    deserialize,
    load_nudges,
    new_nudge,
    save_nudges,
    serialize,
    upsert,
)


def _fixed(hour=10):
    return datetime(2026, 5, 3, hour, tzinfo=timezone.utc)


def test_serialize_roundtrip_preserves_state_and_history():
    n = new_nudge(
        recipient_ref="P-001",
        template_id="ifa_followup_d1",
        scheduled_at=_fixed(8),
        max_retries=2,
    )
    n = advance(n, NudgeOutcome.DISPATCH_OK, now=_fixed(9))
    n = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT, now=_fixed(10))
    d = serialize(n)
    n2 = deserialize(d)

    assert n2.id == n.id
    assert n2.recipient_ref == n.recipient_ref
    assert n2.template_id == n.template_id
    assert n2.state == n.state == NudgeState.NO_RESPONSE
    assert n2.retries == n.retries
    assert n2.max_retries == n.max_retries
    assert n2.scheduled_at == n.scheduled_at
    assert n2.last_event_at == n.last_event_at
    assert n2.history == n.history


def test_load_save_roundtrip(tmp_path: Path):
    p = tmp_path / "store.json"
    a = new_nudge(recipient_ref="P-A", template_id="anc_visit_d3", scheduled_at=_fixed())
    b = new_nudge(recipient_ref="P-B", template_id="ifa_followup_d1", scheduled_at=_fixed())
    save_nudges(p, [a, b])
    out = load_nudges(p)
    assert {n.id for n in out} == {a.id, b.id}


def test_load_missing_file_returns_empty(tmp_path: Path):
    assert load_nudges(tmp_path / "nope.json") == []


def test_upsert_replaces_existing_and_preserves_order(tmp_path: Path):
    a = new_nudge(recipient_ref="P-A", template_id="anc_visit_d3", scheduled_at=_fixed())
    b = new_nudge(recipient_ref="P-B", template_id="ifa_followup_d1", scheduled_at=_fixed())
    nudges = [a, b]
    a2 = advance(a, NudgeOutcome.DISPATCH_OK, now=_fixed(11))
    new_list = upsert(nudges, a2)
    assert [n.id for n in new_list] == [a.id, b.id]
    assert new_list[0].state == NudgeState.SENT


def test_upsert_appends_when_unknown():
    a = new_nudge(recipient_ref="P-A", template_id="anc_visit_d3", scheduled_at=_fixed())
    b = new_nudge(recipient_ref="P-B", template_id="ifa_followup_d1", scheduled_at=_fixed())
    out = upsert([a], b)
    assert len(out) == 2 and out[-1].id == b.id
