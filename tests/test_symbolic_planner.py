import pytest

from instructor.symbolic_planner import World, find_plan
from workshop.baba_env import BabaTextEnv
from workshop.tasks import CHALLENGE_LEVELS
from workshop.types import Observation


def observation(grid, rules=("baba is you", "door is win"), max_steps=20):
    return Observation(grid=grid, active_rules=rules, step=0, max_steps=max_steps)


def test_planner_finds_direct_win_path():
    grid = """     c00   c01   c02
00 | Obj[baba, white] | . | Obj[door, red]
01 | Rule[baba] | Rule[is] | Rule[you]
02 | Rule[door] | Rule[is] | Rule[win]"""
    assert find_plan(observation(grid)) == ["right", "right"]


def test_world_recomputes_rule_after_text_push():
    grid = """     c00   c01   c02
00 | . | Rule[is] | Rule[win]
01 | Rule[ball] | . | .
02 | Obj[baba, white] | . | Obj[ball, red]
03 | Rule[baba] | Rule[is] | Rule[you]"""
    world = World.from_observation(observation(grid, rules=("baba is you",)))
    moved = world.step(world.positions, -1, 0)
    assert ("ball", "win") in world.rules(moved)


@pytest.mark.parametrize("level", CHALLENGE_LEVELS, ids=lambda item: item["level"])
def test_symbolic_plan_clears_real_environment(level, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    env = BabaTextEnv(level["task"], seed=level["seed"], max_steps=level["max_steps"])
    try:
        current = env.reset()
        plan = find_plan(current.observation)
        assert plan is not None
        for action in plan:
            current = env.step(action)
            if current.done:
                break
        assert current.done and current.reward > 0
    finally:
        env.close()
