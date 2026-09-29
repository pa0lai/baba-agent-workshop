import json
from types import SimpleNamespace

import pytest
from PIL import Image

import workshop.runner as runner
from workshop.openai_client import Usage
from workshop.openai_client import InfrastructureError
from workshop.types import Observation


class StaticEnvironment:
    def __init__(self, task, seed, max_steps):
        self.max_steps = max_steps
        self.step_number = 0

    def _result(self):
        observation = Observation(
            grid="00 | Obj[baba]",
            active_rules=("baba is you",),
            step=self.step_number,
            max_steps=self.max_steps,
            last_action="right" if self.step_number else None,
            last_result="World did not change." if self.step_number else "Environment reset.",
        )
        return SimpleNamespace(
            observation=observation,
            reward=0.0,
            done=False,
            info={},
            frame=Image.new("RGB", (2, 2)),
            state_hash="static-state",
        )

    def reset(self):
        self.step_number = 0
        return self._result()

    def step(self, action):
        self.step_number += 1
        return self._result()

    def close(self):
        pass


class RepeatingAgent:
    def __init__(self):
        self.feedback = []

    def act(self, observation, history, llm):
        self.feedback.append(observation.last_result)
        llm.usage.calls += 1
        llm.usage.prompt_tokens += 10
        llm.usage.completion_tokens += 2
        llm.usage.cost_usd += 0.1
        return "right"


def test_episode_usage_is_delta_and_loop_guard_stops_at_six(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "BabaTextEnv", StaticEnvironment)
    llm = SimpleNamespace(usage=Usage(100, 20, 5.0, 10))
    agent = RepeatingAgent()

    result = runner.run_episode(
        agent=agent,
        llm=llm,
        team="Test",
        task="env/static",
        seed=0,
        max_steps=20,
        output_root=tmp_path,
        verbose=False,
    )

    assert result.steps == 6
    assert result.stopped_reason == "state_action_repeat_limit"
    assert result.llm_calls == 10
    assert result.prompt_tokens == 100
    assert result.completion_tokens == 20
    assert result.cost_usd == pytest.approx(1.0)
    assert sum("REPLAN REQUIRED" in feedback for feedback in agent.feedback) == 4

    events = [
        json.loads(line)
        for line in (tmp_path / result.run_dir.split("/")[-1] / "trajectory.jsonl")
        .read_text()
        .splitlines()
    ]
    assert [event["loop_guard"]["state_action_streak"] for event in events] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]
    assert [event["loop_guard"]["replanned"] for event in events] == [
        False,
        False,
        True,
        True,
        True,
        True,
    ]


def test_state_action_guard_resets_when_action_changes():
    guard = runner.StateActionGuard()
    assert guard.record("state", "right") == 1
    assert guard.record("state", "right") == 2
    assert guard.next_count("state", "right") == 3
    assert guard.record("state", "left") == 1
    assert guard.next_count("other-state", "left") == 1


class InfrastructureFailingAgent:
    def act(self, observation, history, llm):
        raise InfrastructureError("provider unavailable")


def test_infrastructure_error_is_not_invalid_student_action(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "BabaTextEnv", StaticEnvironment)
    result = runner.run_episode(
        agent=InfrastructureFailingAgent(),
        llm=SimpleNamespace(usage=Usage()),
        team="Test",
        task="env/static",
        seed=0,
        max_steps=20,
        output_root=tmp_path,
        verbose=False,
    )
    assert result.steps == 0
    assert result.invalid_actions == 0
    assert result.stopped_reason == "infrastructure_error"


def test_expired_episode_deadline_stops_before_agent_call(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "BabaTextEnv", StaticEnvironment)
    agent = RepeatingAgent()
    result = runner.run_episode(
        agent=agent,
        llm=SimpleNamespace(usage=Usage()),
        team="Test",
        task="env/static",
        seed=0,
        max_steps=20,
        output_root=tmp_path,
        verbose=False,
        deadline_monotonic=0,
    )
    assert not agent.feedback
    assert result.stopped_reason == "time_limit"
