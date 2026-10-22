"""PAPERDESK-FIXALL-NCAA-V1 — W4 battery: THE single AI authority gate.

W4.1  one gate on BOTH decide paths (standard + WSL); legacy JS/Python
      evaluators are unwired;
W4.2  opinions are hash-locked to the exact candidate — price/EV/model
      change => new hash => stale review void;
W4.3  STRICT {verdict: ALLOW|VETO} schema; SWITCH/CHALLENGE/ALTERNATIVE/
      ABSTAIN/garbage are INVALID and never actionable; ALLOW with zero
      captured sources is invalid (insufficient evidence is a refusal);
W4.4  silence law: no valid verdict inside the window => PENDING_AI (the
      candidate stays UNDECIDED — retried, never killed); past
      anchor-30m => NOT_PLACED_AI_NO_VERDICT; >30min pending => owner
      alarm;
W4.5  scorecard: ALLOW-placed realized vs VETO hypothetical, net value,
      suggest-only downgrade after >= 100 scored;
W4.6  provider/prompt via config; prompt frozen by version + sha.
"""
from __future__ import annotations

import argparse
import json
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tests.papertrade_exec import test_ops_live_service as _ops  # noqa: E402
from tests.papertrade_exec import test_fixall_w1 as W1           # noqa: E402
from research.papertrade_exec import ai_gate_v2 as G             # noqa: E402
from research.papertrade_exec import ai_scorecard                # noqa: E402
from research.papertrade_exec import execute                     # noqa: E402
from research.papertrade_exec.ai_producer import registered_prompt_sha  # noqa: E402


def _reg_sha():
    return registered_prompt_sha(REPO)[0]

env = _ops.env
incidents = _ops.incidents
ledger_rows = _ops.ledger_rows
make_svc = _ops.make_svc

FX = W1.FX


def _bet_dec(env, ev=0.06):
    # the shape the pinned risk.evaluate_match emits (type included)
    return {"type": "DECISION", "league": FX.league,
            "match_id": FX.match_id, "competition": FX.competition,
            "home": FX.home, "away": FX.away,
            "kickoff_utc": FX.kickoff_utc,
            "decided_at_utc": "2026-10-08T10:00:00Z",
            "status": "BET_PAPER", "chosen_leg": "HOME",
            "stake_cents": 500, "p_frozen": {"HOME": 0.55},
            "odds_frozen": {"HOME": 2.0},
            "ev_net_by_leg": {"HOME": ev, "AWAY": -0.1},
            "equity_at_decision_cents": 100000,
            "anchor_utc": "2026-10-08T12:50:00Z", "reason": "t",
            "model_id": "T", "model_constants": {}}


def _fc_row():
    return {"row_sha256": "c" * 64, "anchor_utc": "2026-10-08T12:50:00Z"}


def _quote_row():
    return {"payload_sha256": "d" * 64, "market": "h2h",
            "odds": {"HOME": 2.0, "AWAY": 1.9}}


def _decide_args(env, flag=True):
    args = argparse.Namespace(**dict(W1.DEC_ARGS, data_root=str(env["data"])))
    args.sandbox = True
    with mock.patch.object(execute, "papertrade_flags",
                           return_value={"pm_cutover_active": False,
                                         "ai_authority_active": flag}):
        yield args


def _run_decide(env, led, evaluate, flag=True):
    core = types.SimpleNamespace(
        risk=types.SimpleNamespace(
            evaluate_match=evaluate,
            in_lock_recheck=lambda led_, now, ok, capital_law=2:
                (lambda d: d)),
        stake_for_decision=lambda eq: 500)
    gen = _decide_args(env, flag)
    args = next(gen)
    with mock.patch.object(execute, "papertrade_flags",
                           return_value={"pm_cutover_active": False,
                                         "ai_authority_active": flag}), \
         mock.patch.object(execute, "require_gate",
                           return_value=(True, "", None)), \
         mock.patch.object(execute, "verify_pins", return_value={}), \
         mock.patch.object(execute, "open_ledger",
                           return_value=(core, led)), \
         mock.patch.object(execute, "fixtures_for",
                           return_value=[FX]), \
         mock.patch.object(execute, "capital_law_for", return_value=2):
        return execute.cmd_decide(args)


def _ledger_fc_qt(led, match_id="m1"):
    fc = next(r for r in led.rows if r.get("type") == "FORECAST"
              and r.get("match_id") == match_id)
    qt = next(r for r in led.rows if r.get("type") == "MARKET_QUOTE"
              and r.get("match_id") == match_id)
    return fc, qt


