"""Tests for the dangerous command guard."""

import unittest

from helloagents.scripts.pre_tool_guard import check_command


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


if __name__ == "__main__":
    unittest.main()
