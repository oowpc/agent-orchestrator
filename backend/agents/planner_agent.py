"""Planner Agent: convert a user requirement into a structured task plan."""

from __future__ import annotations

import json
import re
from pathlib import Path

from backend.config import Settings
from backend.models import Plan
from backend.services.llm_client import LLMClient


class PlannerAgent:
    def __init__(self, llm_client: LLMClient, settings: Settings):
        self.llm_client = llm_client
        self.settings = settings

    def run(self, requirement: str, project_name: str | None = None) -> Plan:
        prompt = self._build_prompt(requirement=requirement, project_name=project_name)
        response = self.llm_client.complete(prompt)
        data = self._parse_json(response.content)
        if not data.get("requirement"):
            data["requirement"] = requirement
        return Plan.from_dict(data)

    def _build_prompt(self, requirement: str, project_name: str | None = None) -> str:
        prompt_path = self.settings.prompts_dir / "planner.md"
        if prompt_path.exists():
            template = prompt_path.read_text(encoding="utf-8")
        else:
            template = DEFAULT_PLANNER_PROMPT
        return template.format(
            requirement=requirement,
            project_name=project_name or "未指定项目",
        )

    def _parse_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```json\s*(.*?)\s*```", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(1))

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])

        raise ValueError("Planner Agent did not return valid JSON.")


DEFAULT_PLANNER_PROMPT = """
你是一个多 Agent 项目的 Planner Agent。

项目名称：{project_name}
用户需求：{requirement}

请把需求拆解成结构化任务计划。

要求：
1. 判断这个需求是否值得做。
2. 给出 2-3 个备选方案。
3. 选择一个推荐方案。
4. 分析风险。
5. 拆成多个任务，每个任务必须包含 Agent、任务类型、描述、验收标准、依赖和风险。
6. 不要直接写代码。
7. 只输出 JSON，不要输出 Markdown。

JSON 格式：
{{
  "requirement": "...",
  "worth_doing": "...",
  "recommended_solution": "...",
  "alternatives": ["..."],
  "risks": ["..."],
  "assumptions": ["..."],
  "tasks": [
    {{
      "task_id": "T001",
      "title": "...",
      "agent": "Backend Agent / Frontend Agent / Tester Agent / Reviewer Agent / Docs Agent / Planner Agent",
      "task_type": "backend / frontend / test / review / docs / planning / general",
      "description": "...",
      "acceptance_criteria": ["..."],
      "dependencies": [],
      "risks": ["..."]
    }}
  ],
  "next_steps": ["..."]
}}
""".strip()
