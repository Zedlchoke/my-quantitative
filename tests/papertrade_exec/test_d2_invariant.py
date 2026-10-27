"""SPEC D2 — BATTERY T1-T7 (SPEC_D2_GATE_INVARIANT_2026-10-26.md muc 5).

T1  M48 replay: ai_gate=null + production V2 VETO + shadow V3 VETO present
    -> BET_PAPER refused (AI_GATE_NULL), PENDING_AI, no ledger row.
T2  ai_gate has hash + ALLOW but NO production opinion file
    -> OPINION_FILE_MISSING.
T3  production opinion VETO vs ai_gate ALLOW -> OPINION_MISMATCH.
T4  ONLY a shadow ALLOW exists -> refused (shadow NEVER binds; muc 2.5).
T5  production ALLOW file with prompt_sha256 != registered sha of its own
    prompt_version -> OPINION_MISMATCH.
T6  full valid binding -> BET_PAPER placed normally, no refusal artifacts.
T7  non-place statuses are NOT blocked by the invariant; flag OFF is
    byte-identical passthrough.

Extra guards (beyond the 7, stronger A7 evidence — nothing in spec forbids
more assurance):
W   every desk append site goes through D2.d2_append_decision (source scan).
F   the d2_gate_invariant_active flag defaults OFF on both planes.

All tests run on the SANDBOX plane only (env fixture) — the real ledger,
real ai_review plane, and real registry are never touched.
"""
from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tests.papertrade_exec import test_ops_live_service as _ops  # noqa: E402
from tests.papertrade_exec import test_fixall_w1 as W1           # noqa: E402
from tests.papertrade_exec import test_fixall_w4 as W4           # noqa: E402
from research.papertrade_exec import ai_gate_v2 as G             # noqa: E402
from research.papertrade_exec import d2_invariant as D2          # noqa: E402
from research.papertrade_exec import execute                     # noqa: E402
from research.papertrade_exec.ai_producer import registered_prompt_sha  # noqa: E402

FX = W1.FX
env = _ops.env                     # sandbox fixture (same plane as W4)
_REG_V2 = registered_prompt_sha(REPO)[0]
_REG_V3 = registered_prompt_sha(REPO, version="AI_PROMPT_V3")[0]
_DS_MODEL = "deepseek/deepseek-v4.1-flash-1017"


class _FakeLedger:
    """Minimal ledger double: records appends, returns the appended row."""

    def __init__(self):
        self.rows = []

    def append_decision(self, row, *, recheck=None, capital_law=2):
        out = dict(row)
        out["row_sha256"] = "f" * 64
        self.rows.append(out)
        return out


def _bet_row(chash=None, verdict="ALLOW"):
    row = {"type": "DECISION", "league": FX.league, "match_id": FX.match_id,
           "competition": FX.competition, "home": FX.home, "away": FX.away,
           "kickoff_utc": FX.kickoff_utc,
           "decided_at_utc": "2026-10-08T10:00:00Z",
           "status": "BET_PAPER", "chosen_leg": "HOME", "stake_cents": 500,
           "p_frozen": {"HOME": 0.55}, "odds_frozen": {"HOME": 2.0},
           "ev_net_by_leg": {"HOME": 0.06, "AWAY": -0.1},
           "equity_at_decision_cents": 100000,
           "anchor_utc": "2026-10-08T12:50:00Z", "reason": "t",
           "model_id": "T", "model_constants": {}}
    if chash is not None:
        row["ai_gate"] = {"gate": "ai_gate_v2", "decision": "PLACE",
                          "candidate_hash": chash,
                          "opinion_verdict": verdict,
                          "opinion_why": "valid"}
    return row


def _op_dir(env):
    return env["data"] / "sandbox" / "ai_review" / "opinions_v2"


