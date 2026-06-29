# 子代理调用协议

本模块定义各 CLI 的子代理调用通道、编排范式和调度规则。

---

## 调用协议

### RLM 角色定义

```yaml
RLM（Role-based Language Model）: HelloAGENTS 的角色子代理系统，通过预设角色调度专用子代理。
角色清单: reviewer, writer, brainstormer
Claude Code agent 文件（安装时部署至 ~/.claude/agents/）:
  reviewer → ha-reviewer.md | writer → ha-writer.md | brainstormer → ha-brainstormer.md
原生子代理映射（角色→类型映射，调用语法详见各 CLI 调用协议）:
  代码探索 → Codex: spawn_agent(agent_type="explorer") | Claude: Agent(subagent_type="Explore") | OpenCode: @explore | Gemini: codebase_investigator | Qwen: general-purpose
  代码实现 → Codex: spawn_agent(agent_type="worker") | Claude: Agent(subagent_type="general-purpose") | OpenCode: build（主代理） | Gemini: generalist | Qwen: general-purpose
  测试运行 → Codex: spawn_agent(agent_type="worker") | Claude: Agent(subagent_type="general-purpose") | OpenCode: build（主代理） | Gemini: 自定义子代理 | Qwen: 自定义子代理
  方案构思 → Codex: spawn_agent(agent_type="brainstormer") | Claude: Agent(subagent_type="ha-brainstormer") | OpenCode: @general | Gemini: generalist | Qwen: general-purpose
  监控轮询 → Codex: spawn_agent(agent_type="monitor") | Claude: Agent(run_in_background=true) | OpenCode: — | Gemini: — | Qwen: —
  批量同构 → Codex: spawn_agents_on_csv | Claude: 多个并行 Task | OpenCode: 多个 Task tool 调用 | Gemini: 多个子代理 | Qwen: 多个子代理
调用方式: 阶段文件中标注 [RLM:角色名] 的位置必须调用角色子代理，各 CLI 调用通道按下文协议执行
```

### 自动编排原则（CRITICAL）

```yaml
核心原则: 子代理编排由实际工作单元数驱动，不以 TASK_COMPLEXITY 作为 ON/OFF 开关
触发条件: 当前阶段/步骤/命令的待执行工作可分解为 ≥2 个可独立并行的工作单元（无论 TASK_COMPLEXITY）
主动触发（应主动，非可选）: 满足触发条件（≥2 个独立工作单元 且 并行收益明确）时，主代理应主动编排子代理；不要求用户显式说"子代理/并行代理"
  措辞统一（CRITICAL）: 自动编排是"满足条件即应执行"的确定性行为，不是"可做可不做"的主观裁量。
    诊断实证: 模糊的"可主动"措辞会导致主代理在灰区默认走串行（如任务收尾的自发审查全程不 spawn）。
    统一用语: 本节及各 CLI 触发点节统一用"应主动 spawn/编排"；严禁用"可主动"弱化为可选。
编排方式: 按编排五步法自动选择代理类型和数量（子代理数 = 独立工作单元数，≤6/批）
不触发: 仅 1 个工作单元、工作单元存在强数据依赖无法并行、或子代理开销不低于收益 → 主代理直接执行
复杂度角色: TASK_COMPLEXITY 影响编排深度和强度（reviewer 调度、验证范围、测试覆盖），不影响是否编排
R1 例外: R1 快速流程为单点操作，天然仅 1 个工作单元，不触发子代理编排
边界保持: 主动编排不得绕过确认、EHRB、职责隔离、阻塞等待、结果真实性、降级处理或主代理汇总决策规则

CLI 一致性（CRITICAL）:
  本原则 CLI 无关——Claude Code、Codex CLI 及其他 CLI 在满足触发条件时均应主动编排，
  仅"调用通道"和"环境前置检测"不同（Claude 用 Task 工具；Codex 用 spawn_agent/CSV，需 /experimental 开启）。
  各 CLI 的稳定性策略、降级阈值、上下文预算机制是"编排失败后的兜底"，
  统计的是已发生的 spawn→close 失败/循环，不构成"编排前预判回避子代理"的理由。
  不得因某 CLI 有失败兜底机制就在编排前默认走主代理直接执行。
```

