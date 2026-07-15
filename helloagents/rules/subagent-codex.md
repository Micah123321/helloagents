# 子代理调用协议 — Codex CLI

> 本文件由 subagent-protocols.md 按 CLI 拆分而来，仅在 Codex CLI 环境下按需加载。

---

## Codex CLI 调用协议（CRITICAL）

```yaml
多代理配置（~/.codex/config.toml [agents] 节）:
  启用: /experimental 命令开启 collab 特性（需重启）
  全局设置:
    agents.max_threads: 最大并发子代理线程数（spawn_agent 上限 6，CSV 上限 64）
    agents.max_depth: 嵌套深度（默认 1，仅一层）
  角色定义（每个角色独立配置）:
    [agents.my_role]
    description = "何时使用此角色的指引"
  config_file = "path/to/role-specific-config.toml"  # 标准 config.toml 格式，可覆盖 developer_instructions/model/sandbox 等
  nickname_candidates = ["Nickname1", "Nickname2"]
  config_file 机制: 角色 TOML 作为高优先级配置层覆盖父代理配置（可覆盖 developer_instructions/model/sandbox 等）
  路由豁免: 由父代理 developer_instructions 统一声明子代理豁免条款，所有子代理（原生/HA/用户自定义/未来新增）
    自动继承该豁免；权限边界可通过 per-role config_file 收紧
  只读角色: HelloAGENTS 为 explorer/reviewer/brainstormer/monitor 部署 read-only config_file，使角色权限边界与只读职责一致
  线程管理: /agent 命令在活跃子代理线程间切换
  审批传播: 父代理审批策略自动传播到子代理

模型默认策略（CRITICAL）:
  默认行为: 子代理默认继承主代理模型（Codex 配置分层: 角色节不设 model = 继承顶层主代理 model）
  HelloAGENTS 写入 [agents.{role}] 时有意不设 model:
    1. codex_roles.py 创建/更新角色节只写 description + nickname_candidates + config_file（只读角色），刻意不写 model
    2. 只读角色 config_file（agents/helloagents-readonly-{role}.toml）只设 sandbox_mode + developer_instructions，不含 model
    → 结果: 所有子代理默认与主代理同模型，与 Claude Code 的 model: inherit 默认行为对齐
  降级为可选优化（非默认）:
    仅当某角色确实需要更轻量模型（如 explorer/monitor 轮询扫描任务，为省成本）时，
    才在对应 [agents.{role}] 节显式设 model = "<轻量模型名>"
    实现/审查/构思类角色（worker/reviewer/brainstormer）通常需要主力模型能力，不建议降级
  保留用户配置: codex_roles.py 更新角色节时保留用户已添加的 model 键（preserving user-added keys），不覆盖用户显式选择

原生子代理:
  代码探索/依赖分析 → spawn_agent(agent_type="explorer", prompt="...")
  代码实现 → spawn_agent(agent_type="worker", prompt="...")
  测试运行 → spawn_agent(agent_type="worker", prompt="...")
  方案构思 → spawn_agent(agent_type="brainstormer", prompt="...")  # DESIGN 步骤10，RLM 角色
  监控轮询 → spawn_agent(agent_type="monitor", prompt="...")  # 长时间运行的轮询任务

上下文传递策略（fork_context 兼容边界）:
  默认策略: 命名 Codex agent 调用使用 spawn_agent(agent_type="...", prompt="...")，默认不传 fork_context。
  prompt 自包含上下文（CRITICAL）:
    - reviewer: prompt 必须包含审查目标、相关 diff/变更摘要、方案/任务约束、验证结果和验收重点
    - writer: prompt 必须包含文档目标、受众、结构要求、关键决策和引用范围
    - DAG 任务中的实现子代理: prompt 必须包含整体方案、已完成任务、当前任务边界、允许写入范围和验证方式
    - brainstormer: prompt 必须包含完整 Phase1 上下文和差异化方向，保持独立构思
    - CSV 批处理 worker: 每行 CSV + instruction 必须自包含全部上下文
  fork_context=true:
    - 仅当当前会话的 spawn_agent schema 明确支持 agent_type 与 fork_context 同用时才可传入
    - 不得通过首次不兼容 spawn 失败来探测兼容性
    - 发现不兼容时立即改用同一 agent_type、省略 fork_context、prompt 内嵌上下文的兼容调用

CSV 批处理编排（需 collab + sqlite 特性）:
  同构并行任务 → spawn_agents_on_csv(csv_path, instruction, ...)
  适用: 批量代码审查/批量测试/批量数据处理等每行任务结构相同的场景
  不适用: 异构任务（不同任务需不同工具/不同逻辑）→ 保留 spawn_agent 方式
  参数:
    csv_path: 输入 CSV 路径（每行一个任务，首行为列头）
    instruction: 指令模板，{column_name} 占位符自动替换为行值
    id_column: 可选，指定用作任务 ID 的列名（默认行索引）
    output_csv_path: 可选，结果导出路径（默认自动生成）
    output_schema: 可选，worker 返回结果的 JSON Schema
    max_concurrency: 并发数（默认 {CSV_BATCH_MAX}，上限 64）
    max_runtime_seconds: 单次 CSV 调用对所有 worker 共用的运行时上限；同构批次按最大任务复杂度计算后显式传入，不把 1800s 当作工作流默认值
  执行流程:
    1. 主代理生成任务 CSV（从 tasks.md 提取同构任务行）
    2. 调用 spawn_agents_on_csv，使用该同构批次的统一预算，直到每个 worker 进入 completed/partial/failed/回收之一
    3. 每个 worker 自动收到行数据 + 指令，执行后调用 report_agent_job_result 回报
    4. 成功时自动导出结果 CSV；部分失败时仍导出（含失败摘要）
    5. 主代理读取 output CSV 汇总结果
  进度监控: agent_job_progress 事件持续发出（pending/running/completed/partial/failed）；主代理保留 partial handoff 并只接手该行的 pending_scope
  状态持久化: SQLite 跟踪每个 item 状态，支持崩溃恢复
  失败处理: 无响应 worker 自动回收 | spawn 失败立即标记 | report_agent_job_result 仅限 worker 会话调用

helloagents 角色:
  角色→agent_type 映射（每个 RLM 角色使用自己的 agent_type，注册在 config.toml [agents.{role}] 节）:
    reviewer → spawn_agent(agent_type="reviewer", prompt="...")
    writer → spawn_agent(agent_type="writer", prompt="...")
    brainstormer → spawn_agent(agent_type="brainstormer", prompt="...")
  路由豁免: 由父代理 developer_instructions 统一处理（见 codex_config.py），
    所有子代理自动继承豁免条款；只读角色额外通过 per-role config_file 限制 sandbox
  执行步骤（同 Claude Code，仅调用方式不同）:
    1. 加载角色预设: 读取 rlm/roles/{角色}.md
    2. 构造 prompt: "[跳过指令] {从角色预设提取的约束} + {具体任务描述}"
       Codex RLM 角色调用默认不传 fork_context；角色 prompt 必须自包含必要上下文
    3. 调用 spawn_agent: agent_type="{角色名}", prompt=上述内容
    4. 接收结果: 解析子代理返回的结构化结果
    5. 记录调用: 在 tasks.md 记录调用结果

用户自定义代理（config.toml [agents.{role}] 中非 ha-* 的角色）:
  调用方式: spawn_agent(agent_type="{custom-role}", prompt="{任务描述}")
  配置来源: ~/.codex/config.toml [agents.{role}] 节（用户自行定义 description/config_file/nickname_candidates 等）
  与 RLM 角色的关系:
    互补: 用户角色处理 RLM 角色未覆盖的领域（如 security-auditor、performance-tester）
    替代: 用户角色 description 覆盖某 RLM 角色能力 → 用户角色优先
    共存: 同一任务可同时调度用户角色 + RLM 角色
  命名冲突: 用户角色名与 ha-* 重名 → ha-* 优先（HelloAGENTS 预设不可被覆盖）
  CSV 批处理: 用户角色可作为 spawn_agents_on_csv 的 worker → 同构任务批量分配给自定义角色
  降级: 用户角色执行失败 → 降级到 RLM 角色或主代理直接执行
  Skill/MCP 辅助: DEVELOP 阶段识别到可用 Skill/MCP 可加速当前子任务 → 主动调用（非强制）
  用户扩展: 自定义子代理调度规则同 G9 用户代理分配规则 | Skills（Codex Skills）| MCP 服务器（不支持插件，扩展能力通过 Skill + MCP 实现）

并行调用: 多个无依赖子代理 → 连续发起多个 spawn_agent → 立即进入按代理独立截止时间收敛的 collab wait（支持多ID单次等待）；某一代理超时只触发该代理的强制 handoff 和接管，不得拖住已完成代理
批次接受证据（引用 subagent-protocols.md 编排启用契约）:
  - spawn_agent: 仅工具返回可用于 wait/send_input/close 的 agent id 才计为实际成功启动；调用计划、prompt 数量和失败调用均不计数
  - spawn_agents_on_csv: 以调用返回的已接受 worker/job 记录及 agent_job_progress 的 running/completed/partial 状态计数；仅写入 CSV 的行数不计为成功启动
  - 主代理在任务日志记录 final_dispatchable_count、successful_start_count、成功 agent/job id 和失败调用证据；普通批次 successful_start_count≥2、complex brainstormer successful_start_count≥3 后才宣称已启用编排
  - 计划门槛已满足但兼容重试后仅 1 个 agent 成功启动 → 立即 send_input 请求 partial handoff，收到 handoff 后 close；无有效 handoff 也必须 close 并记录失败证据，主代理仅接手 pending_scope。该唯一 agent 不作为已启用编排报告
  - CSV 调用返回时唯一成功 worker 已处于 completed/partial 终态 → 保留其已验证 completed_scope，由主代理接手其余 pending_scope；CSV API 无逐 worker send_input/close 通道，须记录终态和失败行证据，不得虚构关闭动作或宣称已启用编排
  - DAG 层、分页批次或 CSV 拆批后的尾批 final_dispatchable_count=1 → 不调用 spawn_agent/CSV，由主代理直接执行；前序批次已启用不改变尾批判定
依赖调用: 自动编排按 DAG 分层，每层重新计算 final_dispatchable_count；该层 <2 时主代理执行，≥2 时才并行 spawn。逐个单代理调用仅限用户显式单角色委派等非自动编排路径
恢复暂停: 未达到动态预算的暂停代理 → 可用 resume_agent 恢复；达到预算后进入强制 handoff，不再用 resume_agent 延长同一任务墙钟
中断通信: send_input 向运行中的子代理发送消息（可选中断当前执行，用于纠偏或补充指令）
关闭子代理: close 关闭指定子代理
审批传播: 父代理审批策略自动传播到子代理，可按类型自动拒绝特定审批请求
限制: Collab 特性门控（/experimental 开启），agents.max_depth=1（仅一层嵌套），spawn_agent ≤6 并发，spawn_agents_on_csv ≤{CSV_BATCH_MAX} 并发（上限 64，CSV_BATCH_MAX=0 时禁用）

示例（DESIGN 步骤10 方案构思，≥3 个并行 spawn 后立即 collab wait）:
  spawn_agent(agent_type="brainstormer", prompt="直接执行以下任务，跳过路由评分。使用 {OUTPUT_LANGUAGE} 输出。你负责: 独立构思一个实现方案。上下文: {Phase1 收集的项目上下文}。差异化方向: {方向1}。")
  spawn_agent(agent_type="brainstormer", prompt="...你负责: 独立构思一个差异化方案，优先考虑不同的实现路径或架构模式。差异化方向: {方向2}。...")
  spawn_agent(agent_type="brainstormer", prompt="...你负责: 独立构思一个差异化方案，优先考虑不同的权衡取舍（如性能vs可维护性）。差异化方向: {方向3}。...")
  collab wait  # 立即进入有界等待，禁止在此之前执行其他步骤

示例（spawn_agent 异构并行，每个子代理职责范围不重叠）:
  spawn_agent(agent_type="worker", prompt="直接执行以下任务，跳过路由评分。使用 {OUTPUT_LANGUAGE} 输出。你负责: 任务1.1。操作范围: filter.py 中的空白判定函数。任务: 实现空白判定逻辑。约束: 代码体积控制: 文件/类超300行评估拆分、超400行强制拆分，函数超40行评估拆分、超60行强制拆分。返回: {status, changes: [{file, type, scope}], issues, verification: {lint_passed, tests_passed}, handoff: {completed_scope, evidence, pending_scope, blockers, next_action}}")
  spawn_agent(agent_type="worker", prompt="直接执行以下任务，跳过路由评分。使用 {OUTPUT_LANGUAGE} 输出。你负责: 任务1.2。操作范围: validator.py 中的输入校验函数。任务: 实现输入校验逻辑。约束: 代码体积控制: 文件/类超300行评估拆分、超400行强制拆分，函数超40行评估拆分、超60行强制拆分。返回: {status, changes, issues, verification, handoff: {completed_scope, evidence, pending_scope, blockers, next_action}}")
  collab wait

示例（spawn_agents_on_csv 同构批处理，批量审查 30 个文件）:
  # 主代理先生成 CSV: path,module,focus（每行一个任务，如 src/api/auth.py,auth,安全检查）
  spawn_agents_on_csv(csv_path="/tmp/review_tasks.csv", instruction="使用 {OUTPUT_LANGUAGE} 输出。审查 {path} 模块 {module}，重点关注 {focus}。返回: {{score: 1-10, issues: [...], suggestions: [...]}}", output_csv_path="/tmp/review_results.csv", max_concurrency=16)
  # 按 worker 动态预算收敛；全部 worker 进入 completed/partial/failed 后读取 output CSV 汇总结果
```

