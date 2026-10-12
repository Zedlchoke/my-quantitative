"""LIVE local dashboard for SPORTS-PAPERTRADE-EXEC-V1 (ERRATUM_EXEC_5 D-1.3).

Binds 127.0.0.1 ONLY (never a public interface). Every /api/state request
re-reads the ledger from disk, verifies the hash chain, and refuses to render
financials when the chain is tampered (fail-closed alarm instead). The page is
an interactive single file (client auto-refresh 8 s ≤ the 10 s law); SANDBOX
and REAL are visually distinct and derived from the GENESIS row's `sandbox`
flag — a sandbox ledger can never render as REAL. Key bytes never appear here.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AUTO_REFRESH_SECONDS = 8
HEARTBEAT_STALE_S = 180          # LIVE if heartbeat younger than this

_REFRESH_HTML = '''<!doctype html>
<html><head><meta charset="utf-8">
<title>SPORTS-PAPERTRADE-EXEC-V1 — live paper desk</title>
<style>
 :root{--bg:#0e1116;--card:#161c24;--ink:#e6edf3;--mut:#8b98a5;--ok:#3fb950;
 --warn:#d29922;--bad:#f85149;--acc:#58a6ff;}
 body{background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,
 "Segoe UI",Roboto,sans-serif;margin:0;padding:18px;}
 h1{font-size:19px;margin:0 0 2px;} h2{font-size:15px;margin:18px 0 6px;
 color:var(--acc);} .sub{color:var(--mut);font-size:12px;}
 .grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));}
 .card{background:var(--card);border:1px solid #232b36;border-radius:10px;
 padding:10px 12px;} .k{color:var(--mut);font-size:11px;text-transform:
 uppercase;letter-spacing:.04em;} .v{font-size:19px;font-weight:650;}
 .pill{display:inline-block;padding:1px 9px;border-radius:999px;font-size:11px;
 font-weight:700;} .pill.ok{background:#12351c;color:var(--ok);}
 .pill.warn{background:#3a2b0a;color:var(--warn);} .pill.bad{background:#3d1214;
 color:var(--bad);} .pill.real{background:#0d2a52;color:#79b8ff;}
 .pill.sb{background:#3a2b0a;color:var(--warn);}
 table{width:100%;border-collapse:collapse;font-size:12.5px;}
 th{color:var(--mut);text-align:left;font-weight:600;border-bottom:1px solid
 #232b36;padding:4px 6px;} td{border-bottom:1px solid #1c232d;padding:4px 6px;
 vertical-align:top;} tr:hover td{background:#1a2130;}
 .num{text-align:right;font-variant-numeric:tabular-nums;}
 select,input{background:#0e1116;color:var(--ink);border:1px solid #232b36;
 border-radius:6px;padding:3px 6px;}
 .banner{border-radius:10px;padding:8px 12px;margin:10px 0;font-weight:700;}
 .banner.sbx{background:#3a2b0a;color:var(--warn);} .banner.tamper{
 background:#3d1214;color:var(--bad);} .banner.real{background:#0d2a52;
 color:#79b8ff;} .muted{color:var(--mut);} code{color:#9ecbff;font-size:12px;}
 .foot{margin-top:16px;color:var(--mut);font-size:11px;}
</style></head><body>
<h1>SPORTS-PAPERTRADE-EXEC-V1 · paper desk</h1>
<div class="sub" id="sub">loading…</div>
<div id="mode"></div><div id="alarms"></div>
<div class="grid" id="wallet"></div>
<h2>Cadence &amp; service</h2><div class="grid" id="svc"></div>
<h2>Odds quota <span class="sub">(frozen 4/day · 120/month)</span></h2>
<div class="grid" id="quota"></div>
<h2>Matches
 <span class="sub">— filter:</span>
 <select id="fLeague"><option>ALL</option></select>
 <select id="fStatus"><option>ALL</option><option>OPEN</option>
 <option>BET_PAPER</option><option>SETTLED</option><option>NO_BET</option>
 <option>NOT_RUN</option></select>
 <span class="sub" id="count"></span></h2>
<table id="matches"><thead><tr>
<th>League</th><th>Match</th><th>Kickoff (UTC)</th><th>Forecast p</th>
<th>Quote (pinnacle)</th><th>EV_net by leg</th><th>Decision</th>
<th>Stake</th><th>Result / PnL</th></tr></thead><tbody></tbody></table>
<h2>Upcoming windows (anchor deadlines)</h2>
<table id="upcoming"><thead><tr><th>League</th><th>Match</th>
<th>Anchor (UTC)</th><th>Countdown</th><th>Eligible now</th><th>Note</th>
</tr></thead><tbody></tbody></table>
<h2>WSL (shared wallet · CAPITAL-V3 §4)</h2>
<table id="wsl"><thead><tr><th>Match</th><th>Kickoff (UTC)</th>
<th>Forecast p×3</th><th>PM book (best/vwap · fee · depth)</th>
<th>Decision</th><th>Stake</th><th>Result / PnL</th></tr></thead>
<tbody></tbody></table>
<h2>Incidents (tail)</h2><table id="incidents"><thead><tr><th>ts</th>
<th>kind</th><th>detail</th></tr></thead><tbody></tbody></table>
<div class="foot" id="foot"></div>
<script>
const $=id=>document.getElementById(id);
const AUTO_REFRESH_SECONDS=8;   // <= the 10s refresh law
const HEARTBEAT_STALE_S=180;     // same threshold as the server
const money=c=>(c/100).toLocaleString("en-US",{style:"currency",currency:"USD"});
function esc(s){return String(s??"").replace(/[&<>"]/g,
 c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
function pill(txt,cls){return `<span class="pill ${cls}">${esc(txt)}</span>`;}
function card(k,v,sub){return `<div class="card"><div class="k">${esc(k)}</div>
 <div class="v">${v}</div>${sub?`<div class="sub">${sub}</div>`:""}</div>`;}
function ago(ts){if(!ts)return"—";const s=(Date.now()-Date.parse(ts))/1e3;
 if(s<90)return Math.round(s)+"s ago";if(s<5400)return Math.round(s/60)+"m ago";
 return Math.round(s/3600)+"h ago";}
function cd(ts){const s=(Date.parse(ts)-Date.now())/1e3;
 if(s<=0)return "PASSED";const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),
 m=Math.floor(s%3600/60);return (d?d+"d ":"")+h+"h "+m+"m";}
function statusClass(st){if(st==="BET_PAPER")return"warn";
 if(st==="NO_EDGE")return"ok";if(st&&st.startsWith("BLOCKED"))return"bad";
 return"warn";}
async function tick(){
 try{const r=await fetch("/api/state",{cache:"no-store"});
  if(!r.ok)throw new Error("http "+r.status);
  render(await r.json());}
 catch(e){$("sub").textContent="state fetch FAILED: "+e.message+
  " — retrying";}
}
function render(S){
 const svc=S.service||{};
 $("sub").innerHTML=`generated <code>${esc(S.generated_at_utc)}</code> · `+
  `ledger <code>${esc(S.ledger.path)}</code> · `+
  `auto-refresh ${AUTO_REFRESH_SECONDS}s`;
 $("mode").innerHTML = S.mode==="SANDBOX"
  ? `<div class="banner sbx">SANDBOX — rehearsal ledger (NOT the real paper
     wallet)</div>`
  : `<div class="banner real">${pill("REAL PAPER LEDGER","real")} — virtual
     money only; this is NOT a real-money account</div>`;
 $("alarms").innerHTML = S.chain.ok ? "" :
  `<div class="banner tamper">CHAIN TAMPER DETECTED — financials withheld:
   ${esc((S.chain.errors||[]).join(" | "))}</div>`;
 const w=S.wallet||{}, q=S.quota||{};
 const alarm = !S.chain.ok;
 $("wallet").innerHTML = alarm ? "" :
  card("Equity", money(w.equity_cents),
       `peak ${money(w.peak_cents)} · drawdown
        ${(100*(w.drawdown_frac||0)).toFixed(2)}%`)+
  card("Open exposure", `${money(w.open_exposure_cents)} / ${money(w.open_exposure_cap_cents)}`,
       `${w.open_count||0} open bet(s)`)+
  card("Realized PnL", money(w.total_pnl_cents||0),
       `WNBA ${money((w.sport_pnl_cents||{}).WNBA||0)} · NBA
        ${money((w.sport_pnl_cents||{}).NBA||0)} · SOCCER
        ${money((w.sport_pnl_cents||{}).SOCCER||0)}`)+
  card("Outcomes", `${(w.outcomes||{}).WIN||0}W /
        ${(w.outcomes||{}).LOSE||0}L / ${(w.outcomes||{}).REFUND||0}R`,
       `${w.settled_count||0} settled · paused: ${w.paused?"YES":"no"}`);
 const svcStatus = svc.heartbeat_age_s==null ? pill("NO HEARTBEAT","bad")
  : svc.heartbeat_age_s<HEARTBEAT_STALE_S ? pill("LIVE","ok")
  : pill("STALE ("+Math.round(svc.heartbeat_age_s/60)+"m)","warn");
 $("svc").innerHTML =
  card("Service", svcStatus, `pid ${esc(svc.pid)} · tick ${ago(svc.last_tick_utc)}`)+
  card("Last cadence", ago(svc.last_cadence_tick_utc),
       svc.last_cadence_result?esc(JSON.stringify(svc.last_cadence_result).slice(0,150)):"")+
  card("Last settle", ago(svc.last_settle_tick_utc),
       `tick latency ${svc.last_tick_ms??"—"} ms · ticks ${esc(svc.tick_count)}`)+
  card("Static rebuild", ago(svc.last_dashboard_rebuild_utc),
       `srv latency ${esc(S.serve_latency_ms)} ms`);
 $("quota").innerHTML=
  card("Today", `${q.used_today??"—"}/4 credits`,
       q.halted?pill("HALTED: "+(q.halt_reason||""),"bad"):"")+
  card("Month", `${q.used_month??"—"}/120 credits`,
       `provider remaining: ${esc(q.remaining_last??"—")}`)+
  card("Journal tail", (q.journal_tail||[]).length+" entries",
       esc((q.journal_tail||[]).slice(-1).map(j=>
        `${j.endpoint} cost=${j.cost_credits} @${j.ts_utc}`).join("")||"—"));
 const fsel=$("fLeague"), keep=fsel.value;
 const leagues=[...new Set((S.matches||[]).map(m=>m.league))];
 fsel.innerHTML=`<option>ALL</option>`+
  leagues.map(l=>`<option>${esc(l)}</option>`).join("");
 if(leagues.includes(keep))fsel.value=keep;
 const fl=fsel.value, fst=$("fStatus").value;
 const rows=(S.matches||[]).filter(m=>
   (fl==="ALL"||m.league===fl) &&
   (fst==="ALL" ||
    (fst==="OPEN"?m.is_open:fst==="SETTLED"?!!m.settlement:
     fst==="NO_BET"?["NO_EDGE","NO_QUOTE","NO_FORECAST","STALE_PRICE",
       "CROSSWALK_MISS","QUOTA_SKIP"].includes(m.decision?.status):
     m.decision?.status===fst)));
 $("count").textContent=`${rows.length}/${(S.matches||[]).length} shown`;
 $("matches").querySelector("tbody").innerHTML = alarm ? "" : rows.map(m=>{
  const d=m.decision||{};
  const st=d.status||"—";
  return `<tr><td>${esc(m.league)}</td>
  <td>${esc(m.home)} v ${esc(m.away)}<div class="sub">${esc(m.competition||"")}
   · id ${esc(m.match_id)}</div></td>
  <td>${esc(m.kickoff_utc||"")}</td>
  <td>${m.forecast?Object.entries(m.forecast.p).map(([k,v])=>
    `${k} ${(100*v).toFixed(1)}%`).join("<br>"):"—"}</td>
  <td>${m.quote?Object.entries(m.quote.odds).map(([k,v])=>
    `${k} ${v}`).join("<br>"):st==="NO_QUOTE"?
    `<span class="muted">no qualifying quote</span>`:"—"}</td>
  <td>${d.ev_net_by_leg?Object.entries(d.ev_net_by_leg).map(([k,v])=>
    `${k} ${(100*v).toFixed(1)}%`).join("<br>"):"—"}</td>
  <td>${pill(st,statusClass(st))}${d.chosen_leg?` · ${esc(d.chosen_leg)}`:""}
   <div class="sub">${esc(d.reason||"")}</div></td>
  <td class="num">${d.stake_cents?money(d.stake_cents):"—"}</td>
  <td>${m.settlement?`${esc(m.settlement.outcome_for_leg)}
    <b>${money(m.settlement.pnl_cents)}</b><div class="sub">${ago(
    m.settlement.settled_at_utc)} · ${esc(m.settlement.source_ref||"").slice(0,90)}</div>`
   :(m.is_open?pill("OPEN","warn"):"")}</td></tr>`;}).join("") ||
  `<tr><td colspan="9" class="muted">no matches</td></tr>`;
 $("upcoming").querySelector("tbody").innerHTML=(S.upcoming||[]).map(u=>
  `<tr><td>${esc(u.league)}</td><td>${esc(u.home)} v ${esc(u.away)}</td>
  <td>${esc(u.anchor_utc)}</td><td>${cd(u.anchor_utc)}</td>
  <td>${u.eligible_now?pill("ELIGIBLE","ok"):pill("not yet","warn")}</td>
  <td class="sub">${esc(u.note||"")}</td></tr>`).join("") ||
  `<tr><td colspan="6" class="muted">no upcoming fixtures in rolling
   horizon</td></tr>`;
 $("wsl").querySelector("tbody").innerHTML = (S.chain.ok ? (S.wsl||[]) : [])
  .map(m=>{const d=m.decision||{};const q=m.quote||{};
   const pm=q.pm_outcomes?Object.entries(q.pm_outcomes).map(([l,o])=>
    `${l}: ${o.best_ask}/${o.vwap_ask} · fee ${o.fee_total_usdc?.toFixed(3)} · `+
    `${o.filled_shares?.toFixed(2)}sh${o.budget_short_usdc>0?" · SHORT":""}`
   ).join("<br>"):"—";
   return `<tr><td>${esc(m.home)} v ${esc(m.away)}<div class="sub">`+
    `${esc(m.competition||"")} · ${esc(m.match_id)}</div></td>`+
    `<td>${esc(m.kickoff_utc||"")}</td>`+
    `<td>${m.forecast?Object.entries(m.forecast.p).map(([k,v])=>
      `${k} ${(100*v).toFixed(1)}%`).join("<br>"):"—"}</td>`+
    `<td>${pm}</td>`+
    `<td>${pill(d.status||"—",statusClass(d.status))}`+
    `${d.chosen_leg?` · ${esc(d.chosen_leg)}`:""}`+
    `<div class="sub">${esc(d.reason||"")}</div>`+
    `${d.stake_law?`<div class="sub">${esc(d.stake_law)} @ eq `+
     `${esc(d.equity_at_decision_cents??"—")}c</div>`:""}</td>`+
    `<td class="num">${d.stake_cents?money(d.stake_cents):"—"}</td>`+
    `<td>${m.settlement?`${esc(m.settlement.outcome_for_leg)} `+
     `<b>${money(m.settlement.pnl_cents)}</b>`:(m.is_open?pill("OPEN","warn"):"")}`+
    `</td></tr>`;}).join("") ||
  `<tr><td colspan="7" class="muted">no WSL rows in the shared ledger</td></tr>`;
 $("incidents").querySelector("tbody").innerHTML=(S.incidents_tail||[])
  .slice().reverse().map(i=>`<tr><td>${esc(i.ts_utc)}</td>
  <td>${pill(i.kind,(i.kind||"").includes("SETTLE")?"ok":(i.kind||"").includes("BLOCK")?"bad":"warn")}
  </td><td class="sub">${esc(i.detail||"")}</td></tr>`).join("");
 $("foot").innerHTML=`Chain ${S.chain.ok?pill("VERIFIED","ok"):
  pill("TAMPERED","bad")} · ${S.ledger.rows_count} rows · genesis
  ${esc(S.ledger.genesis_at||"—")} · key fingerprint
  ${esc(S.key_fingerprint||"—")} · bind 127.0.0.1 only ·
  PAPER (virtual) money · laws: PLAN_sports_papertrade_v1 +
  ERRATUM_CAPITAL_LAW_V2 + ERRATUM_EXEC_5`;
}
setInterval(tick,AUTO_REFRESH_SECONDS*1000);tick();
</script></body></html>'''


def enrich_matches(rows: list[dict]) -> list[dict]:
    """Group the chain-verified ledger rows into one view per match
    (pure; testable). Rows that never reach a DECISION still appear."""
    order, by_mid = [], {}
    for r in rows:
        mid = r.get("match_id")
        if not mid:
            continue
        if mid not in by_mid:
            by_mid[mid] = {"match_id": mid, "league": r.get("league"),
                           "home": r.get("home"), "away": r.get("away"),
                           "competition": r.get("competition"),
                           "kickoff_utc": r.get("kickoff_utc"),
                           "forecast": None, "quote": None, "decision": None,
                           "settlement": None, "is_open": False,
                           "forecasts": []}
            order.append(mid)
        m = by_mid[mid]
        t = r.get("type")
        if t == "FORECAST":
            m["forecast"] = {"p": r.get("p"), "model": r.get("model_id"),
                             "mode": r.get("mode"),
                             "recorded_at_utc": r.get("recorded_at_utc"),
                             "source_ref": r.get("source_ref")}
            # B1R switch (SOCCER-INTL-B1R-PAPER-SWITCH-V1): keep every
            # forecast per match; when both the B1 control and the B1R
            # treatment are present, expose the draw-probability delta.
            m["forecasts"].append({"p": r.get("p"),
                                   "model": r.get("model_id"),
                                   "recorded_at_utc":
                                       r.get("recorded_at_utc")})
            ps = {f["model"]: (f.get("p") or {}).get("DRAW")
                  for f in m["forecasts"]
                  if f.get("p") and f.get("p").get("DRAW") is not None}
            if "B1_SOCCER" in ps and "B1R_SOCCER" in ps:
                m["draw_delta_b1r_minus_b1"] = (ps["B1R_SOCCER"]
                                                - ps["B1_SOCCER"])
                m["decision_model_id"] = "B1R_SOCCER"
        elif t == "MARKET_QUOTE":
            m["quote"] = {"odds": (r.get("odds") or {}), 
                          "bookmaker": r.get("bookmaker"),
                          "fetch_ts_utc": r.get("fetch_ts_utc"),
                          "source_last_update_utc":
                              r.get("source_last_update_utc")}
            # CAPITAL-V3 §4.5: WSL PM quote rows carry the walked book.
            if r.get("pm_outcomes"):
                m["quote"]["pm_outcomes"] = r.get("pm_outcomes")
                m["quote"]["event_id"] = r.get("event_id")
                m["quote"]["payout_rules"] = r.get("payout_rules")
        elif t == "DECISION":
            m["decision"] = {"status": r.get("status"),
                             "chosen_leg": r.get("chosen_leg"),
                             "stake_cents": r.get("stake_cents"),
                             "ev_net_by_leg": r.get("ev_net_by_leg"),
                             "p_frozen": r.get("p_frozen"),
                             "odds_frozen": r.get("odds_frozen"),
                             "decided_at_utc": r.get("decided_at_utc"),
                             "reason": r.get("reason"),
                             # CAPITAL-V3 §3.6 row fields (v3 rows only)
                             "equity_at_decision_cents":
                                 r.get("equity_at_decision_cents"),
                             "stake_law": r.get("stake_law")}
        elif t == "SETTLEMENT":
            m["settlement"] = {"result": r.get("result"),
                               "outcome_for_leg": r.get("outcome_for_leg"),
                               "pnl_cents": r.get("pnl_cents"),
                               "settled_at_utc": r.get("settled_at_utc"),
                               "source_ref": r.get("source_ref")}
    out = []
    for mid in order:
        m = by_mid[mid]
        d = m["decision"]
        m["is_open"] = bool(d and d["status"] == "BET_PAPER"
                            and not m["settlement"])
        out.append(m)
    return out


def build_state(*, core, ledger_path: str | Path, data_root: Path,
                sandbox: bool, key_fingerprint: str | None,
                heartbeat: dict | None, incidents: list[dict],
                upcoming: list[dict], capital_law: int = 2,
                serve_latency_ms=None) -> dict:
    """Fresh state: re-read + verify the chain FIRST; fail closed on tamper by
    withholding financials (the client renders the alarm banner)."""
    led = core.ledger.PaperLedger(ledger_path).load()
    chain_ok, chain_errs = led.verify_chain()
    genesis = next((r for r in led.rows if r.get("type") == "GENESIS"), {})
    mode = "SANDBOX" if bool(genesis.get("sandbox")) or sandbox else "REAL"
    state: dict = {
        "generated_at_utc": datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": mode,
        "chain": {"ok": bool(chain_ok), "errors": chain_errs[:10]},
        "ledger": {"path": str(ledger_path), "rows_count": len(led.rows),
                   "genesis_at": genesis.get("at_utc"),
                   "wallet_cents": genesis.get("wallet_cents")},
        "key_fingerprint": key_fingerprint,
        "matches": enrich_matches(led.rows) if chain_ok else [],
        "upcoming": upcoming,
        "incidents_tail": incidents[-30:],
        "service": {}, "wallet": {}, "quota": {},
        "serve_latency_ms": serve_latency_ms,
    }
    hb_age = None
    if heartbeat:
        ts = heartbeat.get("ts_utc")
        if ts:
            hb_age = max(0, (datetime.now(timezone.utc) -
                             datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                             .replace(tzinfo=timezone.utc)).total_seconds())
        svc = {k: heartbeat.get(k) for k in
               ("pid", "tick_count", "last_tick_utc", "last_tick_ms",
                "last_cadence_tick_utc", "last_cadence_result",
                "last_settle_tick_utc", "last_dashboard_rebuild_utc",
                "port")}
        svc["heartbeat_age_s"] = hb_age
        state["service"] = svc
    if chain_ok:
        settled_refs = led.settled_decision_refs()
        pnl_by_sport = {"NBA": 0, "SOCCER": 0, "WNBA": 0, "WSL": 0}
        outcomes = {"WIN": 0, "LOSE": 0, "REFUND": 0}
        settled = 0
        for r in led.rows:
            if r.get("type") == "SETTLEMENT":
                settled += 1
                pnl_by_sport[r["league"]] = \
                    pnl_by_sport.get(r["league"], 0) + r["pnl_cents"]
                outcomes[r.get("outcome_for_leg")] = \
                    outcomes.get(r.get("outcome_for_leg"), 0) + 1
        total_pnl = sum(pnl_by_sport.values())
        drawdown = led.drawdown_frac()
        # CAPITAL-V3 §2: the open-cap display follows the RESOLVED law
        # (caller passes capital_law; 2 => 100.00, 3 => 500.00).
        cap_cents = 50_000 if capital_law == 3 else 10_000
        state["wallet"] = {
            "equity_cents": led.equity_cents(),
            "peak_cents": led.equity_peak_cents(),
            "drawdown_frac": drawdown,
            "paused": drawdown >= 0.10,
            "open_exposure_cents": led.open_exposure_cents(),
            "open_exposure_cap_cents": cap_cents,
            "capital_law": ("v3-1pct (stake 1% equity half-up; cap $500 + "
                            "availability)" if capital_law == 3 else
                            "v2 fixed $5 stake; cap $100"),
            "open_count": sum(1 for m in state["matches"] if m["is_open"]),
            "settled_count": settled,
            "total_pnl_cents": total_pnl,
            "sport_pnl_cents": pnl_by_sport,
            "outcomes": outcomes,
        }
    # CAPITAL-V3 §4.5: WSL section rendered from the SHARED ledger's own
    # rows (forecast p x3, walked market/price/fee/depth, decision + precise
    # NOT_RUN reason, stake, PnL) — same chain-verified rows as above; the
    # WSL standalone provenance ledger is NEVER rendered as bets.
    state["wsl"] = [m for m in state["matches"] if m.get("league") == "WSL"]
    qpath = Path(data_root) / "data" / "quota_state.json"
    if qpath.exists():
        state["quota"] = json.loads(qpath.read_text())
    jpath = Path(data_root) / "data" / "quota_journal.jsonl"
    if jpath.exists():
        lines = jpath.read_text().splitlines()[-20:]
        state["quota"]["journal_tail"] = \
            [json.loads(l) for l in lines if l.strip()]
    return state


class _Handler(BaseHTTPRequestHandler):
    state_fn = None                     # injected by serve()

    def log_message(self, *a):          # silence per-request stderr noise
        pass

    def _send(self, code, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, _REFRESH_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path == "/api/state":
            try:
                payload = json.dumps(self.state_fn(), default=str).encode()
                self._send(200, payload, "application/json")
            except Exception as e:                    # fail loud to the page
                self._send(500, json.dumps(
                    {"error": f"{type(e).__name__}: {e}"}).encode(),
                    "application/json")
            return
        if self.path == "/healthz":
            self._send(200, b'{"ok":true}', "application/json")
            return
        self._send(404, b'{"error":"not found"}', "application/json")


def serve(state_fn, port: int = 8791):
    handler = type("BoundHandler", (_Handler,), {"state_fn": staticmethod(state_fn)})
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv
