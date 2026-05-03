"""Pure state machine tests — no transport, no clock dependency."""

from datetime import datetime, timezone

from nudges import (
    Nudge,
    NudgeOutcome,
    NudgeState,
    advance,
    new_nudge,
)


def _fixed_now(year=2026, month=5, day=3, hour=10):
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


def test_new_nudge_starts_scheduled():
    n = new_nudge(recipient_ref="P-001", template_id="ifa_followup_d1")
    assert isinstance(n, Nudge)
    assert n.state == NudgeState.SCHEDULED
    assert n.retries == 0
    assert n.history == ()


def test_happy_path_scheduled_sent_confirmed():
    n = new_nudge(recipient_ref="P-001", template_id="ifa_followup_d1")
    n = advance(n, NudgeOutcome.DISPATCH_OK, now=_fixed_now())
    assert n.state == NudgeState.SENT
    n = advance(n, NudgeOutcome.REPLY_CONFIRMED, now=_fixed_now(hour=11))
    assert n.state == NudgeState.CONFIRMED
    kinds = [e[1] for e in n.history]
    assert kinds == ["sent", "confirmed"]


def test_no_response_then_retry_then_escalate():
    n = new_nudge(recipient_ref="P-002", template_id="anc_visit_d3", max_retries=1)
    n = advance(n, NudgeOutcome.DISPATCH_OK, now=_fixed_now())
    n = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT, now=_fixed_now(hour=11))
    assert n.state == NudgeState.NO_RESPONSE
    n = advance(n, NudgeOutcome.DISPATCH_OK, now=_fixed_now(hour=12))
    assert n.state == NudgeState.SENT
    assert n.retries == 1
    n = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT, now=_fixed_now(hour=13))
    assert n.state == NudgeState.NO_RESPONSE
    n = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT, now=_fixed_now(hour=14))
    assert n.state == NudgeState.ESCALATED


def test_dispatch_failed_escalates_immediately():
    n = new_nudge(recipient_ref="P-003", template_id="ifa_followup_d1")
    n = advance(n, NudgeOutcome.DISPATCH_FAILED, now=_fixed_now())
    assert n.state == NudgeState.ESCALATED


def test_terminal_states_are_idempotent():
    n = new_nudge(recipient_ref="P-004", template_id="anc_visit_d3")
    n = advance(n, NudgeOutcome.DISPATCH_OK, now=_fixed_now())
    n = advance(n, NudgeOutcome.REPLY_CONFIRMED, now=_fixed_now(hour=11))
    assert n.state == NudgeState.CONFIRMED
    again = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT, now=_fixed_now(hour=12))
    assert again.state == NudgeState.CONFIRMED
