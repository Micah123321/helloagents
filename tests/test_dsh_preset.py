"""Tests for DSH (DeepSeek Harness) preset install/uninstall/status."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helloagents.core.dsh_config import (
    _dsh_home,
    _preset_dir,
    _install_dsh,
    _uninstall_dsh,
    _show_dsh_details,
    _is_managed,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stub_template_dir(tmp: Path) -> Path:
    """Create a minimal dsh/ template directory under *tmp*/helloagents/dsh/."""
    d = tmp / "helloagents" / "dsh"
    d.mkdir(parents=True)
    (d / "agent.cordis.yml").write_text(
        "# HELLOAGENTS_ROUTER: v2 — test preset\n"
        "- id: test\n  name: '@deepseek-ai/dsh-persona'\n",
        encoding="utf-8",
    )
    (d / "preset.yml").write_text("name: Test\norder: 99\n", encoding="utf-8")
    (d / "bootstrap.md").write_text("# HelloAGENTS test\n", encoding="utf-8")
    (d / "helloagents-carrier.mjs").write_text(
        "export const name = 'test';\n",
        encoding="utf-8",
    )
    return d


def _stub_skill_md(tmp: Path) -> Path:
    """Create a stub SKILL.md at the package root."""
    skill = tmp / "SKILL.md"
    skill.write_text("name: helloagents\ndescription: test\n", encoding="utf-8")
    return skill


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class DshPresetInstallTests(unittest.TestCase):
    """Install—creates the full preset directory."""

    def test_install_creates_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            template_dir = _stub_template_dir(Path(tmp))
            skill_md = _stub_skill_md(Path(tmp))

            with mock.patch(
                "helloagents.core.dsh_config._template_dir",
                return_value=template_dir,
            ), mock.patch(
                "helloagents.core.dsh_config.get_skill_md_path",
                return_value=skill_md,
            ):
                ok = _install_dsh(dsh_home)

            self.assertTrue(ok)
            preset = _preset_dir(dsh_home)
            self.assertTrue((preset / "agent.cordis.yml").is_file())
            self.assertTrue((preset / "preset.yml").is_file())
            self.assertTrue((preset / "bootstrap.md").is_file())
            self.assertTrue((preset / "plugins" / "helloagents-carrier.mjs").is_file())
            self.assertTrue((preset / "skills" / "helloagents" / "SKILL.md").is_file())

    def test_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            template_dir = _stub_template_dir(Path(tmp))
            skill_md = _stub_skill_md(Path(tmp))

            with mock.patch(
                "helloagents.core.dsh_config._template_dir",
                return_value=template_dir,
            ), mock.patch(
                "helloagents.core.dsh_config.get_skill_md_path",
                return_value=skill_md,
            ):
                self.assertTrue(_install_dsh(dsh_home))
                # Second install should succeed without error
                self.assertTrue(_install_dsh(dsh_home))

            preset = _preset_dir(dsh_home)
            self.assertTrue((preset / "agent.cordis.yml").is_file())

    def test_install_preserves_unmanaged_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            template_dir = _stub_template_dir(Path(tmp))
            skill_md = _stub_skill_md(Path(tmp))

            # Create an unmanaged preset (no marker)
            unmanaged_preset = _preset_dir(dsh_home)
            unmanaged_preset.mkdir(parents=True)
            (unmanaged_preset / "agent.cordis.yml").write_text(
                "custom content", encoding="utf-8",
            )
            (unmanaged_preset / "user_data.txt").write_text("keep", encoding="utf-8")

            with mock.patch(
                "helloagents.core.dsh_config._template_dir",
                return_value=template_dir,
            ), mock.patch(
                "helloagents.core.dsh_config.get_skill_md_path",
                return_value=skill_md,
            ):
                ok = _install_dsh(dsh_home)

            self.assertTrue(ok)
            # The old unmanaged preset should have been backed up
            backup = unmanaged_preset.with_suffix(".bak")
            self.assertTrue(backup.is_dir())
            self.assertTrue((backup / "user_data.txt").exists())
            # New preset should be in place
            self.assertTrue((unmanaged_preset / "agent.cordis.yml").is_file())
            self.assertIn("HELLOAGENTS_ROUTER", (unmanaged_preset / "agent.cordis.yml").read_text(encoding="utf-8"))


class DshPresetUninstallTests(unittest.TestCase):
    """Uninstall—removes only managed presets."""

    def test_uninstall_removes_managed_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            template_dir = _stub_template_dir(Path(tmp))
            skill_md = _stub_skill_md(Path(tmp))

            with mock.patch(
                "helloagents.core.dsh_config._template_dir",
                return_value=template_dir,
            ), mock.patch(
                "helloagents.core.dsh_config.get_skill_md_path",
                return_value=skill_md,
            ):
                _install_dsh(dsh_home)

            removed = _uninstall_dsh(dsh_home)

            self.assertGreater(len(removed), 0)
            self.assertFalse(_preset_dir(dsh_home).exists())

    def test_uninstall_preserves_unmanaged_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            preset = _preset_dir(dsh_home)
            preset.mkdir(parents=True)
            (preset / "agent.cordis.yml").write_text("custom", encoding="utf-8")
            (preset / "user_data.txt").write_text("keep", encoding="utf-8")

            removed = _uninstall_dsh(dsh_home)

            self.assertEqual(removed, [])
            self.assertTrue(preset.exists())
            self.assertTrue((preset / "user_data.txt").exists())

    def test_uninstall_missing_dir_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            removed = _uninstall_dsh(dsh_home)
            self.assertEqual(removed, [])


class DshHomeTests(unittest.TestCase):
    """DSH_HOME environment variable resolution."""

    def test_defaults_to_dot_dsh(self):
        # Remove only DSH_HOME, keep the rest of the environment
        with mock.patch.dict(os.environ, {"DSH_HOME": ""}, clear=False):
            self.assertEqual(_dsh_home(), Path.home() / ".dsh")

    def test_env_var_override(self):
        with mock.patch.dict(os.environ, {"DSH_HOME": "C:\\custom\\dsh"}, clear=False):
            self.assertEqual(_dsh_home(), Path("C:\\custom\\dsh"))

    def test_ignores_empty_env_var(self):
        with mock.patch.dict(os.environ, {"DSH_HOME": "  "}, clear=False):
            self.assertEqual(_dsh_home(), Path.home() / ".dsh")


class DshMarkerTests(unittest.TestCase):
    """Marker detection in agent.cordis.yml."""

    def test_detects_marker_in_managed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            preset = Path(tmp)
            (preset / "agent.cordis.yml").write_text(
                "# HELLOAGENTS_ROUTER: v2 — managed\n", encoding="utf-8",
            )
            self.assertTrue(_is_managed(preset))

    def test_detects_no_marker_in_unmanaged_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            preset = Path(tmp)
            (preset / "agent.cordis.yml").write_text("custom\n", encoding="utf-8")
            self.assertFalse(_is_managed(preset))

    def test_returns_false_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(_is_managed(Path(tmp)))

    def test_returns_false_on_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            preset = Path(tmp)
            (preset / "agent.cordis.yml").write_text("", encoding="utf-8")
            self.assertFalse(_is_managed(preset))


class DshStatusTests(unittest.TestCase):
    """Status details display and completeness."""

    def test_show_details_returns_false_for_missing_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            details = _show_dsh_details(dsh_home)
            self.assertFalse(details["preset_dir"])
            for k in ("composition", "bootstrap", "carrier", "metadata", "skill"):
                self.assertFalse(details[k])

    def test_show_details_returns_true_for_installed_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            template_dir = _stub_template_dir(Path(tmp))
            skill_md = _stub_skill_md(Path(tmp))

            with mock.patch(
                "helloagents.core.dsh_config._template_dir",
                return_value=template_dir,
            ), mock.patch(
                "helloagents.core.dsh_config.get_skill_md_path",
                return_value=skill_md,
            ):
                _install_dsh(dsh_home)

            details = _show_dsh_details(dsh_home)
            self.assertTrue(details["preset_dir"])
            self.assertTrue(details["composition"])
            self.assertTrue(details["bootstrap"])
            self.assertTrue(details["carrier"])
            self.assertTrue(details["metadata"])
            self.assertTrue(details["skill"])


class DshCliTargetIntegrationTests(unittest.TestCase):
    """Verify the dsh CLI target is registered and resolves correctly."""

    def test_dsh_target_in_cli_targets(self):
        from helloagents._common import CLI_TARGETS
        self.assertIn("dsh", CLI_TARGETS)
        self.assertEqual(CLI_TARGETS["dsh"]["mode"], "preset")

    def test_cli_dir_for_dsh(self):
        from helloagents._common import cli_dir_for
        with mock.patch.dict(os.environ, {"DSH_HOME": "C:\\dsh"}, clear=False):
            self.assertEqual(cli_dir_for("dsh"), Path("C:\\dsh"))

    def test_detect_installed_detects_dsh_preset(self):
        from helloagents._common import _detect_installed_targets
        with tempfile.TemporaryDirectory() as tmp:
            dsh_home = Path(tmp) / ".dsh"
            template_dir = _stub_template_dir(Path(tmp))
            skill_md = _stub_skill_md(Path(tmp))

            with mock.patch(
                "helloagents.core.dsh_config._template_dir",
                return_value=template_dir,
            ), mock.patch(
                "helloagents.core.dsh_config.get_skill_md_path",
                return_value=skill_md,
            ), mock.patch.dict(os.environ, {"DSH_HOME": str(dsh_home)}, clear=False):
                _install_dsh(dsh_home)

            with mock.patch.dict(os.environ, {"DSH_HOME": str(dsh_home)}, clear=False):
                installed = _detect_installed_targets()
            self.assertIn("dsh", installed)


if __name__ == "__main__":
    unittest.main()