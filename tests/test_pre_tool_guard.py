"""Tests for the dangerous command guard."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from helloagents.scripts.pre_tool_guard import check_command, evaluate_hook_payload


class PreToolGuardTests(unittest.TestCase):
    def test_blocks_destructive_file_commands(self):
        dangerous = [
            "rm -rf /",
            "rm -rf ./important",
            "rm -rf .",
            "Remove-Item -LiteralPath 'C:/tmp/project' -Recurse -Force",
            "del /s /q build",
            "rmdir /s /q build",
            "git rm secrets.txt",
            "git clean -fdx",
            "find . -name '*.pyc' -delete",
        ]

        for command in dangerous:
            with self.subTest(command=command):
                self.assertTrue(check_command(command)[0])

    def test_blocks_embedded_destructive_python(self):
        dangerous = [
            'python -c "import shutil; shutil.rmtree(\'src\')"',
            'python3 -c "import os; os.remove(\'config.py\')"',
            'py -c "from pathlib import Path; Path(\'x\').unlink()"',
        ]

        for command in dangerous:
            with self.subTest(command=command):
                self.assertTrue(check_command(command)[0])

    def test_blocks_indirect_and_encoded_shell_execution(self):
        dangerous = [
            '$(printf rm) -rf /',
            'rm -rf "$target"',
            'git -C repo clean -fdx',
            'powershell -EncodedCommand ZABlAGwA',
            'powershell -enc ZABlAGwA',
            'pwsh -Command "& $dangerousCommand"',
            "r''m -rf target",
            'printf payload | base64 -d | sh',
            'git -C repo push -f origin main',
            'git push origin +HEAD:main',
            'helloagents uninstall codex',
            'helloagents clean',
            'helloagents update feature/security',
        ]

        for command in dangerous:
            with self.subTest(command=command):
                self.assertTrue(check_command(command)[0])

    def test_blocks_database_cache_permission_and_device_risks(self):
        dangerous = [
            "DROP TABLE users",
            "DELETE FROM users",
            "redis-cli FLUSHALL",
            "cache purge all",
            "chmod 777 /tmp/app",
            "mkfs.ext4 /dev/sdb1",
            "dd if=image.iso of=/dev/sda",
            "git push origin main --force",
            "git reset --hard upstream/main",
        ]

        for command in dangerous:
            with self.subTest(command=command):
                self.assertTrue(check_command(command)[0])

    def test_allows_non_destructive_commands(self):
        safe = [
            "git status --short",
            "python -c \"print('ok')\"",
            "DELETE FROM users WHERE id = 1",
            "chmod 755 scripts/tool.sh",
            "cache list",
            "git push origin feature/safety",
        ]

        for command in safe:
            with self.subTest(command=command):
                self.assertFalse(check_command(command)[0])

    def test_hook_payload_contract_denies_dangerous_command(self):
        result = evaluate_hook_payload({
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf target"},
        })

        self.assertEqual(result["permissionDecision"], "deny")
        self.assertIn("危险命令", result["reason"])

    def test_hook_payload_fails_closed_when_shape_is_unknown(self):
        payloads = [
            {},
            {"tool_name": "Bash", "tool_input": []},
            {"tool_name": "Bash", "tool_input": {"script": "rm -rf target"}},
        ]

        for payload in payloads:
            with self.subTest(payload=json.dumps(payload)):
                result = evaluate_hook_payload(payload)
                self.assertEqual(result["permissionDecision"], "deny")
                self.assertIn("无法安全解析", result["reason"])

    def test_hook_payload_allows_known_safe_command(self):
        result = evaluate_hook_payload({
            "tool_name": "Bash",
            "tool_input": {"command": "git status --short"},
        })

        self.assertIsNone(result)

    def test_hook_payload_accepts_camel_case_shell_contract(self):
        result = evaluate_hook_payload({
            "toolName": "run_shell_command",
            "toolInput": {"command": "rm -rf target"},
        })

        self.assertEqual(result["permissionDecision"], "deny")

    def test_guard_process_denies_with_nonzero_exit(self):
        script = Path(__file__).resolve().parents[1] / "helloagents" / "scripts" / "pre_tool_guard.py"
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf target"},
        })

        result = subprocess.run(
            [sys.executable, str(script)],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("危险命令", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
