"""Project configuration model and loader.

A target project can expose `.agents/project.yaml` so Agent Orchestrator knows
how to plan, dispatch, test, and review tasks for that project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RepoConfig:
    provider: str = "github"
    full_name: str = ""
    default_branch: str = "main"


@dataclass
class ProjectRules:
    prefer_pull_request: bool = True
    allow_direct_commit: bool = False
    require_user_confirmation_for: list[str] = field(default_factory=list)
    protected_paths: list[str] = field(default_factory=list)


@dataclass
class ProjectCommands:
    install: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)
    lint: list[str] = field(default_factory=list)
    frontend_test: list[str] = field(default_factory=list)


@dataclass
class ProjectConfig:
    name: str
    project_type: str
    description: str
    repo: RepoConfig
    tech_stack: dict[str, Any] = field(default_factory=dict)
    agents: dict[str, Any] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    rules: ProjectRules = field(default_factory=ProjectRules)
    commands: ProjectCommands = field(default_factory=ProjectCommands)
    output: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        project_data = data.get("project", {}) or {}
        repo_data = data.get("repo", {}) or {}
        rules_data = data.get("rules", {}) or {}
        commands_data = data.get("commands", {}) or {}

        return cls(
            name=str(project_data.get("name", "unknown-project")),
            project_type=str(project_data.get("type", "unknown")),
            description=str(project_data.get("description", "")),
            repo=RepoConfig(
                provider=str(repo_data.get("provider", "github")),
                full_name=str(repo_data.get("full_name", "")),
                default_branch=str(repo_data.get("default_branch", "main")),
            ),
            tech_stack=dict(data.get("tech_stack", {}) or {}),
            agents=dict(data.get("agents", {}) or {}),
            paths=dict(data.get("paths", {}) or {}),
            rules=ProjectRules(
                prefer_pull_request=bool(rules_data.get("prefer_pull_request", True)),
                allow_direct_commit=bool(rules_data.get("allow_direct_commit", False)),
                require_user_confirmation_for=list(
                    rules_data.get("require_user_confirmation_for", []) or []
                ),
                protected_paths=list(rules_data.get("protected_paths", []) or []),
            ),
            commands=ProjectCommands(
                install=list(commands_data.get("install", []) or []),
                test=list(commands_data.get("test", []) or []),
                lint=list(commands_data.get("lint", []) or []),
                frontend_test=list(commands_data.get("frontend_test", []) or []),
            ),
            output=dict(data.get("output", {}) or {}),
            raw=data,
        )

    @classmethod
    def from_yaml_text(cls, text: str) -> "ProjectConfig":
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("Project config must be a YAML mapping.")
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, path: Path) -> "ProjectConfig":
        return cls.from_yaml_text(path.read_text(encoding="utf-8"))

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.name or self.name == "unknown-project":
            issues.append("project.name is missing")
        if self.repo.provider == "github" and not self.repo.full_name:
            issues.append("repo.full_name is missing")
        if self.rules.allow_direct_commit:
            issues.append("rules.allow_direct_commit=true is risky; prefer Pull Requests")
        return issues

    def summary_markdown(self) -> str:
        lines: list[str] = []
        lines.append(f"# Project Config: {self.name}")
        lines.append("")
        lines.append(f"- 类型：{self.project_type}")
        lines.append(f"- 描述：{self.description or '无'}")
        lines.append(f"- 仓库：{self.repo.full_name or '未配置'}")
        lines.append(f"- 默认分支：{self.repo.default_branch}")
        lines.append("")
        lines.append("## 技术栈")
        lines.append("")
        if self.tech_stack:
            for key, value in self.tech_stack.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("未配置")
        lines.append("")
        lines.append("## 测试命令")
        lines.append("")
        if self.commands.test:
            for command in self.commands.test:
                lines.append(f"- `{command}`")
        else:
            lines.append("未配置")
        lines.append("")
        lines.append("## 安全规则")
        lines.append("")
        lines.append(f"- 优先 PR：{self.rules.prefer_pull_request}")
        lines.append(f"- 允许直接提交：{self.rules.allow_direct_commit}")
        if self.rules.require_user_confirmation_for:
            lines.append("- 需要用户确认：")
            for item in self.rules.require_user_confirmation_for:
                lines.append(f"  - {item}")
        return "\n".join(lines) + "\n"
