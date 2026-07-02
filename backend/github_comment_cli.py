"""Post local task records to GitHub Issues as comments."""

from __future__ import annotations

import argparse
import sys

from backend.config import get_settings
from backend.services.github_service import GitHubService, GitHubServiceError
from backend.task_manager import TaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-github-comment")
    subparsers = parser.add_subparsers(dest="command")

    evidence = subparsers.add_parser("evidence")
    evidence.add_argument("repo_full_name")
    evidence.add_argument("issue_number", type=int)
    evidence.add_argument("evidence_id")
    evidence.add_argument("--dry-run", action="store_true")

    review = subparsers.add_parser("review")
    review.add_argument("repo_full_name")
    review.add_argument("issue_number", type=int)
    review.add_argument("evidence_id")
    review.add_argument("--dry-run", action="store_true")

    conflict = subparsers.add_parser("conflict")
    conflict.add_argument("repo_full_name")
    conflict.add_argument("issue_number", type=int)
    conflict.add_argument("conflict_id")
    conflict.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.command:
        print("Use evidence, review, or conflict.")
        return 1

    settings = get_settings()
    manager = TaskManager(settings.database_path)

    try:
        if args.command == "evidence":
            body = render_evidence(manager.get_evidence(args.evidence_id))
        elif args.command == "review":
            rows = manager.list_reviews(evidence_package_id=args.evidence_id)
            if not rows:
                raise ValueError("No review records found.")
            body = render_reviews(args.evidence_id, rows)
        elif args.command == "conflict":
            rows = [row for row in manager.list_conflicts() if row["id"] == args.conflict_id]
            if not rows:
                raise ValueError("Conflict record not found.")
            body = render_conflict(rows[0])
        else:
            return 1

        if args.dry_run:
            print(body)
            return 0

        if not settings.enable_github_write:
            raise ValueError("GitHub write is disabled. Set ENABLE_GITHUB_WRITE=true to enable it.")
        service = GitHubService(token=settings.github_token, api_base_url=settings.github_api_base_url)
        comment = service.create_issue_comment(args.repo_full_name, args.issue_number, body)
        print(comment.html_url)
        return 0
    except (ValueError, GitHubServiceError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


def render_evidence(row: dict) -> str:
    lines = [
        "## Evidence Package",
        "",
        f"Evidence ID: `{row['id']}`",
        f"Task DB ID: `{row['task_db_id']}`",
        f"Agent: {row['agent_name']}",
        "",
        "### Completed Work",
        row["completed_work"],
    ]
    add_list(lines, "Evidence Locations", row["evidence_locations"])
    add_list(lines, "Commands Run", row["commands_run"])
    add_list(lines, "Changed Files", row["changed_files"])
    add_list(lines, "Risks", row["risks"])
    add_list(lines, "Suggested Next Steps", row["suggested_next_steps"])
    return "\n".join(lines)


def render_reviews(evidence_id: str, rows: list[dict]) -> str:
    lines = ["## Review Records", "", f"Evidence ID: `{evidence_id}`"]
    for row in rows:
        result = "passed" if row["passed"] else "failed"
        lines += ["", f"### Review `{row['id']}`", f"Reviewer: {row['reviewer_agent']}", f"Result: {result}", f"Summary: {row['summary']}"]
        if row["issues"]:
            lines.append("Issues:")
            for issue in row["issues"]:
                lines.append(f"- [{issue.get('severity', 'unknown')}] {issue.get('message', '')} / {issue.get('suggestion', '')}")
    return "\n".join(lines)


def render_conflict(row: dict) -> str:
    lines = [
        "## Conflict Record",
        "",
        f"Conflict ID: `{row['id']}`",
        f"Task DB ID: `{row['task_db_id']}`",
        f"Type: {row['conflict_type']}",
        f"Decision Owner: {row['decision_owner']}",
        f"Status: {row['status']}",
    ]
    if row["final_decision"]:
        lines.append(f"Final Decision: {row['final_decision']}")
    add_list(lines, "Agents Involved", row["agents_involved"])
    if row["claims"]:
        lines += ["", "### Claims"]
        for claim in row["claims"]:
            lines.append(f"- {claim.get('agent', 'unknown')}: {claim.get('claim', '')}")
    add_list(lines, "Evidence Refs", row["evidence_refs"])
    return "\n".join(lines)


def add_list(lines: list[str], title: str, items: list[str]) -> None:
    if items:
        lines += ["", f"### {title}"]
        for item in items:
            lines.append(f"- {item}")


if __name__ == "__main__":
    raise SystemExit(main())
