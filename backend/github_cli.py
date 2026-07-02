"""CLI for GitHub API operations.

For the current MVP, this CLI focuses on creating GitHub Issues from stored
Agent Orchestrator tasks.
"""

from __future__ import annotations

import argparse
import sys

from backend.config import get_settings
from backend.models import Task
from backend.services.github_service import GitHubService, GitHubServiceError
from backend.task_manager import TaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-github",
        description="Create GitHub Issues from Agent Orchestrator tasks.",
    )
    subparsers = parser.add_subparsers(dest="command")

    repo_parser = subparsers.add_parser("repo", help="检查目标仓库是否可访问")
    repo_parser.add_argument("repo_full_name", help="例如 oowpc/report-agent")

    issues_parser = subparsers.add_parser("issues", help="把一个 Plan 的任务创建为 GitHub Issues")
    issues_parser.add_argument("repo_full_name", help="目标仓库，例如 oowpc/report-agent")
    issues_parser.add_argument("plan_id", help="Plan ID，例如 plan_xxx")
    issues_parser.add_argument("--dry-run", action="store_true", help="只打印将要创建的 Issue，不真正调用 GitHub")
    issues_parser.add_argument("--status", default="pending", help="只派发某个状态的任务，默认 pending")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    settings = get_settings()
    manager = TaskManager(settings.database_path)

    try:
        if args.command == "repo":
            service = _github_service(settings)
            repo = service.get_repo(args.repo_full_name)
            print(f"仓库可访问：{repo.get('full_name', args.repo_full_name)}")
            print(f"默认分支：{repo.get('default_branch', 'unknown')}")
            return 0

        if args.command == "issues":
            tasks = manager.list_tasks(plan_id=args.plan_id, status=args.status)
            if not tasks:
                print("没有匹配的任务。")
                return 0

            if args.dry_run:
                _print_dry_run(args.repo_full_name, args.plan_id, tasks)
                return 0

            service = _github_service(settings)
            for task_data in tasks:
                task = _task_from_row(task_data)
                issue = service.create_issue_from_task(
                    repo_full_name=args.repo_full_name,
                    task=task,
                    plan_id=args.plan_id,
                    extra_labels=["status:planned"],
                )
                print(f"已创建 Issue #{issue.number}: {issue.title}")
                print(issue.html_url)
            return 0

    except (GitHubServiceError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"未知命令：{args.command}", file=sys.stderr)
    return 1


def _github_service(settings):
    if not settings.enable_github_write:
        raise ValueError("ENABLE_GITHUB_WRITE=false。若要调用 GitHub 写操作，请在 .env 中设置 ENABLE_GITHUB_WRITE=true。")
    return GitHubService(token=settings.github_token, api_base_url=settings.github_api_base_url)


def _task_from_row(row: dict) -> Task:
    return Task(
        task_id=row["task_id"],
        title=row["title"],
        agent=row["agent"],
        task_type=row["task_type"],
        description=row["description"],
        acceptance_criteria=row["acceptance_criteria"],
        dependencies=row["dependencies"],
        risks=row["risks"],
    )


def _print_dry_run(repo_full_name: str, plan_id: str, tasks: list[dict]) -> None:
    print(f"Dry run: 将把 Plan {plan_id} 的 {len(tasks)} 个任务派发到 {repo_full_name}")
    print("")
    for task in tasks:
        print(f"- [{task['task_id']}] {task['title']} -> {task['agent']} ({task['task_type']})")


if __name__ == "__main__":
    raise SystemExit(main())