def _write_opinion(env, led, dec, verdict, *, sources=("https://x",),
                   reason=None, match_id="m1"):
    fc, qt = _ledger_fc_qt(led, match_id)
    chash = G.candidate_hash_for(dec, fc, qt)
    op = {"match_id": FX.match_id, "candidate_hash": chash,
          "verdict": verdict,
          "reason_codes": reason or [f"R-{verdict}"],
          "summary": "reviewed; captured sources checked",
          "sources": [{"url": u, "fetched_at_utc": "2026-10-08T09:00:00Z",
                       "excerpt": "headline"} for u in sources],
          "model_id": "test-model", "provider": "test",
          "prompt_version": "AI_PROMPT_V2",
          "prompt_sha256": _reg_sha(),
          "created_at_utc": "2026-10-08T09:00:00Z"}
    # U4-M6: the sandbox decide consumes the SANDBOX ai_review plane —
    # a plumbing arg only; the opinion schema/semantics are untouched.
    G.record_opinion(env["data"], op, sandbox=True)
    return chash


# ------------------------------------------------------------------ schema --

def test_v2_schema_two_verdicts_only(env):
    base = {"match_id": "m1", "candidate_hash": "h" * 64,
            "reason_codes": ["R"], "summary": "s", "sources": [
                {"url": "https://x", "fetched_at_utc": "t",
                 "excerpt": "e"}],
            "prompt_sha256": _reg_sha()}
    ok, why = G.validate_opinion({**base, "verdict": "ALLOW"})
    assert ok, why
    ok, why = G.validate_opinion({**base, "verdict": "VETO"})
    assert ok, why
    for bad in ("SWITCH", "CHALLENGE", "ALTERNATIVE", "ABSTAIN", "KEEP",
                "APPROVE", ""):
        ok, why = G.validate_opinion({**base, "verdict": bad})
        assert not ok
    ok, why = G.validate_opinion({**base, "verdict": "ALLOW",
                                  "sources": []})
    assert not ok and "insufficient evidence" in why
    ok, why = G.validate_opinion({**base, "verdict": "ALLOW",
                                  "sources": [{"fetched_at_utc": "t"}]})
    assert not ok and "url" in why


# ------------------------------------------------------------------ W4.2 ----

def test_opinion_hash_lock_voids_stale_review(env):
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    dec = _bet_dec(env)
    chash = _write_opinion(env, led, dec, "ALLOW")
    op, why = G.load_opinion_for(env["data"], "m1", chash, sandbox=True)
    assert op and op["verdict"] == "ALLOW"
    # price moves => new hash => the old review is VOID
    qt2 = {**_quote_row(), "payload_sha256": "e" * 64}
    op2, why2 = G.load_opinion_for(env["data"], "m1",
                                   G.candidate_hash_for(dec, _fc_row(), qt2),
                                   sandbox=True)
    assert op2 is None and "no opinion bound" in why2


# ------------------------------------------------------------------ W4.4 ----

def test_decide_allow_places_with_evidence_block(env):
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    dec = _bet_dec(env)
    _write_opinion(env, led, dec, "ALLOW")
    out = _run_decide(env, led, lambda *a, **k: dict(dec))
    assert out["journaled"][0]["status"] == "BET_PAPER"
    row = next(r for r in led.rows if r.get("type") == "DECISION"
               and r.get("status") == "BET_PAPER")
    assert row["ai_gate"]["decision"] == "PLACE"
    assert row["ai_gate"]["opinion_verdict"] == "ALLOW"
    assert row["ai_gate"]["candidate_hash"]
    # pending queue cleared
    assert G._load_pending(env["data"], sandbox=True) == {}


def test_decide_veto_blocks_with_hypothetical_evidence(env):
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    dec = _bet_dec(env)
    _write_opinion(env, led, dec, "VETO", reason=["INJURY_RISK"])
    out = _run_decide(env, led, lambda *a, **k: dict(dec))
    assert out["journaled"][0]["status"] == "NOT_PLACED_AI_VETO"
    row = next(r for r in led.rows if r.get("status") == "NOT_PLACED_AI_VETO")
    assert row["ai_gate"]["hypothetical_stake_cents"] == 500
    assert row["ai_gate"]["hypothetical_decimal_odds"] == 2.0
    assert not [r for r in led.rows if r.get("status") == "BET_PAPER"]


