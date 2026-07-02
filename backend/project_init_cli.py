"""CLI for initializing target projects with `.agents/` config files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backend.config import Settings, get_settings
from backend.project_initializer import ProjectInitializer
from backend.services.github_service import GitHubService, GitHubServiceError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-project-init",
        description="Initialize a target project for Agent Orchestrator.",
    )
    subparsers = parser.add_subparsers(dest="command")

    local_parser = subparsers.add_parser("local", help="在本地项目目录创建 .agents 配置")
    local_parser.add_argument("project_path", help="目标项目本地路径")
    _add_common_args(local_parser)
    local_parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的本地 .agents 文件")

    github_parser = subparsers.add_parser("github", help="在 GitHub 目标仓库创建 .agents 配置")
    github_parser.add_argument("repo_full_name", help="目标项目仓库，例如 oowpc/report-agent")
    _add_common_args(github_parser)
    github_parser.add_argument("--branch", default=None, help="写入目标分支，默认使用仓库默认分支")
    github_parser.add_argument("--dry-run", action="store_true", help="只打印将要创建的文件，不真正写入 GitHub")

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-name", default=None, help="项目名称，默认从仓库名或目录名推断")
    parser.add_argument("--project-type", default="web-app", help="项目类型，例如 web-app / cli / data-app")
    parser.add_argument("--description", default="", help="项目描述")
    parser.add_argument("--frontend", default="React", help="前端技术栈")
    parser.add_argument("--backend", default="FastAPI", help="后端技术栈")
    parser.add_argument("--database", default="SQLite", help="数据库")
    parser.add_argument("--default-branch", default="main", help="默认分支")
    parser.add_argument("--test-command", default="pytest", help="测试命令")
    parser.add_argument("--lint-command", default="ruff check .", help="Lint 命令")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    settings = get_settings()
    initializer = ProjectInitializer()

    try:
        if args.command == "local":
            project_path = Path(args.project_path)
            repo_full_name = _infer_repo_full_name(settings, args.project_name, project_path.name)
            project_name = args.project_name or project_path.name
            files = _build_files(initializer, args, project_name=project_name, repo_full_name=repo_full_name)
            result = initializer.init_local(project_path=project_path, files=files, overwrite=args.overwrite)
            _print_result(result.created, result.skipped)
            return 0

        if args.command == "github":
            project_name = args.project_name or args.repo_full_name.split("/")[-1]
            files = _build_files(initializer, args, project_name=project_name, repo_full_name=args.repo_full_name)
            if args.dry_run:
                print(f"Dry run: 将在 {args.repo_full_name} 创建以下文件：")
                for file in files:
                    print(f"- {file.path}")
                return 0

            _require_github_write(settings)
            service = GitHubService(
                token=settings.github_token,
                api_base_url=settings.github_api_base_url,
            )
            result = initializer.init_github(
                service=service,
                repo_full_name=args.repo_full_name,
                files=files,
                branch=args.branch,
                overwrite=False,
            )
            _print_result(result.created, result.skipped)
            return 0

    except (FileNotFoundError, ValueError, GitHubServiceError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"未知命令：{args.command}", file=sys.stderr)
    return 1


def _build_files(initializer: ProjectInitializer, args: argparse.Namespace, project_name: str, repo_full_name: str):
    return initializer.build_files(
        project_name=project_name,
        repo_full_name=repo_full_name,
        project_type=args.project_type,
        description=args.description,
        frontend=args.frontend,
        backend=args.backend,
        database=args.database,
        default_branch=args.default_branch,
        test_command=args.test_command,
        lint_command=args.lint_command,
    )


def _infer_repo_full_name(settings: Settings, project_name: str | None, fallback_name: str) -> str:
    owner = settings.github_default_owner or "oowpc"
    repo = project_name or fallback_name
    return f"{owner}/{repo}"


def _require_github_write(settings: Settings) -> None:
    if not settings.enable_github_write:
        raise ValueError("ENABLE_GITHUB_WRITE=false。若要写入 GitHub，请在 .env 中设置 ENABLE_GITHUB_WRITE=true。")


def _print_result(created: list[str], skipped: list[str]) -> None:
    if created:
        print("已创建：")
        for path in created:
            print(f"- {path}")
    if skipped:
        print("已跳过：")
        for path in skipped:
            print(f"- {path}")
    if not created and not skipped:
        print("没有文件变更。")


if __name__ == "__main__":
    raise SystemExit(main())
