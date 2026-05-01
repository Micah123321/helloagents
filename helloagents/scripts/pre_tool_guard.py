#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloAGENTS PreToolUse Guard — 危险命令安全防护

匹配工具调用中的高危命令模式，匹配时返回 deny 决策阻止执行。
无匹配时 exit(0) 不输出 = 放行。

输入(stdin): JSON，包含 tool_name, tool_input 等字段
输出(stdout): JSON {permissionDecision, reason} 或空（放行）
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
    # 文件/目录删除：Shell、PowerShell、CMD、Git、Python 常见入口
    _danger(
        rf'\brm\s+(?!--?(?:help|version)\b)(?:-[^\s]+\s+|--[^\s]+\s+)*[^\s;&|]+',
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
        r'\bgit\s+rm\b[^\n;&|]*',
        "Git 文件删除命令 (git rm)"
    ),
    _danger(
        r'\bgit\s+clean\b(?=[^\n;&|]*(?:-[A-Za-z]*f[A-Za-z]*\b|--force\b))[^\n;&|]*',
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
        r'\bgit\s+push\b(?=[^\n;&|]*(?:--force|-f)\b)(?=[^\n;&|]*\b(?:main|master)\b)[^\n;&|]*',
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
]


def check_command(command: str) -> tuple[bool, str]:
    """检查命令是否匹配危险模式。返回 (is_dangerous, reason)。"""
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True, reason
    return False, ""


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
    if not command:
        sys.exit(0)

    is_dangerous, reason = check_command(command)
    if is_dangerous:
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
        result = {
            "permissionDecision": "deny",
            "reason": f"[HelloAGENTS] 危险命令被拦截: {reason}",
        }
        print(json.dumps(result, ensure_ascii=False))
    # 不输出 = 放行


if __name__ == "__main__":
    main()
