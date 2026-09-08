"""LAB DASHBOARD — Lớp 2: Renderer (stdlib).

Nhận snapshot dict từ dashboard_collect, xuất HTML tự chứa: CSS/SVG
inline, JS vanilla tối thiểu (filter/accordion), KHÔNG CDN, không mạng.
Tiếng Việt + thuật ngữ Anh. Mọi panel có footer nguồn. Giá trị None /
thiếu -> `KHÔNG CÓ DỮ LIỆU`, không bao giờ suy diễn.
"""

from __future__ import annotations

import html as _html
import json

NO_DATA = "KHÔNG CÓ DỮ LIỆU"

_CSS = """
:root{--bg:#0f1216;--card:#171c23;--card2:#1d242e;--fg:#e8ecf1;--mut:#8b98a8;
--acc:#4da3ff;--ok:#3ecf8e;--warn:#f5b544;--bad:#ff6b6b;--line:#2a3340}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,'SF Pro Text','Segoe UI',Roboto,sans-serif;
padding:20px 24px 60px}
h1{font-size:22px;margin:0 0 2px}
h2{font-size:16px;margin:26px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:13px;margin:14px 0 6px;color:var(--acc)}
.sub{color:var(--mut);font-size:12px}
.grid{display:grid;gap:12px}
.g3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:12px 14px}
.card .k{color:var(--mut);font-size:11px;text-transform:uppercase;
letter-spacing:.04em}
.card .v{font-size:15px;margin-top:2px}
.num{font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:1px 8px;border-radius:99px;font-size:11px;
border:1px solid var(--line);background:var(--card2)}
.badge.ok{color:var(--ok);border-color:var(--ok)}
.badge.bad{color:var(--bad);border-color:var(--bad)}
.badge.mut{color:var(--mut)}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);
vertical-align:top}
th{color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;
letter-spacing:.03em}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
tr.anchor td:first-child{color:var(--acc);font-weight:600}
.src{color:var(--mut);font-size:11px;margin-top:8px;word-break:break-all}
.nd{color:var(--mut);font-style:italic}
.filterbar{margin:8px 0;display:flex;gap:8px;flex-wrap:wrap}
.filterbar input,.filterbar select{background:var(--card2);color:var(--fg);
border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-size:12px}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;
margin:6px 0;padding:8px 12px}
summary{cursor:pointer;font-weight:600;font-size:13px}
details .body{white-space:pre-wrap;font-size:12.5px;color:var(--fg);
margin-top:8px;max-height:340px;overflow:auto}
pre{white-space:pre-wrap;word-break:break-all;font-size:11.5px;
background:var(--card2);padding:8px;border-radius:6px;color:var(--mut)}
.dim{opacity:.55}
.tag-TECHABORT,.tag-NOT_RUN_SUPERSEDED{opacity:.55}
.scroll{max-height:520px;overflow:auto;border:1px solid var(--line);
border-radius:8px}
.scroll table{position:sticky}
.scroll th{position:sticky;top:0;background:var(--card2);z-index:1}
"""

_JS = """
function fFail(){
  var a=document.getElementById('f-asset').value,
      v=document.getElementById('f-verdict').value,
      q=document.getElementById('f-q').value.toLowerCase(),
      rows=document.querySelectorAll('#fail-tbody tr');
  var n=0;
  rows.forEach(function(r){
    var ok=(a==='*'||r.dataset.asset===a)&&(v==='*'||r.dataset.verdict===v)
          &&(!q||r.textContent.toLowerCase().includes(q));
    r.style.display=ok?'':'none'; if(ok)n++;
  });
  document.getElementById('fail-count').textContent=n;
}
"""


def esc(x) -> str:
    if x is None:
        return f'<span class="nd">{NO_DATA}</span>'
    return _html.escape(str(x))


def esc_attr(x) -> str:
    return _html.escape("" if x is None else str(x), quote=True)


def fmt_num(x) -> str:
    if x is None:
        return f'<span class="nd">{NO_DATA}</span>'
    if isinstance(x, float):
        s = f"{x:.6g}"
    else:
        s = str(x)
    return f'<span class="num">{esc(s)}</span>'


