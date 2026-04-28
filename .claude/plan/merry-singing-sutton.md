# 优化 HelloAGENTS 工作流：小任务效率问题

## Context

用户在 Xboard-new 项目中执行了一个极简任务（在 docker-publish.yml 的 paths-ignore 中加一行 `.helloagents/**`），但经过 R2 标准流程（评估→确认→DESIGN Phase1 6步→Phase2 方案包创建/验证→DEVELOP 15步→KB同步→归档）花了约 20 分钟。根因是两个层面：

1. **路由判定偏高** — 该任务符合 R1 全部条件（目标文件/位置/内容全部已知、路径唯一、单点可逆、无 EHRB），但被判定为 R2
2. **R2 对 simple 任务开销过大** — 即使正确走了 R2，完整方案包生命周期（创建→填充→验证→执行→归档）对单行改动是过度工程

## 优化方案

### 改动 1: 强化 G4 路由判定锚点（CLAUDE.md 全局规则）

**文件**: `C:/Users/xiaohuli/.claude/CLAUDE.md` — G4 路由规则章节

在 `通用路径级别判定` 的维度表之后、`各级别行为` 之前，新增 **R1 快判锚点** 小节：

```yaml
R1 快判锚点（AI 校准用，匹配任一模式即可快速判定 R1）:
  模式A — 已知位置单点修改:
    特征: 用户指定了具体文件 + 修改位置可从描述直接确定 + 改动为增删改≤5行
    典型: "在 X 文件的 Y 位置加一行 Z"、"把 A 文件里的 B 改成 C"、"删除 X 文件的 Y 行"
  模式B — 已知命令执行:
    特征: 用户要求执行一条具体命令或运行一个脚本 + 无需选择参数
    典型: "运行 npm test"、"执行 migrate"、"格式化 src/ 目录"
  模式C — 已知模式复制:
    特征: 参照已有代码/配置添加同类项 + 不改变架构
    典型: "像 X 一样加一个 Y"、"在现有列表里追加 Z"
  校准原则:
    - 匹配锚点 = 强信号 R1，仍需逐维度确认（防止 EHRB 漏检）
    - 不匹配锚点 ≠ 一定是 R2，继续正常维度判定
    - 锚点仅辅助 AI 校准判定阈值，不改变维度判定规则本身
```

### 改动 2: R2 simple 轻量通道（design.md + develop.md）

**文件**: `C:/Users/xiaohuli/.claude/helloagents/stages/design.md`

在 Phase2 步骤7 `模式分支判定` 中，为 `TASK_COMPLEXITY=simple` 增加轻量路径：

```yaml
| TASK_COMPLEXITY=simple | 跳过多方案对比 + 跳过方案包创建 | → 轻量 DEVELOP |

TASK_COMPLEXITY=simple 轻量路径:
  条件: simple 且 涉及文件≤3 且 总改动行≤30
  行为:
    - 跳过 create_package.py、proposal.md、tasks.md、validate_package.py
    - 直接在 DESIGN 阶段输出轻量方案摘要（需求+方案+风险+验证方式，≤200字）
    - 设置 LIGHTWEIGHT_DESIGN = true
    - 直接进入 DEVELOP（不创建 CREATED_PACKAGE）
  回退: 条件不满足 → 走现有 simple/moderate 路径（创建方案包）
```

**文件**: `C:/Users/xiaohuli/.claude/helloagents/stages/develop.md`

在步骤1 `确定待执行方案包` 中增加轻量入口：

```yaml
LIGHTWEIGHT入口（LIGHTWEIGHT_DESIGN=true，从轻量 DESIGN 进入）:
  无方案包: 基于 DESIGN 阶段的轻量方案摘要直接执行
  流程简化:
    - 步骤1: 跳过（无方案包）
    - 步骤2: 环境变量检查（保留）
    - 步骤3-5: 跳过（无方案包读取、无额外上下文收集）
    - 步骤6: 主代理直接执行改动（不调度子代理）
    - 步骤7: EHRB 检查（保留）
    - 步骤8: 按 R1 验收标准执行（探测项目工具→有则用，无则跳过）
    - 步骤9: 跳过完整交付验收（功能验收由步骤8覆盖）
    - 步骤10-12: KB 同步按 R1 规则（CHANGELOG 快速修改分类）
    - 步骤13: 跳过
    - 步骤14: 跳过归档（无方案包）
    - 步骤15: 遗留方案包扫描（保留）
```

### 改动 3: 状态变量扩展（stages.md G6）

**文件**: `C:/Users/xiaohuli/.claude/rules/helloagents/stages.md` — G6 状态变量定义

新增变量：

```yaml
LIGHTWEIGHT_DESIGN: false  # DESIGN Phase2 simple 轻量路径设为 true
```

在状态重置协议中将 `LIGHTWEIGHT_DESIGN` 加入任务重置列表。

## 涉及文件清单

| 文件 | 改动类型 | 改动量 |
|------|---------|--------|
| `C:/Users/xiaohuli/.claude/CLAUDE.md` | 在 G4 级别判定后新增 R1 锚点 | ~15 行 |
| `C:/Users/xiaohuli/.claude/helloagents/stages/design.md` | 步骤7 增加 simple 轻量路径 | ~15 行 |
| `C:/Users/xiaohuli/.claude/helloagents/stages/develop.md` | 步骤1 增加 LIGHTWEIGHT 入口 | ~20 行 |
| `C:/Users/xiaohuli/.claude/rules/helloagents/stages.md` | G6 新增状态变量 + 重置规则 | ~5 行 |

## 预期效果

- **路由正确时（R1）**: 单行改动走 R1 快速流程，预计 2-3 分钟完成
- **路由偏高时（R2 simple）**: 轻量通道跳过方案包生命周期，预计 5-8 分钟完成（比现在 20 分钟减少 60%+）
- **不影响**: moderate/complex 任务的完整流程不变

## 验证方式

- 在另一个项目中测试「在 X 文件 Y 位置加一行 Z」类任务，观察是否正确判定 R1
- 用 `~auto` 强制 R2 执行一个 simple 任务，验证轻量通道是否跳过方案包创建
- 验证 moderate/complex 任务不受影响（仍走完整方案包流程）
