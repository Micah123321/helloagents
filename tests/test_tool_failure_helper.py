"""Regression tests for Claude Code tool failure recovery guidance."""

import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from helloagents.scripts import tool_failure_helper


class ToolFailureHelperTests(unittest.TestCase):
    def test_edit_failure_suggests_the_real_file_tools(self):
        suggestion = tool_failure_helper.get_suggestion(
            "Error editing file",
            "Create",
        )

        self.assertIn("Write", suggestion)
        self.assertIn("Edit", suggestion)
        self.assertIn("Update", suggestion)
        self.assertIn("不要用 Create", suggestion)

    def test_hook_emits_context_for_create_edit_failure(self):
        payload = {
            "tool_name": "Create",
            "error": "Error editing file",
        }
        output = io.StringIO()

        with patch.object(tool_failure_helper.sys, "stdin", io.StringIO(json.dumps(payload))), \
             patch.object(tool_failure_helper.sys, "stdout", output):
            tool_failure_helper.main()

        result = json.loads(output.getvalue())
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Create", context)
        self.assertIn("Write", context)
        self.assertIn("不要用 Create", context)

    def test_unknown_error_remains_silent(self):
        output = io.StringIO()

        with patch.object(tool_failure_helper.sys, "stdin", io.StringIO(
                json.dumps({"tool_name": "Create", "error": "unknown failure"})
        )), patch.object(tool_failure_helper.sys, "stdout", output):
            with self.assertRaises(SystemExit) as raised:
                tool_failure_helper.main()

        self.assertEqual(0, raised.exception.code)
        self.assertEqual("", output.getvalue())

    def test_claude_rules_document_tool_boundary(self):
        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        hooks = Path("helloagents/hooks/claude_code_hooks.json").read_text(
            encoding="utf-8"
        )

        self.assertIn("新建文件: 使用当前工具列表中的 Write", agents)
        self.assertIn("Create 不是本项目约定的文件写入/编辑工具", agents)
        self.assertIn("Write|Edit|Update|NotebookEdit", hooks)


if __name__ == "__main__":
    unittest.main()
