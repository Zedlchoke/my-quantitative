"""PAPERDESK UPGRADE V2 — U4 battery: PLANE HYGIENE.

  M6  ai_review plane sandbox separation: ai_gate_v2.ai_review_dir gains
      the sandbox param (<data-root>/sandbox/ai_review when sandbox=True);
      the flag is threaded from execute.apply_ai_gate_v2 (args.sandbox),
      ops_service._ai_pending_view/_ai_produce_for_pending (self.sandbox)
      and the producer. A SANDBOX decide/producer/ops pass must not change
      ONE BYTE of the REAL ai_review plane.
  M8  durable-writer law: pending.json and cascade_state.json are written
      tmp+os.replace ATOMICALLY under an fcntl.flock on a companion
      .lock file — a failed write leaves the previous bytes intact.
  M4  EV quarantine terminal law: a match with a FINAL NOT_PLACED_EV_OUTLIER
      row is terminal (never re-queued through the quarantine pool), and a
      quarantined match without a fresh quote learns its state on the OPS
      plane only — a second pass appends NO new QUARANTINED ledger row
      (no-churn law; the ledger-side no-churn behavior is additionally
      exercised by test_fixall_w1.test_decide_quarantine_reentry_...).
  L2  plane hooks: --sandbox-control-dir / --sandbox-registry explicitly
      provided on the REAL plane => BLOCKED_TEST_HOOK_IN_REAL_MODE.
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

from tests.papertrade_exec import test_fixall_w1 as W1            # noqa: E402
from tests.papertrade_exec import test_ops_live_service as _ops   # noqa: E402
from research.papertrade_exec import ai_gate_v2 as G              # noqa: E402
from research.papertrade_exec import ai_producer                  # noqa: E402
from research.papertrade_exec import execute                      # noqa: E402

env = _ops.env
make_svc = _ops.make_svc
FX = W1.FX


# ------------------------------------------------------------------ M6 ----

def test_ai_review_dir_sandbox_param(tmp_path):
    d = tmp_path / "data"
    assert G.ai_review_dir(d) == d / "ai_review"
    assert G.ai_review_dir(d, sandbox=False) == d / "ai_review"
    assert G.ai_review_dir(d, sandbox=True) == d / "sandbox" / "ai_review"


def _bet_dec():
    return {"type": "DECISION", "league": FX.league,
            "match_id": FX.match_id, "competition": FX.competition,
            "home": FX.home, "away": FX.away,
            "kickoff_utc": FX.kickoff_utc,
            "decided_at_utc": "2026-10-08T10:00:00Z",
            "status": "BET_PAPER", "chosen_leg": "HOME",
            "stake_cents": 500, "p_frozen": {"HOME": 0.55},
            "odds_frozen": {"HOME": 2.0},
            "ev_net_by_leg": {"HOME": 0.06, "AWAY": -0.1},
            "equity_at_decision_cents": 100000,
            "anchor_utc": "2026-10-08T12:50:00Z", "reason": "t",
            "model_id": "T", "model_constants": {}}


def _sandbox_decide(env, *, flag=True):
    """Drive cmd_decide on a REAL sandbox ledger with the AI gate flag
    forced on (sandbox rehearsal of the W4 gate path)."""
    core = types.SimpleNamespace(
        risk=types.SimpleNamespace(
            evaluate_match=lambda *a, **k: dict(_bet_dec()),
            in_lock_recheck=lambda led_, now, ok, capital_law=2:
                (lambda d: d)),
        stake_for_decision=lambda eq: 500)
    args = argparse.Namespace(**dict(W1.DEC_ARGS,
                                     data_root=str(env["data"])))
    args.sandbox = True
    with mock.patch.object(execute, "papertrade_flags",
                           return_value={"pm_cutover_active": False,
                                         "ai_authority_active": flag}), \
         mock.patch.object(execute, "require_gate",
                           return_value=(True, "", None)), \
         mock.patch.object(execute, "verify_pins", return_value={}), \
         mock.patch.object(execute, "open_ledger",
                           return_value=(core, env["led"])), \
         mock.patch.object(execute, "fixtures_for",
                           return_value=[FX]), \
         mock.patch.object(execute, "capital_law_for", return_value=2):
        return execute.cmd_decide(args)


def test_sandbox_decide_never_touches_the_real_ai_review_plane(env):
    """THE M6 battery law: a sandbox decide consumes ONLY
    <data>/sandbox/ai_review; the REAL plane stays byte-identical."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    env["led"] = led
    # pre-existing REAL plane with sentinel bytes
    real = env["data"] / "ai_review"
    real.mkdir(parents=True)
    (real / "pending.json").write_text('{"sentinel": true}')
    (real / "gate_events.jsonl").write_text('{"sentinel": "real-plane"}\n')
    before = {p.name: p.read_bytes() for p in sorted(real.iterdir())
              if p.is_file()}

    out = _sandbox_decide(env)
    assert out["journaled"][0]["status"] == "PENDING_AI"
    # the sandbox plane carries the queue
    sb_pending = env["data"] / "sandbox" / "ai_review" / "pending.json"
    assert sb_pending.exists() and "m1" in json.loads(sb_pending.read_text())
    # the REAL plane: byte-for-byte untouched, no new files
    after = {p.name: p.read_bytes() for p in sorted(real.iterdir())
             if p.is_file()}
    assert after == before
    assert set(after) == set(before)