def _write_prod_opinion(env, chash, *, verdict="ALLOW", model=_DS_MODEL,
                        prompt_version="AI_PROMPT_V2", sha=None,
                        match_id="m1"):
    d = _op_dir(env)
    d.mkdir(parents=True, exist_ok=True)
    op = {"match_id": match_id, "candidate_hash": chash,
          "verdict": verdict, "reason_codes": ["R"],
          "summary": "s", "sources": [
              {"url": "https://x", "fetched_at_utc": "2026-10-08T09:00:00Z",
               "excerpt": "headline"}],
          "model_id": model, "provider": "openrouter",
          "prompt_version": prompt_version,
          "prompt_sha256": sha if sha is not None else (
              _REG_V2 if prompt_version == "AI_PROMPT_V2" else _REG_V3),
          "created_at_utc": "2026-10-08T09:00:00Z"}
    (d / f"{match_id}_{chash}.json").write_text(json.dumps(op))
    return op


def _write_shadow_opinion(env, chash, *, verdict="ALLOW"):
    d = env["data"] / "sandbox" / "ai_review" / "shadow" / "opinions_v3"
    d.mkdir(parents=True, exist_ok=True)
    op = {"match_id": "m1", "candidate_hash": chash, "verdict": verdict,
          "reason_codes": ["R"], "summary": "s", "sources": [
              {"url": "https://x", "fetched_at_utc": "2026-10-08T09:00:00Z",
               "excerpt": "headline"}],
          "model_id": _DS_MODEL, "provider": "openrouter",
          "prompt_version": "AI_PROMPT_V3", "prompt_sha256": _REG_V3,
          "created_at_utc": "2026-10-08T09:00:00Z"}
    (d / f"m1_{chash}.json").write_text(json.dumps(op))
    return op


def _gate_events(env):
    p = env["data"] / "sandbox" / "ai_review" / "gate_events.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def _telemetry(env):
    p = env["data"] / "sandbox" / "ai_review" / "telemetry.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def _refusals(env):
    return [e for e in _gate_events(env)
            if e.get("kind") == D2.D2_REFUSAL_EVENT]


# --------------------------------------------------- cmd_decide harness ----

def _run_decide_d2(env, led, evaluate, *, ai_flag, d2_flag):
    args = argparse.Namespace(**dict(W1.DEC_ARGS, data_root=str(env["data"])))
    args.sandbox = True
    core = types.SimpleNamespace(
        risk=types.SimpleNamespace(
            evaluate_match=evaluate,
            in_lock_recheck=lambda led_, now, ok, capital_law=2:
                (lambda d: d)),
        stake_for_decision=lambda eq: 500)
    with mock.patch.object(
            execute, "papertrade_flags",
            return_value={"pm_cutover_active": False,
                          "ai_authority_active": ai_flag,
                          "d2_gate_invariant_active": d2_flag}), \
         mock.patch.object(execute, "require_gate",
                           return_value=(True, "", None)), \
         mock.patch.object(execute, "verify_pins", return_value={}), \
         mock.patch.object(execute, "open_ledger",
                           return_value=(core, led)), \
         mock.patch.object(execute, "fixtures_for",
                           return_value=[FX]), \
         mock.patch.object(execute, "capital_law_for", return_value=2):
        return execute.cmd_decide(args)


def _true_chash(env, led):
    fc, qt = W4._ledger_fc_qt(led, "m1")
    return G.candidate_hash_for(W4._bet_dec(env), fc, qt)


# ------------------------------------------------------------------ T1 ------