def test_decide_silence_is_pending_then_no_verdict(env):
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    # (a) inside the window (now << anchor-30m): PENDING — the candidate
    # stays UNDECIDED, nothing is appended, the queue records it
    out = _run_decide(env, led, lambda *a, **k: dict(_bet_dec(env)))
    assert out["journaled"][0]["status"] == "PENDING_AI"
    assert not [r for r in led.rows if r.get("type") == "DECISION"]
    pending = G._load_pending(env["data"], sandbox=True)
    assert "m1" in pending and pending["m1"]["attempts"] == 1
    # (b) garbage verdict (SWITCH) is INVALID => still pending
    fc_l, qt_l = _ledger_fc_qt(led)
    chash = G.candidate_hash_for(_bet_dec(env), fc_l, qt_l)
    bad_dir = env["data"] / "sandbox" / "ai_review" / "opinions_v2"
    bad_dir.mkdir(parents=True, exist_ok=True)
    (bad_dir / f"m1_{chash}.json").write_text(json.dumps(
        {"match_id": "m1", "candidate_hash": chash, "verdict": "SWITCH",
         "reason_codes": ["R"], "summary": "s", "sources": [],
         "prompt_sha256": "b" * 64}))
    out = _run_decide(env, led, lambda *a, **k: dict(_bet_dec(env)))
    assert out["journaled"][0]["status"] == "PENDING_AI"
    assert not [r for r in led.rows if r.get("type") == "DECISION"]
    # (c) past the deadline => terminal NOT_PLACED_AI_NO_VERDICT
    _ops.sandbox_ledger_path(env).unlink()   # fresh ledger for part (c)
    led2 = W1._sandbox_ledger(env)
    W1._seed_chain(led2, "m1", kickoff="2026-10-08T01:00:00Z")
    # the seed hardcodes a future anchor — force it into the past so part
    # (c) exercises the post-deadline branch
    next(r for r in led2.rows if r.get("type") == "FORECAST")[
        "anchor_utc"] = "2026-10-08T00:10:00Z"
    fc = {**_fc_row(), "anchor_utc": "2026-10-08T00:10:00Z"}
    dec2 = {**_bet_dec(env), "anchor_utc": "2026-10-08T00:10:00Z"}
    fx_past = type(FX)("NBA", "m1", "Detroit Pistons", "Boston Celtics",
                       "2026-10-08T01:00:00Z", "NBA", "2026-10-08", "T")
    core = types.SimpleNamespace(
        risk=types.SimpleNamespace(
            evaluate_match=lambda *a, **k: dict(dec2),
            in_lock_recheck=lambda led_, now, ok, capital_law=2:
                (lambda d: d)),
        stake_for_decision=lambda eq: 500)
    args = next(_decide_args(env, flag=True))
    with mock.patch.object(execute, "papertrade_flags",
                           return_value={"pm_cutover_active": False,
                                         "ai_authority_active": True}), \
         mock.patch.object(execute, "require_gate",
                           return_value=(True, "", None)), \
         mock.patch.object(execute, "verify_pins", return_value={}), \
         mock.patch.object(execute, "open_ledger",
                           return_value=(core, led2)), \
         mock.patch.object(execute, "fixtures_for",
                           return_value=[fx_past]), \
         mock.patch.object(execute, "capital_law_for", return_value=2):
        out = execute.cmd_decide(args)
    assert out["journaled"][0]["status"] == "NOT_PLACED_AI_NO_VERDICT"
    row = next(r for r in led2.rows
               if r.get("status") == "NOT_PLACED_AI_NO_VERDICT")
    assert row["stake_cents"] == 0
    assert G._load_pending(env["data"], sandbox=True) == {}


def test_provider_down_alarm(env):
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    out = _run_decide(env, led, lambda *a, **k: dict(_bet_dec(env)))
    assert out["journaled"][0]["status"] == "PENDING_AI"
    # age the pending entry beyond the 30-minute alarm law
    pending = G._load_pending(env["data"], sandbox=True)
    pending["m1"]["first_pending_utc"] = (
        datetime.now(timezone.utc) - timedelta(minutes=45)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    G._save_pending(env["data"], pending, sandbox=True)
    svc = make_svc(env)
    svc._ai_pending_watch()
    kinds = [i["kind"] for i in incidents(env)]
    assert "AI_PROVIDER_DOWN" in kinds
    svc._ai_pending_watch()                  # once per day per entry
    assert kinds.count("AI_PROVIDER_DOWN") == 1


# ------------------------------------------------------------------ W4.1 ----

def test_legacy_evaluators_unwired_from_decide(env):
    """The decide path must never consult the legacy evaluators (the v2
    gate is the only authority)."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    dec = _bet_dec(env)
    _write_opinion(env, led, dec, "ALLOW")

    def forbidden(*a, **k):
        raise AssertionError("legacy AI evaluator called from decide")

    with mock.patch.object(execute, "load_ai_opinion", forbidden), \
         mock.patch.object(execute, "ai_boundary_review", forbidden):
        out = _run_decide(env, led, lambda *a, **k: dict(dec))
    assert out["journaled"][0]["status"] == "BET_PAPER"


def test_gate_off_is_byte_identical(env):
    """Flag OFF => no gate artifacts at all (DISABLED law)."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    out = _run_decide(env, led, lambda *a, **k: dict(_bet_dec(env)),
                      flag=False)
    assert out["journaled"][0]["status"] == "BET_PAPER"
    row = next(r for r in led.rows if r.get("status") == "BET_PAPER")
    assert "ai_gate" not in row
    assert G._load_pending(env["data"]) == {}


