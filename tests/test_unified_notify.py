"""Tests for unified notification context and hook proxies."""

import importlib.machinery
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parents[1] / "helloagents" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_script_module(name: str):
    module_path = SCRIPTS_DIR / f"{name}.py"
    loader = importlib.machinery.SourceFileLoader(name, str(module_path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


notify_context = _load_script_module("_notify_context")
unified_notify = _load_script_module("unified_notify")
notify_channels = _load_script_module("_notify_channels")
codex_notify = _load_script_module("codex_notify")


class NotifyContextTests(unittest.TestCase):
    def test_project_name_from_cwd_uses_leaf_directory(self):
        self.assertEqual(
            notify_context.project_name_from_cwd("E:/code/python/goedge"),
            "goedge",
        )

    def test_detect_g3_event_maps_status_icon(self):
        self.assertEqual(
            notify_context.detect_g3_event("✅【HelloAGENTS】- 完成：任务"),
            "complete",
        )
        self.assertEqual(
            notify_context.detect_g3_event("⚠️【HelloAGENTS】- 警告：风险"),
            "warning",
        )
        self.assertEqual(
            notify_context.detect_g3_event("🔵【HelloAGENTS】- 标准流程：确认"),
            "confirm",
        )
        self.assertIsNone(notify_context.detect_g3_event("子代理结果", default=None))

    def test_build_context_includes_project_and_task(self):
        message = "✅【HelloAGENTS】- 完成：实现登录\n\n执行结果: 已完成登录功能"
        context = notify_context.build_context("complete", message, "E:/repo/goedge")

        self.assertEqual(context.event, "complete")
        self.assertEqual(context.project, "goedge")
        self.assertIn("完成了 - goedge - 完成：实现登录", context.body)
        self.assertEqual(context.body, context.speech)

    def test_codex_payload_filters_non_tui_client(self):
        payload = json.dumps({
            "type": "agent-turn-complete",
            "client": "vscode",
            "last-assistant-message": "✅【HelloAGENTS】- 完成：测试",
        })

        self.assertIsNone(notify_context.build_context_from_codex_payload(payload))

    def test_codex_payload_builds_context_for_tui(self):
        payload = json.dumps({
            "type": "approval-requested",
            "client": "codex-tui",
            "cwd": "E:/repo/helloagents",
        })

        context = notify_context.build_context_from_codex_payload(payload)

        self.assertIsNotNone(context)
        self.assertEqual(context.event, "confirm")
        self.assertIn("helloagents", context.body)


class UnifiedNotifyDispatchTests(unittest.TestCase):
    def test_notify_respects_sound_only_mode(self):
        context = notify_context.build_context("complete", cwd="E:/repo/goedge")

        with patch.object(unified_notify, "get_notify_mode", return_value=2), \
             patch.object(unified_notify, "send_desktop") as desktop, \
             patch.object(unified_notify, "play_context_sound") as sound:
            unified_notify.notify(context)

        desktop.assert_not_called()
        sound.assert_called_once_with(context)

    def test_notify_respects_both_mode(self):
        context = notify_context.build_context("warning", cwd="E:/repo/goedge")

        with patch.object(unified_notify, "get_notify_mode", return_value=3), \
             patch.object(unified_notify, "send_desktop") as desktop, \
             patch.object(unified_notify, "play_context_sound") as sound:
            unified_notify.notify(context)

        desktop.assert_called_once_with(context.title, context.body)
        sound.assert_called_once_with(context)


class NotifyChannelTests(unittest.TestCase):
    def test_windows_toast_uses_encoded_command_for_xml(self):
        completed = type("Completed", (), {"returncode": 0})()

        with patch.object(notify_channels.sys, "platform", "win32"), \
             patch.object(notify_channels, "ICON_PATH", Path("missing-icon.png")), \
             patch.object(notify_channels, "_ensure_win_appid"), \
             patch.object(notify_channels.subprocess, "run", return_value=completed) as run, \
             patch.object(notify_channels, "bell") as bell:
            notify_channels.send_desktop("HelloAGENTS", "完成了 - helloagents - 测试")

        argv = run.call_args.args[0]
        self.assertIn("-EncodedCommand", argv)
        self.assertNotIn("<toast>", argv)
        bell.assert_not_called()

    def test_windows_toast_bells_on_nonzero_exit(self):
        failed = type("Completed", (), {"returncode": 1})()

        with patch.object(notify_channels.sys, "platform", "win32"), \
             patch.object(notify_channels, "ICON_PATH", Path("missing-icon.png")), \
             patch.object(notify_channels, "_ensure_win_appid"), \
             patch.object(notify_channels.subprocess, "run", return_value=failed), \
             patch.object(notify_channels, "bell") as bell:
            notify_channels.send_desktop("HelloAGENTS", "完成了 - helloagents - 测试")

        bell.assert_called_once()


class CodexNotifyProxyTests(unittest.TestCase):
    def test_codex_notify_delegates_payload_and_runs_update_check(self):
        payload = json.dumps({"type": "approval-requested", "client": "codex-tui"})

        with patch.object(sys, "argv", ["codex_notify.py", payload]), \
             patch.object(codex_notify, "UNIFIED_NOTIFY", SCRIPTS_DIR / "unified_notify.py"), \
             patch.object(codex_notify.subprocess, "run") as run, \
             patch.object(codex_notify.subprocess, "Popen") as popen:
            codex_notify.main()

        run.assert_called_once()
        self.assertIn("--codex-payload", run.call_args.args[0])
        self.assertIn(payload, run.call_args.args[0])
        popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
