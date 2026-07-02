"""LLM client wrapper.

The CLI MVP supports two modes:
1. mock mode: deterministic local output, useful before API keys are configured.
2. openai-compatible mode: call any OpenAI-compatible chat completions API.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.config import Settings


@dataclass
class LLMResponse:
    content: str
    model: str


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(self, prompt: str) -> LLMResponse:
        if self.settings.use_mock_llm:
            return LLMResponse(content=self._mock_response(prompt), model="mock-planner")

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openai package is required. Run: pip install -r requirements.txt") from exc

        client = OpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url or None,
        )
        response = client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        return LLMResponse(content=content, model=self.settings.llm_model)

    def _mock_response(self, prompt: str) -> str:
        return """
{
  "requirement": "根据用户输入生成多 Agent 任务计划",
  "worth_doing": "值得做。该需求适合作为 Orchestrator 的第一阶段能力，可以先验证任务拆解、风险分析和验收标准生成流程。",
  "recommended_solution": "先实现命令行 Planner MVP：输入需求，输出任务拆分、风险、验收标准和 Markdown 报告；暂不自动改代码。",
  "alternatives": [
    "方案 A：只做命令行 Planner，最快验证核心流程。",
    "方案 B：加入 SQLite 任务状态管理，便于后续扩展。",
    "方案 C：直接接入 GitHub Issues，但复杂度更高。"
  ],
  "risks": [
    "如果过早自动改代码，可能带来安全风险。",
    "如果任务没有验收标准，后续 Agent 执行会发散。",
    "如果没有日志，后续难以追踪 Agent 做过什么。"
  ],
  "assumptions": [
    "当前阶段优先做可控 MVP。",
    "默认不执行危险操作。",
    "用户会手动确认后续代码修改。"
  ],
  "tasks": [
    {
      "task_id": "T001",
      "title": "实现 CLI 入口",
      "agent": "Backend Agent",
      "task_type": "backend",
      "description": "提供命令行入口，接收用户需求并调用 Planner Agent。",
      "acceptance_criteria": [
        "支持 python -m backend.main \"需求文本\" 调用",
        "无需求输入时给出清晰错误提示",
        "能把生成结果保存到 outputs/plans/"
      ],
      "dependencies": [],
      "risks": ["命令行参数解析需要保持简单，避免过早复杂化。"]
    },
    {
      "task_id": "T002",
      "title": "实现 Planner Agent",
      "agent": "Planner Agent",
      "task_type": "planning",
      "description": "把用户需求转换为结构化任务计划。",
      "acceptance_criteria": [
        "输出是否值得做",
        "输出推荐方案",
        "输出风险分析",
        "输出任务列表和验收标准"
      ],
      "dependencies": ["T001"],
      "risks": ["LLM 输出可能不是合法 JSON，需要做容错处理。"]
    },
    {
      "task_id": "T003",
      "title": "实现 Markdown 报告生成",
      "agent": "Reporter Agent",
      "task_type": "docs",
      "description": "把结构化计划转换为可读的 Markdown 报告。",
      "acceptance_criteria": [
        "报告包含需求、方案、风险、任务拆分、下一步",
        "报告表格结构清晰",
        "报告能直接保存为 .md 文件"
      ],
      "dependencies": ["T002"],
      "risks": ["报告过长时需要保持结构清楚。"]
    }
  ],
  "next_steps": [
    "先运行 mock 模式验证命令行流程。",
    "配置真实 LLM_API_KEY 后再接入模型。",
    "确认输出格式稳定后再加入 SQLite。"
  ]
}
""".strip()
