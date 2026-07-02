"""Core data models for the CLI MVP.

These models intentionally keep the multi-agent workflow evidence-driven:
- Task is upgraded into a task package.
- EvidencePackage records what an agent actually did and where proof lives.
- ReviewRecord and ConflictRecord make disagreement explicit instead of implicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    task_id: str
    title: str
    agent: str
    task_type: str
    description: str
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    # Task package fields
    goal: str = ""
    boundary: str = ""
    input_materials: list[str] = field(default_factory=list)
    tool_permissions: list[str] = field(default_factory=list)
    deliverable_format: str = ""
    evidence_requirements: list[str] = field(default_factory=list)
    blocking_conditions: list[str] = field(default_factory=list)
    decision_owner: str = "user"
    next_action: str = ""


@dataclass
class EvidencePackage:
    task_db_id: str
    agent_name: str
    completed_work: str
    evidence_locations: list[str] = field(default_factory=list)
    commands_run: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    suggested_next_steps: list[str] = field(default_factory=list)


@dataclass
class ReviewRecord:
    task_db_id: str
    reviewer_agent: str
    passed: bool
    summary: str
    issues: list[dict[str, Any]] = field(default_factory=list)
    evidence_package_id: str | None = None


@dataclass
class ConflictRecord:
    task_db_id: str
    conflict_type: str
    agents_involved: list[str]
    claims: list[dict[str, Any]]
    evidence_refs: list[str]
    decision_owner: str
    status: str = "open"
    final_decision: str = ""


@dataclass
class DecisionRecord:
    conflict_id: str
    decision_owner: str
    decision: str
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class Plan:
    requirement: str
    worth_doing: str
    recommended_solution: str
    alternatives: list[str]
    risks: list[str]
    tasks: list[Task]
    assumptions: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Plan":
        tasks = [
            Task(
                task_id=str(item.get("task_id", "")),
                title=str(item.get("title", "")),
                agent=str(item.get("agent", "General Worker Agent")),
                task_type=str(item.get("task_type", "general")),
                description=str(item.get("description", "")),
                acceptance_criteria=list(item.get("acceptance_criteria", [])),
                dependencies=list(item.get("dependencies", [])),
                risks=list(item.get("risks", [])),
                goal=str(item.get("goal", item.get("title", ""))),
                boundary=str(item.get("boundary", "只完成本任务范围内的工作，不修改无关模块。")),
                input_materials=list(item.get("input_materials", [])),
                tool_permissions=list(item.get("tool_permissions", [])),
                deliverable_format=str(
                    item.get(
                        "deliverable_format",
                        "Markdown summary with changed files, evidence, risks, and next steps.",
                    )
                ),
                evidence_requirements=list(
                    item.get(
                        "evidence_requirements",
                        [
                            "说明完成了什么",
                            "列出修改文件或证据位置",
                            "列出运行过的命令和结果",
                            "列出剩余风险和建议下一步",
                        ],
                    )
                ),
                blocking_conditions=list(
                    item.get(
                        "blocking_conditions",
                        ["需求不明确", "缺少必要输入材料", "需要超出权限的工具或危险操作"],
                    )
                ),
                decision_owner=str(item.get("decision_owner", "user")),
                next_action=str(item.get("next_action", "等待指派 Agent 执行并提交证据包。")),
            )
            for item in data.get("tasks", [])
        ]
        return cls(
            requirement=str(data.get("requirement", "")),
            worth_doing=str(data.get("worth_doing", "")),
            recommended_solution=str(data.get("recommended_solution", "")),
            alternatives=list(data.get("alternatives", [])),
            risks=list(data.get("risks", [])),
            tasks=tasks,
            assumptions=list(data.get("assumptions", [])),
            next_steps=list(data.get("next_steps", [])),
        )
