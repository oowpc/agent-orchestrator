# 统一状态表

统一状态表是多 Agent 协作的调度台视图。

它把任务、证据、审查、冲突、下一步放在同一张表里，避免多 Agent 变成没有状态的群聊。

## 查看状态表

```bash
python -m backend.state_cli
```

只看某个 Plan：

```bash
python -m backend.state_cli --plan-id plan_xxx
```

只看某个状态：

```bash
python -m backend.state_cli --status blocked
```

显示详情：

```bash
python -m backend.state_cli --details
```

## 状态表字段

状态表会展示：

```text
Task DB ID
Plan ID
Task
Status
Owner
Evidence
Reviews
Open Conflicts
Next
```

含义：

- Status：任务当前状态
- Owner：决策 owner
- Evidence：证据包数量
- Reviews：审查记录数量
- Open Conflicts：未解决冲突数量
- Next：下一步动作

## 使用方式

一个典型流程：

```bash
python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
python -m backend.state_cli --plan-id plan_xxx
python -m backend.evidence_cli submit task_xxx --agent "Backend Agent" --completed-work "完成摘要" --changed-file backend/a.py --next-step "交给 Reviewer 审查"
python -m backend.state_cli --plan-id plan_xxx --details
```

## 设计原则

统一状态表不是为了替代证据包，而是为了把证据、风险和下一步汇总到一个视图中。

如果一个任务显示为 done，但 Evidence 为 0，这个状态就不可信。

如果 Open Conflicts 大于 0，就不应该直接合并或交付。
