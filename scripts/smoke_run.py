"""Offline smoke run that exercises the complete runner without an API key."""

from pathlib import Path

import team_agent
from workshop.openrouter import ScriptedLLM
from workshop.runner import run_episode


def main() -> None:
    llm = ScriptedLLM(["ACTION: idle"] * 4)
    result = run_episode(
        agent=team_agent,
        llm=llm,
        team="SmokeTest",
        task="env/goto_win",
        seed=0,
        max_steps=4,
        output_root=Path("runs"),
        verbose=False,
    )
    print(result.to_dict())


if __name__ == "__main__":
    main()

