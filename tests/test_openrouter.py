from types import SimpleNamespace

import pytest
import requests

from workshop.openrouter import InfrastructureError, OpenRouterLLM


def make_llm(monkeypatch, retries=2):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return OpenRouterLLM(max_retries=retries)


def test_retries_429_then_succeeds_without_double_counting(monkeypatch):
    llm = make_llm(monkeypatch)
    responses = [
        SimpleNamespace(
            status_code=429,
            raise_for_status=lambda: (_ for _ in ()).throw(
                requests.HTTPError(response=SimpleNamespace(status_code=429))
            ),
        ),
        SimpleNamespace(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "cost": 0.001},
                "choices": [{"message": {"content": "ACTION: right"}}],
            },
        ),
    ]
    monkeypatch.setattr("workshop.openrouter.requests.post", lambda *a, **k: responses.pop(0))
    monkeypatch.setattr("workshop.openrouter.time.sleep", lambda _seconds: None)
    assert llm.complete("go") == "ACTION: right"
    assert llm.usage.calls == 1
    assert llm.usage.cost_usd == pytest.approx(0.001)


def test_timeout_becomes_infrastructure_error(monkeypatch):
    llm = make_llm(monkeypatch, retries=0)
    monkeypatch.setattr(
        "workshop.openrouter.requests.post",
        lambda *a, **k: (_ for _ in ()).throw(requests.Timeout("slow")),
    )
    with pytest.raises(InfrastructureError):
        llm.complete("go")


def test_usage_callback_persists_each_successful_request(monkeypatch):
    seen = []
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    llm = OpenRouterLLM(max_retries=0, usage_callback=lambda usage: seen.append(usage.cost_usd))
    response = SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "cost": 0.002},
            "choices": [{"message": {"content": "ACTION: up"}}],
        },
    )
    monkeypatch.setattr("workshop.openrouter.requests.post", lambda *a, **k: response)
    llm.complete("go")
    assert seen == [pytest.approx(0.002)]
