from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .baba_env import BabaTextEnv
from .openrouter import BudgetExceeded
from .telemetry import post_update
from .types import Transition


@dataclass
class EpisodeResult:
    team: str
    task: str
    seed: int
    success: bool
    reward: float
    steps: int
    repeated_states: int
    invalid_actions: int
    llm_calls: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    stopped_reason: str
    run_dir: str

    def to_dict(self) -> dict:
        return asdict(self)


def run_episode(
    *,
    agent,
    llm,
    team: str,
    task: str,
    seed: int,
    max_steps: int,
    output_root: Path,
    scoreboard_url: str | None = None,
    verbose: bool = True,
) -> EpisodeResult:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe_task = task.replace("env/", "").replace("/", "_").replace("#", "_")
    run_dir = output_root / f"{stamp}-{team}-{safe_task}-s{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    trajectory_path = run_dir / "trajectory.jsonl"

    env = BabaTextEnv(task=task, seed=seed, max_steps=max_steps)
    history: list[Transition] = []
    frames = []
    state_counts: dict[str, int] = {}
    repeated_states = 0
    invalid_actions = 0
    total_reward = 0.0
    success = False
    stopped_reason = "step_limit"

    current = env.reset()
    frames.append(current.frame)
    state_counts[current.state_hash] = 1

    try:
        for step_index in range(max_steps):
            if verbose:
                print(f"\n[{team}] {task} seed={seed} step={step_index}/{max_steps}")
                print(current.observation.grid)
                print("Rules:", "; ".join(current.observation.active_rules))

            try:
                action = str(agent.act(current.observation, history, llm)).lower().strip()
            except BudgetExceeded:
                stopped_reason = "budget_exceeded"
                break
            except Exception as exc:  # keep a workshop run alive after student-code errors
                action = "idle"
                invalid_actions += 1
                if verbose:
                    print(f"Agent error ({type(exc).__name__}): {exc}; using idle")

            if action not in {"idle", "up", "right", "down", "left"}:
                invalid_actions += 1
                action = "idle"

            previous_hash = current.state_hash
            current = env.step(action)
            frames.append(current.frame)
            changed = previous_hash != current.state_hash
            state_counts[current.state_hash] = state_counts.get(current.state_hash, 0) + 1
            if state_counts[current.state_hash] > 1:
                repeated_states += 1
            transition = Transition(
                step=step_index,
                action=action,
                reward=current.reward,
                done=current.done,
                state_changed=changed,
                state_hash=current.state_hash,
            )
            history.append(transition)
            total_reward += current.reward

            event = {
                "observation": current.observation.to_dict(),
                "transition": transition.to_dict(),
            }
            with trajectory_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

            usage = getattr(llm, "usage", None)
            post_update(
                scoreboard_url,
                {
                    "team": team,
                    "task": task,
                    "seed": seed,
                    "step": step_index + 1,
                    "max_steps": max_steps,
                    "success": bool(current.done and current.reward > 0),
                    "reward": total_reward,
                    "cost_usd": float(getattr(usage, "cost_usd", 0.0)),
                    "status": "running" if not current.done else "finished",
                },
                current.frame,
            )

            if verbose:
                print("Action:", action, "Reward:", current.reward)
            if current.done:
                success = current.reward > 0
                stopped_reason = "success" if success else "environment_done"
                break
    finally:
        env.close()

    if frames:
        frames[0].save(
            run_dir / "replay.gif",
            save_all=True,
            append_images=frames[1:],
            duration=220,
            loop=0,
        )

    usage = getattr(llm, "usage", None)
    result = EpisodeResult(
        team=team,
        task=task,
        seed=seed,
        success=success,
        reward=total_reward,
        steps=len(history),
        repeated_states=repeated_states,
        invalid_actions=invalid_actions,
        llm_calls=int(getattr(usage, "calls", 0)),
        prompt_tokens=int(getattr(usage, "prompt_tokens", 0)),
        completion_tokens=int(getattr(usage, "completion_tokens", 0)),
        cost_usd=float(getattr(usage, "cost_usd", 0.0)),
        stopped_reason=stopped_reason,
        run_dir=str(run_dir),
    )
    (run_dir / "result.json").write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    post_update(
        scoreboard_url,
        {**result.to_dict(), "status": "finished"},
        frames[-1] if frames else None,
    )
    return result