# ------------------------------------------------------------------ W4.5 ----
# U2 truth laws: veto ACTUAL results come from the results plane (ledger
# SETTLEMENT first, then the caller's results_by_mid); a veto with no
# obtainable final result is UNSCORED and excluded from the downgrade
# denominator; the TOP-LINE value is ai_layer_value = −vetoed_hypothetical;
# the downgrade gate counts veto_scored_actual only (DOWNGRADE_MIN_SCORED).

def _sc_opinions(tmp, specs, *, model="test-model"):
    d = tmp / "opinions_v2"
    d.mkdir(parents=True, exist_ok=True)
    for h, v in specs:
        (d / f"op_{h}.json").write_text(json.dumps(
            {"candidate_hash": h, "verdict": v,
             "reason_codes": ["INJURY_RISK"] if v == "VETO" else ["FORM"],
             "summary": "reviewed", "model_id": model,
             "created_at_utc": "2026-10-21T00:00:00Z"}))
    return d


def _sc_rows():
    return [
        {"type": "GENESIS", "row_sha256": "0" * 64},
        # ALLOW-placed WIN
        {"type": "DECISION", "league": "NBA", "match_id": "m1",
         "status": "BET_PAPER", "row_sha256": "a" * 64,
         "ai_gate": {"candidate_hash": "h1", "verdict": "ALLOW"}},
        {"type": "MARKET_QUOTE", "match_id": "m1", "odds": {"HOME": 2.0}},
        {"type": "SETTLEMENT", "match_id": "m1", "result": "HOME",
         "pnl_cents": 500, "decision_row_sha256": "a" * 64},
        # VETO that WOULD have lost (AI kept money): settle law HAND MATH:
        # leg HOME d=2.0, actual AWAY -> lose -> −stake = −500c
        {"type": "DECISION", "league": "NBA", "match_id": "m2",
         "status": "NOT_PLACED_AI_VETO", "row_sha256": "b" * 64,
         "stake_cents": 0,
         "ai_gate": {"candidate_hash": "h2", "verdict": "VETO",
                     "hypothetical_leg": "HOME",
                     "hypothetical_stake_cents": 500,
                     "hypothetical_decimal_odds": 2.0}},
        {"type": "SETTLEMENT", "match_id": "m2", "result": "AWAY"},
        # VETO that WOULD have won (AI cost money): leg HOME d=3.0, actual
        # HOME -> win -> +stake·(d−1) = 500·2 = +1000c
        {"type": "DECISION", "league": "NBA", "match_id": "m3",
         "status": "NOT_PLACED_AI_VETO", "row_sha256": "c" * 64,
         "stake_cents": 0,
         "ai_gate": {"candidate_hash": "h3", "verdict": "VETO",
                     "hypothetical_leg": "HOME",
                     "hypothetical_stake_cents": 500,
                     "hypothetical_decimal_odds": 3.0}},
        {"type": "SETTLEMENT", "match_id": "m3", "result": "HOME"},
    ]


def test_scorecard_allow_vs_veto_and_downgrade_suggestion(tmp_path):
    rows = _sc_rows()
    opdir = _sc_opinions(tmp_path, (("h1", "ALLOW"), ("h2", "VETO"),
                                    ("h3", "VETO")))
    sc = ai_scorecard.compute_scorecard(ledger_rows=rows,
                                        opinions_dir=opdir,
                                        min_scored_for_downgrade=2)
    assert sc["schema"] == "ai_scorecard@2"
    assert sc["reviews_scored"] == 3          # 1 settled ALLOW + 2 scored vetoes
    assert sc["allow_placed"] == 1
    assert sc["allow_settled"] == 1
    assert sc["veto_reviewed"] == 2
    assert sc["veto_scored_actual"] == 2      # the U2 downgrade denominator
    assert sc["placed_realized_pnl_cents"] == 500
    # vetoed set: m2 would have lost (−500), m3 would have won (+1000)
    assert sc["vetoed_hypothetical_pnl_cents"] == 500
    assert sc["net_value_of_ai_layer_cents"] == 0     # data: 500 − 500
    assert sc["downgrade_proposal"]["eligible"] is True
    assert sc["downgrade_proposal"]["suggest_demote_to_shadow"] is True
    assert sc["downgrade_proposal"]["denominator"] == {
        "veto_scored_actual": 2, "unscored_vetoes_excluded": 0}
    # U2 breakdowns
    assert sc["per_league"]["NBA"]["veto_scored"] == 2
    assert sc["per_league"]["NBA"]["allow_placed"] == 1
    assert sc["per_model"]["test-model"]["veto"] == 2
    assert sc["per_reason_code"]["codes"].get("INJURY_RISK") == 2


