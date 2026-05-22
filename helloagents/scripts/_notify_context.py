#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Notification context parsing helpers for HelloAGENTS hooks."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


VALID_EVENTS = {"complete", "idle", "confirm", "error", "warning"}
EVENT_PREFIX = {
    "complete": "完成了",
    "idle": "在等你呢",
    "confirm": "需要确认",
    "error": "出错了",
    "warning": "需要注意",
}

G3_MARKER = "\u3010HelloAGENTS\u3011"
WARNING_ICONS = frozenset({"\u26a0\ufe0f", "\u26a0"})
ERROR_ICONS = frozenset({"\u274c"})
COMPLETE_ICONS = frozenset({"\u2705", "\U0001f4a1", "\u26a1", "\U0001f527"})
CONFIRM_ICONS = frozenset({"\u2753", "\U0001f4d0"})
CONTEXT_ICONS = frozenset({"\U0001f535"})
TUI_CLIENT = "codex-tui"


@dataclass(frozen=True)
class NotificationContext:
    """Resolved notification content for all channels."""

    event: str
    project: str
    task: str
    title: str
    body: str
    speech: str


def clean_text(value: str, limit: int) -> str:
    """Normalize user-visible notification text and enforce max length."""
    text = re.sub(r"[\r\n\t]+", " ", value or "")
    text = re.sub(r"\s+", " ", text.replace("`", "")).strip(" -:：")
    if not text:
        return ""
    return text[: max(0, limit - 1)].rstrip() + "…" if len(text) > limit else text


def project_name_from_cwd(cwd: str | None) -> str:
    """Return a short project name inferred from cwd."""
    raw = cwd or os.getcwd()
    try:
        path = Path(raw).expanduser()
        name = path.name or path.drive.rstrip(":") or "当前项目"
    except (OSError, ValueError):
        name = str(raw).replace("\\", "/").rstrip("/").split("/")[-1]
    return clean_text(name, 32) or "当前项目"


def detect_g3_event(text: str, default: str | None = "complete") -> str | None:
    """Detect a notification event from a HelloAGENTS G3 status line."""
    if not text:
        return default
    first_line = text.strip().split("\n")[0]
    marker_index = first_line.find(G3_MARKER)
    if marker_index < 0:
        return default
    icon = first_line[:marker_index].strip()
    status_text = first_line[marker_index + len(G3_MARKER):]
    return _event_from_icon(icon, status_text, default) if icon else default


def task_summary_from_message(text: str, fallback: str = "当前任务") -> str:
    """Extract a short task summary from a final assistant message."""
    if not text:
        return fallback
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return fallback

    candidates = [_status_summary(lines[0])]
    labels = ("📋 需求:", "执行结果:", "变更摘要:", "✅", "- ")
    for line in lines[1:8]:
        if line.startswith("🔄"):
            continue
        if any(line.startswith(label) for label in labels):
            candidates.append(line)
    if len(candidates) == 1:
        candidates.extend(lines[1:4])

    for candidate in candidates:
        clean = clean_text(_strip_summary_label(candidate), 56)
        if clean:
            return clean
    return fallback


def build_context(
    event: str,
    message: str = "",
    cwd: str | None = None,
    title: str | None = None,
) -> NotificationContext:
    """Build a unified notification context."""
    safe_event = event if event in VALID_EVENTS else "complete"
    project = project_name_from_cwd(cwd)
    task = task_summary_from_message(message)
    prefix = EVENT_PREFIX[safe_event]
    body = f"{prefix} - {project} - {task}"
    return NotificationContext(
        event=safe_event,
        project=project,
        task=task,
        title=title or "HelloAGENTS",
        body=body,
        speech=body,
    )


def build_context_from_codex_payload(payload: str) -> NotificationContext | None:
    """Build context from Codex CLI notify payload."""
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return None
    client = (data.get("client") or "").lower()
    if client and client != TUI_CLIENT:
        return None

    notify_type = data.get("type", "")
    cwd = data.get("cwd") or data.get("workspace") or data.get("project")
    if notify_type == "approval-requested":
        return build_context("confirm", data.get("last-assistant-message", ""), cwd)
    if notify_type != "agent-turn-complete":
        return None

    last_msg = data.get("last-assistant-message", "")
    event = detect_g3_event(last_msg, default=None)
    return build_context(event, last_msg, cwd) if event else None


def load_json(raw: str) -> dict:
    """Load JSON object from raw text, returning empty dict on failure."""
    try:
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _event_from_icon(icon: str, status_text: str, default: str | None) -> str | None:
    for ch in WARNING_ICONS:
        if ch in icon:
            return "warning"
    for ch in ERROR_ICONS:
        if ch in icon:
            return "error"
    for ch in COMPLETE_ICONS:
        if ch in icon:
            return "complete"
    for ch in CONFIRM_ICONS:
        if ch in icon:
            return "confirm"
    for ch in CONTEXT_ICONS:
        return "confirm" if "确认" in status_text else "idle"
    return default


def _status_summary(first_line: str) -> str:
    marker_index = first_line.find(G3_MARKER)
    if marker_index < 0:
        return ""
    status = first_line[marker_index + len(G3_MARKER):]
    return clean_text(status.lstrip(" -—–"), 52)


def _strip_summary_label(text: str) -> str:
    labels = (
        "📋 需求:", "📋 需求：", "执行结果:", "执行结果：",
        "变更摘要:", "变更摘要：", "✅", "- ",
    )
    value = text
    for label in labels:
        if value.startswith(label):
            return value[len(label):]
    return value