def test_d2_t1_m48_replay_refused_and_pending(env):
    """T1 (tái hiện M48): gate OFF-era row (ai_gate null) reaches the append
    with BOTH a production V2 VETO opinion and a shadow V3 VETO opinion on
    disk for the SAME candidate — D2 (flag ON) refuses the BET_PAPER."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    chash = _true_chash(env, led)
    # the opinions that existed for M48: production V2 VETO (0 sources —
    # lawfully invalid but PRESENT on disk) + shadow V3 VETO
    _op_dir(env).mkdir(parents=True, exist_ok=True)
    (env["data"] / "sandbox" / "ai_review" / "opinions_v2" /
     f"m1_{chash}.json").write_text(json.dumps({
         "match_id": "m1", "candidate_hash": chash, "verdict": "VETO",
         "reason_codes": ["INSUFFICIENT_EVIDENCE"], "summary": "s",
         "sources": [], "model_id": "minimax/minimax-m3.1-flash:free",
         "prompt_version": "AI_PROMPT_V2", "prompt_sha256": _REG_V2,
         "created_at_utc": "2026-10-08T07:02:40Z"}))
    _write_shadow_opinion(env, chash, verdict="VETO")
    out = _run_decide_d2(env, led, lambda *a, **k: dict(W4._bet_dec(env)),
                         ai_flag=False, d2_flag=True)
    # refused: no BET_PAPER row anywhere in the ledger
    assert out["journaled"][0]["status"] == "PENDING_AI"
    assert not [r for r in led.rows if r.get("status") == "BET_PAPER"]
    assert not [r for r in led.rows if r.get("type") == "DECISION"]
    # PENDING_AI re-marked with the TRUE candidate hash (producer-ready)
    pending = G._load_pending(env["data"], sandbox=True)
    assert pending["m1"]["candidate_hash"] == chash
    assert D2.D2_REFUSAL_DETAIL in pending["m1"]["last_detail"]
    # gate_event with the exact code
    ref = _refusals(env)
    assert len(ref) == 1 and ref[0]["code"] == "AI_GATE_NULL"
    assert ref[0]["candidate_hash"] == chash
    assert ref[0]["match_id"] == "m1"
    # telemetry counter
    tel = [t for t in _telemetry(env) if t.get("outcome") == D2.D2_TELEMETRY_OUTCOME]
    assert len(tel) == 1 and tel[0]["code"] == "AI_GATE_NULL"


# ------------------------------------------------------------ T2–T5 (unit) --

def test_d2_t2_opinion_file_missing(env):
    led = _FakeLedger()
    row = _bet_row(chash="a" * 64, verdict="ALLOW")
    out = D2.d2_append_decision(led, row, data_root=env["data"],
                                sandbox=True, active=True)
    assert out["d2_refused"] is True and out["d2_code"] == "OPINION_FILE_MISSING"
    assert out["status"] == "PENDING_AI"
    assert led.rows == []                      # nothing appended
    assert _refusals(env)[-1]["code"] == "OPINION_FILE_MISSING"
    assert G._load_pending(env["data"], sandbox=True)["m1"]["last_detail"] \
        .startswith(D2.D2_REFUSAL_DETAIL)


def test_d2_t3_verdict_mismatch(env):
    chash = "b" * 64
    _write_prod_opinion(env, chash, verdict="VETO")   # file says VETO
    led = _FakeLedger()
    row = _bet_row(chash=chash, verdict="ALLOW")      # gate says ALLOW
    out = D2.d2_append_decision(led, row, data_root=env["data"],
                                sandbox=True, active=True)
    assert out["d2_code"] == "OPINION_MISMATCH" and led.rows == []


def test_d2_t4_shadow_never_binds(env):
    chash = "c" * 64
    # ONLY a shadow ALLOW exists — production dir has nothing (muc 2.5)
    _write_shadow_opinion(env, chash, verdict="ALLOW")
    led = _FakeLedger()
    row = _bet_row(chash=chash, verdict="ALLOW")
    out = D2.d2_append_decision(led, row, data_root=env["data"],
                                sandbox=True, active=True)
    assert out["d2_refused"] is True and led.rows == []
    assert _refusals(env)[-1]["code"] == "OPINION_FILE_MISSING"
    # and a full production binding still places (shadow irrelevant)
    _write_prod_opinion(env, chash, verdict="ALLOW")
    led2 = _FakeLedger()
    out2 = D2.d2_append_decision(led2, _bet_row(chash=chash), data_root=env["data"],
                                 sandbox=True, active=True,
                                 recheck=lambda d: d)
    assert out2["status"] == "BET_PAPER" and len(led2.rows) == 1


def test_d2_t5_prompt_digest_mismatch(env):
    chash = "d" * 64
    # digest does NOT match the registered sha of its own prompt_version
    _write_prod_opinion(env, chash, sha="0" * 64)
    led = _FakeLedger()
    out = D2.d2_append_decision(led, _bet_row(chash=chash), data_root=env["data"],
                                sandbox=True, active=True)
    assert out["d2_code"] == "OPINION_MISMATCH" and led.rows == []
    # V3-version digest mismatch is equally refused
    chash2 = "e" * 64
    _write_prod_opinion(env, chash2, prompt_version="AI_PROMPT_V3",
                        sha="1" * 64)
    out2 = D2.d2_append_decision(led, _bet_row(chash=chash2),
                                 data_root=env["data"], sandbox=True,
                                 active=True)
    assert out2["d2_code"] == "OPINION_MISMATCH"


# ------------------------------------------------------------------ T6 ------

def test_d2_t6_valid_binding_places_normally(env):
    """T6 (đối chứng): full valid binding (ALLOW + production file matching
    hash/match/verdict/digest/model) through the REAL decide path with both
    flags ON -> BET_PAPER placed, zero refusal artifacts."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    chash = _true_chash(env, led)
    _write_prod_opinion(env, chash, verdict="ALLOW", model=_DS_MODEL)
    out = _run_decide_d2(env, led, lambda *a, **k: dict(W4._bet_dec(env)),
                         ai_flag=True, d2_flag=True)
    assert out["journaled"][0]["status"] == "BET_PAPER"
    row = next(r for r in led.rows if r.get("status") == "BET_PAPER")
    assert row["ai_gate"]["candidate_hash"] == chash
    assert row["ai_gate"]["opinion_verdict"] == "ALLOW"
    assert _refusals(env) == []
    assert not [t for t in _telemetry(env)
                if t.get("outcome") == D2.D2_TELEMETRY_OUTCOME]
    assert G._load_pending(env["data"], sandbox=True) == {}