def test_scorecard_veto_without_result_is_unscored_not_denominator(tmp_path):
    """U2 law 1: a blocked match never settles (H2 root) — with no
    settlement and nothing on the results plane, the veto is UNSCORED:
    excluded from reviews_scored and from the downgrade denominator,
    reported separately."""
    rows = _sc_rows()
    # m3's settlement removed: the veto has no obtainable final result
    rows = [r for r in rows
            if not (r.get("type") == "SETTLEMENT"
                    and r.get("match_id") == "m3")]
    opdir = _sc_opinions(tmp_path, (("h1", "ALLOW"), ("h2", "VETO"),
                                    ("h3", "VETO")))
    sc = ai_scorecard.compute_scorecard(ledger_rows=rows,
                                        opinions_dir=opdir,
                                        min_scored_for_downgrade=2)
    assert sc["veto_scored_actual"] == 1          # only m2
    assert sc["unscored_vetoes"] == 1
    assert sc["unscored_veto_match_ids"] == ["m3"]
    assert sc["reviews_scored"] == 2              # 1 ALLOW + 1 scored veto
    assert sc["vetoed_hypothetical_pnl_cents"] == -500   # m2 only
    # denominator = veto_scored_actual (1) < 2: gate stays INELIGIBLE even
    # though a naive count of all vetoes (2) would have crossed it
    assert sc["downgrade_proposal"]["eligible"] is False
    assert sc["downgrade_proposal"]["scored"] == 1
    # the results-plane parameter rescues the veto: U2 law 1 second source
    sc2 = ai_scorecard.compute_scorecard(
        ledger_rows=rows, opinions_dir=opdir,
        min_scored_for_downgrade=2, results_by_mid={"m3": "HOME"})
    assert sc2["veto_scored_actual"] == 2
    assert sc2["unscored_vetoes"] == 0
    assert sc2["vetoed_hypothetical_pnl_cents"] == 500   # −500 + 1000
    assert sc2["downgrade_proposal"]["eligible"] is True


def test_scorecard_ai_layer_value_sign_law(tmp_path):
    """U2 law 2 headline: ai_layer_value = −vetoed_hypothetical.
    Vetoes that would have LOST => positive (AI saved); vetoes that would
    have WON => negative (AI cost)."""
    opdir = _sc_opinions(tmp_path, (("h1", "ALLOW"), ("h2", "VETO"),
                                    ("h3", "VETO")))
    saved = ai_scorecard.compute_scorecard(
        ledger_rows=[r for r in _sc_rows()
                     if not (r.get("type") == "SETTLEMENT"
                             and r.get("match_id") == "m3")],
        opinions_dir=opdir)
    assert saved["vetoed_hypothetical_pnl_cents"] == -500
    assert saved["ai_layer_value_cents"] == 500          # the AI SAVED 500c
    cost = ai_scorecard.compute_scorecard(
        ledger_rows=[r for r in _sc_rows()
                     if not (r.get("type") == "SETTLEMENT"
                             and r.get("match_id") == "m2")],
        opinions_dir=opdir)
    assert cost["vetoed_hypothetical_pnl_cents"] == 1000
    assert cost["ai_layer_value_cents"] == -1000         # the AI COST 1000c


def test_scorecard_no_verdict_counting(tmp_path):
    """U2 law 3: NOT_PLACED_AI_NO_VERDICT rows are their own class —
    counted with their hypothetical PnL when the frozen gate-block
    evidence shape is present; never in the veto denominator."""
    rows = _sc_rows()
    # a no-verdict row WITH the hypothetical evidence shape, result on the
    # plane: leg AWAY d=2.0, actual HOME -> lose -> −500c
    rows.append({"type": "DECISION", "league": "NBA", "match_id": "m4",
                 "status": "NOT_PLACED_AI_NO_VERDICT",
                 "row_sha256": "d" * 64, "stake_cents": 0,
                 "ai_gate": {"candidate_hash": "h4",
                             "hypothetical_leg": "AWAY",
                             "hypothetical_stake_cents": 500,
                             "hypothetical_decimal_odds": 2.0}})
    rows.append({"type": "DECISION", "league": "NBA", "match_id": "m5",
                 "status": "NOT_PLACED_AI_NO_VERDICT",
                 "row_sha256": "e" * 64, "stake_cents": 0,
                 "ai_gate": {"candidate_hash": "h5"}})   # no evidence shape
    opdir = _sc_opinions(tmp_path, (("h1", "ALLOW"), ("h2", "VETO"),
                                    ("h3", "VETO")))
    # a blocked match never settles (H2 root): m4's final result arrives on
    # the RESULTS PLANE (the caller's results_by_mid, e.g. ESPN/UMA)
    sc = ai_scorecard.compute_scorecard(
        ledger_rows=rows, opinions_dir=opdir,
        results_by_mid={"m4": "HOME"})
    nv = sc["not_placed_no_verdict"]
    assert nv["count"] == 2
    assert nv["with_evidence_shape"] == 1
    assert nv["scored_hypothetical"] == 1
    assert nv["hypothetical_pnl_cents"] == -500   # AWAY d=2.0 vs HOME: lose
    assert sorted(nv["match_ids"]) == ["m4", "m5"]
    # the class never enters the scored reviews or the veto denominator
    assert sc["veto_scored_actual"] == 2
    assert sc["reviews_scored"] == 3


