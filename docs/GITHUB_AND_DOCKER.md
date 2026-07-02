# GitHub API + Docker 方案

本项目后续采用两条主线：

1. **GitHub API 连接实际项目仓库**：用于读取仓库、创建 Issue、创建分支、创建 PR、评论 Review 结果。
2. **Docker 沙箱执行命令**：用于在隔离环境中运行测试、lint、构建命令，避免污染主机环境。

## 1. 为什么用 GitHub API

GitHub API 适合做正式的多 Agent 协作流程。

Orchestrator 可以：

- 读取目标仓库信息
- 根据 Planner 的任务自动创建 Issues
- 给 Issue 添加 Agent 标签
- 后续创建功能分支
- 后续创建 Draft PR
- 后续在 PR 中写 Review 评论
- 后续检查 CI 状态

第一版只实现安全的派单动作：

```text
Plan 中的任务 → GitHub Issues
```

暂不直接改代码、暂不创建 PR、暂不合并。

## 2. 环境变量

复制 `.env.example`：

```bash
cp .env.example .env
```

填写：

```env
GITHUB_TOKEN=你的 GitHub Token
GITHUB_DEFAULT_OWNER=oowpc
ENABLE_GITHUB_WRITE=true
```

建议 Token 权限从小开始：

- 只给目标仓库权限
- 初期只需要 Issues 写权限
- 后续需要 PR / Contents 写权限时再扩大

## 3. 生成任务计划

先生成一个 Plan：

```bash
python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
```

输出中会出现：

```text
Plan ID：plan_xxx
```

## 4. Dry run 检查派单

先不要直接创建 Issue，先 dry run：

```bash
python -m backend.github_cli issues oowpc/report-agent plan_xxx --dry-run
```

它会打印将要创建的 Issues。

## 5. 创建 GitHub Issues

确认无误后：

```bash
python -m backend.github_cli issues oowpc/report-agent plan_xxx
```

系统会把每个任务创建成一个 Issue，并添加标签：

```text
agent-task
agent:backend
agent:frontend
agent:tester
type:backend
type:frontend
type:test
status:planned
```

## 6. 检查仓库访问

```bash
python -m backend.github_cli repo oowpc/report-agent
```

## 7. Docker 运行 Orchestrator

构建镜像：

```bash
docker build -t agent-orchestrator .
```

运行帮助命令：

```bash
docker run --rm agent-orchestrator
```

使用 `.env`、挂载输出目录和数据库目录：

```bash
docker run --rm \
  --env-file .env \
  -v "$(pwd)/storage:/app/storage" \
  -v "$(pwd)/outputs:/app/outputs" \
  agent-orchestrator \
  python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
```

Windows PowerShell 可以用：

```powershell
docker run --rm `
  --env-file .env `
  -v "${PWD}/storage:/app/storage" `
  -v "${PWD}/outputs:/app/outputs" `
  agent-orchestrator `
  python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
```

## 8. Docker Compose

构建并运行：

```bash
docker compose run --rm orchestrator python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
```

派发 Issue：

```bash
docker compose run --rm orchestrator python -m backend.github_cli issues oowpc/report-agent plan_xxx --dry-run
```

确认后：

```bash
docker compose run --rm orchestrator python -m backend.github_cli issues oowpc/report-agent plan_xxx
```

## 9. Docker 沙箱设计

后续真正执行代码时，不应该直接在主机运行测试命令，而应该进入隔离容器。

推荐原则：

- 目标项目代码只读挂载，或者在临时副本中执行
- 限制 CPU
- 限制内存
- 限制运行时间
- 默认关闭网络
- 不挂载 `.env`、密钥、凭证目录
- 命令执行日志必须保存

后续流程：

```text
Orchestrator
↓
拉取目标项目临时副本
↓
启动 Docker 沙箱
↓
运行 pytest / npm test / lint
↓
收集 stdout / stderr / exit code
↓
Tester Agent 分析日志
↓
Reviewer Agent 判断是否通过
```

## 10. 当前实现边界

已实现：

- GitHub API service 初版
- 从 SQLite Plan 任务创建 GitHub Issues
- Dry run 派单
- Dockerfile
- docker-compose.yml

未实现：

- 自动创建分支
- 自动修改代码
- 自动创建 PR
- Docker 沙箱执行目标项目测试
- CI 状态读取
- PR Review 评论

建议下一步：

1. 先用 GitHub Issues 跑通派单。
2. 再接入目标项目 `.agents/project.yaml`。
3. 然后再做 Docker 沙箱测试执行。
