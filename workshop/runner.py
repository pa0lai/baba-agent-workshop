from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, replace
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


@dataclass
class StateActionGuard:
    pair: tuple[str, str] | None = None
    count: int = 0

    def next_count(self, state_hash: str, action: str) -> int:
        return self.count + 1 if self.pair == (state_hash, action) else 1

    def record(self, state_hash: str, action: str) -> int:
        pair = (state_hash, action)
        self.count = self.count + 1 if self.pair == pair else 1
        self.pair = pair
        return self.count


def _usage_snapshot(llm) -> tuple[int, int, int, float]:
    usage = getattr(llm, "usage", None)
    return (
        int(getattr(usage, "calls", 0)),
        int(getattr(usage, "prompt_tokens", 0)),
        int(getattr(usage, "completion_tokens", 0)),
        float(getattr(usage, "cost_usd", 0.0)),
    )


def _usage_delta(
    start: tuple[int, int, int, float], end: tuple[int, int, int, float]
) -> tuple[int, int, int, float]:
    return tuple(max(0, current - initial) for initial, current in zip(start, end))


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
    usage_start = _usage_snapshot(llm)

    env = BabaTextEnv(task=task, seed=seed, max_steps=max_steps)
    history: list[Transition] = []
    frames = []
    state_counts: dict[str, int] = {}
    repeated_states = 0
    invalid_actions = 0
    total_reward = 0.0
    success = False
    stopped_reason = "step_limit"
    state_action_guard = StateActionGuard()

    current = env.reset()
    frames.append(current.frame)
    state_counts[current.state_hash] = 1

    try:
        for step_index in range(max_steps):
            if verbose:
                print(f"\n[{team}] {task} seed={seed} step={step_index}/{max_steps}")
                print(current.observation.grid)
                print("Rules:", "; ".join(current.observation.active_rules))

            def choose_action(observation):
                nonlocal invalid_actions, stopped_reason
                try:
                    selected = str(agent.act(observation, history, llm)).lower().strip()
                except BudgetExceeded:
                    stopped_reason = "budget_exceeded"
                    return None
                except Exception as exc:  # keep a workshop run alive after student-code errors
                    selected = "idle"
                    invalid_actions += 1
                    if verbose:
                        print(f"Agent error ({type(exc).__name__}): {exc}; using idle")
                if selected not in {"idle", "up", "right", "down", "left"}:
                    invalid_actions += 1
                    selected = "idle"
                return selected

            action = choose_action(current.observation)
            if action is None:
                break

            replanned = False
            if state_action_guard.next_count(current.state_hash, action) >= 3:
                feedback = (
                    "REPLAN REQUIRED: This state and action have repeated at least three "
                    "times. Choose a different action or strategy to escape the loop."
                )
                replan_observation = replace(
                    current.observation,
                    last_result=(current.observation.last_result + "\n" + feedback).strip(),
                )
                replanned_action = choose_action(replan_observation)
                if replanned_action is None:
                    break
                action = replanned_action
                replanned = True
                if verbose:
                    print("Loop guard: repeated state+action; requested a new plan.")

            previous_hash = current.state_hash
            state_action_streak = state_action_guard.record(previous_hash, action)
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
                "loop_guard": {
                    "pre_state_hash": previous_hash,
                    "state_action_streak": state_action_streak,
                    "replanned": replanned,
                },
            }
            with trajectory_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

            episode_cost = _usage_delta(usage_start, _usage_snapshot(llm))[3]
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
                    "cost_usd": episode_cost,
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
            if state_action_streak >= 6:
                stopped_reason = "state_action_repeat_limit"
                if verbose:
                    print("Loop guard: stopping after six repeated state+action attempts.")
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

    llm_calls, prompt_tokens, completion_tokens, cost_usd = _usage_delta(
        usage_start, _usage_snapshot(llm)
    )
    result = EpisodeResult(
        team=team,
        task=task,
        seed=seed,
        success=success,
        reward=total_reward,
        steps=len(history),
        repeated_states=repeated_states,
        invalid_actions=invalid_actions,
        llm_calls=llm_calls,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
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
