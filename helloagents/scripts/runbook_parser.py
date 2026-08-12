"""Helpers for extracting local validation commands from runbook.yaml."""

from __future__ import annotations

import shlex
import sys
from pathlib import Path
from typing import Optional


def strip_inline_comment(value: str) -> str:
    """Remove a YAML-style inline comment outside simple quoted values."""
    value = value.strip()
    if not value or value[0] in ("'", '"'):
        return value.strip('"').strip("'")
    return value.split("#", 1)[0].strip().strip('"').strip("'")


SAFE_MODULES = {"pytest", "unittest", "py_compile"}
SAFE_TOOLS = {"pytest", "ruff", "mypy"}
SAFE_NPM_SCRIPTS = {"lint", "typecheck", "type-check", "test"}
SHELL_META = ("\n", "\r", ";", "&", "|", ">", "<", "`", "$(", "${")
FORBIDDEN_TOOL_ARGS = {
    "pytest": {"--basetemp", "--rootdir", "--override-ini", "-p"},
    "ruff": {"--fix", "--unsafe-fixes"},
    "mypy": {"--install-types"},
}


def _has_executable_path(value: str) -> bool:
    """Return whether an executable token names a path instead of a command."""
    return (
        value in {".", ".."}
        or "/" in value
        or "\\" in value
        or (len(value) >= 2 and value[1] == ":")
    )


def _has_forbidden_tool_args(tool: str, args: list[str]) -> bool:
    """Reject validation options that write, install, or load arbitrary code."""
    forbidden = FORBIDDEN_TOOL_ARGS.get(tool, set())
    for arg in args:
        option = arg.split("=", 1)[0]
        if option in forbidden:
            return True
    return False


def parse_validation_command(command: str) -> Optional[list[str]]:
    """Parse a project validation command into a conservative argv list."""
    command = command.strip()
    if not command or any(token in command for token in SHELL_META):
        return None
    if "{" in command or "}" in command:
        return None
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return None
    if not argv:
        return None

    if _has_executable_path(argv[0]):
        return None
    executable = argv[0].lower()
    if executable in {"python", "python3", "py"}:
        module_index = 1
        if argv[1:3] == ["-X", "utf8"]:
            module_index = 3
        if (len(argv) <= module_index + 1
                or argv[module_index] != "-m"
                or argv[module_index + 1] not in SAFE_MODULES):
            return None
        tool = argv[module_index + 1]
        if _has_forbidden_tool_args(tool, argv[module_index + 2:]):
            return None
        argv[0] = sys.executable
    elif executable == "npm":
        if (len(argv) == 2 and argv[1] == "test"):
            return argv
        if len(argv) != 3 or argv[1] != "run" or argv[2] not in SAFE_NPM_SCRIPTS:
            return None
    elif executable not in SAFE_TOOLS:
        return None
    elif _has_forbidden_tool_args(executable, argv[1:]):
        return None
    return argv


def is_runnable_command(command: str) -> bool:
    """Return whether a parsed runbook value is a safe validation command."""
    return parse_validation_command(command) is not None


def indent_width(line: str) -> int:
    """Return leading-space indentation width."""
    return len(line) - len(line.lstrip(" "))


def extract_list_under_key(lines: list[str], key: str) -> list[str]:
    """Extract a simple scalar list under a YAML key.

    This intentionally supports only the small subset used by
    .helloagents/runbook.yaml templates, avoiding a third-party YAML
    dependency in hook execution.
    """
    commands: list[str] = []
    key_indent: Optional[int] = None
    in_block = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = indent_width(raw_line)
        if not in_block:
            if stripped == f"{key}:":
                key_indent = indent
                in_block = True
            continue

        if key_indent is not None and indent <= key_indent and not stripped.startswith("- "):
            break
        if stripped.startswith("- "):
            command = strip_inline_comment(stripped[2:])
            if is_runnable_command(command):
                commands.append(command)

    return commands


def find_block(
    lines: list[str],
    key: str,
    *,
    start: int = 0,
    end: Optional[int] = None,
    parent_indent: int = -1,
) -> Optional[tuple[int, int, int]]:
    """Find a simple YAML mapping block by key."""
    end = len(lines) if end is None else end
    for index in range(start, end):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            continue

        indent = indent_width(raw_line)
        if parent_indent >= 0 and indent <= parent_indent:
            break
        if stripped == f"{key}:":
            block_end = end
            for next_index in range(index + 1, end):
                next_line = lines[next_index]
                next_stripped = next_line.strip()
                if not next_stripped or next_stripped.startswith("#"):
                    continue
                if indent_width(next_line) <= indent:
                    block_end = next_index
                    break
            return index + 1, block_end, indent

    return None


def top_level_block(
    lines: list[str],
    key: str,
) -> Optional[tuple[int, int, int]]:
    """Find a top-level YAML mapping block by key."""
    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            continue
        if indent_width(raw_line) == 0 and stripped == f"{key}:":
            block_end = len(lines)
            for next_index in range(index + 1, len(lines)):
                next_line = lines[next_index]
                next_stripped = next_line.strip()
                if not next_stripped or next_stripped.startswith("#"):
                    continue
                if indent_width(next_line) == 0:
                    block_end = next_index
                    break
            return index + 1, block_end, 0
    return None


