from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ACTIONS = ("idle", "up", "right", "down", "left")


@dataclass(frozen=True)
class Observation:
    grid: str
    active_rules: tuple[str, ...]
    step: int
    max_steps: int
    last_action: str | None = None
    last_result: str = ""

    @property
    def steps_remaining(self) -> int:
        return max(0, self.max_steps - self.step)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Transition:
    step: int
    action: str
    reward: float
    done: bool
    state_changed: bool
    state_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

