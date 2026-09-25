from __future__ import annotations

import argparse
import importlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from workshop.openrouter import OpenRouterLLM
from workshop.runner import run_episode
from workshop.tasks import FINAL_SUITE, PUBLIC_SUITE
from workshop.telemetry import post_update


load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("public", "final"), default="public")
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--model", default=os.getenv("OPENROUTER_MODEL"))
    parser.add_argument("--team", default=os.getenv("TEAM_NAME", "Team Transformer"))
    parser.add_argument("--scoreboard")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    suite = PUBLIC_SUITE if args.suite == "public" else FINAL_SUITE
    budget = args.budget if args.budget is not None else (3.0 if args.suite == "public" else 9.0)
    agent = importlib.import_module("team_agent")
    team = getattr(agent, "TEAM_NAME", args.team)
    llm = OpenRouterLLM(model=args.model, budget_usd=budget)
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
