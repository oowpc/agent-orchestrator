"""Small CLI for inspecting and updating stored tasks."""

from __future__ import annotations

import argparse
import sys

from backend.config import get_settings
from backend.task_manager import TaskManager, VALID_STATUSES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-tasks",
        description="Inspect and update Agent Orchestrator tasks stored in SQLite.",
    )
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="列出任务")
    list_parser.add_argument("--plan-id", default=None, help="只查看某个 Plan 的任务")
    list_parser.add_argument("--status", default=None, help="只查看某个状态的任务")

    ready_parser = subparsers.add_parser("ready", help="列出可以执行的 pending 任务")
    ready_parser.add_argument("plan_id", help="Plan ID")

    update_parser = subparsers.add_parser("status", help="更新任务状态")
    update_parser.add_argument("task_db_id", help="数据库里的任务 ID，例如 task_xxx")
    update_parser.add_argument("status", choices=sorted(VALID_STATUSES), help="新状态")
    update_parser.add_argument("--message", default="", help="状态变更说明")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    settings = get_settings()
    manager = TaskManager(settings.database_path)

    if args.command == "list":
        tasks = manager.list_tasks(plan_id=args.plan_id, status=args.status)
        _print_task_table(tasks)
        return 0

    if args.command == "ready":
        tasks = manager.get_ready_tasks(plan_id=args.plan_id)
        _print_task_table(tasks)
        return 0

    if args.command == "status":
        manager.update_status(args.task_db_id, args.status, message=args.message)
        print(f"任务状态已更新：{args.task_db_id} -> {args.status}")
        return 0

    print(f"未知命令：{args.command}", file=sys.stderr)
    return 1


def _print_task_table(tasks: list[dict]) -> None:
    if not tasks:
        print("暂无任务。")
        return
    print("| DB ID | Plan ID | 任务 ID | 状态 | Agent | 标题 |")
    print("|---|---|---|---|---|---|")
    for task in tasks:
        print(
            f"| {task['id']} | {task['plan_id']} | {task['task_id']} | "
            f"{task['status']} | {task['agent']} | {task['title']} |"
        )


if __name__ == "__main__":
    raise SystemExit(main())
