# 目标项目配置 `.agents/project.yaml`

Agent Orchestrator 是一个可复用的总控系统。为了让它接管不同项目，每个目标项目都应该提供一个配置文件：

```text
.agents/project.yaml
```

这个文件告诉 Orchestrator：

- 项目是什么
- GitHub 仓库在哪
- 技术栈是什么
- 哪些 Agent 可以参与
- 哪些目录是前端/后端/测试/文档
- 如何运行测试
- 哪些操作必须用户确认

## 1. 推荐目录

目标项目仓库中建议放：

```text
.agents/
├── project.yaml
├── roles.md
├── coding-rules.md
└── test-rules.md
```

## 2. 配置模板

可以从本仓库复制模板：

```text
templates/project-agent-config.yaml
```

复制到目标项目：

```bash
mkdir -p .agents
cp path/to/agent-orchestrator/templates/project-agent-config.yaml .agents/project.yaml
```

## 3. 配置字段说明

### project

```yaml
project:
  name: report-agent
  type: web-app
  description: 智能报表分析 Agent
```

### repo

```yaml
repo:
  provider: github
  full_name: oowpc/report-agent
  default_branch: main
```

### tech_stack

```yaml
tech_stack:
  frontend: React
  backend: FastAPI
  database: SQLite
  language:
    - Python
    - TypeScript
```

### agents

```yaml
agents:
  planner: enabled
  backend_worker: enabled
  frontend_worker: enabled
  tester: enabled
  reviewer: enabled
  docs: enabled
  devops: disabled
```

### paths

```yaml
paths:
  backend: backend/
  frontend: frontend/
  tests: tests/
  docs: docs/
```

### rules

```yaml
rules:
  prefer_pull_request: true
  allow_direct_commit: false
  require_user_confirmation_for:
    - delete_file
    - database_migration
    - dependency_change
    - deploy
    - merge_pr
    - large_refactor
  protected_paths:
    - .env
    - .env.*
    - secrets/
    - credentials/
```

### commands

```yaml
commands:
  install:
    - pip install -r requirements.txt
  test:
    - pytest
  lint:
    - ruff check .
  frontend_test:
    - npm test
```

## 4. 本地读取配置

```bash
python -m backend.project_cli local ../report-agent
```

指定配置文件：

```bash
python -m backend.project_cli local ../report-agent --config .agents/project.yaml
```

## 5. 从 GitHub 读取配置

需要 `.env` 中配置：

```env
GITHUB_TOKEN=你的 GitHub Token
```

然后运行：

```bash
python -m backend.project_cli github oowpc/report-agent
```

指定分支：

```bash
python -m backend.project_cli github oowpc/report-agent --ref main
```

## 6. 配置检查

`project_cli` 会做一些基本检查：

- 是否缺少 `project.name`
- 是否缺少 `repo.full_name`
- 是否开启了高风险的 `allow_direct_commit`

后续会继续增加：

- 检查测试命令是否配置
- 检查 protected paths 是否合理
- 检查 Agent 是否启用
- 检查目标仓库是否可访问

## 7. 设计原则

1. 每个实际项目自己维护 `.agents/project.yaml`。
2. Orchestrator 不要把某个项目的规则写死在总控仓库中。
3. 默认通过 PR 修改代码，不直接提交主分支。
4. 默认不执行危险命令。
5. 测试命令必须在 Docker 沙箱或受控环境中运行。
