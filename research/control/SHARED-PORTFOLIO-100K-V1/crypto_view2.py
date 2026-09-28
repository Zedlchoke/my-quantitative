"""PROSPECTIVE-SHADOW-V1 — crypto view v2 (REVIEW BUILD, port 8776).

READ-ONLY. Scratch review build per owner order 2026-09-25: the running
view at 127.0.0.1:8765 is NOT touched. Differences vs the running copy:
  - header frames ONE shared 100k portfolio (epoch 2, PREVIEW) instead of
    per-family 100k cards; per-family equity is shown as EPOCH-1 BOOK ONLY;
  - BTC4H-BANDRIDGE included;
  - links to the unified Phorec 2 dashboard (8767);
  - no per-family 100,000 baseline line rendered as an account.
GET-only, writes nothing outside its own log dir.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import portfolio_lib as pl

PORT = 8776
FAMILIES = ["XSECT-FUND-CARRY-7D", "BASISLV-PREMFADE-28D",
            "ILLIQ-AMIHUD-28D-W", "BTC4H-BANDRIDGE"]
EPOCH2 = {"BTC4H-BANDRIDGE", "BASISLV-PREMFADE-28D", "ILLIQ-AMIHUD-28D-W"}

CSS = """:root{--bg:#0f1216;--card:#171c23;--fg:#e8ecf1;--mut:#8b98a8;
--acc:#4da3ff;--ok:#3ecf8e;--warn:#f5b544;--bad:#ff6b6b;--line:#2a3340}
body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,'SF Pro Text',sans-serif;padding:20px 26px 60px}
h1{font-size:20px;margin:0 0 2px}h2{font-size:15px;margin:22px 0 8px;
border-bottom:1px solid var(--line);padding-bottom:4px}
.sub{color:var(--mut);font-size:12px}
.banner{background:#3d2f00;color:var(--warn);border:1px solid #6b5500;
border-radius:10px;padding:10px 14px;font-size:13px;margin:12px 0;line-height:1.6}
.grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:10px 12px}.k{color:var(--mut);font-size:11px;text-transform:uppercase}
.v{font-size:15px;margin-top:2px;font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin-top:6px}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-size:11px;text-transform:uppercase}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap;text-align:right}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
pre{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:10px;font-size:11.5px;overflow:auto;max-height:340px}
a{color:var(--acc)}"""


def read_jsonl(path: Path) -> list[dict]:
    return pl.read_jsonl(path)


def money(v) -> str:
    return f"{v:,.2f}" if isinstance(v, (int, float)) else "UNAVAILABLE"


def build_state() -> dict:
    hb = pl.read_json(pl.PSV1_RESULTS / "runtime/heartbeat.json") or {}
    vhb = pl.read_json(pl.PSV1_RESULTS / "runtime/valuation_heartbeat.json") or {}
    fam = {}
    for f in FAMILIES:
        marks = read_jsonl(pl.PSV1_RESULTS / f"valuation_marks/{f}.jsonl")
        fam[f] = {"last": marks[-1] if marks else None, "n_marks": len(marks),
                  "marks": marks}
    ledger = read_jsonl(pl.PSV1_RESULTS / "ledgers/XSECT-FUND-CARRY-7D.jsonl")
    return {"decision_hb": hb, "valuation_hb": vhb, "families": fam,
            "ledger_events": ledger}


def render(state: dict) -> str:
    hb, vhb = state["decision_hb"], state["valuation_hb"]
    carry = state["families"]["XSECT-FUND-CARRY-7D"]
    last_carry = carry["last"] or {}
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
    fam_cards = ""
    for f, d in state["families"].items():
        last = d["last"] or {}
        status = last.get("status", "NO_MARK")
        cls = {"RUNNING": "ok", "FLAT_OK": "warn"}.get(status, "bad")
        tag = ("Sleeve epoch-2" if f in EPOCH2
               else "ĐÃ RETIRE khỏi epoch-2 — sách cũ, chạy về flat theo A3")
        fam_cards += (f"<div class='card'><div class='k'>{f}</div>"
                      f"<div class='v'>{money(last.get('equity'))} "
                      f"<span class='{cls}'>{status}</span></div>"
                      f"<div class='sub'>{tag} — equity SÁCH CŨ (epoch-1), "
                      f"không phải tài khoản riêng trong portfolio mới</div>"
                      f"<div class='sub'>{last.get('mark_timestamp_utc','—')} · "
                      f"{d['n_marks']} marks · gross {last.get('gross', 0):.4f}</div></div>")
    vhb_err = vhb.get("last_error")
    err_html = (f"<p class='bad'>valuation last_error: {vhb_err}</p>" if vhb_err
                else "<p class='ok'>valuation: no error</p>")
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<title>Shadow Monitor v2 — SHARED PORTFOLIO 100K (PREVIEW)</title><style>{CSS}</style></head><body>
<h1>Shadow Monitor v2 — SHARED PORTFOLIO 100K <span class="sub">(paper · PREVIEW)</span></h1>
<div class="sub">Epoch 2 CHƯA ACTIVATE · một portfolio 100.000 USD-equivalent cho toàn bộ sleeve ·
bản review, không thay bản 8765 đang chạy ·
<a href="http://127.0.0.1:8767/">→ Phorec 2 (portfolio + lịch PnL)</a> · <a href="/state.json">state.json</a></div>
<div class="banner">EPOCH 2 · PREVIEW — CHƯA ACTIVATE. Mỗi thẻ dưới đây là <b>sách cũ epoch-1
(mỗi sleeve 100k)</b>, chỉ dùng làm lịch sử/quan sát. Trong portfolio mới, mỗi sleeve chỉ là
<b>đóng góp vào tài khoản chung $100,000</b> — không còn cộng các sleeve thành 300k/400k.
CUTOVER BLOCKED chờ GO của owner.</div>

<h2>Sách cũ theo gia đình (4 gia đình — epoch-1)</h2>
<div class="grid">{fam_cards}</div>
{err_html}

<h2>Vị thế hiện tại — XSECT-FUND-CARRY-7D (sách cũ, chạy về flat khi A3 được GO)</h2>
<table><tr><th>Symbol</th><th>Chiều</th><th>Qty</th><th>Giá vào</th><th>Giá mark</th>
<th>Notional</th><th>uPnL</th></tr>{rows_pos or '<tr><td colspan=7 class="sub">không có</td></tr>'}</table>
<div class="sub">realized {money(last_carry.get('realized_pnl'))} ·
unrealized {money(last_carry.get('unrealized_pnl'))} · fees {money(last_carry.get('fees'))} ·
slippage {money(last_carry.get('slippage'))} · funding {money(last_carry.get('funding'))} ·
giá từ {last_carry.get('price_source','—')} · PnL dương KHÔNG phải bằng chứng strategy tốt</div>

<h2>Workers</h2>
<div class="sub">decision pid {hb.get('pid')} · loop cuối {hb.get('last_loop_utc','—')} ·
valuation pid {vhb.get('pid')} · {vhb.get('marks_written','?')} marks · loop cuối {vhb.get('last_loop_utc','—')}</div>
<pre>{json.dumps(vhb, indent=1)[:1500]}</pre>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        state = build_state()
        if self.path == "/state.json":
            slim = dict(state)
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
    print(f"crypto view v2 (REVIEW, epoch2 NOT activated) → http://127.0.0.1:{PORT}/")
    print("does not touch 8765 or any worker")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
