"""Vision module — bounded clinical-adjacent use of Gemma 4 multimodal.

We deliberately scope vision to *routing* and *transcription* tasks, not
diagnostic interpretation. See app/streamlit_app.py "Photo" tab.
"""

from .client import (  # noqa: F401
    VisionResult,
    analyze_image,
    describe_medicine_packet,
    read_printed_text,
    read_register_row,
)
