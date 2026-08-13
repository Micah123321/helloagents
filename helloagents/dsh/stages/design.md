# 方案设计模块 — DSH 适配版

本模块定义方案构思和详细规划的执行规则，在 R2 标准流程下执行。
DSH 适配版：所有阶段执行通过 DSH 内置工具完成，不依赖 Python 运行时。

**核心职责:** 收集项目上下文（Phase1）+ 设计实现方案（Phase2），生成方案包（proposal.md + tasks.md）。

---

## 模块入口

```yaml
前置: EVALUATE 阶段完成（评估确认：核心维度全部充分 或 最后一轮追问确认合一已完成）
设置: CURRENT_STAGE = DESIGN
```

---

## 执行模式适配

| 模式 | TASK_COMPLEXITY=complex | TASK_COMPLEXITY=simple/moderate |
|------|----------|----------|
| INTERACTIVE | 输出方案对比→用户选择→详细规划→进入 DEVELOP | Phase1+Phase2(跳过多方案对比)→进入 DEVELOP |
| DELEGATED | 推荐方案作为选择→详细规划→进入 DEVELOP | Phase1+Phase2(跳过多方案对比)→进入 DEVELOP |

⚠️ 选择方案 = 确认执行，不再有第二次确认

### 阶段切换

```yaml
方案类型约束:
  R2 标准流程（通用路径、~auto、~plan）: 类型始终为 implementation → 进入 DEVELOP

方案确定后:
  implementation 类型:
    设置 CREATED_PACKAGE = 方案包路径
    CURRENT_STAGE = DEVELOP → 加载 dsh/stages/develop.md → 进入 DEVELOP
```

---

## 执行流程

### Phase1: 上下文收集

> 使用 DSH 内置工具: `read`（读文件）、`glob`（路径匹配）、`grep`（内容搜索）、`pwsh pwd`（当前目录）

1. **读取项目上下文**（使用 `read` 工具）:
   - `AGENTS.md` 或 `README.md`（项目根目录）
   - `.helloagents/context.md`（知识库上下文文件）
   - `.helloagents/INDEX.md`（知识库索引）
   - 关键配置文件（`package.json`、`pyproject.toml`、`Cargo.toml` 等，使用 `glob` 查找）

2. **目录结构扫描**（使用 `glob` 工具）:
   - 扫描项目的主要目录结构
   - 识别源代码目录、测试目录、配置文件位置

3. **知识库检查**（按 KB_CREATE_MODE）:
   - 模式 0: KB_SKIPPED=true，跳过知识库操作
   - 模式 1: 知识库不存在时提示"建议执行 ~init"
   - 模式 2: 编程任务时自动创建/更新知识库
   - 模式 3: 始终自动创建知识库

4. **TASK_COMPLEXITY 判定**:
   - 多交付物/架构未定/技术选型/用户明确要求多方案 → complex
   - 其余 → simple/moderate

### Phase2: 需求分析与方案规划

#### TASK_COMPLEXITY=complex — 多方案对比

1. **并行派发 brainstormer 子代理**（使用 `subagent` 工具）:
   - 每个子代理独立构思一个差异化方案
   - 至少 3 个 brainstormer 实际启动
   - 子代理 prompt 中指定差异化方向
   - 子代理任务自包含（含项目上下文、需求信息）

2. **方案比较与选择**:
   - 收集所有子代理返回的方案
   - 综合评估：技术可行性、实施成本、风险、维护性
   - DELEGATED 模式：推荐最优方案并记录理由
   - INTERACTIVE 模式：输出方案对比供用户选择

3. **生成方案包**:
   - 创建 `plan/{timestamp}_{feature}/` 目录
   - 写入 `proposal.md`（方案说明+选择理由）
   - 写入 `tasks.md`（DAG 任务清单+验收项）

#### TASK_COMPLEXITY=simple/moderate — 唯一方案

1. **直接确定方案**（跳过多方案对比）
2. **生成方案包**:
   - 创建 `plan/{timestamp}_{feature}/` 目录
   - 写入 `proposal.md`（方案说明）
   - 写入 `tasks.md`（任务清单+验收项）

### Phase3: 方案包生成规范

#### proposal.md 结构

```markdown
# {方案名称}

## 概述
{一句话描述}

## 需求分析
{需求理解摘要}

## 方案设计
{核心设计思路}

## 技术选型
{技术栈选择及理由}

## 实施路径
{实施步骤概要}

## 验收标准
{可验证的完成条件}
```

#### tasks.md 结构

```markdown
# 任务清单

## 依赖关系
```text
graph TD
  task1 --> task2
  task1 --> task3
  task2 --> task4
```

## 任务

### Task 1: {任务名称}
- **描述:** {任务描述}
- **依赖:** 无
- **验收:** {验收条件}
- **状态:** [ ]

### Task 2: {任务名称}
- **描述:** {任务描述}
- **依赖:** Task 1
- **验收:** {验收条件}
- **状态:** [ ]
```

---

## DSH 工具映射

| 操作 | DSH 工具 | 说明 |
|------|---------|------|
| 读文件 | `read` | 读取项目文件、知识库 |
| 搜索文件 | `glob` | 按路径模式查找文件 |
| 搜索内容 | `grep` | 搜索文件内容 |
| 写文件 | `write` | 创建方案包文件 |
| 编辑文件 | `edit` | 修改已有文件 |
| 查目录 | `pwsh pwd` | 获取当前工作目录 |
| 子代理 | `subagent` | 派发 brainstormer |
| 搜索网络 | `web_search` | 技术调研 |
| 任务列表 | `todo_write` | 跟踪任务进度 |