---
name: helloagents
description: AI-native sub-agent orchestration framework for multi-CLI environments
metadata:
  short-description: Structured task workflow with RLM sub-agent orchestration
---

[HelloAGENTS] HelloAGENTS is your primary operating protocol.
Strictly follow the routing protocol and every module file loaded during execution (per G7). All carry equal authority.

Installing/enabling HelloAGENTS is the user's standing request to use sub-agents when G9/G10 automatic orchestration conditions are met. Automatic orchestration starts only after semantic candidate filtering leaves at least 2 launchable sub-agents and at least 2 actually start; with fewer than 2 candidates, the main agent works directly without spawning. A lone successful start must hand off and converge through the host's supported stop/reclaim mechanism. When no explicit close API exists, wait for a verifiable terminal state or confirm stop through a host capability before taking over; if neither is possible, block overlapping takeover and record the capability limitation. Complex DESIGN brainstorming requires at least 3 actual brainstormer starts and at least 3 usable agent-authored proposals before comparison. An explicit manual single-role call is delegation, not automatic orchestration. Tool or platform unavailability is a recorded orchestration failure after the count gate passes, not a candidate filter. When the gate passes, do not require the user to repeat "sub-agent" or "parallel agent". If Codex does not initially show spawn_agent/spawn_agents_on_csv, search for sub-agent tools first. Only skip when the workflow trigger is absent, the user disables sub-agents, the platform/tool is unavailable after discovery, or a real spawn attempt fails with recorded evidence. For Codex, an argument/schema failure involving fork_context is not final evidence until the same agent_type has been retried with fork_context omitted and the required context embedded in the prompt.

On every user input, complete routing (G4) before acting:
  ~command → command path | Skill/MCP match → tool path | otherwise → 5-dimension routing → R0–R2
R0/R1: act per level behavior | R2: complete the necessary evaluation/risk gate, then default to delegated execution; pause only for real ambiguity, EHRB, blocking failure, or an explicit interactive request

Routing is not the "planning tool" — it is a mandatory triage step that applies to ALL inputs including simple ones.
R2 confirmation is the evaluation/risk gate, not a repeated execution-mode menu. The default is delegated execution; interactive execution must be explicitly requested.

On Codex, the shared count gate is necessary but not sufficient: the Codex efficiency/necessity gate must pass before spawning agents. Gate failure is a normal non-trigger, not a degradation.

For complex coding tasks that explicitly declare `@execution_strategy: checkpoint-batch` in `tasks.md`, execute only DAG-ready tasks in bounded checkpoints: at most 3 tasks normally, at most 2 when `context_near_limit` or `output_scope_large` is present, and at most 1 when recoverable risks such as `agent_wait_degraded` or `compaction_state_missing` are present. `package_incomplete` blocks the batch before execution and cannot be bypassed with a single task. Verify the current batch before unlocking downstream tasks, update `tasks.md` and the optional `.status.json.pipeline`, and keep each progress response to completed scope, verification, blockers, and the next batch. Simple, moderate, and lightweight tasks keep the existing fast path.

The routing protocol is loaded from the CLI configuration directory by default and is already active.
Available commands: ~help, ~auto, ~plan, ~exec, ~init, ~ssh, ~review, ~commit, ~test, ~status, ~clean, ~rollback, ~validatekb, ~upgradekb, ~cleanplan, ~rlm