def extract_scalar_in_block(
    lines: list[str],
    start: int,
    end: int,
    key: str,
) -> Optional[str]:
    """Extract a scalar `key: value` from a block."""
    for raw_line in lines[start:end]:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            continue
        if stripped.startswith(f"{key}:"):
            value = stripped.split(":", 1)[1]
            return strip_inline_comment(value)
    return None


def is_truthy_yaml(value: Optional[str]) -> bool:
    """Return whether a scalar string is YAML truthy for our templates."""
    return (value or "").strip().lower() in {"true", "yes", "on", "1"}


def workflow_block(
    lines: list[str],
    workflow_name: str,
) -> Optional[tuple[int, int, int]]:
    """Find a workflow block under top-level `workflows:`."""
    workflows = top_level_block(lines, "workflows")
    if not workflows:
        return None
    start, end, workflow_parent_indent = workflows
    return find_block(
        lines,
        workflow_name,
        start=start,
        end=end,
        parent_indent=workflow_parent_indent,
    )


def extract_validation_workflow_names(lines: list[str]) -> list[str]:
    """Read validation workflow references in priority order."""
    validation = find_block(lines, "validation")
    if not validation:
        return []

    validation_start, validation_end, validation_indent = validation
    workflows = find_block(
        lines,
        "workflows",
        start=validation_start,
        end=validation_end,
        parent_indent=validation_indent,
    )
    if not workflows:
        return []

    workflows_start, workflows_end, _ = workflows
    names: list[str] = []
    for key in ("default", "latest_commit"):
        value = extract_scalar_in_block(lines, workflows_start, workflows_end, key)
        if value and value not in names:
            names.append(value)
    return names


def default_workflow_names(lines: list[str]) -> list[str]:
    """Return workflow names marked with `default: true`."""
    workflows = top_level_block(lines, "workflows")
    if not workflows:
        return []

    workflows_start, workflows_end, workflows_indent = workflows
    names: list[str] = []
    index = workflows_start
    while index < workflows_end:
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            index += 1
            continue

        indent = indent_width(raw_line)
        if indent <= workflows_indent:
            break
        if stripped.endswith(":"):
            name = stripped[:-1].strip()
            block = find_block(
                lines,
                name,
                start=index,
                end=workflows_end,
                parent_indent=workflows_indent,
            )
            if block:
                block_start, block_end, _ = block
                default_value = extract_scalar_in_block(
                    lines, block_start, block_end, "default"
                )
                if is_truthy_yaml(default_value):
                    names.append(name)
                index = block_end
                continue
        index += 1

    return names


def workflow_direct_commands(lines: list[str], workflow_name: str) -> list[str]:
    """Extract local direct commands from a workflow block."""
    block = workflow_block(lines, workflow_name)
    if not block:
        return []

    start, end, _ = block
    environment = extract_scalar_in_block(lines, start, end, "environment")
    protected = extract_scalar_in_block(lines, start, end, "protected")
    requires_confirmation = extract_scalar_in_block(
        lines, start, end, "requires_confirmation"
    )

    if environment and environment not in {"local", "localhost"}:
        return []
    if is_truthy_yaml(protected) or is_truthy_yaml(requires_confirmation):
        return []

    has_remote_action = False
    commands: list[str] = []
    current_step_is_local = True
    for raw_line in lines[start:end]:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            current_step_is_local = True
            step_body = stripped[2:].strip()
            if step_body.startswith("action:"):
                action = strip_inline_comment(step_body.split(":", 1)[1])
                current_step_is_local = action in {"local", "run"}
                if not current_step_is_local:
                    has_remote_action = True
            elif step_body.startswith("command:"):
                command = strip_inline_comment(step_body.split(":", 1)[1])
                if is_runnable_command(command):
                    commands.append(command)
            continue

        if stripped.startswith("action:"):
            action = strip_inline_comment(stripped.split(":", 1)[1])
            current_step_is_local = action in {"local", "run"}
            if not current_step_is_local:
                has_remote_action = True
            continue

        if stripped.startswith("command:") and current_step_is_local:
            command = strip_inline_comment(stripped.split(":", 1)[1])
            if is_runnable_command(command):
                commands.append(command)

    if has_remote_action:
        return []

    return commands


def load_runbook_yaml(cwd: str) -> Optional[list[str]]:
    """Read local validation commands from .helloagents/runbook.yaml."""
    runbook_file = Path(cwd) / ".helloagents" / "runbook.yaml"
    if not runbook_file.is_file():
        return None

    try:
        content = runbook_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    lines = content.splitlines()
    before_commit = extract_list_under_key(lines, "before_commit")
    if before_commit:
        return before_commit

    workflow_names = extract_validation_workflow_names(lines)
    for conventional_name in ("latest_commit_fixes",):
        if conventional_name not in workflow_names:
            workflow_names.append(conventional_name)
    for default_name in default_workflow_names(lines):
        if default_name not in workflow_names:
            workflow_names.append(default_name)
    if "local_iteration" not in workflow_names:
        workflow_names.append("local_iteration")

    for workflow_name in workflow_names:
        commands = workflow_direct_commands(lines, workflow_name)
        if commands:
            return commands

    return None
