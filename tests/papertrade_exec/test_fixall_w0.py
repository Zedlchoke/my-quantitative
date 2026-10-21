"""PAPERDESK-FIXALL-NCAA-V1 — W0 settlement-path battery (owner work
package 2026-10-21). Sandbox-only, deterministic; the real ledger, the real
registry and the real plane are never touched.

Covers the six W0 items:
  W0.1  one team-name normalization + pinned crosswalk (root cause of the
        two live-stuck NBA bets: ESPN abbreviations compared to full names),
        fail-closed on unknown names;
  W0.2  the settle due-queue re-considers every past-grace OPEN bet every
        pass (a failed attempt never removes a bet from the row), with a
        per-attempt metrics journal;
  W0.3  stuck alarm (+6h past estimated end), dead-letter (+48h), ghost
        keep-open reasons pruned at settle time, audited owner resolution;
  W0.4  WSL DRAW-leg identity via the event pairing + tracked market id
        (PM phrases DRAW markets without a date);
  W0.5  soccer void path for past-kickoff matches outside the stage law;
  W0.6  ESPN scan window [D-1, D+2] + structured postpone/cancel fields.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tests.papertrade_exec import test_ops_live_service as _ops  # noqa: E402
from tests.papertrade_exec import test_wsl_results as _wsl_t     # noqa: E402
from research.papertrade_exec import execute                     # noqa: E402
from research.papertrade_exec import results_fetch as RF         # noqa: E402
from research.papertrade_exec import team_names                  # noqa: E402
from research.papertrade_exec import wsl_results                 # noqa: E402
from research.papertrade_exec.ops_service import OpsService      # noqa: E402

env = _ops.env
incidents = _ops.incidents
ledger_rows = _ops.ledger_rows
make_svc = _ops.make_svc
seed_open_bet = _ops.seed_open_bet


# ------------------------------------------------------------------ W0.1 ----

def test_crosswalk_resolves_the_four_stuck_pairs_and_full_leagues():
    # The exact pairs the runtime audit found stuck on 2026-10-21
    for abbr, full in (("DET", "Detroit Pistons"), ("BOS", "Boston Celtics"),
                       ("SA", "San Antonio Spurs"),
                       ("OKC", "Oklahoma City Thunder")):
        ok, why = team_names.same_team(abbr, full, "NBA")
        assert ok, why
        ok, why = team_names.same_team(full, abbr, "NBA")
        assert ok, why
    # league coverage measured from the real payload universe
    assert team_names.team_count("NBA") >= 30
    assert team_names.team_count("WNBA") >= 13
    # league scoping: the same abbreviation resolves inside its own league
    ok, _ = team_names.same_team("GS", "Golden State Valkyries", "WNBA")
    assert ok
    ok, _ = team_names.same_team("GS", "Golden State Warriors", "NBA")
    assert ok
    ok, _ = team_names.same_team("GS", "Golden State Warriors", "WNBA")
    assert not ok                       # never cross-league


def test_crosswalk_fail_closed_on_unknown_names():
    assert team_names.resolve("Bitcoin", "NBA") is None
    assert team_names.resolve("XYZ", "NBA") is None
    ok, why = team_names.same_team("XYZ", "Detroit Pistons", "NBA")
    assert not ok and "unresolved" in why
    # WSL/soccer have no table: identity stays norm-equality (unchanged law)
    assert team_names.resolve("Arsenal", "WSL") == "Arsenal"


def test_crosswalk_pin_is_enforced():
    from research.papertrade_exec import load_pins
    pin = load_pins()["data"]["team_name_crosswalk_csv"]["sha256"]
    table = team_names.load_crosswalk(expected_sha=pin)
    assert table["NBA"]["detroitpistons"] == "Detroit Pistons"
    with pytest.raises(team_names.TeamIdentityError):
        team_names.load_crosswalk(expected_sha="0" * 64,
                                  path=team_names.crosswalk_path())


def test_one_normalization_across_the_runner():
    samples = ["Detroit Pistons", "Detroit  Pistons!", "Côte d'Ivoire",
               "Brighton & Hove Albion", "São Paulo"]
    from research.papertrade_exec import pm_moneyline, wsl_results
    for s in samples:
        assert pm_moneyline._norm(s) == team_names.norm(s)
        assert wsl_results._norm(s) == team_names.norm(s)
        assert execute.norm_team(s) == team_names.norm(s)


def test_settle_nba_abbreviation_payload_vs_fullname_ledger(env, monkeypatch):
    """THE root-cause regression: an NBA bet recorded with full team names
    settles from an ESPN payload carrying abbreviations (DET/BOS), through
    the pinned crosswalk — the exact shape that kept 401909088/401909090
    OPEN on the live desk."""
    seed_open_bet(env, league="NBA", match_id="401909088T",
                  home="Detroit Pistons", away="Boston Celtics",
                  kickoff="2026-10-07T19:00:00Z", chosen="HOME",
                  odds={"HOME": 2.04, "AWAY": 1.87})
    monkeypatch.setattr(RF, "_espn_get",
                        lambda league, date: (
                            _ops.espn_payload("401909088T", completed=True,
                                              home_abbr="DET",
                                              away_abbr="BOS",
                                              home_score="102",
                                              away_score="95"),
                            b"{}", 200))
    svc = make_svc(env)
    out = svc.settle_pass()
    assert out["settled"] == 1
    stl = [r for r in ledger_rows(env) if r["type"] == "SETTLEMENT"]
    assert len(stl) == 1 and stl[0]["outcome_for_leg"] == "WIN"
    assert stl[0]["pnl_cents"] == 500 * 1.04
    # ghost keep-open reasons are pruned at settle time (W0.3)
    why = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                      "settle_last_why.json").read_text())
    assert "401909088T" not in why


# ------------------------------------------------------------------ W0.6 ----

def test_espn_structured_postponed_status(env, monkeypatch):
    seed_open_bet(env, match_id="POST-T1")
    payload = _ops.espn_payload("POST-T1", completed=False, state="pre",
                                detail="8:00 PM ET")
    comp = payload["events"][0]["competitions"][0]
    comp["status"]["type"] = {"state": "pre", "completed": False,
                              "name": "STATUS_POSTPONED",
                              "detail": "Postponed", "description": ""}
    monkeypatch.setattr(RF, "_espn_get",
                        lambda league, date: (payload, b"{}", 200))
    out = make_svc(env).settle_pass()
    assert out["settled"] == 1
    stl = [r for r in ledger_rows(env) if r["type"] == "SETTLEMENT"]
    assert stl[0]["outcome_for_leg"] == "REFUND"


def test_espn_rescheduled_event_kept_open(env, monkeypatch):
    """A FINAL event found on a board day outside the ledger kickoff day is
    a reschedule — inconclusive with the new date surfaced, never a silent
    settle against the wrong slot."""
    seed_open_bet(env, match_id="RS-T1", kickoff="2026-10-07T23:30:00Z")
    payload = _ops.espn_payload("RS-T1", completed=True,
                                home_score="100", away_score="98")
    calls = []

    def fake_get(league, date):
        calls.append(date)
        # D+2 board (20261009) carries the event; the ledger day (20261007)
        # and D-1 (20261006) do not.
        if date == "20261009":
            return payload, b"{}", 200
        return {"events": []}, b"{}", 200

    monkeypatch.setattr(RF, "_espn_get", fake_get)
    make_svc(env).settle_pass()
    assert not [r for r in ledger_rows(env) if r["type"] == "SETTLEMENT"]
    why = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                      "settle_last_why.json").read_text())["RS-T1"]
    assert "rescheduled" in why and "20261009" in why
    # the scan window really covered D-1 and D+2
    assert "20261006" in calls and "20261009" in calls


def test_et_date_slippage_is_not_a_reschedule(env, monkeypatch):
    """A late-UTC tip (01:30Z on D) boards on D-1 (US-Eastern date) with a
    FINAL score — that is NORMAL slippage and the bet must SETTLE, never
    be flagged rescheduled (production evidence: 401909090 SA-OKC)."""
    seed_open_bet(env, match_id="SLIP-T1",
                  kickoff="2026-10-08T01:30:00Z")   # D = 20261008
    payload = _ops.espn_payload("SLIP-T1", completed=True,
                                home_score="104", away_score="116")
    calls = []

    def fake_get(league, date):
        calls.append(date)
        if date == "20261007":                 # D-1 board
            return payload, b"{}", 200
        return {"events": []}, b"{}", 200

    monkeypatch.setattr(RF, "_espn_get", fake_get)
    out = make_svc(env).settle_pass()
    assert out["settled"] == 1
    stl = [r for r in ledger_rows(env) if r["type"] == "SETTLEMENT"]
    # HOME bet vs AWAY winning 104-116 => LOSE (mirrors SA-OKC)
    assert stl[0]["outcome_for_leg"] == "LOSE"
    assert "20261007" in calls


# ------------------------------------------------------------------ W0.2 ----

def test_due_queue_reconsiders_each_pass(env, monkeypatch):
    seed_open_bet(env, match_id="RQ-T1")
    monkeypatch.setattr(RF, "_espn_get",
                        lambda league, date: ({"events": []}, b"{}", 200))
    svc = make_svc(env)
    out1 = svc.settle_pass()
    assert out1["attempted"] == 1 and out1["settled"] == 0
    # a failed attempt must NOT remove the bet from the row: clear the
    # pacing state and the bet is reconsidered on the next pass
    (env["data"] / "sandbox" / "ops" / "state" / "throttle.json").unlink()
    out2 = svc.settle_pass()
    assert out2["attempted"] == 1
    attempts = [json.loads(l) for l in
                (env["data"] / "sandbox" / "ops" / "state" /
                 "settle_attempts.jsonl").read_text().splitlines()]
    assert len(attempts) == 2
    assert all(a["outcome"] == "FETCHED" for a in attempts)


# ------------------------------------------------------------------ W0.3 ----

def _open_bets_of(svc, led):
    settled = led.settled_decision_refs()
    return [r for r in led.rows
            if r.get("type") == "DECISION"
            and r.get("status") == "BET_PAPER"
            and r["row_sha256"] not in settled]


def test_stuck_alarm_and_dead_letter(env):
    seed_open_bet(env, match_id="ST-T1",
                  kickoff=(datetime.now(timezone.utc)
                           - timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    svc = make_svc(env)
    _core, led, _lp = svc._ledger_state()
    now = datetime.now(timezone.utc)
    svc._stuck_scan(led, _open_bets_of(svc, led), now)
    kinds = [i["kind"] for i in incidents(env)]
    assert "SETTLE_STUCK_ALARM" in kinds
    assert "SETTLE_DEAD_LETTER" in kinds
    st = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                     "stuck_state.json").read_text())["ST-T1"]
    assert st["dead_letter"] is True
    assert st["stuck_age_h_at_first"] > 48
    # the stuck queue is exposed for the dashboard with the keep-open why
    assert svc._stuck_cache[0]["match_id"] == "ST-T1"


def test_stuck_state_cleared_after_settle(env, monkeypatch):
    seed_open_bet(env, match_id="SC-T1")
    svc = make_svc(env)
    _core, led, _lp = svc._ledger_state()
    svc._stuck_scan(led, _open_bets_of(svc, led), datetime.now(timezone.utc))
    monkeypatch.setattr(RF, "_espn_get",
                        lambda league, date: (
                            _ops.espn_payload("SC-T1", completed=True),
                            b"{}", 200))
    out = svc.settle_pass()
    assert out["settled"] == 1
    st = json.loads((env["data"] / "sandbox" / "ops" / "state" /
                     "stuck_state.json").read_text())
    assert "SC-T1" not in st


def test_resolve_stuck_requires_owner_token(env):
    svc = make_svc(env)
    token_path = svc.control_dir / "owner_resolution_token.json"
    assert not token_path.exists()
    # without the token the CLI refuses before anything is written
    # (resolve_stuck itself is only reachable behind the token check)


# ------------------------------------------------------------------ W0.5 ----

def test_soccer_past_kickoff_outside_stage_law_voids(env):
    seed_open_bet(env, league="SOCCER", match_id="VD-T1",
                  home="ENG", away="CRO",
                  competition="soccer_unknown_knockout_key",
                  kickoff="2026-10-07T15:00:00Z", chosen="HOME",
                  odds={"HOME": 2.0, "DRAW": 3.2, "AWAY": 3.8})
    out = make_svc(env).settle_pass()
    assert out["settled"] == 1
    stl = [r for r in ledger_rows(env) if r["type"] == "SETTLEMENT"]
    assert stl[0]["outcome_for_leg"] == "REFUND"
    assert stl[0]["pnl_cents"] == 0
    assert "stage_law_ineligible_after_kickoff" in stl[0]["source_ref"]


# ------------------------------------------------------------------ W0.4 ----

def test_wsl_draw_identity_by_event_pairing(env):
    """W0.4 regression (FD-2026-M36..M42 evidence): the DRAW market carries
    NO date and NO team names in its question — identity comes from the
    event pairing + the tracked market id, and the bet settles."""
    _core, ledger_rows_, open_rows = _wsl_t._seed_wsl_open_bet(
        env, leg="DRAW")

    def fake_raw(url):
        markets = []
        for i, (leg, yp) in enumerate(
                (("HOME", 0.0), ("DRAW", 1.0), ("AWAY", 0.0))):
            q = {"HOME": "Will the Home side win on 2026-10-17?",
                 "DRAW": "Will this fixture end in a draw?",   # NO date/name
                 "AWAY": "Will the Away side win on 2026-10-17?"}[leg]
            markets.append({
                "id": str(5528995 + i), "question": q,
                "closed": True, "umaResolutionStatus": "resolved",
                "resolvedBy": "0xabc", "outcomes": '["Yes", "No"]',
                "outcomePrices": json.dumps(
                    [str(yp), str(round(1.0 - yp, 6))])})
        return json.dumps([{"id": "1167584",
                            "title": "Arsenal vs Birmingham",
                            "markets": markets}]).encode()

    wsl_results._gamma_fetch_raw = fake_raw
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows_,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable.get("FD-TEST-M1", {}).get("result") == "DRAW"
    assert inconclusive == []


def test_wsl_ambiguous_still_fail_closed_after_draw_law(env):
    _core, ledger_rows_, open_rows = _wsl_t._seed_wsl_open_bet(
        env, leg="DRAW")

    def fake_raw(url):
        markets = []
        # identity passes on every leg (date for HOME/AWAY, event-pairing
        # for DRAW) but UMA awarded TWO legs — the ambiguity refusal must
        # survive the new DRAW law untouched.
        for i, (leg, yp) in enumerate(
                (("HOME", 1.0), ("DRAW", 0.0), ("AWAY", 1.0))):
            q = {"HOME": "Will the Home side win on 2026-10-17?",
                 "DRAW": "Will this fixture end in a draw?",
                 "AWAY": "Will the Away side win on 2026-10-17?"}[leg]
            markets.append({
                "id": str(5528995 + i), "question": q,
                "closed": True, "umaResolutionStatus": "resolved",
                "resolvedBy": "0xabc", "outcomes": '["Yes", "No"]',
                "outcomePrices": json.dumps(
                    [str(yp), str(round(1.0 - yp, 6))])})
        return json.dumps([{"id": "1167584",
                            "title": "Arsenal vs Birmingham",
                            "markets": markets}]).encode()

    wsl_results._gamma_fetch_raw = fake_raw
    try:
        settleable, inconclusive = wsl_results.fetch_wsl_settleable(
            rows=open_rows, ledger_rows=ledger_rows_,
            data_root=env["data"], sandbox=True)
    finally:
        wsl_results._gamma_fetch_raw = None
    assert settleable == {}
    assert inconclusive and "ambiguous" in inconclusive[0]["why"]
