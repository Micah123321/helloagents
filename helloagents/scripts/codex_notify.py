#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HelloAGENTS Codex notify proxy.

Keeps Codex-specific update checks and delegates user notifications to the
unified notification entry point.
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
UNIFIED_NOTIFY = SCRIPTS_DIR / "unified_notify.py"


def main() -> int:
    _ensure_utf8_stdio()
    payload = sys.argv[1] if len(sys.argv) > 1 else ""
    if payload and UNIFIED_NOTIFY.exists():
        _run_unified_notify(payload)
    _run_update_check()
    return 0


def _ensure_utf8_stdio() -> None:
    if sys.platform != "win32":
        return
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None or getattr(stream, "closed", False):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            buffer = getattr(stream, "buffer", None)
            if buffer is not None and not getattr(buffer, "closed", False):
                setattr(sys, name, io.TextIOWrapper(
                    buffer, encoding="utf-8", errors="replace"))


def _run_unified_notify(payload: str) -> None:
    try:
        subprocess.run(
            [sys.executable, str(UNIFIED_NOTIFY), "--codex-payload", payload],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def _run_update_check() -> None:
    try:
        subprocess.Popen(
            ["helloagents", "--check-update", "--silent"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
