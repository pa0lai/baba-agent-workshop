from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path

from dotenv import load_dotenv

from workshop.baba_env import BabaTextEnv
from workshop.openrouter import OpenRouterLLM
from workshop.runner import run_episode


load_dotenv()


def manual(task: str, seed: int, max_steps: int) -> None:
    env = BabaTextEnv(task, seed=seed, max_steps=max_steps)
    current = env.reset()
    keys = {"w": "up", "a": "left", "s": "down", "d": "right", "x": "idle"}
    try:
        while not current.done:
            print("\n" + current.observation.grid)
            print("Rules:", "; ".join(current.observation.active_rules))
            raw = input("W/A/S/D move, X wait, Q quit > ").lower().strip()
            if raw == "q":
                break
            current = env.step(keys.get(raw, "idle"))
            print(current.observation.last_result, "reward=", current.reward)
    finally:
        env.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="env/goto_win")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=45)
    parser.add_argument("--budget", type=float, default=3.0)
    parser.add_argument("--model", default=os.getenv("OPENROUTER_MODEL"))
    parser.add_argument("--team", default=None)
    parser.add_argument("--scoreboard")
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()

    if args.manual:
        manual(args.task, args.seed, args.max_steps)
        return

    agent = importlib.import_module("team_agent")
    team = args.team or getattr(agent, "TEAM_NAME", os.getenv("TEAM_NAME", "Team Transformer"))
    llm = OpenRouterLLM(model=args.model, budget_usd=args.budget)
    result = run_episode(
        agent=agent,
        llm=llm,
        team=team,
        task=args.task,
        seed=args.seed,
        max_steps=args.max_steps,
        output_root=Path("runs"),
        scoreboard_url=args.scoreboard,
    )
    print("\nResult:", result.to_dict())


if __name__ == "__main__":
    main()
