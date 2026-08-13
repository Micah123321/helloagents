"""Tests for Codex config helpers."""

import re
import tempfile
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    tomllib = None

from helloagents.core.codex_config import (
    _CODEX_DEVELOPER_INSTRUCTIONS,
    _configure_codex_csv_batch,
    _configure_codex_developer_instructions,
    _remove_codex_developer_instructions,
)


class CodexConfigTests(unittest.TestCase):
    def test_configure_codex_multi_agent_settings_migrates_old_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            config_path = dest_dir / "config.toml"
            config_path.write_text(
                "\n".join([
                    "[agents]",
                    "max_threads = 64",
                    "max_depth = 1",
                    'interrupt_message = "legacy"',
                    "max_concurrent_threads_per_session = 2",
                    'preserved = "agents-value"',
                    "",
                    "[agents.worker]",
                    "max_depth = 9",
                    "",
                    "[features]",
                    "enable_fanout = false",
                    'preserved = "features-value"',
                    "",
                    "[features.multi_agent_v2]",
                    "enabled = true",
                    'tool_namespace = "legacy"',
                    "max_concurrent_threads_per_session = 3",
                    'preserved = "v2-value"',
                    "",
                ]),
                encoding="utf-8",
            )

            _configure_codex_csv_batch(dest_dir)

            config = config_path.read_text(encoding="utf-8")
            self.assertNotIn("max_threads =", config.split("[agents.worker]", 1)[0])
            self.assertNotIn("max_depth = 1", config.split("[agents.worker]", 1)[0])
            self.assertNotIn("interrupt_message =", config.split("[agents.worker]", 1)[0])
            self.assertIn("max_depth = 9", config)
            self.assertNotIn("enabled =", config.split("[features.multi_agent_v2]", 1)[1])
            self.assertNotIn("tool_namespace =", config)
            self.assertIn('preserved = "agents-value"', config)
            self.assertIn('preserved = "features-value"', config)
            self.assertIn('preserved = "v2-value"', config)

            if tomllib is not None:
                parsed = tomllib.loads(config)
                self.assertEqual(parsed["agents"]["max_concurrent_threads_per_session"], 10)
                self.assertTrue(parsed["features"]["enable_fanout"])
                self.assertEqual(
                    parsed["features"]["multi_agent_v2"],
                    {
                        "hide_spawn_agent_metadata": True,
                        "expose_spawn_agent_model_overrides": False,
                        "min_wait_timeout_ms": 50000,
                        "default_wait_timeout_ms": 120000,
                        "max_wait_timeout_ms": 240000,
                        "preserved": "v2-value",
                    },
                )

    def test_configure_codex_multi_agent_settings_creates_missing_sections_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)

            _configure_codex_csv_batch(dest_dir)
            first = (dest_dir / "config.toml").read_text(encoding="utf-8")
            _configure_codex_csv_batch(dest_dir)
            second = (dest_dir / "config.toml").read_text(encoding="utf-8")

            self.assertEqual(first, second)
            self.assertIn("[agents]", first)
            self.assertIn("[features.multi_agent_v2]", first)
            self.assertIn("max_concurrent_threads_per_session = 10", first)
            self.assertIn("hide_spawn_agent_metadata = true", first)
            if tomllib is not None:
                tomllib.loads(first)

    def assert_codex_spawn_compatibility_guidance(self, text):
        self.assertIn("agent_type", text)
        self.assertIn("fork_context", text)
        self.assertIn("prompt", text)
        self.assertTrue(
            any(
                marker in text
                for marker in (
                    "自包含上下文",
                    "self-contained context",
                    "embedded context",
                )
            )
        )
        self.assertTrue(
            any(
                marker in text
                for marker in (
                    "首次不兼容 spawn",
                    "first incompatible spawn",
                    "first incompatible sub-agent spawn",
                )
            )
        )

    def test_developer_instructions_include_subagent_standing_authorization(self):
        text = _CODEX_DEVELOPER_INSTRUCTIONS

        self.assertIn("Sub-agent standing authorization", text)
        self.assertIn("explicit standing request", text)
        self.assertIn("automatic orchestration conditions are met", text)
        self.assertIn("unavailable after discovery", text)
        self.assertIn("search/discover sub-agent tools first", text)
        self.assertIn("spawn_agent or spawn_agents_on_csv", text)
        self.assert_codex_spawn_compatibility_guidance(text)
        self.assertIn("Codex reasoning effort policy", text)
        for value in ("low", "medium", "high", "xhigh", "max"):
            with self.subTest(value=value):
                self.assertIn(value, text)
        self.assertIn('"middle" to "medium"', text)
        self.assertIn("CSV batches", text)
        self.assertIn("omit it and record", text)
        self.assertIn("does not own a spawn_agent or CSV wrapper", text)
        self.assertIn("tasks.md execution logs or the acceptance report", text)

    def test_configure_writes_subagent_authorization_to_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)

            _configure_codex_developer_instructions(dest_dir)

            config = (dest_dir / "config.toml").read_text(encoding="utf-8")
            self.assertIn("developer_instructions", config)
            self.assertIn("Sub-agent standing authorization", config)
            self.assertIn("explicit standing request", config)
            self.assertIn("search/discover sub-agent tools first", config)
            self.assert_codex_spawn_compatibility_guidance(config)
            self.assertIn("Codex reasoning effort policy", config)
            self.assertIn('"middle" to "medium"', config)
            self.assertNotRegex(
                config,
                re.compile(r"reasoning_effort\s*=\s*[\"']middle[\"']"),
            )
            if tomllib is not None:
                parsed = tomllib.loads(config)
                self.assertIn("developer_instructions", parsed)

    def test_remove_restores_backed_up_user_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            config_path = dest_dir / "config.toml"
            user_value = 'developer_instructions = "keep user value"'
            config_path.write_text(user_value + '\n\n[tools]\n', encoding="utf-8")

            _configure_codex_developer_instructions(dest_dir)
            self.assertTrue(_remove_codex_developer_instructions(dest_dir))

            restored = config_path.read_text(encoding="utf-8")
            self.assertIn(user_value, restored)
            self.assertNotIn("Sub-agent standing authorization", restored)
            self.assertFalse((dest_dir / "developer_instructions.bak").exists())

    def test_remove_preserves_unmanaged_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            config_path = dest_dir / "config.toml"
            user_value = 'developer_instructions = "keep user value"'
            config_path.write_text(user_value + "\n", encoding="utf-8")

            self.assertFalse(_remove_codex_developer_instructions(dest_dir))
            self.assertEqual(config_path.read_text(encoding="utf-8"), user_value + "\n")

    def test_configure_preserves_escaped_user_instructions_for_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            config_path = dest_dir / "config.toml"
            user_value = 'developer_instructions = "say \\"hello\\" safely"'
            config_path.write_text(user_value + "\n\n[tools]\n", encoding="utf-8")

            self.assertTrue(_configure_codex_developer_instructions(dest_dir))
            self.assertTrue(_remove_codex_developer_instructions(dest_dir))

            restored = config_path.read_text(encoding="utf-8")
            self.assertIn(user_value, restored)
            if tomllib is not None:
                self.assertEqual(tomllib.loads(restored)["developer_instructions"], 'say "hello" safely')

    def test_configure_preserves_literal_user_instructions_for_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            config_path = dest_dir / "config.toml"
            user_value = "developer_instructions = 'keep literal value'"
            config_path.write_text(user_value + "\n", encoding="utf-8")

            self.assertTrue(_configure_codex_developer_instructions(dest_dir))
            self.assertTrue(_remove_codex_developer_instructions(dest_dir))

            self.assertIn(user_value, config_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
