# Instructor Guide

## Before the workshop

1. Test one student-like Windows laptop and one macOS laptop with Python 3.10
   or 3.11.
2. Run `python -m pytest -q` and `python -m scripts.smoke_run`. Missing `baba`
   is a hard test failure, not a skip.
3. Run the frozen reference check and inspect its JSON, HTML, and all replays.
4. Pilot the starter and a plausible student improvement on the assigned model.
5. Give every team its own OpenAI API key; prefer a separate project per team and set provider-side limits.

No dashboard, instructor IP, inbound connection, or upload step is required.

## Activity goal

The primary goal is eight core levels: Bronze 4/8, Silver 6/8, and Gold 8/8.
The two compositional levels are bonuses so they do not block a 30-minute class:

- `two_room-make_you-make_win`
- `two_room-make_wall_win`

Teams choose levels freely. Use `python challenge.py --core` for the classroom
checkpoint and `python challenge.py --all` for all ten.

## Operational safeguards

- Default limits are 30 minutes per invocation and 6 minutes per level.
- Timeout, connection, 429, and OpenAI API 5xx failures are infrastructure
  outcomes and do not increment invalid student actions.
- `--resume` retains cleared episodes after interruption.
- `runs/challenge-budget.json` carries reported cost across invocations. It is
  a convenience guard; the OpenAI usage dashboard is authoritative for billing.
- The report records the final agent hash. Resume rejects a changed agent so
  one report cannot silently mix different implementations.

## Instructor reference agent

`instructor/reference_agent.py` is a hybrid reference implementation, not raw
GPT-4.1-mini puzzle-solving. GPT routes each level to a local symbolic-search
component that parses the text grid, simulates pushes and dynamic rules, and
searches low-level actions.

```bash
python challenge.py --all --agent instructor.reference_agent \
  --budget-ledger runs/reference-budget.json --quiet
```

See `REFERENCE_RESULTS.md` for the maintained evidence record. Do not call the
workshop camera-ready until the current ten-level command succeeds end to end
within the limits on a clean installation.

## Optional legacy tools

`evaluate.py` and the dashboard remain for backwards compatibility. If the
unauthenticated dashboard is demonstrated, keep it on a trusted LAN. Never run
student code with a shared instructor key.
