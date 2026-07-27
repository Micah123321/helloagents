"""Tests for HelloAGENTS updater helpers."""

import io
import unittest
from unittest.mock import Mock, patch

from helloagents.core import updater as up
from helloagents.core.updater import _is_windows_entrypoint_lock_error


class _Result:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class UpdaterTests(unittest.TestCase):
    def test_detects_chinese_windows_entrypoint_lock_error(self):
        text = (
            "error: Failed to install entrypoint\n"
            "Caused by: failed to copy file from "
            "C:\\Users\\x\\AppData\\Roaming\\uv\\tools\\helloagents\\"
            "Scripts\\helloagents.exe to "
            "C:\\Users\\x\\.local\\bin\\helloagents.exe: "
            "另一个程序正在使用此文件，进程无法访问。 (os error 32)"
        )

        self.assertTrue(_is_windows_entrypoint_lock_error(text))

    def test_detects_english_windows_entrypoint_lock_error(self):
        text = (
            "error: Failed to install entrypoint\n"
            "helloagents.exe cannot access the file because it is "
            "being used by another process. (os error 32)"
        )

        self.assertTrue(_is_windows_entrypoint_lock_error(text))

    def test_ignores_regular_uv_error(self):
        text = "error: Failed to resolve dependencies for helloagents"

        self.assertFalse(_is_windows_entrypoint_lock_error(text))

    def test_uv_entrypoint_lock_schedules_deferred_uv_without_pip(self):
        stderr = (
            "error: Failed to install entrypoint\n"
            "failed to copy helloagents.exe: "
            "另一个程序正在使用此文件，进程无法访问。 (os error 32)"
        )
        run = Mock(return_value=_Result(1, stderr=stderr))
        schedule = Mock(return_value=True)

        with patch.object(up, "get_version", return_value="2.3.9+m"), \
             patch.object(up, "_detect_channel", return_value="dev/2.3.8"), \
             patch.object(up, "_get_repo_url", return_value="https://github.com/Micah123321/helloagents.git"), \
             patch.object(up, "fetch_latest_version", return_value="2.3.9+m"), \
             patch.object(up, "_local_commit_id", return_value="old"), \
             patch.object(up, "_remote_commit_id", return_value="new"), \
             patch.object(up, "_detect_installed_targets", return_value=["codex"]), \
             patch.object(up, "_detect_install_method", return_value="uv"), \
             patch.object(up, "_cleanup_pip_remnants"), \
             patch.object(up, "_win_cleanup_bak"), \
             patch.object(up, "win_preemptive_unlock", return_value=None), \
             patch.object(up, "win_finish_unlock") as finish_unlock, \
             patch.object(up, "_win_deferred_pip", schedule), \
             patch.object(up.sys, "platform", "win32"), \
             patch("builtins.input", return_value="Y"), \
             patch("sys.stdout", io.StringIO()), \
             patch("subprocess.run", run):
            up.update()

        uv_calls = [call.args[0] for call in run.call_args_list if call.args[0][:3] == ["uv", "tool", "install"]]
        self.assertEqual(len(uv_calls), 1)
        uv_cmd = uv_calls[0]
        self.assertEqual(uv_cmd[:3], ["uv", "tool", "install"])
        self.assertIn("--force", uv_cmd)
        self.assertIn("--no-cache", uv_cmd)
        schedule.assert_called_once()
        self.assertEqual(schedule.call_args.args[0], uv_cmd)
        post_cmds = schedule.call_args.kwargs["post_cmds"]
        self.assertIn(["-m", "helloagents.cli", "_post_update"], [
            cmd[1:4] for cmd in post_cmds
        ])
        self.assertIn("3", post_cmds[0])
        finish_unlock.assert_called_once_with(None, False)

    def test_uv_non_lock_error_does_not_fallback_to_pip(self):
        run = Mock(return_value=_Result(1, stderr="error: failed to resolve"))

        with patch.object(up, "get_version", return_value="2.3.9+m"), \
             patch.object(up, "_detect_channel", return_value="dev/2.3.8"), \
             patch.object(up, "_get_repo_url", return_value="https://github.com/Micah123321/helloagents.git"), \
             patch.object(up, "fetch_latest_version", return_value="2.3.9+m"), \
             patch.object(up, "_local_commit_id", return_value="old"), \
             patch.object(up, "_remote_commit_id", return_value="new"), \
             patch.object(up, "_detect_installed_targets", return_value=[]), \
             patch.object(up, "_detect_install_method", return_value="uv"), \
             patch.object(up, "_cleanup_pip_remnants"), \
             patch.object(up, "_win_cleanup_bak"), \
             patch.object(up, "win_preemptive_unlock", return_value=None), \
             patch.object(up, "win_finish_unlock"), \
             patch.object(up, "_win_deferred_pip") as schedule, \
             patch.object(up.sys, "platform", "win32"), \
             patch("builtins.input", return_value="Y"), \
             patch("sys.stdout", io.StringIO()), \
             patch("subprocess.run", run):
            up.update()

        uv_calls = [call.args[0] for call in run.call_args_list if call.args[0][:3] == ["uv", "tool", "install"]]
        self.assertEqual(len(uv_calls), 1)
        schedule.assert_not_called()


if __name__ == "__main__":
    unittest.main()
