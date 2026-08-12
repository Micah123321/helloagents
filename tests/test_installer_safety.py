"""Tests for installer and uninstaller ownership boundaries."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helloagents.core import installer
from helloagents.core.uninstaller import _remove_agent_files


class InstallerSafetyTests(unittest.TestCase):
    def test_deploy_agent_preserves_conflicting_user_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = base / "package"
            source_agents = package / "agents"
            dest = base / "claude"
            installed_agents = dest / "agents"
            source_agents.mkdir(parents=True)
            installed_agents.mkdir(parents=True)
            (source_agents / "ha-reviewer.md").write_text("managed", encoding="utf-8")
            user_agent = installed_agents / "ha-reviewer.md"
            user_agent.write_text("user", encoding="utf-8")

            with mock.patch.object(
                installer, "get_helloagents_module_path", return_value=package
            ):
                self.assertFalse(installer._deploy_agent_files(dest))

            self.assertEqual(user_agent.read_text(encoding="utf-8"), "user")

    def test_installer_propagates_hook_configuration_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            module = base / "package" / "helloagents"
            module.mkdir(parents=True)
            agents_md = base / "package" / "AGENTS.md"
            skill_md = base / "package" / "SKILL.md"
            agents_md.write_text("<!-- HELLOAGENTS_ROUTER: v2 -->", encoding="utf-8")
            skill_md.write_text("skill", encoding="utf-8")

            with mock.patch.object(installer.Path, "home", return_value=base), \
                 mock.patch.object(installer, "get_agents_md_path", return_value=agents_md), \
                 mock.patch.object(installer, "get_skill_md_path", return_value=skill_md), \
                 mock.patch.object(installer, "get_helloagents_module_path", return_value=module), \
                 mock.patch.object(installer, "_deploy_claude_rules", return_value=1), \
                 mock.patch.object(installer, "_deploy_agent_files"), \
                 mock.patch.object(installer, "_sync_global_config"), \
                 mock.patch.object(installer, "_configure_claude_hooks", return_value=False), \
                 mock.patch.object(installer, "_configure_claude_permissions", return_value=True), \
                 mock.patch.object(installer, "_configure_claude_auto_memory", return_value=True):
                self.assertFalse(installer.install("claude"))

    def test_uninstall_removes_only_unchanged_managed_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = base / "package"
            source_agents = package / "agents"
            dest = base / "claude"
            installed_agents = dest / "agents"
            source_agents.mkdir(parents=True)
            installed_agents.mkdir(parents=True)
            (source_agents / "ha-reviewer.md").write_text("managed", encoding="utf-8")
            (installed_agents / "ha-reviewer.md").write_text("managed", encoding="utf-8")
            (installed_agents / "ha-custom.md").write_text("user", encoding="utf-8")

            with mock.patch(
                "helloagents.core.uninstaller.get_helloagents_module_path",
                return_value=package,
            ):
                removed = _remove_agent_files(dest)

            self.assertEqual(removed, [str(installed_agents / "ha-reviewer.md")])
            self.assertFalse((installed_agents / "ha-reviewer.md").exists())
            self.assertTrue((installed_agents / "ha-custom.md").exists())

    def test_uninstall_preserves_modified_managed_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = base / "package"
            source_agents = package / "agents"
            dest = base / "claude"
            installed_agents = dest / "agents"
            source_agents.mkdir(parents=True)
            installed_agents.mkdir(parents=True)
            (source_agents / "ha-reviewer.md").write_text("managed", encoding="utf-8")
            installed = installed_agents / "ha-reviewer.md"
            installed.write_text("user modified", encoding="utf-8")

            with mock.patch(
                "helloagents.core.uninstaller.get_helloagents_module_path",
                return_value=package,
            ):
                removed = _remove_agent_files(dest)

            self.assertEqual(removed, [])
            self.assertEqual(installed.read_text(encoding="utf-8"), "user modified")


if __name__ == "__main__":
    unittest.main()
