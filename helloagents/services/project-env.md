# 项目环境服务 (ProjectEnvService)

本模块定义项目级服务器、环境、路径和运行命令配置的读取与维护规则。

---

## 服务概述

```yaml
服务名称: ProjectEnvService（项目环境服务）
服务类型: 领域服务
适用范围: ~ssh、~test、~verify、~loop、R1/R2 验证、DEVELOP 阶段、远程测试/部署/日志查看请求

核心职责:
  - 管理项目内 .helloagents/project.yaml、secrets.local.yaml、runbook.yaml
  - 识别开发/测试/生产环境、远程服务器角色、远程项目路径和日常命令
  - 为测试、迭代、部署、日志、回滚等流程提供命令来源
  - 为敏感连接信息和生产环境动作提供安全边界

执行者: 主代理（按服务接口规范直接执行）
数据所有权:
  - {KB_ROOT}/project.yaml
  - {KB_ROOT}/project.local.yaml（可选，本机覆盖，默认不提交）
  - {KB_ROOT}/secrets.local.yaml（本机敏感连接信息，禁止提交）
  - {KB_ROOT}/runbook.yaml
排除:
  - 真实私钥文件
  - 系统级 ~/.ssh/config
  - Windows Credential Manager / 1Password / KeePass / 环境变量中的真实凭据
```

---

## 配置文件模型

### project.yaml（可提交）

```yaml
用途: 项目环境结构、环境角色、host_ref、远程路径、非敏感命令、安全策略
允许内容:
  - 项目名称、类型、本地根路径
  - local/dev/test/production 环境定义
  - 每个环境的 role、host_ref、workspace、log_dir、upload_dir
  - commands 中的 install/lint/test/build/status/logs 等非敏感命令
  - protected、requires_confirmation、blocked_actions 等安全策略
禁止内容:
  - 明文密码
  - 私钥内容
  - API token
  - 数据库连接密码
```

### secrets.local.yaml（禁止提交）

```yaml
用途: 本机连接信息和敏感信息引用
允许内容:
  - host_ref 对应的 ip、port、user、ssh_alias
  - private_key_path（路径引用，不是私钥内容）
  - password_ref（如 env:NAME、wincred:NAME、1password:NAME、keepass:NAME）
  - Windows 本地 shell、OpenSSH 路径、workspace 覆盖
不推荐但可识别:
  - plaintext_password
处理: 仅允许测试/开发环境；必须警告；production 中出现时视为 EHRB 风险
```

### runbook.yaml（可提交）

```yaml
用途: 日常流程和命令编排
常见 workflow:
  - local_iteration: 本地迭代验证
  - test_iteration: 测试环境验证
  - deploy_test: 测试环境部署
  - deploy_production: 生产部署
  - rollback_production: 生产回滚
  - logs_test / logs_production: 日志查看
命令来源:
  - command: 直接命令
  - command_ref: 引用 project.yaml commands
  - action: ssh/scp/local/run
```

### project.local.yaml（可选，禁止提交）

```yaml
用途: 覆盖 project.yaml 中不适合提交的本机路径或工具路径
优先级: 高于 project.yaml，低于用户本轮明确指令
```

---

## 读取优先级

```text
用户本轮明确指令
  > {KB_ROOT}/project.local.yaml
  > {KB_ROOT}/secrets.local.yaml
  > {KB_ROOT}/runbook.yaml
  > {KB_ROOT}/project.yaml
  > {KB_ROOT}/verify.yaml
  > package.json / pyproject.toml / Makefile 等自动检测
```

**DO:** 读取项目环境配置时同时报告使用的 environment、host_ref、workspace 和命令来源。

**DO NOT:** 在未确认目标环境和命令前连接远程服务器；把 secrets.local.yaml 内容写入回复、日志、方案包或知识库归档。

---

## 服务接口

### detect()

```yaml
触发:
  - ~test / ~verify / ~loop
  - R1/R2 验证命令探测
  - DEVELOP 阶段步骤8/9
  - 用户请求测试、迭代、部署、日志、远程检查

流程:
  1. 检查 {KB_ROOT}/project.yaml、project.local.yaml、secrets.local.yaml、runbook.yaml 是否存在
  2. 解析可用环境、host_ref、workspace、命令和 workflows
  3. 检查敏感信息泄露风险
  4. 返回 project_env_context

返回:
  exists: true|false
  environments: [...]
  workflows: [...]
  validation_commands: [...]
  warnings: [...]
```

### initOrUpdate(input)

```yaml
触发: ~ssh 命令
输入: 用户提供的服务器、环境角色、远程路径、命令、连接方式
流程:
  1. 读取现有配置（如存在）
  2. 合并用户新提供的信息
  3. 缺少关键字段时追问：环境角色、host_ref、workspace、连接引用、日常命令
  4. 生成或更新 project.yaml / secrets.local.yaml / runbook.yaml
  5. 检查 .gitignore 是否忽略 secrets.local.yaml、project.local.yaml、*.pem、*.key
  6. 输出文件变更和安全提示

验收:
  - project.yaml 至少包含 project、environments、paths 或 commands
  - secrets.local.yaml 至少包含 hosts 或 credential_refs（用户明确跳过敏感配置时可为空模板）
  - runbook.yaml 至少包含 local_iteration 或 validation.before_commit
```

