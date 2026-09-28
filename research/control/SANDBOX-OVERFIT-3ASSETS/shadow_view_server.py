"""PROSPECTIVE-SHADOW-V1 — read-only web view at http://127.0.0.1:8765/

Owner-ordered view (2026-09-20). READ-ONLY: chỉ ĐỌC state của cycle từ
plans/ACTIVE_CYCLES.json (main checkout) và results/prospective_shadow_v1/
(worktree). Không ghi file nào của cycle, không đụng worker pids, không
đụng registry/ledger. Refresh trang = đọc lại file mới nhất.

Chạy: .venv/bin/python shadow_view_server.py  (foreground)
     nohup ... &                             (background)
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path("/Users/hoangminhlong/my-quantitative")
WT = ROOT / ".worktrees/prospective-shadow-v1/integration"
SH = WT / "results/prospective_shadow_v1"
PORT = 8765
FAMILIES = ["XSECT-FUND-CARRY-7D", "BASISLV-PREMFADE-28D", "ILLIQ-AMIHUD-28D-W"]

CSS = """:root{--bg:#0f1216;--card:#171c23;--fg:#e8ecf1;--mut:#8b98a8;
--acc:#4da3ff;--ok:#3ecf8e;--warn:#f5b544;--bad:#ff6b6b;--line:#2a3340}
body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,'SF Pro Text',sans-serif;padding:20px 26px 60px}
h1{font-size:20px;margin:0 0 2px}h2{font-size:15px;margin:22px 0 8px;
border-bottom:1px solid var(--line);padding-bottom:4px}
.sub{color:var(--mut);font-size:12px}
.grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:10px 12px}.k{color:var(--mut);font-size:11px;text-transform:uppercase}
.v{font-size:15px;margin-top:2px;font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin-top:6px}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-size:11px;text-transform:uppercase}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap; text-align:right}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
pre{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:10px;font-size:11.5px;overflow:auto;max-height:340px}
a{color:var(--acc)}"""


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        return {"_error": str(exc)}


def read_jsonl(path: Path) -> list[dict]:
    out = []
    try:
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue  # partial line while worker appends
    except OSError:
        pass
    return out


def money(v) -> str:
    return f"{v:,.2f}" if isinstance(v, (int, float)) else "—"


def equity_svg(marks: list[dict]) -> str:
    xs = [m.get("mark_timestamp_utc", "") for m in marks]
    ys = [m.get("equity") for m in marks]
    pts_all = [(i, y) for i, y in enumerate(ys) if isinstance(y, (int, float))]
    if len(pts_all) < 2:
        return ""
    w, h = 860, 180
    lo = min(y for _, y in pts_all)
    hi = max(y for _, y in pts_all)
    pad = max(hi - lo, 1.0) * 0.08
    lo, hi = lo - pad, hi + pad
    n = len(ys)
    px = lambda i: 30 + i / (n - 1) * (w - 50)
    py = lambda y: (h - 24) - (y - lo) / (hi - lo) * (h - 44)
    pts = " ".join(f"{px(i):.1f},{py(y):.1f}" for i, y in pts_all)
    y0 = py(100000.0)
    return (f'<svg width="{w}" height="{h}" font-family="monospace" font-size="10">'
            f'<line x1="30" y1="{y0:.0f}" x2="{w-20}" y2="{y0:.0f}" stroke="#444" stroke-dasharray="4,3"/>'
            f'<text x="32" y="{y0-3:.0f}" fill="#888">100,000</text>'
            f'<polyline fill="none" stroke="#4da3ff" stroke-width="1.4" points="{pts}"/>'
            f'<text x="{w-20}" y="{py(pts_all[-1][1])-4:.0f}" fill="#4da3ff" text-anchor="end">'
            f'{money(pts_all[-1][1])}</text></svg>')


def build_state() -> dict:
    active = read_json(ROOT / "plans/ACTIVE_CYCLES.json")
    cyc = next((c for c in active.get("cycles", [])
                if c.get("cycle_id") == "PROSPECTIVE-SHADOW-V1"), {})
    hb = read_json(SH / "runtime/heartbeat.json")
    vhb = read_json(SH / "runtime/valuation_heartbeat.json")
    fam = {}
    for f in FAMILIES:
        marks = read_jsonl(SH / f"valuation_marks/{f}.jsonl")
        fam[f] = {"last": marks[-1] if marks else None, "n_marks": len(marks),
                  "marks": marks}
    events = read_jsonl(SH / "ledgers/XSECT-FUND-CARRY-7D.jsonl")
    return {"cycle": cyc, "decision_hb": hb, "valuation_hb": vhb,
            "families": fam, "ledger_events": events}


def render(state: dict) -> str:
    cyc, hb, vhb = state["cycle"], state["decision_hb"], state["valuation_hb"]
    carry = state["families"]["XSECT-FUND-CARRY-7D"]
    last_carry = carry["last"] or {}
    eq = last_carry.get("equity")
    pnl_total = (eq - 100000.0) if isinstance(eq, (int, float)) else None
    rows_pos = ""
    for p in last_carry.get("positions") or []:
        up = p.get("unrealized_pnl")
        cls = "ok" if isinstance(up, (int, float)) and up >= 0 else "bad"
        rows_pos += (f"<tr><td>{p.get('symbol')}</td>"
                     f"<td class='n'>{'LONG' if (p.get('qty') or 0) > 0 else 'SHORT'}</td>"
                     f"<td class='n'>{p.get('qty'):,.2f}</td>"
                     f"<td class='n'>{money(p.get('avg_price'))}</td>"
                     f"<td class='n'>{money(p.get('mark_price'))}</td>"
                     f"<td class='n'>{money(p.get('notional'))}</td>"
                     f"<td class='n {cls}'>{money(up)}</td></tr>")
    rows_events = ""
    for e in reversed(state["ledger_events"][-10:]):
        cls = "ok" if (e.get("total_pnl") or 0) >= 0 else "bad"
        tw = ", ".join(f"{k}:{v:+.2f}" for k, v in sorted((e.get("target_weights") or {}).items()))
        rows_events += (f"<tr><td>{e.get('scheduled_decision_utc','')}</td>"
                        f"<td class='n'>{money(e.get('equity'))}</td>"
                        f"<td class='n {cls}'>{money(e.get('total_pnl'))}</td>"
                        f"<td class='n'>{money(e.get('fee'))}</td>"
                        f"<td class='n'>{money(e.get('funding_cashflow'))}</td>"
                        f"<td>{tw}</td></tr>")
    fam_cards = ""
    for f, d in state["families"].items():
        last = d["last"] or {}
        status = last.get("status", "NO_MARK")
        cls = {"RUNNING": "ok", "FLAT_OK": "warn"}.get(status, "bad")
        fam_cards += (f"<div class='card'><div class='k'>{f}</div>"
                      f"<div class='v'>{money(last.get('equity'))} "
                      f"<span class='{cls}'>{status}</span></div>"
                      f"<div class='sub'>{last.get('mark_timestamp_utc','—')} · "
                      f"{d['n_marks']} marks · gross {last.get('gross', 0):.4f}</div></div>")
    vhb_err = vhb.get("last_error")
    err_html = (f"<p class='bad'>valuation last_error: {vhb_err}</p>" if vhb_err
                else "<p class='ok'>valuation: no error</p>")
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<title>Shadow Monitor — PROSPECTIVE-SHADOW-V1</title><style>{CSS}</style></head><body>
<h1>Shadow Monitor — PROSPECTIVE-SHADOW-V1 <span class="sub">(paper)</span></h1>
<div class="sub">{cyc.get('phase','')[:300]}</div>
<div class="sub">lifecycle {cyc.get('lifecycle')} · đọc-only từ worktree, tự refresh 30s ·
<a href="/state.json">raw state.json</a></div>

<h2>Tổng quan</h2>
<div class="grid">
<div class="card"><div class="k">CARRY equity (paper)</div>
<div class="v">{money(eq)} USD</div>
<div class="sub">P&amp;L từ 100k: <b class="{'ok' if pnl_total and pnl_total>=0 else 'bad'}">{money(pnl_total)}</b></div></div>
<div class="card"><div class="k">Decision worker (pid {hb.get('pid')})</div>
<div class="v">{'đang chạy' if hb.get('pid') else '—'} · {hb.get('loop_count','?')} vòng</div>
<div class="sub">loop cuối {hb.get('last_loop_utc','—')}</div></div>
<div class="card"><div class="k">Valuation worker (pid {vhb.get('pid')})</div>
<div class="v">{'đang chạy' if vhb.get('pid') else '—'} · {vhb.get('marks_written','?')} marks</div>
<div class="sub">loop cuối {vhb.get('last_loop_utc','—')}</div></div>
<div class="card"><div class="k">Quyết định tiếp theo</div>
<div class="v">{hb.get('next_decision_per_family',{}).get('XSECT-FUND-CARRY-7D','—')}</div>
<div class="sub">cả 3 family 00:00 UTC hằng ngày</div></div>
</div>
{err_html}

<h2>3 gia đình strategy (equity marks, 15 phút/mark)</h2>
<div class="grid">{fam_cards}</div>
{equity_svg(carry['marks'])}

<h2>Vị thế hiện tại — XSECT-FUND-CARRY-7D</h2>
<table><tr><th>Symbol</th><th>Chiều</th><th>Qty</th><th>Giá vào</th><th>Giá mark</th>
<th>Notional</th><th>uPnL</th></tr>{rows_pos or '<tr><td colspan=7 class="sub">không có</td></tr>'}</table>
<div class="sub">realized {money(last_carry.get('realized_pnl'))} ·
unrealized {money(last_carry.get('unrealized_pnl'))} · fees {money(last_carry.get('fees'))} ·
slippage {money(last_carry.get('slippage'))} · giá từ {last_carry.get('price_source','—')}</div>

<h2>Lịch sử quyết định (10 sự kiện gần nhất)</h2>
<table><tr><th>Đến hạn (UTC)</th><th>Equity</th><th>PnL kỳ</th><th>Phí</th>
<th>Funding</th><th>Target weights</th></tr>
{rows_events or '<tr><td colspan=6 class="sub">trống</td></tr>'}</table>

<h2>Heartbeat thô</h2>
<pre>{json.dumps(hb, indent=1)[:2200]}</pre>
<pre>{json.dumps(vhb, indent=1)[:2200]}</pre>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        state = build_state()
        if self.path == "/state.json":
            slim = {k: v for k, v in state.items()}
            slim["families"] = {f: {k: v for k, v in d.items() if k != "marks"}
                                for f, d in state["families"].items()}
            body = json.dumps(slim, indent=1, default=str).encode()
            ctype = "application/json"
        else:
            body = render(state).encode()
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"shadow view → http://127.0.0.1:{PORT}/")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
