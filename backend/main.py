"""CLI entry point for the Agent Orchestrator MVP."""

from __future__ import annotations

import argparse
import sys

from backend.agents.planner_agent import PlannerAgent
from backend.agents.reporter_agent import ReporterAgent
from backend.config import get_settings
from backend.services.llm_client import LLMClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-orchestrator",
        description="Generate a multi-agent task plan from a user requirement.",
    )
    parser.add_argument("requirement", nargs="?", help="用户需求，例如：给报表 Agent 增加数据质量检查功能")
    parser.add_argument("--project", default=None, help="目标项目名称，例如 report-agent")
    parser.add_argument("--print", action="store_true", help="同时在终端打印 Markdown 报告")
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

    if args.print:
        print(reporter.render_plan(plan))

    print(f"任务计划已生成：{output_path}")
    if settings.use_mock_llm:
        print("当前使用 mock LLM 模式。配置 LLM_API_KEY 后可接入真实模型。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
