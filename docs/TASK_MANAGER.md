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

保存计划中的每一个任务。

字段包括：

- id：数据库任务 ID，例如 `task_xxx`
- plan_id：所属计划 ID
- task_id：计划内任务编号，例如 `T001`
- title
- agent
- task_type
- description
- status
- acceptance_criteria_json
- dependencies_json
- risks_json
- created_at
- updated_at

### task_events

保存任务事件日志。

字段包括：

- id
- task_db_id
- event_type
- message
- payload_json
- created_at

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

## 7. 更新任务状态

```bash
python -m backend.tasks_cli status task_xxx running --message "开始执行"
```

完成任务：

```bash
python -m backend.tasks_cli status task_xxx done --message "已完成并通过人工检查"
```

标记需要返工：

```bash
python -m backend.tasks_cli status task_xxx needs_fix --message "缺少边界情况处理"
```

## 8. 当前限制

当前 Task Manager 只负责保存和更新任务状态。

暂不负责：

- 自动执行任务
- 自动改代码
- 自动创建 GitHub Issue
- 自动运行测试
- 自动合并 PR

这些会在后续阶段接入。
