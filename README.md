# Baba Agent Workshop

A local classroom challenge built on the open-source
[Baba Is AI](https://github.com/nacloos/baba-is-ai) benchmark. Students improve
the component between a text observation and a legal game action; no instructor
server, LAN scoreboard, upload, or locked level order is required.

## What students edit

Only [`team_agent.py`](team_agent.py) is required. Teams can improve memory,
prompting, parsing, planning, verification, retrieval, or deterministic search.
Legal actions are `idle`, `up`, `right`, `down`, and `left`.

## Quick start

Python 3.10 or 3.11 is recommended. The pinned Baba source is downloaded as a
ZIP, so student computers do not need Git for installation.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Put a team-specific, provider-limited OpenRouter key in `.env`:

```text
OPENROUTER_API_KEY=...
TEAM_NAME=Attention
```

Then try the game and agent:

```bash
python practice.py --manual --task env/goto_win
python challenge.py --level make_win
python challenge.py --core
```

Use `python challenge.py --all` to add the two bonus levels. An interrupted or
infrastructure-failed run can continue without repeating cleared levels:

```bash
python challenge.py --resume runs/challenge-YYYYMMDD-HHMMSS
```

Every run produces JSON results, replay GIFs, and a local `report.html` with
status, steps, per-level cost, runtime, and the submitted agent's SHA-256 hash.

## Challenge structure

| Core level | Skill |
| --- | --- |
| `goto_win` | Basic navigation |
| `goto_win-distr_obj_rule` | Ignore distractions |
| `two_room-goto_win` | Plan across rooms |
| `two_room-goto_win-distr_win_rule` | Cross rooms with a false rule |
| `make_win` | Create a WIN rule |
| `make_win-distr_rule` | Create WIN with distractions |
| `two_room-break_stop-goto_win` | Break a STOP rule |
| `two_room-break_stop-make_win` | Combined rule puzzle |

Bonus levels are `two_room-make_you-make_win` and
`two_room-make_wall_win`. Bronze is 4/8 core, Silver 6/8, Gold 8/8, and the
bonus levels extend the goal without blocking the 30-minute activity.

## Safety limits

The default whole-run limit is 30 minutes and the per-level limit is 6 minutes.
OpenRouter timeouts, 429s, and 5xx responses are retried and reported as
infrastructure errors, not invalid student actions. Episode cost is a per-level
delta. A local ledger enforces the configured budget across challenge process
restarts; an OpenRouter credit limit remains the authoritative hard cap.

If the same state and action recur three times, the runner requests replanning;
six consecutive repetitions stop that episode. History entries include the
observed grid, active rules, and action result so teams can build real memory.

## Suggested 30-minute flow

1. 3 min — manual demo and starter-agent failure.
2. 5 min — teams run a baseline and inspect replays.
3. 15 min — improve `team_agent.py`.
4. 5 min — run `python challenge.py --core`.
5. 2 min — teams explain which component helped.

`evaluate.py` and the unauthenticated dashboard remain optional legacy tools.
Do not run arbitrary student code with a shared instructor API key.

## Attribution

Baba Is AI is MIT-licensed and accompanies *Baba Is AI: Break the Rules to
Beat the Benchmark* (Cloos et al., 2024). BALROG's text-observation design
inspired the adapter used here.
