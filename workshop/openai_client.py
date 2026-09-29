from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable

import requests
from dotenv import load_dotenv


load_dotenv()


class BudgetExceeded(RuntimeError):
    pass


class InfrastructureError(RuntimeError):
    """OpenAI API/network failure that must not be scored as an agent error."""


class RequestDeadlineExceeded(InfrastructureError):
    pass


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0


class OpenAILLM:
    def __init__(
        self,
        model: str | None = None,
        budget_usd: float = 3.0,
        api_key: str | None = None,
        timeout: int = 60,
        max_retries: int = 2,
        usage_callback: Callable[[Usage], None] | None = None,
    ):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Copy .env.example to .env.")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.budget_usd = float(budget_usd)
        self.timeout = timeout
        self.max_retries = max_retries
        self.usage_callback = usage_callback
        self.deadline_monotonic: float | None = None
        self.usage = Usage()
        self.input_rate = float(os.getenv("OPENAI_INPUT_USD_PER_M", "0.40"))
        self.cached_input_rate = float(
            os.getenv("OPENAI_CACHED_INPUT_USD_PER_M", "0.10")
        )
        self.output_rate = float(os.getenv("OPENAI_OUTPUT_USD_PER_M", "1.60"))

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.budget_usd - self.usage.cost_usd)

    def set_deadline(self, deadline_monotonic: float | None) -> None:
        self.deadline_monotonic = deadline_monotonic

    def _request_timeout(self) -> float:
        if self.deadline_monotonic is None:
            return float(self.timeout)
        remaining = self.deadline_monotonic - time.monotonic()
        if remaining <= 0:
            raise RequestDeadlineExceeded("Challenge time limit reached before API call.")
        return max(0.1, min(float(self.timeout), remaining))

    def complete(self, prompt: str, max_tokens: int = 220) -> str:
        if self.remaining_usd <= 0:
            raise BudgetExceeded(f"Budget exhausted: ${self.usage.cost_usd:.4f}")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }

        response = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self._request_timeout(),
                )
                response.raise_for_status()
                break
            except (requests.Timeout, requests.ConnectionError) as exc:
                retryable = True
                last_error = exc
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                retryable = status == 429 or (status is not None and status >= 500)
                last_error = exc
            except requests.RequestException as exc:
                retryable = False
                last_error = exc

            if not retryable or attempt >= self.max_retries:
                raise InfrastructureError(
                    f"OpenAI API request failed after {attempt + 1} attempt(s): {last_error}"
                ) from last_error
            delay = min(2**attempt, 4)
            if self.deadline_monotonic is not None:
                remaining = self.deadline_monotonic - time.monotonic()
                if remaining <= delay:
                    raise RequestDeadlineExceeded(
                        "Challenge time limit reached while retrying OpenAI API."
                    ) from last_error
            time.sleep(delay)

        if response is None:  # pragma: no cover - defensive
            raise InfrastructureError("OpenAI API returned no response.")
        try:
            data = response.json()
            usage = data.get("usage") or {}
            prompt_tokens = int(usage.get("prompt_tokens") or 0)
            completion_tokens = int(usage.get("completion_tokens") or 0)
            details = usage.get("prompt_tokens_details") or {}
            cached_tokens = min(
                prompt_tokens, max(0, int(details.get("cached_tokens") or 0))
            )
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("message content is not text")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise InfrastructureError(f"Malformed OpenAI API response: {exc}") from exc

        uncached_tokens = prompt_tokens - cached_tokens
        cost = (
            uncached_tokens * self.input_rate
            + cached_tokens * self.cached_input_rate
            + completion_tokens * self.output_rate
        ) / 1_000_000
        self.usage.prompt_tokens += prompt_tokens
        self.usage.completion_tokens += completion_tokens
        self.usage.cost_usd += cost
        self.usage.calls += 1
        if self.usage_callback is not None:
            try:
                self.usage_callback(self.usage)
            except OSError as exc:
                raise InfrastructureError(f"Could not persist budget ledger: {exc}") from exc

        if self.usage.cost_usd > self.budget_usd:
            raise BudgetExceeded(
                f"Request completed, but budget is now ${self.usage.cost_usd:.4f} "
                f"> ${self.budget_usd:.2f}."
            )
        return content


class ScriptedLLM:
    """Small deterministic test double used by unit tests and smoke runs."""

    def __init__(self, outputs: list[str]):
        self.outputs = list(outputs)
        self.usage = Usage()
        self.budget_usd = 0.0
        self.deadline_monotonic = None

    def set_deadline(self, deadline_monotonic: float | None) -> None:
        self.deadline_monotonic = deadline_monotonic

    def complete(self, prompt: str, max_tokens: int = 220) -> str:
        self.usage.calls += 1
        return self.outputs.pop(0) if self.outputs else "ACTION: idle"