---

## Codex CLI 子代理交互策略

```yaml
request_user_input:
  子代理可通过 request_user_input 向用户发起确认请求
  HelloAGENTS 策略:
    DELEGATED 模式: 默认禁止（子代理不得中断自动化流程），审批配置自动拒绝
    INTERACTIVE 模式: 允许（用户可在 /agent 切换线程后响应）
    EHRB Critical: 始终允许（安全优先，无论模式）
  配置: 父代理审批策略自动传播到子代理
```

---

## Codex CLI 主动编排触发点（CRITICAL）

```yaml
定位: 本节平衡稳定性策略的"失败兜底"信号——明确 Codex 在哪些场景应主动 spawn 子代理。
子代理编排由实际工作单元数驱动（同 Claude Code），不要求用户显式说"子代理/并行代理"。
下面是 Codex 环境下应主动 spawn 的典型场景，触发条件沿用 subagent-protocols.md 自动编排原则:

DESIGN Phase1（上下文收集）:
  ≥2 个可独立扫描的目录/模块 → spawn_agent(agent_type="explorer") 按目录拆分并行扫描（≤6/批）
  ≥2 个可独立分析的依赖单元 → explorer 按单元拆分并行深度分析
  单一目录/单元或新建项目 → 主代理直接执行

DESIGN Phase2（方案构思，TASK_COMPLEXITY=complex）:
  ≥3 个独立 brainstormer 并行，每个独立构思一个差异化方案，spawn 后立即 collab wait

DEVELOP 步骤6（代码实现）:
  ≥2 个可独立并行的任务项 → spawn_agent(agent_type="worker") 按 DAG 层级或主代理判断并行
  同层 ≥6 个结构相同的同构任务（相同指令模板+不同参数）→ 优先 spawn_agents_on_csv 批处理（CSV_BATCH_MAX>0 时）

DEVELOP 步骤7（安全与质量检查，含任务收尾自发审查）:
  complex+核心/安全模块 → 强制完成 reviewer 审查职责；最终可派发审查单元≥2 时 spawn reviewer/explorer，只有1个审查单元时由主代理按 reviewer 清单执行；prompt 必须内嵌完整审查上下文
  其他任务但满足 ≥2 文件/维度 + 并行收益明确 → 按 ~review 规则 spawn reviewer/explorer 并行审查
  任务收尾的自发代码审查（验收前自审，非显式 ~review）等同 ~review 处理，应主动编排

DEVELOP 步骤8（测试编写）:
  独立测试文件≥2 → worker 按文件分配并行编写

命令路径（并行收益明确时主动编排）:
  ~review: ≥2 个分析维度或审查文件≥2 且并行收益明确 → 按维度/文件组拆分并行审查
    强项场景: 大批量文件审查（如≥6 个文件）→ spawn_agents_on_csv 批处理是 Codex 独有的高吞吐通道
  ~verify: 同 ~review（审查+验证+修复场景），≥2 维度或文件≥2 且并行收益明确 → 并行
  ~commit: 步骤2 变更分析/预提交质量检查，待提交文件≥2 或需多维度检查 → spawn explorer/reviewer 并行
    临界区（步骤3 git add→commit/锁/偏差检测/推送）始终主代理独占，不拆子代理（临界区白名单）
  ~test: 步骤3/4 失败定位，失败文件≥2 或失败维度独立 → spawn worker/explorer 并行定位根因
  ~validatekb: ≥2 个验证维度或知识库文件≥2 → 并行验证
  ~init: ≥2 个可独立扫描的模块目录 → explorer 并行扫描

CSV 批处理主动判定（Codex 独有）:
  CSV_BATCH_MAX>0 且同层/同批 ≥6 个结构相同的任务 → 优先 spawn_agents_on_csv（异构任务仍用 spawn_agent）
  CSV_BATCH_MAX=0 → 退回 spawn_agent 逐个执行
  拆批后的尾批只有 1 行 → 主代理直接执行，不为凑批或沿用前序编排状态启动单 worker

工具发现前置（CRITICAL）:
  当 G10 判定应主动编排，但当前可见工具列表未直接显示 spawn_agent 时:
    1. 必须先调用 tool_search 搜索 "spawn_agent multi-agent subagent collab"
    2. 若发现 multi_agent_v1.spawn_agent 或等价单体子代理工具 → 按 Codex 调用协议使用该工具
       参数兼容性: 若 schema 不含 fork_context，或调用返回 unknown field/invalid argument/agent_type 与 fork_context 不兼容等参数错误，必须立即改用同一 agent_type 且省略 fork_context、将上下文写入 prompt 后重试一次；该兼容性重试不计入稳定性失败、不触发主代理降级。重试仍失败才记录为实际 spawn 调用失败
    3. 若只发现 spawn_agents_on_csv:
       - 同构任务≥6且 CSV_BATCH_MAX>0 → 使用 CSV 批处理
       - 异构任务或任务数<6 → 继续寻找单体 spawn_agent
    4. 继续寻找单体 spawn_agent 时，依次追加搜索 "spawn_agent"、"multi_agent_v1.spawn_agent agent spawn collab"（最多 2 次），每次结果写入降级证据；仍找不到才降级
    5. 工具发现失败、平台明确不可用或实际 spawn 调用失败 → 主代理直接执行，并记录为环境限制或调用失败证据
  禁止:
    - 仅凭初始工具列表未显示 spawn_agent 就判断无单体子代理通道
    - 仅凭工具说明写有"用户显式要求"就跳过 HelloAGENTS 已触发的主动编排

环境前置（编排前一次性检测，非每次回避）:
  /experimental 未开启 或 agents.max_threads=0 → 跳过所有子代理调度，主代理直接执行 + 标记 [降级执行] + 记录环境证据（这是环境限制，不是回避）
  检测通过 → 后续按上述触发点主动编排

边界（编排不得绕过，与稳定性策略一致）:
  确认、EHRB、阻塞等待（spawn 后立即 collab wait）、结果真实性、降级处理、主代理汇总决策、临界区白名单
降级证据:
  降级报告必须说明触发原因: 工具发现失败 / 环境前置未满足 / 实际 spawn 调用失败 / 子代理超时或失败；禁止使用"可能只暴露批处理通道"等推测性描述作为直接降级依据
  Codex fork_context 参数兼容性失败不算最终实际 spawn 调用失败；必须先执行同一 agent_type、省略 fork_context、prompt 自包含上下文的兼容重试
```

