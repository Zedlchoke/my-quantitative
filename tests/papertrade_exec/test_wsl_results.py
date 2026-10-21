"""WSL RESULTS SOURCE V1 battery (owner bug report 2026-10-20 — the six
WSL bets stuck OPEN). Sandbox-only, deterministic, `_gamma_get_json`
stubbed — the real plane is never touched. Covers: FT exactly-one-YES law,
ambiguous/pending/date-mismatch/missing-quote inconclusives, transport
error, journal files, the lane source gate, and an E2E sandbox settle
through the PINNED append-only core (duplicate refused)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tests.papertrade_exec import test_ops_live_service as _ops  # noqa: E402
from research.papertrade_exec import wsl_results                  # noqa: E402
from research.papertrade_exec import wsl_lane                     # noqa: E402
from research.papertrade_exec.ops_service import OpsService       # noqa: E402

env = _ops.env
incidents = _ops.incidents


def _seed_wsl_open_bet(env, *, match_id="FD-TEST-M1", leg="DRAW",
                       kickoff="2026-10-17T11:45:00Z",
                       event_id="1167584", home="Arsenal",
                       away="Birmingham",
                       market_ids=("5528995", "5528996", "5528997")):
    from research.papertrade_exec import execute as _exec
    core = _exec.load_pinned_core(roots={}).ledger.PaperLedger(
        _ops.sandbox_ledger_path(env)).load()
    core.genesis(plan_sha256="wsl-test", sandbox=True)
    outcomes = ["HOME", "DRAW", "AWAY"]
    odds = {"HOME": 1.10, "DRAW": 8.0, "AWAY": 12.0}
    common = {"league": "WSL", "match_id": match_id, "home": home,
              "away": away, "competition": "WSL_LEAGUE",
              "kickoff_utc": kickoff}
    core.append({"type": "FORECAST", **common,
                 "p": {k: 1 / 3 for k in outcomes},
                 "model_id": "TEST", "model_constants": {},
                 "recorded_at_utc": "2026-10-16T00:00:00Z",
                 "mode": "SYNTHETIC", "source_ref": "TEST-SANDBOX"})
    core.append({"type": "MARKET_QUOTE", **common, "event_id": event_id,
                 "odds": odds, "bookmaker": "polymarket",
                 "market": "90min-1X2-YES-binaries",
                 "fetch_ts_utc": "2026-10-16T05:00:00Z",
                 "anchor_utc": kickoff, "payload_sha256": "0" * 64,
                 "key_fingerprint": None,
                 "pm_outcomes": {
                     "HOME": {"market_id": market_ids[0],
                              "token_id_yes": "t-home", "best_ask": 0.9},
                     "DRAW": {"market_id": market_ids[1],
                              "token_id_yes": "t-draw", "best_ask": 0.07},
                     "AWAY": {"market_id": market_ids[2],
                              "token_id_yes": "t-away", "best_ask": 0.058}},
                 "source_ref": "TEST-SANDBOX"})
    core.append({"type": "DECISION", **common,
                 "decided_at_utc": "2026-10-16T05:01:00Z",
                 "model_id": "TEST", "model_constants": {},
                 "stake_cents": 1022, "stake_law": "v3-1pct",
                 "chosen_leg": leg, "p_frozen": {k: 1 / 3
                                                 for k in outcomes},
                 "odds_frozen": odds,
                 "ev_net_by_leg": {k: 0.2 for k in outcomes},
                 "quote_meta": None, "forecast_meta": None,
                 "status": "BET_PAPER", "reason": "TEST-SANDBOX"})
    ledger_rows = [json.loads(l) for l in
                   Path(_ops.sandbox_ledger_path(env)).read_text()
                   .splitlines() if l.strip()]
    open_rows = [r for r in ledger_rows
                 if r.get("type") == "DECISION"
                 and r.get("status") == "BET_PAPER"]
    return core, ledger_rows, open_rows


def _gamma_payload(results, *, question_date="2026-10-17", closed=True,
                   uma="resolved", market_ids=("5528995", "5528996",
                                               "5528997")):
    markets = []
    for i, leg in zip(market_ids, ("HOME", "DRAW", "AWAY")):
        yp = results.get(leg)
        markets.append({
            "id": str(i),
            "question": f"Will the Home side win on {question_date}?"
            if leg == "HOME" else
            f"Will this fixture end in a draw on {question_date}?"
            if leg == "DRAW" else
            f"Will the Away side win on {question_date}?",
            "closed": closed, "umaResolutionStatus": uma,
            "resolvedBy": "0xabc0000000000000000000000000000000000000",
            "outcomes": '["Yes", "No"]',
            "outcomePrices": json.dumps(
                [str(yp), str(round(1.0 - yp, 6))
                 if yp is not None else "0"])})
    return [{"id": "1167584", "title": "Arsenal vs Birmingham",
             "markets": markets}]


def _stub(payload_fn, market_ids=("5528995", "5528996", "5528997"),
          question_date="2026-10-17", closed=True, uma="resolved"):
    def inner(url):
        import json as _json
        markets = []
        markets = []
        for i, leg in zip(market_ids, ("HOME", "DRAW", "AWAY")):
            yp = payload_fn().get(leg)
            qtext = (f"Will the Home side win on {question_date}?"
                     if leg == "HOME" else
                     "Will Arsenal vs Birmingham end in a draw?"
                     if leg == "DRAW" else
                     f"Will the Away side win on {question_date}?")
            markets.append({
                "id": str(i),
                "question": qtext,
                "closed": closed, "umaResolutionStatus": uma,
                "resolvedBy": "0xabc", "outcomes": '["Yes", "No"]',
                "outcomePrices": _json.dumps(
                    [str(yp), str(round(1.0 - yp, 6))
                     if yp is not None else "0"])})
        raw = _json.dumps([{"id": "1167584",
                            "title": "Arsenal vs Birmingham",
                            "markets": markets}]).encode()
        return raw
    wsl_results._gamma_fetch_raw = inner


def test_ft_resolution_draw_is_settleable_with_uma_source_ref(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(env, leg="DRAW")
    _stub(lambda: {"HOME": 0.0, "DRAW": 1.0, "AWAY": 0.0})
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable.get("FD-TEST-M1", {}).get("result") == "DRAW"
    src = settleable["FD-TEST-M1"]["source_ref"]
    assert src.startswith("polymarket_uma event=1167584")
    assert "uma=resolved" in src and "winner=DRAW" in src
    assert inconclusive == []
    jr = env["data"] / "data" / "wsl_results"
    assert len(list(jr.glob("*.json"))) == 1
    assert (jr / "index.jsonl").exists()


def test_home_variant_settles(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(
        env, match_id="M-H", leg="HOME",
        market_ids=("7700001", "7700002", "7700003"))
    _stub(lambda: {"HOME": 1.0, "DRAW": 0.0, "AWAY": 0.0},
      market_ids=("7700001", "7700002", "7700003"))
    try:
        settleable, _inc = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable["M-H"]["result"] == "HOME"


def test_ambiguous_all_no_is_not_settleable(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(env)
    _stub(lambda: {"HOME": 0.0, "DRAW": 0.0, "AWAY": 0.0})
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable == {}
    assert inconclusive and ("ambiguous" in inconclusive[0]["why"]
                             or "finished 90-minute"
                             in inconclusive[0]["why"])


def test_fifty_fifty_is_not_settleable(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(env)
    _stub(lambda: {"HOME": 0.5, "DRAW": 0.5, "AWAY": 0.5})
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable == {} and inconclusive


def test_pending_uma_is_not_settleable(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(env)
    _stub(lambda: {"HOME": 0.0, "DRAW": 1.0, "AWAY": 0.0},
      closed=False, uma="pending")
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable == {}
    assert "finished 90-minute" in inconclusive[0]["why"]


def test_question_date_mismatch_is_not_settleable(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(env)
    _stub(lambda: {"HOME": 0.0, "DRAW": 1.0, "AWAY": 0.0},
      question_date="2026-11-17")
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable == {} and inconclusive


def test_missing_quote_row_is_inconclusive(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(env)
    ledger_rows = [r for r in ledger_rows
                   if r.get("type") != "MARKET_QUOTE"]
    settleable, inconclusive = wsl_results.fetch_wsl_settleable(
        rows=open_rows, ledger_rows=ledger_rows,
        data_root=env["data"], sandbox=True)
    assert settleable == {}
    assert "identity unresolved" in inconclusive[0]["why"]


def test_crosswalk_and_ampersand_resolves(env):
    """PM title uses 'Brighton and Hove Albion WFC'; ledger stores
    'Brighton & Hove Albion' — the PINNED crosswalk inversion resolves it."""
    _, ledger_rows, open_rows = _seed_wsl_open_bet(
        env, match_id="FD-TEST-M38", leg="HOME", home="Manchester City",
        away="Brighton & Hove Albion",
        market_ids=("5575282", "5575283", "5575284"))
    def raw(url):
        import json as _json
        markets = []
        for i, leg in zip(("5575282", "5575283", "5575284"),
                          ("HOME", "DRAW", "AWAY")):
            yp = {"HOME": 1.0, "DRAW": 0.0, "AWAY": 0.0}[leg]
            q = (f"Will Manchester City WFC win on 2026-10-18?" if leg ==
                 "HOME" else
                 "Will Manchester City WFC vs. Brighton and Hove Albion WFC "
                 "end in a draw?" if leg == "DRAW" else
                 "Will Brighton and Hove Albion WFC win on 2026-10-18?")
            markets.append({"id": str(i), "question": q, "closed": True,
                            "umaResolutionStatus": "resolved",
                            "resolvedBy": "0xabc",
                            "outcomes": '["Yes", "No"]',
                            "outcomePrices": _json.dumps(
                                [str(yp), str(round(1.0 - yp, 6))])})
        return _json.dumps([{
            "id": "1172253",
            "title": "Manchester City WFC vs. Brighton and Hove Albion WFC",
            "markets": markets}]).encode()
    wsl_results._gamma_fetch_raw = raw
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable.get("FD-TEST-M38", {}).get("result") == "HOME", (
        settleable, inconclusive)
    assert inconclusive == []


def test_gamma_transport_error_raises(env):
    _, ledger_rows, open_rows = _seed_wsl_open_bet(env)
    def stub(url):
        raise RuntimeError("network down")
    wsl_results._gamma_fetch_raw = stub
    try:
        with pytest.raises(RuntimeError):
            wsl_results.fetch_wsl_settleable(
                rows=open_rows, ledger_rows=ledger_rows,
                data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None


def test_lane_gate_refuses_foreign_source_file(env, tmp_path):
    results = tmp_path / "r.json"
    results.write_text(json.dumps(
        {"FD-X": {"result": "HOME", "source_ref": "espn guess"}}))
    with pytest.raises(Exception) as ei:
        wsl_lane.cmd_settle(type("A", (), {
            "results": str(results), "league": "WSL",
            "date": "2026-10-17"}))
    assert "BLOCKED_NO_RESULTS_SOURCE" in str(ei.value)
    results.write_text(json.dumps(
        {"FD-X": {"result": "HOME",
                  "source_ref": "polymarket_uma event=1167584 "
                                "winner=HOME"}}))
    try:
        wsl_lane.cmd_settle(type("A", (), {
            "results": str(results), "league": "WSL",
            "date": "2026-10-17"}))
        blocked = False
    except Exception as exc:
        blocked = "BLOCKED_NO_RESULTS_SOURCE" in str(exc)
        assert blocked is False, "unexpected gate refusal: " + str(exc)


def test_e2e_sandbox_settle_through_pinned_core(env, monkeypatch):
    from research.papertrade_exec import wsl_results, execute
    core, ledger_rows, open_rows = _seed_wsl_open_bet(env, leg="DRAW")
    before = len(core.rows)
    _stub(lambda: {"HOME": 0.0, "DRAW": 1.0, "AWAY": 0.0})
    svc = OpsService(data_root=env["data"], sandbox=True, serve=False,
                     once=True)
    svc.grace_hours = 0
    svc.settle_throttle_bypass = True
    out = svc.settle_pass()
    assert out["settled"] == 1, out
    rows = _ops.ledger_rows(env)
    settlements = [r for r in rows if r.get("type") == "SETTLEMENT"]
    assert len(settlements) == 1
    st = settlements[0]
    assert st["result"] == "DRAW" and st["outcome_for_leg"] == "WIN"
    assert st["chosen_leg"] == "DRAW"
    assert st["source_ref"].startswith("polymarket_uma event=")
    dec = next(r for r in rows if r.get("type") == "DECISION"
               and r.get("match_id") == "FD-TEST-M1")
    d_eff = dec["odds_frozen"]["DRAW"]
    assert st["pnl_cents"] == int(round(1022 * (d_eff - 1.0)))
    from research.papertrade_exec import execute as _exec
    fresh = _exec.load_pinned_core(roots={}).ledger.PaperLedger(
        _ops.sandbox_ledger_path(env)).load()
    ok, errs = fresh.verify_chain()
    assert ok and len(fresh.rows) == before + 1
    # idempotence: a second settle pass settles NOTHING (the pinned core's
    # settled_decision_refs mark the decision; duplicate is refused)
    out2 = svc.settle_pass()
    assert out2["settled"] == 0
    assert len([r for r in _ops.ledger_rows(env)
                if r.get("type") == "SETTLEMENT"]) == 1


def test_classify_open_bets_stale_corpus_law():
    """Owner DoD 2026-10-21: past-kickoff WSL bets without a clean UMA
    resolution surface STALE_CORPUS — never fabricated from W/D/L."""
    from research.papertrade_exec import wsl_results as WR
    led_rows = [{"type": "MARKET_QUOTE", "league": "WSL",
                 "match_id": "M1", "event_id": "1172249",
                 "pm_outcomes": {"HOME": {"market_id": 1},
                                 "DRAW": {"market_id": 2},
                                 "AWAY": {"market_id": 3}}},
                {"type": "MARKET_QUOTE", "league": "WSL",
                 "match_id": "M2", "event_id": "1172253",
                 "pm_outcomes": {"HOME": {"market_id": 4},
                                 "DRAW": {"market_id": 5},
                                 "AWAY": {"market_id": 6}}}]
    rows = [
        {"match_id": "M1", "kickoff_utc": "2026-10-17T14:00:00Z"},   # past+grace
        {"match_id": "M2", "kickoff_utc": "2099-01-01T14:00:00Z"},   # future
        {"match_id": "M3", "kickoff_utc": "2026-10-17T14:00:00Z"},   # no quote row
    ]
    got = {h["match_id"]: h["status"] for h in WR.classify_open_bets(
        rows=rows, ledger_rows=led_rows, now_utc="2026-10-21T00:00:00Z")}
    assert got["M1"] == "STALE_CORPUS"
    assert got["M2"] == "AWAITING_KICKOFF"
    assert got["M3"] == "IDENTITY_UNRESOLVED"
