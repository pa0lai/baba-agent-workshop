from __future__ import annotations

import hashlib
import html
import json
import os
from datetime import datetime
from pathlib import Path

from .tasks import CHALLENGE_LEVELS, CORE_LEVELS


RULE_BREAKER_MAX_STEPS = 200


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def achievement(core_cleared: int, total_steps: int, bonus_cleared: int = 0) -> str:
    if core_cleared == 8 and bonus_cleared == 2:
        return "Master Rule Breaker"
    if core_cleared == 8 and total_steps < RULE_BREAKER_MAX_STEPS:
        return "Rule Breaker"
    if core_cleared == 8:
        return "Gold"
    if core_cleared >= 6:
        return "Silver"
    if core_cleared >= 4:
        return "Bronze"
    return "Keep Building"


def write_report(
    *,
    output_dir: Path,
    results: list,
    agent_path: Path,
    model: str,
    selected_tasks: list[str] | None = None,
    budget_spent_usd: float | None = None,
    budget_limit_usd: float | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    by_task = {result.task: result for result in results}
    selected_tasks = selected_tasks or [item["task"] for item in CHALLENGE_LEVELS]
    selected_set = set(selected_tasks)
    cleared = sum(result.success for result in results if result.task in selected_set)
    core_tasks = {item["task"] for item in CORE_LEVELS}
    core_cleared = sum(result.success for result in results if result.task in core_tasks)
    bonus_cleared = sum(
        result.success
        for result in results
        if result.task not in core_tasks and result.task in selected_set
    )
    total_steps = sum(result.steps for result in results)
    total_cost = sum(result.cost_usd for result in results)
    total_duration = sum(result.duration_seconds for result in results)
    agent_hash = file_sha256(agent_path)
    badge = achievement(core_cleared, total_steps, bonus_cleared)

    rows = []
    for item in CHALLENGE_LEVELS:
        result = by_task.get(item["task"])
        if item["task"] not in selected_set:
            status, css = "NOT SELECTED", "pending"
            steps = cost = duration = "—"
            replay = ""
        elif result is None:
            status, css = "NOT RUN", "pending"
            steps = cost = duration = "—"
            replay = ""
        else:
            if result.success:
                status, css = "CLEARED", "cleared"
            elif result.stopped_reason == "infrastructure_error":
                status, css = "INFRA ERROR", "infra"
            elif result.stopped_reason == "time_limit":
                status, css = "TIME LIMIT", "infra"
            else:
                status, css = "FAILED", "failed"
            steps = str(result.steps)
            cost = f"${result.cost_usd:.4f}"
            duration = f"{result.duration_seconds:.1f}s"
            replay_path = Path(result.run_dir) / "replay.gif"
            replay_url = html.escape(os.path.relpath(replay_path, output_dir))
            replay = f'<a href="{replay_url}"><img src="{replay_url}" alt="Replay"></a>'
        rows.append(
            "<tr>"
            f'<td><code>{html.escape(item["level"])}</code><small>{html.escape(item["description"])}</small></td>'
            f'<td><span class="status {css}">{status}</span></td>'
            f"<td>{steps}</td><td>{cost}</td><td>{duration}</td><td>{replay}</td>"
            "</tr>"
        )

    percent = 100 * cleared / max(1, len(selected_tasks))
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "model": model,
        "agent_path": str(agent_path),
        "agent_sha256": agent_hash,
        "cleared": cleared,
        "total": len(selected_tasks),
        "core_cleared": core_cleared,
        "core_total": len(CORE_LEVELS),
        "bonus_cleared": bonus_cleared,
        "selected_tasks": selected_tasks,
        "achievement": badge,
        "steps": total_steps,
        "cost_usd": total_cost,
        "duration_seconds": total_duration,
        "budget_spent_usd": budget_spent_usd,
        "budget_limit_usd": budget_limit_usd,
        "episodes": [result.to_dict() for result in results],
    }
    (output_dir / "challenge.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Baba Agent Challenge Report</title><style>
:root{{--bg:#09101d;--card:#111b2d;--line:#263650;--text:#e8eef8;--muted:#91a4bd;--green:#43d17d;--red:#ff6874;--gold:#ffd166}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:38px 22px}}
h1{{margin:0 0 8px;font-size:38px}}.lead{{color:var(--muted)}}.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:26px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px}}.big{{font-size:28px;font-weight:800}}.label,small{{display:block;color:var(--muted);font-size:12px;margin-top:5px}}
.bar{{height:16px;background:#1e2a40;border-radius:99px;overflow:hidden}}.fill{{height:100%;width:{percent:.2f}%;background:linear-gradient(90deg,#38bdf8,#43d17d)}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:14px;overflow:hidden}}th,td{{padding:13px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}}th{{color:var(--muted);font-size:12px;text-transform:uppercase}}
.status{{font-weight:800}}.cleared{{color:var(--green)}}.failed{{color:var(--red)}}.infra{{color:var(--gold)}}.pending{{color:var(--muted)}}img{{width:120px;max-height:90px;object-fit:contain;background:#05080e;border-radius:8px}}
.hash{{font:12px ui-monospace;word-break:break-all;color:var(--muted)}}.badge{{color:var(--gold)}}
</style></head><body><main>
<h1>{cleared} / {len(selected_tasks)} CLEARED</h1><div class="lead">{core_cleared} / 8 core · {bonus_cleared} / 2 bonus</div>
<div class="summary"><div class="card"><div class="big badge">{html.escape(badge)}</div><div class="label">Achievement</div></div><div class="card"><div class="big">{total_steps}</div><div class="label">Steps</div></div><div class="card"><div class="big">${total_cost:.4f}</div><div class="label">Cost</div></div><div class="card"><div class="big">{total_duration:.1f}s</div><div class="label">Runtime</div></div></div>
<div class="bar"><div class="fill"></div></div><p class="lead">Model: <code>{html.escape(model)}</code></p>
<table><thead><tr><th>Level</th><th>Status</th><th>Steps</th><th>Cost</th><th>Time</th><th>Replay</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<div class="card" style="margin-top:18px"><div class="label">Final agent SHA-256</div><div class="hash">{agent_hash}</div></div>
</main></body></html>"""
    report_path = output_dir / "report.html"
    report_path.write_text(page, encoding="utf-8")
    return report_path
