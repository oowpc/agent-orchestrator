# 目标项目初始化

`agent-orchestrator` 可以给目标项目自动生成 `.agents/` 接入配置。

生成的文件包括：

```text
.agents/project.yaml
.agents/roles.md
.agents/coding-rules.md
.agents/test-rules.md
```

## 本地初始化

在本地目标项目目录中创建 `.agents/` 文件：

```bash
python -m backend.project_init_cli local ../report-agent --project-name report-agent
```

如果文件已经存在，默认会跳过。

覆盖本地文件：

```bash
python -m backend.project_init_cli local ../report-agent --overwrite
```

## GitHub 初始化 Dry Run

先检查将要创建哪些文件：

```bash
python -m backend.project_init_cli github oowpc/report-agent --dry-run
```

## GitHub 初始化

需要在 `.env` 中开启 GitHub 写入能力：

```env
ENABLE_GITHUB_WRITE=true
```

然后运行：

```bash
python -m backend.project_init_cli github oowpc/report-agent --project-name report-agent
```

## 自定义技术栈

```bash
python -m backend.project_init_cli github oowpc/report-agent \
  --project-name report-agent \
  --project-type web-app \
  --frontend Vue \
  --backend FastAPI \
  --database SQLite \
  --test-command pytest \
  --lint-command "ruff check ." \
  --dry-run
```

## 初始化后检查配置

从 GitHub 读取：

```bash
python -m backend.project_cli github oowpc/report-agent
```

从本地读取：

```bash
python -m backend.project_cli local ../report-agent
```

## 再按项目配置派单

生成 Plan：

```bash
python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
```

按项目配置 dry run：

```bash
python -m backend.github_cli project-issues oowpc/report-agent plan_xxx --dry-run
```

正式派单：

```bash
python -m backend.github_cli project-issues oowpc/report-agent plan_xxx
```

## 当前安全限制

GitHub 初始化当前只创建不存在的文件。

如果目标仓库已经存在同名文件，系统会跳过，不会覆盖。

原因：覆盖 GitHub 文件应该走 PR 流程，避免误改项目规则。