def fmt_text(x) -> str:
    if x is None or x == "":
        return f'<span class="nd">{NO_DATA}</span>'
    return esc(x)


def _src(path: str) -> str:
    return f'<div class="src">Nguồn: {esc(path)}</div>'


# ---------------------------------------------------------------------------
# Các panel
# ---------------------------------------------------------------------------

def _panel_header(s: dict) -> str:
    h = s["header"]
    prog = h.get("program") or {}
    cards = [f"""<div class="card"><div class="k">Program (denominators, P-9)</div>
    <div class="v num">{esc(prog.get('published'))} published / {esc(prog.get('observed'))} observed</div></div>"""]
    for asset in ("crypto", "stocks", "forex"):
        a = h.get(asset) or {}
        cards.append(
            f'<div class="card"><div class="k">{esc(asset)}</div>'
            f'<div class="v num">{esc(a.get("published"))} / {esc(a.get("observed"))}</div></div>')
    zero = h.get("zero_survivors")
    zero_v = ('<span class="badge ok">0 survivors</span>'
              if zero is True else
              f'<span class="badge bad">{esc(zero or NO_DATA)}</span>')
    s1 = h.get("s1")
    go = "".join(
        f'<div class="v"><span class="badge">{esc(g["phrase"])}</span> '
        f'<span class="sub">{esc(g["plan"])}</span></div>'
        for g in (h.get("go_registry") or [])) or f'<div class="v nd">{NO_DATA}</div>'
    srcs = (f"{h.get('source')} (denominators, S1); "
            + "; ".join(g["source"] for g in (h.get("go_registry") or [])))
    return f"""<h2>1 · Tổng quan chương trình</h2>
<div class="grid g3">{''.join(cards)}
<div class="card"><div class="k">Survivors</div><div class="v">{zero_v}</div></div>
<div class="card"><div class="k">S1</div><div class="v">{esc(s1)}</div></div>
<div class="card"><div class="k">GO registry (§7)</div>{go}</div>
</div>{_src(srcs)}"""


def _panel_assets(s: dict) -> str:
    cards = []
    for a in s["assets"]:
        arts = a.get("latest_artifacts") or []
        art_txt = ("<br>".join(
            f'<span class="num">{esc(x["name"])}</span> '
            f'<span class="sub">{esc(x["mtime_utc"])}</span>' for x in arts)
            or f'<span class="nd">{NO_DATA}</span>')
        hb = a.get("heartbeat")
        hb_txt = (f'<span class="num">{esc(json.dumps(hb, ensure_ascii=False)[:120])}</span>'
                  if hb not in (None, NO_DATA) else f'<span class="nd">{NO_DATA}</span>')
        ev = a.get("last_event")
        ev_txt = (esc(json.dumps(ev, ensure_ascii=False)[:140])
                  if ev not in (None, NO_DATA) else f'<span class="nd">{NO_DATA}</span>')
        lock = a.get("heavy_lock_rows") or []
        lock_txt = (f'{len(lock)} row (mới nhất: '
                    f'{esc(json.dumps(lock[-1], ensure_ascii=False)[:100])})'
                    if lock else f'<span class="nd">{NO_DATA}</span>')
        cards.append(f"""<div class="card">
<div class="k">{esc(a['cycle_id'])}</div>
<div class="v">{esc(a['measured_status'])}</div>
<div class="k" style="margin-top:8px">branch / HEAD</div>
<div class="v num">{esc(a['branch'])} @ {esc(a['head_short'])}</div>
<div class="k" style="margin-top:8px">plan</div>
<div class="v sub">{esc(a['plan'])}</div>
<div class="k" style="margin-top:8px">budget</div>
<div class="v">{esc(a['budget'])}</div>
<div class="k" style="margin-top:8px">artifact mới nhất trong control dir</div>
<div class="v" style="font-size:12px">{art_txt}</div>
<div class="k" style="margin-top:8px">heartbeat</div>
<div class="v" style="font-size:12px">{hb_txt}</div>
<div class="k" style="margin-top:8px">event cuối</div>
<div class="v" style="font-size:12px">{ev_txt}</div>
<div class="k" style="margin-top:8px">heavy-lock (cycle này)</div>
<div class="v" style="font-size:12px">{lock_txt}</div>
</div>""")
    srcs = ("`git -C <worktree> rev-parse`, control dir từng cycle "
            "(state/heartbeat/event_log, chỉ ĐỌC), heavy_runtime history; "
            + "; ".join(a["control_dir"] for a in s["assets"]))
    return f"<h2>2 · Ba cycle đang chạy (chỉ ĐỌC)</h2><div class=\"grid g3\">{''.join(cards)}</div>{_src(srcs)}"


