"""Tests for settings hook failure reporting."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helloagents.core.claude_config import (
    _configure_claude_hooks,
    _configure_claude_permissions,
    _get_helloagents_permissions,
)
from helloagents.core.settings_hooks import _configure_settings_hooks


class SettingsHooksTests(unittest.TestCase):
    def test_missing_hook_definition_reports_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            with mock.patch(
                "helloagents.core.settings_hooks._load_hooks_json",
                return_value={},
            ):
                self.assertFalse(_configure_settings_hooks(dest, "missing.json"))

    def test_malformed_settings_reports_hook_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            (dest / "settings.json").write_text("not json", encoding="utf-8")

            self.assertFalse(_configure_claude_hooks(dest))

    def test_malformed_settings_reports_permission_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            (dest / "settings.json").write_text("not json", encoding="utf-8")

            self.assertFalse(_configure_claude_permissions(dest))

    def test_permissions_do_not_authorize_all_helloagents_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            permissions = _get_helloagents_permissions(Path(tmp))

        self.assertNotIn("Bash(helloagents *)", permissions)
        self.assertFalse(any("uninstall" in entry for entry in permissions))
        self.assertFalse(any("update" in entry for entry in permissions))
        self.assertIn("Bash(helloagents version *)", permissions)
        self.assertFalse(any(entry.startswith("Bash(find ") for entry in permissions))


if __name__ == "__main__":
    unittest.main()
