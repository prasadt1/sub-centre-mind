"""JSONL event schema for Sub-Centre Mind audit trail."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal

EventType = Literal[
    "rag_answer",
    "confidence_gate_blocked",
    "tool_refusal",
    "tool_protocol",
]


@dataclass
class AuditEvent:
    """One append-only event line (JSON object per line)."""

    ts_iso: str
    event_id: str
    kind: EventType
    detail: dict[str, Any] = field(default_factory=dict)

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def new_event(kind: EventType, **detail: Any) -> AuditEvent:
    return AuditEvent(
        ts_iso=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        event_id=str(uuid.uuid4()),
        kind=kind,
        detail=dict(detail),
    )


def append_event(path: Path, ev: AuditEvent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(ev.to_json_line() + "\n")


def iter_events(path: Path) -> Iterator[AuditEvent]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            yield AuditEvent(
                ts_iso=d["ts_iso"],
                event_id=d["event_id"],
                kind=d["kind"],
                detail=d.get("detail") or {},
            )
