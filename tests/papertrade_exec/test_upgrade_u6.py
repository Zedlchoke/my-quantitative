"""PAPERDESK UPGRADE V2 — U6 battery: the CLV measurement plane.

MEASURE ONLY — nothing here touches a decision, the ledger, or a gate.
Covers, with BOTH fetchers stubbed (never real network):
  * the no-vig law hand-computed (2-way 1/1.5 + 1/2.8; 3-way analog),
  * every FORECAST match gets a close record (placed bet or not),
  * the honest NO_RUN paths (odds_fetch quota/exception -> NO_RUN_PINNACLE
    with the reason; pm_fetch None -> NO_RUN_PM),
  * one record per match per day (same-day re-call overwrites; the next
    day gets its own file),
  * placed-bet CLV sign cases on BOTH references (entry 2.10 vs close
    1.90 positive; entry 1.80 vs close 2.00 negative),
  * real vs sandbox sidecar path separation,
  * clv_report aggregation: per-league CLV mean/median/n, decision drift
    (forecast-time quote vs close), month buckets, raw TOA payload parse.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import clv_plane as CP          # noqa: E402
from research.papertrade_exec.quota_guard import ProviderQuotaSkip  # noqa

NOW = datetime(2026, 10, 21, 18, 0, 0, tzinfo=timezone.utc)
KICK = "2026-10-21T23:30:00Z"


def _forecast(match_id, league="NBA", home="ATL Dream", away="NY Liberty"):
    return {"type": "FORECAST", "league": league, "match_id": match_id,
            "home": home, "away": away, "kickoff_utc": KICK,
            "p": {"HOME": 0.6, "AWAY": 0.4},
            "model_id": "TEST_SYNTHETIC", "mode": "SYNTHETIC",
            "recorded_at_utc": "2026-10-21T12:00:00Z",
            "source_ref": "TEST-SANDBOX-FABRICATION"}


def _bet(match_id, chosen="HOME", odds=None, stake=500):
    return {"type": "DECISION", "league": "NBA", "match_id": match_id,
            "home": "ATL Dream", "away": "NY Liberty",
            "kickoff_utc": KICK,
            "decided_at_utc": "2026-10-21T12:06:00Z",
            "stake_cents": stake, "chosen_leg": chosen,
            "p_frozen": {"HOME": 0.6, "AWAY": 0.4},
            "odds_frozen": odds or {"HOME": 2.10, "AWAY": 1.80},
            "status": "BET_PAPER", "reason": "TEST-SANDBOX-FABRICATION"}


def _quote(match_id, odds=None):
    return {"type": "MARKET_QUOTE", "league": "NBA",
            "match_id": match_id, "home": "ATL Dream",
            "away": "NY Liberty", "kickoff_utc": KICK,
            "odds": odds or {"HOME": 2.00, "AWAY": 1.87},
            "bookmaker": "pinnacle", "market": "h2h",
            "fetch_ts_utc": "2026-10-21T12:05:00Z",
            "source_ref": "TEST-SANDBOX-FABRICATION"}


def _pin_ok(sport_key, mids):
    assert sport_key == "basketball_nba"
    return {m: {"HOME": 1.90, "AWAY": 2.00} for m in mids}


def _pm_ok(home, away):
    return {"HOME": 0.50, "AWAY": 0.52}


# --------------------------------- the no-vig law (hand-computed) -----------

def test_no_vig_2way_hand_computed():
    # 1/1.5 + 1/2.8 = 2/3 + 5/14 = 43/42 -> normalized 28/43, 15/43
    p = CP.no_vig_probabilities({"HOME": 1.5, "AWAY": 2.8})
    assert p["HOME"] == pytest.approx(float(Fraction(28, 43)))
    assert p["AWAY"] == pytest.approx(float(Fraction(15, 43)))
    assert p["HOME"] + p["AWAY"] == pytest.approx(1.0)


def test_no_vig_3way_hand_computed():
    # 1/2.9 + 1/3.5 + 1/2.6 = 10/29 + 2/7 + 5/13
    odds = {"HOME": 2.9, "DRAW": 3.5, "AWAY": 2.6}
    inv = [Fraction(10, 29), Fraction(2, 7), Fraction(5, 13)]
    s = sum(inv)
    p = CP.no_vig_probabilities(odds)
    for leg, f in zip(("HOME", "DRAW", "AWAY"), inv):
        assert p[leg] == pytest.approx(float(f / s))
    assert sum(p.values()) == pytest.approx(1.0)
    # degenerate inputs are refused, never normalized by invention
    assert CP.no_vig_probabilities({"HOME": 1.5}) is None
    assert CP.no_vig_probabilities({"HOME": 0.9, "AWAY": 2.0}) is None
    assert CP.no_vig_probabilities({}) is None
    assert CP.no_vig_probabilities(None) is None


# --------------------------------- records: every FORECAST match ------------

def test_every_forecast_match_gets_a_record_entry_only_when_placed(tmp_path):
    rows = [_forecast("401A"), _forecast("401B"),
            _bet("401A"), _quote("401A"), _quote("401B")]
    summary = CP.record_closing_quotes(
        ledger_rows=rows, data_root=tmp_path, sandbox=True,
        odds_fetch=_pin_ok, pm_fetch=_pm_ok, now_utc=NOW)
    d = tmp_path / "sandbox" / "ops" / "clv"
    assert summary["records"] == 2 and summary["pin_ok"] == 2
    assert summary["pm_ok"] == 2 and summary["sidecar_dir"] == str(d)
    ra = json.loads((d / "clv_NBA_401A_20261021.json").read_text())
    rb = json.loads((d / "clv_NBA_401B_20261021.json").read_text())
    for r in (ra, rb):
        assert r["schema"] == "clv_close@1" and r["status"] == "OK"
        assert r["pin_close"] == {"HOME": 1.9, "AWAY": 2.0}
        assert r["pm_close"] == {"HOME": 0.5, "AWAY": 0.52}
        assert r["sampled_at_utc"] == "2026-10-21T18:00:00Z"
        s = sum(r["pin_novig_prob"].values())
        assert s == pytest.approx(1.0)
    # entry attaches ONLY to the placed bet; forecast-only stays bare
    assert ra["entry"] == {"chosen_leg": "HOME", "entry_decimal": 2.10,
                           "stake_cents": 500}
    assert rb["entry"] is None
    # forecast-time quote carried for the drift measurement
    assert ra["forecast_quote"]["odds"] == {"HOME": 2.0, "AWAY": 1.87}


def test_odds_fetch_called_once_per_league_with_all_match_ids(tmp_path):
    seen = []

    def odds_fetch(sport_key, mids):
        seen.append((sport_key, tuple(mids)))
        return _pin_ok(sport_key, mids)

    rows = [_forecast("401A"), _forecast("401B"), _forecast("401C")]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=odds_fetch,
                             pm_fetch=_pm_ok, now_utc=NOW)
    assert seen == [("basketball_nba", ("401A", "401B", "401C"))]


# --------------------------------- honest NO_RUN paths ----------------------

def test_quota_skip_records_no_run_pin_with_reason(tmp_path):
    def quota(sport_key, mids):
        raise ProviderQuotaSkip("odds:basketball_nba would exceed the caps")

    rows = [_forecast("401A"), _bet("401A")]
    summary = CP.record_closing_quotes(
        ledger_rows=rows, data_root=tmp_path, sandbox=True,
        odds_fetch=quota, pm_fetch=_pm_ok, now_utc=NOW)
    assert summary["no_run_pin"] == 1 and summary["pin_ok"] == 0
    rec = json.loads((tmp_path / "sandbox" / "ops" / "clv" /
                      "clv_NBA_401A_20261021.json").read_text())
    assert rec["pin_status"] == "NO_RUN_PINNACLE"
    assert rec["pin_close"] is None and rec["pin_novig_prob"] is None
    assert "quota" in rec["why_pin"]
    assert rec["pm_status"] == "OK"          # PM side measured anyway
    assert rec["status"] == "NO_RUN_PINNACLE"


def test_arbitrary_exception_is_no_run_too(tmp_path):
    def boom(sport_key, mids):
        raise RuntimeError("provider 502")

    rows = [_forecast("401A")]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=boom,
                             pm_fetch=_pm_ok, now_utc=NOW)
    rec = json.loads((tmp_path / "sandbox" / "ops" / "clv" /
                      "clv_NBA_401A_20261021.json").read_text())
    assert rec["pin_status"] == "NO_RUN_PINNACLE"
    assert "error: RuntimeError" in rec["why_pin"]


def test_pm_none_records_no_run_pm(tmp_path):
    rows = [_forecast("401A")]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=_pin_ok,
                             pm_fetch=lambda h, a: None, now_utc=NOW)
    rec = json.loads((tmp_path / "sandbox" / "ops" / "clv" /
                      "clv_NBA_401A_20261021.json").read_text())
    assert rec["pm_status"] == "NO_RUN_PM" and rec["pm_close"] is None
    assert rec["why_pm"] and rec["status"] == "NO_RUN_PM"
    assert rec["pin_status"] == "OK"         # pin side measured anyway

    def boom(h, a):
        raise RuntimeError("pm down")

    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=_pin_ok,
                             pm_fetch=boom, now_utc=NOW)
    rec2 = json.loads((tmp_path / "sandbox" / "ops" / "clv" /
                       "clv_NBA_401A_20261021.json").read_text())
    assert rec2["pm_status"] == "NO_RUN_PM"
    assert "pm down" in rec2["why_pm"]


def test_unmapped_odds_payload_is_no_run_not_invented(tmp_path):
    rows = [_forecast("401A")]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True,
                             odds_fetch=lambda s, m: {"401B": {
                                 "HOME": 1.9, "AWAY": 2.0}},
                             pm_fetch=_pm_ok, now_utc=NOW)
    rec = json.loads((tmp_path / "sandbox" / "ops" / "clv" /
                      "clv_NBA_401A_20261021.json").read_text())
    assert rec["pin_status"] == "NO_RUN_PINNACLE"
    assert "absent" in rec["why_pin"]


# --------------------------------- one record per match per day -------------

def test_one_record_per_match_per_day(tmp_path):
    rows = [_forecast("401A")]
    for _ in range(3):                      # same-day re-calls overwrite
        CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                                 sandbox=True, odds_fetch=_pin_ok,
                                 pm_fetch=_pm_ok, now_utc=NOW)
    d = tmp_path / "sandbox" / "ops" / "clv"
    files = list(d.glob("clv_NBA_401A_*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text())["sampled_day"] == "20261021"
    # the next calendar day gets its own record
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=_pin_ok,
                             pm_fetch=_pm_ok,
                             now_utc=NOW + timedelta(days=1))
    assert len(list(d.glob("clv_NBA_401A_*.json"))) == 2
    assert (d / "clv_NBA_401A_20261022.json").exists()


# --------------------------------- placed-bet CLV sign cases ----------------

def test_placed_bet_clv_sign_cases_both_references(tmp_path):
    # bet A: HOME @ 2.10, pin close 1.90 -> +10.5%; PM 0.50 -> +5.0%
    # bet B: AWAY @ 1.80, pin close 1.90 -> -10.0%; PM 0.48 -> -13.6%
    # bet C: HOME @ 1.95, pin close 1.90 ->  +2.6%; PM 0.55 ->  +7.25%
    rows = [_forecast("401A"), _bet("401A", chosen="HOME",
                                    odds={"HOME": 2.10, "AWAY": 1.80}),
            _quote("401A", odds={"HOME": 2.00, "AWAY": 1.87}),
            _forecast("401B", home="CHI Sky", away="CONN Sun"),
            _bet("401B", chosen="AWAY", odds={"HOME": 2.00, "AWAY": 1.80}),
            _quote("401B", odds={"HOME": 2.00, "AWAY": 1.87}),
            _forecast("401C", home="SEA Storm", away="LV Aces"),
            _bet("401C", chosen="HOME", odds={"HOME": 1.95, "AWAY": 1.95})]

    def pin(sport_key, mids):
        out = {m: {"HOME": 1.90, "AWAY": 2.00} for m in mids}
        out["401B"] = {"HOME": 2.00, "AWAY": 1.90}   # close per match
        return out

    def pm(home, away):
        if home == "ATL Dream":
            return {"HOME": 0.50, "AWAY": 0.52}
        if home == "CHI Sky":
            return {"HOME": 0.55, "AWAY": 0.48}
        return {"HOME": 0.55, "AWAY": 0.52}

    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=pin, pm_fetch=pm,
                             now_utc=NOW)
    rep = CP.clv_report(tmp_path / "sandbox" / "ops" / "clv")
    lg = rep["leagues"]["NBA"]
    clv_a = 2.10 / 1.90 - 1
    clv_b = 1.80 / 1.90 - 1
    clv_c = 1.95 / 1.90 - 1
    assert lg["placed_bets"] == 3 and lg["n_records"] == 3
    assert lg["clv_pin"]["n"] == 3
    assert lg["clv_pin"]["mean"] == pytest.approx(
        round((clv_a + clv_b + clv_c) / 3, 6))
    assert lg["clv_pin"]["median"] == pytest.approx(round(clv_c, 6))
    assert lg["clv_pm"]["n"] == 3
    assert lg["clv_pm"]["mean"] == pytest.approx(
        round(((2.10 * 0.50 - 1) + (1.80 * 0.48 - 1)
               + (1.95 * 0.55 - 1)) / 3, 6))
    # signs: A and C beat the close (+), B lost to it (-)
    assert clv_a > 0 and clv_c > 0 and clv_b < 0
    # all three land in the month bucket
    mb = lg["months"]["2026-10"]
    assert mb["n"] == 3 and mb["clv_pin"]["n"] == 3
    assert mb["clv_pin"]["mean"] == lg["clv_pin"]["mean"]
    # decision drift: forecast quote vs close per common leg (C has no
    # forecast quote on file -> drift stays n=2, honestly)
    # 401A: (2.00/1.90-1 + 1.87/2.00-1)/2 ; 401B: (2.00/2.00-1 + 1.87/1.90-1)/2
    da = (2.00 / 1.90 - 1 + 1.87 / 2.00 - 1) / 2
    db = (2.00 / 2.00 - 1 + 1.87 / 1.90 - 1) / 2
    assert lg["decision_drift"]["n"] == 2
    assert lg["decision_drift"]["mean"] == pytest.approx(
        round((da + db) / 2, 6))


def test_report_excludes_unplaced_from_clv_but_counts_drift(tmp_path):
    rows = [_forecast("401A"), _quote("401A")]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=_pin_ok,
                             pm_fetch=_pm_ok, now_utc=NOW)
    rep = CP.clv_report(tmp_path / "sandbox" / "ops" / "clv")
    lg = rep["leagues"]["NBA"]
    assert lg["placed_bets"] == 0
    assert lg["clv_pin"]["n"] == 0 and lg["clv_pm"]["n"] == 0
    assert lg["clv_pin"]["mean"] is None
    assert lg["decision_drift"]["n"] == 1     # drift needs no placed bet


# --------------------------------- sandbox vs real path separation ----------

def test_sandbox_and_real_planes_are_separate(tmp_path):
    rows = [_forecast("401A")]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=_pin_ok,
                             pm_fetch=_pm_ok, now_utc=NOW)
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=False, odds_fetch=_pin_ok,
                             pm_fetch=_pm_ok, now_utc=NOW)
    assert (tmp_path / "sandbox" / "ops" / "clv" /
            "clv_NBA_401A_20261021.json").exists()
    assert (tmp_path / "ops" / "clv" /
            "clv_NBA_401A_20261021.json").exists()
    rep_s = CP.clv_report(tmp_path / "sandbox" / "ops" / "clv")
    rep_r = CP.clv_report(tmp_path / "ops" / "clv")
    assert rep_s["records"] == 1 and rep_r["records"] == 1
    # an empty sidecar dir reports honestly, never throws
    empty = CP.clv_report(tmp_path / "nowhere")
    assert empty["records"] == 0 and empty["leagues"] == {}


# --------------------------------- raw The-Odds-API payload shape -----------

def test_raw_toa_payload_parsed_with_pinnacle_preference(tmp_path):
    raw = [{"id": "401A", "bookmakers": [
        {"key": "fanduel", "markets": [{"key": "h2h", "outcomes": [
            {"name": "ATL Dream", "price": 1.5},
            {"name": "NY Liberty", "price": 2.5}]}]},
        {"key": "pinnacle", "markets": [{"key": "h2h", "outcomes": [
            {"name": "ATL Dream", "price": 1.9},
            {"name": "NY Liberty", "price": 2.0},
            {"name": "draw", "price": 12.0}]}]}]}]
    rows = [_forecast("401A")]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True,
                             odds_fetch=lambda s, m: raw,
                             pm_fetch=_pm_ok, now_utc=NOW)
    rec = json.loads((tmp_path / "sandbox" / "ops" / "clv" /
                      "clv_NBA_401A_20261021.json").read_text())
    assert rec["pin_close"] == {"AWAY": 2.0, "DRAW": 12.0, "HOME": 1.9}
    assert rec["pin_status"] == "OK"
    # no pinnacle on the board -> honest NO_RUN, never a fanduel stand-in
    raw_nopin = [{"id": "401A", "bookmakers": [
        {"key": "fanduel", "markets": [{"key": "h2h", "outcomes": [
            {"name": "ATL Dream", "price": 1.5}]}]}]}]
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True,
                             odds_fetch=lambda s, m: raw_nopin,
                             pm_fetch=_pm_ok, now_utc=NOW)
    rec2 = json.loads((tmp_path / "sandbox" / "ops" / "clv" /
                       "clv_NBA_401A_20261021.json").read_text())
    assert rec2["pin_status"] == "NO_RUN_PINNACLE"
    assert "pinnacle" in rec2["why_pin"]


# --------------------------------- measure-only guarantee -------------------

def test_measure_only_writes_nothing_but_sidecars(tmp_path):
    rows = [_forecast("401A"), _bet("401A"), _quote("401A")]
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    CP.record_closing_quotes(ledger_rows=rows, data_root=tmp_path,
                             sandbox=True, odds_fetch=_pin_ok,
                             pm_fetch=_pm_ok, now_utc=NOW)
    after = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    new_files = [str(p) for p in after - before
                 if (tmp_path / p).is_file()]
    assert new_files, "the closer must write its sidecar records"
    assert all(p.startswith("sandbox/ops/clv/") for p in new_files), \
        new_files
