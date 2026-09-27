# Instructor Reference Verification

The instructor reference is a hybrid agent: GPT-4.1 Mini performs component
routing, while a generic symbolic search component parses the current text
grid, simulates PUSH and dynamic `IS` rules, and produces verified actions. It
does not contain a table of level-specific action sequences.

## Current ten-level status

The real-environment automated check currently verifies that symbolic plans
clear all ten frozen seeds, including the two bonus levels (20 and 14 steps).
This is an offline component check, not a completed OpenRouter run.

The required ten-level `openai/gpt-4.1-mini` end-to-end refresh has **not yet
been verified**. The first camera-ready attempt on 2026-09-27 stopped before
making a request because `OPENROUTER_API_KEY` was absent. Do not present the
older eight-level record below as evidence for the new ten-level suite.

## Historical eight-level run

Verified locally on 2026-09-27 with commit parent `ac73bf2`, model
`openai/gpt-4.1-mini`, and the eight frozen challenge seeds:

| Level | Result | Steps | LLM calls |
| --- | --- | ---: | ---: |
| `goto_win` | cleared | 7 | 1 |
| `goto_win-distr_obj_rule` | cleared | 5 | 1 |
| `two_room-goto_win` | cleared | 4 | 1 |
| `two_room-goto_win-distr_win_rule` | cleared | 4 | 1 |
| `make_win` | cleared | 17 | 1 |
| `make_win-distr_rule` | cleared | 12 | 1 |
| `two_room-break_stop-goto_win` | cleared | 11 | 1 |
| `two_room-break_stop-make_win` | cleared | 19 | 1 |

Summary:

- 8/8 cleared
- Rule Breaker achievement
- 79 total environment steps
- 8 total LLM calls
- USD 0.0012292 reported cost
- 11.107 seconds summed episode runtime; 11.60 seconds wall time
- 0 repeated states and 0 invalid actions
- reference agent SHA-256:
  `48d7a0f91d4d2df51dd11c3fa9ffbef046e41cf782ede5e3007fa1fbcdf59a0e`

Historical command:

```bash
python challenge.py --all \
  --agent instructor.reference_agent \
  --model openai/gpt-4.1-mini \
  --quiet
```

The generated report was `runs/challenge-20260927-025232/report.html`. The
`runs/` directory is intentionally gitignored; the real-environment symbolic
clearance check is retained as an automated test instead.
