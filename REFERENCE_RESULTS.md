# Instructor Reference Verification

The instructor reference is a hybrid agent: GPT-4.1 Mini performs component
routing, while a generic symbolic search component parses the current text
grid, simulates PUSH and dynamic `IS` rules, and produces verified actions. It
does not contain a table of level-specific action sequences.

## Current ten-level status

> Routing note: these measurements were recorded through OpenRouter with the
> provider-qualified model ID `openai/gpt-4.1-mini`. The workshop now calls
> OpenAI directly with model ID `gpt-4.1-mini`; rerun the ten-level check before
> treating this table as evidence for the new route.

Verified end to end on 2026-09-28 at commit `dd2658c`, using
`openai/gpt-4.1-mini` and the ten frozen challenge seeds:

| Level | Result | Steps | LLM calls | Cost |
| --- | --- | ---: | ---: | ---: |
| `goto_win` | cleared | 7 | 1 | $0.0001220 |
| `goto_win-distr_obj_rule` | cleared | 5 | 1 | $0.0001228 |
| `two_room-goto_win` | cleared | 4 | 1 | $0.0001756 |
| `two_room-goto_win-distr_win_rule` | cleared | 4 | 1 | $0.0001836 |
| `make_win` | cleared | 17 | 1 | $0.0001280 |
| `make_win-distr_rule` | cleared | 12 | 1 | $0.0001248 |
| `two_room-break_stop-goto_win` | cleared | 11 | 1 | $0.0001840 |
| `two_room-break_stop-make_win` | cleared | 19 | 1 | $0.0001884 |
| `two_room-make_you-make_win` | cleared | 20 | 1 | $0.0001916 |
| `two_room-make_wall_win` | cleared | 14 | 1 | $0.0001868 |

Summary:

- 10/10 cleared: 8/8 core and 2/2 bonus
- Master Rule Breaker achievement
- 113 environment steps and 10 LLM calls
- USD 0.0016076 reported cost
- 13.991 seconds summed episode runtime; 14.9 seconds observed wall time
- every episode produced a replay GIF
- reference agent SHA-256:
  `48d7a0f91d4d2df51dd11c3fa9ffbef046e41cf782ede5e3007fa1fbcdf59a0e`

Command:

```bash
python challenge.py --all \
  --agent instructor.reference_agent \
  --model openai/gpt-4.1-mini \
  --budget-ledger runs/reference-budget-camera-ready.json \
  --time-limit 360 --level-time-limit 60 --quiet
```

The generated report was
`runs/challenge-20260928-000125/report.html`. The `runs/` directory is
intentionally gitignored; the real-environment ten-level symbolic clearance
check is retained as an automated test.

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
