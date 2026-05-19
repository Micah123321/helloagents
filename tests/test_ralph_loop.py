"""Tests for Ralph Loop runbook command detection."""

import tempfile
import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helloagents.scripts.ralph_loop import detect_verify_commands
from helloagents.scripts.runbook_parser import load_runbook_yaml


class RalphLoopRunbookTests(unittest.TestCase):
    def _write_runbook(self, root: Path, content: str) -> None:
        config_dir = root / ".helloagents"
        config_dir.mkdir()
        (config_dir / "runbook.yaml").write_text(content, encoding="utf-8")

    def test_validation_before_commit_keeps_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_runbook(
                root,
                """
validation:
  before_commit:
    - "python -m pytest tests/test_fast.py"

workflows:
  local_iteration:
    environment: local
    steps:
      - name: test
        command: "python -m pytest tests/test_slow.py"
""",
            )

            self.assertEqual(
                load_runbook_yaml(str(root)),
                ["python -m pytest tests/test_fast.py"],
            )

    def test_validation_default_workflow_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_runbook(
                root,
                """
validation:
  before_commit: []
  workflows:
    default: quick_checks

workflows:
  quick_checks:
    environment: local
    steps:
      - name: lint
        command: "python -m py_compile helloagents/cli.py"
      - name: test
        command: "python -m pytest tests/test_ralph_loop.py"
""",
            )

            self.assertEqual(
                detect_verify_commands(str(root)),
                [
                    "python -m py_compile helloagents/cli.py",
                    "python -m pytest tests/test_ralph_loop.py",
                ],
            )

    def test_latest_commit_fixes_workflow_is_conventional_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_runbook(
                root,
                """
validation:
  before_commit: []

workflows:
  latest_commit_fixes:
    default: true
    environment: local
    steps:
      - name: related_tests
        command: "python -m pytest tests/test_ralph_loop.py -q"
      - name: templated_command
        command: "python -m pytest {changed_tests}"
      - name: command_ref_only
        command_ref: commands.local.test
""",
            )

            self.assertEqual(
                load_runbook_yaml(str(root)),
                ["python -m pytest tests/test_ralph_loop.py -q"],
            )

    def test_remote_or_protected_workflows_are_not_auto_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_runbook(
                root,
                """
validation:
  before_commit: []
  workflows:
    default: deploy_production

workflows:
  deploy_production:
    environment: production
    protected: true
    requires_confirmation: true
    steps:
      - name: connect
        action: ssh
        host_ref: prod_server
      - name: deploy
        command: "git pull && ./deploy.sh"

  local_iteration:
    environment: local
    steps:
      - name: test
        command: "python -m pytest tests/test_ralph_loop.py"
""",
            )

            self.assertEqual(
                load_runbook_yaml(str(root)),
                ["python -m pytest tests/test_ralph_loop.py"],
            )

    def test_workflow_with_remote_action_is_not_partially_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_runbook(
                root,
                """
validation:
  before_commit: []
  workflows:
    default: mixed_remote

workflows:
  mixed_remote:
    steps:
      - name: connect
        action: ssh
        host_ref: test_server
      - name: deploy
        command: "git pull && ./deploy.sh"

  local_iteration:
    environment: local
    steps:
      - name: test
        command: "python -m pytest tests/test_ralph_loop.py"
""",
            )

            self.assertEqual(
                load_runbook_yaml(str(root)),
                ["python -m pytest tests/test_ralph_loop.py"],
            )


if __name__ == "__main__":
    unittest.main()
