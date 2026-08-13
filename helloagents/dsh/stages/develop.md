# 开发实施模块 — DSH 适配版

本模块定义开发实施阶段的详细执行规则，执行方案包中的任务清单。
DSH 适配版：所有执行通过 DSH 内置工具完成，不依赖 Python 运行时。

**核心职责:** 执行 tasks.md 中的任务清单，通过子代理完成任务执行和知识库同步。

---

## 模块入口

```yaml
前置:
  NATURAL入口: 方案设计阶段完成（CREATED_PACKAGE 已设置，KB_SKIPPED 和 TASK_COMPLEXITY 已由 DESIGN Phase1 设置）
  DIRECT入口: ~exec 命令（KB_SKIPPED 和 TASK_COMPLEXITY 在本阶段首次设置）
设置: CURRENT_STAGE = DEVELOP
```

---

## 执行模式适配

| 入口 | 方案包来源 | 多包处理 |
|------|-----------|---------|
| NATURAL | CREATED_PACKAGE 变量 | 直接执行（仅1个包） |
| DIRECT (~exec) | 扫描 plan/ 目录 | 输出确认（方案包选择清单）→ ⛔ END_TURN |

| 模式 | 行为 | 完成后 |
|------|------|--------|
| INTERACTIVE | 执行全部步骤，每批暂停确认 | 输出完成 → 等待确认 |
| DELEGATED | 执行全部步骤，省略中间态 | 输出委托执行结果 → 状态重置 |

---

## 执行流程

### 步骤1: 加载方案包

> 使用 DSH 工具: `read`（读 tasks.md）、`glob`（查找 plan 目录）

1. 读取 `tasks.md` 获取任务清单
2. 读取 `proposal.md` 获取方案上下文
3. 识别 DAG 依赖关系（拓扑排序）
4. 加载 `dsh/rules/` 和 `dsh/agents/` 模块文件

### 步骤2: 设置工作变量

```yaml
KB_SKIPPED: 从 DESIGN Phase1 继承（或 ~exec 入口按 KB_CREATE_MODE 设置）
TASK_COMPLEXITY: 从 DESIGN Phase1 继承（或 ~exec 入口判定）
```

### 步骤3-5: 执行任务（按 DAG 依赖顺序）

#### 普通执行（非复杂编码）

按 DAG 拓扑顺序逐一或并行执行任务：

1. **锁定任务**: 从 DAG 中选择所有依赖已就绪的任务
2. **实施**: 使用 DSH 工具执行（`write`/`edit` 创建或修改文件，`pwsh` 运行命令）
3. **验证**: 对修改执行验证（lint/测试/内联验证）
4. **更新状态**: 在 tasks.md 中标记任务状态
5. **进入下一批**: 解锁下游任务

#### 复杂编码分批执行（`@execution_strategy: checkpoint-batch`）

仅当 `tasks.md` 顶部显式声明 `@execution_strategy: checkpoint-batch` 时启用：

```yaml
每批最多 3 个原子任务
风险收紧: 一般风险→2个，可恢复强风险→1个
风险信号: context_near_limit, output_scope_large, agent_wait_degraded, compaction_state_missing
每批流程: 锁定范围 → 实施 → 聚焦验证 → 更新 tasks.md → 输出短摘要
阻断性风险: package_incomplete → 不得以单任务批次继续
```

### 步骤6: KB 同步

> 使用 DSH 工具: `read`（读现有文件）、`write`/`edit`（写更新）

1. 更新 `CHANGELOG.md`（记录变更摘要）
2. 更新 `modules/`（按模块记录变更）
3. 更新方案包状态（`.status.json` 标记完成）
4. 移动方案包到 `archive/`（完成后归档）

### 步骤7: 验收

> 使用 DSH 工具: `pwsh`（运行命令）、`read`（检查结果）

1. **变更已应用**: 确认所有文件修改已写入
2. **目标验证**:
   - 优先探测项目验证工具（`runbook.yaml` → `package.json scripts` → `pyproject.toml`）
   - 有 lint/类型检查 → 对修改文件执行
   - 有测试命令 → 运行相关测试
   - 均不可用 + 可执行代码 → 内联验证（构造最小输入验证输出）
   - 均不可用 + 配置文件 → 语法检查
   - 纯文本 → 跳过

### 步骤8: 完成

输出验收报告：

```yaml
格式: ✅ 状态栏 + 执行结果 + 变更摘要 + 下一步引导
```

---

## DSH 工具映射

| 操作 | DSH 工具 | 说明 |
|------|---------|------|
| 读文件 | `read` | 读取方案包、项目文件 |
| 写文件 | `write` | 创建新文件 |
| 编辑文件 | `edit` | 修改已有文件 |
| 搜索文件 | `glob` | 查找文件路径 |
| 搜索内容 | `grep` | 搜索文件内容 |
| 运行命令 | `pwsh` | 执行 Shell 命令 |
| 子代理 | `subagent` | 派发任务子代理 |
| 任务列表 | `todo_write` | 跟踪实施进度 |
| 网络搜索 | `web_search` | 技术查询 |
| 后台任务 | `job_output`/`job_kill` | 管理长时间运行任务 |

## 子代理使用

开发实施阶段适合派发子代理的场景：

| 场景 | 工具 | 说明 |
|------|------|------|
| 并行探索 | `subagent` | 多个独立模块同时探索 |
| 代码审查 | `subagent` | 独立审查已修改文件 |
| 技术调研 | `subagent` + `web_search` | 查询最佳实践 |
| 独立模块实现 | `subagent` | 无依赖的模块并行实现 |

> 派生时省略全部可选参数（不传 agent_type/model/reasoning_effort），由泛型派生加载默认配置。