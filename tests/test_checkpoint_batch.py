import json
import tempfile
import unittest
from pathlib import Path

from helloagents.scripts import inject_context, pre_compact, progress_snapshot
from helloagents.scripts.validate_package import validate_package


PIPELINE = {
    "mode": "checkpoint-batch",
    "batch_id": "B1",
    "checkpoint": "CP1",
    "state": "verifying",
    "task_ids": ["1.1"],
    "risk_signals": [],
    "verified_scope": [],
    "resume_scope": ["1.1"],
}


def checkpoint_tasks() -> str:
    """Return a minimal executable checkpoint-batch task list."""
    return """# 任务清单: sample

```yaml
@feature: sample
@task_complexity: complex
@execution_strategy: checkpoint-batch
@batch_policy: max3-normal-max2-risk-max1-strong-risk
@pipeline_state: optional-status-json-pipeline
```

## 任务列表

- [ ] 1.1 实现第一步
  - 预期变更: 修改一个明确文件范围
  - 完成标准: 当前行为测试通过
  - 验证方式: python -X utf8 -m unittest
  - depends_on: []
  - batch_id: B1
  - checkpoint: CP1
  - batch_verify: python -X utf8 -m unittest tests.test_checkpoint_batch
- [ ] 1.2 实现第二步
  - 预期变更: 修改下游文件范围
  - 完成标准: 下游行为测试通过
  - 验证方式: python -X utf8 -m unittest
  - depends_on: [1.1]
  - batch_id: B2
  - checkpoint: CP2
  - batch_verify: python -X utf8 -m unittest tests.test_checkpoint_batch
"""


class CheckpointContractTests(unittest.TestCase):
    def _validate_tasks(self, tasks_content: str) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir)
            (package / "proposal.md").write_text("# proposal\n", encoding="utf-8")
            (package / "tasks.md").write_text(tasks_content, encoding="utf-8")
            return validate_package(package)

    def test_complete_checkpoint_contract_is_executable(self):
        result = self._validate_tasks(checkpoint_tasks())

        self.assertTrue(result["valid"])
        self.assertTrue(result["executable"])
        self.assertTrue(result["tasks"]["checkpoint"]["enabled"])
        self.assertEqual(result["tasks"]["checkpoint"]["issues"], [])

    def test_missing_batch_verify_blocks_checkpoint_package(self):
        tasks = checkpoint_tasks().replace(
            "  - batch_verify: python -X utf8 -m unittest tests.test_checkpoint_batch\n",
            "",
        )
        result = self._validate_tasks(tasks)

        self.assertFalse(result["valid"])
        self.assertFalse(result["executable"])
        self.assertTrue(any("batch_verify" in issue for issue in result["issues"]))

    def test_standard_package_bypasses_checkpoint_fields(self):
        tasks = """# 任务清单: legacy

```yaml
@feature: legacy
@execution_strategy: standard
```

## 任务列表

- [ ] 1.1 保持旧方案包行为
  - 预期变更: 修改一个明确文件范围
  - 完成标准: 现有检查通过
  - 验证方式: python -X utf8 -m unittest
  - depends_on: []
"""
        result = self._validate_tasks(tasks)

        self.assertTrue(result["valid"])
        self.assertTrue(result["executable"])
        self.assertFalse(result["tasks"]["checkpoint"]["enabled"])

    def test_dependency_parser_rejects_unknown_and_malformed_ids(self):
        unknown = checkpoint_tasks().replace(
            "  - depends_on: [1.1]\n", "  - depends_on: [99]\n"
        )
        malformed = checkpoint_tasks().replace(
            "  - depends_on: [1.1]\n", "  - depends_on: [1.1, nope]\n"
        )

        for tasks in (unknown, malformed):
            with self.subTest(tasks=tasks):
                result = self._validate_tasks(tasks)
                self.assertFalse(result["valid"])
                self.assertTrue(
                    any("depends_on" in issue for issue in result["issues"])
                )

    def test_dependency_parser_accepts_integer_task_ids(self):
        tasks = checkpoint_tasks()
        tasks = tasks.replace("1.1 实现第一步", "1 实现第一步")
        tasks = tasks.replace("1.2 实现第二步", "2 实现第二步")
        tasks = tasks.replace("  - depends_on: [1.1]\n", "  - depends_on: [1]\n")

        result = self._validate_tasks(tasks)

        self.assertTrue(result["valid"])

    def test_valid_braced_command_is_not_a_template_placeholder(self):
        tasks = checkpoint_tasks().replace(
            "python -X utf8 -m unittest tests.test_checkpoint_batch",
            "python -c \"print({'ok': True})\"",
        )

        result = self._validate_tasks(tasks)

        self.assertTrue(result["valid"])


