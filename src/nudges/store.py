"""JSON persistence for the Nudge state machine.

Nudges are mutable across runs (state, retries, history). We persist the
*current* list as a single JSON document with atomic write (tmp + rename).

This is intentionally separate from the audit JSONL log:
    - audit log = append-only, immutable events
    - nudge store = current-state of each nudge
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .state import Nudge, NudgeState


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


def serialize(n: Nudge) -> dict[str, Any]:
    return {
        "id": n.id,
        "recipient_ref": n.recipient_ref,
        "template_id": n.template_id,
        "scheduled_at": n.scheduled_at.isoformat(),
        "state": n.state.value,
        "retries": n.retries,
        "max_retries": n.max_retries,
        "last_event_at": _iso(n.last_event_at),
        "history": [list(h) for h in n.history],
    }


def deserialize(d: dict[str, Any]) -> Nudge:
    last = d.get("last_event_at")
    return Nudge(
        id=str(d["id"]),
        recipient_ref=str(d["recipient_ref"]),
        template_id=str(d["template_id"]),
        scheduled_at=datetime.fromisoformat(d["scheduled_at"]),
        state=NudgeState(d.get("state", NudgeState.SCHEDULED.value)),
        retries=int(d.get("retries", 0)),
        max_retries=int(d.get("max_retries", 1)),
        last_event_at=datetime.fromisoformat(last) if last else None,
        history=tuple(tuple(h) for h in d.get("history", [])),
    )


def load_nudges(path: Path) -> list[Nudge]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    out: list[Nudge] = []
    for d in raw:
        if isinstance(d, dict):
            try:
                out.append(deserialize(d))
            except (KeyError, ValueError):
                continue
    return out


def save_nudges(path: Path, nudges: Iterable[Nudge]) -> None:
    """Atomic write: tmp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = [serialize(n) for n in nudges]
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def upsert(nudges: list[Nudge], updated: Nudge) -> list[Nudge]:
    """Return a new list with `updated` replacing the entry of the same id, else appended."""
    out: list[Nudge] = []
    found = False
    for n in nudges:
        if n.id == updated.id:
            out.append(updated)
            found = True
        else:
            out.append(n)
    if not found:
        out.append(updated)
    return out