def test_real_plane_opinion_is_invisible_to_a_sandbox_decide(env):
    """Plane separation is a hard boundary in BOTH directions: an opinion
    written on the REAL plane cannot satisfy a sandbox decide (and vice
    versa) — the hash-locked review must live on the SAME plane."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    env["led"] = led
    dec = _bet_dec()
    fc = next(r for r in led.rows if r.get("type") == "FORECAST")
    qt = next(r for r in led.rows if r.get("type") == "MARKET_QUOTE")
    chash = G.candidate_hash_for(dec, fc, qt)
    from tests.papertrade_exec.test_fixall_w4 import _reg_sha
    G.record_opinion(env["data"], {
        "match_id": "m1", "candidate_hash": chash, "verdict": "ALLOW",
        "reason_codes": ["R"], "summary": "s",
        "sources": [{"url": "https://x", "fetched_at_utc": "t",
                     "excerpt": "e"}],
        "model_id": "t", "provider": "t", "prompt_version": "AI_PROMPT_V2",
        "prompt_sha256": _reg_sha(),
        "created_at_utc": "2026-10-21T00:00:00Z"})
    out = _sandbox_decide(env)   # sandbox gate reads ONLY the sandbox plane
    assert out["journaled"][0]["status"] == "PENDING_AI"
    assert not [r for r in led.rows if r.get("type") == "DECISION"]


def test_ops_service_reads_and_produces_on_the_sandbox_plane(env,
                                                             monkeypatch):
    """ops self.sandbox threads into the pending view, the provider-down
    watch and the producer call (M6 caller law)."""
    svc = make_svc(env)
    assert svc.sandbox is True
    # a REAL-plane queue entry is invisible to the sandbox service
    G.pending_marker(env["data"], "m-real", "h" * 64,
                     "2026-10-08T12:50:00Z", "real plane",
                     sandbox=False)
    assert svc._ai_pending_view() == []
    G.pending_marker(env["data"], "m-sb", "h" * 64,
                     "2026-10-08T12:50:00Z", "sandbox plane",
                     sandbox=True)
    view = svc._ai_pending_view()
    assert [v["match_id"] for v in view] == ["m-sb"]
    # the producer call receives sandbox=True from the service
    captured = {}

    def fake_produce(data_root, *, worktree_root, sandbox=False, **kw):
        captured["sandbox"] = sandbox
        return {"written": 0, "invalid": 0, "provider_failed": 0,
                "rate_limited": 0}

    with mock.patch.object(execute, "papertrade_flags",
                           return_value={"ai_authority_active": True}), \
         mock.patch.object(ai_producer, "produce_for_pending",
                           fake_produce):
        svc._ai_produce_for_pending()
    assert captured["sandbox"] is True


# ------------------------------------------------------------------ M8 ----

def test_save_pending_is_atomic_with_companion_lock(tmp_path):
    d = tmp_path / "data"
    G._save_pending(d, {"m1": {"a": 1}})
    p = G._pending_path(d)
    assert json.loads(p.read_text()) == {"m1": {"a": 1}}
    assert (d / "ai_review" / "pending.json.lock").exists()
    assert not list((d / "ai_review").glob("*.tmp"))
    # a crashing write leaves the PREVIOUS bytes intact (atomicity law)
    v1 = p.read_bytes()
    real_dumps = json.dumps

    def boom(*a, **k):
        raise RuntimeError("disk gone mid-write")

    with mock.patch.object(G, "json") as jmod:
        jmod.dumps.side_effect = boom
        jmod.JSONDecodeError = real_dumps and ValueError
        with pytest.raises(RuntimeError):
            G._save_pending(d, {"m1": {"a": 2}})
    assert p.read_bytes() == v1                 # previous state intact
    assert json.loads(p.read_text()) == {"m1": {"a": 1}}


def test_cascade_state_write_is_atomic_with_companion_lock(tmp_path):
    d = tmp_path / "data"
    P_save = ai_producer.save_cascade
    P_save(d, {"slots": {"m": ai_producer._new_slot()}})
    p = ai_producer.cascade_state_path(d)
    assert json.loads(p.read_text())["slots"]["m"]["state"] == "UP"
    assert (d / "ai_review" / "cascade_state.json.lock").exists()
    assert not list((d / "ai_review").glob("*.tmp"))
    # concurrent writers serialize under the flock: 20 interleaved writes
    import threading
    def writer(i):
        P_save(d, {"slots": {"m": {**ai_producer._new_slot(),
                                   "consecutive_failures": i}}})
    threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    final = json.loads(p.read_text())
    assert isinstance(final["slots"]["m"]["consecutive_failures"], int)


# ------------------------------------------------------------------ M4 ----

def test_final_outlier_match_never_reenters_quarantine_pool(env):
    """A match whose quarantine ENDED in the FINAL NOT_PLACED_EV_OUTLIER
    row is terminal: it stays in `decided` and is never re-queued, no
    matter that older QUARANTINED rows exist."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    led.append_decision({
        "type": "DECISION", "league": "NBA", "match_id": "m1",
        "competition": "NBA", "home": FX.home, "away": FX.away,
        "kickoff_utc": FX.kickoff_utc,
        "decided_at_utc": "2026-10-08T08:00:00Z",
        "status": "QUARANTINED_EV_OUTLIER", "reason": "prior quarantine",
        "stake_cents": 0, "chosen_leg": None})
    led.append_decision({
        "type": "DECISION", "league": "NBA", "match_id": "m1",
        "competition": "NBA", "home": FX.home, "away": FX.away,
        "kickoff_utc": FX.kickoff_utc,
        "decided_at_utc": "2026-10-08T09:00:00Z",
        "status": "NOT_PLACED_EV_OUTLIER",
        "reason": "second source aggregated the outlier — terminal",
        "stake_cents": 0, "chosen_leg": None})
    # a FRESH quote after the terminal row would have unlocked a mere
    # quarantine — but a terminal outlier is terminal, period.
    led.append({"type": "MARKET_QUOTE", "league": "NBA", "match_id": "m1",
                "home": FX.home, "away": FX.away, "competition": "NBA",
                "kickoff_utc": FX.kickoff_utc,
                "odds": {"HOME": 2.0, "AWAY": 1.9},
                "bookmaker": "pinnacle", "market": "h2h",
                "fetch_ts_utc": "2026-10-08T09:30:00Z",
                "source_last_update_utc": "2026-10-08T09:00:00Z",
                "commence_time_utc": FX.kickoff_utc,
                "payload_sha256": "2" * 64, "key_fingerprint": None,
                "mode": "REAL", "source_ref": "TEST-FRESH"})
    reached = {"evaluate": 0}

    def evaluate(*a, **k):
        reached["evaluate"] += 1
        return W1._bet_dec(0.06)

    core = types.SimpleNamespace(
        risk=types.SimpleNamespace(
            evaluate_match=evaluate,
            in_lock_recheck=lambda led_, now, ok, capital_law=2:
                (lambda d: d)),
        stake_for_decision=lambda eq: 1000)
    args = argparse.Namespace(**dict(W1.DEC_ARGS,
                                     data_root=str(env["data"])))
    with mock.patch.object(execute, "require_gate",
                           return_value=(True, "", None)), \
         mock.patch.object(execute, "verify_pins", return_value={}), \
         mock.patch.object(execute, "open_ledger",
                           return_value=(core, led)), \
         mock.patch.object(execute, "fixtures_for",
                           return_value=[FX]), \
         mock.patch.object(execute, "capital_law_for", return_value=2):
        out = execute.cmd_decide(args)
    assert out["skipped"] == [{"match_id": "m1", "why": "already decided"}]
    assert reached["evaluate"] == 0
    statuses = [r.get("status") for r in led.rows
                if r.get("type") == "DECISION"]
    assert statuses.count("BET_PAPER") == 0
    assert statuses.count("NOT_PLACED_EV_OUTLIER") == 1


