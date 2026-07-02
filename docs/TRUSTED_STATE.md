# 可信多 Agent 状态结构

多 Agent 不是群聊。这个项目的核心不是让多个模型同时说话，而是让每个 Agent 的工作都能进入同一套可信状态。

可信状态至少由四部分组成：

1. 任务包
2. 证据包
3. 状态表
4. 冲突升级

## 1. 任务包

任务包定义一个 Agent 可以做什么、不能做什么、做到什么程度算完成。

当前 `Task` 已升级为任务包，核心字段包括：

```text
task_id
title
agent
task_type
description
goal
boundary
input_materials
tool_permissions
deliverable_format
evidence_requirements
blocking_conditions
decision_owner
acceptance_criteria
dependencies
risks
next_action
```

任务包原则：

- Planner Agent 负责定义任务，不直接改代码。
- Worker Agent 负责执行任务，不修改验收标准。
- Reviewer Agent 负责审查，不偷偷重写方案。
- 信息不足时进入 blocked，而不是猜测。

## 2. 证据包

子 Agent 不能只回复“我完成了”。

每次执行都应该提交证据包：

```text
task_db_id
agent_name
completed_work
evidence_locations
commands_run
changed_files
risks
suggested_next_steps
```

证据包回答的是：

- 完成了什么
- 证据在哪里
- 改了哪些文件
- 跑了哪些命令
- 还有什么风险
- 下一步建议是什么

## 3. 状态表

状态表不只是保存 pending / done。

它应该能回答：

- 当前任务是什么状态
- 谁负责
- 阻塞在哪里
- 有哪些风险
- 证据在哪里
- 下一步该谁做什么

当前状态包括：

```text
pending
running
reviewing
testing
needs_fix
done
failed
blocked
```

并且新增了：

```text
evidence_packages
reviews
conflicts
decisions
agent_runs
```

这些表让任务状态可以被证据支撑，而不是只靠 Agent 自述。

## 4. 冲突升级

Agent 之间意见不一致时，不投票，也不看谁更自信。

冲突升级应该回到三件事：

1. 证据
2. 权限
3. 决策 owner

冲突记录包含：

```text
task_db_id
conflict_type
agents_involved
claims
evidence_refs
decision_owner
status
final_decision
```

决策记录包含：

```text
conflict_id
decision_owner
decision
rationale
evidence_refs
```

## 5. CLI 示例

提交证据包：

```bash
python -m backend.evidence_cli submit task_xxx \
  --agent "Backend Agent" \
  --completed-work "实现了缺失值检查函数" \
  --changed-file backend/services/data_quality.py \
  --command "pytest tests/test_data_quality.py" \
  --evidence "outputs/test_logs/data_quality.txt" \
  --risk "尚未做大文件性能测试" \
  --next-step "交给 Reviewer Agent 审查"
```

列出证据：

```bash
python -m backend.evidence_cli list --task task_xxx
```

创建冲突记录：

```bash
python -m backend.evidence_cli conflict task_xxx \
  --type review_disagreement \
  --agents "Backend Agent,Reviewer Agent" \
  --claims-json '[{"agent":"Backend Agent","claim":"实现已满足验收标准"},{"agent":"Reviewer Agent","claim":"缺少空输入测试"}]' \
  --evidence-ref evidence_xxx \
  --owner user
```

记录最终决策：

```bash
python -m backend.evidence_cli decide conflict_xxx \
  --owner user \
  --decision "需要补充空输入测试后再合并" \
  --rationale "Reviewer 的证据指出缺少边界测试，验收标准未完全满足" \
  --evidence-ref evidence_xxx
```

## 6. 下一步

后续应继续做：

1. 在 GitHub Issue 中展示完整任务包。
2. 让 Worker Agent 输出强制符合 EvidencePackage。
3. 让 Reviewer Agent 根据证据包更新状态。
4. 让冲突升级可以自动生成 GitHub comment。
5. 在 Web 控制台展示同一张状态表。