def test_scorecard_invalid_opinions_and_gate_events(tmp_path):
    """U2 law 3: invalid opinions (opinions_v2/.invalid/*.json) counted;
    gate_events.jsonl aggregated to verdicts-per-model."""
    opdir = _sc_opinions(tmp_path, (("h1", "ALLOW"), ("h2", "VETO"),
                                    ("h3", "VETO")))
    bad = opdir / ".invalid"
    bad.mkdir(exist_ok=True)
    (bad / "m9_bad1.json").write_text(json.dumps({"invalid_reason": "x"}))
    (bad / "m9_bad2.json").write_text(json.dumps({"invalid_reason": "y"}))
    (bad / "notes.txt").write_text("not an opinion")     # must NOT count
    gev = tmp_path / "gate_events.jsonl"
    lines = [
        {"ts_utc": "t1", "kind": "PENDING_AI", "match_id": "m1"},
        {"ts_utc": "t2", "kind": "OPINION_PRODUCED", "match_id": "m1",
         "verdict": "ALLOW", "model": "minimax/x"},
        {"ts_utc": "t3", "kind": "OPINION_PRODUCED", "match_id": "m2",
         "verdict": "VETO", "model": "minimax/x"},
        {"ts_utc": "t4", "kind": "OPINION_PRODUCED", "match_id": "m3",
         "verdict": "ALLOW", "model": "fallback/y"},
        {"ts_utc": "t5", "kind": "PROVIDER_FAILED", "match_id": "m4"},
    ]
    gev.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    sc = ai_scorecard.compute_scorecard(
        ledger_rows=_sc_rows(), opinions_dir=opdir, gate_events_path=gev)
    assert sc["invalid_opinions"] == 2
    ge = sc["gate_events"]
    assert ge["read"] is True and ge["total"] == 5
    assert ge["kinds"]["OPINION_PRODUCED"] == 3
    assert ge["kinds"]["PROVIDER_FAILED"] == 1
    assert ge["verdicts_by_model"] == {
        "fallback/y": {"ALLOW": 1}, "minimax/x": {"ALLOW": 1, "VETO": 1}}
    # no journal passed => honest empty read, never a crash
    sc2 = ai_scorecard.compute_scorecard(ledger_rows=_sc_rows(),
                                         opinions_dir=opdir)
    assert sc2["gate_events"]["read"] is False
    assert sc2["gate_events"]["total"] == 0


# ------------------------------------------------------------------ W4.6 ----

def test_provider_and_prompt_frozen_by_config():
    node = pytest.importorskip("subprocess")
    import subprocess
    # the LAW is "provider/prompt frozen BY CONFIG" (W4.6): the producer
    # must use exactly the configured model_id — the concrete model value
    # is config state (owner-tunable), never hardcoded in the test
    cfg = json.loads((REPO / "research" / "papertrade_exec" /
                      "config.json").read_text())
    cfg_model = (cfg.get("ai_provider") or {}).get("model_id")
    assert cfg_model
    script = (
        "const P = require('./apps/paperdesk/main/ai_v2_producer.js');"
        "const cfg = P.loadProviderConfig('.');"
        "const prompt = P.frozenPrompt('.', cfg);"
        "console.log(JSON.stringify({model: cfg.model_id,"
        " version: prompt.version, sha: prompt.sha256,"
        " hasTwoVerdicts: P.VERDICTS_V2.join() === 'ALLOW,VETO'}));"
    )
    out = subprocess.run(["node", "-e", script], capture_output=True,
                         text=True, cwd=REPO, timeout=60)
    assert out.returncode == 0, out.stderr
    payload = json.loads(out.stdout.strip().splitlines()[-1])
    assert payload["hasTwoVerdicts"] is True
    assert payload["version"] == "AI_PROMPT_V2"
    assert len(payload["sha"]) == 64
    assert payload["model"] == cfg_model   # frozen BY CONFIG (whatever it is)


