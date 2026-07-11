#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelloAGENTS PostToolUseFailure Hook — 工具失败错误恢复建议

匹配所有工具的失败事件，根据已知错误模式注入恢复建议到 additionalContext。

输入(stdin): JSON，包含 tool_name, error 等字段
输出(stdout): JSON {hookSpecificOutput: {additionalContext}} 或空
"""

import sys
import io
import json
import re

# Windows UTF-8 编码设置
def _configure_utf8_stream(stream_name: str) -> None:
    """配置标准流，避免替换由测试框架管理的句柄。"""
    stream = getattr(sys, stream_name, None)
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
        return

    buffer = getattr(stream, "buffer", None)
    if buffer is not None:
        setattr(sys, stream_name, io.TextIOWrapper(
            buffer, encoding="utf-8", errors="replace"
        ))


if sys.platform == "win32":
    for _stream_name in ("stdout", "stderr", "stdin"):
        _configure_utf8_stream(_stream_name)


# ---------------------------------------------------------------------------
# 已知错误模式 → 恢复建议
# ---------------------------------------------------------------------------

EDIT_TOOL_RECOVERY_SUGGESTION = (
    "文件编辑工具调用失败: 先用 Read 或 Glob 确认路径和文件是否存在。"
    "新文件使用当前工具列表中的 Write 完整写入；已有文件使用 Edit，"
    "或在客户端暴露时使用 Update 做局部修改。不要用 Create 修改已有文件，"
    "也不要原样重复失败调用。"
)


ERROR_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(
        r"Error editing file|failed to edit(?:ing)? file|cannot edit file|"
        r"edit(?:ing)? file failed",
        re.IGNORECASE,
    ), EDIT_TOOL_RECOVERY_SUGGESTION),

    (re.compile(
        r"(?:\bCreate\b.*(?:already exists|edit|modify|update)|"
        r"(?:already exists|edit|modify|update).*\bCreate\b)",
        re.IGNORECASE | re.DOTALL,
    ), EDIT_TOOL_RECOVERY_SUGGESTION),

    (re.compile(r'Permission denied|EACCES', re.IGNORECASE),
     "权限错误: 检查文件/目录权限，可能需要 chmod 或以管理员权限运行。"
     "如果是 node_modules/.bin 权限问题，尝试删除 node_modules 重新安装。"),

    (re.compile(r'FileNotFoundError|ENOENT|No such file or directory', re.IGNORECASE),
     "文件未找到: 检查路径是否正确，注意大小写敏感性。"
     "使用 ls 或 Glob 确认文件存在。路径中的空格需要引号包裹。"),

    (re.compile(r'UnicodeDecodeError|UnicodeEncodeError', re.IGNORECASE),
     "编码错误: 文件可能不是 UTF-8 编码。尝试使用 encoding='utf-8' errors='replace' 参数，"
     "或先用 file 命令检测文件编码。"),

    (re.compile(r'ENOSPC|disk quota|No space left on device', re.IGNORECASE),
     "磁盘空间不足: 运行 df -h 检查磁盘使用情况，"
     "清理临时文件、node_modules、__pycache__ 等释放空间。"),

    (re.compile(r'CONFLICT|merge conflict|Merge conflict', re.IGNORECASE),
     "Git 合并冲突: 使用 git status 查看冲突文件列表，"
     "逐个编辑解决冲突标记（<<<< ==== >>>>），然后 git add 标记已解决。"),

    (re.compile(r'ModuleNotFoundError|ImportError|Cannot find module', re.IGNORECASE),
     "模块未找到: 检查依赖是否已安装。"
     "Python: pip install <package> 或检查虚拟环境。"
     "Node.js: npm install 或检查 package.json。"),

    (re.compile(r'SyntaxError|IndentationError', re.IGNORECASE),
     "语法错误: 检查最近修改的代码，注意缩进一致性（空格 vs Tab）、"
     "引号配对、括号配对。可以用 python -m py_compile <file> 定位。"),

    (re.compile(r'ETIMEDOUT|ECONNREFUSED|timeout|timed out', re.IGNORECASE),
     "网络超时/连接拒绝: 检查网络连接、代理设置、目标服务是否运行。"
     "可尝试增加超时时间或使用重试机制。"),
]


def get_suggestion(error_text: str, tool_name: str = "") -> str:
    """匹配工具失败并返回恢复建议。

    参数:
        error_text: Hook 上报的错误文本。
        tool_name: 失败工具名称，客户端在 payload 中提供时传入。

    返回:
        简短恢复建议；未知错误返回空字符串。
    """
    searchable_text = f"{tool_name}\n{error_text}"
    for pattern, suggestion in ERROR_PATTERNS:
        if pattern.search(searchable_text):
            return suggestion
    return ""


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "") or "Unknown"
    error = data.get("error", "")
    if not error:
        sys.exit(0)

    suggestion = get_suggestion(error, tool_name)
    if not suggestion:
        sys.exit(0)

    result = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": (
                f"[HelloAGENTS] {tool_name} 失败恢复建议:\n{suggestion}"
            ),
        }
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
