from __future__ import annotations

import argparse
import threading
import time

from flask import Flask, jsonify, request


app = Flask(__name__)
state: dict[str, dict] = {}
lock = threading.Lock()


PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Baba Agent Tournament</title>
<style>
:root{color-scheme:dark;--bg:#090d18;--card:#111827;--line:#273449;--accent:#7dd3fc;--win:#86efac}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 20% 0,#172554,var(--bg) 38%);font:16px system-ui;color:#e5e7eb}
header{display:flex;justify-content:space-between;align-items:end;padding:28px 34px 18px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:34px;letter-spacing:-1px}.sub{color:#94a3b8}.clock{font:700 28px ui-monospace;color:var(--accent)}
#grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px;padding:22px 28px}
.team{background:rgba(17,24,39,.92);border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:0 18px 50px #0005}
.team.win{border-color:#22c55e;box-shadow:0 0 32px #16a34a33}.frame{width:100%;aspect-ratio:1.45;object-fit:contain;background:#05070d;display:block}
.body{padding:14px 16px}.top{display:flex;justify-content:space-between;gap:12px;align-items:center}.name{font-size:22px;font-weight:800}.badge{padding:5px 10px;border-radius:999px;background:#1e293b;font-weight:700}.win .badge{background:#14532d;color:var(--win)}
.task{color:#93c5fd;margin:8px 0 12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}.stat{background:#0b1220;padding:9px;border-radius:10px}.label{font-size:11px;text-transform:uppercase;color:#64748b}.value{font:700 18px ui-monospace;margin-top:3px}.bar{height:7px;background:#1e293b;border-radius:99px;margin-top:13px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,#38bdf8,#a78bfa)}
.empty{grid-column:1/-1;text-align:center;padding:120px;color:#94a3b8;font-size:24px}
</style></head>
<body><header><div><h1>Baba Agent Tournament</h1><div class="sub">Live text-agent trajectories · Baba Is AI</div></div><div class="clock" id="clock"></div></header><main id="grid"><div class="empty">Waiting for teams…</div></main>
<script>
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function refresh(){
 const data=await fetch('/api/state').then(r=>r.json()); const teams=Object.values(data).sort((a,b)=>(b.solved||0)-(a.solved||0)||(b.score||0)-(a.score||0)||(b.success-a.success)||(b.reward-a.reward)||(a.step-b.step));
 document.querySelector('#grid').innerHTML=teams.length?teams.map(t=>{const pct=Math.min(100,100*(t.step||0)/(t.max_steps||1));const complete=Number.isFinite(t.solved);return `<article class="team ${t.success?'win':''}">${t.frame?`<img class="frame" src="data:image/jpeg;base64,${t.frame}">`:'<div class="frame"></div>'}<div class="body"><div class="top"><div class="name">${esc(t.team)}</div><div class="badge">${complete?`${t.solved}/${t.total}`:(t.success?'SOLVED':esc(t.status||'RUNNING'))}</div></div><div class="task">${esc(t.task)}${t.seed===undefined?'':` · seed ${esc(t.seed)}`}</div><div class="stats"><div class="stat"><div class="label">Step</div><div class="value">${t.step||t.steps||0}/${t.max_steps||'–'}</div></div><div class="stat"><div class="label">Reward</div><div class="value">${Number(t.reward||0).toFixed(1)}</div></div><div class="stat"><div class="label">Cost</div><div class="value">$${Number(t.cost_usd||0).toFixed(3)}</div></div><div class="stat"><div class="label">Score</div><div class="value">${t.score??'–'}</div></div></div><div class="bar"><div class="fill" style="width:${pct}%"></div></div></div></article>`}).join(''):'<div class="empty">Waiting for teams…</div>';
}
setInterval(refresh,1000);setInterval(()=>document.querySelector('#clock').textContent=new Date().toLocaleTimeString(),1000);refresh();
</script></body></html>
"""


@app.get("/")
def index():
    return PAGE


@app.get("/api/state")
def get_state():
    with lock:
        return jsonify(state)


@app.post("/api/update")
def update():
    payload = request.get_json(force=True)
    team = str(payload.get("team", "Unknown"))[:80]
    payload["updated_at"] = time.time()
    with lock:
        previous = state.get(team, {})
        state[team] = {**previous, **payload}
    return {"ok": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
