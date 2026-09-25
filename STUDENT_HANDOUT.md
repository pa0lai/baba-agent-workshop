# Build an Agent That Breaks the Rules

Your team controls a character in **Baba Is AI**. The world is governed by
sentences placed directly on the map:

```text
BABA IS YOU
FLAG IS WIN
WALL IS STOP
ROCK IS PUSH
```

Text blocks can be pushed. Breaking or creating a sentence changes the game
immediately.

## Your mission

Improve [`team_agent.py`](team_agent.py) so the same agent can solve unseen
maps. You may change any function in that file, but not the benchmark engine.

Ideas:

- remember useful past states;
- detect repeated movement;
- keep an explicit plan;
- predict whether a move will break `... IS YOU`;
- ask one LLM to plan and another call to verify;
- write your own deterministic search or rule parser.

## Commands

```bash
python practice.py --manual --task env/goto_win
python practice.py --task env/goto_win --seed 0
pytest -q
python evaluate.py --suite public
```

The instructor will give you the final command and scoreboard URL.

## Rules

- Use the assigned model and team key.
- Do not edit `workshop/` or the evaluator.
- Do not hard-code a public map's action sequence.
- Stay under the USD 10 team budget.
- Your final agent must return exactly one of `idle`, `up`, `right`, `down`, or
  `left` at every step.