class PipelineStatePreservationTests(unittest.TestCase):
    def test_snapshot_hooks_preserve_existing_pipeline(self):
        stats = {
            "completed": 1,
            "failed": 0,
            "skipped": 0,
            "pending": 1,
            "uncertain": 0,
            "total": 2,
        }
        content = "- [ ] 1.1 pending task\n"

        for module in (progress_snapshot, pre_compact):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as temp_dir:
                package = Path(temp_dir)
                tasks_path = package / "tasks.md"
                tasks_path.write_text(content, encoding="utf-8")
                (package / ".status.json").write_text(
                    json.dumps({"pipeline": PIPELINE}, ensure_ascii=False),
                    encoding="utf-8",
                )

                module._write_status_json(tasks_path, stats, content)
                status = json.loads(
                    (package / ".status.json").read_text(encoding="utf-8")
                )

                self.assertEqual(status["pipeline"], PIPELINE)
                self.assertEqual(status["completed"], 1)

    def test_malformed_pipeline_is_not_preserved(self):
        stats = {
            "completed": 1,
            "failed": 0,
            "skipped": 0,
            "pending": 1,
            "uncertain": 0,
            "total": 2,
        }
        content = "- [ ] 1.1 pending task\n"

        for module in (progress_snapshot, pre_compact):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as temp_dir:
                package = Path(temp_dir)
                tasks_path = package / "tasks.md"
                tasks_path.write_text(content, encoding="utf-8")
                (package / ".status.json").write_text("[]", encoding="utf-8")

                module._write_status_json(tasks_path, stats, content)
                status = json.loads(
                    (package / ".status.json").read_text(encoding="utf-8")
                )

                self.assertNotIn("pipeline", status)

    def test_checkpoint_context_requires_complex_package_and_valid_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / ".helloagents" / "plan" / "active"
            package.mkdir(parents=True)
            (package / "proposal.md").write_text("# active\n", encoding="utf-8")
            (package / "tasks.md").write_text(
                "@task_complexity: simple\n@execution_strategy: checkpoint-batch\n",
                encoding="utf-8",
            )
            (package / ".status.json").write_text(
                json.dumps({"pipeline": PIPELINE}, ensure_ascii=False),
                encoding="utf-8",
            )

            self.assertEqual(
                inject_context._get_checkpoint_pipeline_context(temp_dir), ""
            )

            (package / "tasks.md").write_text(
                "@task_complexity: complex\n@execution_strategy: checkpoint-batch\n",
                encoding="utf-8",
            )
            (package / ".status.json").write_text("{}", encoding="utf-8")

            context = inject_context._get_checkpoint_pipeline_context(temp_dir)

            self.assertIn("compaction_state_missing", context)

    def test_long_subagent_context_keeps_checkpoint_resume_scope(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ha_dir = root / ".helloagents"
            package = ha_dir / "plan" / "active"
            package.mkdir(parents=True)
            (ha_dir / "context.md").write_text("C" * 4000, encoding="utf-8")
            (ha_dir / "guidelines.md").write_text("G" * 3000, encoding="utf-8")
            (package / "proposal.md").write_text("P" * 6000, encoding="utf-8")
            (package / "tasks.md").write_text(
                "@task_complexity: complex\n@execution_strategy: checkpoint-batch\n"
                + "T" * 1500,
                encoding="utf-8",
            )
            (package / ".status.json").write_text(
                json.dumps(
                    {"pipeline": {**PIPELINE, "resume_scope": ["resume-marker"]}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            context = inject_context.handle_subagent_start(temp_dir)
            text = context["hookSpecificOutput"]["additionalContext"]

            self.assertIn("resume_scope: resume-marker", text)
            self.assertLessEqual(
                len(text),
                15000 + len("[HelloAGENTS] 方案包上下文（自动注入）:\n"),
            )


if __name__ == "__main__":
    unittest.main()
