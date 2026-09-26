from __future__ import annotations

import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


load_dotenv()


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0


class OpenRouterLLM:
    def __init__(
        self,
        model: str | None = None,
        budget_usd: float = 3.0,
        api_key: str | None = None,
        timeout: int = 60,
    ):
        self.model = model or os.getenv(
            "OPENROUTER_MODEL", "qwen/qwen3-235b-a22b-2507"
        )
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is missing. Copy .env.example to .env.")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.budget_usd = float(budget_usd)
        self.timeout = timeout
        self.usage = Usage()
        self.reasoning_effort = os.getenv("OPENROUTER_REASONING_EFFORT", "").strip()
        self.provider_sort = os.getenv("OPENROUTER_PROVIDER_SORT", "throughput").strip()
        self.input_rate = float(os.getenv("OPENROUTER_INPUT_USD_PER_M", "0.20"))
        self.output_rate = float(os.getenv("OPENROUTER_OUTPUT_USD_PER_M", "0.60"))

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.budget_usd - self.usage.cost_usd)

    def complete(self, prompt: str, max_tokens: int = 220) -> str:
        if self.remaining_usd <= 0:
            raise BudgetExceeded(f"Budget exhausted: ${self.usage.cost_usd:.4f}")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "usage": {"include": True},
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        if self.provider_sort:
            payload["provider"] = {"sort": self.provider_sort}

        response = requests.post(
            f"{self.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/pa0lai/baba-agent-workshop",
                "X-Title": "Baba Agent Workshop",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        reported_cost = usage.get("cost")
        estimated_cost = (
            prompt_tokens * self.input_rate + completion_tokens * self.output_rate
        ) / 1_000_000
        cost = float(reported_cost) if reported_cost is not None else estimated_cost
        self.usage.prompt_tokens += prompt_tokens
        self.usage.completion_tokens += completion_tokens
        self.usage.cost_usd += cost
        self.usage.calls += 1

        if self.usage.cost_usd > self.budget_usd:
            raise BudgetExceeded(
                f"Request completed, but budget is now ${self.usage.cost_usd:.4f} "
                f"> ${self.budget_usd:.2f}."
            )
        return data["choices"][0]["message"]["content"]


class ScriptedLLM:
    """Small deterministic test double used by unit tests and smoke runs."""

    def __init__(self, outputs: list[str]):
        self.outputs = list(outputs)
        self.usage = Usage()
        self.budget_usd = 0.0

    def complete(self, prompt: str, max_tokens: int = 220) -> str:
        self.usage.calls += 1
        return self.outputs.pop(0) if self.outputs else "ACTION: idle"
