from __future__ import annotations

import argparse
import importlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from workshop.openai_client import OpenAILLM
from workshop.runner import run_episode
from workshop.tasks import SUITES
from workshop.telemetry import post_update


load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=tuple(SUITES), default="public")
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL"))
    parser.add_argument("--team", default=None)
    parser.add_argument("--scoreboard")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    suite = SUITES[args.suite]
    default_budgets = {"public": 3.0, "final": 9.0, "all": 10.0}
    budget = args.budget if args.budget is not None else default_budgets[args.suite]
    agent = importlib.import_module("team_agent")
    team = args.team or getattr(agent, "TEAM_NAME", os.getenv("TEAM_NAME", "Team Transformer"))
    llm = OpenAILLM(model=args.model, budget_usd=budget)
    results = []
    for item in suite:
        results.append(
            run_episode(
                agent=agent,
                llm=llm,
                team=team,
                task=item["task"],
                seed=item["seed"],
                max_steps=item["max_steps"],
                output_root=Path("runs"),
                scoreboard_url=args.scoreboard,
                verbose=not args.quiet,
            )
        )

    solved = sum(result.success for result in results)
    steps = sum(result.steps for result in results)
    repeats = sum(result.repeated_states for result in results)
    invalid = sum(result.invalid_actions for result in results)
    score = solved * 1000 - steps - repeats * 3 - invalid * 5
    summary = {
        "team": team,
        "suite": args.suite,
        "solved": solved,
        "total": len(results),
        "steps": steps,
        "repeated_states": repeats,
        "invalid_actions": invalid,
        "cost_usd": llm.usage.cost_usd,
        "score": score,
        "episodes": [result.to_dict() for result in results],
    }
    post_update(
        args.scoreboard,
        {
            **{key: value for key, value in summary.items() if key != "episodes"},
            "task": f"{args.suite} suite complete",
            "success": solved == len(results),
            "status": "finished",
        },
    )
    path = Path("runs") / f"summary-{args.suite}-{team}-{int(time.time())}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
