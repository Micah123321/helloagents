"""Tests for the stdlib-only CLI recovery path."""

import io
import unittest
from unittest.mock import Mock, patch

from helloagents import cli


class _Result:
    def __init__(self, returncode: int, stdout: str = ""):
        self.returncode = returncode
        self.stdout = stdout


class CliReinstallTests(unittest.TestCase):
    def test_reinstall_uses_maintenance_branch_and_no_cache_by_default(self):
        commit = "a" * 40
        run = Mock(side_effect=[_Result(0, f"{commit}\trefs/heads/dev/2.3.8\n"), _Result(0)])

        with patch("shutil.which", return_value="uv"), \
             patch("subprocess.run", run), \
             patch("sys.prefix", "/usr"), \
             patch("sys.base_prefix", "/usr"), \
             patch("sys.stdout", io.StringIO()):
            cli._reinstall([])

        self.assertEqual(run.call_count, 2)
        cmd = run.call_args_list[1].args[0]
        self.assertEqual(cmd[:3], ["uv", "tool", "install"])
        self.assertIn(f"git+https://github.com/Micah123321/helloagents.git@{commit}", cmd)
        self.assertIn("--force", cmd)
        self.assertIn("--no-cache", cmd)

    def test_reinstall_preserves_explicit_branch(self):
        commit = "b" * 40
        run = Mock(side_effect=[_Result(0, f"{commit}\trefs/heads/main\n"), _Result(0)])

        with patch("shutil.which", return_value="uv"), \
             patch("subprocess.run", run), \
             patch("sys.prefix", "/usr"), \
             patch("sys.base_prefix", "/usr"), \
             patch("sys.stdout", io.StringIO()):
            cli._reinstall(["main"])

        self.assertEqual(run.call_args_list[0].args[0][-1], "refs/heads/main")
        cmd = run.call_args_list[1].args[0]
        self.assertIn(f"git+https://github.com/Micah123321/helloagents.git@{commit}", cmd)

    def test_reinstall_aborts_when_remote_commit_cannot_be_pinned(self):
        run = Mock(return_value=_Result(0, "not-a-commit\trefs/heads/main\n"))

        with patch("shutil.which", return_value="uv"), \
             patch("subprocess.run", run), \
             patch("sys.prefix", "/usr"), \
             patch("sys.base_prefix", "/usr"), \
             patch("sys.stdout", io.StringIO()), \
             self.assertRaises(SystemExit):
            cli._reinstall(["main"])

        self.assertEqual(run.call_count, 1)

    def test_reinstall_uses_uv_pip_inside_venv(self):
        commit = "c" * 40
        run = Mock(side_effect=[_Result(0, f"{commit}\trefs/heads/dev/2.3.8\n"), _Result(0)])

        with patch("shutil.which", return_value="uv"), \
             patch("subprocess.run", run), \
             patch("sys.prefix", "/venv"), \
             patch("sys.base_prefix", "/usr"), \
             patch("sys.stdout", io.StringIO()):
            cli._reinstall([])

        self.assertEqual(run.call_count, 2)
        cmd = run.call_args_list[1].args[0]
        self.assertEqual(cmd[:3], ["uv", "pip", "install"])
        self.assertIn("--upgrade", cmd)
        self.assertIn("--force-reinstall", cmd)
        self.assertIn("--no-cache-dir", cmd)


if __name__ == "__main__":
    unittest.main()
