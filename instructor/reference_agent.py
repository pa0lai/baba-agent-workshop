"""Instructor reference agent with persistent planning and execution memory."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from instructor.symbolic_planner import find_plan
from workshop.types import ACTIONS, Observation, Transition


TEAM_NAME = "Instructor Reference"


@dataclass
class ControllerState:
    plan: str = ""
    plan_step: int = -1
    prior_actions: list[str] = field(default_factory=list)
    symbolic_actions: list[str] = field(default_factory=list)


controller = ControllerState()


def parse_action(text: str) -> str:
    explicit = re.findall(r"ACTION\s*:\s*(idle|up|right|down|left)", text, re.I)
    return explicit[-1].lower() if explicit else "idle"


def recent_history(history: list[Transition], limit: int = 12) -> str:
    items = history[-limit:]
    return "\n".join(
        f"step {item.step}: {item.action}, changed={item.state_changed}, reward={item.reward}"
        for item in items
    ) or "(none)"


def needs_plan(observation: Observation, history: list[Transition]) -> bool:
    if not controller.plan:
        return True
    if "REPLAN REQUIRED" in observation.last_result:
        return True
    if observation.step - controller.plan_step >= 8:
        return True
    if len(history) >= 2 and not history[-1].state_changed and not history[-2].state_changed:
        return True
    return False


def build_planner_prompt(observation: Observation, history: list[Transition]) -> str:
    return f"""
You are the strategic planner for a Baba Is You puzzle agent. Build a concrete,
coordinate-aware plan from the CURRENT state, not from assumptions about the
original map.

Mechanics:
- Rows increase downward and columns increase rightward.
- Baba moves one cell per action. Text Rule[...] blocks are always pushable.
- To push text up, stand below it; to push left, stand to its right, etc.
- Active SUBJECT IS PROPERTY rules update immediately when text moves.
- Objects without STOP can be crossed or overlapped.
- Preserve the only active ... IS YOU rule.
- A level is won by overlapping a YOU object with an object whose active rule
  is WIN.
- Some levels require creating BALL IS WIN. Others require breaking WALL IS
  STOP before crossing the wall column.

Current grid:
{observation.grid}

Active rules:
{chr(10).join('- ' + rule for rule in observation.active_rules)}

Recent outcomes:
{recent_history(history)}

Previous plan, if any:
{controller.plan or '(none)'}

Describe the exact rule-changing subgoal, target text block, required pushing
side, and a short movement sequence. Check map boundaries and avoid oscillation.
End with a concise numbered plan for the executor. Do not output only one move.
""".strip()


def build_executor_prompt(observation: Observation, history: list[Transition]) -> str:
    return f"""
You execute one safe move in Baba Is You. Re-check the CURRENT grid before
following the strategic plan; the plan may be stale after a push.

Strategic plan:
{controller.plan}

Current grid:
{observation.grid}

Active rules:
{chr(10).join('- ' + rule for rule in observation.active_rules)}

Last feedback: {observation.last_result or '(none)'}
Recent outcomes:
{recent_history(history)}

Choose the single move that makes progress toward the next plan subgoal. Do not
repeat an action that just failed to change the state. Preserve ... IS YOU.
Legal actions: {', '.join(ACTIONS)}
Return one final line exactly: ACTION: <legal action>
""".strip()


def build_router_prompt(observation: Observation, actions: list[str]) -> str:
    return f"""
You route a Baba Is You task to the safest available agent component.

Available components:
- SYMBOLIC_SEARCH: exact local state search with dynamic rule simulation. It
  produced a {len(actions)}-step legal plan and independently verified that the
  terminal state overlaps YOU with WIN.
- LANGUAGE_PLANNER: flexible but unverified step-by-step language reasoning.

Current grid:
{observation.grid}

Active rules:
{chr(10).join('- ' + rule for rule in observation.active_rules)}

Symbolic candidate actions:
{', '.join(actions)}

Choose the component that should control low-level actions. Prefer verified
search for a bounded deterministic grid. Return exactly one line:
COMPONENT: SYMBOLIC_SEARCH
or
COMPONENT: LANGUAGE_PLANNER
""".strip()


def act(observation: Observation, history: list[Transition], llm) -> str:
    global controller
    if observation.step == 0:
        controller = ControllerState()
        symbolic_plan = find_plan(observation)
        if symbolic_plan:
            route = llm.complete(
                build_router_prompt(observation, symbolic_plan), max_tokens=120
            )
            if re.search(r"COMPONENT\s*:\s*SYMBOLIC_SEARCH", route, re.I):
                controller.symbolic_actions = symbolic_plan

    if controller.symbolic_actions:
        action = controller.symbolic_actions.pop(0)
        controller.prior_actions.append(action)
        return action

    if needs_plan(observation, history):
        controller.plan = llm.complete(
            build_planner_prompt(observation, history), max_tokens=900
        )
        controller.plan_step = observation.step

    response = llm.complete(build_executor_prompt(observation, history), max_tokens=300)
    action = parse_action(response)
    controller.prior_actions.append(action)
    return action
