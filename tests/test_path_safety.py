"""Tests for managed recursive-delete boundaries."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helloagents.core.win_helpers import win_safe_rmtree


class PathSafetyTests(unittest.TestCase):
    def test_removes_descendant_of_managed_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "managed"
            target = root / "plugin"
            target.mkdir(parents=True)
            (target / "data.txt").write_text("managed", encoding="utf-8")

            self.assertTrue(win_safe_rmtree(target, root))
            self.assertFalse(target.exists())

    def test_preserves_managed_root_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "managed"
            root.mkdir()

            self.assertFalse(win_safe_rmtree(root, root))
            self.assertTrue(root.exists())

    def test_preserves_target_outside_managed_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "managed"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()

            self.assertFalse(win_safe_rmtree(outside, root))
            self.assertTrue(outside.exists())

    def test_preserves_link_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "managed"
            outside = base / "outside"
            link = root / "linked"
            root.mkdir()
            outside.mkdir()
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("当前环境不允许创建目录符号链接")

            self.assertFalse(win_safe_rmtree(link, root))
            self.assertTrue(outside.exists())

    def test_preserves_target_when_managed_root_is_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            outside = base / "outside"
            target = outside / "plugin"
            linked_root = base / "managed"
            target.mkdir(parents=True)
            try:
                linked_root.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("当前环境不允许创建目录符号链接")

            self.assertFalse(win_safe_rmtree(linked_root / "plugin", linked_root))
            self.assertTrue(target.exists())

    def test_preserves_target_below_intermediate_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "managed"
            outside = base / "outside"
            target = outside / "plugin"
            linked_parent = root / "linked"
            root.mkdir()
            target.mkdir(parents=True)
            try:
                linked_parent.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("当前环境不允许创建目录符号链接")

            self.assertFalse(win_safe_rmtree(linked_parent / "plugin", root))
            self.assertTrue(target.exists())

    def test_preserves_broken_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "managed"
            link = root / "broken"
            root.mkdir()
            try:
                link.symlink_to(root / "missing", target_is_directory=True)
            except OSError:
                self.skipTest("当前环境不允许创建目录符号链接")

            self.assertFalse(win_safe_rmtree(link, root))
            self.assertTrue(link.is_symlink())

    def test_preserves_link_during_old_directory_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "managed"
            target = root / "plugin"
            outside = base / "outside"
            stale_link = root / "~plugin.old.1.1"
            target.mkdir(parents=True)
            outside.mkdir()
            try:
                stale_link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("当前环境不允许创建目录符号链接")

            with mock.patch("helloagents.core.win_helpers.shutil.rmtree") as remove:
                remove.side_effect = lambda path: Path(path).rmdir()
                self.assertTrue(win_safe_rmtree(target, root))
                removed = {Path(call.args[0]) for call in remove.call_args_list}

            self.assertNotIn(stale_link, removed)
            self.assertTrue(outside.exists())

    def test_does_not_delete_old_directory_by_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "managed"
            target = root / "plugin"
            user_backup = root / "~plugin.old.personal-backup"
            target.mkdir(parents=True)
            user_backup.mkdir()

            self.assertTrue(win_safe_rmtree(target, root))
            self.assertTrue(user_backup.exists())


if __name__ == "__main__":
    unittest.main()
