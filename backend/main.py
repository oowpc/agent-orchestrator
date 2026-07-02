"""CLI entry point for the Agent Orchestrator MVP."""

from __future__ import annotations

import argparse
import sys

from backend.agents.planner_agent import PlannerAgent
from backend.agents.reporter_agent import ReporterAgent
from backend.config import get_settings
from backend.services.llm_client import LLMClient
from backend.task_manager import TaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-orchestrator",
        description="Generate a multi-agent task plan from a user requirement.",
    )
    parser.add_argument("requirement", nargs="?", help="用户需求，例如：给报表 Agent 增加数据质量检查功能")
    parser.add_argument("--project", default=None, help="目标项目名称，例如 report-agent")
    parser.add_argument("--print", action="store_true", help="同时在终端打印 Markdown 报告")
    parser.add_argument("--no-save-db", action="store_true", help="只生成 Markdown，不写入 SQLite 任务库")
    parser.add_argument("--list-tasks", action="store_true", help="生成计划后打印任务状态表")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.requirement:
        parser.print_help()
        print("\n错误：请提供一个需求文本。", file=sys.stderr)
        return 1

    settings = get_settings()
    llm_client = LLMClient(settings)
    planner = PlannerAgent(llm_client=llm_client, settings=settings)
    reporter = ReporterAgent()

    plan = planner.run(requirement=args.requirement, project_name=args.project)
    output_path = reporter.save_plan(plan, settings.outputs_dir / "plans")

    plan_id: str | None = None
    if not args.no_save_db:
        task_manager = TaskManager(settings.database_path)
        plan_id = task_manager.save_plan(plan, report_path=output_path)
        print(f"任务已写入 SQLite：{settings.database_path}")
        print(f"Plan ID：{plan_id}")
        if args.list_tasks:
            _print_task_table(task_manager.list_tasks(plan_id=plan_id))

    if args.print:
        print(reporter.render_plan(plan))

    print(f"任务计划已生成：{output_path}")
    if settings.use_mock_llm:
        print("当前使用 mock LLM 模式。配置 LLM_API_KEY 后可接入真实模型。")
    return 0


def _print_task_table(tasks: list[dict]) -> None:
    if not tasks:
        print("暂无任务。")
        return
    print("\n任务状态：")
    print("| DB ID | 任务 ID | 状态 | Agent | 标题 |")
    print("|---|---|---|---|---|")
    for task in tasks:
        print(f"| {task['id']} | {task['task_id']} | {task['status']} | {task['agent']} | {task['title']} |")
    print("")


if __name__ == "__main__":
    raise SystemExit(main())
