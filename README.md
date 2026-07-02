# Agent Orchestrator

一个可复用的多 Agent 总控系统，用来指挥多个专业 Agent 协作完成软件项目任务。

它的目标不是让多个模型随便聊天，而是把任务拆解、派发、执行、审查、测试、汇总这一整套流程管理起来。

> 核心定位：用一个 Orchestrator 像项目经理一样管理一组 AI 工程师。

## 项目愿景

很多 AI 编程工具可以帮你写代码，但当项目变复杂以后，仅靠一个聊天框或一个代码 Agent 容易出现这些问题：

- 需求没有拆清楚，执行 Agent 不知道做到什么程度算完成。
- 多个 Agent 同时改同一个文件，容易冲突。
- 没有验收标准，做完以后不知道是否真的合格。
- 没有审查和测试环节，容易把 bug 合进去。
- 没有任务记录，后续很难追踪谁做了什么。

Agent Orchestrator 想解决这些问题：

```text
用户需求
↓
总控 Orchestrator
↓
Planner Agent 拆任务
↓
Task Queue 管理任务状态
↓
Worker Agents 执行任务
↓
Reviewer / Tester 检查结果
↓
Reporter 汇总交付
```

## 适用场景

本项目适合用于：

- 报表 Agent 项目开发
- 城市间出行建议 Agent 项目开发
- 模型互考 Arena 项目开发
- Web 应用开发
- 数据分析项目
- GitHub 仓库任务自动拆解
- Codex / OpenCode / 自定义 Agent 协作管理

一句话：

> 让一个总控 Agent 指挥其他 Agent 给你干活。

## 推荐仓库关系

本仓库是一个独立的、可复用的总控平台。实际项目应该单独建仓库。

例如：

```text
agent-orchestrator/        # 多 Agent 总控平台
report-agent/              # 实际项目：报表 Agent
travel-agent/              # 实际项目：出行 Agent
llm-mutual-exam-arena/     # 实际项目：模型互考 Arena
```

每个实际项目仓库可以放一个 `.agents/project.yaml` 配置文件，让总控系统知道它的技术栈、测试命令、权限规则和 Agent 分工。

## 核心概念

### 1. Orchestrator

总控层，负责理解需求、调度任务、控制流程和风险。

它不应该直接下场乱改代码，而应该负责：

- 判断需求是否值得做
- 生成修改方案
- 分析风险
- 拆分任务
- 指派 Agent
- 检查任务状态
- 决定是否返工
- 汇总最终结果

### 2. Planner Agent

负责把用户需求拆成结构化任务。

例如用户说：

```text
给报表 Agent 增加数据质量检查功能。
```

Planner 应该拆成：

```text
T001: 后端实现缺失值检查
T002: 后端实现重复行检查
T003: 后端实现异常值检测
T004: 前端展示质量检查结果
T005: 测试 Agent 编写测试用例
T006: 文档 Agent 更新 README
```

### 3. Worker Agents

负责具体执行任务，可以分为：

- Backend Agent
- Frontend Agent
- Data Agent
- Docs Agent
- General Worker Agent

### 4. Reviewer Agent

负责审查任务结果，包括：

- 是否满足验收标准
- 是否有边界情况遗漏
- 是否有安全风险
- 是否引入过度设计
- 是否破坏已有功能

### 5. Tester Agent

负责生成测试用例、运行测试命令、分析测试结果。

### 6. Reporter Agent

负责生成最终任务报告，包括完成内容、修改文件、测试结果、风险和下一步建议。

## 任务状态机

任务不应该只是一个文本，而应该有明确状态。

推荐状态：

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

常规流程：

```text
pending → running → reviewing → testing → done
```

返工流程：

```text
reviewing → needs_fix → running
```

缺少信息：

```text
running → blocked → 等待用户补充
```

## 任务结构示例

每个任务都应该是结构化的。

```json
{
  "task_id": "T001",
  "title": "实现 Excel 缺失值检查",
  "type": "backend",
  "assigned_agent": "backend_agent",
  "priority": "high",
  "status": "pending",
  "input": {
    "module": "data_quality",
    "requirement": "检查每一列缺失值数量和比例"
  },
  "constraints": [
    "不要直接修改前端",
    "函数需要支持 pandas DataFrame",
    "返回结果必须是 JSON 可序列化格式"
  ],
  "acceptance_criteria": [
    "能统计每列缺失数量",
    "能统计每列缺失比例",
    "空 DataFrame 有明确错误提示",
    "有基础单元测试"
  ],
  "dependencies": [],
  "output": null
}
```

