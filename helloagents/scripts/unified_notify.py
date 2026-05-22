#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified HelloAGENTS notification entry point."""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _config import get_notify_mode
from _notify_channels import play_context_sound, send_desktop
from _notify_context import (
    VALID_EVENTS,
    NotificationContext,
    build_context,
    build_context_from_codex_payload,
    detect_g3_event,
    load_json,
)

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
TAIL_BYTES = 64 * 1024


def build_context_from_claude_stop(payload: str) -> NotificationContext | None:
    """Build context for Claude Code Stop hook stdin payload."""
    data = load_json(payload)
    cwd = data.get("cwd") or os.getcwd()
    text = ""
    event = "complete"
    project_dir = _find_project_dir(cwd)
    if project_dir:
        jsonl = _latest_jsonl(project_dir)
        if jsonl:
            text, stop_reason = _read_last_assistant_entry(jsonl)
            if stop_reason == "tool_use":
                return None
            event = detect_g3_event(text, default="complete") or "complete"
    return build_context(event, text, cwd)


def notify(context: NotificationContext) -> None:
    """Dispatch desktop and sound notifications according to NOTIFY_LEVEL."""
    mode = get_notify_mode()
    if mode in (1, 3):
        send_desktop(context.title, context.body)
    if mode in (2, 3):
        play_context_sound(context)


def _find_project_dir(cwd: str) -> Path | None:
    expected = CLAUDE_PROJECTS / _cwd_to_project_name(cwd)
    return expected if expected.is_dir() else None


def _cwd_to_project_name(cwd: str) -> str:
    name = cwd.replace(":\\", "--").replace(":/", "--")
    return name.replace("\\", "-").replace("/", "-")


def _latest_jsonl(project_dir: Path) -> Path | None:
    files = [p for p in project_dir.iterdir() if p.suffix == ".jsonl" and p.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime, default=None)


def _read_last_assistant_entry(jsonl_path: Path) -> tuple[str, str]:
    try:
        size = jsonl_path.stat().st_size
        with jsonl_path.open("rb") as fh:
            fh.seek(max(0, size - min(size, TAIL_BYTES)))
            raw = fh.read().decode("utf-8", errors="replace")
    except (OSError, ValueError):
        return "", ""

    for line in reversed(raw.strip().splitlines()):
        try:
            result = _assistant_entry(json.loads(line))
        except (json.JSONDecodeError, TypeError):
            continue
        if result is not None:
            return result
    return "", ""


def _assistant_entry(record: dict) -> tuple[str, str] | None:
    if record.get("type") == "assistant":
        message = record.get("message", {})
        return _extract_content_text(message.get("content", "")), message.get("stop_reason", "") or ""
    if record.get("role") == "assistant":
        return _extract_content_text(record.get("content", "")), record.get("stop_reason", "") or ""
    return None


def _extract_content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item.get("text", "") for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n".join(part for part in parts if part.strip())
    return ""


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HelloAGENTS unified notification")
    parser.add_argument("--event", choices=sorted(VALID_EVENTS))
    parser.add_argument("--message", default="")
    parser.add_argument("--cwd")
    parser.add_argument("--title")
    parser.add_argument("--claude-stop", action="store_true")
    parser.add_argument("--codex-payload")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    stdin_payload = _read_stdin()
    context = _resolve_context(args, stdin_payload)
    if context is not None:
        notify(context)
    return 0


def _resolve_context(args: argparse.Namespace, stdin_payload: str) -> NotificationContext | None:
    if args.codex_payload:
        return build_context_from_codex_payload(args.codex_payload)
    if args.claude_stop:
        return build_context_from_claude_stop(stdin_payload)
    stdin_data = load_json(stdin_payload)
    message = args.message or stdin_data.get("last-assistant-message", "")
    cwd = args.cwd or stdin_data.get("cwd")
    return build_context(args.event or "complete", message, cwd, args.title)


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
