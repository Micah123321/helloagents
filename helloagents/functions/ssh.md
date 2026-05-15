# ~ssh 命令 - 项目环境与服务器配置

本模块定义项目级服务器、环境、远程路径和运行命令配置的初始化/维护流程。

---

## 命令说明

```yaml
命令: ~ssh [<环境/服务器/命令描述>]
类型: 场景确认类
功能: 生成或更新 .helloagents/project.yaml、secrets.local.yaml、runbook.yaml
评估: 需求理解 + EHRB 检测（不评分不追问）
```

---

## 执行模式适配

```yaml
规则:
  1. 独立工具命令，不受 WORKFLOW_MODE 影响
  2. 不主动连接真实服务器，不执行远程命令
  3. 可写入项目内 .helloagents 环境配置文件
  4. 涉及 production/protected/root/plaintext_password 时必须输出风险提示
  5. secrets.local.yaml 与 project.local.yaml 必须检查 .gitignore
```

---

## 执行流程

### 步骤1: 需求理解 + EHRB 检测

```yaml
提取信息:
  - 项目名称和项目类型（从现有配置/代码库推断，不足则用当前目录名）
  - 环境角色: local/dev/test/production
  - host_ref 和服务器说明
  - 连接方式: ssh_alias / ip+port+user / private_key_path / password_ref
  - 远程 workspace、upload_dir、log_dir
  - 日常命令: install/lint/test/typecheck/build/dev/status/logs/deploy/restart/rollback
  - Windows 本地开发特殊项: shell、workspace、ssh_client、path_style

EHRB:
  - 本命令默认只写配置，不连接服务器，不执行远程命令
  - 用户要求立刻连接、部署、重启、删除、清缓存、写数据库 → 按 G2 EHRB 处理，必要时中断确认
```

### 步骤2: 扫描现有配置

```yaml
读取:
  - {KB_ROOT}/project.yaml
  - {KB_ROOT}/project.local.yaml
  - {KB_ROOT}/secrets.local.yaml
  - {KB_ROOT}/runbook.yaml
  - {KB_ROOT}/verify.yaml
  - package.json / pyproject.toml / Makefile（用于推荐命令）

判定:
  - 全部不存在 → 初始化模式
  - 部分存在 → 更新/补全模式
  - 存在敏感信息疑似提交风险 → 输出警告
```

### 步骤3: 信息充分性检查

```yaml
最低充分线:
  - 至少知道一个环境角色（local/dev/test/production）
  - 至少知道一个 workspace 或命令组
  - 远程环境若要可连接，必须有 host_ref 和连接引用

不足时:
  输出: 确认/追问（缺失字段 + 推荐模板）
  ⛔ END_TURN

用户可选择:
  1. 按推荐模板生成（推荐）
  2. 只生成空模板
  3. 取消
```

### 步骤4: 输出确认

```yaml
确认内容:
  - 将创建或更新的文件
  - 可提交文件: project.yaml、runbook.yaml
  - 本机文件: secrets.local.yaml、project.local.yaml
  - 不会执行远程连接或命令
  - 安全规则: production/protected 后续必须确认

输出: 确认
⛔ END_TURN
用户确认后:
  继续 → 步骤5
  取消 → 状态重置
```

### 步骤5: 创建或更新配置文件

```yaml
模板:
  - services/templates.md 中登记的 project.yaml
  - services/templates.md 中登记的 secrets.local.yaml
  - services/templates.md 中登记的 runbook.yaml

写入策略:
  - 文件不存在 → 用模板创建并填充已知信息
  - 文件存在 → 最小修改，保留用户已有字段和注释意图
  - 不把 secrets.local.yaml 内容复制到 project.yaml/runbook.yaml
  - 不生成真实密码；仅生成 password_ref 或注释占位

字段规则:
  - production 默认 protected: true
  - root 用户默认标记 warnings
  - 明文密码默认不生成
  - Windows 本地环境默认 shell: powershell、path_style: windows
```

### 步骤6: .gitignore 检查

```yaml
检测:
  - .gitignore 是否存在
  - 是否包含:
    .helloagents/secrets.local.yaml
    .helloagents/project.local.yaml
    .helloagents/secrets.*.yaml
    .helloagents/*.pem
    .helloagents/*.key
    .helloagents/*.password

处理:
  - 缺失时提示建议添加
  - 仅在用户确认或本命令确认中已授权写入时自动补充
  - 若 secrets.local.yaml 已被 Git 跟踪，输出警告并建议用户移出索引
```

### 步骤7: 验收

```yaml
检查:
  - YAML 文件存在且非空
  - project.yaml 包含 project/environments/commands 或 paths
  - runbook.yaml 包含 workflows 或 validation
  - secrets.local.yaml 不包含私钥正文
  - production/protected 规则存在
  - .gitignore 覆盖本机敏感文件

输出: 完成（创建/更新文件 + 后续使用方式）
→ 状态重置
```

---

## 输出要素

### 确认场景

```yaml
主体内容:
  操作摘要: 将初始化/更新项目环境配置，不连接服务器
  影响范围: .helloagents/project.yaml、secrets.local.yaml、runbook.yaml、可选 .gitignore
  安全边界: secrets.local.yaml 禁止提交，production 后续执行必须确认
选项:
  1. 继续生成/更新配置（推荐）
  2. 只生成空模板
  3. 取消
```

### 完成场景

```yaml
主体内容:
  执行结果: 已创建/更新项目环境配置
  变更摘要: 文件列表、识别的环境、可用 workflow
  验收结果: 敏感信息检查、.gitignore 检查、production 保护检查
下一步:
  "运行 `~test` 或发起迭代需求时将自动读取项目环境配置。"
```

---

## 不确定性处理

| 场景 | 处理 |
|------|------|
| 用户只说“配置服务器”但未给环境角色 | 追问 local/dev/test/production 映射 |
| 用户给出 root 密码 | 建议改为 SSH key 或 password_ref；生产环境拒绝明文 |
| 用户给出 IP/端口但不给路径 | 可写入 secrets.local.yaml，project.yaml 中 workspace 留待补充 |
| 用户要求连接验证 | 先生成配置，再按 EHRB/确认流程执行连接测试 |
| 已有配置格式异常 | 输出错误，建议修复或备份后重建 |