def _panel_running(s: dict) -> str:
    r = s["running"]
    rows = []
    for hl in r["heavy_lock"]:
        lock = hl["lock"]
        lock_txt = (esc(json.dumps(lock, ensure_ascii=False))
                    if isinstance(lock, dict) else f'<span class="nd">{esc(lock)}</span>')
        rows.append(f'<tr><td>{esc(hl["runtime"])}</td><td>{lock_txt}</td></tr>')
    hist = []
    for h in r["heavy_history"]:
        for row in h["last"]:
            hist.append(
                f'<tr><td>{esc(h["runtime"])}</td>'
                f'<td>{esc(row.get("cycle_id"))}</td>'
                f'<td>{esc(row.get("role"))}</td>'
                f'<td>{esc(row.get("status"))}</td>'
                f'<td>{esc(row.get("started_at"))}</td>'
                f'<td>{esc(row.get("released_at"))}</td></tr>')
    ps = r["ps_workers"]
    ps_rows = "\n".join(f"<tr><td>{esc(l)}</td></tr>" for l in ps["rows"]) or \
        f'<tr><td><span class="nd">{NO_DATA}</span></td></tr>'
    srcs = ("; ".join(hl["source"] for hl in r["heavy_lock"])
            + "; " + ps["source"] + f' ({ps["label"]})')
    return f"""<h2>3 · Đang chạy trên máy</h2>
<div class="grid g3">
<div class="card"><div class="k">Heavy-lock hiện hành</div>
<table><tr><th>runtime</th><th>lock</th></tr>{''.join(rows)}</table></div>
<div class="card"><div class="k">History 10 dòng cuối (mỗi runtime)</div>
<div class="scroll"><table><tr><th>runtime</th><th>cycle</th><th>role</th>
<th>status</th><th>start</th><th>release</th></tr>{''.join(hist) or f'<tr><td colspan="6"><span class="nd">{NO_DATA}</span></td></tr>'}</table></div></div>
<div class="card"><div class="k">python worker ({esc(ps["label"])})</div>
<table>{ps_rows}</table></div>
</div>{_src(srcs)}"""