---

## Codex CLI 子代理稳定性策略（CRITICAL）

```yaml
定位（重要）: 本节机制仅在"子代理已 spawn 并失败/超时/无返回"之后生效，
  是编排失败后的兜底，不构成编排前回避子代理的理由。
  Codex 与 Claude Code 一样应主动编排（见上方"主动编排触发点"），仅触发条件和调用通道不同。

目的: 子代理反复 spawn→wait→close 失败循环浪费上下文窗口时，切换到稳定的主代理执行路径

参数/schema 错误处理（CRITICAL）:
  参数/schema 错误不是子代理运行稳定性失败
  触发: fork_context 字段未知、agent_type 与 fork_context 组合非法、参数校验失败、unknown field、invalid argument
  处理: 不进入等待/close/连续失败统计；按"省略 fork_context + prompt 自包含上下文"的兼容调用重试一次
  失败统计: 兼容重试仍失败时，才记录为实际 spawn 调用失败

单次等待策略:
  动态预算: 主代理在 spawn 前按 `scope_units`、`dependency_depth` 和 `task_weight` 计算每个子代理的预算，不使用全局固定秒数:
    `wait_budget_seconds = clamp(120 + 60*min(scope_units, 8) + 120*min(dependency_depth, 3) + 60*task_weight, 180, 900)`
    `task_weight`: scan=1、analysis/review=2、implementation/test=3；`scope_units` 为独立文件/模块/维度数；无依赖时 `dependency_depth=0`
    `handoff_grace_seconds = clamp(round(wait_budget_seconds*0.1), 30, 90)`
    主代理必须在 prompt 或任务日志中记录预算输入、计算结果和人工调整原因；300 秒只可作为中等扫描任务的示例，不是默认值
  正常等待: spawn 后立即 collab wait；每轮返回后分别处理已完成、失败、partial handoff 和仍运行的代理
  已完成代理: 立即保留实际结果，校验 changes.scope 或 handoff.completed_scope，不等待其他代理才能记录
  截止触发: 某代理超过墙钟仍无 completed/failed/partial 结果 → 只向该代理发送一次强制回传请求，明确要求:
    "请立即返回 status=partial 或 completed；列出 handoff.completed_scope、handoff.evidence、handoff.pending_scope、handoff.blockers 和 handoff.next_action。不要继续扩展任务范围。"
  宽限期: 强制回传请求后按 `handoff_grace_seconds` 或一轮 collab wait 等待；普通“仍在处理”不重置墙钟，也不算有效结果
  接管: 收到有效 partial handoff → 先 close 并确认关闭，再由主代理执行 pending_scope；没有有效回传 → close 并按原任务减去已验证范围接手，记录 timeout_no_handoff
  批次收敛: 所有代理必须进入 completed/failed/partial handoff/closed 之一后，才进入依赖下游步骤；已完成代理不因同批其他代理延迟而重做
  DO NOT: 用“有零散产出”重置墙钟；跳过强制回传直接关闭；原代理未 close 时执行重叠接管；超时后无条件全量重跑

降级前置（CRITICAL）:
  代理级接管: 只有触发墙钟超时或无有效 handoff 的代理需要 close；确认该代理关闭后，主代理才能接手其 pending_scope
  健康代理保留: 同批其他代理若仍在动态预算内正常推进，不得因某一代理超时而 close；它们继续独立收敛，结果照常保留
  最小启动数例外: 批次兼容重试收敛后仅 1 个代理成功启动时，优先执行上方“批次接受证据”的单代理 handoff+close；这属于编排未形成，不适用健康代理继续运行规则
  批次级切换: 连续失败阈值触发“主代理直接执行模式”只影响后续尚未派发的任务；不得终止当前健康代理，也不得在其仍运行时接手重叠范围
  DO NOT: 子代理仍在运行时主代理执行相同范围的任务（重复劳动+潜在文件冲突）

连续失败阈值:
  触发时机: 同一流程中（从进入 DESIGN 或 DEVELOP 阶段到状态重置之间）连续 2 个子代理超时/无返回
  触发后行为: → 进入"主代理直接执行模式"
    后续所有任务不再尝试 spawn_agent，主代理逐项直接执行
    标注: 在 tasks.md 相关任务后追加 [主代理直接执行]
  退出条件: 当前流程结束（状态重置时自动解除）
  首次运行失败: 降级当前任务 + 下一个任务仍尝试 spawn_agent；任务级墙钟超时先按强制 handoff 处理，只有没有有效回传且关闭后才计入本阈值；参数兼容性失败按上方兼容重试处理，不计入本阈值
  定位: 本阈值是失败后的兜底（连续 2 次确实超时/无返回才触发），不是编排前的预判回避

环境检测:
  /experimental 未开启 或 agents.max_threads=0 → 跳过所有子代理调度，主代理直接执行 + 标记 [降级执行] + 记录环境证据
  定位: 这是环境能力检测（编排前一次性判断），不是对子代理稳定性的预判回避

上下文预算感知（DELEGATED 模式）:
  跟踪: 记录子代理 spawn→close 循环累计次数（含所有任务的所有失败尝试），并记录每次 handoff 是否成功保留部分结果
  阈值: 同一流程中累计 ≥3 次 spawn→close 循环 → 进入主代理直接执行模式（与连续失败阈值触发相同行为）
  目的: 即使失败不连续（中间夹杂成功），累积的上下文消耗也可能过大
  定位: 本机制统计的是"已发生的 spawn→close 循环"，触发于实际消耗之后，非编排前的预判
```