### 通用子代理触发场景总表（单一事实源）

> 本表是各阶段/命令编排触发的唯一判定基准。各阶段文件（design/develop）、各命令文件（review/verify/commit/test/init/wiki/validatekb）、
> 各 CLI 触发点节（subagent-codex.md / subagent-claude.md）均引用本表，只补本场景特有边界，不重复定义触发阈值。

```yaml
判定基准（CRITICAL - 满足任一即应主动编排）:
  - ≥2 个可独立并行的工作单元（目录/模块/文件/维度/任务项）且无强数据依赖
  - 同一动作需对 ≥2 个目标执行（读取/扫描/审查/验证）
  - 单一工作单元规模过大可按职责/区域拆为 ≥2 个并行子单元，且拆分收益明确
  不触发: 仅 1 个工作单元、强数据依赖、或子代理开销不低于收益 → 主代理直接执行（或并行工具调用）

四类通用场景（按场景选默认代理类型，编排五步法步骤2c）:

  1. 资源读取/扫描（信息收集）:
     典型: 读取 ≥2 个文件、扫描 ≥2 个目录/模块、读取 ≥2 个项目配置、跨文件搜索定位
     默认代理: Explore（只读）/ Codex spawn_agent(explorer)
     判定: ≥2 个独立读取目标 → spawn 子代理并行读取；轻量单次读取 → 并行工具调用（非子代理）
     适用阶段/命令: DESIGN Phase1 步骤4/6、DEVELOP 步骤5、~init、~wiki、~ssh 只读扫描

  2. 代码/质量审查（多维度审查）:
     典型: 显式 ~review/~verify、DEVELOP 阶段收尾的自发代码审查（非显式命令）、复杂任务的核心/安全模块审查
     默认代理: reviewer（RLM 角色）/ Codex spawn_agent(reviewer, fork_context=true)
     判定: ≥2 个分析维度 或 审查文件 ≥2 且并行收益明确 → 按维度/文件组并行审查（≤6/批）
     维度: 后端/API、前端/UI、迁移/持久化、测试/验证、质量、安全、性能、简化/过度工程、视觉/UX
     适用阶段/命令: ~review、~verify、DEVELOP 步骤7、任何阶段的自发代码审查

  3. 提交辅助（变更分析 + 预提交检查）:
     典型: ~commit 步骤2 变更点提取、代码-文档一致性检查、测试覆盖检查
     默认代理: explorer（读 diff 提取变更点）+ reviewer（预提交质量检查）
     判定: 待提交文件 ≥2 或需 ≥2 维度预提交检查 → spawn 子代理并行
     临界区边界（CRITICAL，见下方"临界区白名单"）: git add→commit 临界区永不拆给子代理

  4. 测试/验证分析与失败定位:
     典型: ~test 步骤3/4 失败根因定位、~verify 步骤4/5 验证执行与修复、DEVELOP 步骤8 测试编写
     默认代理: worker（测试编写/修复）/ explorer（失败定位）/ Codex spawn_agent(worker)
     判定: 失败文件 ≥2 或失败维度独立可并行 → spawn 子代理并行定位根因；主代理汇总
     新增测试: 独立测试文件 ≥2 → 按文件分配 worker 并行编写（≤6/批）

降级处理（所有场景通用）:
  子代理调用失败 / CLI 不支持子代理 / 环境前置未满足 → 主代理在当前上下文直接完成 + tasks.md 标记 [降级执行]
  保留结果: 部分成功（status=partial）的子代理产出始终保留，未完成部分由主代理汇总补充
```

### 临界区白名单（CRITICAL - 永不拆给子代理）

