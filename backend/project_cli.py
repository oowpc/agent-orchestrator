"""CLI for reading target project configuration.

Target projects should add `.agents/project.yaml`. This CLI can load it from a
local path or from a GitHub repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backend.config import get_settings
from backend.project_config import ProjectConfig
from backend.services.github_service import GitHubService, GitHubServiceError


DEFAULT_CONFIG_PATH = ".agents/project.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-project",
        description="Inspect target project .agents/project.yaml config.",
    )
    subparsers = parser.add_subparsers(dest="command")

    local_parser = subparsers.add_parser("local", help="从本地项目目录读取配置")
    local_parser.add_argument("project_path", help="目标项目目录")
    local_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="配置文件路径")

    github_parser = subparsers.add_parser("github", help="从 GitHub 仓库读取配置")
    github_parser.add_argument("repo_full_name", help="例如 oowpc/report-agent")
    github_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="配置文件路径")
    github_parser.add_argument("--ref", default=None, help="分支、tag 或 commit SHA")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "local":
            path = Path(args.project_path) / args.config
            config = ProjectConfig.from_file(path)
            _print_config(config)
            return 0

        if args.command == "github":
            settings = get_settings()
            service = GitHubService(
                token=settings.github_token,
                api_base_url=settings.github_api_base_url,
            )
            file = service.get_text_file(args.repo_full_name, args.config, ref=args.ref)
            config = ProjectConfig.from_yaml_text(file.content)
            _print_config(config)
            print(f"\n配置来源：{file.html_url}")
            return 0

    except (FileNotFoundError, ValueError, GitHubServiceError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"未知命令：{args.command}", file=sys.stderr)
    return 1


def _print_config(config: ProjectConfig) -> None:
    print(config.summary_markdown())
    issues = config.validate()
    if issues:
        print("## 配置问题")
        print("")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("## 配置检查")
        print("")
        print("未发现明显问题。")


if __name__ == "__main__":
    raise SystemExit(main())
