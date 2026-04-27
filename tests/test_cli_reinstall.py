"""Tests for the stdlib-only CLI recovery path."""

import io
import unittest
from unittest.mock import Mock, patch

from helloagents import cli


class _Result:
    def __init__(self, returncode: int):
        self.returncode = returncode


class CliReinstallTests(unittest.TestCase):
    def test_reinstall_uses_maintenance_branch_and_no_cache_by_default(self):
        run = Mock(return_value=_Result(0))

        with patch("shutil.which", return_value="uv"), \
             patch("subprocess.run", run), \
             patch("sys.stdout", io.StringIO()):
            cli._reinstall([])

        run.assert_called_once()
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:3], ["uv", "tool", "install"])
        self.assertIn("git+https://github.com/Micah123321/helloagents.git@dev/2.3.8", cmd)
        self.assertIn("--force", cmd)
        self.assertIn("--no-cache", cmd)

    def test_reinstall_preserves_explicit_branch(self):
        run = Mock(return_value=_Result(0))

        with patch("shutil.which", return_value="uv"), \
             patch("subprocess.run", run), \
             patch("sys.stdout", io.StringIO()):
            cli._reinstall(["main"])

        cmd = run.call_args.args[0]
        self.assertIn("git+https://github.com/Micah123321/helloagents.git@main", cmd)


if __name__ == "__main__":
    unittest.main()