def test_js_parse_v2_rejects_switch_and_empty_allow():
    import subprocess
    script = (
        "const P = require('./apps/paperdesk/main/ai_v2_producer.js');"
        "const bad = P.parseV2('{\"verdict\":\"SWITCH\",\"reason_codes\":"
        "[\"R\"],\"summary\":\"s\"}');"
        "const emptyAllow = P.parseV2('{\"verdict\":\"ALLOW\","
        "\"reason_codes\":[\"R\"],\"summary\":\"s\",\"sources\":[]}');"
        "const ok = P.parseV2('{\"verdict\":\"ALLOW\",\"reason_codes\":"
        "[\"R\"],\"summary\":\"s\",\"sources\":[{\"url\":"
        "\"https://x\"}]}');"
        "console.log(JSON.stringify({bad: bad.ok, emptyAllow: emptyAllow.ok,"
        " ok: ok.ok, okVerdict: ok.verdict}));"
    )
    out = subprocess.run(["node", "-e", script], capture_output=True,
                         text=True, cwd=REPO, timeout=60)
    assert out.returncode == 0, out.stderr
    payload = json.loads(out.stdout.strip().splitlines()[-1])
    assert payload == {"bad": False, "emptyAllow": False, "ok": True,
                       "okVerdict": "ALLOW"}


# ------------------------------------------------- A7 remediation checks ----

def test_a7_m2_league_pause_law(env):
    """QD1: a paused league refuses NEW decisions on the REAL plane,
    loudly, BEFORE any ledger touch; sandbox rehearsals are unaffected
    (the pause is a production-plane owner law)."""
    from research.papertrade_exec import execute as E
    # QD1 pause was LIFTED by owner order 2026-10-21 (lift condition met:
    # ledger rows 85-86 carry two distinct NBA forecast p vectors), so the
    # production config must resolve NBA as NOT paused...
    assert E.league_paused("NBA") is None
    assert E.league_paused("WNBA") is None
    # ...while the LAW itself is still verified on synthetic shapes:
    # A7-R1: a malformed league_pauses table fails CLOSED
    with mock.patch.object(E, "load_config",
                           return_value={"league_pauses": ["bad-shape"]}):
        assert E.league_paused("WNBA") is not None
    with mock.patch.object(E, "load_config",
                           return_value={"league_pauses": {"X": {}}}):
        assert E.league_paused("X") is not None     # missing 'active'
    with mock.patch.object(E, "load_config",
                           return_value={"league_pauses":
                                         {"X": {"active": False}}}):
        assert E.league_paused("X") is None         # explicit False = open
    # REAL plane refusal, verified on a SYNTHETIC paused config (the
    # production config now has the pause lifted — owner order 2026-10-21):
    touched = {"ledger": False}

    def _forbidden(*a, **k):
        touched["ledger"] = True
        raise AssertionError("open_ledger must not be reached")

    args = argparse.Namespace(**dict(W1.DEC_ARGS, data_root=str(env["data"])))
    args.sandbox = False
    paused_cfg = {"league_pauses": {"NBA": {
        "active": True, "reason": "synthetic QD1 pause for the battery"}}}
    with mock.patch.object(E, "load_config",
                           return_value={"league_pauses": paused_cfg[
                               "league_pauses"], "sport_keys":
                               E.load_config().get("sport_keys", {})}), \
            mock.patch.object(E, "require_gate", return_value=(True, "", None)), \
            mock.patch.object(E, "verify_pins", return_value={}), \
            mock.patch.object(E, "open_ledger", _forbidden):
        with pytest.raises(E.BlockError) as ei:
            E.cmd_decide(args)
    assert ei.value.code == "BLOCKED_LEAGUE_PAUSED"
    assert touched["ledger"] is False
    # SANDBOX plane: unaffected (the battery still rehearses the chain)
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    out = _run_decide(env, led, lambda *a, **k: dict(_bet_dec(env)),
                      flag=False)
    assert out["journaled"][0]["status"] == "BET_PAPER"


def test_a7_m3_weekly_scorecard_job(env):
    svc = make_svc(env)
    (env["data"] / "ai_review" / "opinions_v2").mkdir(parents=True,
                                                      exist_ok=True)
    svc._maybe_weekly_scorecard()
    p = env["data"] / "sandbox" / "ops" / "state" / "ai_scorecard.json"
    data = json.loads(p.read_text())
    assert data["reviews_scored"] == 0          # empty opinions: honest 0
    kinds = [i["kind"] for i in incidents(env)]
    assert "AI_SCORECARD_COMPUTED" in kinds
    # the 7-day pacing holds (second call inside the window is a no-op)
    svc._maybe_weekly_scorecard()
    kinds = [i["kind"] for i in incidents(env)]
    assert kinds.count("AI_SCORECARD_COMPUTED") == 1


