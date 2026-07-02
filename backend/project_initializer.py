"""Initialize target projects for Agent Orchestrator.

This module creates the `.agents/` files required for a target project to be
managed by Agent Orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.services.github_service import GitHubService, GitHubServiceError


@dataclass
class InitFile:
    path: str
    content: str


@dataclass
class InitResult:
    created: list[str]
    skipped: list[str]


class ProjectInitializer:
    def __init__(self, templates_dir: Path = Path("templates")):
        self.templates_dir = templates_dir

    def build_files(
        self,
        project_name: str,
        repo_full_name: str,
        project_type: str = "web-app",
        description: str = "",
        frontend: str = "React",
        backend: str = "FastAPI",
        database: str = "SQLite",
        default_branch: str = "main",
        test_command: str = "pytest",
        lint_command: str = "ruff check .",
    ) -> list[InitFile]:
        project_yaml = self._render_project_yaml(
            project_name=project_name,
            repo_full_name=repo_full_name,
            project_type=project_type,
            description=description,
            frontend=frontend,
            backend=backend,
            database=database,
            default_branch=default_branch,
            test_command=test_command,
            lint_command=lint_command,
        )
        return [
            InitFile(".agents/project.yaml", project_yaml),
            InitFile(".agents/roles.md", self._read_template("roles.md")),
            InitFile(".agents/coding-rules.md", self._read_template("coding-rules.md")),
            InitFile(".agents/test-rules.md", self._read_template("test-rules.md")),
        ]

    def init_local(self, project_path: Path, files: list[InitFile], overwrite: bool = False) -> InitResult:
        created: list[str] = []
        skipped: list[str] = []
        for file in files:
            target = project_path / file.path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not overwrite:
                skipped.append(file.path)
                continue
            target.write_text(file.content, encoding="utf-8")
            created.append(file.path)
        return InitResult(created=created, skipped=skipped)

    def init_github(
        self,
        service: GitHubService,
        repo_full_name: str,
        files: list[InitFile],
        branch: str | None = None,
        overwrite: bool = False,
    ) -> InitResult:
        if overwrite:
            raise ValueError("GitHub overwrite is not supported yet. Use a PR workflow in a later version.")

        created: list[str] = []
        skipped: list[str] = []
        for file in files:
            if service.text_file_exists(repo_full_name=repo_full_name, path=file.path, ref=branch):
                skipped.append(file.path)
                continue
            service.create_text_file(
                repo_full_name=repo_full_name,
                path=file.path,
                content=file.content,
                message=f"chore: add Agent Orchestrator config {file.path}",
                branch=branch,
            )
            created.append(file.path)
        return InitResult(created=created, skipped=skipped)

    def _read_template(self, name: str) -> str:
        path = self.templates_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        return path.read_text(encoding="utf-8")

    def _render_project_yaml(
        self,
        project_name: str,
        repo_full_name: str,
        project_type: str,
        description: str,
        frontend: str,
        backend: str,
        database: str,
        default_branch: str,
        test_command: str,
        lint_command: str,
    ) -> str:
        return f"""# Target project configuration for Agent Orchestrator

project:
  name: {project_name}
  type: {project_type}
  description: {description or '由 Agent Orchestrator 管理的目标项目'}

repo:
  provider: github
  full_name: {repo_full_name}
  default_branch: {default_branch}

tech_stack:
  frontend: {frontend}
  backend: {backend}
  database: {database}
  language:
    - Python
    - TypeScript

agents:
  planner: enabled
  backend_worker: enabled
  frontend_worker: enabled
  tester: enabled
  reviewer: enabled
  docs: enabled
  devops: disabled

paths:
  backend: backend/
  frontend: frontend/
  tests: tests/
  docs: docs/

rules:
  prefer_pull_request: true
  allow_direct_commit: false
  require_user_confirmation_for:
    - delete_file
    - database_migration
    - dependency_change
    - deploy
    - merge_pr
    - large_refactor
  protected_paths:
    - .env
    - .env.*
    - secrets/
    - credentials/

commands:
  install:
    - pip install -r requirements.txt
  test:
    - {test_command}
  lint:
    - {lint_command}
  frontend_test:
    - npm test

output:
  report_format: markdown
  save_reports_to: .agents/reports/
  create_github_issues: true
  create_pull_requests: true

notes:
  - 所有 Agent 输出必须有验收标准。
  - Worker Agent 不允许修改无关文件。
  - 任何危险操作都必须等待用户确认。
"""
