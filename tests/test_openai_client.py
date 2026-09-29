from types import SimpleNamespace

import pytest
import requests

from workshop.openai_client import InfrastructureError, OpenAILLM


def make_llm(monkeypatch, retries=2):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return OpenAILLM(max_retries=retries)


def test_retries_429_then_succeeds_and_prices_cached_tokens(monkeypatch):
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
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                    "prompt_tokens_details": {"cached_tokens": 4},
                },
                "choices": [{"message": {"content": "ACTION: right"}}],
            },
        ),
    ]
    monkeypatch.setattr(
        "workshop.openai_client.requests.post", lambda *a, **k: responses.pop(0)
    )
    monkeypatch.setattr("workshop.openai_client.time.sleep", lambda _seconds: None)
    assert llm.complete("go") == "ACTION: right"
    assert llm.usage.calls == 1
    assert llm.usage.cost_usd == pytest.approx(0.000006)


def test_request_uses_direct_openai_chat_completions(monkeypatch):
    captured = {}
    llm = make_llm(monkeypatch, retries=0)
    response = SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [{"message": {"content": "ACTION: up"}}],
        },
    )

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr("workshop.openai_client.requests.post", fake_post)
    llm.complete("go")
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["json"]["model"] == "gpt-4.1-mini"
    assert "provider" not in captured["json"]
    assert "usage" not in captured["json"]
    assert captured["headers"] == {
        "Authorization": "Bearer test-key",
        "Content-Type": "application/json",
    }


def test_timeout_becomes_infrastructure_error(monkeypatch):
    llm = make_llm(monkeypatch, retries=0)
    monkeypatch.setattr(
        "workshop.openai_client.requests.post",
        lambda *a, **k: (_ for _ in ()).throw(requests.Timeout("slow")),
    )
    with pytest.raises(InfrastructureError):
        llm.complete("go")


def test_usage_callback_persists_estimated_cost(monkeypatch):
    seen = []
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    llm = OpenAILLM(
        max_retries=0, usage_callback=lambda usage: seen.append(usage.cost_usd)
    )
    response = SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [{"message": {"content": "ACTION: up"}}],
        },
    )
    monkeypatch.setattr("workshop.openai_client.requests.post", lambda *a, **k: response)
    llm.complete("go")
    assert seen == [pytest.approx(0.000002)]
