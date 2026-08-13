"""Tests for Codex agent role configuration."""

import tempfile
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    tomllib = None

from helloagents.core.codex_roles import (
    _DEFAULT_AGENT_CONFIG,
    _configure_codex_agent_roles,
    _remove_codex_agent_roles,
)


class CodexRoleTests(unittest.TestCase):
    def test_configure_writes_readonly_role_configs(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)

            _configure_codex_agent_roles(dest_dir)

            config = (dest_dir / "config.toml").read_text(encoding="utf-8")
            self.assertIn('[agents.reviewer]', config)
            self.assertIn('config_file = "agents/helloagents-readonly-reviewer.toml"', config)
            self.assertIn('[agents.brainstormer]', config)
            self.assertIn('config_file = "agents/helloagents-readonly-brainstormer.toml"', config)
            self.assertNotIn("reasoning_effort", config)
            self.assertNotIn("model_reasoning_effort", config)

            worker_section = config.split("[agents.worker]", 1)[1].split("[agents.monitor]", 1)[0]
            self.assertNotIn("config_file", worker_section)

            role_config = dest_dir / "agents" / "helloagents-readonly-reviewer.toml"
            self.assertTrue(role_config.exists())
            content = role_config.read_text(encoding="utf-8")
            self.assertIn('sandbox_mode = "read-only"', content)
            self.assertIn("Do not create, edit, move, rename, or delete files.", content)
            if tomllib is not None:
                parsed = tomllib.loads(content)
                self.assertEqual(parsed["sandbox_mode"], "read-only")

    def test_configure_writes_and_replaces_managed_default_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            default_path = dest_dir / "agents" / "default.toml"
            default_path.parent.mkdir(parents=True)
            default_path.write_text('model = "user-model"\n', encoding="utf-8")

            _configure_codex_agent_roles(dest_dir)
            first = default_path.read_text(encoding="utf-8")
            _configure_codex_agent_roles(dest_dir)
            second = default_path.read_text(encoding="utf-8")

            self.assertEqual(first, _DEFAULT_AGENT_CONFIG)
            self.assertEqual(second, _DEFAULT_AGENT_CONFIG)
            self.assertIn('description = "One-shot read-only scout locked to gpt-5.6-luna with medium reasoning."', first)
            self.assertIn('model = "gpt-5.6-luna"', first)
            self.assertIn('model_reasoning_effort = "medium"', first)
            self.assertIn("只做探索、检索、核验", first)
            self.assertIn("[features]", first)
            if tomllib is not None:
                parsed = tomllib.loads(first)
                self.assertEqual(parsed["name"], "default")
                self.assertEqual(parsed["model"], "gpt-5.6-luna")
                self.assertEqual(parsed["model_reasoning_effort"], "medium")
                self.assertFalse(parsed["features"]["image_generation"])

    def test_configure_does_not_write_fork_context_to_codex_role_configs(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)

            _configure_codex_agent_roles(dest_dir)

            config = (dest_dir / "config.toml").read_text(encoding="utf-8")
            self.assertNotIn("fork_context", config)

            role_configs = sorted((dest_dir / "agents").glob("helloagents-readonly-*.toml"))
            self.assertTrue(role_configs)
            for role_config in role_configs:
                with self.subTest(path=role_config.name):
                    content = role_config.read_text(encoding="utf-8")
                    self.assertNotIn("fork_context", content)
                    self.assertNotIn("reasoning_effort", content)
                    if tomllib is not None:
                        tomllib.loads(content)

    def test_configure_updates_existing_role_and_preserves_user_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            (dest_dir / "config.toml").write_text(
                "\n".join([
                    "[agents.reviewer]",
                    'description = "old"',
                    'nickname_candidates = ["Old"]',
                    'model = "gpt-custom"',
                    "",
                    "[agents.custom]",
                    'description = "user role"',
                    "",
                ]),
                encoding="utf-8",
            )

            _configure_codex_agent_roles(dest_dir)

            config = (dest_dir / "config.toml").read_text(encoding="utf-8")
            reviewer_section = config.split("[agents.reviewer]", 1)[1].split("[agents.custom]", 1)[0]
            self.assertIn('description = "Code review and quality inspection"', reviewer_section)
            self.assertIn('nickname_candidates = ["Inspector", "Sentinel", "Auditor"]', reviewer_section)
            self.assertIn('config_file = "agents/helloagents-readonly-reviewer.toml"', reviewer_section)
            self.assertIn('model = "gpt-custom"', reviewer_section)
            self.assertIn("[agents.custom]", config)

    def test_remove_cleans_managed_role_configs_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)
            _configure_codex_agent_roles(dest_dir)
            custom = dest_dir / "agents" / "custom.toml"
            custom.write_text("sandbox_mode = \"workspace-write\"\n", encoding="utf-8")

            removed = _remove_codex_agent_roles(dest_dir)

            self.assertTrue(removed)
            config = (dest_dir / "config.toml").read_text(encoding="utf-8")
            self.assertNotIn("[agents.reviewer]", config)
            self.assertFalse((dest_dir / "agents" / "helloagents-readonly-reviewer.toml").exists())
            self.assertTrue(custom.exists())


if __name__ == "__main__":
    unittest.main()
