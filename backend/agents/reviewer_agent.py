"""Reviewer Agent scaffold.

The first version is rule-based. Later it can be replaced or enhanced with an
LLM reviewer that evaluates task outputs and diffs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.models import Task


@dataclass
class ReviewIssue:
    severity: str
    message: str
    suggestion: str


@dataclass
class ReviewResult:
    passed: bool
    issues: list[ReviewIssue] = field(default_factory=list)
    summary: str = ""


class ReviewerAgent:
    """Review a planned task before execution.

    This is intentionally conservative: it checks whether a task has enough
    information to be safely assigned to a Worker Agent.
    """

    def review_task_plan(self, task: Task) -> ReviewResult:
        issues: list[ReviewIssue] = []

        if not task.description.strip():
            issues.append(
                ReviewIssue(
                    severity="high",
                    message="任务缺少描述。",
                    suggestion="补充任务背景、目标和执行范围。",
                )
            )

        if not task.acceptance_criteria:
            issues.append(
                ReviewIssue(
                    severity="high",
                    message="任务缺少验收标准。",
                    suggestion="为任务添加可检查的验收标准。",
                )
            )

        if "删除" in task.description or "delete" in task.description.lower():
            issues.append(
                ReviewIssue(
                    severity="medium",
                    message="任务可能涉及删除操作。",
                    suggestion="删除文件、数据或资源前必须要求用户确认。",
                )
            )

        passed = not any(issue.severity == "high" for issue in issues)
        summary = "任务计划可执行。" if passed else "任务计划需要补充信息后再执行。"
        return ReviewResult(passed=passed, issues=issues, summary=summary)
