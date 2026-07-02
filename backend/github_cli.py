"""CLI for GitHub API operations.

For the current MVP, this CLI focuses on creating GitHub Issues from stored
Agent Orchestrator tasks. It can dispatch tasks directly to a repository name
or infer the repository from a target project's `.agents/project.yaml`.
"""

from __future__ import annotations

import argparse
import sys

from backend.config import Settings, get_settings
from backend.models import Task
from backend.project_config import ProjectConfig
from backend.services.github_service import GitHubService, GitHubServiceError
from backend.task_manager import TaskManager

DEFAULT_CONFIG_PATH = ".agents/project.yaml"


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

    project_issues_parser = subparsers.add_parser(
        "project-issues",
        help="读取目标项目 .agents/project.yaml 后派发 GitHub Issues",
    )
    project_issues_parser.add_argument("repo_full_name", help="目标项目仓库，例如 oowpc/report-agent")
    project_issues_parser.add_argument("plan_id", help="Plan ID，例如 plan_xxx")
    project_issues_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="目标项目配置路径")
    project_issues_parser.add_argument("--ref", default=None, help="配置文件所在分支、tag 或 commit SHA")
    project_issues_parser.add_argument("--dry-run", action="store_true", help="只打印将要创建的 Issue，不真正调用 GitHub")
    project_issues_parser.add_argument("--status", default="pending", help="只派发某个状态的任务，默认 pending")

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
            service = _github_service(settings, require_write=False)
            repo = service.get_repo(args.repo_full_name)
            print(f"仓库可访问：{repo.get('full_name', args.repo_full_name)}")
            print(f"默认分支：{repo.get('default_branch', 'unknown')}")
            return 0

        if args.command == "issues":
            return _dispatch_issues(
                settings=settings,
                manager=manager,
                repo_full_name=args.repo_full_name,
                plan_id=args.plan_id,
                status=args.status,
                dry_run=args.dry_run,
                project_config=None,
            )

        if args.command == "project-issues":
            service = _github_service(settings, require_write=False)
            config_file = service.get_text_file(args.repo_full_name, args.config, ref=args.ref)
            project_config = ProjectConfig.from_yaml_text(config_file.content)
            config_issues = project_config.validate()
            if config_issues:
                print("目标项目配置存在问题：", file=sys.stderr)
                for issue in config_issues:
                    print(f"- {issue}", file=sys.stderr)
                return 1
            if project_config.repo.full_name != args.repo_full_name:
                print(
                    "警告：命令传入的仓库与 project.yaml 中的 repo.full_name 不一致。",
                    file=sys.stderr,
                )
                print(f"命令仓库：{args.repo_full_name}", file=sys.stderr)
                print(f"配置仓库：{project_config.repo.full_name}", file=sys.stderr)
                print("将以 project.yaml 中的 repo.full_name 为准。", file=sys.stderr)

            return _dispatch_issues(
                settings=settings,
                manager=manager,
                repo_full_name=project_config.repo.full_name,
                plan_id=args.plan_id,
                status=args.status,
                dry_run=args.dry_run,
                project_config=project_config,
            )

    except (GitHubServiceError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"未知命令：{args.command}", file=sys.stderr)
    return 1


def _dispatch_issues(
    settings: Settings,
    manager: TaskManager,
    repo_full_name: str,
    plan_id: str,
    status: str,
    dry_run: bool,
    project_config: ProjectConfig | None,
) -> int:
    tasks = manager.list_tasks(plan_id=plan_id, status=status)
    if not tasks:
        print("没有匹配的任务。")
        return 0

    if dry_run:
        _print_dry_run(repo_full_name, plan_id, tasks, project_config=project_config)
        return 0

    service = _github_service(settings, require_write=True)
    for task_data in tasks:
        task = _task_from_row(task_data)
        issue = service.create_issue_from_task(
            repo_full_name=repo_full_name,
            task=task,
            plan_id=plan_id,
            extra_labels=_extra_labels(project_config),
        )
        print(f"已创建 Issue #{issue.number}: {issue.title}")
        print(issue.html_url)
    return 0


def _github_service(settings: Settings, require_write: bool):
    if require_write and not settings.enable_github_write:
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


def _extra_labels(project_config: ProjectConfig | None) -> list[str]:
    labels = ["status:planned"]
    if project_config:
        labels.append(f"project:{_normalize_label(project_config.name)}")
    return labels


def _print_dry_run(
    repo_full_name: str,
    plan_id: str,
    tasks: list[dict],
    project_config: ProjectConfig | None = None,
) -> None:
    print(f"Dry run: 将把 Plan {plan_id} 的 {len(tasks)} 个任务派发到 {repo_full_name}")
    if project_config:
        print(f"目标项目：{project_config.name} ({project_config.project_type})")
        if project_config.commands.test:
            print("测试命令：")
            for command in project_config.commands.test:
                print(f"  - {command}")
        if project_config.rules.require_user_confirmation_for:
            print("需要用户确认的操作：")
            for item in project_config.rules.require_user_confirmation_for:
                print(f"  - {item}")
    print("")
    for task in tasks:
        print(f"- [{task['task_id']}] {task['title']} -> {task['agent']} ({task['task_type']})")


def _normalize_label(value: str) -> str:
    return value.lower().replace(" ", "-").replace("/", "-")


if __name__ == "__main__":
    raise SystemExit(main())
