<div align="center">
  <img src="./readme_images/01-hero-banner.svg" alt="HelloAGENTS" width="800">
</div>

# HelloAGENTS

<div align="center">

**Let AI go beyond analysis — keep pushing until implementation and verification are done.**

[![Version](https://img.shields.io/badge/version-2.4.1-orange.svg)](./pyproject.toml)
[![npm](https://img.shields.io/npm/v/helloagents.svg)](https://www.npmjs.com/package/helloagents)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB.svg)](./pyproject.toml)
[![Commands](https://img.shields.io/badge/commands-22-6366f1.svg)](./helloagents/functions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)

</div>

<p align="center">
  <a href="./README.md"><img src="https://img.shields.io/badge/简体中文-blue?style=for-the-badge" alt="简体中文"></a>
  <a href="./README_EN.md"><img src="https://img.shields.io/badge/English-blue?style=for-the-badge" alt="English"></a>
</p>

---

> [!IMPORTANT]
> **Looking for the old version of HelloAGENTS?** The legacy codebase has been moved to a separate archive repository: [helloagents-archive](https://github.com/hellowind777/helloagents-archive)

## Table of Contents

- [Before and After](#before-and-after)
- [Core Features](#core-features)
  - [Sub-Agent Native Mapping](#sub-agent-native-mapping)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [In-Chat Workflow Commands](#in-chat-workflow-commands)
- [Usage Guide](#usage-guide)
- [Repository Guide](#repository-guide)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)
- [Version History](#version-history)
- [Contributing](#contributing)
- [License](#license)
- [Next Steps](#next-steps)

## Before and After

<table>
<tr>
<td width="50%" valign="top" align="center">

**Without HelloAGENTS**

<img src="./readme_images/08-demo-snake-without-helloagents.png" alt="Snake demo without HelloAGENTS" width="520">

</td>
<td width="50%" valign="top" align="center">

**With HelloAGENTS**

<img src="./readme_images/07-demo-snake-with-helloagents.png" alt="Snake demo with HelloAGENTS" width="520">

</td>
</tr>
</table>

| Challenge | Without HelloAGENTS | With HelloAGENTS |
|-----------|-------------------|-----------------|
| Stops at planning | Ends with suggestions | Pushes to implementation and validation |
| Output drift | Different structure every prompt | Unified routing and stage chain |
| Risky operations | Easier to make destructive mistakes | EHRB risk detection and escalation |
| Knowledge continuity | Context gets scattered | Built-in KB and session memory |
| Reusability | Prompt-by-prompt effort | Commandized reusable workflow |

## Core Features

<table>
<tr>
<td width="50%" valign="top">
<img src="./readme_images/02-feature-icon-installer.svg" width="48" align="left">

**RLM Sub-Agent Orchestration**

3 specialized roles (reviewer / writer / brainstormer) plus host CLI native sub-agents (explore / code / brainstorm) are dispatched automatically based on task complexity. Tasks are scheduled via DAG dependency analysis with topological sort and layer-by-layer parallel dispatch. Supports cross-CLI parallel scheduling and Agent Teams collaboration.

**Your gain:** complex tasks are broken down and handled by the right specialist, with parallel execution when possible.
</td>
<td width="50%" valign="top">
<img src="./readme_images/03-feature-icon-workflow.svg" width="48" align="left">

**Structured Workflow (Evaluate → Design → Develop)**

Every input is scored on five dimensions and routed to R0 direct response, R1 fast flow, or R2 standard flow. R2 enters the full stage chain with explicit entry conditions, deliverables, and verification gates. Supports interactive and fully delegated modes.

**Your gain:** proportional effort — simple queries stay fast, complex tasks get full process with verification at every step.
</td>
</tr>
<tr>
<td width="50%" valign="top">
<img src="./readme_images/04-feature-icon-safety.svg" width="48" align="left">

**Three-Layer Safety Detection (EHRB)**

Keyword scan, semantic analysis, and tool-output inspection identify destructive operations before execution. CLIs with PreToolUse support block typical dangerous commands through hooks; Codex CLI currently has no pre-execution dangerous-command hook and relies on routing confirmation, approval propagation, and read-only role configs.

**Your gain:** safer defaults with zero-config protection.
</td>
<td width="50%" valign="top">
<img src="./readme_images/05-feature-icon-compat.svg" width="48" align="left">

**Project Knowledge Base**

L1 project knowledge base (structured docs synced from code), context survives across sessions.

**Your gain:** project context persists across sessions — no need to re-explain.
</td>
</tr>
<tr>
<td width="50%" valign="top">
<img src="./readme_images/02-feature-icon-installer.svg" width="48" align="left">

**Extensibility & Customization**

Unified notifications with project and task context, user-defined tool orchestration (sub-agents, skills, MCP servers, plugins), and flexible configuration options. All features work across 6 CLI targets with graceful degradation.

**Your gain:** tailor the workflow to your team's needs without forking the codebase.
</td>
<td width="50%" valign="top">
<img src="./readme_images/03-feature-icon-workflow.svg" width="48" align="left">

**Multi-CLI Support**

One rule set works across Claude Code, Codex CLI, OpenCode, Gemini CLI, Qwen CLI, and Grok CLI (Experimental/Community). Automatic feature detection and graceful degradation ensure consistent experience regardless of CLI capabilities.

**Your gain:** switch between CLIs without relearning workflows or reconfiguring rules.
</td>
</tr>
</table>

### Sub-Agent Native Mapping

| CLI | Native Sub-Agent Mechanism | RLM Mapping |
|-----|---------------------------|-------------|
| Claude Code | Agent tool (explore / code / shell) | Direct mapping, supports Agent Teams |
| Codex CLI | spawn_agent / Collab (multi-thread) | spawn_agent parallel scheduling, CSV batch orchestration |
| OpenCode | Task tool (build / plan / general / explore) | Direct sub-agent mapping |
| Gemini CLI | Built-in tool calls | Fallback to sequential execution |
| Qwen CLI | Built-in tool calls | Fallback to sequential execution |
| Grok CLI (Experimental) | Built-in tool calls | Fallback to sequential execution |

Additionally, HelloAGENTS provides: **five-dimension routing scoring** (action need, target clarity, decision scope, impact range, EHRB risk) to automatically determine processing depth for each input; **6 CLI targets** (Claude Code / Codex CLI / OpenCode / Gemini CLI / Qwen CLI / Grok CLI) with one rule set across all; **Hooks integration** (Claude Code 11 lifecycle hooks + Codex CLI notify hook + Gemini CLI 6 hooks + Grok CLI 3 hooks) with automatic graceful degradation when unavailable.

### CLI Compatibility Quick Reference

| CLI | Recommended Version | Key Features | Configuration Notes |
|-----|-------------------|--------------|---------------------|
| **Claude Code** | Latest | Agent Teams, 11 lifecycle hooks | Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for teams mode |
| **Codex CLI** | 0.110+ | spawn_agent, CSV batch, enable_fanout | Enable sub-agents, CSV orchestration, set `project_doc_max_bytes >= 131072` |
| **OpenCode** | Latest | Task tool, custom agents, MCP | Supports primary agents (build/plan) + subagents (general/explore) |
| **Gemini CLI** | Latest | Built-in tool calls | Sequential execution fallback |
| **Qwen CLI** | Latest | Built-in tool calls | Sequential execution fallback |
| **Grok CLI** (Experimental) | Latest | Built-in tool calls | Community wrapper, hooks not fully verified |

<details>
<summary>📋 Detailed CLI-specific notes (click to expand)</summary>

**Codex CLI Configuration:**
- Enable sub-agents and CSV orchestration features
- Set `project_doc_max_bytes = 131072` in config.toml
- Configure `developer_instructions` for routing protocol priority
- Enable `enable_fanout` for CSV batch orchestration (v0.110+)
- Configure `nickname_candidates` for agent role identification
- Configure read-only role configs for read-only sub-agents; Codex CLI currently does not provide a PreToolUse dangerous-command hook
- Configure CSV batch processing if using parallel workflows

**Claude Code Setup:**
- Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable for Agent Teams
- 11 lifecycle hooks auto-configured during installation (SessionStart, UserPromptSubmit, SubagentStart/Stop, PostToolUse, Stop, TeammateIdle, PreCompact, PreToolUse, SessionEnd, PostToolUseFailure)
- Auto-memory feature disabled during installation (prevents conflicts with AGENTS.md rules)

**Other CLIs:**
- OpenCode supports Task tool with primary agents (build/plan) and subagents (general/explore)
- Gemini/Qwen/Grok use sequential execution fallback
- All features work with graceful degradation
- Hooks may not be available on all platforms

</details>

## Quick Start

> **Choose your installation method:**
> - **2.x/m maintenance channel** → Method A (UV, recommended)
> - **No UV available** → Method B (pip)
> - **Need the upstream 3.x channel** → install upstream `main` explicitly

> **Prerequisite:** Use AI CLI versions that support the features you need, such as sub-agents and CSV orchestration. VSCode extensions often lag behind terminal CLIs.

> ⚠️ **Windows PowerShell 5.1** does not support `&&`. Run commands on each side of `&&` separately, or upgrade to [PowerShell 7+](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows).

### Method A: UV install for the 2.x/m maintenance channel (recommended)

**Install and select targets:**

    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents

**Install Codex target only:**

    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents install codex

**Verify channel:**

    helloagents version --force --cache-ttl 0
    helloagents status

Expected package version: `2.4.1`; expected branch: `dev/2.3.8`.

**Update:**

    helloagents update

When `helloagents update` uses UV, it now adds `--force --no-cache` automatically to avoid reusing stale same-version wheels on the maintenance branch.

**Local source reinstall (for development / verification):**

    uv tool install --force --no-cache "E:\code\python\helloagents"

**Uninstall:**

    uv tool uninstall helloagents

### Method B: pip install for the 2.x/m maintenance channel

    python -m pip install --upgrade --no-cache-dir "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8"
    helloagents

If pip reports `externally-managed-environment`, use Method A with UV.

### Method C: Install UV first

Skip this if `uv` is already available.

    # Windows PowerShell
    irm https://astral.sh/uv/install.ps1 | iex

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

> After installing UV, restart your terminal to make the `uv` command available.

### Method D: npm / npx bootstrap (not the 2.x/m default)

    npx helloagents

The npm package follows the npm release channel and may not install this repository's 2.x/m maintenance build. Use Method A or B when you need the maintenance channel.

### HelloAGENTS commands (after installation)

> ⚠️ These commands depend on the installed package. If a remote update causes issues, use the native install/update/uninstall commands from your installation method above.

    helloagents                  # interactive menu
    helloagents install codex    # specify target directly
    helloagents install --all    # install to all detected CLIs
    helloagents status           # check installation status
    helloagents version          # check version
    helloagents update           # update + auto-sync all targets
    helloagents update main      # explicit branch switch + auto-sync
    helloagents uninstall codex  # uninstall from a CLI target
    helloagents uninstall --all  # uninstall from all targets
    helloagents clean            # clean caches

### Codex CLI example

**First install:**

    # UV
    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents install codex

    # pip
    python -m pip install --upgrade --no-cache-dir "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8"
    helloagents install codex

**Update later (auto-syncs installed targets):**

    helloagents update

> ⚠️ **Codex CLI config.toml compatibility notes:** The following settings may affect HelloAGENTS:
> - `[features]` `child_agents_md = true` — experimental, injects extra instructions that may conflict with HelloAGENTS
> - `project_doc_max_bytes` too low — default 32KB, AGENTS.md will be truncated (auto-set to 131072 during install)
> - `agent_max_depth = 1` — limits sub-agent nesting depth, recommend keeping default or ≥2
> - `agent_max_threads` too low — default 6, lower values limit parallel sub-agent scheduling (CSV batch mode recommends ≥16)
> - `[features]` `multi_agent = true` — must be enabled for sub-agent orchestration to work
> - `[features]` `enable_fanout = true` — must be enabled for CSV batch orchestration (spawn_agents_on_csv)
> - Collab sub-agent scheduling requires Codex CLI feature gate to be enabled
>
> 💡 **Best practices:**
> - Codex 0.110+ recommended for full feature set (enable_fanout, nickname_candidates)
> - HelloAGENTS is optimized for Codex CLI — supports `high` and below reasoning effort levels. `xhigh` reasoning is **not supported** and may cause instruction-following issues
> - Use the terminal/CLI version of Codex for the best experience. The VSCode extension updates lag behind the CLI — newer features (e.g., CSV batch orchestration, Collab multi-agent) may require waiting for the extension to catch up

### Claude Code example

**First install:**

    # UV
    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents install claude

    # pip
    python -m pip install --upgrade --no-cache-dir "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8"
    helloagents install claude

**Update later (auto-syncs installed targets):**

    helloagents update

> 💡 **Claude Code sub-agent orchestration tips:**
> - Sub-agents (Agent tool) work out of the box, no extra configuration needed
> - Agent Teams collaboration mode requires environment variable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
> - Parallel sub-agent count is managed automatically by the model, no user-side limit config needed

## Configuration

Customize workflow behavior via `~/.helloagents/helloagents.json` after installation. Only include keys you want to override — missing keys use defaults.

**Available keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `OUTPUT_LANGUAGE` | string | `zh-CN` | Language for AI output and KB files |
| `KB_CREATE_MODE` | int | `2` | KB creation: `0`=OFF, `1`=on-demand (prompt ~init), `2`=auto on code changes, `3`=always auto |
| `BILINGUAL_COMMIT` | int | `1` | Commit language: `0`=OUTPUT_LANGUAGE only, `1`=OUTPUT_LANGUAGE + English |
| `EVAL_MODE` | int | `1` | Clarification mode: `1`=progressive (1 question/round, max 4), `2`=one-shot (all at once, max 2) |
| `UPDATE_CHECK` | int | `72` | Update check cache TTL in hours: `0`=OFF |
| `CSV_BATCH_MAX` | int | `16` | CSV batch max concurrency: `0`=OFF, cap 64 (Codex CLI only) |
| `NOTIFY_LEVEL` | int | `2` | Notification mode: `0`=OFF, `1`=desktop, `2`=sound, `3`=desktop+sound; unified notifications include project name and task summary; legacy `notify_level` is still supported |

Notifications are routed through `unified_notify.py`. When the main agent completes, waits for confirmation, warns, or errors, desktop and sound notifications use the same short context where possible, for example `Completed - goedge - login feature`; if system speech is unavailable, HelloAGENTS falls back to the bundled event sounds.

**Example:**

```json
{
  "KB_CREATE_MODE": 0,
  "EVAL_MODE": 2
}
```

> File missing or unparseable is silently skipped with defaults applied. Unknown keys produce a warning and are ignored.

### Common Configuration Scenarios

<details>
<summary>📝 English-only projects</summary>

```json
{
  "OUTPUT_LANGUAGE": "en-US",
  "BILINGUAL_COMMIT": 0
}
```
All AI outputs, KB files, and commit messages will be in English only.
</details>

<details>
<summary>🚫 Disable automatic KB creation</summary>

```json
{
  "KB_CREATE_MODE": 0
}
```
Knowledge base won't be created automatically. Use `~init` command when needed.
</details>

<details>
<summary>⚡ High-concurrency batch processing (Codex CLI)</summary>

```json
{
  "CSV_BATCH_MAX": 32
}
```
Increase parallel CSV batch processing from 16 to 32 (max 64). Requires Codex CLI with CSV orchestration enabled.
</details>

<details>
<summary>🔕 Disable update checks</summary>

```json
{
  "UPDATE_CHECK": 0
}
```
Skip version update checks entirely (not recommended for production use).
</details>

<details>
<summary>💬 One-shot clarification mode</summary>

```json
{
  "EVAL_MODE": 2
}
```
Ask all clarification questions at once (max 2 rounds) instead of progressive mode (1 question per round, max 4).
</details>

## How It Works

**In short:** HelloAGENTS automatically selects processing depth based on task complexity — simple questions get fast responses, complex tasks go through the full evaluate→design→develop flow, with safety checks and memory retention throughout.

**Detailed flow:**

1. **Install & Deploy** — Run `helloagents` to select target CLI, auto-deploys config files and hooks
2. **Smart Routing** — Every input is auto-scored; simple queries get direct answers, complex tasks enter structured workflow
3. **Stage Progression** — Complex tasks advance through "Evaluate → Design → Develop" stages, each with clear deliverables
4. **Auto Orchestration** — System dispatches sub-agents and specialized roles based on complexity, parallelizes when possible
5. **Safety Guard** — Each step scans for destructive operations, risky actions require user confirmation, and CLIs with PreToolUse support block typical dangerous commands before execution
6. **Memory Retention** — User preferences, project knowledge, session context persist across sessions
7. **Verified Completion** — Stage chain completes with verified output, auto-syncs knowledge base

## In-Chat Workflow Commands

These commands run inside AI chat, not your system shell.

**Common Commands:**

| Command | Purpose |
|---|---|
| ~auto | full autonomous workflow |
| ~plan | planning and package generation |
| ~exec | execute existing package |
| ~build | smart build (execute package if exists, otherwise route by need) |
| ~init | initialize knowledge base |
| ~ssh | initialize/update project servers, environments, paths, and run commands |
| ~commit | generate commit message from context |
| ~status / ~help | status and help |

**Quality Checks:**

| Command | Purpose |
|---|---|
| ~test | run project tests |
| ~review | code review |
| ~verify | review + verify + auto-fix + wrap-up (~review superset) |
| ~validatekb | validate knowledge base |
| ~loop | iterative improvement until quality target is met |

**Product & Exploration:**

| Command | Purpose |
|---|---|
| ~idea | lightweight tech exploration and direction comparison (read-only) |
| ~prd | interactive product requirements document generation |

**Advanced Features:**

| Command | Purpose |
|---|---|
| ~wiki | KB creation and sync (~init KB subset) |
| ~upgradekb | upgrade knowledge structure |
| ~clean / ~cleanplan | cleanup and archive workflow artifacts |
| ~rollback | rollback workflow state |
| ~rlm | role orchestration (spawn / agents / resume / team) |

## Usage Guide

### Three Workflow Modes

| Mode | Description | When to use |
|------|-------------|-------------|
| `~auto` | Full autonomous flow from requirement to verified implementation (Evaluate → Design → Develop → Verify) | Clear requirement, want end-to-end delivery |
| `~plan` | Planning only, generates a proposal package then stops — no code written | Want to review the plan before committing |
| `~exec` | Skip evaluation and design, execute an existing plan package directly | After `~plan` review, ready to implement |
| `~build` | Smart entry: executes package if one exists, otherwise routes by need | Unified entry point regardless of package state |

Typical pattern: `~plan` first → review → `~exec` to implement. Or just `~auto` for one-shot delivery, or `~build` to auto-detect.

### Interactive vs Delegated Mode

When `~auto` or `~plan` presents its confirmation, you choose:

- **Interactive (default):** pauses at key decision points (plan selection, failure handling)
- **Delegated (fully automatic):** auto-advances all stages, auto-selects recommended options, only pauses on EHRB risk
- **Plan-only delegated:** fully automatic but stops after design, never enters development

Without `~` commands, plain-text input is automatically routed to R0–R2 based on complexity.

### Requirement Evaluation

Before R2 tasks enter execution, the system scores requirements on four dimensions (scope 0–3, deliverable spec 0–3, implementation conditions 0–2, acceptance criteria 0–2). The pass condition is based on core dimension sufficiency (scope ≥ 3, implementation conditions ≥ 1, deliverable spec ≥ 1) rather than a fixed total score threshold. Dimensions below the sufficiency line trigger clarifying questions:

- `EVAL_MODE=1` (default, progressive): asks 1 insufficient dimension per round, up to 4 rounds
- `EVAL_MODE=2` (one-shot): asks all insufficient dimensions at once, up to 2 rounds

The last round of questioning is combined with confirmation (question + execution mode selection), reducing standalone confirmation steps. Context inferred from the existing codebase counts toward the score automatically. Say "skip evaluation / just do it" to bypass the questioning phase.

### Parallel Design Proposals

In the R2 standard path, the design stage dispatches 3–6 sub-agents to independently generate competing implementation proposals. The main agent evaluates all proposals across four dimensions: user value, solution soundness, risk (including EHRB), and implementation cost. Weights are dynamically adjusted based on project characteristics (e.g., performance-critical systems weight soundness higher; MVPs weight cost higher).

- Interactive mode: user selects a proposal or requests re-generation (max 1 retry)
- Delegated mode: recommended proposal is auto-selected
- R2 standard path: complex tasks go through multi-proposal comparison; simple tasks skip it and go directly to planning

### Lightweight Design Path

When an R2 task meets all of the following conditions, it automatically enters the lightweight path, skipping package creation:

- TASK_COMPLEXITY = simple, affected files ≤ 3, estimated changes ≤ 30 lines

Lightweight behavior: skips proposal.md / tasks.md creation, outputs a ≤200-word solution summary, then enters DEVELOP directly with main agent execution (no sub-agent dispatch), using R1-level acceptance criteria. Falls back to the standard path if conditions aren't met.

### Auto Dependency Management

During development, the system auto-detects the project's package manager via lockfiles (`yarn.lock` → yarn, `uv.lock` → uv, `Gemfile.lock` → bundler, etc.) and handles dependencies:

- Declared but missing dependencies: auto-installed
- New dependencies required by tasks: auto-added with declaration file updated
- Ambiguous dependencies: user is asked before installing

### Quality Verification (Ralph Loop & Break-loop)

**Ralph Loop** (Claude Code, via SubagentStop Hook): after a sub-agent completes code changes, the project's verification command runs automatically. On failure, the sub-agent is blocked from exiting and must fix the issue (max 1 retry loop). Verification command priority: `.helloagents/runbook.yaml` → `.helloagents/verify.yaml` → `package.json` scripts → auto-detected.

**Break-loop** (deep root cause analysis): triggered when a task fails repeatedly (after Ralph Loop + at least 1 manual fix attempt), performing five-dimension root cause analysis:

1. Root cause classification (logic error / type mismatch / missing dependency / environment / design flaw)
2. Why previous fixes didn't work
3. Prevention mechanism suggestions
4. Systemic scan — same issue in other modules?
5. Lessons learned recorded in the acceptance report

### Smart Commit (~commit)

`~commit` does more than generate a message:

- Analyzes `git diff` to auto-generate Conventional Commits formatted messages
- Pre-commit quality checks (code-doc consistency, test coverage, verification commands)
- Auto-excludes sensitive files (`.env`, `*.pem`, `*.key`, etc.) — never runs `git add .`
- Shows file list before staging, supports exclusion
- Options: local commit only / commit + push / commit + push + create PR
- Bilingual commit messages when `BILINGUAL_COMMIT=1`

### Iterative Improvement (~loop)

Set a quality target and guard command (e.g., "test coverage >= 80%"), and the system automatically loops improve→verify until the target is met:

- Each round: apply improvements → run verification command → check target
- Stops when target is met, max rounds reached (default 5), or 2 consecutive rounds show no progress
- Supports per-round rollback (reverts changes on verification failure)
- Use cases: "increase test coverage to 90%", "fix all lint errors"

### Tech Exploration (~idea)

Read-only lightweight analysis — no file writes, no code changes, no package creation:

- Compares 2–4 technical directions, evaluating feasibility, risk, and ecosystem compatibility
- Use cases: quick evaluation before tech choices, "would this approach work?" questions
- Outputs multi-direction comparison table + recommended direction

### Product Requirements Document (~prd)

Interactive structured PRD generation, discussing each dimension (product overview, feature scope, user scenarios, technical constraints, acceptance criteria) one round at a time. Outputs a complete PRD to the `plan/` directory. Supports interactive and fully delegated modes.

### Comprehensive Verification (~verify)

Superset of `~review`, covering review → verify → auto-fix → wrap-up:

- Code review (Critical/Warning/Info severity grading)
- Run lint/type checks/tests/build
- Auto-fix on failure (max 3 rounds)
- Generate verification report + write to CHANGELOG
- Auto-detects recent changes when called without arguments

### Manual Sub-Agent Invocation

Beyond automatic dispatch, you can manually invoke specific roles:

    ~rlm spawn reviewer "review src/api/ for security issues"
    ~rlm spawn writer "generate API reference docs"
    ~rlm spawn reviewer,writer "analyze and document the auth module"  # parallel

Available roles: `reviewer` (code review), `writer` (documentation), `brainstormer` (multi-proposal comparison).

### Multi-Terminal Collaboration

Multiple terminals (across different CLIs) can share a task list:

    # Terminal A
    hellotasks=my-project codex

    # Terminal B
    hellotasks=my-project claude

Commands once enabled:

    ~rlm tasks                  # view shared task list
    ~rlm tasks available        # see unclaimed tasks
    ~rlm tasks claim <id>       # claim a task
    ~rlm tasks complete <id>    # mark done
    ~rlm tasks add "task title" # add a new task

Tasks are stored in `{KB_ROOT}/tasks/` with file locking to prevent concurrent conflicts.

### KB Auto-Sync & CHANGELOG

The knowledge base syncs automatically at these points:

- After every development stage, main agent syncs module docs to reflect actual code
- After every R1/R2 task completion, CHANGELOG is auto-appended
- On session end (Claude Code Stop Hook), KB sync flag set asynchronously

CHANGELOG uses semantic versioning (X.Y.Z). Version source priority: user-specified → project file (package.json, pyproject.toml, etc., supporting 15+ languages/frameworks) → git tag → last CHANGELOG entry → 0.1.0. R1 fast-path changes are recorded under a "Quick Modifications" category with file:line range.

`KB_CREATE_MODE` controls automatic behavior: `0`=off, `1`=prompt on demand, `2`=auto on code changes (default), `3`=always auto.

### Worktree Isolation

When multiple sub-agents need to modify different regions of the same file simultaneously (Claude Code only), the system automatically uses `Task(isolation="worktree")` to create an independent git worktree for each sub-agent, preventing Edit tool conflicts. The main agent merges all worktree changes in the consolidation phase. Only activated when sub-agents have overlapping file writes; read-only tasks don't use it.

### CSV Batch Orchestration (Codex CLI)

When ≥6 structurally identical tasks exist in the same execution layer, the system auto-converts `tasks.md` into a task CSV and dispatches via `spawn_agents_on_csv`. Each worker receives its row data + instruction template, executes independently, and reports results.

- Progress tracked in real-time via `agent_job_progress` events (pending/running/completed/failed/ETA)
- State persisted in SQLite for crash recovery
- Partial failures still export results with failure summary
- Heterogeneous tasks automatically fall back to `spawn_agent` sequential dispatch
- Configure concurrency via `CSV_BATCH_MAX` (default 16, max 64, set to 0 to disable)

### Update Check

On the first response of each session, the system silently checks for new versions. Results are cached at `~/.helloagents/.update_cache`, valid for the duration set by `UPDATE_CHECK` (default 72 hours, set to 0 to disable). When a new version is available, `⬆️ New version {version} available` appears in the response footer. Any errors during the check are silently skipped and never interrupt normal usage.

Maintenance builds marked with `+m` / `-m` (for example `2.3.9-m`, Python metadata `2.3.9+m`) follow their installed maintenance branch by default. The 2.x/m channel checks `dev/2.3.8` and no longer compares against `main` / latest 3.x releases unless you explicitly run `helloagents update <branch>`.

## Repository Guide

- AGENTS.md: router and workflow protocol
- SKILL.md: skill discovery metadata for CLI targets
- pyproject.toml: package metadata (v2.4.1)
- helloagents/cli.py: CLI entry point
- helloagents/_common.py: shared constants and utilities
- helloagents/core/: CLI management modules (install, uninstall, update, status, dispatcher, hooks settings)
- helloagents/functions: command definitions (21)
- helloagents/stages: design, develop
- helloagents/services: knowledge, package, memory and support services
- helloagents/rules: state, cache, tools, scaling, sub-agent protocols
- helloagents/rlm: role library and orchestration helpers
- helloagents/hooks: Claude Code, Codex CLI, Gemini CLI, and Grok CLI hooks configs
- helloagents/scripts: automation scripts (sound notify, progress snapshot, safety guard, etc.)
- helloagents/agents: sub-agent definitions (3 RLM roles)
- helloagents/assets: sound resources (5 event sounds)
- helloagents/templates: KB and plan templates

## FAQ

**Q: Is this a Python CLI tool or prompt package?**

A: Both. The CLI manages installation and updates, while the workflow behavior comes from AGENTS.md and documentation files. Think of it as a delivery system + intelligent workflow protocol.

**Q: Which target should I install?**

A: Choose the CLI you're actively using: `codex` (Codex CLI), `claude` (Claude Code), `gemini` (Gemini CLI), `qwen` (Qwen CLI), `grok` (Grok CLI), or `opencode` (OpenCode). You can install to multiple targets with `helloagents install --all`. See [CLI Compatibility Quick Reference](#cli-compatibility-quick-reference) for details.

**Q: What if a rules file already exists?**

A: HelloAGENTS automatically backs up non-HelloAGENTS files before replacement. Backups are timestamped and stored in your CLI's config directory. You can restore them anytime if needed.

**Q: What is RLM?**

A: Role Language Model — HelloAGENTS's sub-agent orchestration system. It includes 3 specialized roles (reviewer, writer, brainstormer) plus native CLI sub-agents. Tasks are scheduled via DAG dependency analysis with parallel execution when possible. Learn more in [Usage Guide](#usage-guide).

**Q: Where does project knowledge go?**

A: In the project-local `.helloagents/` directory. The knowledge base auto-syncs when code changes (controlled by `KB_CREATE_MODE` config). It includes module docs and CHANGELOG. See [KB Auto-Sync & CHANGELOG](#kb-auto-sync--changelog).

**Q: Does knowledge persist across sessions?**

A: Yes. The project knowledge base is stored in the project-local `.helloagents/` directory. Context survives even if you close and reopen your CLI.

**Q: What are Hooks?**

A: Lifecycle hooks auto-deployed during installation. Claude Code gets 11 event hooks (safety checks, dangerous command guard, progress snapshots, KB sync, unified notifications, tool failure recovery, etc.); Codex CLI gets a notify hook for update checks and unified notifications, but currently has no pre-execution dangerous-command hook; Gemini CLI gets 6 hooks (context injection, progress snapshots, unified notifications, pre-compression snapshots); Grok CLI gets 3 hooks (context injection, safety guard, progress snapshots). All optional — features degrade gracefully when hooks aren't available. No manual configuration needed.

**Q: What is Agent Teams?**

A: An experimental Claude Code feature where multiple Claude Code instances collaborate as teammates with shared task lists and mailbox communication. Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. When unavailable, HelloAGENTS falls back to standard Task sub-agents. See [Multi-Terminal Collaboration](#multi-terminal-collaboration).

## Troubleshooting

### Command not found

**Problem:** `helloagents: command not found` after installation

**Diagnosis:** Install path not in system PATH

**Solution:**
- UV: Restart terminal after UV installation
- pip: Check `pip show helloagents` for install location, add to PATH
- Verify with `which helloagents` (Unix) or `where helloagents` (Windows)

**Verification:** Run `helloagents version`

---

### Package version unknown

**Problem:** Version shows as "unknown"

**Diagnosis:** Package metadata not available

**Solution:** Install the package first: `uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache`

**Verification:** Run `helloagents version` — should show current version number

---

### Target not detected

**Problem:** CLI target not found during installation

**Diagnosis:** Config directory doesn't exist yet

**Solution:** Launch the target CLI at least once to create its config directory, then retry `helloagents install <target>`

**Verification:** Check config paths:
- Codex CLI: `~/.codex/`
- Claude Code: `~/.claude/`
- Others: see CLI documentation

---

### Custom rules overwritten

**Problem:** Custom rules replaced by HelloAGENTS

**Diagnosis:** Installation replaces existing files

**Solution:** Restore from timestamped backup in CLI config directory (e.g., `~/.codex/AGENTS_20260304132146_bak.md`)

**Verification:** Check backup files in config directory

---

### Images not rendering

**Problem:** README images don't display

**Diagnosis:** Missing image files or incorrect paths

**Solution:**
- Keep relative paths in README (e.g., `./readme_images/`)
- Ensure `readme_images/` folder is committed to repository
- Verify image files exist locally

**Verification:** Check `ls readme_images/` shows all referenced images

---

### CCswitch replaces HelloAGENTS config

**Problem:** After switching CCswitch profiles, HelloAGENTS stops working (workflow commands unrecognized, hooks not firing, rules missing)

**Diagnosis:** CCswitch replaces the entire CLI config directory (e.g., `~/.claude/`) when switching profiles, overwriting HelloAGENTS's hooks, permissions, and rule files

**Solution:** After switching CCswitch profiles, run one of these commands to restore HelloAGENTS:

    helloagents install claude    # reinstall to specific CLI target
    helloagents update            # update + auto-sync all installed targets

**Prevention:** Since v2.3.5, automatic configuration integrity check on session start — if HelloAGENTS config is missing or corrupted, a warning is displayed with recovery instructions

**Verification:** Run `helloagents status` to confirm all targets show as installed

---

### CCswitch configuration conflict

**Problem:** HelloAGENTS config reappears after uninstall when switching CCswitch profiles

**Diagnosis:** CCswitch saved HelloAGENTS settings before uninstall

**Solution:** After uninstalling HelloAGENTS, manually clean up HelloAGENTS-related settings (hooks, permissions, rules) from all saved CCswitch profiles

**Verification:** Check CCswitch profile directories for HelloAGENTS remnants

## Version History

### v2.4.1 (current)

**Unified Notifications:**
- Added `unified_notify.py` as the shared notification entry point, so sound and desktop notifications use the same project name and task summary, such as `Completed - helloagents - current task`
- Codex `notify`, Claude Stop, and Gemini AfterAgent hooks now route through the unified entry point; Codex notifications from IDE clients remain silent
- Sound notifications prefer system TTS for dynamic context and fall back to bundled event sounds; desktop notifications use the same context line
- Windows Toast notifications now pass XML through `-EncodedCommand`, preventing notification content from being parsed as PowerShell command syntax

**Workflow Experience:**
- Completion footers can now offer 2-4 numbered next actions, prioritizing review, commit/verification, and concrete follow-up work based on the current change
- `~commit` now shows the safe staging list after the user confirms the commit mode and no longer asks for the same staging range twice; sensitive files, empty lists, conflicts, or EHRB risks still pause for handling

**Post-2.4.0 Enhancements:**
- Added `~ssh` and ProjectEnvService for project environments, host references, remote paths, runbook validation commands, and sensitive credential-reference boundaries
- Improved `~test` and Ralph Loop runbook parsing with project aliases, default `latest_commit_fixes` workflows, and safeguards that skip remote, production, or template-placeholder commands
- `~review current changes` can detect the recent-change scope directly, then create and run the conservative fix path when review findings need code changes
- R2 final clarification now merges with execution-mode confirmation, and pending confirmations can recover from interruptions and semantic replies like "continue" or "start review"
- Plan package archival now syncs `tasks.md`, `LIVE_STATUS`, and `.status.json`, reducing manual cleanup after migration
- Codex read-only sub-agents use isolated role config files, and the docs now clarify hook capability and safety boundaries

### v2.4.0

**6 New Workflow Commands (total 15→21):**
- `~idea`: Lightweight tech exploration and comparison, read-only analysis (no file writes, no plan packages), ideal for quick evaluation before technology decisions
- `~build`: Superset of `~exec` — executes plan packages when available, routes to on-demand implementation when not, serving as a unified build entry point
- `~prd`: Interactive structured PRD (Product Requirements Document) generation, discusses each dimension then outputs a complete PRD to `plan/` directory
- `~loop`: Iterative improvement — sets quality metrics + guard commands, then auto-loops execute→verify until targets are met or max rounds reached
- `~wiki`: Pure knowledge base management (KB subset of `~init`), handles only KB creation/sync without rules or skills linking
- `~verify`: Superset of `~review`, covering review → run verification → auto-fix (up to 3 rounds) → generate report + write to CHANGELOG

**Lightweight Execution Paths:**
- Added R1 quick-judge anchors: three patterns (known-location single edit, known-command execution, known-pattern copy) enable fast R1 determination, reducing simple tasks being misrouted to R2
- Added LIGHTWEIGHT_DESIGN path: when R2 simple tasks involve ≤3 files and ≤30 lines of changes, skip plan package creation and enter DEVELOP directly with a lightweight proposal summary, reducing process overhead for small tasks

**~clean Command Expansion:**
- Upgraded to "clean & archive" — added plan package archival capability: scans completed packages and migrates them to `archive/YYYY-MM/` via `migrate_package.py` (instead of direct deletion)
- More granular user options: clean all + archive, cache only, archive packages only, selective processing

**Workflow Rule Improvements:**
- Added GPT anti-pattern rules for split delivery, filler closings, and holding-back behavior
- Added quality baselines for output standards, language style, technical choice, silent failure prevention, blocking criteria, and UI acceptance
- Added frontend copy sanitization rules: prohibit writing functional descriptions or product copy in component attributes (title/subtitle/description/tooltip, etc.), enforced across sub-agent prompt templates, develop stage instructions, reviewer checklist, and project guidelines template
- Backported the first batch of planning-design improvements: evidence-driven assumptions, option tradeoffs, validation strategy, and richer plan templates

**Testing & Infrastructure:**
- Added 3 test files: updater Windows lock file handling, CLI recovery paths, version check multi-format parsing
- Install scripts (install.sh / install.ps1) default to maintenance branch, support `HELLOAGENTS_BRANCH` environment variable override
- CONTRIBUTING.md updated to package-first structure declaration

### v2.3.9-m

**Maintenance Channel:**
- Published the 2.x/m maintenance build as `v2.3.9-m` while keeping Python package metadata PEP 440-compatible as `2.3.9+m`
- Changed maintenance-build update detection to follow the installed branch/source by default, with the 2.x/m fallback branch set to `dev/2.3.8`
- `main` / latest 3.x releases no longer trigger default update prompts for the 2.x/m channel
- `helloagents update <branch>` still supports explicit branch switching when users intentionally leave the maintenance channel
- UV install and update paths now use `--force --no-cache` to avoid stale same-version wheels on the maintenance branch

**Workflow Rule Improvements:**
- Added GPT anti-pattern rules for split delivery, filler closings, and holding-back behavior
- Added quality baselines for output standards, language style, technical choice, silent failure prevention, blocking criteria, and UI acceptance
- Added frontend copy sanitization rules: prohibit writing functional descriptions or product copy in component attributes (title/subtitle/description/tooltip, etc.), enforced across sub-agent prompt templates, develop stage instructions, reviewer checklist, and project guidelines template
- Backported the first batch of planning-design improvements: evidence-driven assumptions, option tradeoffs, validation strategy, and richer plan templates

### v2.3.8

**Architecture Changes:**
- Routing tier consolidation: removed R2 simplified flow and R3 standard flow, unified to R0/R1/R2 three-tier routing. New R2 standard flow merges use cases from both old R2 and R3
- Evaluation now driven by dimension sufficiency (scope ≥ 3, implementation conditions ≥ 1, deliverable spec ≥ 1), replacing fixed total score threshold (previously "score ≥ 8")
- Last-round question+confirmation combined: clarifying question + execution mode selection in the same turn, reducing standalone confirmation steps
- DESIGN multi-proposal comparison now triggered by TASK_COMPLEXITY (complex → multi-proposal, simple/moderate → skip), replacing route-level triggering
- Removed L0 user memory system and custom command extension (`user/` directory): simplified to single-layer project knowledge model (L1 project KB only)
- Config system consolidation: migrated from two-tier priority config (`config.json` at project + global level) to single `~/.helloagents/helloagents.json` with auto-sync on install
- Added code size control rules: warning threshold (file/class 300 lines, function 40 lines), mandatory split threshold (file/class 400 lines, function 60 lines)

**New Features:**
- Added 5 new workflow commands: `~test`, `~rollback`, `~validatekb`, `~upgradekb`, `~cleanplan`
- Added notify_level config key (0=off, 1=desktop, 2=sound, 3=both) for notification behavior control
- Added standalone config reader module (`scripts/_config.py`) for hook scripts
- Brainstormer sub-agent output format enhanced: added `key_findings` field for proposal highlights

**Security:**
- Fixed path injection vulnerability in shared_tasks.py: `list_id` from environment variable now sanitized before use in file path construction
- Fixed incomplete path traversal guard in validate_package.py: `relative_to()` failure now properly exits with error instead of falling through

**Bug Fixes:**
- Fixed Gemini/Grok hooks PostToolUse matcher missing NotebookEdit (now `Write|Edit|NotebookEdit`, consistent with Claude Code)
- Fixed pre_compact.py still using deprecated LIVE_STATUS HTML comments while progress_snapshot.py had migrated to .status.json
- Fixed pre_compact.py `_get_current_task` regex only matching numbered lists, now supports unordered lists
- Fixed progress_snapshot.py docstring incorrectly stating Grok uses async=true (actual config is async=false)
- Fixed dispatcher update check cache_ttl default from None to 72 hours
- Fixed utils.py incorrectly treating Python package source directories as legacy KB directories during migration
- Fixed cli.py error recovery passing args as branch name when dispatcher is broken

**Improvements:**
- Codex CLI feature flags updated: replaced `sqlite`+`collaboration_modes` with `enable_fanout` for CSV batch orchestration
- Added Windows UTF-8 encoding block to codex_notify.py (all other hook scripts already had it)
- Extended stop_sound_router.py UTF-8 encoding to cover stdout/stderr (previously only stdin)
- Added NOTE comments across all intentionally duplicated functions for cross-file sync awareness
- Added yearly changelog archive template (`CHANGELOG_{YYYY}.md`)

### v2.3.7

**Bug Fixes:**
- Fixed non-coding tasks incorrectly creating knowledge base when KB_CREATE_MODE=2 (added programming task check in design.md Phase1 step 1)
- Fixed R2 standard flow redirecting to archive instead of DEVELOP after proposal selection (constrained overview type to ~exec entry only)
- Fixed non-coding tasks incorrectly creating plan packages (added programming task precondition to package.md create() interface)

**Improvements:**
- Optimized implementation plan state recovery after context compression
- Optimized overall design flow

### v2.3.6

**New Features:**
- Sub-agent orchestration overhaul: added brainstormer sub-agent for independent parallel proposal ideation during DESIGN multi-proposal comparison
- Sub-agent blocking mechanism: auto-block and fallback to main agent on sub-agent failure or timeout

**Improvements:**
- Tool/Shell constraint optimization: allow fallback to Shell when built-in tools fail (fixes Codex CLI Windows apply_patch repeated failures)
- Shell encoding constraint refinement: explicit UTF-8 no-BOM requirement, separate read/write encoding handling for PowerShell
- Added batch file write rule (merge ≥3 files into a single temp script to avoid sandbox per-command blocking)
- Removed session memory features that couldn't be fully implemented in CLI (session_summary template, SessionEnd memory sync), streamlined service layer
- Sub-agent consolidation: removed 3 redundant sub-agents (kb-keeper, pkg-keeper, synthesizer), functionality returned to main agent and RLM roles
- Sub-agent voice notification skip, task stability fixes
- Uninstall script enhancements
- Visual verification gap and UI quality fixes

### v2.3.5

**New Features:**
- Voice notification system with 5 event sounds (complete, idle, confirm, error, warning) across Windows/macOS/Linux, with smart two-layer routing (stop_reason + G3 format icon detection)
- Claude Code hooks expanded from 9 to 11 lifecycle event types: added dangerous command guard (PreToolUse), session end cleanup (SessionEnd), and tool failure recovery suggestions (PostToolUseFailure)
- Hooks support expanded to Gemini CLI (SessionStart, BeforeAgent/AfterAgent, PreCompress, PreToolUse, PostToolUse) and Grok CLI (UserPromptSubmit, PreToolUse, PostToolUse)
- Codex CLI 0.110 features: `enable_fanout` for CSV batch orchestration, `nickname_candidates` for agent role identification
- Configuration integrity check on session start (auto-detect config corruption or replacement by CCswitch etc.)
- Context compression pre-save with automatic progress snapshot (pre_compact.py, progress_snapshot.py — actual implementations replacing placeholder hooks)
- User-defined tool registration and orchestration — intelligent invocation of custom sub-agents, skills, MCP servers, and plugins

**Improvements:**
- Comprehensive audit fixes (21 issues: 6 HIGH + 9 MEDIUM + 6 LOW)
  - Code quality: extracted 5 shared utility functions, eliminated circular dependencies
  - Cross-platform: unified platform detection, consistent encoding handling
  - Security: configuration backup before overwrite, placeholder validation
  - Documentation: configuration rationale, compatibility verification notes
- Core architecture: new dispatcher module, Codex roles definition, Claude rules management, hooks settings manager
- Install/update script refactoring with persistent configuration
- Voice notification accuracy and false positive reduction (Codex client filtering, Windows sync playback)
- Sub-agent nickname optimization across CLIs
- Codex CLI interactive menu, persistent memory, and context compression optimization
- R2 flow and evaluation module re-integration
- Context compression state persistence optimization
- Tool/Shell usage optimization
- CCswitch compatibility notes for configuration cleanup after uninstall
- SKILL discovery entry optimization

### v2.3.4

- Split 3 oversized files (>450 lines) into 6 independent modules
- Consolidated 9 CLI management scripts into core/ subpackage
- Extracted shared constants and utilities into dedicated module, eliminating circular dependencies
- Removed redundant backward-compatible re-exports
- Elevated Codex CLI routing protocol priority to prevent system prompt override

### v2.3.0

- Comprehensive cross-audit fix: unified role output format, normalized path references, code-doc consistency alignment
- Quality verification loop (Ralph Loop): auto-verify after sub-agent completion, block and feedback on failure
- Auto context injection for sub-agents and rule reinforcement for main agent
- Deep 5-dimension root cause analysis on repeated failures (break-loop)
- Auto-inject project technical guidelines before sub-agent development
- Pre-commit quality checks (code-doc consistency, test coverage, verification commands)
- Worktree isolation for parallel editing
- Auto-append Git author info to CHANGELOG entries

## Contributing

See CONTRIBUTING.md for contribution rules and PR checklist.

## License

This project is dual-licensed: Code under Apache-2.0, Documentation under CC BY 4.0. See [LICENSE.md](./LICENSE.md).

## Next Steps

**Getting Started:**
- Install HelloAGENTS using your preferred method: [Quick Start](#quick-start)
- Try `~auto` with a simple task to see the full workflow in action
- Explore `~plan` + `~exec` for more control over the process

**Learn More:**
- Read [Usage Guide](#usage-guide) for detailed workflow patterns
- Check [Configuration](#configuration) to customize behavior
- Review [In-Chat Workflow Commands](#in-chat-workflow-commands) reference

**Community & Support:**
- Star the repo if HelloAGENTS helps your workflow
- Report issues or request features on [GitHub Issues](https://github.com/Micah123321/helloagents/issues)
- Contribute improvements: see [CONTRIBUTING.md](./CONTRIBUTING.md)

---

<div align="center">

If this project helps your workflow, a star is always appreciated.

Thanks to <a href="https://codexzh.com/?ref=EEABC8">codexzh.com</a> / <a href="https://ccodezh.com">ccodezh.com</a> for supporting this project

</div>
