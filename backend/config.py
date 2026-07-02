"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


if load_dotenv:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "mock-planner")

    outputs_dir: Path = Path(os.getenv("OUTPUTS_DIR", "outputs"))
    prompts_dir: Path = Path(os.getenv("PROMPTS_DIR", "backend/prompts"))

    enable_code_execution: bool = os.getenv("ENABLE_CODE_EXECUTION", "false").lower() == "true"
    enable_github_write: bool = os.getenv("ENABLE_GITHUB_WRITE", "false").lower() == "true"

    @property
    def use_mock_llm(self) -> bool:
        """Use deterministic mock output when no real API key is configured."""
        return not self.llm_api_key or self.llm_provider.lower() == "mock"


def get_settings() -> Settings:
    return Settings()
