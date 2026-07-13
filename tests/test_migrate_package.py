"""Tests for HelloAGENTS package migration."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def _load_migrate_module():
    module_path = (
        Path(__file__).resolve().parent.parent
        / "helloagents"
        / "scripts"
        / "migrate_package.py"
    )
    spec = importlib.util.spec_from_file_location("migrate_package", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migrate_package = _load_migrate_module()


class MigratePackageTests(unittest.TestCase):
    def _make_package(self, root: Path, name: str, tasks: str) -> Path:
        package_path = root / ".helloagents" / "plan" / name
        package_path.mkdir(parents=True)
        (package_path / "proposal.md").write_text("# Proposal\n", encoding="utf-8")
        (package_path / "tasks.md").write_text(tasks, encoding="utf-8")
        return package_path

    def test_completed_archive_syncs_tasks_metadata_and_status_json(self):
        tasks = """# 任务清单: sample

```yaml
@feature: sample
@created: 2026-05-05
@status: in_progress
@mode: R2
```

## LIVE_STATUS

```json
{"status":"in_progress","completed":2,"failed":0,"pending":0,"total":2,"percent":100,"current":"准备归档","updated_at":"2026-05-05 23:59:00"}
```

## 任务列表

- [√] 1.1 完成实现
- [√] 1.2 完成验证
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = self._make_package(
                root,
                "202605052343_sample",
                tasks,
            )

            report = migrate_package.migrate_package(
                package_path,
                root / ".helloagents" / "archive",
                "completed",
            )

            self.assertTrue(report.success)
            self.assertFalse(package_path.exists())
            archived = (
                root
                / ".helloagents"
                / "archive"
                / "2026-05"
                / "202605052343_sample"
            )
            content = (archived / "tasks.md").read_text(encoding="utf-8")
            self.assertIn("> **@status:** completed |", content)
            self.assertIn("@status: completed", content)

            live_raw = content.split("```json", 1)[1].split("```", 1)[0]
            live_status = json.loads(live_raw)
            self.assertEqual(live_status["status"], "completed")
            self.assertEqual(live_status["completed"], 2)
            self.assertEqual(live_status["pending"], 0)
            self.assertEqual(live_status["percent"], 100)
            self.assertEqual(live_status["current"], "已归档到 archive/2026-05")

            status_json = json.loads(
                (archived / ".status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status_json["status"], "completed")
            self.assertEqual(status_json["completed"], 2)
            self.assertEqual(status_json["done"], 2)
            self.assertEqual(status_json["total"], 2)
            self.assertEqual(status_json["current"], "已归档到 archive/2026-05")

    def test_skipped_archive_inserts_yaml_status_when_missing(self):
        tasks = """# 任务清单: sample

```yaml
@feature: sample
@created: 2026-05-05
@mode: R2
```

## 任务列表

- [ ] 1.1 待执行
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = self._make_package(
                root,
                "202605052344_sample",
                tasks,
            )

            report = migrate_package.migrate_package(
                package_path,
                root / ".helloagents" / "archive",
                "skipped",
            )

            self.assertTrue(report.success)
            archived = (
                root
                / ".helloagents"
                / "archive"
                / "2026-05"
                / "202605052344_sample"
            )
            content = (archived / "tasks.md").read_text(encoding="utf-8")
            self.assertIn("> **@status:** skipped |", content)
            self.assertIn("@status: skipped", content)

            status_json = json.loads(
                (archived / ".status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status_json["status"], "skipped")
            self.assertEqual(status_json["pending"], 1)
            self.assertEqual(status_json["current"], "已跳过并归档到 archive/2026-05")

    def test_status_counts_ignore_execution_log_markers(self):
        tasks = """# 任务清单: sample

```yaml
@feature: sample
@created: 2026-05-05
@status: in_progress
@mode: R2
```

## 任务列表

- [√] 1.1 完成实现
- [ ] 1.2 待验证

## 执行日志

| 时间 | 任务 | 状态 | 备注 |
|------|------|------|------|
| 2026-05-05 23:59 | 方案设计 | [√] | 已完成 |
| 2026-05-06 00:01 | 验证 | [ ] | 待执行 |
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_path = self._make_package(
                root,
                "202605052345_sample",
                tasks,
            )

            report = migrate_package.migrate_package(
                package_path,
                root / ".helloagents" / "archive",
                "completed",
            )

            self.assertTrue(report.success)
            archived = (
                root
                / ".helloagents"
                / "archive"
                / "2026-05"
                / "202605052345_sample"
            )
            status_json = json.loads(
                (archived / ".status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status_json["completed"], 1)
            self.assertEqual(status_json["pending"], 1)
            self.assertEqual(status_json["total"], 2)


if __name__ == "__main__":
    unittest.main()
