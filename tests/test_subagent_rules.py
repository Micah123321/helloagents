"""Static checks for HelloAGENTS sub-agent orchestration rules."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPAWN_AGENT_TYPE_WITH_FORK_CONTEXT = re.compile(
    r"spawn_agent\((?=[^)]*\bagent_type\s*=)(?=[^)]*\bfork_context\s*=\s*(?:true|True))[^)]*\)"
)


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class SubagentRuleTests(unittest.TestCase):
    def test_codex_rules_require_tool_discovery_before_downgrade(self):
        codex_rules = read_text("helloagents/rules/subagent-codex.md")

        self.assertIn("工具发现前置", codex_rules)
        self.assertIn("tool_search", codex_rules)
        self.assertIn("仅凭初始工具列表未显示 spawn_agent", codex_rules)
        self.assertIn("降级证据", codex_rules)

    def test_general_subagent_rules_require_degradation_evidence(self):
        protocols = read_text("helloagents/rules/subagent-protocols.md")

        self.assertIn("授权裁决", protocols)
        self.assertIn("降级证据（CRITICAL）", protocols)
        self.assertIn("降级触发: 工具未发现 | CLI 不支持子代理", protocols)
        self.assertIn("环境前置未满足 | 实际 spawn 调用失败 | 子代理超时或失败", protocols)
        self.assertIn("无证据不得", protocols)
        self.assertIn("DEVELOP 步骤7收尾审查", protocols)
        self.assertIn("子代理降级缺少可审计证据", protocols)

        agents = read_text("AGENTS.md")
        self.assertIn("工具未发现 / CLI 不支持 / 环境前置未满足", agents)
        self.assertIn("实际 spawn 调用失败 / 子代理超时或失败", agents)

    def test_high_frequency_triggers_record_codex_degradation_evidence(self):
        expected = {
            "helloagents/functions/review.md": "G10 执行 tool_search 工具发现",
            "helloagents/functions/verify.md": "降级前必须完成 G10 工具发现",
            "helloagents/stages/develop.md": "Codex 降级证据",
        }

        for relative_path, needle in expected.items():
            with self.subTest(path=relative_path):
                self.assertIn(needle, read_text(relative_path))

    def test_runtime_entry_points_include_standing_authorization(self):
        agents = read_text("AGENTS.md")
        skill = read_text("SKILL.md")

        self.assertIn("站立授权", agents)
        self.assertIn("满足该前置", agents)
        self.assertIn("standing request", skill)
        self.assertIn("search for sub-agent tools first", skill)

    def test_lightweight_path_does_not_override_parallel_work_units(self):
        develop = read_text("helloagents/stages/develop.md")
        readme = read_text("README.md")
        readme_en = read_text("README_EN.md")

        self.assertIn("若识别出 ≥2 个独立工作单元且并行收益明确", develop)
        self.assertIn("按 R1 验收标准执行", develop)
        self.assertIn("若识别出 ≥2 个独立工作单元且并行收益明确", readme)
        self.assertIn("R1 验收标准", readme)
        self.assertIn("跳过完整交付验收", readme)
        self.assertIn("≥2 independent work units", readme_en)
        self.assertIn("R1-level acceptance criteria", readme_en)
        self.assertIn("skips full delivery acceptance", readme_en)

    def test_readme_codex_config_notes_do_not_restore_stale_multi_agent_flag(self):
        readme = read_text("README.md")
        readme_en = read_text("README_EN.md")

        for text in (readme, readme_en):
            self.assertNotIn("multi_agent = true", text)
            self.assertIn("spawn_agent", text)
            self.assertIn("enable_fanout", text)
            self.assertIn("Collab", text)

        self.assertIn("工具发现", readme)
        self.assertIn("tool discovery", readme_en)

    def test_codex_named_agent_type_defaults_to_embedded_prompt_context(self):
        codex_rules = read_text("helloagents/rules/subagent-codex.md")

        self.assertIn("agent_type", codex_rules)
        self.assertIn("默认不传 fork_context", codex_rules)
        self.assertIn("prompt 自包含上下文", codex_rules)
        self.assertIn("首次不兼容 spawn", codex_rules)

    def test_codex_agent_type_examples_do_not_combine_fork_context_true(self):
        paths = [
            "helloagents/rules/subagent-codex.md",
            "helloagents/rules/subagent-protocols.md",
            "helloagents/stages/develop.md",
        ]

        for relative_path in paths:
            with self.subTest(path=relative_path):
                text = read_text(relative_path)
                self.assertIsNone(SPAWN_AGENT_TYPE_WITH_FORK_CONTEXT.search(text))

    def test_subagent_waiting_uses_dynamic_budget_and_partial_handoff(self):
        codex_rules = read_text("helloagents/rules/subagent-codex.md")
        protocols = read_text("helloagents/rules/subagent-protocols.md")
        agents = read_text("AGENTS.md")
        develop = read_text("helloagents/stages/develop.md")
        readme = read_text("README.md")
        readme_en = read_text("README_EN.md")

        for text in (codex_rules, protocols, agents):
            self.assertIn("scope_units", text)
            self.assertIn("dependency_depth", text)
            self.assertIn("task_weight", text)
            self.assertIn("wait_budget_seconds", text)
            self.assertIn("partial handoff", text)
            self.assertIn("pending_scope", text)

        for text in (develop, readme, readme_en):
            self.assertIn("partial", text)
            self.assertIn("handoff", text)
            self.assertIn("pending_scope", text)

        self.assertIn("completed/partial/failed/ETA", develop)
        self.assertIn("completed/partial/failed/ETA", readme)
        self.assertIn("completed/partial/failed/ETA", readme_en)
        self.assertIn("CSV API 的 max_runtime_seconds 是本次调用内所有 worker 共用的单一值", protocols)
        self.assertIn("需要逐 worker 独立预算", protocols)
        self.assertIn("需要逐 worker 独立 handoff 时退回 spawn_agent", develop)

        self.assertIn("clamp(120 + 60*min(scope_units, 8)", codex_rules)
        self.assertIn("clamp(round(wait_budget_seconds*0.1), 30, 90)", codex_rules)
        self.assertNotIn("默认截止: 每个子代理自 spawn 成功起计算 300 秒", codex_rules)
        self.assertNotIn("重置剩余等待计数", codex_rules)
        self.assertIn("健康代理保留", codex_rules)
        self.assertIn("只有触发墙钟超时或无有效 handoff 的代理需要 close", codex_rules)

    def test_agent_result_schema_defines_partial_handoff(self):
        schema = json.loads(read_text("helloagents/rlm/schemas/agent_result.json"))
        handoff = schema["properties"]["handoff"]

        self.assertEqual(handoff["type"], "object")
        self.assertEqual(
            set(handoff["properties"]),
            {"completed_scope", "evidence", "pending_scope", "blockers", "next_action"},
        )
        partial_rule = schema["allOf"][0]
        self.assertEqual(
            partial_rule["if"]["properties"]["status"]["const"], "partial"
        )
        self.assertEqual(partial_rule["then"]["required"], ["handoff"])
        self.assertEqual(
            partial_rule["then"]["properties"]["handoff"]["required"],
            ["completed_scope", "evidence", "pending_scope"],
        )

    def test_readme_and_hooks_document_codex_spawn_compatibility_boundary(self):
        expected = {
            "README.md": (
                ["agent_type", "fork_context", "prompt"],
                ["兼容边界", "兼容性边界", "兼容性说明"],
            ),
            "README_EN.md": (
                ["agent_type", "fork_context", "prompt"],
                ["compatibility boundary", "compatibility notes"],
            ),
            "helloagents/hooks/hooks_reference.md": (
                ["agent_type", "fork_context", "prompt"],
                ["兼容边界", "兼容性边界"],
            ),
            "helloagents/hooks/codex_cli_hooks.toml": (
                ["agent_type", "fork_context", "prompt"],
                ["兼容边界", "兼容性边界"],
            ),
        }

        for relative_path, (needles, boundary_markers) in expected.items():
            with self.subTest(path=relative_path):
                text = read_text(relative_path)
                for needle in needles:
                    self.assertIn(needle, text)
                self.assertTrue(any(marker in text for marker in boundary_markers))


if __name__ == "__main__":
    unittest.main()
