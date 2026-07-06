"""Tests for Codex config helpers."""

import tempfile
import unittest
from pathlib import Path

from helloagents.core.codex_config import (
    _CODEX_DEVELOPER_INSTRUCTIONS,
    _configure_codex_developer_instructions,
)


class CodexConfigTests(unittest.TestCase):
    def test_developer_instructions_include_subagent_standing_authorization(self):
        text = _CODEX_DEVELOPER_INSTRUCTIONS

        self.assertIn("Sub-agent standing authorization", text)
        self.assertIn("explicit standing request", text)
        self.assertIn("automatic orchestration conditions are met", text)
        self.assertIn("unavailable after discovery", text)
        self.assertIn("search/discover sub-agent tools first", text)
        self.assertIn("spawn_agent or spawn_agents_on_csv", text)

    def test_configure_writes_subagent_authorization_to_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp)

            _configure_codex_developer_instructions(dest_dir)

            config = (dest_dir / "config.toml").read_text(encoding="utf-8")
            self.assertIn("developer_instructions", config)
            self.assertIn("Sub-agent standing authorization", config)
            self.assertIn("explicit standing request", config)
            self.assertIn("search/discover sub-agent tools first", config)


if __name__ == "__main__":
    unittest.main()
