# 架构设计

本文档记录 Agent Orchestrator 的核心架构。

## 1. 总体架构

Agent Orchestrator 是一个多 Agent 调度系统。它不直接等同于某一个模型，而是由任务系统、状态机、Agent 分工、审查机制和外部工具集成共同组成。

```text
用户需求
↓
Orchestrator 总控
↓
Planner Agent 拆解任务
↓
Task Manager 保存任务和状态
↓
Worker Agent 执行任务
↓
Reviewer Agent 审查结果
↓
Tester Agent 测试
↓
Reporter Agent 汇总报告
```

## 2. 核心模块

### Orchestrator

负责调度整个流程。

主要职责：

- 接收用户需求
- 调用 Planner 生成任务计划
- 根据依赖关系安排任务顺序
- 选择合适的 Agent 执行任务
- 控制任务状态流转
- 触发审查、测试、返工
- 生成最终报告

### Task Manager

负责管理任务生命周期。

能力：

- 创建任务
- 更新任务状态
- 记录依赖关系
- 判断哪些任务可以执行
- 保存任务输出
- 记录 Agent 运行日志

### Agent Registry

负责记录可用 Agent。

示例：

```text
planner_agent
backend_worker_agent
frontend_worker_agent
tester_agent
reviewer_agent
reporter_agent
```

### LLM Client

统一封装模型调用。

目标：

- 支持 OpenAI-compatible API
- 支持多模型配置
- 支持不同 Agent 使用不同模型
- 记录 token 用量和成本
- 统一错误处理和重试

### GitHub Service

负责连接目标项目仓库。

能力：

- 读取仓库文件
- 创建 Issue
- 创建分支
- 创建或更新文件
- 创建 Pull Request
- 评论审查结果

### Sandbox Service

负责安全执行命令。

建议后续使用 Docker 沙箱，限制：

- CPU
- 内存
- 网络
- 运行时间
- 可访问文件目录

## 3. 任务状态机

推荐状态：

| 状态 | 含义 |
|---|---|
| pending | 等待执行 |
| running | 正在执行 |
| reviewing | 等待审查 |
| testing | 等待测试 |
| needs_fix | 需要返工 |
| done | 完成 |
| failed | 失败 |
| blocked | 被阻塞 |

常规流转：

```text
pending → running → reviewing → testing → done
```

返工流转：

```text
reviewing → needs_fix → running
```

阻塞流转：

```text
running → blocked → 等待用户补充信息
```

## 4. 数据模型草案

### Project

```json
{
  "id": "project_001",
  "name": "report-agent",
  "repo_full_name": "oowpc/report-agent",
  "default_branch": "main",
  "config_path": ".agents/project.yaml"
}
```

### Task

```json
{
  "id": "T001",
  "project_id": "project_001",
  "title": "实现缺失值检查",
  "type": "backend",
  "assigned_agent": "backend_worker_agent",
  "status": "pending",
  "dependencies": [],
  "acceptance_criteria": [],
  "created_at": "2026-01-01T00:00:00Z"
}
```

### AgentRun

```json
{
  "id": "run_001",
  "task_id": "T001",
  "agent_name": "backend_worker_agent",
  "input": {},
  "output": {},
  "status": "success",
  "token_usage": 1200,
  "started_at": "2026-01-01T00:00:00Z",
  "finished_at": "2026-01-01T00:01:00Z"
}
```

### Review

```json
{
  "id": "review_001",
  "task_id": "T001",
  "passed": false,
  "issues": [
    {
      "severity": "medium",
      "message": "没有处理空 DataFrame。",
      "suggestion": "增加空表判断和测试。"
    }
  ]
}
```

## 5. 权限设计

| Agent | 读文件 | 写文件 | 执行命令 | 创建 PR | 合并 PR |
|---|---|---|---|---|---|
| Planner | 是 | 否 | 否 | 否 | 否 |
| Worker | 是 | 是 | 可选 | 可选 | 否 |
| Tester | 是 | 否 | 是 | 否 | 否 |
| Reviewer | 是 | 否 | 否 | 否 | 否 |
| Reporter | 是 | 否 | 否 | 否 | 否 |
| Orchestrator | 是 | 可选 | 可选 | 是 | 需用户确认 |

## 6. 安全原则

1. 默认不允许直接修改主分支。
2. 默认不允许删除文件。
3. 默认不允许自动合并 PR。
4. 默认不允许执行任意 Shell 命令。
5. 任何危险操作都需要用户确认。
6. 所有 Agent 输出应保存日志，便于审计。

## 7. MVP 架构

第一版不要直接做自动改代码，可以先做：

```text
CLI 输入需求
↓
Planner Agent 输出任务拆分
↓
Task Manager 保存任务
↓
Reviewer Agent 审查计划
↓
Reporter Agent 生成 Markdown 报告
```

后续再逐步接入 GitHub 和 Docker 沙箱。
