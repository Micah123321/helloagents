# ~commit 命令 - Git 提交

本模块定义 Git 提交的执行规则，基于 Conventional Commits 国际规范。

---

## 命令说明

```yaml
命令: ~commit [<message>]
类型: 场景确认类
功能: 生成提交信息并执行 Git 提交
评估: 需求理解 + EHRB 检测（不评分不追问）
```

---

## 执行模式适配

```yaml
规则:
  1. 独立工具命令，不受 WORKFLOW_MODE 影响
  2. 提交方式与提交信息必须用户确认；确认后不得因同一暂存范围重复要求确认
  3. 根据远程配置动态显示推送选项
  4. 支持: 本地提交 / 推送 / 创建PR

并发防护（CRITICAL）:
  - 本仓库可能存在多个并发进程同时执行 ~commit 或其他 git 操作（多名 AI/主代理+子代理同仓库协作）
  - 必须使用 `.helloagents/commit.lock` 文件锁保护最短临界区（任务级暂存 → cached diff 审查 → git commit），防范暂存冲突
  - 锁只覆盖 Git index 和 HEAD 写入，不覆盖 diff 分析、测试、提交信息生成、用户确认或失败等待
  - 锁获取失败（死锁）时按下方"并发冲突处理"流程走，不自以为是地覆盖或忽略

任务级提交隔离（CRITICAL）:
  - 提交单位是"当前任务的增量"，不是"当前文件的全部 diff"
  - 多线程/并行任务可能修改同一个文件；同文件存在其他任务 hunk 时，必须按 hunk/patch 隔离
  - 文件在本任务开始前已经 dirty，或无法证明全部 hunk 属于当前任务 → 标记为 mixed-file
  - mixed-file 禁止整文件 `git add <path>`，只能暂存当前任务 patch/hunk
  - 禁止全局 index 操作: `git add .`、`git reset HEAD`、`git restore --staged -- .`、`git checkout -- .`
  - patch/hunk 暂存失败最多重建 1 次；仍失败则 fail-fast 输出冲突文件和处理选项，不得反复清 index、重建 patch、再检查
```

---

## 执行约束

```yaml
核心约束: 只负责提交现有变更，不负责创建变更
用户描述中的"目标说明"作为提交范围参考，不执行文件操作
提交范围: 以当前任务上下文、用户指定范围和任务基线为准；不得把共享文件中的全部未提交 diff 默认视为本任务变更
```

**DO NOT:** 在用户确认前执行任何读取或改变项目文件状态的操作

---

## 执行流程

### 步骤1: 需求理解 + EHRB 检测

```yaml
无独立输出，直接进入下一步
```

### 步骤2: 环境检测与变更分析