```yaml
定位: 扩大子代理适用面时，并发敏感或状态一致性要求高的操作始终由主代理独占执行。
  子代理只读或操作各自独立文件集无竞态；以下操作因涉及共享状态/串行原子性，禁止并行子代理。

始终主代理独占执行:
  - 提交临界区: git add → git commit（~commit 步骤3，commit.lock 保护段）
  - 并发锁管理: commit.lock 获取/死锁检测/释放、偏差检测快照对比（~commit 步骤3）
  - EHRB 确认: G2 风险确认与升级（所有阶段）
  - 状态文件写入: .status.json、tasks.md 状态符号与 LIVE_STATUS、进度快照（所有阶段）
  - 方案包归档: migrate_package.py 调用、archive/_index.md 更新、INDEX.md 活跃指向清除（DEVELOP 步骤14、~clean）
  - 推送/远程: git push/pull/rebase（~commit 步骤3 推送段）

判定原则: 操作读写共享状态文件、持有互斥锁、或需串行原子性 → 主代理独占；操作各自独立只读/独立文件集 → 可并行子代理
```

### 强制调用规则

```yaml
强制调用规则（标注"强制"的必须调用，标注"跳过"的可跳过，子代理编排均遵循自动编排原则 + 通用触发场景总表）:
  EVALUATE: 主代理直接执行，不调用子代理
  DESIGN:
    Phase1（上下文收集）—
    子代理（按编排五步法选择类型）— 现有项目资源+≥2个可独立扫描的目录/模块 项目资源扫描自动编排（步骤4）| ≥2个可独立分析的单元 深度依赖分析自动编排（步骤6）| 单一目录/单元或新建项目 主代理直接执行
    Phase2（方案构思）—
    brainstormer — R2 标准流程步骤10 方案构思时强制（TASK_COMPLEXITY=complex），≥3 个子代理并行（每个独立构思一个方案）
    方案包填充/知识库同步/归档 — 主代理按服务接口规范直接执行（不通过子代理中转）
  DEVELOP:
    子代理（按编排五步法选择类型）— ≥2个可独立并行的任务项 自动编排（步骤6，按 DAG 或主代理判断依赖后并行）| 新增测试用例时自动编排（步骤8）| 仅1个任务项 主代理直接执行
    代码审查（步骤7，含任务收尾的自发审查）— 应主动编排（不受 complex+核心模块限制）:
      complex+涉及核心/安全模块 → reviewer 强制（fork_context）
      其他任务但满足 ≥2 文件/维度 + 并行收益明确 → 按 ~review 规则主动 spawn reviewer/explorer 并行审查
      仅 1 文件/1 维度 → 主代理直接执行
      关键: 任务收尾的自发代码审查（验收前的自审，非显式 ~review 命令）等同 ~review 处理，满足总表审查场景触发条件即应主动编排
    知识库同步/归档 — 主代理按服务接口规范直接执行（不通过子代理中转，归档属临界区白名单）
  命令路径:
    ~review: 子代理（按编排五步法选择类型）— ≥2个分析维度或审查文件≥2 且并行收益明确时，应主动按 functions/review.md 的当前分析维度或文件分组并行；确认、EHRB、阻塞等待、结果真实性和主代理汇总边界不变
    ~verify: 同 ~review（审查+验证+修复场景），≥2 维度或文件≥2 时应主动编排
    ~commit: 步骤2 变更分析/预提交质量检查，待提交文件≥2 或需多维度检查时 spawn explorer/reviewer 并行；步骤3 临界区（git add→commit/锁/偏差检测/EHRB/推送）始终主代理独占（临界区白名单）
    ~test: 步骤3/4 失败定位/修复方案生成，失败文件≥2 或失败维度独立时 spawn worker/explorer 并行定位根因
    ~validatekb: 子代理（按编排五步法选择类型）— ≥2个验证维度或知识库文件≥2 时并行（按文件数和维度数分配子代理）
    ~init: 子代理（按编排五步法选择类型）— ≥2个可独立扫描的模块目录时并行
    ~ssh: 主代理按 ProjectEnvService 直接执行；只读扫描可并行，配置写入不通过子代理中转
    其他命令: 已知命令流程内出现 ≥2 个独立扫描/实现/验证单元，且并行收益明确时，应按自动编排原则主动编排；命令确认、EHRB 和写入职责边界不变

通用路径角色（不绑定特定阶段，按需调用）:
  writer — 用户通过 ~rlm spawn writer 手动调用，用于生成独立文档（非知识库同步）

跳过条件: 仅当标注"跳过"的条件成立时可跳过，其余情况必须调用
代理降级: 子代理调用失败 → 主代理直接执行，在 tasks.md 标记 [降级执行]
语言传播: 构建子代理 prompt 时须包含当前 OUTPUT_LANGUAGE 设置，确保子代理输出语言与主代理一致
触发判定基准: 所有上述场景的触发阈值统一引用"通用子代理触发场景总表"，各命令文件不重复定义
```

