#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloAGENTS PreToolUse Guard — 危险命令安全防护

匹配工具调用中的高危命令模式，匹配时以退出码 2 阻止执行。
无匹配时 exit(0) 不输出 = 放行。

输入(stdin): JSON，包含 tool_name, tool_input 等字段
输出(stderr): 拒绝原因；无输出表示放行
"""

import sys
import io
import json
import re
import subprocess
from pathlib import Path

# Windows UTF-8 编码设置
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')


# ---------------------------------------------------------------------------
# 危险命令模式
# ---------------------------------------------------------------------------

def _danger(pattern: str, reason: str, flags: int = re.IGNORECASE) -> tuple[re.Pattern, str]:
    """Create a dangerous command pattern.

    Args:
        pattern: Regular expression matched against the shell command string.
        reason: Human-readable reason returned when the pattern matches.
        flags: Regular expression flags.

    Returns:
        A compiled pattern and its denial reason.
    """
    return re.compile(pattern, flags), reason


COMMAND_BOUNDARY = r'(?=$|[\n;&|])'

DANGEROUS_PATTERNS: list[tuple[re.Pattern, str]] = [
    _danger(
        r'\$\([^)]*\)|`[^`]+`|\b(?:powershell|pwsh)\b[^\n;&|]*'
        r'(?:-(?:EncodedCommand|enc)\b|-Command\b[^\n;&|]*[&$])',
        "动态或编码 Shell 命令无法安全审查"
    ),
    _danger(
        r"(?:\b[a-zA-Z]+(?:''|\"\")+[a-zA-Z]+\b|\b(?:eval|source)\b|"
        r"\bbase64\b)",
        "无法可靠规范化的动态 Shell 命令"
    ),
    # 文件/目录删除：Shell、PowerShell、CMD、Git、Python 常见入口
    _danger(
        rf'\brm\s+(?!--?(?:help|version)\b)[^\n;&|]*{COMMAND_BOUNDARY}',
        "Shell 文件删除命令 (rm)"
    ),
    _danger(
        rf'\b(?:Remove-Item|del|erase)\b(?!--?(?:help|version)\b)[^\n;&|]*{COMMAND_BOUNDARY}',
        "PowerShell/CMD 文件删除命令 (Remove-Item/del/erase)"
    ),
    _danger(
        rf'\b(?:rmdir|rd)\b(?!--?(?:help|version)\b)[^\n;&|]*{COMMAND_BOUNDARY}',
        "目录删除命令 (rmdir/rd)"
    ),
    _danger(
        r'\bgit\s+(?:-C\s+\S+\s+)*rm\b[^\n;&|]*',
        "Git 文件删除命令 (git rm)"
    ),
    _danger(
        r'\bgit\s+(?:-C\s+\S+\s+)*clean\b'
        r'(?=[^\n;&|]*(?:-[A-Za-z]*f[A-Za-z]*\b|--force\b))[^\n;&|]*',
        "Git 未跟踪文件清理 (git clean --force)"
    ),
    _danger(
        r'\b(?:python|python3|py)\b[\s\S]*\b(?:shutil\.rmtree|os\.(?:remove|unlink|rmdir)|(?:pathlib\.)?Path\([^)]*\)\.(?:unlink|rmdir))\s*\(',
        "Python 文件删除调用 (shutil.rmtree/os.remove/Path.unlink)",
        re.IGNORECASE | re.DOTALL
    ),
    _danger(
        r'\bfind\b[^\n;&|]*\s-delete\b',
        "find -delete 文件删除命令"
    ),
    # 强推/硬重置
    _danger(
        r'\bgit\s+(?:-C\s+\S+\s+)*push\b'
        r'(?=[^\n;&|]*(?:(?:--force|-f)\b|\+[^\s:]*:[^\s]*(?:main|master)\b))'
        r'(?=[^\n;&|]*\b(?:main|master)\b)[^\n;&|]*',
        "强制推送到主分支 (git push --force main/master)"
    ),
    _danger(
        r'\bgit\s+reset\s+--hard\s+\S+/(main|master)\b',
        "硬重置到远程主分支 (git reset --hard origin/main)"
    ),
    # 数据库删除/无条件删除
    _danger(
        r'\bDROP\s+(DATABASE|TABLE|SCHEMA)\b',
        "数据库删除操作 (DROP DATABASE/TABLE/SCHEMA)"
    ),
    _danger(
        r'\bDELETE\s+FROM\b(?:(?!\bWHERE\b|;)[\s\S])*(?:;|$)',
        "无 WHERE 条件的数据删除 (DELETE FROM)",
        re.IGNORECASE | re.DOTALL
    ),
    # 缓存清空、权限过度开放、格式化/原始设备写入
    _danger(
        r'\b(?:FLUSHALL|FLUSHDB)\b|\bcache\s+(?:purge|flush)\b',
        "缓存清空命令 (FLUSHALL/FLUSHDB/cache purge/cache flush)"
    ),
    _danger(
        r'\bchmod\s+(?:-[A-Za-z]+\s+)?777\b',
        "过度开放权限 (chmod 777)"
    ),
    _danger(
        r'\bmkfs(?:\.\w+)?\b',
        "文件系统格式化 (mkfs)"
    ),
    _danger(
        r'\bdd\s+.*\bof=/dev/',
        "原始设备写入 (dd of=/dev/)"
    ),
    _danger(
        r'\bhelloagents\s+(?:uninstall|clean|update)\b',
        "HelloAGENTS 高风险管理命令"
    ),
]


def check_command(command: str) -> tuple[bool, str]:
    """检查命令是否匹配危险模式。返回 (is_dangerous, reason)。"""
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True, reason
    return False, ""


def _deny(reason: str) -> dict[str, str]:
    """Build the hook denial response."""
    return {
        "permissionDecision": "deny",
        "reason": f"[HelloAGENTS] {reason}",
    }


def evaluate_hook_payload(data: object) -> dict[str, str] | None:
    """Evaluate a command-hook payload and fail closed on unknown shapes."""
    if not isinstance(data, dict):
        return _deny("无法安全解析 Hook 输入")

    tool_name = data.get("tool_name") or data.get("toolName")
    if tool_name not in {"Bash", "run_shell_command"}:
        return _deny("无法安全解析 Hook 工具类型")

    tool_input = data.get("tool_input") or data.get("toolInput")
    if not isinstance(tool_input, dict):
        return _deny("无法安全解析 Hook 输入")

    command = tool_input.get("command") or tool_input.get("cmd")
    if not isinstance(command, str) or not command.strip():
        return _deny("无法安全解析 Hook 命令字段")

    is_dangerous, reason = check_command(command)
    if is_dangerous:
        return _deny(f"危险命令被拦截: {reason}")
    return None


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print("[HelloAGENTS] 无法安全解析空 Hook 输入", file=sys.stderr)
            return 2
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print("[HelloAGENTS] 无法安全解析 Hook JSON", file=sys.stderr)
        return 2

    result = evaluate_hook_payload(data)
    if result:
        # 播放警告声音（非阻塞）
        sound_script = Path(__file__).parent / "sound_notify.py"
        if sound_script.exists():
            try:
                subprocess.Popen(
                    [sys.executable, str(sound_script), "warning"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass
        print(result["reason"], file=sys.stderr)
        return 2
    # 不输出 = 放行
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
