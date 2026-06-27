# ~test 命令 - 运行测试

本模块定义运行测试的执行规则。

---

## 命令说明

```yaml
命令: ~test
类型: 场景确认类
功能: 检测框架运行测试并分析结果
评估: 需求理解 + EHRB 检测（不评分不追问）
```

---

## 执行模式适配

```yaml
规则:
  1. 独立工具命令，不受 WORKFLOW_MODE 影响
  2. 优先解析项目上下文和 runbook workflow，再回退框架检测
  3. 自动识别“最新 commit / 最近提交 / 所有修复功能”等测试意图
  4. 多个同优先级本地 workflow 或多框架共存时才询问用户选择
  5. 无法检测时请求用户提供测试命令
  6. 测试失败时提供修复方案选项
```

---

## 执行流程

### 步骤1: 需求理解 + EHRB 检测

```yaml
解析输入:
  - 项目定位: 项目 id/alias、项目根路径、project.yaml/runbook.yaml/secrets.local.yaml 路径
  - 测试意图: 最新 commit、最近提交、本次提交、所有修复、修复功能、全量回归、指定测试命令
  - 环境意图: local/dev/test/production

安全:
  - 若用户输入明文密码，不在回复、日志、方案包或知识库中复述
  - 提示改用 password_ref（如 env:SITEGUARD_AI_PASSWORD）或 secrets.local.yaml profiles
  - remote/protected/production workflow 只预览，不在本步骤执行
```

### 步骤2: 扫描测试环境

```yaml
扫描（多个独立检测项，同一消息中发起多个并行工具调用）:
  1. 优先调用 ProjectEnvService.resolveProjectContext(input, cwd):
     - 当前目录存在 .helloagents/project.yaml → 使用当前项目
     - 输入包含项目 id/alias → 读取 ~/.helloagents/projects.yaml 或 project.yaml aliases 定位项目
     - 输入包含配置文件路径 → 自动推导同目录 project.yaml/runbook.yaml/secrets.local.yaml，不要求用户逐个列出
  2. 调用 ProjectEnvService.resolveTestIntent(input, project_context):
     - “最新 commit/最近提交/本次提交/HEAD” → latest_commit
     - “所有修复/修复功能/fixes” → latest_commit_fixes
     - “全部/全量/回归” → all
  3. 调用 ProjectEnvService.validationCommands(scope=test):
     - 按测试意图优先读取 runbook validation.workflows.latest_commit / workflows.latest_commit_fixes
     - 其次读取 validation.before_commit、validation.workflows.default、workflows.*.default=true、workflows.local_iteration
     - 命中唯一的本地测试 workflow → 作为推荐测试命令，可直接进入确认执行
     - 命中远程/protected workflow → 输出目标环境和命令预览，按确认规则处理
  4. 未命中 ProjectEnvService → 并行读取项目配置文件（package.json/pyproject.toml 等）中的测试配置 + 常见测试目录（test/tests/__tests__/）+ 文件命名模式（*_test.*/*.spec.*）
  汇总: 根据 ProjectEnvService 或并行读取结果识别测试框架/测试命令

少问确认:
  - 唯一本地 workflow + 唯一命令组: 输出测试计划确认，不再询问配置文件或密码
  - 多个本地 workflow 同优先级命中: 询问用户选择
  - 多框架共存且 runbook 未指定默认 workflow: 询问用户选择
  - secrets.local.yaml 存在 password_ref/profile: 只显示引用名，不读取真实密码

无法检测: 请求用户提供测试命令

输出: 确认（测试框架选择）
⛔ END_TURN
用户确认后: 选择框架N / 全部运行 / 输入测试命令 / 取消(→状态重置)
```

### 步骤3: 执行测试

```yaml
执行: 测试命令（带超时保护）→ 捕获输出和退出码

结果分析:
  1. 解析通过/失败/跳过统计
  2. 提取失败测试的文件路径和行号
  3. 分析错误信息确定失败原因
  4. 判断是否为阻断性测试失败
  5. 生成修复建议
```

### 步骤4: 后续操作

```yaml
有失败时:
  输出: 确认（测试结果摘要+失败列表+修复建议）
  ⛔ END_TURN
  用户确认后:
  生成修复方案: 创建 plan/YYYYMMDDHHMM_fix-tests/ 方案包
  仅记录报告: 输出完整报告
  跳过: 不执行操作

→ 状态重置
```

---

## 不确定性处理

| 场景 | 处理 |
|------|------|
| 无法检测框架 | 询问用户提供测试命令 |
| 多框架共存 | 列出选项请用户选择 |
| 项目别名未命中 | 提示先运行 `~ssh <项目名>` 绑定，或提供项目根路径 |
| 用户只提供 project.yaml/runbook.yaml/secrets.local.yaml 其中之一 | 自动推导同目录下其他配置文件 |
| 用户输入明文密码 | 不复述密码，提示轮换并改为 password_ref |
| “最新 commit”但无 Git 信息 | 回退 runbook 默认 workflow，并在结果中标注 |
| 测试超时 | 询问是否延长或终止 |
| 输出无法解析 | 返回原始输出，建议手动分析 |

---

## 交付检查

- [ ] 测试命令已实际执行并捕获退出码，未跳过执行直接声称结果
- [ ] 失败测试已定位到文件路径和行号
- [ ] 失败根因已分析（而非仅复制错误信息）
- [ ] 修复建议针对失败根因，未修补症状
- [ ] 生成修复方案包时，tasks.md 仅包含保守可执行任务（不混入备选方案）

**元认知自检:** 如果某测试一运行就直接通过（无任何修改即绿），说明它没有验证被测行为——重新审视测试是否覆盖了真实断言，而非恒真断言。
