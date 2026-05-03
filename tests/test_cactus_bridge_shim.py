"""Unit tests for scripts/cactus_bridge_shim.py (no live HTTP server)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SHIM = _ROOT / "scripts" / "cactus_bridge_shim.py"


@pytest.fixture(scope="module")
def shim_mod():
    spec = importlib.util.spec_from_file_location("cactus_bridge_shim", _SHIM)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_forward_returns_upstream_json(shim_mod) -> None:
    fake_resp = MagicMock()
    fake_resp.status = 200
    fake_resp.read.return_value = json.dumps({"response": "hello"}).encode()

    ctx = MagicMock()
    ctx.__enter__.return_value = fake_resp
    ctx.__exit__.return_value = None

    with patch.object(shim_mod, "urlopen", return_value=ctx):
        status, body = shim_mod._forward("http://127.0.0.1:11434", "/api/generate", b"{}", 30.0)

    assert status == 200
    assert json.loads(body.decode())["response"] == "hello"


def test_forward_http_error_passes_body(shim_mod) -> None:
    from urllib.error import HTTPError
    from io import BytesIO

    err = HTTPError("http://x", 500, "Internal", {}, BytesIO(b'{"error":"boom"}'))

    with patch.object(shim_mod, "urlopen", side_effect=err):
        status, body = shim_mod._forward("http://127.0.0.1:11434", "/api/chat", b"{}", 30.0)

    assert status == 500
    assert b"boom" in body
