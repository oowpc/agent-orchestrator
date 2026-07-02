# GitHub 同步说明

本项目现在可以把本地可信状态记录同步到 GitHub Issue comment。

支持同步：

- evidence package
- review record
- conflict record

## 1. 同步证据包

先 dry run：

```bash
python -m backend.github_comment_cli evidence oowpc/report-agent 12 evidence_xxx --dry-run
```

确认后写入 GitHub：

```bash
python -m backend.github_comment_cli evidence oowpc/report-agent 12 evidence_xxx
```

## 2. 同步审查记录

```bash
python -m backend.github_comment_cli review oowpc/report-agent 12 evidence_xxx --dry-run
```

确认后：

```bash
python -m backend.github_comment_cli review oowpc/report-agent 12 evidence_xxx
```

## 3. 同步冲突记录

```bash
python -m backend.github_comment_cli conflict oowpc/report-agent 12 conflict_xxx --dry-run
```

确认后：

```bash
python -m backend.github_comment_cli conflict oowpc/report-agent 12 conflict_xxx
```

## 4. 环境变量

写入 GitHub 前需要：

```env
GITHUB_TOKEN=your_github_token
ENABLE_GITHUB_WRITE=true
```

## 5. 推荐流程

```bash
python -m backend.main "给报表 Agent 增加数据质量检查功能" --list-tasks
python -m backend.github_cli project-issues oowpc/report-agent plan_xxx
python -m backend.evidence_cli submit task_xxx --agent "Backend Agent" --completed-work "完成摘要" --changed-file backend/a.py --next-step "交给 Reviewer 审查"
python -m backend.review_cli evidence evidence_xxx --apply
python -m backend.github_comment_cli evidence oowpc/report-agent 12 evidence_xxx
python -m backend.github_comment_cli review oowpc/report-agent 12 evidence_xxx
```

这样 GitHub Issue 会保存任务包，SQLite 会保存可信状态，Issue comments 会保存证据和审查过程。
