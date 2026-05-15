#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloAGENTS 质量验证循环脚本 (Ralph Loop)

借鉴 Trellis 的 ralph-loop.py，利用 SubagentStop hook 的 decision: "block" 能力。
当代码实现类子代理完成时，自动运行项目验证命令（lint/typecheck/test），
不通过则阻止子代理停止并反馈错误，子代理继续修复，形成自动质量闭环。

输入(stdin): JSON，包含 agent_type, stop_hook_active, cwd 等字段
输出(stdout): JSON，包含 decision 和 reason（验证失败时）
"""

import sys
import json
import subprocess
import io
from pathlib import Path
from typing import List, Optional

# Windows UTF-8 编码设置
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

# 验证命令执行超时（秒）
CMD_TIMEOUT = 60


def load_verify_yaml(cwd: str) -> Optional[List[str]]:
    """从 .helloagents/verify.yaml 读取自定义验证命令。"""
    verify_file = Path(cwd) / ".helloagents" / "verify.yaml"
    if not verify_file.is_file():
        return None

    try:
        content = verify_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    # 简易 YAML 解析：提取 commands 列表中的非注释行
    commands = []
    in_commands = False
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("commands:"):
            in_commands = True
            continue
        if in_commands:
            if stripped.startswith("- ") and not stripped.startswith("# "):
                cmd = stripped[2:].strip().strip('"').strip("'")
                if cmd and not cmd.startswith("#"):
                    commands.append(cmd)
            elif stripped and not stripped.startswith("#"):
                # 遇到非列表项非注释行，结束 commands 块
                break

    return commands if commands else None


def _strip_inline_comment(value: str) -> str:
    """Remove a YAML-style inline comment outside simple quoted values."""
    value = value.strip()
    if not value or value[0] in ("'", '"'):
        return value.strip('"').strip("'")
    return value.split("#", 1)[0].strip().strip('"').strip("'")


def _is_runnable_command(command: str) -> bool:
    """Return whether a parsed runbook value is a concrete command."""
    command = command.strip()
    if not command:
        return False
    # Template placeholders must not reach shell=True execution.
    if "{" in command and "}" in command:
        return False
    return True


def _indent_width(line: str) -> int:
    """Return leading-space indentation width."""
    return len(line) - len(line.lstrip(" "))


def _extract_list_under_key(lines: list[str], key: str) -> list[str]:
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

        indent = _indent_width(raw_line)
        if not in_block:
            if stripped == f"{key}:":
                key_indent = indent
                in_block = True
            continue

        if key_indent is not None and indent <= key_indent and not stripped.startswith("- "):
            break
        if stripped.startswith("- "):
            command = _strip_inline_comment(stripped[2:])
            if _is_runnable_command(command):
                commands.append(command)

    return commands


def load_runbook_yaml(cwd: str) -> Optional[List[str]]:
    """从 .helloagents/runbook.yaml 读取本地验证命令。"""
    runbook_file = Path(cwd) / ".helloagents" / "runbook.yaml"
    if not runbook_file.is_file():
        return None

    try:
        content = runbook_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    lines = content.splitlines()

    # 优先读取 validation.before_commit 里的直接命令列表。
    before_commit = _extract_list_under_key(lines, "before_commit")
    if before_commit:
        return before_commit

    # 降级读取 local_iteration workflow 中的 command 字段。command_ref 需要
    # project.yaml 展开，hook 脚本不做跨文件复杂解析，留给主代理规则流程处理。
    commands: list[str] = []
    in_local_iteration = False
    local_indent: Optional[int] = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = _indent_width(raw_line)
        if not in_local_iteration:
            if stripped == "local_iteration:":
                in_local_iteration = True
                local_indent = indent
            continue

        if local_indent is not None and indent <= local_indent and stripped.endswith(":"):
            break
        if stripped.startswith("command:"):
            command = _strip_inline_comment(stripped.split(":", 1)[1])
            if _is_runnable_command(command):
                commands.append(command)

    return commands if commands else None


def detect_from_package_json(cwd: str) -> List[str]:
    """从 package.json scripts 中检测 lint/typecheck/test 命令。"""
    pkg_file = Path(cwd) / "package.json"
    if not pkg_file.is_file():
        return []

    try:
        data = json.loads(pkg_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    scripts = data.get("scripts", {})
    commands = []
    for key in ("lint", "typecheck", "type-check", "test"):
        if key in scripts:
            commands.append(f"npm run {key}")
    return commands


def detect_verify_commands(cwd: str) -> List[str]:
    """按优先级检测验证命令: runbook.yaml > verify.yaml > package.json > pyproject.toml。"""
    # 优先级1: 项目运行手册
    runbook = load_runbook_yaml(cwd)
    if runbook:
        return runbook

    # 优先级2: 自定义验证配置
    custom = load_verify_yaml(cwd)
    if custom:
        return custom

    # 优先级3: package.json
    npm_cmds = detect_from_package_json(cwd)
    if npm_cmds:
        return npm_cmds

    # 优先级4: pyproject.toml
    py_cmds = detect_from_pyproject(cwd)
    if py_cmds:
        return py_cmds

    return []


def run_verification(commands: List[str], cwd: str) -> tuple:
    """
    依次执行验证命令，收集结果。

    Returns:
        (all_passed: bool, failures: list[dict])
    """
    failures = []
    for cmd in commands:
        try:
            # Security note: shell=True is intentional here. Commands come from
            # project-local config files (verify.yaml / package.json), not from
            # untrusted external input. Shell interpretation is required for
            # compound commands (e.g. "npm run lint", pipes, &&).
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                timeout=CMD_TIMEOUT,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                stdout = result.stdout or ""
                stderr = result.stderr or ""
                output = (stdout + stderr).strip()
                # 截断过长输出
                if len(output) > 1000:
                    output = output[:1000] + "\n...(已截断)"
                failures.append({"cmd": cmd, "output": output})
        except subprocess.TimeoutExpired:
            failures.append({"cmd": cmd, "output": f"超时（>{CMD_TIMEOUT}s）"})
        except OSError as e:
            failures.append({"cmd": cmd, "output": str(e)})

    return len(failures) == 0, failures


def detect_from_pyproject(cwd: str) -> List[str]:
    """从 pyproject.toml 检测常见验证命令。"""
    pyproject = Path(cwd) / "pyproject.toml"
    if not pyproject.is_file():
        return []

    try:
        content = pyproject.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    commands = []
    # 检测 ruff/flake8/mypy/pytest 配置
    if "[tool.ruff" in content:
        commands.append("ruff check .")
    if "[tool.mypy" in content:
        commands.append("mypy .")
    if "[tool.pytest" in content:
        commands.append("pytest --tb=short -q")
    return commands


def main():
    """主入口: 从 stdin 读取 SubagentStop 事件，执行质量验证循环。"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # 防无限循环: stop_hook_active=true 说明已在循环中，直接放行
    if data.get("stop_hook_active", False):
        sys.exit(0)

    # 仅对 general-purpose 类型生效（代码实现子代理）
    agent_type = data.get("agent_type", "")
    if agent_type != "general-purpose":
        sys.exit(0)

    cwd = data.get("cwd", ".")

    # 检测验证命令
    commands = detect_verify_commands(cwd)
    if not commands:
        sys.exit(0)

    # 执行验证
    all_passed, failures = run_verification(commands, cwd)

    if all_passed:
        sys.exit(0)

    # 有失败 → 阻止子代理停止，反馈错误
    details = []
    for f in failures:
        details.append(f"❌ {f['cmd']}:\n{f['output']}")
    reason = "验证未通过，请修复:\n" + "\n\n".join(details)

    result = {"decision": "block", "reason": reason}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
