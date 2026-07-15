"""Static checks for HelloAGENTS sub-agent orchestration rules."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helloagents.core.claude_rules import _split_agents_md
from helloagents.core.codex_config import _configure_codex_developer_instructions


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

    def test_auto_orchestration_requires_dispatchable_and_started_minimums(self):
        expected = {
            "AGENTS.md": [
                "最终可派发子代理数必须 ≥2",
                "实际成功启动子代理数 ≥2",
                "才可声明“已启用子代理编排”",
            ],
            "helloagents/rules/subagent-protocols.md": [
                "最终可派发子代理数 ≥2 才进入派发",
                "实际成功启动子代理数 ≥2",
                "最终可派发子代理数 <2",
            ],
        }

        for relative_path, needles in expected.items():
            with self.subTest(path=relative_path):
                text = read_text(relative_path)
                for needle in needles:
                    self.assertIn(needle, text)
                self.assertNotIn(
                    "无显式 close 能力时记录终态或能力限制证据",
                    text,
                )

    def test_single_candidate_test_group_and_tail_stay_with_main_agent(self):
        protocols = read_text("helloagents/rules/subagent-protocols.md")
        develop = read_text("helloagents/stages/develop.md")
        review = read_text("helloagents/functions/review.md")
        validatekb = read_text("helloagents/functions/validatekb.md")

        self.assertIn("不调用单个子代理", protocols)
        self.assertIn("尾批边界", protocols)
        self.assertIn("最终仅1个测试文件/测试职责 → 主代理直接设计并编写", develop)
        self.assertIn("最终分组数<2（包括去重/合并后坍缩为单组）", review)
        self.assertIn("最终分组数<2（包括去重/合并后坍缩为单组）", validatekb)
        self.assertNotIn("需要新增测试用例时自动编排（步骤8）", protocols)
        self.assertNotIn("需要新增测试用例时 → 按编排五步法调度子代理", develop)

    def test_cli_rules_gate_on_actual_starts_and_use_real_reclaim_capabilities(self):
        codex = read_text("helloagents/rules/subagent-codex.md")
        claude = read_text("helloagents/rules/subagent-claude.md")

        for text in (codex, claude):
            self.assertIn("successful_start_count≥2", text)
            self.assertIn("complex brainstormer successful_start_count≥3", text)
            self.assertIn("partial handoff", text)

        self.assertIn("wait/send_input/close 的 agent id", codex)
        self.assertIn("CSV API 无逐 worker send_input/close 通道", codex)
        self.assertIn("普通 Agent 通道无统一 close API", claude)
        self.assertIn("当前环境暴露可寻址消息能力时", claude)
        self.assertIn('SendMessage(type="shutdown_request")', claude)

    def test_complex_brainstorming_requires_three_actual_starts(self):
        design = read_text("helloagents/stages/design.md")
        protocols = read_text("helloagents/rules/subagent-protocols.md")

        self.assertIn("最终可派发 brainstormer 少于 3 个时不得派发", design)
        self.assertIn("实际成功启动 brainstormer ≥3", design)
        self.assertIn("计划 3~6 个且实际成功启动 ≥3 个子代理", protocols)
        self.assertNotIn("复杂度: complex，已启用子代理编排", design)

    def test_runtime_and_docs_propagate_orchestration_gate(self):
        expected = {
            "SKILL.md": ["at least 2 launchable", "at least 2 actually start"],
            "helloagents/core/codex_config.py": [
                "at least two launchable sub-agents",
                "actually start",
            ],
            "helloagents/scripts/inject_context.py": [
                "最终可派发数≥2",
                "实际成功启动数≥2",
            ],
            "README.md": ["至少 2 个可派发", "至少 2 个实际启动"],
            "README_EN.md": ["at least 2 launchable", "at least 2 actually start"],
        }

        for relative_path, needles in expected.items():
            with self.subTest(path=relative_path):
                text = read_text(relative_path)
                for needle in needles:
                    self.assertIn(needle, text)

        inject_context = read_text("helloagents/scripts/inject_context.py")
        self.assertNotIn("moderate/complex 任务必须编排子代理", inject_context)

    def test_design_runtime_context_includes_brainstormer_start_gate(self):
        script = ROOT / "helloagents" / "scripts" / "inject_context.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / ".helloagents" / "plan" / "active"
            package.mkdir(parents=True)
            (package / "proposal.md").write_text("# active", encoding="utf-8")
            payload = json.dumps(
                {"hookEventName": "UserPromptSubmit", "cwd": temp_dir}
            )
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(script)],
                input=payload,
                text=True,
                capture_output=True,
                encoding="utf-8",
                check=True,
            )

        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("complex 多方案构思计划3~6个 brainstormer", context)
        self.assertIn("实际成功启动≥3", context)
        self.assertIn("至少返回3个代理独立生成的可用方案才可比较", context)

    def test_tool_unavailability_is_degradation_not_candidate_filtering(self):
        paths = (
            "AGENTS.md",
            "helloagents/rules/subagent-protocols.md",
            "helloagents/stages/develop.md",
            "helloagents/functions/review.md",
            "helloagents/functions/validatekb.md",
        )
        forbidden = (
            "不可用候选",
            "不可用角色/工具后的候选数量",
            "可用性过滤",
        )

        for relative_path in paths:
            with self.subTest(path=relative_path):
                text = read_text(relative_path)
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)

        protocols = read_text("helloagents/rules/subagent-protocols.md")
        self.assertIn("能力前置", protocols)
        self.assertIn("不可用属于编排失败降级", protocols)
        self.assertIn("不参与最终可派发数计算", protocols)
        self.assertIn("最终可派发数低于场景门槛且由主代理执行 → 合规未触发", protocols)
        self.assertNotIn("未调用且未标记[降级执行] →", protocols)

        propagation = {
            "SKILL.md": "not a candidate filter",
            "README.md": "不参与候选过滤",
            "README_EN.md": "not a candidate filter",
            "helloagents/core/codex_config.py": "not a candidate filter",
        }
        for relative_path, needle in propagation.items():
            with self.subTest(propagation=relative_path):
                self.assertIn(needle, read_text(relative_path))

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir)
            _configure_codex_developer_instructions(destination)
            generated = (destination / "config.toml").read_text(encoding="utf-8")
        self.assertIn("not a candidate filter", generated)
        self.assertIn("block overlapping takeover", generated)

    def test_design_phase_one_uses_post_filter_group_counts(self):
        design = read_text("helloagents/stages/design.md")

        self.assertIn("重新计算最终扫描组数", design)
        self.assertIn("重新计算最终分析组数", design)
        self.assertIn("最终扫描组数 <2 → 主代理直接执行", design)
        self.assertIn("最终分析组数 <2 → 主代理直接执行", design)
        self.assertNotIn("子代理数=目录数", design)
        self.assertNotIn("子代理数=单元数", design)

    def test_common_rules_do_not_assume_every_cli_has_close(self):
        expected = {
            "AGENTS.md": ("必须等待可验证终态", "阻断接管"),
            "helloagents/rules/subagent-protocols.md": (
                "无法确认代理停止时",
                "阻断重叠接管",
            ),
            "SKILL.md": (
                "wait for a verifiable terminal state",
                "block overlapping takeover",
            ),
            "README.md": ("必须等待可验证终态", "阻断重叠接管"),
            "README_EN.md": (
                "wait for a verifiable terminal state",
                "block overlapping takeover",
            ),
        }

        for relative_path, needles in expected.items():
            with self.subTest(path=relative_path):
                text = read_text(relative_path)
                for needle in needles:
                    self.assertIn(needle, text)

    def test_codex_dag_layers_do_not_spawn_single_dependency_agents(self):
        codex = read_text("helloagents/rules/subagent-codex.md")

        self.assertIn("每层重新计算 final_dispatchable_count", codex)
        self.assertIn("该层 <2 时主代理执行", codex)
        self.assertNotIn("有依赖 → 逐个 spawn_agent", codex)

    def test_complex_comparison_requires_three_usable_agent_proposals(self):
        design = read_text("helloagents/stages/design.md")

        self.assertIn("方案产出门槛", design)
        self.assertIn("至少有 3 个由不同代理返回的可用方案", design)
        self.assertIn("不得从空 pending_scope 生成整套替代方案", design)
        self.assertIn("可用方案少于 3 个", design)

    def test_claude_split_preserves_orchestration_gate(self):
        split_rules = _split_agents_md(read_text("AGENTS.md"))

        self.assertIn("最终可派发子代理数必须 ≥2", split_rules["subagent.md"])
        self.assertIn("实际成功启动子代理数 ≥2", split_rules["subagent.md"])
        self.assertNotIn("最终可派发子代理数必须 ≥2", split_rules["CLAUDE.md"])

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
