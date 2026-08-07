# 任务清单: {feature}

```yaml
@feature: {feature}
@created: {YYYY-MM-DD}
@status: pending
@mode: R2
@task_complexity: {simple|moderate|complex}
@execution_strategy: standard
@batch_policy: max3-normal-max2-risk-max1-strong-risk
@pipeline_state: optional-status-json-pipeline
# standard 方案保持原有路径；复杂编码方案可将 @execution_strategy 改为 checkpoint-batch
```

当 `@execution_strategy: checkpoint-batch` 且 `@task_complexity: complex` 时，每个任务还必须声明 `batch_id`、`checkpoint` 和 `batch_verify`。批次只能包含当前 DAG 的 ready 任务；验证未通过时不得进入下游批次。旧方案包不要求这些字段。

## 进度概览

| 完成 | 失败 | 跳过 | 总数 |
|------|------|------|------|
| 0 | 0 | 0 | X |

---

## 任务列表

### 1. {阶段/模块名称}

- [ ] 1.1 在 `{文件路径}` 中实现 {具体功能}
  - 预期变更: {该文件/范围内要发生什么变化}
  - 完成标准: {可验证的完成条件}
  - 验证方式: {命令/检查/人工核对方式}
  - depends_on: []
  - batch_id: {B1，可选}
  - checkpoint: {CP1，可选}
  - batch_verify: {当前批验证命令/检查，可选}
- [ ] 1.2 在 `{文件路径}` 中实现 {具体功能}
  - 预期变更: {该文件/范围内要发生什么变化}
  - 完成标准: {可验证的完成条件}
  - 验证方式: {命令/检查/人工核对方式}
  - depends_on: [1.1]
  - batch_id: {B1，可选}
  - checkpoint: {CP1，可选}
  - batch_verify: {当前批验证命令/检查，可选}

### 2. {阶段/模块名称}

- [ ] 2.1 {任务描述}
  - 预期变更: {该任务的具体产出}
  - 完成标准: {可验证的完成条件}
  - 验证方式: {命令/检查/人工核对方式}
  - depends_on: [1.2]
  - batch_id: {B2，可选}
  - checkpoint: {CP2，可选}
  - batch_verify: {当前批验证命令/检查，可选}

---

## 执行日志

| 时间 | 任务 | 状态 | 备注 |
|------|------|------|------|

---

## 执行备注

> 记录执行过程中的重要说明、决策变更、风险提示等
