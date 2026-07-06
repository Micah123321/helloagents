"""Static checks for HelloAGENTS sub-agent orchestration rules."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
