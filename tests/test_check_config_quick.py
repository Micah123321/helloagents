import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from helloagents.scripts import check_config_quick


class CheckConfigIntegrityTests(unittest.TestCase):
    def _write_settings(self, home: Path, cli_dir: str, settings: dict) -> None:
        config_dir = home / cli_dir
        config_dir.mkdir(parents=True)
        (config_dir / "settings.json").write_text(
            json.dumps(settings), encoding="utf-8"
        )

    def test_claude_accepts_lowercase_installed_hook_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".claude",
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": (
                                            'python "C:/Users/test/.claude/helloagents/'
                                            'scripts/check_config_quick.py" --force'
                                        ),
                                    }
                                ]
                            }
                        ]
                    }
                },
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertTrue(check_config_quick.check_config_integrity("claude"))

    def test_claude_accepts_hook_description_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".claude",
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "custom-check",
                                        "description": "HelloAGENTS config check",
                                    }
                                ]
                            }
                        ]
                    }
                },
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertTrue(check_config_quick.check_config_integrity("claude"))

    def test_claude_rejects_unrelated_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".claude",
                {"hooks": {"SessionStart": [{"hooks": [{"command": "custom-check"}]}]}},
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertFalse(check_config_quick.check_config_integrity("claude"))

    def test_claude_ignores_marker_outside_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".claude",
                {
                    "permissions": {"allow": ["Read(HelloAGENTS/**)"]},
                    "hooks": {
                        "SessionStart": [{"hooks": [{"command": "custom-check"}]}]
                    },
                },
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertFalse(check_config_quick.check_config_integrity("claude"))

    def test_claude_rejects_helloagents_in_event_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".claude",
                {"hooks": {"HelloAgentsDisabled": []}},
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertFalse(check_config_quick.check_config_integrity("claude"))

    def test_claude_rejects_unrelated_command_argument(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".claude",
                {
                    "hooks": {
                        "SessionStart": [
                            {"hooks": [{"command": "echo helloagents disabled"}]}
                        ]
                    }
                },
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertFalse(check_config_quick.check_config_integrity("claude"))

    def test_claude_rejects_script_path_in_unrelated_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".claude",
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "hooks": [
                                    {
                                        "command": (
                                            "echo helloagents/scripts/"
                                            "check_config_quick.py disabled"
                                        )
                                    }
                                ]
                            }
                        ]
                    }
                },
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertFalse(check_config_quick.check_config_integrity("claude"))

    def test_other_json_cli_accepts_lowercase_installed_hook_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self._write_settings(
                home,
                ".gemini",
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "hooks": [
                                    {
                                        "command": (
                                            'python3 "~/.gemini/helloagents/'
                                            'scripts/check.py"'
                                        )
                                    }
                                ]
                            }
                        ]
                    }
                },
            )

            with patch.object(check_config_quick.Path, "home", return_value=home):
                self.assertTrue(check_config_quick.check_config_integrity("gemini"))

    def test_import_does_not_replace_standard_streams(self) -> None:
        streams = (sys.stdin, sys.stdout, sys.stderr)

        importlib.reload(check_config_quick)

        self.assertEqual(streams, (sys.stdin, sys.stdout, sys.stderr))


if __name__ == "__main__":
    unittest.main()
