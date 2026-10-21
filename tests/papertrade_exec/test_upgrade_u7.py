"""PAPERDESK UPGRADE V2 — U7 battery: NEW-LAW ERA (FROZEN SPEC + SHADOW).

All numbers SYNTHETIC (hand-computed); no network anywhere. Covers:
  1. evaluate(): the sharp-price gate (3% margin, PM fee ONCE), the
     log-odds blend at the PROVISIONAL w, the disagreement-scaled
     threshold, and every NO_RUN path — each against hand-computed
     expectations from the frozen spec's own formulas;
  2. shadow_recent_decisions(): journal path law (sandbox-aware), one
     record per candidate, hourly-tick DEDUP, SHADOW-ONLY note;
  3. ops wiring: the CLV hourly tick samples only near-kickoff FORECAST
     matches with a REAL sport key (WSL excluded), writes the U6 sidecar,
     never blocks on error (CLV_SAMPLE_ERROR); the shadow tick journals +
     incidents on error;
  4. the frozen spec's registered sha256 re-measures (digest-blanked
     formula) — the freeze is verifiable by anyone.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.papertrade_exec import new_law_shadow as S          # noqa
from research.papertrade_exec import clv_plane                    # noqa
from research.papertrade_exec.ops_service import OpsService       # noqa

NOW = datetime.now(timezone.utc)
SPEC = REPO / "research" / "control" / "PAPERDESK-FIXALL-NCAA-V1" / \
    "NEW_LAW_SPEC_FROZEN_V1.md"

# hand-computed reference frame: pin 1.5/2.8 -> no-vig {0.651163, 0.348837}
PIN = {"HOME": 1.5, "AWAY": 2.8}
P_PIN_HOME = (1 / 1.5) / (1 / 1.5 + 1 / 2.8)          # 0.651162790697674


def _fee_eff(pm_decimal: float) -> float:
    """PM fee ONCE: p + 0.05*p*(1-p) — the frozen law, spelled out."""
    p = 1.0 / pm_decimal
    return p + 0.05 * p * (1 - p)


# ------------------------------- 1) evaluate: the frozen law -----------------

def test_take_case_hand_computed():
    # p_pm_eff = 0.552959 < 0.651163*0.97 = 0.631628 -> gate PASS
    # blend(0.65, 0.651163, w=.5) = 0.650581; thr = .05+.5*.001163 = .050581
    # ev = 0.650581 - 0.552959 = 0.097623 >= thr -> TAKE
    r = S.evaluate(p={"HOME": 0.65, "AWAY": 0.35},
                   pm_odds={"HOME": 1.85, "AWAY": 2.00},
                   pin_odds=PIN, chosen_leg="HOME")
    assert r["action"] == "TAKE" and r["why"] == "EDGE_OK"
    assert r["p_pm_fee_adjusted"] == pytest.approx(_fee_eff(1.85), abs=1e-6)
    assert r["p_pin_leg"] == pytest.approx(P_PIN_HOME, abs=1e-6)
    assert r["threshold"] == pytest.approx(
        0.05 + 0.5 * abs(0.65 - P_PIN_HOME), abs=1e-6)
    assert r["ev_blend"] == pytest.approx(
        0.650581 - _fee_eff(1.85), abs=1e-5)
    # the blend NEVER uses the PM price: p_blend sits between model+pin
    assert 0.64 < r["p_blend"] < 0.66


def test_sharp_price_gate_skips_fair_price():
    # PM at the pin fair decimal (1.5): eff 0.677778 > 0.631628 -> SKIP
    r = S.evaluate(p={"HOME": 0.70, "AWAY": 0.30},
                   pm_odds={"HOME": 1.50, "AWAY": 2.60},
                   pin_odds=PIN, chosen_leg="HOME")
    assert r["action"] == "SKIP" and r["why"] == "SHARP_PRICE_GATE"
    # boundary characterization from BOTH strict sides of the margin:
    # solve p + 0.05p(1-p) = ref*0.97  ->  0.05p^2 - 1.05p + target = 0
    target = P_PIN_HOME * (1 - S.SHARP_PRICE_MARGIN)
    disc = 1.05 ** 2 - 4 * 0.05 * target
    p_at = (1.05 - disc ** 0.5) / (2 * 0.05)
    # a hair CHEAPER than the margin passes the gate, a hair MORE
    # EXPENSIVE flips to SKIP
    r_ok = S.evaluate(p={"HOME": 0.651, "AWAY": 0.349},
                      pm_odds={"HOME": 1.0 / (p_at * 0.999),
                               "AWAY": 2.60},
                      pin_odds=PIN, chosen_leg="HOME")
    assert r_ok["why"] != "SHARP_PRICE_GATE"
    r_bad = S.evaluate(p={"HOME": 0.651, "AWAY": 0.349},
                       pm_odds={"HOME": 1.0 / (p_at * 1.001),
                                "AWAY": 2.60},
                       pin_odds=PIN, chosen_leg="HOME")
    assert r_bad["why"] == "SHARP_PRICE_GATE"


def test_edge_below_skips_when_model_disagrees():
    # model 0.52 vs pin 0.651163: disagreement scales thr to 0.115582;
    # ev = blend - eff = -0.006438 -> SKIP EDGE_BELOW
    r = S.evaluate(p={"HOME": 0.52, "AWAY": 0.48},
                   pm_odds={"HOME": 1.72, "AWAY": 2.10},
                   pin_odds=PIN, chosen_leg="HOME")
    assert r["action"] == "SKIP" and r["why"] == "EDGE_BELOW"
    assert r["threshold"] == pytest.approx(
        0.05 + 0.5 * abs(0.52 - P_PIN_HOME), abs=1e-6)
    assert r["ev_blend"] < r["threshold"]


def test_no_run_paths_are_honest():
    base = dict(p={"HOME": 0.65, "AWAY": 0.35},
                pm_odds={"HOME": 1.85, "AWAY": 2.00}, pin_odds=PIN)
    assert S.evaluate(**base, chosen_leg="DRAW")["why"].startswith(
        "leg DRAW absent")
    assert S.evaluate(p={"HOME": 0.65, "AWAY": 0.35}, pm_odds=base["pm_odds"],
                      pin_odds={"HOME": 1.5}, chosen_leg="HOME")["why"] == \
        "pinnacle reference degenerate or leg absent"
    assert S.evaluate(p={"HOME": 0.65, "AWAY": 0.35},
                      pm_odds={"HOME": 1.0, "AWAY": 2.0},
                      pin_odds=PIN, chosen_leg="HOME")["why"].startswith(
        "degenerate pm decimal")
    assert S.evaluate(p=base["p"], pm_odds=None, pin_odds=PIN,
                      chosen_leg="HOME")["why"] == "pm quote leg absent"
    # absent chosen_leg -> honest best-leg scan, still the same law
    best = S.evaluate(p=base["p"], pm_odds=base["pm_odds"], pin_odds=PIN,
                      chosen_leg=None)
    assert best["action"] == "TAKE" and best["leg"] == "HOME" \
        and best["leg_selection"] == "shadow_best_leg"
    # constants mirror the frozen spec verbatim
    assert (S.SHARP_PRICE_MARGIN, S.EDGE_BASE, S.EDGE_DISAGREEMENT_K) == \
        (0.03, 0.05, 0.5)
    assert S.PROVISIONAL_W == 0.5          # labeled provisional, NOT a fit


# ------------------------------- 2) journal + dedup --------------------------

def _ledger_rows():
    ko = (NOW + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        {"type": "FORECAST", "league": "NBA", "match_id": "M1",
         "home": "A", "away": "B", "kickoff_utc": ko,
         "p": {"HOME": 0.65, "AWAY": 0.35}},
        {"type": "MARKET_QUOTE", "league": "NBA", "match_id": "M1",
         "bookmaker": "pinnacle", "odds": dict(PIN),
         "fetch_ts_utc": "2026-10-21T00:00:00Z"},
        {"type": "MARKET_QUOTE", "league": "NBA", "match_id": "M1",
         "bookmaker": "POLYMARKET_CLOB", "odds": {"HOME": 1.85,
                                                  "AWAY": 2.00},
         "fetch_ts_utc": "2026-10-21T00:01:00Z"},
        {"type": "DECISION", "league": "NBA", "match_id": "M1",
         "status": "BET_PAPER", "chosen_leg": "HOME",
         "odds_frozen": {"HOME": 1.85}, "kickoff_utc": ko},
    ]


def test_journal_sandbox_path_and_dedup(tmp_path):
    j = S.shadow_recent_decisions(ledger_rows=_ledger_rows(),
                                  data_root=tmp_path, sandbox=True)
    jp = tmp_path / "sandbox" / "ops" / "shadow_new_law.jsonl"
    assert j["journal"] == str(jp) and j["evaluated"] == 1
    assert jp.exists()
    row = json.loads(jp.read_text().splitlines()[0])
    assert row["schema"] == S.SCHEMA and row["match_id"] == "M1"
    assert row["action"] == "TAKE"
    assert "no production decision" in row["note"]
    # hourly re-tick: the SAME frozen inputs dedupe to ZERO new records
    j2 = S.shadow_recent_decisions(ledger_rows=_ledger_rows(),
                                   data_root=tmp_path, sandbox=True)
    assert j2["evaluated"] == 0
    assert len(jp.read_text().splitlines()) == 1


def test_journal_real_plane_separate(tmp_path):
    S.shadow_recent_decisions(ledger_rows=[], data_root=tmp_path,
                              sandbox=False)
    assert (tmp_path / "ops" / "shadow_new_law.jsonl").exists() is False
    S.shadow_recent_decisions(
        ledger_rows=[{"type": "FORECAST", "league": "NBA",
                      "match_id": "X", "home": "A", "away": "B",
                      "kickoff_utc": "2026-10-21T01:00:00Z",
                      "p": {"HOME": 0.6, "AWAY": 0.4}}],
        data_root=tmp_path, sandbox=False)
    assert (tmp_path / "ops" / "shadow_new_law.jsonl").exists()


# ------------------------------- 3) ops wiring -------------------------------

def make_svc(tmp_path) -> OpsService:
    svc = OpsService(data_root=tmp_path, sandbox=True, serve=False,
                     once=True)
    return svc


class _FakeLed:
    def __init__(self, rows):
        self.rows = rows


def test_clv_tick_samples_near_kickoff_only(tmp_path, monkeypatch):
    svc = make_svc(tmp_path)
    ko_near = NOW + timedelta(minutes=30)
    ko_far = NOW + timedelta(hours=10)
    rows = [
        {"type": "FORECAST", "league": "NBA", "match_id": "NEAR",
         "home": "A", "away": "B",
         "kickoff_utc": ko_near.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "p": {"HOME": 0.6, "AWAY": 0.4}},
        {"type": "FORECAST", "league": "NBA", "match_id": "FAR",
         "home": "C", "away": "D",
         "kickoff_utc": ko_far.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "p": {"HOME": 0.6, "AWAY": 0.4}},
        {"type": "FORECAST", "league": "WSL", "match_id": "WSLX",
         "home": "E", "away": "F",
         "kickoff_utc": ko_near.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "p": {"HOME": 0.6, "AWAY": 0.4}},
    ]
    monkeypatch.setattr(svc, "_ledger_state",
                        lambda: (None, _FakeLed(rows), None))
    seen = {}
    prices = {}

    def odds_fetch(sport_key, match_ids):
        seen["key"], seen["mids"] = sport_key, list(match_ids)
        return [{"id": "NEAR", "bookmakers": [
            {"key": "pinnacle", "markets": [{"key": "h2h", "outcomes": [
                {"name": "A", "price": 1.9}, {"name": "B", "price": 2.0}]}]}]}]

    def pm_fetch(home, away):
        prices["pair"] = (home, away)
        return {"HOME": 0.55, "AWAY": 0.47}

    monkeypatch.setattr(svc, "_clv_odds_fetch", odds_fetch)
    monkeypatch.setattr(svc, "_clv_pm_fetch", pm_fetch)
    svc._clv_closing_quotes()
    # only the near-kickoff NBA match: WSL has NO Pinnacle sport key
    assert seen["key"] == "basketball_nba" and seen["mids"] == ["NEAR"]
    side = tmp_path / "sandbox" / "ops" / "clv"
    files = list(side.glob("clv_*.json"))
    assert len(files) == 1
    rec = json.loads(files[0].read_text())
    assert rec["match_id"] == "NEAR" and rec["pin_status"] == "OK" \
        and rec["pm_status"] == "OK"
    assert rec["pin_close"] == {"HOME": 1.9, "AWAY": 2.0}
    # the call was METRICS, not incidents
    inc = tmp_path / "sandbox" / "ops" / "state" / "incidents.jsonl"
    assert not inc.exists() or "CLV_SAMPLE_ERROR" not in inc.read_text()


def test_clv_tick_never_blocks_on_error(tmp_path, monkeypatch):
    svc = make_svc(tmp_path)
    ko = (NOW + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [{"type": "FORECAST", "league": "NBA", "match_id": "M",
             "home": "A", "away": "B", "kickoff_utc": ko,
             "p": {"HOME": 0.6, "AWAY": 0.4}}]
    monkeypatch.setattr(svc, "_ledger_state",
                        lambda: (None, _FakeLed(rows), None))

    def boom(*a, **kw):
        raise RuntimeError("odds api down")

    monkeypatch.setattr(svc, "_clv_odds_fetch", boom)
    svc._clv_closing_quotes()
    # the odds failure is fail-safe INSIDE the plane: honest NO_RUN record,
    # the tick continues, NO incident (the plane owns that failure mode)
    side = tmp_path / "sandbox" / "ops" / "clv"
    recs = list(side.glob("clv_*.json"))
    assert recs and \
        json.loads(recs[0].read_text())["pin_status"] == "NO_RUN_PINNACLE"
    inc = (tmp_path / "sandbox" / "ops" / "state" / "incidents.jsonl")
    assert not inc.exists() or "CLV_SAMPLE_ERROR" not in inc.read_text()
    # a failure OUTSIDE the plane's own fail-safe (e.g. the plane itself)
    # is ONE CLV_SAMPLE_ERROR incident and still never blocks the tick
    from research.papertrade_exec import clv_plane as CP

    def kaboom(**kw):
        raise RuntimeError("disk on fire")
    monkeypatch.setattr(CP, "record_closing_quotes", kaboom)
    monkeypatch.setattr(svc, "_clv_odds_fetch",
                        lambda sk, mids: [{"id": "M"}])
    monkeypatch.setattr(svc, "_throttle_ok", lambda k, i: True)  # 2nd hour
    svc._clv_closing_quotes()
    assert inc.exists() and "CLV_SAMPLE_ERROR" in inc.read_text()


def test_shadow_tick_journals_and_incidents(tmp_path, monkeypatch):
    svc = make_svc(tmp_path)
    monkeypatch.setattr(svc, "_ledger_state",
                        lambda: (None, _FakeLed(_ledger_rows()), None))
    svc._shadow_new_law()
    jp = tmp_path / "sandbox" / "ops" / "shadow_new_law.jsonl"
    assert jp.exists() and len(jp.read_text().splitlines()) == 1
    # module failure -> ONE incident, tick survives
    def boom(**kw):
        raise ValueError("journal disk full")
    monkeypatch.setattr(S, "shadow_recent_decisions", boom)
    monkeypatch.setattr(svc, "_throttle_ok", lambda k, i: True)  # next hour
    svc._shadow_new_law()
    inc = (tmp_path / "sandbox" / "ops" / "state" / "incidents.jsonl")
    assert inc.exists() and "SHADOW_NEW_LAW_ERROR" in inc.read_text()


def test_clv_sport_keys_mapping_law(tmp_path, monkeypatch):
    keys = OpsService._clv_sport_keys()
    # config-registered real keys ride through; the WSL pseudo-key never does
    assert keys.get("NBA") == "basketball_nba"
    assert keys.get("WNBA") == "basketball_wnba"
    assert keys.get("NCAA-M") == "mens-college-basketball"
    assert keys.get("SOCCER") == "soccer_uefa_nations_league"   # first of list
    assert "WSL" not in keys


# ------------------------------- 4) frozen spec integrity --------------------

def test_spec_sha_registration_remeasures():
    text = SPEC.read_text()
    m = re.search(r"replaced by empty\):\s*`?([0-9a-f]{64})", text)
    assert m, "spec carries no registered digest"
    registered = m.group(1)
    blanked = text.replace(registered, "", 1)
    assert hashlib.sha256(blanked.encode()).hexdigest() == registered
    # the frozen constants really are in the frozen document
    assert "SHARP_PRICE_MARGIN = 3%" in text or "0.03" in text
    assert "n ≥ 200" in text and "−5%" in text
