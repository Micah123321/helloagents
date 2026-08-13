# HelloAGENTS — DSH Agent Skill

> 本技能是 HelloAGENTS 在 DeepSeek Harness 中的适配层，提供路由协议、G3 输出格式、子代理编排和安全规则。
> 通过 DSH agent preset (`helloagents/dsh/preset.yml`) 自动加载。

## 能力

| 能力 | 说明 |
|------|------|
| 路由协议 (G4) | R0/R1/R2 三级路由，含需求评估与追问 |
| 输出格式 (G3) | 状态栏 + 主体 + 下一步引导 |
| 安全规则 (G2) | EHRB 检测与静默失败防护 |
| 子代理编排 (G9/G10) | 通过 DSH subagent/subagent_fork/workflow 工具 |
| 命令系统 | 22 个 ~xxx 命令（help/auto/plan/exec 等） |

## 加载

本技能由 DSH skill-filesystem 自动发现。使用时加载 `helloagents` 技能即可注入完整协议。

## 依赖

- DSH 平台提供: `read`/`write`/`edit`/`grep`/`glob`（文件）、`subagent`/`subagent_fork`/`workflow`（子代理）、`web_search`（搜索）
- 主 HelloAGENTS 包提供: `functions/*.md`、`services/*.md`、`templates/*` 等模块文件