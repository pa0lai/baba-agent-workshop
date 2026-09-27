import json
import sys
from pathlib import Path

from PIL import Image

import challenge
from challenge import progress_bar
from workshop.openrouter import Usage
from workshop.report import write_report
from workshop.runner import EpisodeResult
from workshop.tasks import BONUS_LEVELS, CHALLENGE_LEVELS, CORE_LEVELS, LEVEL_BY_NAME


def test_challenge_catalog_has_eight_core_and_two_bonus_levels():
    assert len(CHALLENGE_LEVELS) == 10
    assert len(CORE_LEVELS) == 8
    assert len(BONUS_LEVELS) == 2
    assert len(LEVEL_BY_NAME) == 10
    assert LEVEL_BY_NAME["make_win"]["task"] == "env/make_win"


def test_progress_bar():
    assert progress_bar(6, 8) == "█" * 15 + "░" * 5


def test_local_report_contains_results_replay_and_agent_hash(tmp_path):
    episode_dir = tmp_path / "episodes" / "one"
    episode_dir.mkdir(parents=True)
    Image.new("RGB", (2, 2)).save(episode_dir / "replay.gif")
    agent_path = tmp_path / "team_agent.py"
    agent_path.write_text("def act(): pass\n", encoding="utf-8")
    result = EpisodeResult(
        team="Test",
        task="env/goto_win",
        seed=0,
        success=True,
        reward=1.0,
        steps=7,
        repeated_states=0,
        invalid_actions=0,
        llm_calls=7,
        prompt_tokens=100,
        completion_tokens=20,
        cost_usd=0.01,
        duration_seconds=3.5,
        stopped_reason="success",
        run_dir=str(episode_dir),
    )

    report = write_report(
        output_dir=tmp_path,
        results=[result],
        agent_path=agent_path,
        model="test/model",
        selected_tasks=[item["task"] for item in CORE_LEVELS],
    )

    page = report.read_text(encoding="utf-8")
    payload = json.loads((tmp_path / "challenge.json").read_text())
    assert "1 / 8 CLEARED" in page
    assert "replay.gif" in page
    assert "goto_win" in page
    assert payload["agent_sha256"] in page
    assert payload["episodes"][0]["duration_seconds"] == 3.5
    assert payload["core_total"] == 8


def test_core_run_honors_cli_team_and_resume_skips_cleared(monkeypatch, tmp_path):
    calls = []

    class FakeLLM:
        def __init__(self, model=None, budget_usd=0, usage_callback=None):
            self.model = model or "test/model"
            self.usage = Usage()

        def set_deadline(self, deadline):
            self.deadline = deadline

    def fake_run_episode(**kwargs):
        calls.append(kwargs)
        return EpisodeResult(
            team=kwargs["team"],
            task=kwargs["task"],
            seed=kwargs["seed"],
            success=True,
            reward=1.0,
            steps=1,
            repeated_states=0,
            invalid_actions=0,
            llm_calls=0,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            duration_seconds=0.1,
            stopped_reason="success",
            run_dir=str(tmp_path / "episode"),
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(challenge, "OpenRouterLLM", FakeLLM)
    monkeypatch.setattr(challenge, "run_episode", fake_run_episode)
    monkeypatch.setattr(challenge.time, "strftime", lambda _format: "fixed")
    ledger = tmp_path / "ledger.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["challenge.py", "--core", "--team", "CLI Team", "--budget-ledger", str(ledger)],
    )
    challenge.main()

    output_dir = tmp_path / "runs" / "challenge-fixed"
    payload = json.loads((output_dir / "challenge.json").read_text(encoding="utf-8"))
    assert len(calls) == 8
    assert {call["team"] for call in calls} == {"CLI Team"}
    assert payload["core_cleared"] == 8

    monkeypatch.setattr(
        sys,
        "argv",
        ["challenge.py", "--resume", str(output_dir), "--team", "CLI Team", "--budget-ledger", str(ledger)],
    )
    challenge.main()
    assert len(calls) == 8