### 子代理行为约束（CRITICAL）

```yaml
路由跳过（由 <execution_constraint> SUB-AGENT CHECK 保证）: 子代理收到的 prompt 是已分配的具体任务，必须直接执行，跳过 R0-R2 路由评分
  原因: 路由评分是主代理的职责，子代理重复评分会导致错误的流程标签（如标准流程的子代理输出"快速流程"）
  实现: 子代理 prompt 必须以 "[跳过指令]" 开头，execution_constraint 检测到此标记后短路跳过所有路由和 G3 格式
输出格式: 子代理只输出任务执行结果，不输出流程标题（如"【HelloAGENTS】– 快速流程"等）

上下文注入（Claude Code）:
  主代理: UserPromptSubmit hook 在每次用户消息时注入阶段规则摘要 + 活跃子代理状态，确保 compact 后规则和子代理进度不丢失
  子代理: SubagentStart hook 自动注入当前方案包上下文（proposal.md + tasks.md + context.md）+ 技术指南（guidelines.md），
    主代理构建子代理 prompt 时仍需包含任务描述和约束条件，hook 注入的上下文作为补充而非替代
    技术指南: .helloagents/guidelines.md 存放项目级编码约定（框架规范/代码风格/架构约束），子代理开发前自动获取

质量验证循环（Claude Code）: SubagentStop hook 在代码实现子代理完成时自动运行项目验证命令，
  验证失败 → 子代理继续修复（最多1次循环，stop_hook_active=true 时放行）
  验证命令来源: .helloagents/runbook.yaml > .helloagents/verify.yaml > package.json scripts > 自动检测

Worktree 隔离（Claude Code）: 当多个子代理需修改同一文件的不同区域时，
  使用 Agent(isolation="worktree") 在独立 worktree 中执行，避免 Edit 工具冲突
  适用: DAG 同层任务涉及同文件不同函数/区域
  不适用: 子代理仅读取文件（无写冲突）或任务间无文件重叠
  worktree 子代理完成后，主代理在汇总阶段合并变更

阻塞等待与结果真实性（CRITICAL）:
  阻塞等待: spawn 子代理后必须立即阻塞等待全部返回，等待期间禁止执行任何后续流程步骤
    Claude Code: 多个 Task 调用自动阻塞直到全部返回
    Codex CLI: 连续 spawn_agent 后立即 collab wait，不得在 spawn 与 wait 之间插入其他操作
    其他 CLI: 使用 CLI 提供的等价阻塞等待机制
    DO NOT: spawn 后"先做其他事再回来看结果"— 这会导致子代理结果丢失或被主代理伪造内容替代
  结果真实性: 主代理仅汇总和决策子代理返回的实际内容，禁止在子代理未完成或未返回时自行生成应由子代理产出的内容
  降级例外: 子代理超时/失败触发降级 [→ 降级处理] 后，主代理接手执行属于正常降级，不违反此规则
```

### 编排标准范式