## 推荐技术栈

第一版建议先做成一个轻量系统。

### 后端

- Python
- FastAPI
- SQLite 起步，后续可换 PostgreSQL
- OpenAI-compatible API Client
- Pydantic

### 任务队列

- MVP：数据库轮询 / 内存队列
- 进阶：Redis + RQ / Celery

### 前端

- React / Vue
- Tailwind CSS
- 简单任务看板

### 外部集成

- GitHub API
- Codex / OpenCode / 自定义代码 Agent
- Docker 沙箱
- CI 测试

## 推荐项目结构

```text
agent-orchestrator/
├── README.md
├── backend/
│   ├── main.py
│   ├── orchestrator.py
│   ├── task_manager.py
│   ├── agents/
│   │   ├── planner_agent.py
│   │   ├── worker_agent.py
│   │   ├── reviewer_agent.py
│   │   ├── tester_agent.py
│   │   └── reporter_agent.py
│   ├── services/
│   │   ├── llm_client.py
│   │   ├── github_service.py
│   │   ├── sandbox_service.py
│   │   └── project_service.py
│   ├── models/
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── agent_run.py
│   │   └── review.py
│   └── prompts/
│       ├── planner.md
│       ├── worker.md
│       ├── reviewer.md
│       └── reporter.md
├── frontend/
├── docs/
├── examples/
├── templates/
└── .agents/
```

## MVP 开发路线

### 阶段 1：命令行版本

目标：先不自动改代码，只做任务拆解和报告生成。

功能：

- 输入用户需求
- Planner Agent 拆任务
- 生成任务列表
- 生成风险分析
- 生成 Markdown 任务报告

### 阶段 2：任务管理版本

目标：把任务保存起来，形成可追踪的状态机。

功能：

- 任务入库
- 任务状态流转
- Worker Agent 执行文字任务
- Reviewer Agent 审查
- Reporter Agent 汇总

### 阶段 3：GitHub 集成版本

目标：让 Orchestrator 能连接实际项目仓库。

功能：

- 读取目标仓库 `.agents/project.yaml`
- 创建 GitHub Issues
- 创建任务分支
- 生成 PR 草稿
- 评论 Review 结果

### 阶段 4：自动执行版本

目标：接入代码执行能力。

功能：

- Docker 沙箱运行测试
- Worker Agent 修改代码
- Tester Agent 执行测试命令
- Reviewer Agent 审查 diff
- 通过后创建 PR

### 阶段 5：Web 控制台

目标：把流程做成可视化任务看板。

功能：

- 项目列表
- 任务看板
- Agent 运行日志
- 测试结果展示
- 用户确认按钮
- 成本统计

## 权限与安全原则

多 Agent 系统一定要控制权限。

建议规则：

- Planner 只能读需求，不能写代码。
- Reviewer 只能审查，不能改代码。
- Tester 可以执行测试，但应在沙箱中运行。
- Worker 可以修改代码，但不能直接合并主分支。
- Orchestrator 可以创建 PR，但合并必须由用户确认。

危险操作必须二次确认：

- 删除文件
- 修改数据库结构
- 安装新依赖
- 大规模重构
- 部署线上服务
- 合并 PR

## 目标项目接入方式

实际项目仓库建议增加：

```text
.agents/project.yaml
.agents/roles.md
.agents/coding-rules.md
.agents/test-rules.md
```

其中 `project.yaml` 用于告诉总控系统：

- 项目名称
- GitHub 仓库地址
- 技术栈
- 测试命令
- 哪些操作需要确认
- 是否允许自动创建 PR

示例见：[`templates/project-agent-config.yaml`](templates/project-agent-config.yaml)

## 当前状态

项目处于初始化设计阶段。

当前重点：

- 明确多 Agent 总控系统的核心架构
- 完成 README 和基础文档
- 设计任务结构、状态机和 Agent 分工
- 准备最小可运行 MVP

## 下一步

建议先实现：

1. `Planner Agent`：输入需求，输出任务拆分。
2. `Task Manager`：保存任务和状态。
3. `Reviewer Agent`：审查任务结果。
4. `Reporter Agent`：生成 Markdown 报告。
5. 一个简单 CLI：`python main.py "你的需求"`

## 项目定位

本项目不是为了做一个“全自动乱改代码的 AI”，而是为了做一个安全、可控、可追踪的多 Agent 项目管理系统。

它的核心目标是：

> 让 AI Agent 像一个小团队一样协作，同时让人类仍然掌握关键决策权。