def test_quarantine_no_fresh_quote_pass_writes_no_ledger_row(env):
    """M4 no-churn: the repeated-quarantine knowledge lives on the OPS
    plane (journaled report + ai_review gate event), NEVER as another
    QUARANTINED ledger row."""
    led = W1._sandbox_ledger(env)
    W1._seed_chain(led, "m1")
    led.append_decision({
        "type": "DECISION", "league": "NBA", "match_id": "m1",
        "competition": "NBA", "home": FX.home, "away": FX.away,
        "kickoff_utc": FX.kickoff_utc,
        "decided_at_utc": "2026-10-08T08:00:00Z",
        "status": "QUARANTINED_EV_OUTLIER", "reason": "prior quarantine",
        "stake_cents": 0, "chosen_leg": None})
    core = types.SimpleNamespace(
        risk=types.SimpleNamespace(
            evaluate_match=lambda *a, **k: W1._bet_dec(0.06),
            in_lock_recheck=lambda led_, now, ok, capital_law=2:
                (lambda d: d)),
        stake_for_decision=lambda eq: 1000)
    args = argparse.Namespace(**dict(W1.DEC_ARGS,
                                     data_root=str(env["data"])))
    with mock.patch.object(execute, "require_gate",
                           return_value=(True, "", None)), \
         mock.patch.object(execute, "verify_pins", return_value={}), \
         mock.patch.object(execute, "open_ledger",
                           return_value=(core, led)), \
         mock.patch.object(execute, "fixtures_for",
                           return_value=[FX]), \
         mock.patch.object(execute, "capital_law_for", return_value=2):
        out = execute.cmd_decide(args)
    assert out["journaled"][0]["status"] == "QUARANTINED_EV_OUTLIER"
    assert out["journaled"][0]["reason"].endswith("(M4 no-churn)")
    rows = [r for r in led.rows
            if r.get("status") == "QUARANTINED_EV_OUTLIER"]
    assert len(rows) == 1                        # the ORIGINAL row only
    # the ops-plane gate event fired on the SANDBOX ai_review plane
    events = G.ai_review_dir(env["data"], sandbox=True) / \
        "gate_events.jsonl"
    assert events.exists()
    kinds = [json.loads(l)["kind"] for l in
             events.read_text().splitlines() if l.strip()]
    assert "EV_OUTLIER_STILL_QUARANTINED" in kinds


# ------------------------------------------------------------------ L2 ----

def test_l2_real_mode_refuses_explicit_sandbox_hooks(capsys):
    for hook in ("--sandbox-control-dir", "--sandbox-registry"):
        rc = execute.main([hook, "/tmp/definitely-not-real-control",
                           "key-check"])
        out = capsys.readouterr().out
        assert rc == execute.EXIT_BLOCKED_OTHER
        assert "BLOCKED_TEST_HOOK_IN_REAL_MODE" in out


def test_l2_sandbox_mode_still_accepts_explicit_hooks(capsys):
    """The hooks are REHEARSAL plumbing: with --sandbox they pass the L2
    plane check and the command proceeds (key-check then fails on the
    missing key file — a DIFFERENT, lawful block)."""
    rc = execute.main(["--sandbox",
                       "--sandbox-control-dir", "/tmp/sb-control",
                       "--sandbox-registry", "/tmp/sb-registry.json",
                       "key-check"])
    out = capsys.readouterr().out
    assert "BLOCKED_TEST_HOOK_IN_REAL_MODE" not in out
    assert rc != execute.EXIT_BLOCKED_OTHER
