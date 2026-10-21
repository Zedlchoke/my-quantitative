"""PAPERDESK-FIXALL-NCAA-V1 — W1 battery (owner work package 2026-10-21).

W1.1  inactive soccer sport keys poll at most once per UTC day (the
      runtime audit measured 232-282 wasted 404 calls/day against
      soccer_fifa_world_cup_group);
W1.2  credit calls obey the PROVIDER-credit meter (2 credits per
      basketball odds call) + reconciliation journal + drift report;
W1.3  constant-forecast batches are blocked on the decide path
      (BLOCKED_CONSTANT_FORECAST) + the refresh lookback root-cause fix;
W1.4  one odds snapshot can never price two fixtures
      (NOT_RUN_QUOTE_COLLISION), on the standard AND the WSL decide path;
W1.5  EV_net > 100% quarantines the candidate (second-source PM
      cross-check; terminal NOT_PLACED_EV_OUTLIER when both sources
      agree or retries exhaust);
W1.6  ONE constant law source: laws.py -> generated JS, parity-tested;
W1.7  pause-watch startup silence, incident storm collapse,
      DASHBOARD_REBUILT demoted to the metrics plane.
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
from research.papertrade_exec import adapters as A                # noqa: E402
from research.papertrade_exec import execute                      # noqa: E402
from research.papertrade_exec import laws                         # noqa: E402
from research.papertrade_exec import quota_guard                  # noqa: E402
from research.papertrade_exec import results_fetch as RF          # noqa: E402
from research.papertrade_exec.ops_service import OpsService       # noqa: E402

env = _ops.env
incidents = _ops.incidents
ledger_rows = _ops.ledger_rows
make_svc = _ops.make_svc


FX = A.Fixture(league="NBA", match_id="m1", home="Detroit Pistons",
               away="Boston Celtics", kickoff_utc="2026-10-08T19:00:00Z",
               competition="NBA", et_local_date="2026-10-08",
               source_ref="TEST-SANDBOX-FIXTURE")


def _sandbox_ledger(env):
    core = execute.load_pinned_core(roots={})
    led = core.ledger.PaperLedger(_ops.sandbox_ledger_path(env)).load()
    led.genesis(plan_sha256="w1-test", sandbox=True)
    return led


def _seed_chain(led, match_id="m1", *, odds=None, kickoff="2026-10-08T19:00:00Z",
                p=None, bookmaker="pinnacle"):
    outcomes = ["HOME", "AWAY"]
    odds = odds or {"HOME": 2.0, "AWAY": 1.9}
    p = p or {"HOME": 0.55, "AWAY": 0.45}
    common = {"league": "NBA", "match_id": match_id, "home": FX.home,
              "away": FX.away, "competition": "NBA", "kickoff_utc": kickoff}
    led.append({"type": "FORECAST", **common, "p": p,
                "model_version_sha": "TEST", "recorded_at_utc":
                    "2026-10-08T00:00:00Z",
                "anchor_utc": "2026-10-08T12:50:00Z",
                "mode": "SYNTHETIC", "source_ref": "TEST",
                "fixture_source": "TEST"})
    led.append({"type": "MARKET_QUOTE", **common, "odds": odds,
                "bookmaker": bookmaker, "market": "h2h",
                "fetch_ts_utc": "2026-10-08T02:00:00Z",
                "source_last_update_utc": "2026-10-08T01:00:00Z",
                "commence_time_utc": kickoff, "payload_sha256": "0" * 64,
                "key_fingerprint": None, "mode": "REAL",
                "source_ref": "TEST"})


DEC_ARGS = dict(league="NBA", date="2026-10-08", sandbox=True,
                sandbox_control_dir="/tmp/nonexistent-control",
                sandbox_registry="/tmp/nonexistent-registry.json",
                data_root="/tmp/nonexistent-data", now="2026-10-08T10:00:00Z")


def _run_decide(env, led, *, evaluate=None, fixtures=None):
    """Drive execute.cmd_decide against a REAL sandbox ledger with the gate
    plumbing mocked (the pinned decide laws are NOT mocked away — the
    guards under test live in cmd_decide itself)."""
    core = types.SimpleNamespace(
        risk=types.SimpleNamespace(
            evaluate_match=evaluate or (lambda *a, **k: {"status": "NO_EDGE",
                                                         "reason": "t"}),
            in_lock_recheck=lambda led, now, ok, capital_law=2:
                (lambda d: d)),
        stake_for_decision=lambda eq: 1000)
    args = argparse.Namespace(**DEC_ARGS)
    with mock.patch.object(execute, "require_gate", return_value=(True, "",
                                                                  None)), \
         mock.patch.object(execute, "verify_pins", return_value={}), \
         mock.patch.object(execute, "open_ledger",
                           return_value=(core, led)), \
         mock.patch.object(execute, "fixtures_for",
                           return_value=fixtures or [FX]), \
         mock.patch.object(execute, "capital_law_for", return_value=2):
        return execute.cmd_decide(args)


# ------------------------------------------------------------------ W1.1 ----

def test_inactive_key_window_law():
    assert execute._key_window_active("soccer_uefa_nations_league",
                                      "2026-10-21") is True
    assert execute._key_window_active("soccer_fifa_world_cup_group",
                                      "2026-10-21") is False
    assert execute._key_window_active("soccer_fifa_world_cup_group",
                                      "2030-06-10") is True


def test_inactive_key_polls_once_per_day(tmp_path):
    calls = {}

    class FakeClient:
        fingerprint = "t"

        def get_events(self, key):
            calls[key] = calls.get(key, 0) + 1
            return json.dumps([]).encode(), {}

    args = argparse.Namespace(data_root=str(tmp_path))
    # soccer_fifa_world_cup_group has no window covering 2026 -> inactive
    with mock.patch.object(execute, "_odds_for",
                           return_value=(None, None, FakeClient())):
        execute.real_soccer_fixtures(args, "2026-10-21")
        execute.real_soccer_fixtures(args, "2026-10-21")
    # the 404 key (2030 window) is polled at most ONCE/day; the active
    # UNL key keeps its normal cadence (2 plan-days requested here)
    assert calls.get("soccer_fifa_world_cup_group", 0) == 1
    assert calls.get("soccer_uefa_nations_league", 0) == 2


# ------------------------------------------------------------------ W1.2 ----

def test_provider_quota_guard_costs_and_caps(tmp_path):
    hdrs = {"x-requests-used": 0, "x-requests-remaining": 500}

    class FakeClient:
        fingerprint = "t"

        def get_odds(self, key, *, markets="h2h"):
            hdrs["x-requests-used"] += 2       # provider debits 2
            hdrs["x-requests-remaining"] -= 2
            return b"[]", dict(hdrs)

    g = quota_guard.ProviderQuotaGuard(tmp_path)
    c = g.guard(FakeClient())
    c.get_odds("basketball_wnba")
    c.get_odds("basketball_wnba")
    st = json.loads((tmp_path / "data" / "provider_quota_state.json")
                    .read_text())
    assert st["credits_day"] == 4              # 2 provider credits per call
    with pytest.raises(quota_guard.ProviderQuotaSkip):
        c.get_odds("basketball_wnba")          # would exceed the 4/day cap
    led = (tmp_path / "data" / "provider_quota_ledger.jsonl").read_text()
    assert "cost_credits" in led


def test_provider_quota_guard_drift_reported(tmp_path):
    hdrs = {"x-requests-used": 100, "x-requests-remaining": 400}

    class FakeClient:
        fingerprint = "t"

        def get_odds(self, key, *, markets="h2h"):
            hdrs["x-requests-used"] += 5       # provider moved MORE than
            return b"[]", dict(hdrs)           # the expected 2

    g = quota_guard.ProviderQuotaGuard(tmp_path)
    c = g.guard(FakeClient())
    c.get_odds("basketball_nba")               # baseline (no prev meter)
    c.get_odds("basketball_nba")               # delta 5 vs expected 2
    assert any(d["kind"] == "QUOTA_CREDIT_DRIFT" for d in g.drifts)


# ------------------------------------------------------------------ W1.3 ----

def test_constant_forecast_block():
    rows = [{"p": {"HOME": 0.640065, "AWAY": 0.359935}},
            {"p": {"HOME": 0.640065, "AWAY": 0.359935}},
            {"p": {"HOME": 0.640065, "AWAY": 0.359935}}]
    with pytest.raises(execute.BlockError) as ei:
        execute.constant_forecast_block(rows)
    assert ei.value.code == "BLOCKED_CONSTANT_FORECAST"
    # a normal (per-match) batch passes untouched
    execute.constant_forecast_block(
        [{"p": {"HOME": 0.61, "AWAY": 0.39}},
         {"p": {"HOME": 0.44, "AWAY": 0.56}}])
    execute.constant_forecast_block([{"p": {"HOME": 0.5, "AWAY": 0.5}}])


def test_nba_refresh_lookback_fix():
    days = A.nba_refresh_game_days("2026-10-20", "2026-10-22",
                                   lookback_days=14)
    assert days[0] == "20261006" and days[-1] == "20261022"
    assert len(days) == 17
    cfg = execute.load_config()
    assert cfg.get("nba_refresh_lookback_days") == 14


def test_decide_blocks_constant_batch(env):
    led = _sandbox_ledger(env)
    _seed_chain(led, "m1", p={"HOME": 0.640065, "AWAY": 0.359935})
    _seed_chain(led, "m2", p={"HOME": 0.640065, "AWAY": 0.359935})
    fx2 = A.Fixture(league="NBA", match_id="m2", home="San Antonio Spurs",
                    away="Oklahoma City Thunder",
                    kickoff_utc="2026-10-08T22:00:00Z", competition="NBA",
                    et_local_date="2026-10-08",
                    source_ref="TEST-SANDBOX-FIXTURE")
    with pytest.raises(execute.BlockError) as ei:
        _run_decide(env, led, fixtures=[FX, fx2])
    assert ei.value.code == "BLOCKED_CONSTANT_FORECAST"
    assert not [r for r in led.rows if r.get("type") == "DECISION"]


# ------------------------------------------------------------------ W1.4 ----

def test_quote_collision_unit(env):
    led = _sandbox_ledger(env)
    # PM book-walk arm: EXACT float equality of the full odds vector — the
    # 15-digit runtime evidence pair (M39 == M42) collides...
    _seed_chain(led, "m1", odds={"HOME": 5.647962497524461, "AWAY": 1.2})
    pm_rows = [r for r in led.rows if r.get("type") == "MARKET_QUOTE"]
    for r in pm_rows:
        r["bookmaker"] = "polymarket"          # WSL/PM family rows
    row2 = {"type": "MARKET_QUOTE", "league": "NBA", "match_id": "m2",
            "bookmaker": "polymarket",
            "odds": {"HOME": 5.647962497524461, "AWAY": 1.2}}
    assert execute.quote_collision(led, "m2", row2) == "m1"
    # ...while a genuinely different PM snapshot does not
    row3 = {"type": "MARKET_QUOTE", "league": "NBA", "match_id": "m2",
            "bookmaker": "polymarket",
            "odds": {"HOME": 5.647962497524462, "AWAY": 1.2}}
    assert execute.quote_collision(led, "m2", row3) is None
    # snapshot-bytes arm: identical payload_sha256 collides for ANY bookmaker
    row4 = {"type": "MARKET_QUOTE", "league": "NBA", "match_id": "m2",
            "bookmaker": "pinnacle", "payload_sha256": "a" * 64,
            "odds": {"HOME": 3.1, "AWAY": 1.4}}
    assert execute.quote_collision(led, "m2", row4) is None
    led.append(dict(row4, match_id="m1"))
    assert execute.quote_collision(led, "m2", row4) == "m1"
    # coarse bookmaker prices legitimately repeat — NEVER a collision
    _ops.sandbox_ledger_path(env).unlink()
    led2 = _sandbox_ledger(env)
    _seed_chain(led2, "m1", odds={"HOME": 1.85, "AWAY": 2.05})
    _seed_chain(led2, "m2", odds={"HOME": 1.85, "AWAY": 2.05},
                kickoff="2026-10-08T22:00:00Z")
    assert execute.quote_collision(
        led2, "m2",
        next(r for r in led2.rows if r.get("match_id") == "m2"
             and r.get("type") == "MARKET_QUOTE")) is None


def test_decide_refuses_colliding_quote(env):
    led = _sandbox_ledger(env)
    _seed_chain(led, "m1", odds={"HOME": 5.647962497524461, "AWAY": 1.2},
                p={"HOME": 0.61, "AWAY": 0.39}, bookmaker="polymarket")
    _seed_chain(led, "m2", odds={"HOME": 5.647962497524461, "AWAY": 1.2},
                kickoff="2026-10-08T22:00:00Z",
                p={"HOME": 0.44, "AWAY": 0.56}, bookmaker="polymarket")
    fx2 = A.Fixture(league="NBA", match_id="m2", home="San Antonio Spurs",
                    away="Oklahoma City Thunder",
                    kickoff_utc="2026-10-08T22:00:00Z", competition="NBA",
                    et_local_date="2026-10-08",
                    source_ref="TEST-SANDBOX-FIXTURE")
    reached = {"evaluate": 0}

    def evaluate(*a, **k):
        reached["evaluate"] += 1
        return {"status": "BET_PAPER", "chosen_leg": "HOME",
                "stake_cents": 500, "p_frozen": {"HOME": 0.5},
                "odds_frozen": {"HOME": 2.0},
                "ev_net_by_leg": {"HOME": 0.06, "AWAY": -0.1},
                "equity_at_decision_cents": 100000, "reason": "t"}

    out = _run_decide(env, led, evaluate=evaluate, fixtures=[FX, fx2])
    statuses = {j["match_id"]: j["status"] for j in out["journaled"]}
    # BOTH bets are refused: one snapshot must never price two fixtures —
    # m1 collides with m2's identical row exactly as m2 collides with m1.
    assert statuses["m1"] == "NOT_RUN_QUOTE_COLLISION"
    assert statuses["m2"] == "NOT_RUN_QUOTE_COLLISION"
    assert reached["evaluate"] == 0            # the EV math is never reached


# ------------------------------------------------------------------ W1.5 ----

def _bet_dec(evs):
    return {"status": "BET_PAPER", "chosen_leg": "HOME",
            "stake_cents": 500, "p_frozen": {"HOME": 0.2976},
            "odds_frozen": {"HOME": 10.04},
            "ev_net_by_leg": {"HOME": evs, "AWAY": -0.1},
            "equity_at_decision_cents": 100000, "reason": "t"}


def test_ev_outlier_quarantines_then_terminals(env):
    led = _sandbox_ledger(env)
    _seed_chain(led, "m1")
    # (a) second source disagrees -> quarantined (non-terminal)
    args = argparse.Namespace(**DEC_ARGS)
    args.pm_crosscheck = lambda fx: {"ok": True, "ev_net": 0.30,
                                     "odds": {"HOME": 3.0}}
    dec = _bet_dec(1.9668)                     # the live M39 shape
    row, kind = execute.ev_outlier_disposition(args, led, FX, dec, None,
                                               "2026-10-08T10:00:00Z")
    assert row["status"] == "QUARANTINED_EV_OUTLIER"
    # (b) second source AGREES the outlier -> terminal, never placed
    args.pm_crosscheck = lambda fx: {"ok": True, "ev_net": 2.5,
                                     "odds": {"HOME": 10.0}}
    row, _ = execute.ev_outlier_disposition(args, led, FX, dec, None,
                                            "2026-10-08T10:00:00Z")
    assert row["status"] == "NOT_PLACED_EV_OUTLIER"


def test_decide_quarantine_reentry_requires_fresh_quote(env):
    led = _sandbox_ledger(env)
    _seed_chain(led, "m1")
    led.append_decision({
        "type": "DECISION", "league": "NBA", "match_id": "m1",
        "competition": "NBA", "home": FX.home, "away": FX.away,
        "kickoff_utc": FX.kickoff_utc,
        "decided_at_utc": "2026-10-08T08:00:00Z",
        "status": "QUARANTINED_EV_OUTLIER", "reason": "prior quarantine",
        "stake_cents": 0, "chosen_leg": None})
    seen = {"evaluate": 0}

    def evaluate(*a, **k):
        seen["evaluate"] += 1
        return _bet_dec(0.06)                  # fresh quote says normal

    # no quote captured AFTER the quarantine -> still quarantined, no bet
    out = _run_decide(env, led, evaluate=evaluate)
    assert out["journaled"][0]["status"] == "QUARANTINED_EV_OUTLIER"
    assert seen["evaluate"] == 0
    # U4-M4 no-churn law: a second pass WITHOUT a fresh quote learns the
    # state on the OPS plane only — it must NOT append another
    # QUARANTINED ledger row (churn law).
    out = _run_decide(env, led, evaluate=evaluate)
    assert out["journaled"][0]["status"] == "QUARANTINED_EV_OUTLIER"
    assert len([r for r in led.rows
                if r.get("status") == "QUARANTINED_EV_OUTLIER"]) == 1
    assert seen["evaluate"] == 0
    # a FRESH quote (after the quarantine stamp) unlocks re-evaluation
    led.append({"type": "MARKET_QUOTE", "league": "NBA", "match_id": "m1",
                "home": FX.home, "away": FX.away, "competition": "NBA",
                "kickoff_utc": FX.kickoff_utc,
                "odds": {"HOME": 2.0, "AWAY": 1.9},
                "bookmaker": "pinnacle", "market": "h2h",
                "fetch_ts_utc": "2026-10-08T09:30:00Z",
                "source_last_update_utc": "2026-10-08T09:00:00Z",
                "commence_time_utc": FX.kickoff_utc,
                "payload_sha256": "1" * 64, "key_fingerprint": None,
                "mode": "REAL", "source_ref": "TEST-FRESH"})
    out = _run_decide(env, led, evaluate=evaluate)
    assert out["journaled"][0]["status"] == "BET_PAPER"
    assert seen["evaluate"] == 1


# ------------------------------------------------------------------ W1.6 ----

def test_laws_js_parity_and_builder_determinism():
    sys.path.insert(0, str(REPO / "research" / "papertrade_exec"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "laws_generated_under_test",
        REPO / "apps" / "paperdesk" / "main" / "laws_generated.js")
    # node-free parity: recompute the generated text and compare bytes
    from research.papertrade_exec import build_laws_js
    assert build_laws_js.build() == (REPO / "apps" / "paperdesk" / "main" /
                                     "laws_generated.js").read_text()
    generated = json.loads(build_laws_js.build().split("module.exports = ",
                                                       1)[1].rstrip().rstrip(";"))
    assert generated == laws.as_dict()
    # the pipeline module really consumes the single source
    from research.papertrade_exec import decision_pipeline
    assert decision_pipeline.EV_THRESHOLD == laws.EV_THRESHOLD
    assert decision_pipeline.FLAT_FEE_PRE_CUTOVER == \
        laws.FLAT_FEE_PRE_CUTOVER


# ------------------------------------------------------------------ W1.7 ----

def test_pause_watch_startup_silent_and_transitions_journaled(env):
    svc = make_svc(env)
    ctrl = env["data"] / "sandbox" / "ops" / "control"
    # startup with the flag present -> exactly ONE informative PAUSED row
    (ctrl / "pause_decisions.flag").write_text(
        json.dumps({"by": "test", "at_utc": "2026-10-21T00:00:00Z",
                    "reason": "test"}))
    svc._pause_watch()
    svc._pause_watch()
    kinds = [i["kind"] for i in incidents(env)]
    assert kinds.count("DECISIONS_PAUSED_BY_UI") == 1
    # flag removed -> exactly ONE RESUMED carrying the last pause payload
    (ctrl / "pause_decisions.flag").unlink()
    svc._pause_watch()
    kinds = [i["kind"] for i in incidents(env)]
    assert kinds.count("DECISIONS_RESUMED_BY_UI") == 1
    # a SECOND fresh service starting unpaused journals NOTHING (the W1.7
    # spurious-RESUMED fix)
    svc2 = make_svc(env)
    svc2._pause_watch()
    svc2._pause_watch()
    kinds = [i["kind"] for i in incidents(env)]
    assert kinds.count("DECISIONS_RESUMED_BY_UI") == 1


def test_storm_collapse_and_metrics_plane(env):
    svc = make_svc(env)
    for _ in range(30):
        svc.incident("TICK_ERROR",
                     "FileNotFoundError: .../research/papertrade_exec/"
                     "pins.json")
    kinds = [i["kind"] for i in incidents(env)]
    # ONE row at the first occurrence + a re-journal every 25 occurrences
    # (law: 1 incident + counter + first/last; never a per-tick flood)
    assert kinds.count("TICK_ERROR") == 2
    st = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                     "incident_storms.json").read_text())
    entry = next(iter(st.values()))
    assert entry["count"] == 30 and entry["journaled_count"] == 26
    assert entry["first_utc"] and entry["last_utc"]
    # the metrics plane takes the high-frequency beats instead
    svc._metric("DASHBOARD_REBUILT", {"matches": 26})
    metrics = (env["data"] / "sandbox" / "ops" / "state" /
               "metrics.jsonl").read_text()
    assert "DASHBOARD_REBUILT" in metrics
    assert "DASHBOARD_REBUILT" not in [i["kind"] for i in incidents(env)]
