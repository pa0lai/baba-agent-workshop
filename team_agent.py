"""Student workspace: improve this file and leave the engine untouched."""

from __future__ import annotations

import os
import re

from workshop.types import ACTIONS, Observation, Transition


TEAM_NAME = os.getenv("TEAM_NAME", "Team Transformer")


def select_memory(history: list[Transition], limit: int = 6) -> list[Transition]:
    """Choose the past transitions that the model should see.

    Starter policy: only keep the latest transitions. Teams can replace this
    with retrieval, summaries, loop detection, or an explicit world model.
    """

    return history[-limit:]


def build_prompt(observation: Observation, memory: list[Transition]) -> str:
    """Turn the current state and selected memory into a model prompt."""

    recent = "\n".join(
        f"step {item.step}: action={item.action}; reward={item.reward}; "
        f"state_changed={item.state_changed}; rules={', '.join(item.active_rules) or '(unknown)'}; "
        f"result={item.last_result or '(unknown)'}"
        for item in memory
    ) or "(no previous actions)"

    return f"""
You control a character in Baba Is AI, a rule-manipulation puzzle.

Goal: reach an object whose active property is WIN. Text blocks can be pushed
to create or break rules of the form SUBJECT IS PROPERTY. Never break the only
rule that gives a controllable object the YOU property.

Current grid (row 0 is the top; column 0 is the left):
{observation.grid}

Active rules:
{chr(10).join('- ' + rule for rule in observation.active_rules)}

Recent history:
{recent}

Last action feedback:
{observation.last_result or "(none)"}

Steps remaining: {observation.steps_remaining}
Legal actions: {', '.join(ACTIONS)}

Think briefly about what rule must hold and which text block may need to move.
Return one final line exactly as ACTION: <legal action>.
""".strip()


def parse_action(model_output: str) -> str:
    """Extract one legal action from the model response."""

    text = model_output.lower()
    explicit = re.findall(r"action\s*:\s*(idle|up|right|down|left)", text)
    if explicit:
        return explicit[-1]

    words = re.findall(r"\b(idle|up|right|down|left)\b", text)
    return words[-1] if words else "idle"


def act(observation: Observation, history: list[Transition], llm) -> str:
    """Main component called once per environment step."""

    memory = select_memory(history)
    prompt = build_prompt(observation, memory)
    response = llm.complete(prompt, max_tokens=220)
    return parse_action(response)
