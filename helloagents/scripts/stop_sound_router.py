#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude Code Stop hook compatibility wrapper.

The actual event routing and notification dispatch live in unified_notify.py.
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

UNIFIED_NOTIFY = Path(__file__).parent / "unified_notify.py"


def main() -> int:
    _ensure_utf8_stdio()
    payload = _read_stdin()
    if not UNIFIED_NOTIFY.exists():
        return 0
    try:
        subprocess.run(
            [sys.executable, str(UNIFIED_NOTIFY), "--claude-stop"],
            input=payload,
            text=True,
            encoding="utf-8",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass
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


def _read_stdin() -> str:
    try:
        return sys.stdin.read()
    except Exception:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