```yaml
环境检测（4 个独立命令，同一消息中发起多个并行工具调用）:
  命令: git rev-parse --git-dir | git status --porcelain | git remote -v | git branch --show-current
  非 Git 仓库: 输出: 错误，建议 git init
  无变更: 输出: 完成，提示无需提交

变更分析（按通用触发场景总表"提交辅助"场景，应主动编排 [→ G10]）:
  有远程: git diff origin/{branch}...HEAD（完整变更）
  仅本地: git diff HEAD（已跟踪文件）
  新文件: 直接读取文件内容
  目标: 提取核心改动点，过滤非核心文件
  子代理调用:
    待提交文件 ≥2 或需多维度分析 → spawn explorer 子代理并行读取 diff、按模块/文件组提取变更点（≤6/批）
    主代理汇总子代理返回的变更点 → 生成提交信息（提交信息生成始终主代理，确保 Conventional Commits 一致性）
    仅 1-2 个小文件 → 主代理直接读取 diff
    降级: 子代理失败 → 主代理直接读 diff + tasks.md 标记 [降级执行]

任务级提交范围建模（CRITICAL）:
  1. 建立 task_scope:
     来源优先级: 用户明确指定的文件/模块/目标说明 → 当前方案包任务清单/本轮已修改文件 → diff 分析结果
     范围必须可解释；无法解释的文件默认不纳入自动提交
  2. 建立 task_baseline:
     - 若当前 R2/R1 流程在修改前已有基线记录，使用该基线
     - 若无显式基线，使用步骤2开始时的 git status + per-file diff 作为 commit-time 基线，并把已 dirty 文件标记为 mixed-file
     - 新文件若路径属于 task_scope，可作为当前任务候选；不属于则排除
  3. 标记文件类型:
     - owned-file: 文件在任务开始前干净，且当前 diff 全部属于 task_scope
     - mixed-file: 文件在任务开始前 dirty，或同文件 diff 中存在无法归属当前任务的 hunk
     - excluded-file: 不属于 task_scope、敏感文件、或归属不清且无法隔离
  4. 记录提交计划:
     保存 owned_files、mixed_files、excluded_files、task_scope、baseline_status 到内存
     步骤3 只允许暂存 owned_files 的整文件变更和 mixed_files 的任务 patch/hunk
  若 git status --porcelain 或 per-file diff 失败（仓库被锁等），输出: 错误，提示稍后重试，流程结束。

预提交质量检查（finish-work，按通用触发场景总表"提交辅助"场景，应主动编排 [→ G10]）:
  子代理调用:
    需 ≥2 维度检查（代码-文档一致性 + 测试覆盖 + 验证命令）且并行收益明确 → spawn reviewer 子代理并行执行各维度检查（≤6/批）
    主代理汇总子代理返回的检查结果
    仅单一维度 → 主代理直接执行
    降级: 子代理失败 → 主代理直接执行检查 + tasks.md 标记 [降级执行]
  代码-文档一致性: 变更涉及公共 API/数据模型时，检查对应知识库文档是否已同步更新
    未同步 → 输出: ⚠️ 警告（列出未更新的文档），建议先完成同步再提交
  测试覆盖: 变更涉及核心逻辑时，检查是否有对应测试变更
    无测试变更 → 输出: ℹ️ 提示（建议补充测试），不阻断
  验证命令: 检测项目验证命令（同 Ralph Loop 检测逻辑），有则执行
    失败 → 输出: ⚠️ 警告（验证未通过），建议修复后再提交，不硬阻断

提交信息生成:
  来源: 基于 git diff 实际代码变更（主代理基于子代理汇总的变更点，或直接 diff）
  过滤: 排除 README*.md、LICENSE*、CHANGELOG*、.gitignore 等
  无参数: 分析 diff → 识别 type/scope → summary 描述"改了什么"
  有参数: 使用用户 message，语义分析确定 type

输出: 确认（提交确认）
⛔ END_TURN

用户选择后:
  仅本地提交: 展示安全暂存清单 → 任务级暂存 → cached diff 审查 → git commit（不再二次确认暂存范围）
  提交并推送: 任务级暂存 + git commit + git push
  提交并创建PR: 任务级暂存 + git commit + git push + 引导创建PR
  修改信息: 进入追问流程
  取消: → 状态重置

追问流程:
  AI 判断用户输入是否可作为提交信息
  满足: 更新信息，重新展示确认
  "确认": 使用当前信息
  "取消": → 状态重置
  不满足: 重新展示追问
```

### 步骤3: 执行提交与推送（含并发防护）

