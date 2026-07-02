"""Reviewer Agent scaffold.

The first version is rule-based. Later it can be replaced or enhanced with an
LLM reviewer that evaluates task outputs and diffs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.models import EvidencePackage, Task


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
    """Review task packages and evidence packages.

    This is intentionally conservative: it checks whether a task has enough
    information to be safely assigned to a Worker Agent, and whether a Worker
    submitted enough evidence to support a status change.
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

        if not task.goal.strip():
            issues.append(
                ReviewIssue(
                    severity="high",
                    message="任务缺少明确目标。",
                    suggestion="补充 goal 字段，说明这个任务要达成什么。",
                )
            )

        if not task.boundary.strip():
            issues.append(
                ReviewIssue(
                    severity="medium",
                    message="任务缺少边界说明。",
                    suggestion="补充 boundary 字段，说明不做什么，避免 Agent 扩散修改。",
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

        if not task.evidence_requirements:
            issues.append(
                ReviewIssue(
                    severity="high",
                    message="任务缺少证据要求。",
                    suggestion="补充 evidence_requirements，要求执行 Agent 提供完成内容、证据位置、风险和下一步。",
                )
            )

        if not task.blocking_conditions:
            issues.append(
                ReviewIssue(
                    severity="medium",
                    message="任务缺少阻塞条件。",
                    suggestion="补充 blocking_conditions，说明什么情况下必须停止并上报。",
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
        summary = "任务包可执行。" if passed else "任务包需要补充信息后再执行。"
        return ReviewResult(passed=passed, issues=issues, summary=summary)

    def review_evidence_package(self, evidence: EvidencePackage) -> ReviewResult:
        issues: list[ReviewIssue] = []

        if not evidence.completed_work.strip():
            issues.append(
                ReviewIssue(
                    severity="high",
                    message="证据包缺少完成内容。",
                    suggestion="补充 completed_work，说明实际完成了什么。",
                )
            )

        if not evidence.evidence_locations and not evidence.changed_files and not evidence.commands_run:
            issues.append(
                ReviewIssue(
                    severity="high",
                    message="证据包缺少可核查证据。",
                    suggestion="至少提供证据位置、修改文件或运行命令之一。",
                )
            )

        if not evidence.suggested_next_steps:
            issues.append(
                ReviewIssue(
                    severity="medium",
                    message="证据包缺少建议下一步。",
                    suggestion="补充 suggested_next_steps，方便 Orchestrator 更新状态表。",
                )
            )

        passed = not any(issue.severity == "high" for issue in issues)
        summary = "证据包可用于状态更新。" if passed else "证据包不足，不能支持状态变更。"
        return ReviewResult(passed=passed, issues=issues, summary=summary)