def _panel_failures(s: dict) -> str:
    f = s["failures"]
    rows = []
    for e in f["entries"]:
        if "_parse_error" in e:
            continue
        cls = e.get("verdict_class", "?")
        dim = ' class="dim"' if cls in ("TECHABORT", "NOT_RUN_SUPERSEDED") \
            or e.get("no_quality_evidence") else ""
        warn = (' <span class="badge mut">không mang bằng chứng chất lượng</span>'
                if cls in ("TECHABORT", "NOT_RUN_SUPERSEDED")
                or e.get("no_quality_evidence") else "")
        pf = e.get("primary_failure") or {}
        ev = e.get("evidence") or {}
        detail = json.dumps({
            "cycle_id": e.get("cycle_id"), "family_id": e.get("family_id"),
            "family_title": e.get("family_title"), "status": e.get("status"),
            "measured_summary": e.get("measured_summary"),
            "primary_failure": pf, "secondary_failures": e.get("secondary_failures"),
            "evidence": ev, "recorded_by": e.get("recorded_by"),
            "recorded_utc": e.get("recorded_utc"),
        }, ensure_ascii=False, indent=1)
        rows.append(f"""<tr{dim} data-asset="{esc_attr(e.get('asset'))}" data-verdict="{esc_attr(cls)}">
<td>{esc(e.get('cycle_id'))}</td><td>{esc(e.get('family_id'))}</td>
<td>{esc(e.get('asset'))}</td><td><span class="badge bad">{esc(cls)}</span>{warn}</td>
<td>{esc(pf.get('code'))}</td>
<td class="n">{esc(ev.get('terminal_sha') or NO_DATA)[:12]}</td>
<td><details><summary>mở evidence</summary><pre class="body">{esc(detail)}</pre></details></td></tr>""")
    assets = sorted({e.get("asset") for e in f["entries"] if "asset" in e})
    verdicts = sorted({e.get("verdict_class") for e in f["entries"]
                       if "verdict_class" in e})
    opts = lambda vs: "".join(f'<option>{esc(v)}</option>' for v in vs)
    return f"""<h2>4 · Bộ nhớ thất bại ({f["total"]} family)</h2>
<div class="filterbar">
<input id="f-q" placeholder="lọc chữ ký / family..." oninput="fFail()">
<select id="f-asset" onchange="fFail()"><option value="*">mọi asset</option>{opts(assets)}</select>
<select id="f-verdict" onchange="fFail()"><option value="*">mọi verdict</option>{opts(verdicts)}</select>
<span class="sub"><span id="fail-count">{len(rows)}</span> dòng</span>
</div>
<div class="scroll"><table id="fail-t">
<tr><th>cycle</th><th>family</th><th>asset</th><th>verdict</th>
<th>primary_failure</th><th>terminal sha</th><th>evidence</th></tr>
<tbody id="fail-tbody">{''.join(rows)}</tbody></table></div>
<p class="sub">TECHABORT / NOT_RUN_SUPERSEDED làm mờ: không mang bằng chứng
chất lượng family (FAMILY_PIPELINE §9).</p>{_src(f["source"])}"""


def _panel_signatures(s: dict) -> str:
    counts = s["failures"]["signature_counts"]
    if not counts:
        return (f'<h2>5 · Chữ ký thất bại</h2><p class="nd">{NO_DATA}</p>'
                + _src(s["failures"]["source"]))
    mx = max(c["count"] for c in counts)
    W, BAR = 560, 18
    bars = []
    y = 4
    for c in counts:
        w = int(360 * c["count"] / mx)
        bars.append(
            f'<text x="{W-8}" y="{y+13}" text-anchor="end" font-size="11" '
            f'fill="#8b98a8">{esc(c["code"])}</text>'
            f'<rect x="4" y="{y}" width="{w}" height="{BAR-4}" rx="2" fill="#4da3ff"/>'
            f'<text x="{4+w+6}" y="{y+13}" font-size="11" fill="#e8ecf1">{c["count"]}</text>')
        y += BAR
    svg = (f'<svg viewBox="0 0 {W} {y+6}" width="100%" '
           f'preserveAspectRatio="xMidYMin meet">{"".join(bars)}</svg>')
    return (f'<h2>5 · Chữ ký thất bại (primary_failure)</h2>{svg}'
            + _src(s["failures"]["source"]))


