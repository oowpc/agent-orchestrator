"""Reporter Agent: render structured plans as Markdown reports."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from backend.models import Plan, Task


class ReporterAgent:
    def render_plan(self, plan: Plan) -> str:
        lines: list[str] = []
        lines.append("# 多 Agent 任务计划")
        lines.append("")
        lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## 需求")
        lines.append("")
        lines.append(plan.requirement)
        lines.append("")
        lines.append("## 是否值得做")
        lines.append("")
        lines.append(plan.worth_doing)
        lines.append("")
        lines.append("## 推荐方案")
        lines.append("")
        lines.append(plan.recommended_solution)
        lines.append("")

        self._append_list(lines, "备选方案", plan.alternatives)
        self._append_list(lines, "假设", plan.assumptions)
        self._append_list(lines, "主要风险", plan.risks)

        lines.append("## 任务拆分")
        lines.append("")
        lines.append("| 任务 ID | Agent | 类型 | 任务 | 依赖 |")
        lines.append("|---|---|---|---|---|")
        for task in plan.tasks:
            deps = ", ".join(task.dependencies) if task.dependencies else "无"
            lines.append(f"| {task.task_id} | {task.agent} | {task.task_type} | {task.title} | {deps} |")
        lines.append("")

        lines.append("## 任务详情")
        lines.append("")
        for task in plan.tasks:
            self._append_task(lines, task)

        self._append_list(lines, "下一步", plan.next_steps)
        return "\n".join(lines).rstrip() + "\n"

    def save_plan(self, plan: Plan, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"plan_{timestamp}.md"
        path.write_text(self.render_plan(plan), encoding="utf-8")
        return path

    def _append_list(self, lines: list[str], title: str, items: list[str]) -> None:
        if not items:
            return
        lines.append(f"## {title}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    def _append_task(self, lines: list[str], task: Task) -> None:
        lines.append(f"### {task.task_id}: {task.title}")
        lines.append("")
        lines.append(f"- 指派 Agent：{task.agent}")
        lines.append(f"- 类型：{task.task_type}")
        deps = ", ".join(task.dependencies) if task.dependencies else "无"
        lines.append(f"- 依赖：{deps}")
        lines.append("")
        lines.append("#### 任务描述")
        lines.append("")
        lines.append(task.description)
        lines.append("")
        if task.acceptance_criteria:
            lines.append("#### 验收标准")
            lines.append("")
            for criterion in task.acceptance_criteria:
                lines.append(f"- [ ] {criterion}")
            lines.append("")
        if task.risks:
            lines.append("#### 风险")
            lines.append("")
            for risk in task.risks:
                lines.append(f"- {risk}")
            lines.append("")
