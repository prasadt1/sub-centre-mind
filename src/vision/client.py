"""Thin client around Ollama /api/chat with the `images` field for Gemma 4.

We expose a small set of *bounded* prompts for Sub-Centre Mind use cases:
  - read_printed_text:        guideline / poster / printed protocol photo
  - describe_medicine_packet: medicine pack OCR — always advisory + escalate
  - read_register_row:        ANC/RCH register row → suggested structured draft

Vision is never used for diagnostic interpretation (no rashes, no ECGs, no
ultrasound, no skin/eye images). The Streamlit UI surfaces this boundary too.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional

from llm import GenerateOptions, get_backend


@dataclass(frozen=True)
class VisionResult:
    text: str
    use_case: str
    model: str
    boundary_note: str


def _post_vision(image_bytes: bytes, *, prompt: str, model: str, num_predict: int, timeout: float) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    backend = get_backend()
    return backend.vision(
        b64,
        prompt,
        model=model,
        options=GenerateOptions(num_predict=num_predict, temperature=0.1),
        timeout=timeout,
    )


def analyze_image(
    image_bytes: bytes,
    *,
    prompt: str,
    use_case: str = "custom",
    model: Optional[str] = None,
    num_predict: int = 220,
    timeout: float = 180.0,
    boundary_note: str = "",
) -> VisionResult:
    """Generic image-to-text via Gemma 4 vision (Ollama)."""
    mdl = model or os.environ.get("SCM_MODEL", "gemma4:latest")
    text = _post_vision(
        image_bytes,
        prompt=prompt,
        model=mdl,
        num_predict=num_predict,
        timeout=timeout,
    )
    return VisionResult(text=text, use_case=use_case, model=mdl, boundary_note=boundary_note)


# --- Sub-Centre Mind preset use cases ----------------------------------------

PRINTED_TEXT_PROMPT = (
    "You are reading a printed clinical protocol page or poster. "
    "Output ONLY the text visible in the image, line by line. "
    "Do not summarize, interpret, or add commentary. "
    "If text is unclear, write [unclear] for that part."
)

MEDICINE_PACKET_PROMPT = (
    "You are looking at a photograph of a medicine packet or strip. "
    "Extract the visible brand name, generic name, and dose strength as a short list. "
    "Do NOT recommend whether to give the medicine, the dose, or the timing. "
    "End your output with: 'Decision required from Medical Officer.'"
)

REGISTER_ROW_PROMPT = (
    "You are reading one row of a paper ANC / RCH register. "
    "Extract the visible fields as 'field: value' pairs (e.g. 'Date: ...', 'Hb: ...', 'BP: ...'). "
    "If a value is illegible, mark it [unclear]. "
    "Do not interpret the values. Do not infer diagnoses."
)


def read_printed_text(image_bytes: bytes, **kwargs) -> VisionResult:
    return analyze_image(
        image_bytes,
        prompt=PRINTED_TEXT_PROMPT,
        use_case="printed_text",
        boundary_note=(
            "Vision OCR only. Text returned is verbatim; no clinical interpretation. "
            "Use the Ask tab to retrieve grounded protocol guidance for the same topic."
        ),
        **kwargs,
    )


def describe_medicine_packet(image_bytes: bytes, **kwargs) -> VisionResult:
    return analyze_image(
        image_bytes,
        prompt=MEDICINE_PACKET_PROMPT,
        use_case="medicine_packet",
        boundary_note=(
            "Sub-Centre Mind does not authorize dosing or administration. "
            "Always escalate medicine decisions to the Medical Officer."
        ),
        **kwargs,
    )


def read_register_row(image_bytes: bytes, **kwargs) -> VisionResult:
    return analyze_image(
        image_bytes,
        prompt=REGISTER_ROW_PROMPT,
        use_case="register_row",
        boundary_note=(
            "Extracted fields are a draft. ANM must verify each value against the original "
            "register before any use; system performs no clinical interpretation."
        ),
        **kwargs,
    )
