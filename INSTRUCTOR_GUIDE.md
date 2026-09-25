# Instructor Guide

## Before the workshop

1. Install the repository on one student-like Windows laptop and one macOS
   laptop. Python 3.10/3.11 is the safest choice because the upstream game uses
   legacy Gym.
2. Run `pytest -q` and `python scripts/smoke_run.py`.
3. Pilot the intended model on at least 20 episodes. Aim for 20–40% starter
   success and 60–80% after reasonable improvements.
4. Replace the final task seeds shortly before class if you want to discourage
   hard-coded action sequences.
5. Put every team on the same model, temperature, step limits, and budget.
6. Confirm that student laptops can reach OpenRouter and the instructor's LAN
   address.

## Recommended room setup

- 4–5 students per team.
- One laptop and one team-specific, rate-limited OpenRouter key per team.
- Instructor computer and student computers on the same network.
- Projector browser opened to the dashboard.

Start the dashboard:

```bash
python instructor/dashboard.py --host 0.0.0.0 --port 8000
```

Find the instructor computer's LAN IP and give teams a URL such as
`http://192.168.1.20:8000`.

## Suggested roles

- Driver: edits and runs the code.
- World-model engineer: reads trajectories and tracks rules.
- Prompt engineer: revises the LLM prompt.
- Debugger: detects loops and invalid actions.
- Reporter: explains the final design.

## Difficulty controls

If the starter agent is too strong:

- use `two_room`, `break_stop`, and `make_win` tasks;
- lower the step limit;
- use a smaller fixed model;
- remove some hints from `build_prompt()`;
- score repeated states and calls more heavily.

If the starter agent is too weak:

- begin with `goto_win`;
- keep active rules in the observation;
- raise the step limit;
- provide one successful trajectory;
- allow a stronger model.

## Final score

The provided formula strongly prioritizes solving levels:

```text
score = solved * 1000 - steps - repeated_states * 3 - invalid_actions * 5
```

Change it in `evaluate.py` if you want token efficiency to matter more.

## Operational caveats

- The dashboard is a classroom development server, not an internet-facing
  production service.
- Telemetry is accepted without authentication. Keep it on a trusted LAN.
- Do not give arbitrary student code access to a shared instructor API key.
- The final suite in this repository is classroom-hidden, not cryptographically
  hidden. Replace it or host the manifest separately for a serious contest.

