"""Dispatcher Protocol smoke tests (no transports)."""

from datetime import datetime, timezone

from nudges import (
    ConsoleDispatcher,
    Dispatcher,
    NudgeOutcome,
    RecordingDispatcher,
    new_nudge,
)


def _fixed():
    return datetime(2026, 5, 3, 10, tzinfo=timezone.utc)


def test_console_dispatcher_satisfies_protocol(capsys):
    d = ConsoleDispatcher()
    assert isinstance(d, Dispatcher)
    n = new_nudge(recipient_ref="P-001", template_id="ifa_followup_d1", scheduled_at=_fixed())
    out = d.send(n)
    assert out == NudgeOutcome.DISPATCH_OK
    captured = capsys.readouterr()
    assert "ifa_followup_d1" in captured.out
    assert "P-001" in captured.out


def test_recording_dispatcher_records_and_returns_configured_outcome():
    d = RecordingDispatcher(outcome=NudgeOutcome.DISPATCH_FAILED)
    n = new_nudge(recipient_ref="P-002", template_id="anc_visit_d3", scheduled_at=_fixed())
    out = d.send(n)
    assert out == NudgeOutcome.DISPATCH_FAILED
    assert len(d.calls) == 1
    assert d.calls[0]["template_id"] == "anc_visit_d3"
    assert d.calls[0]["recipient_ref"] == "P-002"