# ------------------------------------------------------------------ T7 ------

def test_d2_t7_non_place_statuses_and_flag_off(env):
    """T7: non-place statuses are never blocked; flag OFF is byte-identical."""
    # (a) VETO terminal still appended with D2 ON
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    chash = _true_chash(env, led)
    _write_prod_opinion(env, chash, verdict="VETO", model=_DS_MODEL)
    out = _run_decide_d2(env, led, lambda *a, **k: dict(W4._bet_dec(env)),
                         ai_flag=True, d2_flag=True)
    assert out["journaled"][0]["status"] == "NOT_PLACED_AI_VETO"
    assert next(r for r in led.rows if r.get("status") == "NOT_PLACED_AI_VETO")
    assert _refusals(env) == []
    # (b) non-place rows passthrough the wrapper untouched
    led2 = _FakeLedger()
    for st in ("NOT_PLACED_AI_NO_VERDICT", "NO_EDGE", "QUOTA_SKIP",
               "NOT_RUN_QUOTE_COLLISION", "NOT_PLACED_EV_OUTLIER"):
        r = {"type": "DECISION", "status": st, "match_id": "m1"}
        D2.d2_append_decision(led2, r, data_root=env["data"],
                              sandbox=True, active=True)
    assert len(led2.rows) == 5
    # (c) flag OFF: BET_PAPER with ai_gate null appends byte-identically
    _ops.sandbox_ledger_path(env).unlink()      # fresh ledger (W4 idiom)
    led3 = W1._sandbox_ledger(env)
    W1._seed_chain(led3, "m1")
    out3 = _run_decide_d2(env, led3, lambda *a, **k: dict(W4._bet_dec(env)),
                          ai_flag=False, d2_flag=False)
    assert out3["journaled"][0]["status"] == "BET_PAPER"
    row = next(r for r in led3.rows if r.get("status") == "BET_PAPER")
    assert "ai_gate" not in row                       # pre-D2 byte shape
    assert _refusals(env) == []