# --------------------------------------------------- U0 battery additions ----

def test_u0_citation_filter_and_excerpt_law(env, tmp_path):
    from research.papertrade_exec import ai_producer
    # parse_v2 keeps model citations verbatim; the PRODUCER filters. The
    # excerpt law lives in validate_opinion (no excerpt => invalid).
    base = {"match_id": "m1", "candidate_hash": "h" * 64,
            "reason_codes": ["R"], "summary": "s",
            "prompt_sha256": _reg_sha()}
    # U0: a source without an excerpt is not a citation
    ok, why = G.validate_opinion({**base, "verdict": "ALLOW", "sources": [
        {"url": "https://x", "fetched_at_utc": "t", "excerpt": ""}]})
    assert not ok and "excerpt" in why
    ok, _ = G.validate_opinion({**base, "verdict": "VETO", "sources": [
        {"url": "https://x", "fetched_at_utc": "t", "excerpt": "e"}]})
    assert ok


def test_u0_prompt_sha_gate_voids_stale_or_reforged(env, monkeypatch):
    """An opinion bound to a prompt sha != the REGISTERED (digest-blanked)
    sha is void — and reforging the registered value into the file keeps
    the formula self-consistent (the battery measures, not hardcodes)."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    dec = _bet_dec(env)
    # an opinion bound to a WRONG prompt sha is VOID (U0/M1 consumption
    # gate) — craft one explicitly with a bogus sha
    fc, qt = _ledger_fc_qt(led)
    chash = G.candidate_hash_for(dec, fc, qt)
    G.record_opinion(env["data"], {
        "match_id": "m1", "candidate_hash": chash, "verdict": "ALLOW",
        "reason_codes": ["R"], "summary": "s",
        "sources": [{"url": "https://x", "fetched_at_utc": "t",
                     "excerpt": "e"}],
        "model_id": "t", "provider": "t", "prompt_version": "AI_PROMPT_V2",
        "prompt_sha256": "f" * 64, "created_at_utc": "2026-10-08T09:00:00Z"})
    op, why = G.load_opinion_for(env["data"], "m1", chash)
    assert op is None and "prompt_sha" in why
    # rebind with the REGISTERED sha measured from the real prompt file
    from research.papertrade_exec.ai_producer import registered_prompt_sha
    reg_sha, _, _ = registered_prompt_sha(REPO)
    op_rec = {"match_id": "m1", "candidate_hash": chash, "verdict": "ALLOW",
              "reason_codes": ["R"], "summary": "s",
              "sources": [{"url": "https://x", "fetched_at_utc": "t",
                           "excerpt": "e"}],
              "model_id": "t", "provider": "t",
              "prompt_version": "AI_PROMPT_V2", "prompt_sha256": reg_sha,
              "created_at_utc": "2026-10-21T00:00:00Z"}
    G.record_opinion(env["data"], op_rec)
    op2, why2 = G.load_opinion_for(env["data"], "m1", chash)
    assert op2 is not None, why2
    # the registered sha is REPRODUCIBLE (measure twice)
    reg2, _, _ = registered_prompt_sha(REPO)
    assert reg2 == reg_sha
    # and the OLD 4365381d… prefix is NOT reproducible from the file
    import hashlib
    raw = (REPO / "research" / "papertrade_exec" / "AI_PROMPT_V2.md")\
        .read_bytes()
    assert not hashlib.sha256(raw).hexdigest().startswith("4365381d")


def test_u0_l1_mixed_case_verdict_never_flips_to_allow(env):
    """'Veto' (mixed case) must consume as VETO — the L1 gap would have
    treated the un-canonical string as the ALLOW branch."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    dec = _bet_dec(env)
    chash = G.candidate_hash_for(dec, *_ledger_fc_qt(led))
    from research.papertrade_exec.ai_producer import registered_prompt_sha
    reg_sha, _, _ = registered_prompt_sha(REPO)
    G.record_opinion(env["data"], {
        "match_id": "m1", "candidate_hash": chash, "verdict": "Veto",
        "reason_codes": ["R"], "summary": "s",
        "sources": [{"url": "https://x", "fetched_at_utc": "t",
                     "excerpt": "e"}],
        "model_id": "t", "provider": "t", "prompt_version": "AI_PROMPT_V2",
        "prompt_sha256": reg_sha, "created_at_utc": "2026-10-21T00:00:00Z"},
        sandbox=True)
    op, _ = G.load_opinion_for(env["data"], "m1", chash, sandbox=True)
    assert op["verdict"] == "VETO"      # canonicalized at load
    out = _run_decide(env, led, lambda *a, **k: dict(dec))
    assert out["journaled"][0]["status"] == "NOT_PLACED_AI_VETO"
