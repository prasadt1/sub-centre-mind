"""Closed-loop nudge engine (transport-agnostic).

For Sub-Centre Mind v1 we keep this in-process and offline-friendly: a state machine
the demo can drive without a real WhatsApp/SMS gateway. Real transports plug in by
implementing a small dispatcher protocol; the engine emits structured AuditEvents so
report drafts can cite back to message IDs.
"""

from .dispatcher import (  # noqa: F401
    ConsoleDispatcher,
    Dispatcher,
    RecordingDispatcher,
)
from .state import (  # noqa: F401
    Nudge,
    NudgeOutcome,
    NudgeState,
    advance,
    new_nudge,
)
from .store import (  # noqa: F401
    deserialize,
    load_nudges,
    save_nudges,
    serialize,
    upsert,
)
