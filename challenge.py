from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from workshop.openrouter import OpenRouterLLM
from workshop.report import write_report
from workshop.runner import run_episode
from workshop.runner import EpisodeResult
from workshop.tasks import CHALLENGE_LEVELS, CORE_LEVELS, LEVEL_BY_NAME


load_dotenv()


def progress_bar(cleared: int, total: int, width: int = 20) -> str:
    filled = round(width * cleared / total)
    return "█" * filled + "░" * (width - filled)


def _agent_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_ledger(path: Path) -> float:
    if not path.exists():
        return 0.0
    return float(json.loads(path.read_text(encoding="utf-8")).get("spent_usd", 0.0))


def _write_ledger(path: Path, spent: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps({"spent_usd": spent, "updated_at": time.time()}, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def _resume_payload(path: Path) -> tuple[Path, dict]:
    output_dir = path if path.is_dir() else path.parent
    json_path = output_dir / "challenge.json" if path.is_dir() else path
    return output_dir, json.loads(json_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Baba Agent Challenge.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--level", choices=tuple(LEVEL_BY_NAME))
    mode.add_argument("--core", action="store_true", help="Run the eight core levels.")
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--resume", type=Path, help="Resume a challenge directory or JSON file.")
    parser.add_argument("--agent", default="team_agent", help="Python module containing act().")
    parser.add_argument("--budget", type=float, default=10.0, help="Cross-run USD cap.")
    parser.add_argument("--budget-ledger", type=Path, default=Path("runs/challenge-budget.json"))
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL"))
    parser.add_argument("--team", default=None)
    parser.add_argument("--time-limit", type=float, default=1800, help="Whole-run seconds.")
    parser.add_argument("--level-time-limit", type=float, default=360, help="Per-level seconds.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    agent = importlib.import_module(args.agent)
    agent_path = Path(agent.__file__).resolve()
    team = args.team or getattr(agent, "TEAM_NAME", "Local Agent")
    results_by_task: dict[str, EpisodeResult] = {}

    if args.resume:
        output_dir, prior = _resume_payload(args.resume)
        if prior.get("agent_sha256") != _agent_hash(agent_path):
            parser.error("Agent file changed since this run; start a new run for a valid hash.")
        selected_tasks = prior.get("selected_tasks") or [
            episode["task"] for episode in prior.get("episodes", [])
        ]
        levels = [item for item in CHALLENGE_LEVELS if item["task"] in selected_tasks]
        for episode in prior.get("episodes", []):
            episode.setdefault("duration_seconds", 0.0)
            results_by_task[episode["task"]] = EpisodeResult(**episode)
        model = args.model or prior.get("model")
    else:
        levels = (
            CHALLENGE_LEVELS
            if args.all
            else CORE_LEVELS
            if args.core
            else [LEVEL_BY_NAME[args.level]]
        )
        model = args.model
        stamp = time.strftime("%Y%m%d-%H%M%S")
        output_dir = Path("runs") / f"challenge-{stamp}"

    spent_before = _load_ledger(args.budget_ledger)
    remaining_budget = args.budget - spent_before
    if remaining_budget <= 0:
        parser.error(
            f"Cross-run budget exhausted (${spent_before:.4f}/${args.budget:.2f}). "
            "Use a fresh instructor-approved ledger or raise the provider-side cap."
        )
    llm = OpenRouterLLM(
        model=model,
        budget_usd=remaining_budget,
        usage_callback=lambda usage: _write_ledger(
            args.budget_ledger, spent_before + usage.cost_usd
        ),
    )
    suite_deadline = time.monotonic() + args.time_limit
    interrupted = False
    report_kwargs = {
        "output_dir": output_dir,
        "agent_path": agent_path,
        "model": llm.model,
        "selected_tasks": [level["task"] for level in levels],
        "budget_limit_usd": args.budget,
    }
    write_report(
        results=list(results_by_task.values()),
        budget_spent_usd=spent_before,
        **report_kwargs,
    )

    try:
        for item in levels:
            previous = results_by_task.get(item["task"])
            if previous is not None and previous.success:
                continue
            if time.monotonic() >= suite_deadline:
                break
            episode_deadline = min(
                suite_deadline, time.monotonic() + args.level_time_limit
            )
            llm.set_deadline(episode_deadline)
            result = run_episode(
                agent=agent,
                llm=llm,
                team=team,
                task=item["task"],
                seed=item["seed"],
                max_steps=item["max_steps"],
                output_root=output_dir / "episodes",
                verbose=not args.quiet,
                deadline_monotonic=episode_deadline,
            )
            results_by_task[item["task"]] = result
            _write_ledger(args.budget_ledger, spent_before + llm.usage.cost_usd)
            write_report(
                results=list(results_by_task.values()),
                budget_spent_usd=spent_before + llm.usage.cost_usd,
                **report_kwargs,
            )
            if result.stopped_reason in {"infrastructure_error", "time_limit", "budget_exceeded"}:
                break
    except KeyboardInterrupt:
        interrupted = True
    finally:
        _write_ledger(args.budget_ledger, spent_before + llm.usage.cost_usd)

    results = list(results_by_task.values())
    cleared = sum(result.success for result in results)
    report_path = write_report(
        results=results,
        budget_spent_usd=spent_before + llm.usage.cost_usd,
        **report_kwargs,
    )
    selected_set = {item["task"] for item in levels}
    core_tasks = {item["task"] for item in CORE_LEVELS} & selected_set
    core_cleared = sum(
        result.success for result in results if result.task in core_tasks
    )
    print(f"\n{cleared} / {len(levels)} CLEARED ({core_cleared} / {len(core_tasks)} CORE)")
    print(progress_bar(cleared, len(levels)))
    print(f"Report: {report_path.resolve()}")
    if interrupted:
        print(f"Interrupted safely. Resume with: python challenge.py --resume {output_dir}")


if __name__ == "__main__":
    main()
