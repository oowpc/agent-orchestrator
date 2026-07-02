# Task Manager 说明

Task Manager 是 Agent Orchestrator 的任务状态管理模块。

第一版使用 Python 内置的 `sqlite3`，不引入复杂数据库依赖，方便快速跑通 MVP。

## 1. 数据库存放位置

默认位置：

```text
storage/agent_orchestrator.sqlite3
```

可以通过环境变量修改：

```env
DATABASE_PATH=storage/agent_orchestrator.sqlite3
```

## 2. 当前数据表

### plans

保存一次 Planner Agent 生成的整体计划。

字段包括：

- id
- requirement
- worth_doing
- recommended_solution
- alternatives_json
- risks_json
- assumptions_json
- next_steps_json
- report_path
- created_at

### tasks

保存计划中的每一个任务，现在已经升级为任务包。

字段包括：

- id：数据库任务 ID，例如 `task_xxx`
- plan_id：所属计划 ID
- task_id：计划内任务编号，例如 `T001`
- title
- agent
- task_type
- description
- status
- goal
- boundary
- input_materials_json
- tool_permissions_json
- deliverable_format
- evidence_requirements_json
- blocking_conditions_json
- decision_owner
- acceptance_criteria_json
- dependencies_json
- risks_json
- next_action
- created_at
- updated_at

### evidence_packages

保存子 Agent 提交的证据包。

字段包括：

- id
- task_db_id
- agent_name
- completed_work
- evidence_locations_json
- commands_run_json
- changed_files_json
- risks_json
- suggested_next_steps_json
- created_at

### reviews

保存审查结果。

字段包括：

- id
- task_db_id
- reviewer_agent
- passed
- issues_json
- summary
- evidence_package_id
- created_at

### conflicts / decisions / agent_runs / task_events

分别保存冲突升级、最终决策、Agent 运行记录和任务事件日志。

## 3. 任务状态

当前支持状态：

```text
pending      等待执行
running      正在执行
reviewing    等待审查
testing      等待测试
needs_fix    需要返工
done         完成
failed       失败
blocked      被阻塞
```

`done` 是受保护状态。默认情况下，任务必须同时满足：

1. 至少有一个证据包。
2. 至少有一个通过的 ReviewRecord。
3. 没有 open / escalated 冲突。

否则不能直接标记为 `done`。

检查是否可以 done：

```bash
python -m backend.tasks_cli can-done task_xxx
```

强制标记 done 只应在人工确认后使用：

```bash
python -m backend.tasks_cli status task_xxx done --force --message "人工确认通过"
```

## 4. 生成计划并写入数据库

```bash
python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
```

输出会包含：

```text
Plan ID：plan_xxx
任务状态表
```

## 5. 查看任务

列出所有任务：

```bash
python -m backend.tasks_cli list
```

显示任务包详情：

```bash
python -m backend.tasks_cli list --verbose
```

列出某个计划的任务：

```bash
python -m backend.tasks_cli list --plan-id plan_xxx
```

按状态过滤：

```bash
python -m backend.tasks_cli list --status pending
```

## 6. 查看可执行任务

可执行任务指：

- 状态是 `pending`
- 依赖任务都已经 `done`

```bash
python -m backend.tasks_cli ready plan_xxx
```

## 7. 更新任务状态和下一步

```bash
python -m backend.tasks_cli status task_xxx running --message "开始执行"
```

标记需要返工：

```bash
python -m backend.tasks_cli status task_xxx needs_fix --message "缺少边界情况处理"
```

更新下一步：

```bash
python -m backend.tasks_cli next task_xxx "交给 Reviewer Agent 审查证据包"
```

## 8. 提交证据包

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

查看证据包：

```bash
python -m backend.evidence_cli list --task task_xxx
```

## 9. 审查证据包

审查一个证据包并写入 ReviewRecord：

```bash
python -m backend.review_cli evidence evidence_xxx
```

审查后自动更新状态：

```bash
python -m backend.review_cli evidence evidence_xxx --apply
```

默认规则：

- 审查通过：尝试更新为 `done`。
- 审查失败：更新为 `needs_fix`。

如果存在未解决冲突，即使审查通过，也不能自动进入 `done`。

## 10. 冲突升级和决策

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

## 11. 当前限制

当前已经具备可信状态的基础数据结构和第一版状态保护，但还没有实现：

- 自动执行任务
- 自动改代码
- 自动创建 PR
- 自动运行 Docker 测试
- 自动把冲突同步为 GitHub comment

这些会在后续阶段接入。
