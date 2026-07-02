"""CLI for reviewing evidence packages.

This closes the first trusted-state loop:
TaskPackage -> EvidencePackage -> ReviewRecord -> protected status update.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict

from backend.agents.reviewer_agent import ReviewerAgent
from backend.config import get_settings
from backend.models import EvidencePackage, ReviewRecord
from backend.task_manager import VALID_STATUSES, TaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-review",
        description="Review evidence packages and write ReviewRecord entries.",
    )
    subparsers = parser.add_subparsers(dest="command")

    evidence = subparsers.add_parser("evidence", help="审查一个证据包")
    evidence.add_argument("evidence_id", help="证据包 ID，例如 evidence_xxx")
    evidence.add_argument("--reviewer", default="Reviewer Agent", help="审查 Agent 名称")
    evidence.add_argument("--apply", action="store_true", help="审查后自动更新任务状态")
    evidence.add_argument("--pass-status", choices=sorted(VALID_STATUSES), default="done", help="审查通过后设置的状态，默认 done")
    evidence.add_argument("--fail-status", choices=sorted(VALID_STATUSES), default="needs_fix", help="审查不通过后设置的状态，默认 needs_fix")
    evidence.add_argument("--force-status", action="store_true", help="更新状态时强制绕过 done 保护，仅人工确认后使用")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    manager = TaskManager(get_settings().database_path)

    try:
        if args.command == "evidence":
            evidence_row = manager.get_evidence(args.evidence_id)
            evidence = _evidence_from_row(evidence_row)
            result = ReviewerAgent().review_evidence_package(evidence)
            review = ReviewRecord(
                task_db_id=evidence.task_db_id,
                reviewer_agent=args.reviewer,
                passed=result.passed,
                summary=result.summary,
                issues=[asdict(issue) for issue in result.issues],
                evidence_package_id=args.evidence_id,
            )
            review_id = manager.add_review(review)
            print(f"ReviewRecord 已写入：{review_id}")
            print(f"审查结果：{'passed' if result.passed else 'failed'}")
            print(f"摘要：{result.summary}")
            if result.issues:
                print("问题：")
                for issue in result.issues:
                    print(f"- [{issue.severity}] {issue.message} 建议：{issue.suggestion}")

            if args.apply:
                target_status = args.pass_status if result.passed else args.fail_status
                manager.update_status(
                    evidence.task_db_id,
                    target_status,
                    message=f"Evidence review {review_id}: {result.summary}",
                    force=args.force_status,
                )
                print(f"任务状态已更新：{evidence.task_db_id} -> {target_status}")
            else:
                suggested = args.pass_status if result.passed else args.fail_status
                print(f"建议状态：{suggested}。如需自动更新，请加 --apply。")
            return 0

    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"未知命令：{args.command}", file=sys.stderr)
    return 1


def _evidence_from_row(row: dict) -> EvidencePackage:
    return EvidencePackage(
        task_db_id=row["task_db_id"],
        agent_name=row["agent_name"],
        completed_work=row["completed_work"],
        evidence_locations=row["evidence_locations"],
        commands_run=row["commands_run"],
        changed_files=row["changed_files"],
        risks=row["risks"],
        suggested_next_steps=row["suggested_next_steps"],
    )


if __name__ == "__main__":
    raise SystemExit(main())
