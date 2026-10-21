"""LIVE local dashboard for SPORTS-PAPERTRADE-EXEC-V1 (ERRATUM_EXEC_5 D-1.3).

Binds 127.0.0.1 ONLY (never a public interface). Every /api/state request
re-reads the ledger from disk, verifies the hash chain, and refuses to render
financials when the chain is tampered (fail-closed alarm instead). The HTML page was REMOVED (W2.3, PAPERDESK-FIXALL-NCAA-V1): the Electron
app is the ONE rendering surface; this server is a state-API read only
(same builder, same ledger). SANDBOX/REAL derives from the GENESIS row's
`sandbox` flag; key bytes never appear here.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AUTO_REFRESH_SECONDS = 8
HEARTBEAT_STALE_S = 180          # LIVE if heartbeat younger than this



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
                desk: dict | None = None,
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
    # W2.4 block 3: the per-league table (one place that shows which league
    # is alive and which is dead, and why) + the W2.4 desk blocks fed by
    # ops_service (stuck queue, CLV plane, per-lane health).
    table: dict = {}
    for m in state["matches"]:
        slot = table.setdefault(m.get("league") or "?", {
            "matches": 0, "decisions": {}, "pnl_cents": 0})
        slot["matches"] += 1
        d = m.get("decision") or {}
        st = d.get("status")
        if st:
            slot["decisions"][st] = slot["decisions"].get(st, 0) + 1
        s = m.get("settlement")
        if s:
            slot["pnl_cents"] += s.get("pnl_cents") or 0
    clv_by_league = ((desk or {}).get("clv") or {}).get("by_league") or {}
    for league, slot in table.items():
        slot["clv_avg_frac"] = (clv_by_league.get(league) or {})\
            .get("clv_avg_frac")
        slot["clv_n"] = (clv_by_league.get(league) or {}).get("n", 0)
    state["desk"] = {
        "stuck": (desk or {}).get("stuck") or [],
        "clv": (desk or {}).get("clv") or {"by_league": {}, "tail": []},
        "health": (desk or {}).get("health") or {"leagues": {}},
        "league_table": table,
    }
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
            # W2.3 (PAPERDESK-FIXALL-NCAA-V1): ONE rendering surface — the
            # Electron app. This endpoint is a READ of the same state API
            # only; the old parallel HTML page is gone (two surfaces
            # building numbers differently was an audit finding).
            self._send(200, json.dumps({
                "surface": "PaperDesk (Electron) is the ONLY rendering "
                           "surface; this endpoint serves the same state "
                           "JSON at /api/state",
                "api": "/api/state"}).encode(), "application/json")
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