### resolveWorkflow(name, environment)

```yaml
触发: 执行测试/迭代/部署/日志请求时
流程:
  1. 在 runbook.yaml 中查找 workflow
  2. 解析 environment → host_ref → workspace
  3. 展开 command_ref
  4. 判定是否 remote/protected/production/requires_confirmation
  5. 返回执行计划

远程执行约束:
  - ssh_alias 优先于 ip+port+user 拼接
  - Windows 本地开发机默认使用 PowerShell 和 OpenSSH
  - 所有远程副作用命令执行前必须展示目标环境、服务器别名、远程路径和命令
```

### validationCommands(scope)

```yaml
触发:
  - ~test
  - DEVELOP 步骤8
  - Ralph Loop

优先级:
  1. runbook.yaml workflows.local_iteration.steps 中的 lint/test/typecheck/build 命令
  2. runbook.yaml validation.before_commit
  3. verify.yaml commands
  4. package.json scripts
  5. pyproject.toml 工具配置

返回:
  commands: [...]
  source: runbook|verify|package_json|pyproject|auto
```

---

## 安全规则

### 敏感信息边界

```yaml
禁止提交:
  - {KB_ROOT}/secrets.local.yaml
  - {KB_ROOT}/project.local.yaml
  - {KB_ROOT}/secrets.*.yaml
  - {KB_ROOT}/*.pem
  - {KB_ROOT}/*.key
  - {KB_ROOT}/*.password

推荐凭据引用:
  - env:NAME
  - wincred:target-name
  - 1password:item/field
  - keepass:path/to/entry
  - ssh-config:alias

明文密码处理:
  - dev/test: 输出警告，允许继续但要求 secrets.local.yaml 不提交
  - production: 视为 EHRB 风险，必须要求用户改为 password_ref 或 ssh_key
```

### 生产环境保护

```yaml
触发条件:
  - environment 名称为 production/prod/live
  - role: production
  - protected: true
  - requires_confirmation: true

必须确认的动作:
  - deploy
  - restart
  - rollback
  - database_write
  - cache_flush
  - destructive_command
  - remote_command（有副作用）

确认内容:
  - 目标环境
  - host_ref / ssh_alias
  - 远程 workspace
  - 即将执行的命令
  - 回滚或停止方式（如已定义）
```

### EHRB 集成

```yaml
远程命令执行前:
  - 先按 G2 执行完整 EHRB 检测
  - 命中生产环境/破坏性命令/权限变更/缓存清空/数据库写入时，降级为 INTERACTIVE
  - Codex CLI 无 PreToolUse Hook 时，主代理规则层必须执行同等检查
```

---

## Windows 本地开发规则

```yaml
本地 host os=windows 时:
  shell: powershell
  path_style: windows
  workspace: 使用正斜杠或双反斜杠均可，但执行前必须正确引用
  ssh_client: 默认使用 Windows OpenSSH，若模板中指定则优先
  写文件: UTF-8 无 BOM
  多行命令: 优先临时 .ps1，避免 Bash 语法

DO:
  - PowerShell 路径使用引号或 -LiteralPath
  - ssh/scp 路径和参数逐项引用
DO NOT:
  - 在 PowerShell 中使用 Bash 专属语法
  - 混用 PowerShell 枚举和 cmd 删除命令
```

---

## 与命令流程协作

### ~ssh

```yaml
职责: 初始化或更新 ProjectEnvService 配置
闸门: 轻量确认
输出: 创建/更新的文件 + 安全提示 + 后续可用 workflow
```

### ~test / ~verify / DEVELOP

```yaml
执行前:
  - 调用 validationCommands(scope)
  - 若 runbook 提供命令，优先使用
  - 若命令目标为 remote/protected，按确认规则暂停
  - 否则回退现有自动探测
```

### ~auto / ~build / 通用 R2

```yaml
上下文收集:
  - 若项目存在 project.yaml/runbook.yaml，作为实施条件和验证条件来源
  - 方案包 proposal.md 的验证策略应记录使用的 environment/workflow
```

---

## 异常处理

| 异常 | 处理 |
|------|------|
| project.yaml 不存在 | 回退现有自动检测；涉及服务器时提示使用 ~ssh 初始化 |
| secrets.local.yaml 不存在 | 本地验证可继续；远程连接前要求用户补充或运行 ~ssh |
| runbook.yaml 不存在 | 回退 verify.yaml / package.json / pyproject.toml |
| command_ref 无法解析 | 输出错误，要求修正引用 |
| 目标环境无法确定 | 追问用户选择 local/dev/test/production |
| production 未 protected | 输出警告并按 protected 处理 |
| secrets.local.yaml 疑似被 Git 跟踪 | 输出警告，建议移出索引并加入 .gitignore |
