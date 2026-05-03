#!/usr/bin/env python3
"""
Demo dispatcher for the nudge state machine.

No real transport: this prints what *would* be sent, drives a small scripted
scenario (confirmed + escalated paths), and optionally appends AuditEvents
to a JSONL log so the report draft can include them.

Usage:
    python scripts/run_nudges.py
    SCM_AUDIT_LOG=data/logs/dev_events.jsonl python scripts/run_nudges.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
for p in (_SRC, _REPO):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from audit.schema import append_event, new_event
from nudges import Nudge, NudgeOutcome, advance, new_nudge


def _print_step(n: Nudge, label: str) -> None:
    last = n.history[-1][1] if n.history else "-"
    print(f"  [{n.id[:8]}] state={n.state.value:<11} retries={n.retries} last={last:<22} ({label})")


def _audit(audit_log: Optional[Path], n: Nudge, kind: str) -> None:
    if audit_log is None:
        return
    append_event(
        audit_log,
        new_event(
            "tool_protocol" if kind == "confirmed" else "tool_refusal",
            nudge_id=n.id,
            recipient_ref=n.recipient_ref,
            template_id=n.template_id,
            terminal_state=n.state.value,
            channel="demo-stub",
        ),
    )


def scenario_happy(audit_log: Optional[Path]) -> None:
    print("\n[Scenario A] IFA reminder confirmed")
    n = new_nudge(recipient_ref="P-001-pseudo", template_id="ifa_followup_d1")
    _print_step(n, "scheduled")
    n = advance(n, NudgeOutcome.DISPATCH_OK)
    _print_step(n, "sent")
    n = advance(n, NudgeOutcome.REPLY_CONFIRMED)
    _print_step(n, "confirmed (reply: ली)")
    _audit(audit_log, n, "confirmed")


def scenario_escalation(audit_log: Optional[Path]) -> None:
    print("\n[Scenario B] ANC visit reminder — no reply, retry, escalate")
    n = new_nudge(
        recipient_ref="P-002-pseudo",
        template_id="anc_visit_d3",
        max_retries=1,
    )
    _print_step(n, "scheduled")
    n = advance(n, NudgeOutcome.DISPATCH_OK)
    _print_step(n, "sent")
    n = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT)
    _print_step(n, "timeout #1")
    n = advance(n, NudgeOutcome.DISPATCH_OK)
    _print_step(n, "retry sent")
    n = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT)
    _print_step(n, "timeout #2")
    n = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT)
    _print_step(n, "escalated → ASHA / MO")
    _audit(audit_log, n, "escalated")


def main() -> None:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Sub-Centre Mind nudge demo — started {started}")
    print("(transport stub: prints state transitions; no WhatsApp / SMS sent)")

    audit_log_env = os.environ.get("SCM_AUDIT_LOG")
    audit_log = Path(audit_log_env) if audit_log_env else None
    if audit_log:
        print(f"Audit log: {audit_log}")

    scenario_happy(audit_log)
    scenario_escalation(audit_log)

    print("\nDone.")


if __name__ == "__main__":
    main()