```yaml
前置: 步骤2用户选择提交方式后

⚠️ 临界区白名单（CRITICAL）: 本步骤全程主代理独占执行，永不拆给子代理。
  原因: 任务级暂存→cached diff 审查→commit 受 commit.lock 互斥保护，偏差检测依赖串行快照对比。
  git apply --cached/git add/commit/锁管理/偏差检测/EHRB/推送 均由主代理串行执行，违反会破坏并发安全 [→ G10 临界区白名单]
  锁范围: 获取锁后只做实时快照、任务级暂存、cached diff 审查、commit 和释放锁；禁止在锁内运行测试、生成提交信息、等待用户确认或做长耗时 diff 分析。

=== 第一阶段: 获取并发锁（CRITICAL） ===

1. 检查 .helloagents/commit.lock 是否存在:
   不存在 → 创建锁文件并写入 {pid: <当前进程PID>, task_scope: ..., owned_files: ..., mixed_files: ..., state: "acquired"}
   存在 → 读取内容，执行死锁检测:
     a. 提取 lock.pid
     b. 验证该 PID 是否还在运行:
        - Windows: tasklist /fi "PID eq {pid}" /nh 检查输出是否包含 {pid}
        - Linux/macOS: kill -0 {pid} 检查退出码
     c. PID 不存在（原进程已死）→ lock 已死锁 → 输出 ℹ️ 提示"清理死锁"，删除旧锁后重新创建
     d. PID 仍在运行 → lock 被其他进程持有 → 输出 ⚠️ 警告（"其他进程({pid})正在提交中"）
        选项: 等待（轮询重试，最多 10 秒） / 手动检查后覆盖锁继续 / 取消
     e. 锁文件内容格式错误或无法读取 → 视为无效锁，删除后重新创建
  始终使用独占写（open+write+close），不依赖原子重命名；写入前检查路径存在性

2. 锁定后立即重新捕获快照:
   执行 git status --porcelain 获取当前实时变更清单
   与步骤2中保存的"基准快照"进行偏差检测:

   === 偏差检测结果与处理 ===

   a. 完全一致 → 无障碍，继续进入任务级暂存

   b. 出现新文件（快照中新增了步骤2时不在的变更文件）:
      说明其他进程在本进程确认期间产生了新变更
      默认处理: 新文件不在 task_scope → 自动排除并记录；在 task_scope → 重新归类为 owned-file 或 mixed-file
      若无法归类 → 输出 ⚠️ 警告（"检测到并发变更: 新增 {N} 个文件"）
      选项: 忽略新文件，只提交步骤2确认的任务范围（推荐） / 重新扫描提交范围 / 中止释放锁

   c. 基准文件消失（步骤2清单中的某些文件已被其他进程提交/重置）:
      说明其他进程已接管了本进程计划提交的部分变更
      移除已消失文件 → 重新检查提交范围
      输出: ℹ️ 提示（"{N} 个文件已被其他进程提交，已排除"）
      检查后剩余文件=0 → 输出: 完成（"待提交变更已被其他进程提交"），释放锁，流程结束
      剩余文件>0 → 继续（提交信息不变，但列出排除的文件）

   d. 基准状态与快照均有但 XY 状态字母不同（如同文件从 M → ? 或相反）:
      说明其他进程对本进程计划提交的文件做了操作
      提取冲突文件列表 → 输出 ⚠️ 警告（"文件状态冲突: {文件列表}"）
      选项: 重新扫描变更并重新生成提交信息后继续 / 中止释放锁

   e. 同文件 hunk 发生漂移（文件仍存在但 diff 上下文变化）:
      owned-file → 降级为 mixed-file，禁止整文件暂存
      mixed-file → 重新生成任务 patch（最多 1 次）
      重新生成后仍无法应用 → fail-fast，释放锁前只回滚本进程已暂存的 patch，不清理全局 index

3. 偏差检测期间若 git status --porcelain 连续 2 次失败（仓库被其他进程长时间锁定）:
   → 输出: 错误（"Git 仓库被锁定，无法取快照"），释放锁，建议稍后重试


=== 第二阶段: 暂存与提交 ===

4. 暂存策略（任务级暂存，禁止直接 git add .）:
   4.1 文件清单: 使用最新（偏差检测后的）提交计划
   4.2 敏感文件检测: 检查变更文件中是否包含 .env、*credential*、*secret*、*.pem、*.key 等敏感文件
       - 发现敏感文件: 从暂存列表中排除，输出警告告知用户
       - 排除后无可提交文件: 输出警告并停止
   4.3 展示暂存清单: 向用户展示将要暂存的文件列表（已排除敏感文件）
       - 此清单是执行前告知，不是第二次确认；用户已在步骤2选择提交方式即视为授权暂存安全候选文件
       - 无敏感文件、无 EHRB 风险、用户未要求排除文件或修改提交信息时，展示清单后直接继续暂存和提交
       - 仅在以下情况暂停确认: 用户选择排除部分文件、用户选择修改提交信息、发现敏感/疑似敏感文件需人工裁决、暂存清单为空、检测到冲突标记或其他 EHRB 风险
       - git diff --check 的普通空白或 LF/CRLF 警告只记录为警告，不触发第二次暂存确认
   4.4 暂存前最后验证:
       - owned-file: 在执行 git add <path> 之前，对该文件执行 git diff --quiet HEAD -- {path}
         文件无变更（exit 0）→ 已被其他进程提交/还原，跳过暂存
         文件有变更（exit 1）→ 允许路径级 `git add <path>`
       - mixed-file: 禁止 `git add <path>`；必须生成当前任务 patch 并执行 `git apply --cached`
   4.5 执行暂存:
       - owned-file: 使用 git add <具体文件路径> 逐一添加
       - mixed-file: 使用任务 patch/hunk 暂存；patch 来源必须能追溯到 task_baseline 与 task_scope
       - patch 应用失败: 只允许重建 1 次；仍失败 → fail-fast，输出冲突文件、失败原因和可选处理，不继续循环
       - 不得使用交互式 `git add -p` 作为自动化默认路径；仅在用户明确要求人工交互时使用
       - 文件数量过多（>20）也不得退回 `git add .`；应分批按路径/patch 处理
   4.6 cached diff 审查（CRITICAL）:
       - 执行 git diff --cached --name-only 与 git diff --cached --check
       - 对 mixed-file 执行关键词/范围审查，确认 cached hunk 只属于 task_scope
       - 发现 unrelated hunk → 只撤回本进程刚应用的 patch/hunk；无法精确撤回时停止并提示，不得清空整个 index
       - 若锁定前已有 unrelated staged content 且无法证明属于当前任务 → 停止提交，输出具体文件，不得把共享 index 一起 commit

5. 提交: git commit -m "{提交信息}"
   提交失败（退出码非 0）→ 按下方"提交失败处理"执行，默认释放锁，避免阻塞其他并行任务

6. 释放并发锁: 删除 .helloagents/commit.lock
   - 必须执行（含提交失败时，死锁清理后释放）
   - 删除失败 → ⚠️ 警告（"锁文件可能残留，建议手动清理 .helloagents/commit.lock"）

7. 推送处理（用户选择推送时，锁已释放）:
   推送前: git fetch origin + 检查远程/本地领先数
   远程领先: git pull --rebase → 继续推送
   本地领先: git push origin {branch}
   分叉状态: git pull --rebase
   有冲突: 输出冲突信息，提示手动处理，流程结束

   创建PR: 推送完成后引导创建


=== 提交失败处理 ===

  场景: git commit 退出码非 0（如钩子拒绝、提交信息格式错误、签名失败）
  处理:
    1. 默认释放锁，避免阻塞其他并行任务；仅当失败可在 30 秒内自动重试且 index 只含本任务 staged content 时短暂保留锁
    2. 分析失败原因（git log/钩子输出/错误信息）
    3. 输出 ⚠️ 警告（"提交失败: {原因}"）
    4. 选项: 修复后重新执行 ~commit / 取消
       - 修复后重新执行 ~commit → 重新走步骤2，重新建立 task_scope 和 mixed-file 判定
       - 取消 → 仅撤回本进程本次 staged patch/hunk；无法精确撤回时提示用户检查 index，不做全局 reset
  锁保护期: 不跨用户决策持有锁，避免 commit 卡住其他并行任务
```

