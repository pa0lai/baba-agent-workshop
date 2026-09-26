# Baba Agent Workshop

A classroom-ready coding challenge built on the open-source
[Baba Is AI](https://github.com/nacloos/baba-is-ai) benchmark.

Students receive a text description of a Baba-style puzzle and write the
component between **observation** and **action**. The projector can still show
the original 2D game, while the model only receives text.

## What students edit

Only [`team_agent.py`](team_agent.py) is required. The starter agent already
runs; teams can improve any of these components:

- `select_memory()` — which previous steps to keep
- `build_prompt()` — how the world and history are presented to the model
- `parse_action()` — how model output becomes a legal action
- `act()` — the orchestration policy

Legal actions are `idle`, `up`, `right`, `down`, and `left`.

## Quick start

Python 3.10 or 3.11 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Put the team's OpenRouter key in `.env`:

```text
OPENROUTER_API_KEY=...
TEAM_NAME=Attention
```

First play a level manually:

```bash
python practice.py --manual --task env/goto_win
```

Then run the starter agent:

```bash
python practice.py --task env/goto_win --seed 0
```

Run all public levels:

```bash
python evaluate.py --suite public
```

During the final, the instructor announces the suite and scoreboard URL:

```bash
python evaluate.py --suite final --scoreboard http://INSTRUCTOR_IP:8000
```

Trajectories, JSON results, and animated GIFs are written to `runs/`.

## Instructor dashboard

On the instructor computer:

```bash
python instructor/dashboard.py --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` on the projector. Each team runner posts only
telemetry (team name, progress, cost, and the rendered frame); API keys and
prompts are never sent to the dashboard.

## Suggested 30-minute flow

1. 3 min — manual demo and starter-agent failure.
2. 12 min — teams edit `team_agent.py`.
3. 5 min — public suite and trajectory debugging.
4. 5 min — one revision.
5. 5 min — final suite with the live dashboard.

## Budget controls

The runner stops before the configured budget is exceeded. Defaults:

- model: `mistralai/mistral-small-3.2-24b-instruct`
- reasoning: disabled (set `OPENROUTER_REASONING_EFFORT` only for a reasoning model)
- per-run budget: USD 3
- final-suite budget: USD 9
- maximum completion: 220 tokens per action

Change these through command-line flags or `.env`. OpenRouter may return the
actual cost for each request. If it does not, the runner uses the configurable
input/output price estimates from `.env`.

## Important classroom security note

Each team should use its own rate-limited OpenRouter key. Do not run arbitrary
student Python inside the same process that holds a shared instructor API key.
For an adversarial or public competition, execute submissions in isolated
containers behind an API proxy.

## Attribution

This repository depends on, but does not redistribute, Baba Is AI. Baba Is AI
is released under the MIT License and accompanies *Baba Is AI: Break the Rules
to Beat the Benchmark* (Cloos et al., 2024). BALROG's text-observation design
inspired the adapter used here.
