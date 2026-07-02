"""Core data models for the CLI MVP."""

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