```yaml
核心模式: 按职责领域拆分 → 每个子代理一个明确范围 → 并行执行 → 主代理汇总

编排五步法:
  1. 识别独立单元: 从任务中提取可独立执行的工作单元（模块/维度/文件组/职责区）
  2. 选择代理类型: 对每个工作单元，按以下优先级匹配代理:
     a. 用户自定义代理: 当前会话可用的非 ha-* 代理，其 description 与工作单元语义匹配 → 优先使用
     b. RLM 角色: 本场景有指定 RLM 角色（如方案构思→brainstormer）→ 使用指定角色
     c. 原生子代理: 以上均无匹配 → 使用本场景默认原生类型（见下方适用场景表）
     匹配规则: 用户代理 description 与工作单元的任务类型（代码实现/测试/审查/扫描等）语义匹配度高 → 命中
     混合编排: 同批次内允许不同工作单元使用不同代理类型（如 3 个任务中 2 个匹配用户代理、1 个用原生子代理）
  3. 分配职责范围: 每个子代理的 prompt 必须明确其唯一职责边界（按任务类型适配，见 prompt 构造模板）
  4. 并行派发: 无依赖的子代理在同一消息中并行发起，有依赖的串行等待
  5. 汇总决策: 阻塞等待全部子代理返回后，主代理汇总实际返回内容并做最终决策 [→ 阻塞等待与结果真实性]

适用场景与编排策略（步骤2c 的默认原生类型）:
  信息收集（代码扫描/依赖分析/状态查询）:
    → 按模块目录或数据源拆分，每个子代理负责一个目录或数据源
    → 默认类型: Explore（只读）
  代码实现（功能开发/Bug修复/重构）:
    → 按任务项或文件中的函数/类拆分，每个子代理负责一个独立代码段
    → 默认类型: general-purpose / worker
  方案构思（设计阶段多方案对比）:
    → 每个子代理独立构思一个差异化方案，不共享中间结果
    → 指定角色: brainstormer（RLM 角色）— Codex: spawn_agent(agent_type="brainstormer") | Claude: Agent(subagent_type="ha-brainstormer")
  质量检查（审查/验证/测试）:
    → 按分析维度拆分（质量/安全/性能），每个子代理负责≥1个维度
    → 默认类型: general-purpose / worker

prompt 构造模板:
  "[跳过指令] 直接执行以下任务，跳过路由评分。
   [语言] 使用 {OUTPUT_LANGUAGE} 输出所有内容。
   [职责边界] 你负责: {按任务类型描述职责边界，见下方}。
   [任务内容] {具体要做什么}。
   [约束条件] {代码风格/格式/限制}。代码体积控制: 预警阈值（文件/类 300 行、函数 40 行须评估拆分）、强制拆分阈值（文件/类 400 行、函数 60 行须按职责拆分），例外: 生成代码、大型测试夹具、迁移脚本、协议常量表。前端文案净化（前端/UI 任务强制）: 组件的 title/subtitle/description/tooltip/placeholder/aria-label 等属性中禁止写入功能说明、产品描述或开发者注释性文本（如"队列、调度器和关键系统状态"、"保留相同的数据入口，但以更轻的页面结构展示"、"一眼看清"、"可以在同一页完成…等运营动作"），这些属性仅用于简洁的用户可见 UI 标签（如"节点管理"、"系统概览"），不超过 8 个字；功能说明属于文档而非代码。
   [返回格式] 返回: {status: completed|partial|failed, changes: [{file, type, scope}], issues: [...], verification: {lint_passed, tests_passed}}"

  职责边界按任务类型适配:
    代码实现 → "你负责: 任务X。操作范围: {文件路径}中的{函数/类名}。"
    代码扫描 → "你负责: 扫描{目录路径}。分析内容: {文件结构/入口点/依赖关系}。"
    方案构思 → "你负责: 独立构思一个实现方案{差异化方向}。"
    质量检查 → "你负责: {维度名称}维度的检查。检查范围: {文件列表或模块列表}。"
    依赖分析 → "你负责: 分析{模块名}模块。分析内容: {依赖关系/API接口/质量问题}。"
    测试编写 → "你负责: 为{测试文件路径}编写测试用例。覆盖范围: {被测函数/类列表}。"

  标准返回格式（代码实现/测试编写类子代理强制，其他类型按需）:
    status: completed（全部完成）| partial（部分完成）| failed（失败）
    changes: [{file: "路径", type: "create|modify|delete", scope: "函数/类名"}]
    issues: ["发现的问题或风险"]
    verification: {lint_passed: true|false|skipped, tests_passed: true|false|skipped}
    注: 此为 prompt 内嵌简化格式，完整字段定义见 rlm/schemas/agent_result.json（RLM 角色子代理使用完整 schema）
```

---

## CLI 调用通道