# ------------------------------------------------------- extra guards -------

def test_d2_wiring_every_append_site_wrapped():
    """Muc 4 evidence: NO bare led.append_decision call site remains in the
    desk decide/quote writers — every DECISION write goes through the D2
    wrapper (source scan, re-read by A7 against the real files)."""
    for rel in ("research/papertrade_exec/execute.py",
                "research/papertrade_exec/wsl_lane.py"):
        src = (REPO / rel).read_text()
        assert "led.append_decision(" not in src, f"bare append in {rel}"
        assert "D2.d2_append_decision(" in src, f"wrapper missing in {rel}"


def test_d2_flag_defaults_off_both_planes(tmp_path, monkeypatch):
    """The D2 flag is OFF unless config+typed-GO both hold (W4 gate law).

    Post-GO guard (A7 FIXTURE_ONLY ruling 2026-10-27,
    a7/A7_PROMOTE_ADOPTION_RULING_2026-10-27.md): the production root now
    carries the owner's REAL D2 GO plane (token + registry marker +
    config key, effective since T0 2026-10-26T14:21:39Z), so the old
    bare real-plane assertion would read the live plane — forbidden
    (expectation must never chase whatever the disk returns). Instead the
    guard builds its OWN planes through the sanctioned seams and checks
    BOTH directions, fail-closed by construction:
      1. real plane CLEAN (tmp control/registry, no token) -> OFF
      2. real plane clean + config key ABSENT -> OFF
      3. sandbox plane default (pre-GO rehearsal state) -> OFF
      4. real plane with a COMPLETE tmp GO plane (token 4 fields, phrase
         verbatim + registry marker + config key true) -> ON
    Production files are only ever READ (registry copy), never written."""
    # 1. clean real plane: no token anywhere -> fail-closed OFF
    args = argparse.Namespace(
        sandbox=False, sandbox_control_dir=str(tmp_path),
        sandbox_registry=str(tmp_path / "CYCLE_REGISTRY.json"))
    assert execute.papertrade_flags(args).get(
        "d2_gate_invariant_active") is False
    # 2. same clean plane with the config key REMOVED -> still OFF
    cfg = execute.load_config()
    fg = dict(cfg.get("feature_gates") or {})
    fg.pop("d2_gate_invariant_active", None)
    monkeypatch.setattr(execute, "load_config",
                        lambda: {**cfg, "feature_gates": fg})
    assert execute.papertrade_flags(args).get(
        "d2_gate_invariant_active") is False
    monkeypatch.undo()
    # 3. sandbox plane defaults to the PRE-GO state -> OFF
    args2 = argparse.Namespace(sandbox=True)
    assert execute.papertrade_flags(args2).get(
        "d2_gate_invariant_active") is False
    # 4. complete GO plane in tmp (both keys hold) -> ON, per the gate law
    (tmp_path / "GO_TOKEN_D2_GATE_INVARIANT.json").write_text(json.dumps({
        "go_phrase_typed_by_owner":
            "GO SPORTS PAPERTRADE EXEC V1 D2 GATE INVARIANT",
        "typed_at_utc": "2026-10-26T14:19:43Z",
        "transcribed_by": "post-GO guard test (tmp plane)",
        "registry_consumption_note": "tmp plane only; never production"}))
    reg = json.loads((REPO / "plans" / "CYCLE_REGISTRY.json").read_text())
    (tmp_path / "CYCLE_REGISTRY.json").write_text(json.dumps(reg))
    assert execute.papertrade_flags(args).get(
        "d2_gate_invariant_active") is True
