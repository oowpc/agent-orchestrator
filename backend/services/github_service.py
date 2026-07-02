"""GitHub REST API service.

This service focuses on safe operations first:
- read repository metadata
- read target project config files
- create target project config files
- create Issues from planned task packages
- create Issue comments for evidence, review, and conflict records

Later versions can add branch creation, file updates, draft PRs, and CI status checks.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import requests

from backend.models import Task


class GitHubServiceError(RuntimeError):
    """Raised when GitHub API calls fail."""


@dataclass(frozen=True)
class GitHubIssue:
    number: int
    title: str
    html_url: str


@dataclass(frozen=True)
class GitHubIssueComment:
    id: int
    html_url: str
    body: str


@dataclass(frozen=True)
class GitHubTextFile:
    path: str
    sha: str
    content: str
    html_url: str


@dataclass(frozen=True)
class GitHubCreatedFile:
    path: str
    commit_sha: str
    html_url: str


class GitHubService:
    def __init__(self, token: str, api_base_url: str = "https://api.github.com"):
        if not token:
            raise ValueError("GITHUB_TOKEN is required for GitHub API operations.")
        self.token = token
        self.api_base_url = api_base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def get_repo(self, repo_full_name: str) -> dict[str, Any]:
        response = self.session.get(f"{self.api_base_url}/repos/{repo_full_name}", timeout=30)
        return self._handle_response(response)

    def get_text_file(
        self,
        repo_full_name: str,
        path: str,
        ref: str | None = None,
    ) -> GitHubTextFile:
        params = {"ref": ref} if ref else None
        response = self.session.get(
            f"{self.api_base_url}/repos/{repo_full_name}/contents/{path}",
            params=params,
            timeout=30,
        )
        data = self._handle_response(response)
        if data.get("type") != "file":
            raise GitHubServiceError(f"GitHub path is not a file: {path}")
        if data.get("encoding") != "base64":
            raise GitHubServiceError(f"Unsupported GitHub file encoding: {data.get('encoding')}")
        raw = base64.b64decode(data.get("content", "")).decode("utf-8")
        return GitHubTextFile(
            path=data["path"],
            sha=data["sha"],
            content=raw,
            html_url=data.get("html_url", ""),
        )

    def text_file_exists(self, repo_full_name: str, path: str, ref: str | None = None) -> bool:
        try:
            self.get_text_file(repo_full_name=repo_full_name, path=path, ref=ref)
            return True
        except GitHubServiceError as exc:
            if "GitHub API error 404" in str(exc):
                return False
            raise

    def create_text_file(
        self,
        repo_full_name: str,
        path: str,
        content: str,
        message: str,
        branch: str | None = None,
    ) -> GitHubCreatedFile:
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        }
        if branch:
            payload["branch"] = branch
        response = self.session.put(
            f"{self.api_base_url}/repos/{repo_full_name}/contents/{path}",
            json=payload,
            timeout=30,
        )
        data = self._handle_response(response)
        content_data = data.get("content", {}) or {}
        commit_data = data.get("commit", {}) or {}
        return GitHubCreatedFile(
            path=content_data.get("path", path),
            commit_sha=commit_data.get("sha", ""),
            html_url=content_data.get("html_url", ""),
        )

    def create_issue(
        self,
        repo_full_name: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> GitHubIssue:
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        response = self.session.post(
            f"{self.api_base_url}/repos/{repo_full_name}/issues",
            json=payload,
            timeout=30,
        )
        data = self._handle_response(response)
        return GitHubIssue(number=data["number"], title=data["title"], html_url=data["html_url"])

    def create_issue_comment(
        self,
        repo_full_name: str,
        issue_number: int,
        body: str,
    ) -> GitHubIssueComment:
        response = self.session.post(
            f"{self.api_base_url}/repos/{repo_full_name}/issues/{issue_number}/comments",
            json={"body": body},
            timeout=30,
        )
        data = self._handle_response(response)
        return GitHubIssueComment(
            id=int(data["id"]),
            html_url=data.get("html_url", ""),
            body=data.get("body", ""),
        )

    def create_issue_from_task(
        self,
        repo_full_name: str,
        task: Task,
        plan_id: str | None = None,
        extra_labels: list[str] | None = None,
    ) -> GitHubIssue:
        labels = ["agent-task", f"agent:{_normalize_label(task.agent)}", f"type:{task.task_type}"]
        if extra_labels:
            labels.extend(extra_labels)
        title = f"[{task.task_id}] {task.title}"
        body = render_task_issue_body(task=task, plan_id=plan_id)
        return self.create_issue(repo_full_name=repo_full_name, title=title, body=body, labels=labels)

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        if response.ok:
            return response.json()
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {"message": response.text}
        message = error_payload.get("message", "Unknown GitHub API error")
        raise GitHubServiceError(f"GitHub API error {response.status_code}: {message}")


def render_task_issue_body(task: Task, plan_id: str | None = None) -> str:
    lines: list[str] = []
    lines.append("## 任务来源")
    lines.append("")
    lines.append("由 Agent Orchestrator 自动生成。")
    if plan_id:
        lines.append(f"Plan ID：`{plan_id}`")
    lines.append("")

    lines.append("## 任务包")
    lines.append("")
    lines.append(f"- 目标：{task.goal or task.title}")
    lines.append(f"- 边界：{task.boundary or '只完成本任务范围内的工作。'}")
    lines.append(f"- 决策 owner：{task.decision_owner or 'user'}")
    lines.append(f"- 交付格式：{task.deliverable_format or '证据报告'}")
    lines.append("")

    lines.append("## 指派 Agent")
    lines.append("")
    lines.append(task.agent)
    lines.append("")

    lines.append("## 任务类型")
    lines.append("")
    lines.append(task.task_type)
    lines.append("")

    lines.append("## 任务描述")
    lines.append("")
    lines.append(task.description)
    lines.append("")

    lines.append("## 输入材料")
    lines.append("")
    _append_items_or_none(lines, task.input_materials)
    lines.append("")

    lines.append("## 工具权限")
    lines.append("")
    _append_items_or_none(lines, task.tool_permissions)
    lines.append("")

    lines.append("## 依赖任务")
    lines.append("")
    _append_items_or_none(lines, task.dependencies)
    lines.append("")

    lines.append("## 验收标准")
    lines.append("")
    if task.acceptance_criteria:
        for criterion in task.acceptance_criteria:
            lines.append(f"- [ ] {criterion}")
    else:
        lines.append("- [ ] 补充明确验收标准")
    lines.append("")

    lines.append("## 证据要求")
    lines.append("")
    if task.evidence_requirements:
        for requirement in task.evidence_requirements:
            lines.append(f"- [ ] {requirement}")
    else:
        lines.append("- [ ] 说明完成内容、证据位置、风险和下一步")
    lines.append("")

    lines.append("## 阻塞条件")
    lines.append("")
    _append_items_or_none(lines, task.blocking_conditions)
    lines.append("")

    lines.append("## 风险")
    lines.append("")
    _append_items_or_none(lines, task.risks)
    lines.append("")

    lines.append("## 执行约束")
    lines.append("")
    lines.append("- 不修改无关文件。")
    lines.append("- 危险操作必须先获得确认。")
    lines.append("- 执行 Agent 不修改验收标准。")
    lines.append("- 审查 Agent 不重写执行方案。")
    lines.append("- 完成后必须提交证据包。")
    lines.append("")

    lines.append("## 建议下一步")
    lines.append("")
    lines.append(task.next_action or "等待指派 Agent 执行并提交证据包。")
    return "\n".join(lines)


def _append_items_or_none(lines: list[str], items: list[str]) -> None:
    if items:
        for item in items:
            lines.append(f"- {item}")
    else:
        lines.append("无")


def _normalize_label(value: str) -> str:
    return value.lower().replace(" agent", "").replace(" ", "-").replace("/", "-")
