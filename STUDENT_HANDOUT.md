# Build an Agent That Breaks the Rules

Your team controls a character in **Baba Is AI**. Text blocks form rules such
as `BABA IS YOU`, `FLAG IS WIN`, and `WALL IS STOP`; pushing a word can change
the world immediately.

Improve [`team_agent.py`](team_agent.py). You may change memory, prompting,
parsing, planning, verification, retrieval, or orchestration, but not the game
engine. History entries include earlier grids, active rules, and action results.

## Commands

```bash
python practice.py --manual --task env/goto_win
python challenge.py --level make_win
python challenge.py --core
python challenge.py --all                 # includes two bonus levels
pytest -q
```

If a run is interrupted, use the resume command printed by the runner. Cleared
levels are not repeated. Open the generated `report.html` for red/green status,
steps, cost, runtime, replay GIFs, and your final agent hash.

- Bronze: 4/8 core
- Silver: 6/8 core
- Gold: 8/8 core
- Bonus: solve either or both compositional levels

## Rules

- Use the assigned model and your team's rate-limited key.
- AI coding assistants are allowed, but your team must explain its component.
- Do not edit `workshop/`, the evaluator, or hard-code map action sequences.
- Stay under the assigned provider and local budget.
- Return exactly one of `idle`, `up`, `right`, `down`, or `left` per step.
