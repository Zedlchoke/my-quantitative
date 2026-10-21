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
          "prompt_sha256": "a" * 64,
          "created_at_utc": "2026-10-08T09:00:00Z"}
    G.record_opinion(env["data"], op)
    return chash


# ------------------------------------------------------------------ schema --

def test_v2_schema_two_verdicts_only(env):
    base = {"match_id": "m1", "candidate_hash": "h" * 64,
            "reason_codes": ["R"], "summary": "s", "sources": [
                {"url": "https://x", "fetched_at_utc": "t"}],
            "prompt_sha256": "a" * 64}
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
    op, why = G.load_opinion_for(env["data"], "m1", chash)
    assert op and op["verdict"] == "ALLOW"
    # price moves => new hash => the old review is VOID
    qt2 = {**_quote_row(), "payload_sha256": "e" * 64}
    op2, why2 = G.load_opinion_for(env["data"], "m1",
                                   G.candidate_hash_for(dec, _fc_row(), qt2))
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
    assert G._load_pending(env["data"]) == {}


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
    pending = G._load_pending(env["data"])
    assert "m1" in pending and pending["m1"]["attempts"] == 1
    # (b) garbage verdict (SWITCH) is INVALID => still pending
    fc_l, qt_l = _ledger_fc_qt(led)
    chash = G.candidate_hash_for(_bet_dec(env), fc_l, qt_l)
    bad_dir = env["data"] / "ai_review" / "opinions_v2"
    bad_dir.mkdir(parents=True, exist_ok=True)
    (bad_dir / f"m1_{chash}.json").write_text(json.dumps(
        {"match_id": "m1", "candidate_hash": chash, "verdict": "SWITCH",
         "reason_codes": ["R"], "summary": "s", "sources": [],
         "prompt_sha256": "a" * 64}))
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
    assert G._load_pending(env["data"]) == {}


def test_provider_down_alarm(env):
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    out = _run_decide(env, led, lambda *a, **k: dict(_bet_dec(env)))
    assert out["journaled"][0]["status"] == "PENDING_AI"
    # age the pending entry beyond the 30-minute alarm law
    pending = G._load_pending(env["data"])
    pending["m1"]["first_pending_utc"] = (
        datetime.now(timezone.utc) - timedelta(minutes=45)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    G._save_pending(env["data"], pending)
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

def test_scorecard_allow_vs_veto_and_downgrade_suggestion():
    rows = [
        {"type": "GENESIS", "row_sha256": "0" * 64},
        # ALLOW-placed WIN
        {"type": "DECISION", "match_id": "m1", "status": "BET_PAPER",
         "row_sha256": "a" * 64,
         "ai_gate": {"candidate_hash": "h1", "verdict": "ALLOW"}},
        {"type": "MARKET_QUOTE", "match_id": "m1",
         "odds": {"HOME": 2.0}},
        {"type": "SETTLEMENT", "match_id": "m1", "result": "HOME",
         "pnl_cents": 500, "decision_row_sha256": "a" * 64},
        # VETO that WOULD have lost (AI kept money)
        {"type": "DECISION", "match_id": "m2", "status":
         "NOT_PLACED_AI_VETO", "row_sha256": "b" * 64, "stake_cents": 0,
         "ai_gate": {"candidate_hash": "h2", "verdict": "VETO",
                     "hypothetical_leg": "HOME",
                     "hypothetical_stake_cents": 500,
                     "hypothetical_decimal_odds": 2.0}},
        {"type": "SETTLEMENT", "match_id": "m2", "result": "AWAY"},
        # VETO that WOULD have won (AI cost money)
        {"type": "DECISION", "match_id": "m3", "status":
         "NOT_PLACED_AI_VETO", "row_sha256": "c" * 64, "stake_cents": 0,
         "ai_gate": {"candidate_hash": "h3", "verdict": "VETO",
                     "hypothetical_leg": "HOME",
                     "hypothetical_stake_cents": 500,
                     "hypothetical_decimal_odds": 3.0}},
        {"type": "SETTLEMENT", "match_id": "m3", "result": "HOME"},
    ]
    tmp = Path("/tmp/ai_scorecard_test")
    (tmp / "opinions_v2").mkdir(parents=True, exist_ok=True)
    for h, v in (("h1", "ALLOW"), ("h2", "VETO"), ("h3", "VETO")):
        (tmp / "opinions_v2" / f"op_{h}.json").write_text(json.dumps(
            {"candidate_hash": h, "verdict": v,
             "created_at_utc": "2026-10-21T00:00:00Z"}))
    sc = ai_scorecard.compute_scorecard(ledger_rows=rows,
                                        opinions_dir=tmp / "opinions_v2",
                                        min_scored_for_downgrade=2)
    assert sc["reviews_scored"] == 3
    assert sc["allow_placed"] == 1
    assert sc["veto_reviewed"] == 2
    assert sc["placed_realized_pnl_cents"] == 500
    # vetoed set: m2 would have lost (-500), m3 would have won (+1000)
    assert sc["vetoed_hypothetical_pnl_cents"] == 500
    assert sc["net_value_of_ai_layer_cents"] == 0
    assert sc["downgrade_proposal"]["eligible"] is True
    assert "suggest_demote_to_shadow" in sc["downgrade_proposal"]


# ------------------------------------------------------------------ W4.6 ----

def test_provider_and_prompt_frozen_by_config():
    node = pytest.importorskip("subprocess")
    import subprocess
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
    assert payload["model"].startswith("minimax/")   # sandbox default


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
    pause = E.league_paused("NBA")
    assert pause and pause.get("active") is True
    assert E.league_paused("WNBA") is None
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
    # REAL plane: refuses before open_ledger is even called
    touched = {"ledger": False}

    def _forbidden(*a, **k):
        touched["ledger"] = True
        raise AssertionError("open_ledger must not be reached")

    args = argparse.Namespace(**dict(W1.DEC_ARGS, data_root=str(env["data"])))
    args.sandbox = False
    with mock.patch.object(E, "require_gate", return_value=(True, "", None)), \
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
