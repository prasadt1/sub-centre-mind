#!/usr/bin/env python3
"""Ollama-compatible HTTP proxy — verifies the ``SCM_BACKEND=cactus`` path end-to-end.

This is **not** the production Cactus native companion (Kotlin / libcactus). It is a
**development shim** that exposes the same ``/api/generate`` and ``/api/chat`` JSON
wire format as Ollama and forwards to a real Ollama daemon. Use it to:

- Run Streamlit (or ``query_router`` / ``generate_answer``) with
  ``SCM_BACKEND=cactus`` and ``SCM_CACTUS_HTTP_BASE=http://127.0.0.1:18765``
- Prove the :class:`llm.cactus.CactusBackend` code path before a phone companion exists
- Record a demo that shows "Cactus URL" → same safety stack (see docs/cactus-poc.md)

Replace this shim with a Kotlin/Cactus on-device server that implements the same
two routes when the mobile POC is ready.

Examples::

    # Terminal A — Ollama
    ollama serve

    # Terminal B — shim (forwards to Ollama)
    python scripts/cactus_bridge_shim.py --port 18765

    # Terminal C — app using Cactus backend
    export SCM_BACKEND=cactus SCM_CACTUS_HTTP_BASE=http://127.0.0.1:18765
    bash scripts/run_app.sh
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_MAX_BODY = 60 * 1024 * 1024  # 60 MiB (vision payloads)


def _forward(upstream_base: str, path: str, body: bytes, timeout: float) -> tuple[int, bytes]:
    base = upstream_base.rstrip("/")
    url = f"{base}{path}"
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except HTTPError as e:
        err_body = e.read()
        if err_body:
            return e.code, err_body
        return e.code, json.dumps({"error": e.reason}).encode()
    except URLError as e:
        return 502, json.dumps({"error": f"upstream: {e.reason}"}).encode()


def make_handler(upstream: str, timeout: float) -> type[BaseHTTPRequestHandler]:
    class _H(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

        def do_POST(self) -> None:
            if self.path not in ("/api/generate", "/api/chat"):
                self.send_error(404, "only /api/generate and /api/chat")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400, "bad Content-Length")
                return
            if length > _MAX_BODY:
                self.send_error(413, "body too large")
                return
            body = self.rfile.read(length) if length else b""
            status, out = _forward(upstream, self.path, body, timeout)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

    return _H


def main() -> None:
    ap = argparse.ArgumentParser(description="Ollama-compatible proxy for CactusBackend dev")
    ap.add_argument("--host", default="127.0.0.1", help="bind address")
    ap.add_argument("--port", type=int, default=18765, help="bind port (default matches ADR examples)")
    ap.add_argument(
        "--upstream",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        help="Ollama base URL (no trailing /api/...)",
    )
    ap.add_argument("--timeout", type=float, default=300.0, help="per-request upstream timeout (s)")
    args = ap.parse_args()

    handler = make_handler(args.upstream, args.timeout)
    httpd = HTTPServer((args.host, args.port), handler)
    print(
        f"cactus_bridge_shim: listening http://{args.host}:{args.port}\n"
        f"  forwarding POST /api/generate and /api/chat → {args.upstream}\n"
        f"\n"
        f"  export SCM_BACKEND=cactus SCM_CACTUS_HTTP_BASE=http://{args.host}:{args.port}\n"
        f"  bash scripts/run_app.sh\n",
        file=sys.stderr,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshim stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
