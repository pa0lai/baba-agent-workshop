from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import baba  # noqa: E402
from baba.world_object import name_mapping  # noqa: E402
from PIL import Image  # noqa: E402

from .types import ACTIONS, Observation


def _clean_rule(rule: dict) -> str | None:
    if "object" not in rule or "property" not in rule:
        return None
    subject = str(rule["object"]).removeprefix("f")
    prop = name_mapping.get(rule["property"], str(rule["property"]))
    return f"{subject} is {prop}"


def _matrix_to_text(matrix) -> str:
    rows = []
    for row_index, row in enumerate(matrix.tolist()):
        cells = [str(cell).replace("Empty", ".") for cell in row]
        rows.append(f"{row_index:02d} | " + " | ".join(cells))
    width = len(matrix[0]) if len(matrix) else 0
    header = "     " + "   ".join(f"c{index:02d}" for index in range(width))
    return header + "\n" + "\n".join(rows)


@dataclass
class StepResult:
    observation: Observation
    reward: float
    done: bool
    info: dict
    frame: Image.Image
    state_hash: str


class BabaTextEnv:
    def __init__(self, task: str, seed: int = 0, max_steps: int = 60):
        self.task = task if task.startswith("env/") else f"env/{task}"
        self.seed = seed
        self.max_steps = max_steps
        self.env = baba.make(self.task, max_steps=max_steps)
        self.step_number = 0
        self.last_action: str | None = None
        self.last_result = ""

    def _state_hash(self) -> str:
        matrix = self.env.render(mode="matrix")
        return hashlib.sha256(repr(matrix.tolist()).encode()).hexdigest()[:16]

    def _observation(self) -> Observation:
        matrix = self.env.render(mode="matrix")
        rules = []
        for raw in self.env.grid._ruleset["_rule_"]:
            cleaned = _clean_rule(raw)
            if cleaned:
                rules.append(cleaned)
        return Observation(
            grid=_matrix_to_text(matrix),
            active_rules=tuple(rules),
            step=self.step_number,
            max_steps=self.max_steps,
            last_action=self.last_action,
            last_result=self.last_result,
        )

    def frame(self) -> Image.Image:
        return Image.fromarray(self.env.render(mode="rgb_array")).convert("RGB")

    def reset(self) -> StepResult:
        self.env.reset(seed=self.seed)
        self.step_number = 0
        self.last_action = None
        self.last_result = "Environment reset."
        return StepResult(
            observation=self._observation(),
            reward=0.0,
            done=False,
            info={},
            frame=self.frame(),
            state_hash=self._state_hash(),
        )

    def step(self, action: str) -> StepResult:
        normalized = action.lower().strip()
        invalid = normalized not in ACTIONS
        if invalid:
            normalized = "idle"
        before = self._state_hash()
        raw_action = getattr(self.env.actions, normalized)
        _, reward, done, info = self.env.step(raw_action)
        self.step_number += 1
        after = self._state_hash()
        self.last_action = normalized
        self.last_result = (
            "Invalid action; treated as idle."
            if invalid
            else ("World changed." if before != after else "World did not change.")
        )
        return StepResult(
            observation=self._observation(),
            reward=float(reward),
            done=bool(done),
            info=dict(info or {}),
            frame=self.frame(),
            state_hash=after,
        )

    def close(self) -> None:
        self.env.close()