| CLI | 通道 | 调用方式 |
|-----|------|----------|
| Claude Code | Agent 工具 | `Agent(subagent_type="general-purpose", prompt="[RLM:{角色}] {任务描述}")`；支持文件级定义 .claude/agents/*.md |
| Claude Code | Agent Teams | complex 级别，多角色协作需互相通信时（实验性，需 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1）[→ Agent Teams 协议] |
| Codex CLI | spawn_agent | Collab 子代理调度（/experimental 开启，agents.max_depth=1，≤6 并发）；支持 [agents] 角色配置 |
| Codex CLI | spawn_agents_on_csv | CSV 批处理（需 collab+sqlite，≤64 并发），同构任务专用 |
| OpenCode | Task tool | 主代理 build/plan + 子代理 general/explore；自定义 .opencode/agent/*.md，支持子代理间委派，MCP 服务器 |
| Gemini CLI | 子代理 | 内置 codebase_investigator + generalist + cli_help + browser_agent（实验性），自定义 .gemini/agents/*.md，A2A 远程代理 |
| Qwen Code | 子代理 | 内置 general-purpose，自定义 .qwen/agents/*.md，/agents create 创建，主代理按 description 自动委派 |
| Grok CLI | 子代理 | 主代理直接执行；自定义 .grok/agents/*.md（前瞻），MCP 服务器 |

### CLI 专属调用协议（按需加载）

各 CLI 的详细调用协议、示例、交互策略和稳定性策略已按 CLI 拆分为独立文件，由 G7 按当前 CLI 选择性加载：

- **Claude Code**: `rules/subagent-claude.md`（Agent 工具协议 + Agent Teams 协议）
- **Codex CLI**: `rules/subagent-codex.md`（spawn_agent/CSV 批处理协议 + 交互策略 + 稳定性策略 + EHRB 豁免）
- **OpenCode / Gemini / Qwen / Grok**: `rules/subagent-other.md`（各 CLI 调用方式 + 用户扩展）

---

## 调度规则

### 并行调度规则（适用所有 CLI）

```yaml
并行批次上限: ≤6 个子代理/批（Codex CLI CSV 批处理模式 ≤16，可配置至 64）
并行适用: 同阶段内无数据依赖的任务
串行强制: 有数据依赖链的任务（如 DAG 中有 depends_on 依赖的下游任务）

任务分配约束（CRITICAL）:
  职责隔离: 每个并行子代理必须有明确且不重叠的职责范围（不同函数/类/模块/逻辑段）
  禁止重复: 禁止将相同职责范围派给多个子代理（同任务+同文件+同函数=纯浪费）
  同文件允许: 多个子代理可操作同一文件，前提是各自负责不同的函数/类/代码段，prompt 中必须明确各自的操作范围
  复杂任务拆分: 单个复杂任务应拆为多个职责明确的子任务，分配给多个子代理并行执行
  分配前检查: 主代理在派发前确认各子代理的职责范围无重叠，有重叠则合并或重新划分

通用并行信息收集原则（适用所有流程和命令）:
  ≥2个独立文件读取/搜索 → 同一消息中发起并行工具调用（Read/Grep/Glob/WebSearch/WebFetch）
  ≥2个独立分析/验证维度 或 文件数≥2，且子代理能明显缩短扫描/验证时间或提升覆盖质量 → 按编排五步法调度子代理并行执行；收益不足时使用并行工具调用或主代理直接执行
  轻量级独立数据源（单次读取即可） → 并行工具调用即可，不需要子代理开销
  子代理数量原则: 子代理数 = 实际独立工作单元数（维度数/模块数/文件数），受≤6/批上限约束，禁止用"多个"模糊带过

CLI 实现:
  Claude Code Task: 同一消息多个 Task 调用
  Claude Code Teams: teammates 自动从共享任务列表认领
  Codex CLI spawn_agent: 多个 spawn_agent + collab wait（异构任务，≤6/批）
  Codex CLI spawn_agents_on_csv: CSV 批处理（同构任务，≤{CSV_BATCH_MAX} 并发，需 collab+sqlite，CSV_BATCH_MAX=0 时禁用）
    适用判定: CSV_BATCH_MAX>0 且同层≥6 个结构相同的任务（相同指令模板+不同参数）→ 优先 CSV 批处理
    不适用: CSV_BATCH_MAX=0 | 任务间指令逻辑不同、需要不同工具集、或任务数<6 → 保留 spawn_agent
  OpenCode: 多个 Task tool 调用（@general / @explore），支持子代理间委派（task_budget + level_limit）
  Gemini CLI: 多个子代理自动委派（实验性）
  Qwen Code: 多个自定义子代理自动委派
  Grok CLI: 降级为串行执行
```

### 降级处理

```yaml
降级触发: 子代理调用失败 | CLI 不支持子代理（Grok CLI）
降级执行: 主代理在当前上下文中直接完成任务
降级标记: 在 tasks.md 对应任务后追加 [降级执行]
```

### DAG 依赖调度（适用 DEVELOP 步骤6）

```yaml
目的: 通过 tasks.md 中的 depends_on 字段显式声明任务依赖，自动计算最优并行批次

tasks.md 依赖声明格式:
  [ ] 1.1 {任务描述} | depends_on: []
  [ ] 1.2 {任务描述} | depends_on: [1.1]
  [ ] 1.3 {任务描述} | depends_on: [1.1]
  [ ] 1.4 {任务描述} | depends_on: [1.2, 1.3]

调度算法（主代理在步骤6开始时执行）:
  1. 解析 tasks.md 中所有任务的 depends_on 字段
  2. 循环依赖检测: 发现循环 → 输出: 错误（循环依赖的任务编号）→ 降级为串行执行
  3. 拓扑排序: 计算执行层级（无依赖=第1层，依赖第1层=第2层，以此类推）
  4. 按层级批次派发: 同层级任务并行（每批≤6），层级间串行等待
  5. 失败传播: 某任务失败 → 所有直接/间接依赖该任务的下游任务标记 [-]（前置失败）

无 depends_on 时的降级: 按原有逻辑（主代理自行判断依赖关系）执行
```

### 分级重试策略（适用所有原生子代理调用）

```yaml
目的: 区分失败类型，避免不必要的全量重试

重试分级:
  瞬时失败（timeout/网络错误/CLI异常）:
    → 自动重试 1 次
    → 仍失败 → 标记 [X]，记录错误详情
  逻辑失败（代码错误/文件未找到/编译失败）:
    → 不自动重试
    → 标记 [X]，记录错误详情和失败原因
  部分成功（子代理返回 status=partial）:
    → 保留已完成的变更
    → 未完成部分记录到 issues，由主代理在汇总阶段决定是否补充执行

重试上限: 每个子代理最多重试 1 次
结果保留: 成功的子代理结果始终保留，仅重试失败项

深度分析（break-loop）: 当同一任务经 Ralph Loop 验证循环仍失败（stop_hook_active=true 放行后主代理接手），
  或主代理补充执行仍失败时，执行 5 维度根因分析后再标记 [X]:
  1. 根因分类: 逻辑错误/类型不匹配/依赖缺失/环境问题/设计缺陷
  2. 修复失败原因: 为什么之前的修复尝试没有解决问题
  3. 预防机制: 建议添加什么检查/测试可防止此类问题
  4. 系统性扩展: 同类问题是否可能存在于其他模块（列出可疑位置）
  5. 知识沉淀: 将分析结论记录到验收报告的"经验教训"区域
  触发条件: 逻辑失败 + 已有≥1次修复尝试（子代理重试或 Ralph Loop 循环）
```

---

## 脚本执行规范

```yaml
脚本执行: python -X utf8 '{脚本路径}'
```

---

## 子代理合规检查（阶段验收时执行）

```yaml
子代理调用合规检查（阶段验收时执行）:
  自动编排合规:
    DESIGN 阶段:
      检查: brainstormer 是否已调用 — 条件: TASK_COMPLEXITY=complex
    DEVELOP 阶段:
      检查: reviewer 是否已调用（complex+涉及核心/安全模块 强制）
      检查: ≥2个独立任务项时子代理是否已编排 — 条件: 任务项≥2 且未标记[降级执行]
    未调用且未标记[降级执行] → ⚠️ 警告性（记录"子代理未按规则调用: {角色名/自动编排}"）
```