### 步骤4: 后续操作

```yaml
输出内容:
  本地提交: 提交信息摘要 + 提交哈希 + 变更文件数
  提交并推送: 提交信息摘要 + 已推送到 origin/{branch}
  提交并创建PR: 提交信息摘要 + PR 创建链接或引导

输出: 完成
→ 状态重置
```

---

## 不确定性处理

| 场景 | 处理 |
|------|------|
| 非 Git 仓库 | 输出: 错误，建议 git init |
| 无变更 | 输出: 完成，提示无需提交 |
| 远程推送冲突 | 输出冲突信息，提示手动处理 |
| 变更类型难以判定 | 默认 chore 类型，提示用户确认 |
| 并发锁冲突（其他进程持锁） | 输出: 警告（"其他进程({pid})正在提交"），等待/覆盖/取消三选一 |
| 偏差检测新增文件 | 输出: 警告（"检测到并发变更"），忽略/扩大/中止三选一 |
| 偏差检测基准文件消失 | 输出: 提示（已被其他进程提交），排除后继续或结束 |
| 偏差检测文件状态冲突 | 输出: 警告（"文件状态冲突"），重新扫描/中止二选一 |
| 同文件混合 hunk | 标记 mixed-file，使用任务 patch/hunk 暂存；失败最多重建 1 次 |
| patch/hunk 隔离失败 | fail-fast 输出冲突文件和处理选项，不清空 index，不进入重试循环 |
| pre-existing staged content | 若无法证明属于当前任务，停止提交并列出文件，禁止连同本任务一起 commit |
| 锁文件已死锁（原进程已死） | 输出: ℹ️ 提示（"清理死锁"），删除旧锁后重新创建 |
| git commit 失败 | 默认释放锁，修复后重新执行 ~commit；只撤回本进程 staged patch/hunk |
| 释放锁失败（.helloagents/commit.lock 删除异常） | ⚠️ 警告（"锁文件可能残留，建议手动清理"），不影响流程正常结束 |

