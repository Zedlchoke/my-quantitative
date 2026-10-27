"""BUG 2026-10-26 (production, pre-existing; NOT D2-related): the V3
research-loop path never promoted an EXPIRED COOLDOWN slot, so a 5xx/timeout
cooldown (10 min) stuck forever — the state survives restarts on disk
(cascade_state.json), the balance-check revive only covers HTTP_402 holds,
and _promote_expired() sat on the legacy branch the research path `continue`s
around. Live evidence: slots deepseek-v4.1-flash(-1017) COOLDOWN since
07:03/07:09Z 2026-10-26 with expired `cooldown_until_utc`; every producer
pass returned all_slots_down; no opinion after 06:57Z.

Fix under test (minimal): run_research_loop promotes expired COOLDOWNs
before each slot selection — expired -> HALF_OPEN, the next REAL call is the
trial (U3 law unchanged). Preserved behaviors asserted here: 402-hold law
(balance-check revive only), silence law (all_slots_down -> PENDING).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tests.papertrade_exec import test_upgrade_u3 as U3   # noqa: E402
from research.papertrade_exec import ai_gate_v2 as G      # noqa: E402
from research.papertrade_exec import ai_producer as P     # noqa: E402
from research.papertrade_exec import ai_research         # noqa: E402
from research.papertrade_exec import execute             # noqa: E402

env = U3.env
NOW_FMT = U3.NOW_FMT
HEAD = "deepseek/deepseek-v4.1-flash-1017"
TAIL = "deepseek/deepseek-v4.1-flash"


def _iso(dt):
    return dt.strftime(NOW_FMT)


def _mark_pending_sb(data, match_id="m1", candidate_hash=None):
    """pending_marker on the SANDBOX plane (U3._mark_pending marks the real
    plane; our producer runs sandbox=True)."""
    chash = candidate_hash or U3._fresh_hash()
    anchor = _iso(datetime.now(timezone.utc) + timedelta(hours=6))
    G.pending_marker(
        data, match_id, chash, anchor, "battery candidate",
        context={"league": "NBA", "match_id": match_id, "home": "H",
                 "away": "A", "kickoff_utc": anchor,
                 "competition": "NBA", "chosen_leg": "HOME",
                 "p_frozen": {"HOME": 0.55}, "odds_frozen": {"HOME": 2.0},
                 "ev_net_by_leg": {"HOME": 0.06}, "stake_cents": 500},
        sandbox=True)
    return chash


def _produce_v3(env, monkeypatch, *, transport, models=(HEAD, TAIL),
                balance_transport=None, mark=True):
    """produce_for_pending on the REAL V3 path (free-research enabled,
    shadow OFF) — the exact road the bug lives on."""
    if mark:
        _mark_pending_sb(env["data"])
    U3._wire_cfg(monkeypatch, execute.load_config(), models=list(models))
    monkeypatch.setattr(ai_research, "collect_evidence",
                        lambda **kw: {"sources": [
                            {"url": "https://example.com/wire",
                             "fetched_at_utc": _iso(datetime.now(timezone.utc)),
                             "excerpt": "headline"}]})
    return P.produce_for_pending(
        env["data"], worktree_root=REPO, provider_transport=transport,
        balance_transport=balance_transport, sandbox=True,
        min_retry_minutes=0,
        fr_over={"enabled": True, "shadow": False, "max_tool_rounds": 2})


def _set_slot(data, model, *, state, until=None, reason=None):
    cascade = P.load_cascade(data, sandbox=True)
    slot = cascade["slots"].setdefault(model, P._new_slot())
    slot["state"] = state
    slot["cooldown_until_utc"] = until
    slot["cooldown_reason"] = reason
    if until is None:
        slot["last_cooldown_min"] = None
    P.save_cascade(data, cascade, sandbox=True)
    return cascade


def _slot(data, model):
    return P.load_cascade(data, sandbox=True)["slots"].get(model)


def _events(data, kind):
    return U3._events(data, sandbox=True, kind=kind)


def _telemetry(data):
    p = G.ai_review_dir(data, True) / "telemetry.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------- T1 -------

def test_t1_expired_cooldown_recovers_on_v3_research_path(env, monkeypatch):
    """The live bug, replayed: slot stuck COOLDOWN with a LONG-EXPIRED
    cooldown_until_utc (07:03Z 2026-10-26 style) + reason 5xx/timeout.
    After the fix the research loop promotes it (cooldown_expired ->
    HALF_OPEN), the real call is the trial, success -> UP, verdict written.
    (Pre-fix this exact setup returned all_slots_down forever — the state
    file on disk keeps the slot stuck across restarts.)"""
    past = _iso(datetime.now(timezone.utc) - timedelta(hours=7))
    _mark_pending_sb(env["data"])
    _set_slot(env["data"], HEAD, state="COOLDOWN", until=past,
              reason="HTTP_5XX_OR_TIMEOUT")
    U3._wire_cfg(monkeypatch, execute.load_config(), models=[HEAD, TAIL])
    monkeypatch.setattr(ai_research, "collect_evidence",
                        lambda **kw: {"sources": [
                            {"url": "https://example.com/wire",
                             "fetched_at_utc": _iso(datetime.now(timezone.utc)),
                             "excerpt": "headline"}]})
    out = P.produce_for_pending(
        env["data"], worktree_root=REPO,
        provider_transport=lambda m, s, p: {"content": U3._valid("VETO")},
        sandbox=True, min_retry_minutes=0,
        fr_over={"enabled": True, "shadow": False, "max_tool_rounds": 2})
    assert out["written"] == 1, out
    tel = [t for t in _telemetry(env["data"])
           if t.get("outcome") != "all_slots_down"]
    assert tel and tel[-1]["models_used"][0]["model"] == HEAD
    # promote journalled, trial succeeded -> slot back UP
    ev = [e for e in _events(env["data"], "CASCADE_SLOT")
          if e.get("trigger") == "cooldown_expired"]
    assert ev and ev[-1]["model"] == HEAD and ev[-1]["to_state"] == "HALF_OPEN"
    assert _slot(env["data"], HEAD)["state"] == "UP"


# ---------------------------------------------------------------- T2 -------

def test_t2_fresh_5xx_cooldowns_then_expires_then_recovers(env, monkeypatch):
    """5xx/timeout -> 10-min COOLDOWN (until in the FUTURE) -> correctly
    unavailable (all_slots_down, silence law) -> once the clock expires
    (simulated on the sandbox state file, exactly the on-disk situation
    production is stuck in) -> promoted -> verdict."""
    def boom(m, s, p):
        raise P.ProviderHTTPError(f"upstream 500 from {m}", status=500)
    out = _produce_v3(env, monkeypatch, transport=boom)
    assert out["written"] == 0                    # silence, no verdict
    slot = _slot(env["data"], HEAD)
    assert slot["state"] == "COOLDOWN" and slot["cooldown_reason"] == \
        "HTTP_5XX_OR_TIMEOUT"
    assert datetime.strptime(slot["cooldown_until_utc"], NOW_FMT).replace(
        tzinfo=timezone.utc) > datetime.now(timezone.utc) - \
        timedelta(seconds=1)
    assert "m1" in G._load_pending(env["data"], sandbox=True)  # QD2 intact
    # still inside the window: no promote, no verdict (law unchanged)
    out2 = _produce_v3(env, monkeypatch, transport=boom, mark=False)
    assert out2["written"] == 0
    # clock expires (sandbox state file = the stuck production state)
    past = _iso(datetime.now(timezone.utc) - timedelta(minutes=1))
    _set_slot(env["data"], HEAD, state="COOLDOWN", until=past,
              reason="HTTP_5XX_OR_TIMEOUT")
    _set_slot(env["data"], TAIL, state="COOLDOWN", until=past,
              reason="HTTP_5XX_OR_TIMEOUT")
    out3 = _produce_v3(env, monkeypatch, transport=lambda m, s, p: {
        "content": U3._valid("VETO")}, mark=False)
    assert out3["written"] == 1, out3
    assert _slot(env["data"], HEAD)["state"] == "UP"


# ---------------------------------------------------------------- T3 -------

def test_t3_402_hold_law_unchanged_balance_revive_only(env, monkeypatch):
    """HTTP 402 -> ALL paid slots held (indefinite, no expiry — promote must
    NOT touch them); the ONLY revive is a successful balance check."""
    def boom402(m, s, p):
        raise P.ProviderHTTPError(f"402 from {m}", status=402)
    _mark_pending_sb(env["data"])
    U3._produce(env, monkeypatch, transport=boom402,
                models=[HEAD, TAIL], low=10.0, mark=False, sandbox=True)
    slot = _slot(env["data"], HEAD)
    assert slot["state"] == "COOLDOWN" and \
        slot["cooldown_reason"] == "HTTP_402" and \
        slot["cooldown_until_utc"] is None          # indefinite hold
    assert _events(env["data"], "AI_LOW_BALANCE")
    # a stale-expiry-looking edit must NOT un-hold a 402 slot: no until,
    # nothing to promote; only the balance check revives (balance 15 >= 10)
    # (legacy path: the transport returns the raw model STRING)
    out = U3._produce(env, monkeypatch, transport=lambda m, s, p:
                      U3._valid("VETO"), models=[HEAD, TAIL], low=10.0,
                      balance_transport=lambda *a: {"data":
                                                    {"limit_remaining": 15.0}},
                      mark=False, sandbox=True)
    assert out["written"] == 1
    rev = [e for e in _events(env["data"], "CASCADE_SLOT")
           if e.get("trigger") == "balance_check_ok"]
    assert rev and _slot(env["data"], HEAD)["state"] == "UP"


# ---------------------------------------------------------------- T4 -------

def test_t4_all_slots_cooldown_inside_window_silence_law(env, monkeypatch):
    """Every slot COOLDOWN with a FUTURE expiry -> all_slots_down -> the
    candidate stays PENDING (never killed, never forced) — W4.4 unchanged."""
    future = _iso(datetime.now(timezone.utc) + timedelta(minutes=9))
    _set_slot(env["data"], HEAD, state="COOLDOWN", until=future,
              reason="HTTP_5XX_OR_TIMEOUT")
    _set_slot(env["data"], TAIL, state="COOLDOWN", until=future,
              reason="HTTP_5XX_OR_TIMEOUT")
    out = _produce_v3(env, monkeypatch, transport=lambda m, s, p: {
        "content": U3._valid("ALLOW")}, mark=True)
    assert out["written"] == 0
    tel = _telemetry(env["data"])
    assert tel and tel[-1]["outcome"] == "all_slots_down"
    assert _slot(env["data"], HEAD)["state"] == "COOLDOWN"   # untouched
    assert "m1" in G._load_pending(env["data"], sandbox=True)  # QD2 intact
