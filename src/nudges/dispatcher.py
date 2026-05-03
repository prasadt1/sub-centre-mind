"""Dispatcher protocol for the nudge engine.

A dispatcher takes a Nudge and reports the outcome of trying to deliver it.
Real transports (WhatsApp, SMS, voice) plug in by implementing this Protocol;
the state machine itself stays transport-free.

For v1 we ship two small implementations:
    - ConsoleDispatcher: prints a one-line "would-send" message, returns DISPATCH_OK
    - RecordingDispatcher: collects calls in-memory (used by tests + the UI)

Real transports (WhatsApp Business API, BSP gateway, SMS providers) are
intentionally out of scope for the demo path to keep the data-sovereignty
narrative consistent. They can be added later without touching state.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from .state import Nudge, NudgeOutcome


@runtime_checkable
class Dispatcher(Protocol):
    """Anything callable as `dispatcher.send(nudge) -> NudgeOutcome`."""

    def send(self, nudge: Nudge) -> NudgeOutcome:  # pragma: no cover - Protocol shape
        ...


@dataclass
class ConsoleDispatcher:
    """Default demo dispatcher: prints a deterministic one-liner."""

    prefix: str = "[nudge]"

    def send(self, nudge: Nudge) -> NudgeOutcome:
        print(
            f"{self.prefix} would send template={nudge.template_id} "
            f"to recipient_ref={nudge.recipient_ref} (id={nudge.id[:8]})"
        )
        return NudgeOutcome.DISPATCH_OK


@dataclass
class RecordingDispatcher:
    """Test / UI dispatcher: appends call info, configurable outcome."""

    outcome: NudgeOutcome = NudgeOutcome.DISPATCH_OK
    calls: list[dict[str, Any]] = field(default_factory=list)

    def send(self, nudge: Nudge) -> NudgeOutcome:
        self.calls.append(
            {
                "id": nudge.id,
                "recipient_ref": nudge.recipient_ref,
                "template_id": nudge.template_id,
                "state_before": nudge.state.value,
            }
        )
        return self.outcome