---

## 附录

### 提交信息格式（Conventional Commits）

```
<emoji> <type>[(scope)]: <summary>

[body]

[footer]
```

### 类型映射表

| emoji | type | 说明 |
|-------|------|------|
| 🎉 | init | 项目初始化 |
| ✨ | feat | 新功能 |
| 🐞 | fix | 错误修复 |
| 📃 | docs | 文档变更 |
| 🌈 | style | 代码格式化 |
| 🦄 | refactor | 代码重构 |
| 🎈 | perf | 性能优化 |
| 🧪 | test | 测试相关 |
| 🔧 | build | 构建系统 |
| 🐎 | ci | CI 配置 |
| 🐳 | chore | 辅助工具 |
| ↩ | revert | 撤销提交 |

### 格式规则

```yaml
summary: 动词开头，≤50字符，不加句号
body: 说明变更动机（可选），每行≤72字符
footer: 关联 issue 或 BREAKING CHANGE（可选）
```

### 双语模式

```yaml
BILINGUAL_COMMIT=0: 仅使用 OUTPUT_LANGUAGE
BILINGUAL_COMMIT=1: 本地语言块在上，英文块在下，用 --- 分隔，两块均为完整格式且精确互译
```

### 特殊场景处理

| 场景 | 特征 | 处理 |
|------|------|------|
| 首次提交 | git log 为空 | type=init，summary=描述项目初始化 |
| 功能分支 | feature/*, fix/* | 推送后提示创建PR |
| 破坏性变更 | 删除公共API、修改数据结构 | type 后添加 !，footer 添加 BREAKING CHANGE |
| 回滚 | 用户说"回滚上次提交" | git revert HEAD，type=revert |

---

## 交付检查

- [ ] 提交信息符合 Conventional Commits 规范（emoji + type + scope + summary）
- [ ] 暂存前已排除敏感文件（.env / *credential* / *secret* / *.pem / *.key 等）
- [ ] 未使用 `git add .` 暴力暂存，而是分步或按具体路径暂存
- [ ] mixed-file 已使用任务 patch/hunk 暂存，未整文件 `git add <path>`
- [ ] 未使用 `git reset HEAD`、`git restore --staged -- .` 等全局 index 清理
- [ ] patch/hunk 暂存失败时已 fail-fast，未反复清 index 或重建 patch
- [ ] 公共 API/数据模型变更已同步知识库文档（未同步有 ⚠️ 警告且原因已说明）
- [ ] 推送前已 `git fetch` 检查远程领先/分叉状态，冲突已处理或提示
- [ ] 实际提交哈希已返回，未声称完成但未提交
- [ ] 并发锁已获取并在提交后释放（若锁残留已输出明确提示）
- [ ] 偏差检测已执行，并发变更已按策略处理或告知用户