def _panel_pnl(s: dict) -> str:
    out = ['<h2>6 · PnL tổng quan — bảng anchor/neighbour/control của '
           'các cycle đóng</h2>']
    out.append('<p class="sub">Mỗi bảng trích từ terminal artifact tại '
               'terminal SHA đã pin trong FAMILY_FAILURES.jsonl '
               '(<code>git show sha:path</code>); mapper theo từng schema '
               'cycle, số trích nguyên văn. Không trích được → '
               f'{NO_DATA} + ledger pointer, không suy diễn.</p>')
    if not s["pnl"]:
        out.append(f'<p class="nd">{NO_DATA}</p>')
    for p in s["pnl"]:
        head = (f'<h3>{esc(p["cycle_id"])} — {esc(p["asset"])} '
                f'<span class="badge mut">{esc(", ".join(p["verdict_classes"]))}</span></h3>'
                f'<div class="sub">families: '
                f'{esc(", ".join(str(x) for x in p["families"] if x is not None) or NO_DATA)}</div>')
        body_rows = []
        t = p.get("table")
        if t:
            for fam in t["families"]:
                body_rows.append(
                    f'<tr><td colspan="8" style="background:var(--card2)">'
                    f'<b>{esc(fam["family_label"])}</b></td></tr>')
                for a in fam["arms"]:
                    body_rows.append(
                        f'<tr class="{esc(a["role"].split(":")[0])}">'
                        f'<td>{esc(a["role"])}</td><td>{esc(a["label"])}</td>'
                        f'<td>{fmt_num(a["expectancy"])}</td>'
                        f'<td>{fmt_num(a["pnl"])}</td>'
                        f'<td>{fmt_num(a["pf"])}</td>'
                        f'<td>{fmt_text(a["folds"])}</td>'
                        f'<td>{fmt_num(a["mdd"])}</td>'
                        f'<td>{fmt_text(a["margins"])}</td></tr>')
        if body_rows:
            tbl = ('<div class="scroll"><table><tr><th>arm</th><th>cell</th>'
                   '<th>expectancy</th><th>PnL</th><th>PF</th><th>folds</th>'
                   '<th>MDD</th><th>margins (P-2)</th></tr>'
                   + "".join(body_rows) + "</table></div>")
        else:
            tbl = (f'<p class="nd">{NO_DATA} — {esc(p.get("no_data_reason")
                                                          or "mapper không trích được arm nào")}</p>'
                   f'<p class="sub">ledger pointer: {esc(p.get("ledger_row")
                                                              or NO_DATA)}</p>')
        out.append(head + tbl + _src(p["source"]))
    return "\n".join(out)


def _panel_near_miss(s: dict) -> str:
    nm = s["near_misses"]
    return (f'<h2>7 · Near-miss (Lead tuyển — ledger mục E)</h2>'
            f'<div class="card"><div class="body" style="white-space:pre-wrap">'
            f'{esc(nm["body"])}</div></div>' + _src(nm["source"]))


def _panel_lessons(s: dict) -> str:
    if not s["lessons"]:
        return (f'<h2>8 · Bài học P-1..P-11</h2><p class="nd">{NO_DATA}</p>'
                + _src(s["failures"]["source"]))
    items = []
    for l in s["lessons"]:
        items.append(
            f'<details><summary>{esc(l["id"])} — {esc(l["title"])}</summary>'
            f'<div class="body">{esc(l["body"])}</div>'
            f'<div class="src">Nguồn: {esc(l["source"])}</div></details>')
    return (f'<h2>8 · Bài học P-1..P-11 (LESSONS.md)</h2>{"".join(items)}'
            + _src(s["lessons"][0]["source"].rsplit(" dòng", 1)[0]))


def render(s: dict) -> str:
    panels = "".join([
        _panel_header(s), _panel_assets(s), _panel_running(s),
        _panel_failures(s), _panel_signatures(s), _panel_pnl(s),
        _panel_near_miss(s), _panel_lessons(s),
    ])
    footer_sources = sorted({
        str(src) for src in (
            s["failures"]["source"], s["header"].get("source"),
            s["near_misses"]["source"], LESSONS_SRC(s),
            *[a["control_dir"] for a in s["assets"]],
            *[hl["source"] for hl in s["running"]["heavy_lock"]],
        ) if src
    })
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<title>Lab Dashboard</title><style>{_CSS}</style></head>
<body>
<h1>LAB DASHBOARD</h1>
<div class="sub">measured_at: <span class="num">{esc(s['measured_at'])}</span>
· root: <code>{esc(s['root'])}</code> · Công cụ cho chủ sở hữu — KHÔNG phải
research cycle; mọi số truy được artifact, thiếu = {NO_DATA}.</div>
{panels}
<h2>9 · Nguồn (footer)</h2>
<ul class="sub">{''.join(f'<li>{esc(x)}</li>' for x in footer_sources)}</ul>
<script>{_JS}</script>
</body></html>"""


def LESSONS_SRC(s: dict) -> str:
    return (s["lessons"][0]["source"].rsplit(" dòng", 1)[0]
            if s["lessons"] else "research/wayfinder/LESSONS.md")
