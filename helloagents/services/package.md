# 方案包服务 (PackageService)

本模块定义方案包服务的完整规范，包括服务接口、执行者、数据所有权和生命周期管理。

---

## 服务概述

```yaml
服务名称: PackageService（方案包服务）
服务类型: 领域服务
适用范围: 所有涉及方案包操作的命令和阶段

核心职责: 方案包创建/初始化、任务状态管理、进度快照、归档迁移、遗留方案包扫描清理

执行者: 主代理（按服务接口规范直接执行）
数据所有权:
  - {KB_ROOT}/plan/（活跃方案包）
  - {KB_ROOT}/archive/（已归档方案包）
```

---

## 服务接口

**DO:** 所有方案包操作通过服务接口执行

**DO NOT:** 直接操作方案包文件，绕过服务接口修改

### create(feature, type)

```yaml
触发: design 阶段步骤11
前置条件: 编程任务（涉及代码创建/修改/删除/重构/测试编写）。非编程任务（纯文档/设计/分析/翻译等不产生代码变更）跳过方案包创建，直接输出方案摘要
参数: feature(功能名), type(implementation|overview)
流程: 生成路径 plan/YYYYMMDDHHMM_{feature}/ → 冲突检查(使用_v2,_v3) → create_package.py → 填充 → 验证
返回: success, package_path, errors
保证: proposal.md + tasks.md 完整，格式符合规范
质量要求:
  proposal.md:
    - 包含需求、方案、影响范围、风险评估
    - R2 implementation 方案应包含方案取舍与验证策略
    - code-review 方案包应包含 conservative_plan、aggressive_plan、selected_plan=conservative 和审查问题摘要
  tasks.md:
    - 每个任务是原子操作
    - 每个任务包含文件路径或明确作用范围
    - 每个任务包含预期变更、完成标准、验证方式、depends_on
    - 任务可独立执行、独立验证，依赖关系可拓扑排序
    - code-review 方案包默认只写入保守方案任务；激进方案作为 proposal.md 备选，不进入默认待执行任务列表
```

### updateTask(taskId, status, result)

```yaml
触发: develop 阶段每个任务完成后
参数: taskId("阶段号-任务号"), status(completed|failed|skipped|pending), result(可选)
流程: 读取 tasks.md → 定位任务 → 更新状态符号 → 添加备注 → 更新统计 → 追加日志(最近5条) → 写回
返回: success, progress, errors
保证: 状态一致性（只能从 pending 转换），日志完整，统计准确，完成备注能对应任务的完成标准或验证方式
```

### snapshot()

```yaml
触发: 任务完成后、阶段转换时
流程: 读取 tasks.md → 统计状态 → 计算百分比 → 更新 LIVE_STATUS 区域 → 追加日志
LIVE_STATUS 格式: 按 G11 定义
返回: success, progress
```

### archive(packagePath)

```yaml
触发: develop 阶段步骤14
流程: 验证方案包状态 → 归档到 archive/YYYY-MM/ → migrate_package.py → 更新 archive/_index.md → 清除 INDEX.md "活跃方案包"指向 → KnowledgeService.updateChangelog()
返回: success, archive_path, changelog_updated
保证: 原路径清理、归档索引更新、活跃方案包指向已清除、CHANGELOG 已记录
```

### scan()

```yaml
触发: 阶段完成时（仅 plan/ 目录存在时执行）
流程: 扫描 plan/ 目录中的遗留方案包
返回: packages[{path, name, created, type}]
条件输出: ≥1个遗留方案包返回列表，否则空列表
```

### validate(packagePath)

```yaml
触发: 方案包创建后、执行前
流程: validate_package.py → 检查必需文件 → 检查格式 → 解析任务列表
返回: valid, issues[{type(blocking|warning), message}]
验收项:
  ⛔ 阻断性: proposal.md 和 tasks.md 存在且非空，tasks.md 至少包含 1 个任务项
  ⚠️ 警告性: proposal.md 缺少方案取舍、验证策略或风险边界
  ⚠️ 警告性: tasks.md 任务缺少文件路径/作用范围、预期变更、完成标准、验证方式或 depends_on
  ⚠️ 警告性: tasks.md 任务粒度过大，无法独立验证
```

---

## 执行者说明

```yaml
执行者: 主代理按服务接口规范直接执行所有方案包操作
职责: 方案包内容填充、任务状态更新、进度快照生成、质量检查
协作: 接收方案设计结果→填充 proposal.md | 接收代码实现结果→更新 tasks.md
```

---

## 生命周期管理

| 阶段 | 触发 | 操作 | 状态 |
|------|------|------|------|
| 创建 | design 阶段方案确定后 | create(feature, type) | @status: pending |
| 开发 | develop 阶段每个任务完成后 | updateTask() + snapshot() | pending → in_progress → completed/failed |
| 归档 | develop 所有任务完成后 | archive() → updateChangelog() | 移动到 archive/YYYY-MM/ |

### Overview 类型特殊处理

```yaml
判定: tasks.md 无执行任务
归档: 按本服务 archive() 接口执行
标记: archive/_index.md 中标注 "overview"
```

### Code-review 类型特殊处理

```yaml
触发: ~review 发现问题后自动创建 plan/YYYYMMDDHHMM_code-review/ 方案包
proposal.md 必填:
  - 审查范围、审查结果摘要、high/medium/low 问题列表
  - conservative_plan: 默认执行路径，最小必要修复，低风险、局部改动、保持现有行为稳定
  - aggressive_plan: 备选路径，更大范围重构、抽象收敛或结构清理
  - selected_plan: conservative
  - 方案取舍: 说明默认运行保守方案，激进方案仅在用户明确指定时执行
tasks.md 必填:
  - 仅包含 conservative_plan 对应的默认可执行任务
  - 每个任务仍需包含文件路径/作用范围、预期变更、完成标准、验证方式、depends_on
执行:
  - 创建并验证方案包后，由 ~review 设置 CURRENT_PACKAGE
  - 进入 DEVELOP 阶段直接执行默认保守任务，不再要求用户手动运行 ~exec
  - EHRB、方案包验证失败、开发实施失败仍按对应规则中断或处理
```

---

## 与其他服务的协作

```yaml
→ KnowledgeService: 归档后调用 updateChangelog()
← AttentionService: 进度快照输出
```

---

## 用户选择规则

### Overview 类型方案包处理

```yaml
触发: ~exec 检测到 overview 类型方案包
选项: 归档(调用 archive()) | 查看(显示 proposal.md) | 取消(→ 状态重置)
```

### 遗留方案包扫描

```yaml
触发: 阶段完成时检测到 ≥1 个遗留方案包
选项: 清理(→ ~cleanplan) | 忽略(继续当前操作)
```

---

## 异常处理

| 异常 | 处理 |
|------|------|
| 方案包创建失败 | 检查 plan/ 目录 → 检查命名冲突 → 暂停提示 |
| 任务更新失败 | 重试一次 → 仍失败记录错误 → 验收报告标注 |
| 归档失败 | 检查 archive/ 目录 → 检查权限 → 重试 → 保留原位 |
| 索引更新失败 | _index.md 不存在时创建 → 写入失败在报告中标注 |