---

## Codex CLI 子代理 EHRB 豁免规则（CRITICAL）

```yaml
问题: Codex CLI 无 SubagentStart/Stop hook，子代理对文件系统的操作完成后，
  主代理可能将其误判为"未由我直接触发的外部变更"误触发 EHRB 检测并安全暂停

RLM 角色操作豁免:
  RLM 角色子代理在其数据所有权范围内的操作 → 自动豁免 EHRB 检测，不触发安全暂停
  数据所有权范围（与 services/ 模块定义一致）:
    reviewer: 只读，不修改文件
    brainstormer: 只读，不修改文件
    writer: 任务描述中指定的输出文件路径
  豁免条件: 变更文件路径在该角色的数据所有权范围内
  非豁免: 变更超出角色数据所有权范围 → 按 G2 EHRB 标准流程处理

预期变更注册（通用，无 SubagentStop hook 的 CLI 均适用）:
  机制:
    1. 主代理在 spawn 子代理前，根据任务描述记录预期文件操作范围（哪些路径会被创建/修改/移动/删除）
    2. 子代理完成后，主代理检查实际变更是否在预期范围内
    3. 预期范围内 → 视为预期操作，继续执行，不触发 EHRB 检测
    4. 预期范围外 → 按 G2 EHRB 检测流程处理
  降级: 无法预判预期范围 → 回退到 RLM 角色数据所有权范围判定 → 仍无法判定 → 标准 EHRB 检测
```
