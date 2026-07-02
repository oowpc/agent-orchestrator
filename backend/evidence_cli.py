"""CLI for evidence packages, conflicts, and decisions.

This is the trust layer of the orchestrator. Agents should not only say
"done"; they should submit evidence that can be reviewed and used for conflict
resolution.
"""

from __future__ import annotations

import argparse
import json
import sys

from backend.config import get_settings
from backend.models import ConflictRecord, DecisionRecord, EvidencePackage
from backend.task_manager import TaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-evidence",
        description="Submit evidence packages and handle conflict escalation.",
    )
    subparsers = parser.add_subparsers(dest="command")

    submit = subparsers.add_parser("submit", help="提交证据包")
    submit.add_argument("task_db_id", help="数据库任务 ID，例如 task_xxx")
    submit.add_argument("--agent", required=True, help="提交证据的 Agent 名称")
    submit.add_argument("--completed-work", required=True, help="完成内容摘要")
    submit.add_argument("--evidence", action="append", default=[], help="证据位置，可多次传入")
    submit.add_argument("--command", action="append", default=[], help="运行过的命令，可多次传入")
    submit.add_argument("--changed-file", action="append", default=[], help="修改文件，可多次传入")
    submit.add_argument("--risk", action="append", default=[], help="剩余风险，可多次传入")
    submit.add_argument("--next-step", action="append", default=[], help="建议下一步，可多次传入")

    list_parser = subparsers.add_parser("list", help="列出证据包")
    list_parser.add_argument("--task", default=None, help="只查看某个任务的证据")

    conflict = subparsers.add_parser("conflict", help="创建冲突升级记录")
    conflict.add_argument("task_db_id", help="数据库任务 ID，例如 task_xxx")
    conflict.add_argument("--type", required=True, help="冲突类型，例如 review_disagreement / test_failure")
    conflict.add_argument("--agents", required=True, help="涉及 Agent，逗号分隔")
    conflict.add_argument("--claims-json", required=True, help="冲突主张 JSON 数组")
    conflict.add_argument("--evidence-ref", action="append", default=[], help="证据引用，可多次传入")
    conflict.add_argument("--owner", default="user", help="决策 owner，默认 user")

    decide = subparsers.add_parser("decide", help="记录冲突决策")
    decide.add_argument("conflict_id", help="冲突 ID，例如 conflict_xxx")
    decide.add_argument("--owner", default="user", help="决策 owner")
    decide.add_argument("--decision", required=True, help="最终决策")
    decide.add_argument("--rationale", required=True, help="决策理由")
    decide.add_argument("--evidence-ref", action="append", default=[], help="证据引用，可多次传入")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    manager = TaskManager(get_settings().database_path)

    try:
        if args.command == "submit":
            evidence = EvidencePackage(
                task_db_id=args.task_db_id,
                agent_name=args.agent,
                completed_work=args.completed_work,
                evidence_locations=args.evidence,
                commands_run=args.command,
                changed_files=args.changed_file,
                risks=args.risk,
                suggested_next_steps=args.next_step,
            )
            evidence_id = manager.add_evidence_package(evidence)
            print(f"证据包已提交：{evidence_id}")
            return 0

        if args.command == "list":
            rows = manager.list_evidence(task_db_id=args.task)
            _print_evidence(rows)
            return 0

        if args.command == "conflict":
            conflict = ConflictRecord(
                task_db_id=args.task_db_id,
                conflict_type=args.type,
                agents_involved=[item.strip() for item in args.agents.split(",") if item.strip()],
                claims=_parse_json_list(args.claims_json),
                evidence_refs=args.evidence_ref,
                decision_owner=args.owner,
                status="open",
            )
            conflict_id = manager.create_conflict(conflict)
            print(f"冲突记录已创建：{conflict_id}")
            return 0

        if args.command == "decide":
            decision = DecisionRecord(
                conflict_id=args.conflict_id,
                decision_owner=args.owner,
                decision=args.decision,
                rationale=args.rationale,
                evidence_refs=args.evidence_ref,
            )
            decision_id = manager.record_decision(decision)
            print(f"决策已记录：{decision_id}")
            return 0

    except (ValueError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"未知命令：{args.command}", file=sys.stderr)
    return 1


def _parse_json_list(text: str) -> list[dict]:
    value = json.loads(text)
    if not isinstance(value, list):
        raise ValueError("claims-json must be a JSON array")
    return value


def _print_evidence(rows: list[dict]) -> None:
    if not rows:
        print("暂无证据包。")
        return
    for row in rows:
        print(f"## {row['id']}")
        print(f"- 任务：{row['task_db_id']}")
        print(f"- Agent：{row['agent_name']}")
        print(f"- 完成内容：{row['completed_work']}")
        if row["evidence_locations"]:
            print("- 证据位置：")
            for item in row["evidence_locations"]:
                print(f"  - {item}")
        if row["changed_files"]:
            print("- 修改文件：")
            for item in row["changed_files"]:
                print(f"  - {item}")
        if row["risks"]:
            print("- 风险：")
            for item in row["risks"]:
                print(f"  - {item}")
        if row["suggested_next_steps"]:
            print("- 建议下一步：")
            for item in row["suggested_next_steps"]:
                print(f"  - {item}")
        print("")


if __name__ == "__main__":
    raise SystemExit(main())
