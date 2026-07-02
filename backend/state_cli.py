"""Unified status table CLI.

The status table is the shared surface used by the orchestrator, workers,
reviewers, testers, and the human decision owner.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.task_manager import TaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-state",
        description="Show the unified multi-agent status table.",
    )
    parser.add_argument("--plan-id", default=None, help="Only show tasks from one Plan ID")
    parser.add_argument("--status", default=None, help="Only show tasks with this status")
    parser.add_argument("--details", action="store_true", help="Show details for risks, evidence, and next action")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    TaskManager(settings.database_path)  # ensure schema exists and migrations are applied
    rows = load_state_rows(settings.database_path, plan_id=args.plan_id, status=args.status)
    print_state_table(rows)
    if args.details:
        print_details(rows)
    return 0


def load_state_rows(database_path: Path, plan_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    clauses: list[str] = []
    params: list[Any] = []
    if plan_id:
        clauses.append("t.plan_id = ?")
        params.append(plan_id)
    if status:
        clauses.append("t.status = ?")
        params.append(status)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"""
        SELECT
            t.id,
            t.plan_id,
            t.task_id,
            t.title,
            t.agent,
            t.status,
            t.decision_owner,
            t.risks_json,
            t.next_action,
            COUNT(DISTINCT e.id) AS evidence_count,
            COUNT(DISTINCT r.id) AS review_count,
            COUNT(DISTINCT CASE WHEN c.status IN ('open', 'escalated') THEN c.id END) AS open_conflict_count
        FROM tasks t
        LEFT JOIN evidence_packages e ON e.task_db_id = t.id
        LEFT JOIN reviews r ON r.task_db_id = t.id
        LEFT JOIN conflicts c ON c.task_db_id = t.id
        {where}
        GROUP BY t.id
        ORDER BY t.created_at ASC, t.task_id ASC
    """
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def print_state_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("暂无状态记录。")
        return
    print("| Task DB ID | Plan ID | Task | Status | Owner | Evidence | Reviews | Open Conflicts | Next |")
    print("|---|---|---|---|---|---:|---:|---:|---|")
    for row in rows:
        print(
            f"| {row['id']} | {row['plan_id']} | {row['task_id']} {row['title']} | "
            f"{row['status']} | {row['decision_owner']} | {row['evidence_count']} | "
            f"{row['review_count']} | {row['open_conflict_count']} | {row['next_action'] or '无'} |"
        )


def print_details(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    print("")
    for row in rows:
        risks = _loads(row.get("risks_json") or "[]")
        print(f"## {row['id']} / {row['task_id']}: {row['title']}")
        print(f"- 状态：{row['status']}")
        print(f"- 决策 owner：{row['decision_owner']}")
        print(f"- 证据包数量：{row['evidence_count']}")
        print(f"- 审查数量：{row['review_count']}")
        print(f"- 未解决冲突：{row['open_conflict_count']}")
        print(f"- 下一步：{row['next_action'] or '无'}")
        if risks:
            print("- 风险：")
            for risk in risks:
                print(f"  - {risk}")
        print("")


def _loads(value: str) -> Any:
    return json.loads(value) if value else []


if __name__ == "__main__":
    raise SystemExit(main())
