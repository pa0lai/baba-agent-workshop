from team_agent import build_prompt, parse_action, select_memory
from workshop.types import Observation, Transition


def sample_observation() -> Observation:
    return Observation(
        grid="00 | Obj[baba] | Rule[flag]\n01 | Rule[baba] | Rule[is]",
        active_rules=("baba is you", "flag is win"),
        step=2,
        max_steps=20,
    )


def test_parse_action_prefers_explicit_final_line():
    assert parse_action("Maybe left.\nACTION: RIGHT") == "right"


def test_parse_action_falls_back_to_idle():
    assert parse_action("I refuse to move") == "idle"


def test_memory_limit():
    history = [Transition(i, "up", 0, False, True, str(i)) for i in range(10)]
    assert [item.step for item in select_memory(history, limit=3)] == [7, 8, 9]


def test_prompt_contains_grid_rules_and_actions():
    prompt = build_prompt(sample_observation(), [])
    assert "Obj[baba]" in prompt
    assert "flag is win" in prompt
    assert "up, right, down, left" in prompt

