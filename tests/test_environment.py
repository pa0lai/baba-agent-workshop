import pytest


baba = pytest.importorskip("baba")

from workshop.baba_env import BabaTextEnv  # noqa: E402


def test_real_environment_smoke(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    env = BabaTextEnv("env/goto_win", seed=0, max_steps=10)
    try:
        first = env.reset()
        assert "Rule[" in first.observation.grid
        assert any("you" in rule for rule in first.observation.active_rules)
        second = env.step("idle")
        assert second.observation.step == 1
        assert second.frame.size[0] > 0
    finally:
        env.close()

