<div align="center">
  <img src="./readme_images/01-hero-banner.svg" alt="HelloAGENTS" width="800">
</div>

# HelloAGENTS

<div align="center">

**让 AI 按流程完成需求评估、实现和验证。**

[![Version](https://img.shields.io/badge/version-2.4.3-orange.svg)](./pyproject.toml)
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
> **需要旧版本的 HelloAGENTS？** 旧版代码库已迁移至独立归档仓库：[helloagents-archive](https://github.com/hellowind777/helloagents-archive)

## 目录

- [前后对比](#前后对比)
- [功能概览](#功能概览)
  - [子代理原生映射](#子代理原生映射)
- [快速开始](#快速开始)
- [配置](#配置)
- [工作原理](#工作原理)
- [聊天内工作流命令](#聊天内工作流命令)
- [使用指南](#使用指南)
- [仓库结构](#仓库结构)
- [FAQ](#faq)
- [故障排除](#故障排除)
- [版本历史](#版本历史)
- [参与贡献](#参与贡献)
- [许可证](#许可证)
- [下一步](#下一步)

---

## 前后对比

<table>
<tr>
<td width="50%" valign="top" align="center">

**未使用 HelloAGENTS**

<img src="./readme_images/08-demo-snake-without-helloagents.png" alt="未使用 HelloAGENTS 的贪吃蛇演示" width="520">

</td>
<td width="50%" valign="top" align="center">

**使用 HelloAGENTS**

<img src="./readme_images/07-demo-snake-with-helloagents.png" alt="使用 HelloAGENTS 的贪吃蛇演示" width="520">

</td>
</tr>
</table>

| 挑战 | 未使用 HelloAGENTS | 使用 HelloAGENTS |
|------|-------------------|-----------------|
| 止步于规划 | 给出建议后结束 | 持续推进到实现与验证 |
| 输出漂移 | 每次提示结构不同 | 统一路由与阶段链 |
| 高风险操作 | 容易误执行破坏性命令 | EHRB 风险检测与升级 |
| 知识延续 | 上下文分散丢失 | 内置知识库与会话记忆 |
| 可复用性 | 逐次提示重复劳动 | 命令化可复用工作流 |

## 功能概览

<table>
<tr>
<td width="50%" valign="top">
<img src="./readme_images/02-feature-icon-installer.svg" width="48" align="left">

**子代理自动编排（RLM）**

3 个专业角色（reviewer / writer / brainstormer）+ 宿主 CLI 原生子代理（explore / code / brainstorm），根据独立工作单元和并行收益自动调度，不要求用户显式说“子代理/并行代理”。任务通过 DAG 依赖分析进行拓扑排序，按层并行派发，支持跨 CLI 并行调度与 Agent Teams 协作。

**实际效果：** 复杂任务会拆成可执行的小任务，能并行时并行处理。
</td>
<td width="50%" valign="top">
<img src="./readme_images/03-feature-icon-workflow.svg" width="48" align="left">

**结构化工作流（评估→设计→开发）**

每条输入经五维评分路由至 R0 直答、R1 快速流或 R2 标准流。R2 进入完整阶段链，每个阶段有明确的进入条件、交付物和验证门控。支持交互模式与全自动委托模式。

**实际效果：** 简单问题直接回答；复杂任务进入完整流程，每步都有可检查的结果。
</td>
</tr>
<tr>
<td width="50%" valign="top">
<img src="./readme_images/04-feature-icon-safety.svg" width="48" align="left">

**三层安全检测（EHRB）**

关键词扫描、语义分析、工具输出检查，在执行前识别破坏性操作。支持 PreToolUse 的 CLI 会用 Hook 拦截典型危险命令；Codex CLI 当前没有执行前危险命令 Hook，依赖规则层确认、审批传播和只读角色配置。

**实际效果：** 默认启用安全检查，无需额外配置。
</td>
<td width="50%" valign="top">
<img src="./readme_images/05-feature-icon-compat.svg" width="48" align="left">

**项目知识库**

L1 项目知识库（从代码自动同步的结构化文档），上下文跨会话持续保留。

**实际效果：** 项目上下文保存在本地，下一次会话可以继续使用。
</td>
</tr>
<tr>
<td width="50%" valign="top">
<img src="./readme_images/02-feature-icon-installer.svg" width="48" align="left">

**可扩展性与自定义**

语音提示（5 种事件音效）、用户自定义工具调度（子代理、skills、MCP 服务器、插件）和配置选项。6 个 CLI 目标都可以安装；某个 CLI 不支持的功能会自动降级。

**实际效果：** 可以按团队使用习惯调整工作流，无需 fork 代码库。
</td>
<td width="50%" valign="top">
<img src="./readme_images/03-feature-icon-workflow.svg" width="48" align="left">

**多 CLI 支持**

一套规则适用于 Claude Code、Codex CLI、OpenCode、Gemini CLI、Qwen CLI 和 Grok CLI（实验性/社区）。安装时会检测当前 CLI 能力；不支持的功能自动降级。

**实际效果：** 切换 CLI 时仍使用同一套路由、阶段和命令规则。
</td>
</tr>
</table>

### 子代理原生映射

| CLI | 原生子代理机制 | RLM 映射方式 |
|-----|---------------|-------------|
| Claude Code | Agent tool（explore / code / shell） | 直接映射，支持 Agent Teams 协作 |
| Codex CLI | spawn_agent / Collab（多线程） | spawn_agent 并行调度，CSV 批量编排 |
| OpenCode | Task tool（build / plan / general / explore） | 直接子代理映射 |
| Gemini CLI | 内置工具调用 | 降级为顺序执行 |
| Qwen CLI | 内置工具调用 | 降级为顺序执行 |
| Grok CLI（实验性）| 内置工具调用 | 降级为顺序执行 |

此外，HelloAGENTS 还提供：**五维路由评分**（行动需求、目标可定位性、决策需求、影响范围、EHRB 风险），用于决定每条输入走 R0/R1/R2 哪个处理级别；**6 个 CLI 目标**共用同一套规则；**Hooks 集成**覆盖 Claude Code、Codex CLI、Gemini CLI 和 Grok CLI，无 Hooks 环境按规则降级执行。

### CLI 兼容性速查表

| CLI | 推荐版本 | 主要特性 | 配置说明 |
|-----|---------|---------|---------|
| **Claude Code** | 最新版 | Agent Teams、11 个生命周期钩子 | Agent Teams 模式需设置 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| **Codex CLI** | 0.110+ | spawn_agent、CSV 批量、enable_fanout | 启用子代理、CSV 编排，设置 `project_doc_max_bytes >= 131072` |
| **OpenCode** | 最新版 | Task tool、自定义代理、MCP | 支持主代理（build/plan）+ 子代理（general/explore） |
| **Gemini CLI** | 最新版 | 内置工具调用 | 降级为顺序执行 |
| **Qwen CLI** | 最新版 | 内置工具调用 | 降级为顺序执行 |
| **Grok CLI**（实验性）| 最新版 | 内置工具调用 | 社区封装，hooks 未完整验证 |

<details>
<summary>📋 各 CLI 详细说明（点击展开）</summary>

**Codex CLI 配置：**
- 启用子代理和 CSV 编排功能
- 在 config.toml 中设置 `project_doc_max_bytes = 131072`
- 配置 `developer_instructions` 以提升路由协议优先级
- 启用 `enable_fanout` 以使用 CSV 批量编排（v0.110+）
- 配置 `nickname_candidates` 以实现角色识别
- 为只读子代理角色配置 read-only role config；Codex CLI 当前不提供 PreToolUse 危险命令拦截
- 如使用并行工作流，配置 CSV 批量处理

**Claude Code 设置：**
- Agent Teams 模式需设置环境变量 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- 11 个生命周期钩子在安装时自动配置（SessionStart、UserPromptSubmit、SubagentStart/Stop、PostToolUse、Stop、TeammateIdle、PreCompact、PreToolUse、SessionEnd、PostToolUseFailure）
- 自动记忆功能在安装时关闭（防止与 AGENTS.md 规则冲突）

**其他 CLI：**
- OpenCode 支持 Task tool，含主代理（build/plan）和子代理（general/explore）
- Gemini/Qwen/Grok 使用顺序执行降级
- 不支持的功能会自动降级
- Hooks 可能在部分平台上不可用

</details>

## 快速开始

> **选择安装方式：**
> - **2.x/m 维护版** → 方式 A（UV，推荐）
> - **没有 UV** → 方式 B（pip）
> - **只想启动安装菜单** → 安装后执行 `helloagents`
> - **需要上游 3.x** → 显式安装上游 `main`，不要使用本页默认命令

> **前置要求：** 各 AI CLI（Codex CLI / Claude Code 等）需升级到支持子代理、CSV 编排等功能的版本。VSCode 插件通常晚于 CLI 发布，遇到功能不可用时优先使用终端版 CLI。

> ⚠️ **Windows PowerShell 5.1** 不支持 `&&` 连接符。请将 `&&` 两侧命令分开执行，或升级到 [PowerShell 7+](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows)。

### 方式 A：UV 安装 2.x/m 维护版（推荐）

**安装并选择目标 CLI：**

    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents

**只安装到 Codex：**

    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents install codex

**验证维护通道：**

    helloagents version --force --cache-ttl 0
    helloagents status

预期版本为 `2.4.3`，分支为 `dev/2.3.8`。

**更新：**

    helloagents update

`helloagents update` 使用 UV 安装时会自动附加 `--force --no-cache`，避免同版本维护分支更新时复用旧 wheel 缓存。

**本地源码重装（开发/验证时使用）：**

    uv tool install --force --no-cache "E:\code\python\helloagents"

**卸载：**

    uv tool uninstall helloagents

### 方式 B：pip 安装 2.x/m 维护版

**安装并选择目标 CLI：**

    python -m pip install --upgrade --no-cache-dir "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8"
    helloagents

**更新：**

    helloagents update

**卸载：**

    python -m pip uninstall helloagents

> 如果 pip 提示 `externally-managed-environment`，说明当前 Python 由 UV 管理。请改用方式 A。

### 方式 C：安装 UV（未安装时）

    # Windows PowerShell
    irm https://astral.sh/uv/install.ps1 | iex

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

> 安装 UV 后请重启终端以使 `uv` 命令生效。

### 方式 D：npm / npx 引导（不作为 2.x/m 默认方式）

    npx helloagents

`npx` 走 npm 发布通道，可能不是本仓库的 2.x/m 维护版。需要固定维护通道时，请使用方式 A 或方式 B。

### HelloAGENTS 命令（安装后可用）

> ⚠️ 以下命令依赖已安装的包。若远程更新导致异常，请使用上方对应安装方式的原生命令操作。

    helloagents                  # 交互式菜单
    helloagents install codex    # 直接指定目标
    helloagents install --all    # 安装到所有已检测的 CLI
    helloagents status           # 查看安装状态
    helloagents version          # 查看版本
    helloagents update           # 更新 + 自动同步所有目标
    helloagents update main      # 显式切换分支 + 自动同步
    helloagents uninstall codex  # 卸载指定目标
    helloagents uninstall --all  # 卸载所有目标
    helloagents clean            # 清理缓存

### Codex CLI 示例

**首次安装：**

    # UV
    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents install codex

    # pip
    python -m pip install --upgrade --no-cache-dir "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8"
    helloagents install codex

**后续更新（自动同步已安装目标）：**

    helloagents update

> ⚠️ **Codex CLI config.toml 兼容性说明：**
> - `[features]` `child_agents_md = true` — 实验性功能，可能与 HelloAGENTS 冲突
> - `project_doc_max_bytes` 过低 — 默认 32KB，AGENTS.md 会被截断（安装时自动设为 131072）
> - `agent_max_depth = 1` — 限制子代理嵌套深度，建议保持默认或 ≥2
> - `agent_max_threads` 过低 — 默认 6，较低值限制并行子代理调度（CSV 批量模式建议 ≥16）
> - `spawn_agent` 能力以当前 Codex 工具发现和 Collab 环境为准；初始工具列表未显示时，HelloAGENTS 会先执行工具发现，不直接判定为不可用
> - `[features]` `enable_fanout = true` — CSV 批量编排（spawn_agents_on_csv）必须启用
> - Collab 子代理调度需要启用 Codex CLI 对应功能开关
>
> **建议配置：**
> - 使用 Codex 0.110+，以启用 enable_fanout 和 nickname_candidates
> - HelloAGENTS 支持 `high` 及以下推理程度；不要使用 `xhigh`，否则可能影响规则跟随
> - 优先使用终端版 Codex。VSCode 插件通常晚于 CLI 发布，部分功能可能暂不可用

### Claude Code 示例

**首次安装：**

    # UV
    uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache
    helloagents install claude

    # pip
    python -m pip install --upgrade --no-cache-dir "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8"
    helloagents install claude

**后续更新：**

    helloagents update

> **Claude Code 子代理说明：**
> - 子代理（Agent tool）默认可用，无需额外配置
> - Agent Teams 协作模式需设置环境变量：`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
> - 并行子代理数量由模型自动管理，无需用户侧限制配置

## 配置

安装后可通过 `~/.helloagents/helloagents.json` 自定义工作流行为。只需包含要覆盖的键，缺省项使用默认值。

**配置项：**

| 键 | 类型 | 默认值 | 说明 |
|----|------|--------|------|
| `OUTPUT_LANGUAGE` | string | `zh-CN` | AI 输出和知识库文件的语言 |
| `KB_CREATE_MODE` | int | `2` | 知识库创建模式：`0`=关闭，`1`=按需（提示运行 ~init），`2`=代码变更时自动创建/更新，`3`=始终自动创建 |
| `BILINGUAL_COMMIT` | int | `1` | 提交信息语言：`0`=仅 OUTPUT_LANGUAGE，`1`=OUTPUT_LANGUAGE + 英文 |
| `EVAL_MODE` | int | `1` | 澄清提问模式：`1`=渐进式（每轮 1 题，最多 4 轮），`2`=一次性（所有未充分维度一起问，最多 2 轮） |
| `UPDATE_CHECK` | int | `72` | 更新检查缓存有效期（小时）：`0`=关闭 |
| `CSV_BATCH_MAX` | int | `16` | CSV 批量编排最大并发数：`0`=关闭，上限 64（仅 Codex CLI） |
| `NOTIFY_LEVEL` | int | `2` | 通知模式：`0`=关闭，`1`=桌面通知，`2`=声音通知，`3`=桌面+声音；统一通知会携带项目名和任务摘要，兼容旧键 `notify_level` |

通知由 `unified_notify.py` 统一处理。主代理完成、等待确认、警告或出错时，桌面通知和语音会尽量使用同一条短消息，例如 `完成了 - goedge - 登录功能`；无法使用系统语音时自动降级为内置事件音效。

**示例：**

```json
{
  "KB_CREATE_MODE": 0,
  "EVAL_MODE": 2
}
```

> 文件不存在或解析失败时静默跳过，使用默认值。未知键会输出警告并忽略。

### 常见配置场景

<details>
<summary>📝 纯英文项目</summary>

```json
{
  "OUTPUT_LANGUAGE": "en-US",
  "BILINGUAL_COMMIT": 0
}
```
所有 AI 输出、知识库文件和提交信息均为纯英文。
</details>

<details>
<summary>🚫 禁用自动创建知识库</summary>

```json
{
  "KB_CREATE_MODE": 0
}
```
知识库不会自动创建。需要时使用 `~init` 命令手动创建。
</details>

<details>
<summary>⚡ 高并发批量处理（Codex CLI）</summary>

```json
{
  "CSV_BATCH_MAX": 32
}
```
将 CSV 批量并行处理数从 16 提升到 32（最大 64）。需要 Codex CLI 启用 CSV 编排功能。
</details>

<details>
<summary>🔕 禁用更新检查</summary>

```json
{
  "UPDATE_CHECK": 0
}
```
完全跳过版本更新检查（不建议在生产环境使用）。
</details>

<details>
<summary>💬 一次性澄清模式</summary>

```json
{
  "EVAL_MODE": 2
}
```
一次性询问所有未充分维度的澄清问题（最多 2 轮），而非渐进式（每轮 1 个问题，最多 4 轮）。
</details>

## 工作原理

**简单来说：** HelloAGENTS 根据任务复杂度自动选择处理深度，简单问题快速响应，复杂任务走完整的评估→设计→开发流程，全程有安全检查和记忆保留。

**详细流程：**

1. **安装部署** — 运行 `helloagents` 选择目标 CLI，自动部署配置文件和钩子
2. **路由判定** — 每条输入按规则评分，简单问题直接回答，复杂任务进入结构化流程
3. **阶段推进** — 复杂任务按"评估→设计→开发"阶段链推进，每个阶段有明确交付物
4. **自动编排** — 系统根据独立工作单元和并行收益自动调度子代理和专业角色，可并行时自动并行
5. **安全防护** — 每步扫描破坏性操作，高风险动作需用户确认；支持 PreToolUse 的 CLI 会执行前拦截典型危险命令
6. **记忆保留** — 用户偏好、项目知识、会话上下文跨会话持续保留
7. **验证完成** — 阶段链以验证通过的输出完成，自动同步知识库

## 聊天内工作流命令

以下命令在 AI 聊天中使用，而非系统终端。

**常用命令：**

| 命令 | 用途 |
|------|------|
| ~auto | 全自动工作流 |
| ~plan | 规划并生成方案包 |
| ~exec | 执行已有方案包 |
| ~build | 智能构建（有方案包则执行，无则按需路由实现） |
| ~init | 初始化知识库 |
| ~ssh | 初始化/更新项目服务器、环境、路径和运行命令配置 |
| ~commit | 根据上下文生成提交信息 |
| ~status / ~help | 状态与帮助 |

**质量检查：**

| 命令 | 用途 |
|------|------|
| ~test | 运行项目测试 |
| ~review | 代码审查 |
| ~verify | 审查+验证+自动修复+收尾（~review 超集） |
| ~validatekb | 验证知识库 |
| ~loop | 循环改进直到质量指标达标 |

**产品与探索：**

| 命令 | 用途 |
|------|------|
| ~idea | 轻量技术探索与方向对比（只读分析，不写文件） |
| ~prd | 交互式生成产品需求文档 |

**高级功能：**

| 命令 | 用途 |
|------|------|
| ~wiki | 知识库创建与同步（~init 的 KB 子集） |
| ~upgradekb | 升级知识库结构 |
| ~clean / ~cleanplan | 清理与归档工作流产物 |
| ~rollback | 回滚工作流状态 |
| ~rlm | 角色编排（spawn / agents / resume / team） |

## 使用指南

### 三种工作流模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `~auto` | 从需求到实现的全自动流程（评估→设计→开发→验证） | 需求明确，希望直接推进到验证结果 |
| `~plan` | 仅规划，生成方案包后停止，不写代码 | 想先审查方案再决定是否实施 |
| `~exec` | 跳过评估和设计，直接执行已有方案包 | `~plan` 审查通过后继续实施 |
| `~build` | 智能入口：有方案包时等价 `~exec`，无方案包时按需路由 | 不确定是否已有方案包，统一入口 |

典型工作流：先 `~plan` 生成方案 → 审查确认 → `~exec` 执行实施。也可直接 `~auto` 一步完成，或用 `~build` 自动判断。

### 交互模式与委托模式

`~auto` 或 `~plan` 确认时可选择执行模式：

- **交互模式（默认）：** 在关键决策点暂停等待确认（方案选择、失败处理等）
- **委托模式（全自动）：** 自动推进所有阶段，自动选择推荐选项，仅在 EHRB 风险检测时中断
- **仅规划委托：** 全自动但止步于设计阶段，不进入开发

不使用 `~` 命令时，直接输入需求会自动路由至 R0–R2 级别处理。

### 需求评估与追问

R2 任务进入执行前，系统会对需求进行四维评分（需求范围 0–3、成果规格 0–3、实施条件 0–2、验收标准 0–2）。通过条件基于核心维度充分性（需求范围 ≥ 3、实施条件 ≥ 1、成果规格 ≥ 1），而非固定总分阈值。未达充分线时触发追问：

- `EVAL_MODE=1`（默认，渐进式）：每轮问 1 个未达充分线的维度，最多 4 轮
- `EVAL_MODE=2`（一次性）：所有未达充分线的维度一起问，最多 2 轮

最后一轮追问会与确认合一输出（追问 + 执行模式选择），减少独立确认环节。已有代码库中可推断的上下文会自动计入评分。如果需求已经足够明确，可以说"跳过评估 / 直接做"跳过追问环节。

### 设计阶段并行方案

R2 标准流的设计阶段会派发 3–6 个子代理，各自独立生成竞争性实现方案。主代理从用户价值、方案合理性、风险（含 EHRB）、实现成本四个维度评估所有方案，权重根据项目特征动态调整（如性能敏感项目提高合理性权重，MVP 项目提高成本权重）。

- 交互模式：用户选择方案或要求重新生成（最多 1 次重试）
- 委托模式：自动选择推荐方案
- R2 标准流中复杂任务走多方案比较，简单任务跳过多方案比较直接进入规划

### 轻量设计路径

当 R2 任务满足以下条件时，自动进入轻量路径，跳过方案包创建：

- TASK_COMPLEXITY = simple 且涉及文件 ≤ 3 且预估改动 ≤ 30 行

轻量路径行为：跳过 proposal.md / tasks.md 创建，输出 ≤ 200 字的方案摘要后直接进入 DEVELOP。仅当任务确认为单一工作单元时由主代理直接执行；若识别出 ≥2 个独立工作单元且并行收益明确，则按 G10 编排子代理或回退标准路径。验证仍按 R1 验收标准执行，探测项目工具后可用则运行，并跳过完整交付验收。条件不满足时自动回退到标准路径。

### 开发阶段自动依赖管理

开发阶段会自动检测项目的包管理器（通过 lockfile 识别：`yarn.lock` → yarn、`uv.lock` → uv、`Gemfile.lock` → bundler 等），并处理依赖问题：

- 已声明但缺失的依赖：自动安装
- 任务需要的新依赖：自动添加并更新依赖声明文件
- 不确定的依赖：询问用户后再安装

### 质量验证（Ralph Loop 与 Break-loop）

**Ralph Loop**（Claude Code，通过 SubagentStop Hook）：子代理完成代码修改后，自动运行项目验证命令。验证失败时阻断子代理退出，要求修复（最多 1 次重试循环）。验证命令来源优先级：`.helloagents/runbook.yaml` → `.helloagents/verify.yaml` → `package.json` scripts → 自动检测。

**Break-loop**（深度根因分析）：当任务经过 Ralph Loop + 至少 1 次手动修复仍反复失败时触发，执行五维根因分析：

1. 根因分类（逻辑错误 / 类型不匹配 / 缺失依赖 / 环境问题 / 设计缺陷）
2. 为什么之前的修复没有生效
3. 预防机制建议
4. 系统性扫描——其他模块是否存在同类问题
5. 经验教训记录到验收报告

### 提交辅助（~commit）

`~commit` 不只是生成提交信息，还包括：

- 分析 `git diff` 自动生成 Conventional Commits 格式的提交信息
- 预提交质量检查（代码-文档一致性、测试覆盖、验证命令）
- 自动排除敏感文件（`.env`、`*.pem`、`*.key` 等），不会执行 `git add .`
- 并行/多线程任务按任务级 hunk/patch 隔离；同文件混合改动标记为 mixed-file，不做整文件暂存
- commit 锁只覆盖任务级暂存、cached diff 审查和提交；patch 失败最多重建一次，禁止全局 index 清理
- 提交前展示文件清单，支持排除
- 可选：仅本地提交 / 提交+推送 / 提交+推送+创建 PR
- `BILINGUAL_COMMIT=1` 时生成双语提交信息

### 循环改进（~loop）

设置一个质量指标和守卫命令（如"测试覆盖率 >= 80%"），系统自动循环执行改进+验证直到达标：

- 每轮自动执行改进→运行验证命令→检查是否达标
- 达标、达最大轮次（默认 5）或连续 2 轮无进步时自动停止
- 支持每轮回滚（验证失败时撤销本轮改动）
- 适用场景："提高测试覆盖率到 90%"、"修复所有 lint 错误"

### 技术探索（~idea）

纯只读的轻量分析，不写文件、不修改代码、不创建方案包：

- 对比 2–4 个技术方向，评估可行性、风险和生态兼容性
- 适用场景：技术选型前的快速探索、"这样做行不行"类问题
- 输出多方向对比表格 + 推荐方向

### 产品需求文档（~prd）

交互式生成结构化 PRD，逐维度讨论（产品概述、功能范围、用户场景、技术约束、验收标准），每个维度一个回合，最后生成完整 PRD 写入 `plan/` 目录。支持交互式和全自动两种模式。

### 全面验证（~verify）

`~review` 的超集，覆盖审查→验证→自动修复→收尾全流程：

- 代码审查（Critical/Warning/Info 分级）
- 运行 lint/类型检查/测试/构建
- 失败时自动修复（最多 3 轮）
- 生成验证报告 + 写入 CHANGELOG
- 无参数时自动检测最近变更

### 手动调用子代理角色

除自动调度外，可手动指定角色执行任务：

    ~rlm spawn reviewer "审查 src/api/ 的安全性"
    ~rlm spawn writer "生成 API 接口文档"
    ~rlm spawn reviewer,writer "分析并记录认证模块"   # 并行多角色

可用角色：`reviewer`（代码审查）、`writer`（文档撰写）、`brainstormer`（多方案构思对比）。

### 多终端协作

多个终端（可跨不同 CLI）共享任务列表协同工作：

    # 终端 A
    hellotasks=my-project codex

    # 终端 B
    hellotasks=my-project claude

启用后可用命令：

    ~rlm tasks                  # 查看共享任务列表
    ~rlm tasks available        # 查看可认领任务
    ~rlm tasks claim <id>       # 认领任务
    ~rlm tasks complete <id>    # 标记完成
    ~rlm tasks add "任务标题"    # 添加新任务

任务存储在 `{KB_ROOT}/tasks/` 下，通过文件锁防止并发冲突。

### KB 自动同步与 CHANGELOG

知识库在以下时机自动同步：

- 每个开发阶段完成后，主代理同步模块文档以反映实际代码
- 每个 R1/R2 任务完成后，CHANGELOG 自动追加条目
- 会话结束时（Claude Code Stop Hook），异步设置 KB 同步标志

CHANGELOG 使用语义版本号（X.Y.Z），版本来源优先级：用户指定 → 项目文件（package.json、pyproject.toml 等，支持 15+ 语言/框架）→ git tag → 上一条 CHANGELOG 条目 → 0.1.0。R1 快速路径的变更记录在"快速修改"分类下，附带 file:line 范围。

`KB_CREATE_MODE` 控制自动行为：`0`=关闭、`1`=按需提示、`2`=代码变更时自动（默认）、`3`=始终自动。

### Worktree 隔离

当多个子代理需要同时修改同一文件的不同区域时（仅 Claude Code），系统自动使用 `Task(isolation="worktree")` 为每个子代理创建独立的 git worktree，避免 Edit 工具冲突。主代理在合并阶段统一合并所有 worktree 的变更。仅在子代理有文件写入重叠时启用，只读任务不使用。

### CSV 批量编排（Codex CLI）

当同一执行层存在 ≥6 个结构相同的任务时，系统自动将 `tasks.md` 转为任务 CSV，通过 `spawn_agents_on_csv` 并行派发。每个 worker 接收各自的行数据 + 指令模板，独立执行并汇报结果。

- 进度通过 `agent_job_progress` 事件实时追踪（pending/running/completed/failed/ETA）
- 状态持久化到 SQLite，支持崩溃恢复
- 部分失败仍导出结果，附带失败摘要
- 异构任务自动回退到 `spawn_agent` 逐个派发
- 通过 `CSV_BATCH_MAX` 配置并发上限（默认 16，最大 64，设为 0 关闭）

### 更新检查

每次会话首条响应时，系统静默检查是否有新版本可用。检查结果缓存在 `~/.helloagents/.update_cache`，有效期由 `UPDATE_CHECK` 配置（默认 72 小时，设为 0 关闭）。有新版本时在响应末尾显示 `⬆️ 新版本 {version} 可用`。检查过程中的任何错误都会静默跳过，不影响正常使用。

带 `+m` / `-m` 标识的维护版（例如发布标识 `2.3.9-m`，Python 元数据 `2.3.9+m`）默认跟随当前安装的维护分支。2.x/m 通道默认检查 `dev/2.3.8`，不再自动对比 `main` / 最新 3.x release；只有显式执行 `helloagents update <branch>` 时才切换到指定分支。

## 仓库结构

- AGENTS.md：路由与工作流协议
- SKILL.md：CLI 目标的技能发现元数据
- pyproject.toml：包元数据（v2.4.3）
- helloagents/cli.py：CLI 入口
- helloagents/_common.py：共享常量与工具函数
- helloagents/core/：CLI 管理模块（安装、卸载、更新、状态、调度器、钩子设置）
- helloagents/functions：命令定义（22 个）
- helloagents/stages：设计、开发阶段定义
- helloagents/services：知识库、方案包、记忆等核心服务
- helloagents/rules：状态机、缓存、工具、扩展、子代理协议
- helloagents/rlm：角色库与编排辅助
- helloagents/hooks：Claude Code、Codex CLI、Gemini CLI、Grok CLI Hooks 配置
- helloagents/scripts：自动化脚本（统一通知、进度快照、安全防护等）
- helloagents/agents：子代理定义（3 个 RLM 角色）
- helloagents/assets：音频资源（5 种事件音效）
- helloagents/templates：KB 和方案模板

## FAQ

**问：这是 Python CLI 工具还是提示词包？**

答：两者兼有。CLI 负责安装和更新管理，工作流行为来自 AGENTS.md 和文档文件。可以理解为：CLI 分发工具 + 工作流规则包。

**问：应该安装哪个目标？**

答：选择你正在使用的 CLI：`codex`（Codex CLI）、`claude`（Claude Code）、`gemini`（Gemini CLI）、`qwen`（Qwen CLI）、`grok`（Grok CLI）或 `opencode`（OpenCode）。可以用 `helloagents install --all` 安装到所有目标。详见[CLI 兼容性速查表](#cli-兼容性速查表)。

**问：如果规则文件已存在怎么办？**

答：HelloAGENTS 会在替换前自动备份非 HelloAGENTS 文件。备份带时间戳，存储在 CLI 配置目录中，随时可以恢复。

**问：什么是 RLM？**

答：Role Language Model——HelloAGENTS 的子代理编排系统。包含 3 个专业角色（reviewer、writer、brainstormer）+ 原生 CLI 子代理。任务通过 DAG 依赖分析调度，可并行时自动并行。详见[使用指南](#使用指南)。

**问：项目知识存储在哪里？**

答：在项目本地的 `.helloagents/` 目录中。知识库在代码变更时自动同步（由 `KB_CREATE_MODE` 配置控制）。包含模块文档和 CHANGELOG。详见 [KB 自动同步与 CHANGELOG](#kb-自动同步与-changelog)。

**问：知识库能跨会话保留吗？**

答：能。项目知识库存于项目本地 `.helloagents/` 目录中，即使关闭重开 CLI，上下文依然保留。

**问：什么是 Hooks？**

答：安装时自动部署的生命周期钩子。Claude Code 有 11 个事件钩子（安全检查、危险命令防护、进度快照、KB 同步、统一通知、工具失败恢复等）；Codex CLI 有 notify 钩子用于更新检查和统一通知，目前没有执行前危险命令拦截钩子；Gemini CLI 有 6 个钩子（上下文注入、进度快照、统一通知、压缩前快照）；Grok CLI 有 3 个钩子（上下文注入、安全防护、进度快照）。全部可选——无 Hooks 时功能自动降级，无需手动配置。

**问：什么是 Agent Teams？**

答：Claude Code 实验性功能，多个 Claude Code 实例作为队友协作，共享任务列表和邮箱通信。通过 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 启用。不可用时回退到标准 Task 子代理。详见[多终端协作](#多终端协作)。

## 故障排除

### 命令未找到

**问题：** 安装后提示 `helloagents: command not found`

**诊断：** 安装路径未加入系统 PATH

**解决：**
- UV：安装 UV 后重启终端
- pip：用 `pip show helloagents` 查看安装位置，添加到 PATH
- 验证：`which helloagents`（Unix）或 `where helloagents`（Windows）

**验证：** 运行 `helloagents version`

---

### 版本号未知

**问题：** 版本显示为"unknown"

**诊断：** 包元数据不可用

**解决：** 先安装包：`uv tool install --from "git+https://github.com/Micah123321/helloagents.git@dev/2.3.8" helloagents --force --no-cache`，或使用 pip 安装维护分支

**验证：** 运行 `helloagents version` 应显示当前版本号

---

### 目标未检测到

**问题：** 安装时找不到 CLI 目标

**诊断：** 配置目录尚不存在

**解决：** 先启动目标 CLI 至少一次以创建配置目录，然后重试 `helloagents install <target>`

**验证：** 检查配置路径：
- Codex CLI：`~/.codex/`
- Claude Code：`~/.claude/`
- 其他：参见 CLI 文档

---

### 自定义规则被覆盖

**问题：** 自定义规则被 HelloAGENTS 替换

**诊断：** 安装时替换现有文件

**解决：** 从 CLI 配置目录中的时间戳备份恢复（如 `~/.codex/AGENTS_20260304132146_bak.md`）

**验证：** 检查配置目录中的备份文件

---

### 图片不显示

**问题：** README 图片无法显示

**诊断：** 图片文件缺失或路径错误

**解决：**
- 保持 README 中的相对路径（如 `./readme_images/`）
- 确保 `readme_images/` 文件夹已提交到仓库
- 验证图片文件本地存在

**验证：** 检查 `ls readme_images/` 显示所有引用的图片

---

### CCswitch 切换后配置丢失

**问题：** 切换 CCswitch 配置方案后，HelloAGENTS 不工作（工作流命令无法识别、钩子不触发、规则缺失）

**诊断：** CCswitch 切换配置方案时会替换整个 CLI 配置目录（如 `~/.claude/`），覆盖了 HelloAGENTS 的钩子、权限和规则文件

**解决：** 切换 CCswitch 配置方案后，运行以下任一命令恢复 HelloAGENTS：

    helloagents install claude    # 重新安装到指定 CLI 目标
    helloagents update            # 更新 + 自动同步所有已安装目标

**预防：** v2.3.5 起新增会话启动时自动配置完整性检测——如果 HelloAGENTS 配置缺失或损坏，会显示警告和恢复指引

**验证：** 运行 `helloagents status` 确认所有目标显示为已安装

---

### CCswitch 配置冲突

**问题：** 卸载 HelloAGENTS 后切换 CCswitch 配置方案时配置重新出现

**诊断：** CCswitch 在卸载前保存了 HelloAGENTS 设置

**解决：** 卸载 HelloAGENTS 后，手动清理所有已保存 CCswitch 配置方案中的 HelloAGENTS 相关设置（hooks、permissions、rules）

**验证：** 检查 CCswitch 配置方案目录中是否有 HelloAGENTS 残留

## 版本历史

### v2.4.3（当前）

**子代理编排优化：**
- 自动编排原则新增 CLI 一致性声明：Claude Code 与 Codex 满足触发条件（≥2 个独立工作单元）时均主动编排子代理，仅调用通道和环境前置不同
- 各 CLI 的稳定性策略与降级阈值定位为编排失败后的兜底，不构成编排前回避子代理的理由
- Codex 子代理协议新增「主动编排触发点」节，覆盖 DESIGN 扫描/构思、DEVELOP 实现/测试、~review/~validatekb/~init 等场景，突出 CSV 批处理为 Codex 独有高吞吐通道
- 稳定性策略重定位为失败后兜底，连续失败和上下文预算阈值标注为失败统计而非预判回避

**Codex 子代理模型默认：**
- 子代理默认继承主代理模型（角色配置不设 model），与 Claude Code 的 model: inherit 默认对齐
- codex_roles.py 创建角色节时刻意不写 model 并保留用户已设 model，只读 config_file 不含 model 以保持继承
- 参考配置示例从按角色分轻量/主力模型改为默认继承，差异化降级降为可选优化

### v2.4.2

**提示词优化：**
- 新增最小化阶梯（编码前 7 步自检：YAGNI→复用→标准库→原生→依赖→精简→最少代码）
- 新增简化标注注释（`ha-min:` 约定，标记有意简化的上限和升级路径）
- 新增过度工程禁止规则（禁止一个实现者的接口、猜测性脚手架、冗余配置项等）
- 产出标准补充 YAGNI 约束和非平凡代码自检要求
- 审查维度扩展简化/过度工程维度，使用标准化标签体系（delete/stdlib/native/yagni/shrink）

**统一通知：**
- 新增 `unified_notify.py` 统一通知入口，声音和桌面通知共用项目名与任务摘要，支持 `完成了 - helloagents - 当前任务` 这类短上下文消息
- Codex `notify`、Claude Stop 和 Gemini AfterAgent Hook 统一转发到新入口；IDE 来源的 Codex 通知继续静默跳过
- 默认声音通知优先使用系统 TTS 播放动态上下文，失败时降级到内置事件音效；桌面通知沿用同一条消息
- Windows Toast 通知改用 `-EncodedCommand` 传递 XML，避免通知内容被 PowerShell 当作命令语法解析

**工作流体验：**
- 完成态 `🔄 下一步` 支持 2-4 个编号动作，优先给出审查、提交/验证和基于本次改动的具体延伸动作
- `~commit` 在用户确认提交方式后只展示安全暂存清单，不再对同一暂存范围二次确认；敏感文件、空清单、冲突或 EHRB 风险仍会暂停

**2.4.0 后续增强汇总：**
- 新增 `~ssh` 和 ProjectEnvService，可记录项目环境、host 引用、远程路径、runbook 验证命令和敏感凭据引用边界
- 增强 `~test`/Ralph Loop 的 runbook 解析，支持项目别名、默认 `latest_commit_fixes` workflow，并跳过远程、生产或模板占位符命令
- `~review 审查本次改动` 可直接识别最近改动范围，审查发现问题后默认创建并执行保守修复方案
- R2 最后一轮追问与执行模式确认合一，确认类 pending 回复支持中断恢复和“继续/确认/开始审查”等语义匹配
- 方案包归档会同步 tasks.md、LIVE_STATUS 和 `.status.json` 状态，减少归档后的手动修正
- Codex 只读子代理使用独立 role config 收紧权限边界，文档同步明确 Hook 能力和安全边界

### v2.4.0

**新增 6 个工作流命令（命令总数 15→21）：**
- `~idea`：轻量技术探索与方向对比，纯只读分析（不写文件、不创建方案包），适用于技术选型前的快速评估
- `~build`：`~exec` 的超集，有方案包时执行方案包，无方案包时按需路由实现，统一构建入口
- `~prd`：交互式生成结构化产品需求文档（PRD），逐维度讨论后输出完整 PRD 到 `plan/` 目录
- `~loop`：循环改进，设置质量指标+守卫命令后自动循环执行改进→验证，直到达标或达最大轮次
- `~wiki`：纯知识库管理（`~init` 的 KB 子集），只处理知识库创建/同步，不涉及 rules 和 skills 链接
- `~verify`：`~review` 的超集，覆盖审查→运行验证→自动修复（最多 3 轮）→生成报告+写入 CHANGELOG 全流程

**轻量执行路径：**
- 新增 R1 快判锚点：已知位置单点修改、已知命令执行、已知模式复制三种模式可快速判定 R1，减少简单任务被误路由到 R2
- 新增 LIGHTWEIGHT_DESIGN 轻量设计路径：R2 simple 且涉及文件 ≤3 且改动 ≤30 行时，跳过方案包创建，基于轻量方案摘要直接进入 DEVELOP，降低小任务流程开销

**~clean 命令扩展：**
- 升级为"清理与归档"，新增方案包归档能力：扫描已完成方案包，通过 `migrate_package.py` 迁移至 `archive/YYYY-MM/`（而非直接删除）
- 用户选项更细粒度：全部清理+归档、仅清理缓存、仅归档方案包、选择性处理

**工作流规则增强：**
- 新增 GPT 反模式规则，治理拆单交付、套话收尾和留一手行为
- 新增产出标准、语言表述、技术选型、静默失败防护、阻塞判定和 UI 验收质量基线
- 新增前端文案净化规则：禁止在组件属性（title/subtitle/description/tooltip 等）中写入功能说明或产品描述性文本，约束从子代理 prompt 模板、开发阶段指令、审查清单到项目指南模板形成完整链路
- 回移第一批计划设计增强：证据驱动假设、方案取舍、验证策略和更完整的方案包模板

**测试与基础设施：**
- 新增 3 个测试文件：updater Windows 锁文件处理、CLI 恢复路径、版本检查多格式解析
- 安装脚本（install.sh / install.ps1）默认使用维护分支，支持 `HELLOAGENTS_BRANCH` 环境变量覆盖
- CONTRIBUTING.md 更新为 package-first 结构声明

### v2.3.9-m

**维护通道：**
- 发布 2.x/m 维护版 `v2.3.9-m`，Python 包元数据使用符合 PEP 440 的 `2.3.9+m`
- 维护版更新检测默认跟随当前安装来源和分支；2.x/m 无显式分支时回退到 `dev/2.3.8`
- 2.x/m 通道不再因为 `main` / 最新 3.x release 触发默认更新提示
- `helloagents update <branch>` 仍保留显式切换分支能力
- UV 安装和更新统一使用 `--force --no-cache`，避免同版本维护分支复用旧 wheel 缓存

**工作流规则增强：**
- 新增 GPT 反模式规则，治理拆单交付、套话收尾和留一手行为
- 新增产出标准、语言表述、技术选型、静默失败防护、阻塞判定和 UI 验收质量基线
- 新增前端文案净化规则：禁止在组件属性（title/subtitle/description/tooltip 等）中写入功能说明或产品描述性文本，约束从子代理 prompt 模板、开发阶段指令、审查清单到项目指南模板形成完整链路
- 回移第一批计划设计增强：证据驱动假设、方案取舍、验证策略和更完整的方案包模板

### v2.3.8

**架构变更：**
- 路由层级合并：删除 R2 简化流程和 R3 标准流程，统一为 R0/R1/R2 三层路由。新 R2 标准流程合并原 R2+R3 的适用场景
- 评估追问改为维度充分性驱动（需求范围 ≥ 3、实施条件 ≥ 1、成果规格 ≥ 1），替代固定总分阈值（原"评分 ≥ 8"）
- 最后一轮追问与确认合一：追问 + 执行模式选择在同一回合输出，减少独立确认环节
- DESIGN 多方案对比改为按 TASK_COMPLEXITY 条件触发（complex → 多方案对比，simple/moderate → 跳过），替代按路由级别触发
- 移除 L0 用户记忆系统和自定义命令扩展（`user/` 目录）：简化为单层项目知识模型（仅 L1 项目知识库）
- 配置系统整合：从两级优先级配置（项目级 + 全局级 `config.json`）迁移到单一 `~/.helloagents/helloagents.json`，安装时自动同步
- 新增代码体积控制规则：警告阈值（文件/类 300 行，函数 40 行），强制拆分阈值（文件/类 400 行，函数 60 行）

**新增功能：**
- 新增 5 个工作流命令：`~test`、`~rollback`、`~validatekb`、`~upgradekb`、`~cleanplan`
- 新增 notify_level 配置项（0=关闭, 1=桌面通知, 2=声音, 3=两者）控制通知行为
- 新增独立配置读取模块（`scripts/_config.py`）供 hook 脚本使用
- brainstormer 子代理输出格式增强：新增 `key_findings` 字段用于方案亮点摘要

**安全修复：**
- 修复 shared_tasks.py 路径注入漏洞：环境变量 `list_id` 在用于文件路径前进行清洗
- 修复 validate_package.py 路径遍历防护不完整：`relative_to()` 失败时现在正确退出而非继续执行

**Bug 修复：**
- 修复 Gemini/Grok hooks PostToolUse 匹配器缺少 NotebookEdit（现为 `Write|Edit|NotebookEdit`，与 Claude Code 一致）
- 修复 pre_compact.py 仍使用已废弃的 LIVE_STATUS HTML 注释，迁移到 .status.json（与 progress_snapshot.py 一致）
- 修复 pre_compact.py `_get_current_task` 正则仅匹配编号列表，现支持无序列表
- 修复 progress_snapshot.py 文档注释错误标注 Grok 为 async=true（实际配置为 async=false）
- 修复 dispatcher 更新检查 cache_ttl 默认值从 None 改为 72 小时
- 修复 utils.py 将 Python 包源码目录误判为旧版知识库目录的问题
- 修复 cli.py 错误恢复时将参数误传为分支名的问题

**改进优化：**
- Codex CLI 功能标志更新：`sqlite`+`collaboration_modes` 替换为 `enable_fanout`（CSV 批量编排）
- codex_notify.py 新增 Windows UTF-8 编码块（其他 hook 脚本已有）
- stop_sound_router.py UTF-8 编码扩展覆盖 stdout/stderr（此前仅 stdin）
- 所有有意重复的函数添加 NOTE 注释，标注跨文件同步要求
- 新增年度变更日志归档模板（`CHANGELOG_{YYYY}.md`）

### v2.3.7

**Bug 修复：**
- 修复非编码任务在 KB_CREATE_MODE=2 时错误创建知识库的问题（design.md Phase1 步骤1 增加编程任务判定）
- 修复 R2 标准流程选方案后出现归档而非进入开发实施的问题（阶段切换规则约束 overview 类型仅限 ~exec 入口）
- 修复非编码任务错误创建方案包的问题（package.md create() 接口增加编程任务前置条件）

**改进优化：**
- 优化上下文压缩后的实施方案状态恢复
- 优化整个设计流程

### v2.3.6

**新增功能：**
- 子代理编排体系重构：新增方案构思子代理（brainstormer），DESIGN 多方案对比阶段支持独立子代理并行构思
- 子代理阻塞机制：子代理调用失败或超时时自动阻断并降级为主代理执行

**改进优化：**
- 工具/Shell 约束规则优化：内置工具执行失败时允许降级为 Shell（解决 Codex CLI Windows apply_patch 反复失败问题）
- Shell 编码约束精确化：明确 UTF-8 无 BOM 要求，区分 PowerShell 读取/写入场景的编码处理
- 新增批量文件写入规则（≥3 文件合并为临时脚本一次执行，避免沙箱逐个拦截）
- 移除 CLI 无法完全落地的 session 记忆功能（session_summary 模板、SessionEnd 记忆同步），精简服务层
- 子代理精简：移除 3 个冗余子代理（kb-keeper、pkg-keeper、synthesizer），功能回归主代理和 RLM 角色
- 子代理语音通知跳过、任务稳定性修复
- 卸载脚本增强
- 视觉验证缺失和 UI 质量差距修复

### v2.3.5

**新增功能：**
- 语音提示系统，支持 5 种事件语音（完成、空闲、确认、错误、警告），跨平台支持 Windows/macOS/Linux，智能两层声音路由（stop_reason + G3 格式图标检测）
- Claude Code 生命周期钩子从 9 个扩展到 11 个事件类型：新增危险命令防护（PreToolUse）、会话结束清理（SessionEnd）、工具失败恢复建议（PostToolUseFailure）
- Hooks 支持扩展到 Gemini CLI（SessionStart、BeforeAgent/AfterAgent、PreCompress、PreToolUse、PostToolUse）和 Grok CLI（UserPromptSubmit、PreToolUse、PostToolUse）
- Codex CLI 0.110 新功能：`enable_fanout` CSV 批量编排、`nickname_candidates` 代理角色识别
- 会话启动时自动配置完整性检测（自动发现配置被 CCswitch 等工具替换的情况）
- 上下文压缩前自动保存进度快照（pre_compact.py、progress_snapshot.py——从占位 Hook 升级为完整实现）
- 用户自定义工具注册发现 + 编排整合机制——智能调用用户自定义的子代理、skills、MCP 服务器和插件

**改进优化：**
- 全面审计修复（21 个问题：6 HIGH + 9 MEDIUM + 6 LOW）
  - 代码质量：提取 5 个共享工具函数，消除循环依赖
  - 跨平台：统一平台判断，一致的编码处理
  - 安全性：配置覆盖前备份，占位符验证
  - 文档：配置说明，兼容性验证记录
- 核心架构新增：调度器模块、Codex 角色定义、Claude 规则管理、Hooks 设置管理器
- 安装/更新脚本重构，支持持久化配置
- 语音通知准确度提升，减少误报（Codex 客户端过滤、Windows 同步播放）
- 子代理昵称跨 CLI 优化
- Codex CLI 交互菜单启用、持久记忆和上下文压缩优化
- R2 流程优化与评估模块重新融合
- 上下文压缩状态持久性优化
- 工具/Shell 使用优化
- CCswitch 兼容性说明，卸载后配置清理提醒
- SKILL 发现入口优化

### v2.3.4

- 超长脚本拆分：3 个超 450 行的文件拆为 6 个独立模块
- CLI 管理脚本统一收纳至 core/ 子包（9 个模块）
- 共享常量与工具函数提取为独立模块，消除循环依赖
- 清理冗余兼容性重导出
- Codex CLI 路由协议权限提升，防止被系统提示词覆盖

### v2.3.0

- 全面交叉审计修复：角色输出格式统一、路径引用规范化、文档与代码一致性对齐
- 质量验证循环（Ralph Loop）：子代理完成后自动验证，失败时阻断并反馈
- 子代理上下文自动注入与主代理规则强化
- 深度五维根因分析（break-loop）应对重复失败
- 开发前自动注入项目技术规范
- 提交前质量检查（代码-文档一致性、测试覆盖、验证命令）
- Worktree 隔离支持并行编辑
- CHANGELOG 条目自动追加 Git 作者信息

## 参与贡献

详见 CONTRIBUTING.md 了解贡献规则和 PR 检查清单。

## 许可证

本项目双重许可：代码采用 Apache-2.0，文档采用 CC BY 4.0。详见 [LICENSE.md](./LICENSE.md)。

## 下一步

**快速开始：**
- 使用你喜欢的方式安装 HelloAGENTS：[快速开始](#快速开始)
- 用简单任务试试 `~auto`，体验完整工作流
- 尝试 `~plan` + `~exec` 获得更多控制权

**深入学习：**
- 阅读[使用指南](#使用指南)了解详细工作流模式
- 查看[配置](#配置)自定义行为
- 参考[聊天内工作流命令](#聊天内工作流命令)

**社区与支持：**
- 如果 HelloAGENTS 对你有帮助，可以给项目点 Star
- 在 [GitHub Issues](https://github.com/Micah123321/helloagents/issues) 报告问题或请求功能
- 参与贡献改进：参见 [CONTRIBUTING.md](./CONTRIBUTING.md)

---

<div align="center">

如果本项目对你的工作流有帮助，可以给项目点 Star。

感谢 <a href="https://codexzh.com/?ref=EEABC8">codexzh.com</a> / <a href="https://ccodezh.com">ccodezh.com</a> 对本项目的支持

</div>
