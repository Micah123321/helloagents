"""Tests for notification defaults and global config migration."""

import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from helloagents._common import VALID_CONFIG_KEYS
from helloagents.core import installer


def _load_script_config_module():
    module_path = Path(__file__).parents[1] / "helloagents" / "scripts" / "_config.py"
    spec = importlib.util.spec_from_file_location("helloagents_script_config", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class NotifyConfigTests(unittest.TestCase):
    def test_default_notify_level_is_sound(self):
        self.assertEqual(VALID_CONFIG_KEYS["NOTIFY_LEVEL"], 2)

        script_config = _load_script_config_module()
        self.assertEqual(script_config.VALID_CONFIG_KEYS["NOTIFY_LEVEL"], 2)

        with patch.object(script_config, "read_global_config", return_value={}):
            self.assertEqual(script_config.get_notify_mode(), 2)

    def test_sync_creates_new_config_with_sound_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            config_file = config_dir / "helloagents.json"

            with patch.object(installer, "GLOBAL_CONFIG_DIR", config_dir), \
                 patch.object(installer, "GLOBAL_CONFIG_FILE", config_file), \
                 patch("sys.stdout", io.StringIO()):
                installer._sync_global_config()

            data = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(data["NOTIFY_LEVEL"], 2)

    def test_sync_migrates_untouched_old_default_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            config_file = config_dir / "helloagents.json"
            config_dir.mkdir(exist_ok=True)
            old_defaults = dict(VALID_CONFIG_KEYS)
            old_defaults["NOTIFY_LEVEL"] = 0
            config_file.write_text(
                json.dumps(old_defaults, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            with patch.object(installer, "GLOBAL_CONFIG_DIR", config_dir), \
                 patch.object(installer, "GLOBAL_CONFIG_FILE", config_file), \
                 patch("sys.stdout", io.StringIO()):
                installer._sync_global_config()

            data = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(data["NOTIFY_LEVEL"], 2)

    def test_sync_preserves_explicit_legacy_notify_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            config_file = config_dir / "helloagents.json"
            config_dir.mkdir(exist_ok=True)
            config_file.write_text(
                json.dumps({"notify_level": 0}, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch.object(installer, "GLOBAL_CONFIG_DIR", config_dir), \
                 patch.object(installer, "GLOBAL_CONFIG_FILE", config_file), \
                 patch("sys.stdout", io.StringIO()):
                installer._sync_global_config()

            data = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertNotIn("notify_level", data)
            self.assertEqual(data["NOTIFY_LEVEL"], 0)

    def test_sync_preserves_custom_notify_level_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            config_file = config_dir / "helloagents.json"
            config_dir.mkdir(exist_ok=True)
            custom_config = dict(VALID_CONFIG_KEYS)
            custom_config["NOTIFY_LEVEL"] = 0
            custom_config["UPDATE_CHECK"] = 0
            config_file.write_text(
                json.dumps(custom_config, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            with patch.object(installer, "GLOBAL_CONFIG_DIR", config_dir), \
                 patch.object(installer, "GLOBAL_CONFIG_FILE", config_file), \
                 patch("sys.stdout", io.StringIO()):
                installer._sync_global_config()

            data = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(data["NOTIFY_LEVEL"], 0)


if __name__ == "__main__":
    unittest.main()
