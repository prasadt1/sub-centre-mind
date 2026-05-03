"""Pure state machine for follow-up nudges. No transport, no I/O.

States:
    SCHEDULED -> SENT -> CONFIRMED       (happy path)
                      \\-> NO_RESPONSE -> ESCALATED (after retries exhausted)

This module is intentionally framework-free so it is unit-testable without
network or storage. The CLI / demo can wrap it with whatever dispatcher
(WhatsApp stub, SMS log, console print) it needs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class NudgeState(str, Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    CONFIRMED = "confirmed"
    NO_RESPONSE = "no_response"
    ESCALATED = "escalated"


class NudgeOutcome(str, Enum):
    """Inputs the engine can receive between states."""

    DISPATCH_OK = "dispatch_ok"
    DISPATCH_FAILED = "dispatch_failed"
    REPLY_CONFIRMED = "reply_confirmed"
    NO_REPLY_TIMEOUT = "no_reply_timeout"


@dataclass(frozen=True)
class Nudge:
    """A single follow-up message and its lifecycle.

    `recipient_ref` is a pseudonym / opaque ID — never raw PII in demos.
    """

    id: str
    recipient_ref: str
    template_id: str
    scheduled_at: datetime
    state: NudgeState = NudgeState.SCHEDULED
    retries: int = 0
    max_retries: int = 1
    last_event_at: Optional[datetime] = None
    history: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def new_nudge(
    *,
    recipient_ref: str,
    template_id: str,
    scheduled_at: Optional[datetime] = None,
    max_retries: int = 1,
) -> Nudge:
    return Nudge(
        id=str(uuid.uuid4()),
        recipient_ref=recipient_ref,
        template_id=template_id,
        scheduled_at=scheduled_at or datetime.now(timezone.utc) + timedelta(days=1),
        max_retries=max_retries,
    )


def _record(n: Nudge, event: str, *, now: datetime) -> Nudge:
    return replace(
        n,
        last_event_at=now,
        history=n.history + ((now.strftime("%Y-%m-%dT%H:%M:%SZ"), event),),
    )


def advance(
    n: Nudge,
    outcome: NudgeOutcome,
    *,
    now: Optional[datetime] = None,
) -> Nudge:
    """Apply an outcome and return the next state. Idempotent on terminal states."""
    now = now or datetime.now(timezone.utc)

    if n.state in (NudgeState.CONFIRMED, NudgeState.ESCALATED):
        return _record(n, f"ignored:{outcome.value}@{n.state.value}", now=now)

    if n.state == NudgeState.SCHEDULED:
        if outcome == NudgeOutcome.DISPATCH_OK:
            return _record(replace(n, state=NudgeState.SENT), "sent", now=now)
        if outcome == NudgeOutcome.DISPATCH_FAILED:
            return _record(
                replace(n, state=NudgeState.ESCALATED),
                "escalated:dispatch_failed",
                now=now,
            )

    if n.state == NudgeState.SENT:
        if outcome == NudgeOutcome.REPLY_CONFIRMED:
            return _record(replace(n, state=NudgeState.CONFIRMED), "confirmed", now=now)
        if outcome == NudgeOutcome.NO_REPLY_TIMEOUT:
            return _record(replace(n, state=NudgeState.NO_RESPONSE), "no_response", now=now)

    if n.state == NudgeState.NO_RESPONSE:
        if outcome == NudgeOutcome.DISPATCH_OK and n.retries < n.max_retries:
            return _record(
                replace(n, state=NudgeState.SENT, retries=n.retries + 1),
                f"retry:{n.retries + 1}",
                now=now,
            )
        if outcome == NudgeOutcome.NO_REPLY_TIMEOUT or n.retries >= n.max_retries:
            return _record(
                replace(n, state=NudgeState.ESCALATED),
                "escalated:no_response",
                now=now,
            )

    return _record(n, f"noop:{outcome.value}@{n.state.value}", now=now)
