# 知识库服务 — DSH 适配版

本文件定义 DSH 环境下的知识库操作规则。

## 知识库目录结构

```
{KB_ROOT}/  （默认项目根 .helloagents/）
├── INDEX.md            # 知识库索引
├── context.md          # 项目上下文
├── CHANGELOG.md        # 变更日志
├── modules/            # 模块文档
│   ├── _index.md       # 模块索引
│   └── {module}.md     # 模块文档
├── plan/               # 方案包
│   └── YYYYMMDDHHMM_<feature>/
│       ├── proposal.md # 方案说明
│       └── tasks.md    # 任务清单
└── archive/            # 归档
    ├── _index.md
    └── YYYY-MM/
```

## KB_CREATE_MODE 行为

| 模式 | 行为 |
|------|------|
| 0 | KB_SKIPPED=true，跳过所有知识库操作（已有 KB_ROOT 时仍更新 CHANGELOG） |
| 1 | 知识库不存在时提示"建议执行 ~init" |
| 2 | 编程任务时自动创建/更新，其余同模式1 |
| 3 | 始终自动创建 |

## 操作规则

### 读取知识库

> 使用 DSH 工具: `read`、`glob`

```yaml
步骤:
  1. 使用 glob 检查 {KB_ROOT}/INDEX.md 是否存在
  2. 存在 → 读取 INDEX.md 获取模块索引
  3. 按需读取 context.md、CHANGELOG.md、modules/{module}.md
```

### 更新知识库

> 使用 DSH 工具: `read`（先读）、`write`/`edit`（后写）

```yaml
CHANGELOG.md 更新格式:
  - 快速修改: - **[模块名]**: 描述 (类型标注)
  - 方案包完成: - **功能**: {feature} - {描述}

modules/ 更新:
  - 首次写入时创建 _index.md
  - 每个模块创建 {module}.md

plan/ 更新:
  - 创建方案包时写入 proposal.md + tasks.md
  - 完成后更新 .status.json

archive/ 更新:
  - 首次写入时创建 _index.md
  - 按月归档 YYYY-MM/
```

## 写入策略

- 目录/文件不存在时自动创建
- 禁止在 {KB_ROOT}/ 外创建知识库文件
- 动态目录（archive/_index.md、archive/YYYY-MM/、modules/_index.md）在首次写入时创建