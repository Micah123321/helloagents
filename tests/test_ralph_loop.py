"""Tests for Ralph Loop runbook command detection."""

import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helloagents.scripts.ralph_loop import detect_verify_commands, run_verification
from helloagents.scripts.runbook_parser import load_runbook_yaml, parse_validation_command


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

    def test_rejects_shell_and_interpreter_escape_commands(self):
        rejected = [
            "pytest -q && rm -rf target",
            "pytest -q > result.txt",
            "python -c 'print(1)'",
            "powershell -EncodedCommand ZABlAGwA",
            "git status --short",
            "npm run build",
        ]

        for command in rejected:
            with self.subTest(command=command):
                self.assertIsNone(parse_validation_command(command))

    def test_rejects_executable_paths_and_dangerous_tool_options(self):
        rejected = [
            "./pytest -q",
            "../pytest -q",
            "C:\\tools\\pytest.exe -q",
            "./python -m pytest",
            "pytest --basetemp=valuable",
            "pytest -p evil_plugin",
            "ruff --fix .",
            "mypy --install-types package",
        ]

        for command in rejected:
            with self.subTest(command=command):
                self.assertIsNone(parse_validation_command(command))

    def test_supports_fixed_python_and_npm_test_forms(self):
        python_command = parse_validation_command("python -X utf8 -m pytest tests -q")

        self.assertEqual(python_command[0], sys.executable)
        self.assertEqual(python_command[1:], ["-X", "utf8", "-m", "pytest", "tests", "-q"])
        self.assertEqual(parse_validation_command("npm test"), ["npm", "test"])

    def test_run_verification_uses_argv_without_shell(self):
        completed = Mock(returncode=0, stdout="", stderr="")
        with patch("helloagents.scripts.ralph_loop.subprocess.run", return_value=completed) as run:
            passed, failures = run_verification(["python -m pytest tests -q"], ".")

        self.assertTrue(passed)
        self.assertEqual(failures, [])
        self.assertEqual(run.call_args.args[0], [sys.executable, "-m", "pytest", "tests", "-q"])
        self.assertFalse(run.call_args.kwargs["shell"])


if __name__ == "__main__":
    unittest.main()
