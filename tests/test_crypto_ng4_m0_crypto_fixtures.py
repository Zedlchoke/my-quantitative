"""CRYPTO-NG4 M0 crypto-specific golden fixtures (plan plans/PLAN_crypto_ng4.md §3).

Three fixtures, all hand-computed, synthetic timestamps only — no market
data, no network, no PnL:

(a) TIME-BASED FOLD ASSIGNMENT against the fold boundaries FROZEN in plan
    §4 F4 BEFORE D1.  Event-triggered decisions at arbitrary UTC hours must
    land in their wall-clock fold; a fold with < 4 decisions triggers the
    population kill (the NG3-A5 2<4 precedent, plan §3(a)); an entry dated
    2026-08-22 is a PHANTOM (A4: outside the panel window) and is REFUSED.

(b) TWO-LEG FUNDING accounting (plan §4 F2): per-leg sign conventions,
    1:(-beta) notional weighting, 8h nominal cadence plus a 4h-stress case
    (cadence is DATA read from the re-proved settlement series, never a
    parameter), the INCLUSIVE settlement-boundary rule (a settlement
    timestamped exactly at entry or exit IS charged) and the
    charged-exactly-once-per-settlement rule.  Expected costs hand-computed.

(c) PROSPECTIVE CONTRACT FLOOR VERIFIER (plan §3(c)/§7): recomputes the
    frozen floor arithmetic from the committed contract dossier
    research/control/ng6_ng7_ng4_dossiers_2026-09/cng4-a3-prospective-
    contract-dossier.json — 60d -> 1440 H1 bars; 90% -> 1296 triads;
    4 x 15-day folds -> 324 valid triads/fold; population share
    4/324 = 1.2346%; weekend CALENDAR guarantees (96 raw weekend H1 bars
    per 15-day fold; >= 16 weekend days per 60-day window).  ANY mismatch
    FAILS (and a tamper probe proves the verifier fails a wrong contract).

Run:  .venv/bin/python -m pytest tests/test_crypto_ng4_m0_crypto_fixtures.py -q
"""

from __future__ import annotations

import copy
import importlib.util
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parent
M0_DIR = WORKTREE / "research" / "control" / "crypto_ng4_run" / "m0"
DOSSIER_PATH = (
    WORKTREE
    / "research"
    / "control"
    / "ng6_ng7_ng4_dossiers_2026-09"
    / "cng4-a3-prospective-contract-dossier.json"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _load("cng4_m0_golden_fixtures", M0_DIR / "test_m0_golden.py")  # gates stay green alongside


# ===================================================================
# (a) TIME-BASED FOLD ASSIGNMENT — plan §4 F4, boundaries frozen in §3
# ===================================================================

def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


# The four folds are contiguous and equal — frozen verbatim from plan §4 F4.
FROZEN_FOLDS = [
    ("FOLD-1", _utc(2025, 10, 22, 0, 0), _utc(2026, 1, 5, 23, 0)),
    ("FOLD-2", _utc(2026, 1, 6, 0, 0), _utc(2026, 3, 22, 23, 0)),
    ("FOLD-3", _utc(2026, 3, 23, 0, 0), _utc(2026, 6, 6, 23, 0)),
    ("FOLD-4", _utc(2026, 6, 7, 0, 0), _utc(2026, 8, 21, 23, 0)),
]
PANEL_FIRST_BAR = _utc(2025, 8, 22, 0, 0)  # panel window 2025-08-22T00:00Z ..
PANEL_LAST_BAR = _utc(2026, 8, 21, 23, 0)  # .. 2026-08-21T23:00Z (365x24 H1)
POPULATION_FLOOR = 4  # plan §3(a): a fold with < 4 decisions is a KILL


class PhantomEntryRefused(Exception):
    """An entry outside the four frozen fold windows (phantom margin day
    2026-08-22, warmup bars, pre-panel time) is refused, never assigned."""


def assign_fold(ts: datetime) -> str:
    """Wall-clock fold of a decision.  Decisions are evaluated at H1 bar
    close at ARBITRARY hours (F4: no calendar/session conditioning), so the
    stamp is floored to its bar-open hour and contained against the frozen
    [start, end] windows, both ends inclusive."""
    ts = ts.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for fold_id, start, end in FROZEN_FOLDS:
        if start <= ts <= end:
            return fold_id
    raise PhantomEntryRefused(f"decision stamp {ts.isoformat()} is outside every frozen fold")


def fold_population(decision_stamps) -> dict:
    counts = {fold_id: 0 for fold_id, _, _ in FROZEN_FOLDS}
    for ts in decision_stamps:
        counts[assign_fold(ts)] += 1
    return counts


def population_kill(decision_stamps):
    """MANDATORY KILL (NG3-A5 precedent): any fold with < 4 decisions."""
    counts = fold_population(decision_stamps)
    killed = sorted(f for f, n in counts.items() if n < POPULATION_FLOOR)
    return counts, killed


def test_fold_fixture_frozen_boundary_geometry():
    """Hand-computed geometry: 4 contiguous equal folds of 76 days = 1824
    H1 bars each; the union starts at the first decidable panel day
    (index 61, 2025-10-22T00:00Z) and ends at the last panel bar."""
    spans = []
    for i, (fold_id, start, end) in enumerate(FROZEN_FOLDS):
        bars = int((end - start).total_seconds() // 3600) + 1  # inclusive both ends
        assert bars == 76 * 24 == 1824, (fold_id, bars)  # hand-computed
        spans.append((start, end))
        if i:  # contiguity: next fold starts exactly one hour after the previous ends
            assert start == spans[i - 1][1] + timedelta(hours=1)
    assert spans[0][0] == _utc(2025, 10, 22, 0, 0)  # first decidable bar
    assert spans[-1][1] == PANEL_LAST_BAR
    assert (spans[0][0] - PANEL_FIRST_BAR).days == 61  # day index 61
    total = sum(int((e - s).total_seconds() // 3600) + 1 for s, e in spans)
    assert total == 4 * 1824 == 7296


def test_fold_assignment_wall_clock_arbitrary_hours():
    """A synthetic arbitrary-hour event stream assigns every decision to
    its wall-clock fold — even shuffled, even at 00:00/23:00 boundaries."""
    events = {
        # FOLD-1: 5 decisions, hours 03/17/23/07 and the fold's last bar
        _utc(2025, 10, 22, 3, 0): "FOLD-1",
        _utc(2025, 11, 1, 17, 0): "FOLD-1",
        _utc(2025, 12, 15, 23, 0): "FOLD-1",
        _utc(2026, 1, 1, 7, 0): "FOLD-1",
        _utc(2026, 1, 5, 23, 0): "FOLD-1",  # inclusive upper boundary
        # FOLD-2: 3 decisions
        _utc(2026, 1, 6, 0, 0): "FOLD-2",  # inclusive lower boundary
        _utc(2026, 2, 14, 11, 0): "FOLD-2",
        _utc(2026, 3, 22, 19, 0): "FOLD-2",
        # FOLD-3: 4 decisions
        _utc(2026, 3, 23, 1, 0): "FOLD-3",
        _utc(2026, 4, 20, 9, 0): "FOLD-3",
        _utc(2026, 5, 9, 13, 0): "FOLD-3",
        _utc(2026, 6, 6, 23, 0): "FOLD-3",
        # FOLD-4: 7 decisions
        _utc(2026, 6, 7, 5, 0): "FOLD-4",
        _utc(2026, 7, 4, 21, 0): "FOLD-4",
        _utc(2026, 7, 19, 2, 0): "FOLD-4",
        _utc(2026, 8, 1, 14, 0): "FOLD-4",
        _utc(2026, 8, 10, 8, 0): "FOLD-4",
        _utc(2026, 8, 15, 16, 0): "FOLD-4",
        _utc(2026, 8, 21, 23, 0): "FOLD-4",
    }
    shuffled = list(events)
    random.Random(20260916).shuffle(shuffled)  # arrival order is irrelevant
    assert {ts: assign_fold(ts) for ts in shuffled} == events
    assert fold_population(shuffled) == {
        "FOLD-1": 5, "FOLD-2": 3, "FOLD-3": 4, "FOLD-4": 7,
    }


def test_fold_population_kill_fires_under_four():
    """FOLD-2 has 3 < 4 decisions -> the population kill fires (FAIL state)."""
    counts, killed = population_kill(list(_fold_stream()))
    assert counts == {"FOLD-1": 5, "FOLD-2": 3, "FOLD-3": 4, "FOLD-4": 7}
    assert killed == ["FOLD-2"]


def test_fold_population_kill_reproduces_ng3_two_less_than_four():
    """The NG3-A5 precedent reproduced in-test: a fold with exactly 2
    anchor decisions (2 < 4) kills that fold."""
    two_in_fold1 = [
        _utc(2025, 10, 23, 6, 0),
        _utc(2025, 12, 1, 18, 0),
    ] + [t for t, f in _fold_stream().items() if f != "FOLD-1"]
    counts, killed = population_kill(two_in_fold1)
    assert counts["FOLD-1"] == 2
    assert "FOLD-1" in killed
    # 4/5/6/4 everywhere -> no kill
    healthy = [
        _utc(2025, 10, 22, 1, 0), _utc(2025, 11, 11, 2, 0),
        _utc(2025, 12, 12, 3, 0), _utc(2026, 1, 4, 4, 0),          # FOLD-1: 4
        _utc(2026, 1, 7, 5, 0), _utc(2026, 2, 2, 6, 0), _utc(2026, 2, 22, 7, 0),
        _utc(2026, 3, 10, 8, 0), _utc(2026, 3, 21, 9, 0),          # FOLD-2: 5
        _utc(2026, 3, 24, 10, 0), _utc(2026, 4, 4, 11, 0), _utc(2026, 4, 24, 12, 0),
        _utc(2026, 5, 5, 13, 0), _utc(2026, 5, 25, 14, 0), _utc(2026, 6, 5, 15, 0),  # 6
        _utc(2026, 6, 8, 16, 0), _utc(2026, 6, 28, 17, 0), _utc(2026, 7, 18, 18, 0),
        _utc(2026, 8, 7, 19, 0),                                    # FOLD-4: 4
    ]
    counts, killed = population_kill(healthy)
    assert counts == {"FOLD-1": 4, "FOLD-2": 5, "FOLD-3": 6, "FOLD-4": 4}
    assert killed == []


def _fold_stream():
    return {
        _utc(2025, 10, 22, 3, 0): "FOLD-1",
        _utc(2025, 11, 1, 17, 0): "FOLD-1",
        _utc(2025, 12, 15, 23, 0): "FOLD-1",
        _utc(2026, 1, 1, 7, 0): "FOLD-1",
        _utc(2026, 1, 5, 23, 0): "FOLD-1",
        _utc(2026, 1, 6, 0, 0): "FOLD-2",
        _utc(2026, 2, 14, 11, 0): "FOLD-2",
        _utc(2026, 3, 22, 19, 0): "FOLD-2",
        _utc(2026, 3, 23, 1, 0): "FOLD-3",
        _utc(2026, 4, 20, 9, 0): "FOLD-3",
        _utc(2026, 5, 9, 13, 0): "FOLD-3",
        _utc(2026, 6, 6, 23, 0): "FOLD-3",
        _utc(2026, 6, 7, 5, 0): "FOLD-4",
        _utc(2026, 7, 4, 21, 0): "FOLD-4",
        _utc(2026, 7, 19, 2, 0): "FOLD-4",
        _utc(2026, 8, 1, 14, 0): "FOLD-4",
        _utc(2026, 8, 10, 8, 0): "FOLD-4",
        _utc(2026, 8, 15, 16, 0): "FOLD-4",
        _utc(2026, 8, 21, 23, 0): "FOLD-4",
    }


def test_phantom_entry_2026_08_22_refused():
    """The A2 'margin day 2026-08-22' is a PHANTOM (A4: outside the panel
    window) — an entry dated 2026-08-22 is REFUSED, never assigned, never
    silently dropped into FOLD-4."""
    with pytest.raises(PhantomEntryRefused):
        assign_fold(_utc(2026, 8, 22, 0, 0))
    with pytest.raises(PhantomEntryRefused):
        assign_fold(_utc(2026, 8, 22, 13, 0))  # arbitrary hour, still phantom
    # warmup bars (before the first decidable day) are equally refused
    with pytest.raises(PhantomEntryRefused):
        assign_fold(_utc(2025, 10, 21, 23, 0))
    with pytest.raises(PhantomEntryRefused):
        assign_fold(_utc(2025, 8, 21, 23, 0))  # pre-panel
    # and the kill machinery refuses phantoms too instead of miscounting
    with pytest.raises(PhantomEntryRefused):
        population_kill([_utc(2026, 8, 22, 0, 0)] + list(_fold_stream()))


# ===================================================================
# (b) TWO-LEG FUNDING ACCOUNTING — plan §4 F2, hand-computed goldens
# ===================================================================

def two_leg_funding(entry_ts, exit_ts, settlements, beta, notional=1.0):
    """Complete two-leg funding cost over the holding window
    [entry_ts, exit_ts], INCLUSIVE at both ends (plan F2: a settlement
    timestamped exactly at entry or exit IS charged).

    settlements is the MEASURED re-proved funding series — a list of
    (timestamp, funding_rate) pairs; the cadence (8h nominal, 4h stress)
    is DATA here, never a parameter.  Each settlement is charged EXACTLY
    ONCE: a repeated settlement timestamp in the series is a data fault
    and is refused (double-charging is an accounting violation).

    Sign convention per leg: leg cost = rate * signed_weight * notional,
    signed_weight = +1 for the long leg and -beta for the short leg — a
    long PAYS when the funding rate is positive, a short RECEIVES; with
    the 1:(-beta) notional weighting the pair cost per settlement is
    rate * (1 - beta) * notional.
    """
    entry_ts = entry_ts.astimezone(timezone.utc)
    exit_ts = exit_ts.astimezone(timezone.utc)
    seen = set()
    charged = []
    long_leg = 0.0
    short_leg = 0.0
    for ts, rate in settlements:
        ts = ts.astimezone(timezone.utc)
        if ts in seen:
            raise ValueError(f"duplicate funding settlement {ts.isoformat()}")
        seen.add(ts)
        if entry_ts <= ts <= exit_ts:
            charged.append(ts)
            long_leg += rate * (+1.0) * notional
            short_leg += rate * (-beta) * notional
    pair_cost = long_leg + short_leg
    return {"pair_cost": pair_cost, "long_leg": long_leg, "short_leg": short_leg,
            "charged": charged}


def _h8_settlements():
    """8h nominal cadence (00:00/08:00/16:00 UTC), FOLD-4 window."""
    r = {}
    r[_utc(2026, 6, 10, 0, 0)] = 0.00010   # before entry -> NOT charged
    r[_utc(2026, 6, 10, 8, 0)] = 0.00010   # charged
    r[_utc(2026, 6, 10, 16, 0)] = -0.00020  # charged
    r[_utc(2026, 6, 11, 0, 0)] = 0.00005   # charged
    r[_utc(2026, 6, 11, 8, 0)] = 0.00010   # charged — INCLUSIVE: == exit
    r[_utc(2026, 6, 11, 16, 0)] = 0.00010  # after exit -> NOT charged
    return sorted(r.items())


ENTRY = _utc(2026, 6, 10, 5, 0)
EXIT = _utc(2026, 6, 11, 8, 0)  # exactly a settlement stamp
BETA = 1.25  # 1 : -1.25 notional weighting


def test_funding_8h_hand_computed():
    """Hand-computed 8h golden:
    charged rates = 0.0001 - 0.0002 + 0.00005 + 0.0001 = +0.00005
    long leg      = +0.00005 (net payer)
    short leg     = -1.25 * 0.00005 = -0.0000625 (net receiver)
    pair cost     = (1 - 1.25) * 0.00005 = -0.0000125
    4 settlements charged, before-entry and after-exit stamps excluded."""
    res = two_leg_funding(ENTRY, EXIT, _h8_settlements(), BETA)
    assert len(res["charged"]) == 4
    assert res["charged"] == [
        _utc(2026, 6, 10, 8, 0), _utc(2026, 6, 10, 16, 0),
        _utc(2026, 6, 11, 0, 0), _utc(2026, 6, 11, 8, 0),
    ]
    assert res["long_leg"] == pytest.approx(0.00005, abs=1e-15)
    assert res["short_leg"] == pytest.approx(-0.0000625, abs=1e-15)
    assert res["pair_cost"] == pytest.approx(-0.0000125, abs=1e-15)


def test_funding_boundary_is_inclusive_at_both_ends():
    """A settlement timestamped EXACTLY at exit is charged (the 06-11T08:00
    stamp above); one exactly at entry is charged too.  An exclusive
    implementation produces +0.00000125 on the same data and fails."""
    res = two_leg_funding(ENTRY, EXIT, _h8_settlements(), BETA)
    assert _utc(2026, 6, 11, 8, 0) in res["charged"]  # exit-inclusive
    entry_at_settlement = two_leg_funding(
        _utc(2026, 6, 10, 8, 0), EXIT, _h8_settlements(), BETA
    )
    assert _utc(2026, 6, 10, 8, 0) in entry_at_settlement["charged"]  # entry-inclusive
    assert entry_at_settlement["pair_cost"] == pytest.approx(-0.0000125, abs=1e-15)
    # sensitivity: an EXIT-EXCLUSIVE kernel would drop the last stamp:
    # charged rates become 0.00005 - 0.0001 = -0.00005, pair cost
    # (-0.25)*(-0.00005) = +0.0000125 — sign-flipped vs the inclusive
    # golden -0.0000125, so the inclusive rule is what the fixture pins.
    exclusive_wrong = sum(r for t, r in _h8_settlements()
                          if ENTRY <= t < EXIT) * (1 - BETA)
    assert exclusive_wrong == pytest.approx(0.0000125, abs=1e-15)
    assert exclusive_wrong != pytest.approx(-0.0000125, abs=1e-12)


def test_funding_charged_exactly_once_per_settlement():
    """Every charged settlement appears exactly once; a duplicated
    settlement timestamp in the measured series is refused outright."""
    res = two_leg_funding(ENTRY, EXIT, _h8_settlements(), BETA)
    assert len(res["charged"]) == len(set(res["charged"])) == 4
    doubled = _h8_settlements() + [(_utc(2026, 6, 10, 8, 0), 0.00010)]
    with pytest.raises(ValueError, match="duplicate"):
        two_leg_funding(ENTRY, EXIT, doubled, BETA)


def test_funding_per_leg_sign_conventions():
    """Hand-computed single-settlement signs: a LONG pays a positive rate
    (+1e-4), the SHORT leg receives -1.25e-4 under 1:(-1.25) weighting;
    a negative rate reverses both."""
    s = [(_utc(2026, 6, 10, 8, 0), 0.0001)]
    pos = two_leg_funding(ENTRY, EXIT, s, BETA)
    assert pos["long_leg"] == pytest.approx(+0.0001, abs=1e-15)   # long pays
    assert pos["short_leg"] == pytest.approx(-0.000125, abs=1e-15)  # short receives
    assert pos["pair_cost"] == pytest.approx(-0.000025, abs=1e-15)
    neg = two_leg_funding(ENTRY, EXIT, [(_utc(2026, 6, 10, 8, 0), -0.0001)], BETA)
    assert neg["long_leg"] == pytest.approx(-0.0001, abs=1e-15)    # long receives
    assert neg["short_leg"] == pytest.approx(+0.000125, abs=1e-15)  # short pays
    assert neg["pair_cost"] == pytest.approx(+0.000025, abs=1e-15)
    # 1:(-beta) weighting identity: pair = (1 - beta) * long-leg-per-unit
    assert pos["pair_cost"] == pytest.approx((1 - BETA) * pos["long_leg"], abs=1e-15)


def test_funding_4h_stress_cadence_hand_computed():
    """4h-stress case: the SAME function over a denser MEASURED series —
    cadence is data, never hardcoded.  Hand-computed:
    charged rates = 1e-4 + 1.5e-4 - 2e-4 + 2.5e-5 + 5e-5 - 7.5e-5 + 1e-4
                  = +1.5e-4  (7 settlements inside the window)
    long leg      = +1.5e-4
    short leg     = -1.25 * 1.5e-4 = -1.875e-4
    pair cost     = (1 - 1.25) * 1.5e-4 = -3.75e-5."""
    r = {}
    r[_utc(2026, 6, 10, 0, 0)] = 0.000100    # before entry
    r[_utc(2026, 6, 10, 4, 0)] = 0.000020    # before entry
    r[_utc(2026, 6, 10, 8, 0)] = 0.000100    # charged
    r[_utc(2026, 6, 10, 12, 0)] = 0.000150   # charged
    r[_utc(2026, 6, 10, 16, 0)] = -0.000200  # charged
    r[_utc(2026, 6, 10, 20, 0)] = 0.000025   # charged
    r[_utc(2026, 6, 11, 0, 0)] = 0.000050    # charged
    r[_utc(2026, 6, 11, 4, 0)] = -0.000075   # charged
    r[_utc(2026, 6, 11, 8, 0)] = 0.000100    # charged — == exit, inclusive
    r[_utc(2026, 6, 11, 12, 0)] = 0.000030   # after exit
    res = two_leg_funding(ENTRY, EXIT, sorted(r.items()), BETA)
    assert len(res["charged"]) == 7
    assert res["long_leg"] == pytest.approx(0.00015, abs=1e-15)
    assert res["short_leg"] == pytest.approx(-0.0001875, abs=1e-15)
    assert res["pair_cost"] == pytest.approx(-0.0000375, abs=1e-15)
    # the stress window is one full holding window inside a single fold (F4)
    assert assign_fold(ENTRY) == assign_fold(EXIT) == "FOLD-4"


# ===================================================================
# (c) PROSPECTIVE CONTRACT FLOOR VERIFIER — plan §3(c)/§7
# ===================================================================

def verify_floors(d: dict) -> None:
    """Recompute every frozen floor of the committed A3 prospective
    contract from first principles and MATCH it against the contract's own
    frozen numbers.  ANY mismatch raises AssertionError — the test FAILS.
    (Raised on the live dossier in test_floor_verifier; a tamper probe
    below proves a wrong contract fails here.)"""
    assert d["schema"] == "cng4_a3_prospective_contract@1"
    assert d["cycle_id"] == "CRYPTO-NG4"

    fa = d["d2_control_cell_definitions_and_floor_arithmetic"][
        "decision_frequency_arithmetic_H1"
    ]
    # 60 consecutive UTC days x 24 H1 bars/day = 1440 decision bars.
    assert fa["window_days"] == 60 and fa["bars_per_day"] == 24
    assert fa["total_H1_bars"] == 60 * 24 == 1440
    # 4 x 15-day folds (fold COUNT aligned to the A2 family structure).
    assert "4 chronological folds" in fa["folds"] and "15 days" in fa["folds"]
    assert 15 * 24 == 360 and "360 H1 bars/fold" in fa["folds"]
    # 90% validity -> >= 1296 of 1440 total; >= 324 of 360 per fold.
    # Integer arithmetic: 1440*90/100 and 360*90/100 are exact.
    assert (1440 * 90) % 100 == 0 and 1440 * 90 // 100 == 1296
    assert (360 * 90) % 100 == 0 and 360 * 90 // 100 == 324
    assert "90%" in fa["validity_floor"]
    assert ">= 324 valid triads/fold" in fa["validity_floor"]
    assert ">= 1296 total" in fa["validity_floor"]
    # Population floor: >= 4 valid bars per control cell per fold.
    assert ">= 4 valid bars per control cell per fold" in fa["population_requirement"]
    # Minimum population share: 4/324 = 1.2346% (hand-computed golden).
    assert round(4 / 324 * 100, 4) == 1.2346
    cells = d["d2_control_cell_definitions_and_floor_arithmetic"]["per_control_cells"]
    div = next(c for c in cells if c["control"] == "venue_divergence")
    assert "s >= 1.235%" in div["fold_cells_at_share"]  # contract's own rounding
    assert abs(1.235 - 100 * 4 / 324) < 5e-4  # consistent at 3 decimal places

    # Weekend CALENDAR guarantee (plan §7: the BINDING guarantee is the
    # calendar guarantee, NOT the '86 valid bars' figure): any 15-day
    # window contains >= 4 weekend days = 96 raw weekend H1 bars, and any
    # 60-day window >= 16 weekend days.  Proven by brute force over all
    # seven weekday starts, then matched to the contract text.
    def weekend_days(start: date, n: int) -> int:
        return sum(1 for i in range(n) if (start + timedelta(days=i)).weekday() >= 5)

    base = date(2026, 1, 1)
    min_15d = min(weekend_days(base + timedelta(days=o), 15) for o in range(7))
    min_60d = min(weekend_days(base + timedelta(days=o), 60) for o in range(7))
    assert min_15d == 4 and min_15d * 24 == 96   # 96 raw weekend H1 bars / fold
    assert min_60d == 16 and min_60d * 24 == 384
    wl = next(c for c in cells if c["control"] == "weekend_liquidity")
    cg = wl["calendar_guarantee"]
    assert ">= 4 weekend days = 96 weekend H1 bars" in cg
    assert "60 days guarantee >= 16 weekend days" in cg
    ff9 = d["freeze_fields"]["9_minimum_coverage_duration"]
    assert "1440 H1 decision bars (24/day)" in ff9["calendar_arithmetic"]
    assert "floor(60/7)*2 = 16 weekend days" in ff9["calendar_arithmetic"]
    assert "384 weekend H1 bars" in ff9["calendar_arithmetic"]
    assert floor607() == 16  # floor(60/7)*2 hand-check: 8 full weeks * 2

    # Coverage floors
    ff10 = d["freeze_fields"]["10_minimum_complete_observation_count"]
    assert ">= 1296 of 1440 (90%)" in ff10["frozen_floors"]["total_valid_triads"]
    assert ">= 324 of 360 (90%)" in ff10["frozen_floors"]["per_fold_valid_triads"]


def floor607() -> int:
    return (60 // 7) * 2  # 8 full weeks x 2 weekend days


def test_floor_verifier_recomputes_committed_contract():
    assert DOSSIER_PATH.is_file(), DOSSIER_PATH
    verify_floors(json.loads(DOSSIER_PATH.read_text()))  # any mismatch FAILS


def test_floor_verifier_fails_a_tampered_contract():
    """Sensitivity probe (G8 discipline): flipping ANY frozen floor number
    makes the verifier raise — the floor check cannot be silently passed by
    a wrong contract."""
    d = json.loads(DOSSIER_PATH.read_text())
    bad = copy.deepcopy(d)
    fa = bad["d2_control_cell_definitions_and_floor_arithmetic"][
        "decision_frequency_arithmetic_H1"
    ]
    fa["total_H1_bars"] = 1441  # tampered arithmetic
    with pytest.raises(AssertionError):
        verify_floors(bad)
    bad2 = copy.deepcopy(d)
    wl = next(
        c
        for c in bad2["d2_control_cell_definitions_and_floor_arithmetic"]["per_control_cells"]
        if c["control"] == "weekend_liquidity"
    )
    wl["calendar_guarantee"] = wl["calendar_guarantee"].replace(
        "96 weekend H1 bars", "86 weekend H1 bars"  # the A3 '86' figure is NOT the guarantee
    )
    with pytest.raises(AssertionError):
        verify_floors(bad2)


def test_shared_golden_suite_still_green_alongside():
    """The three crypto fixtures never weaken the shared suite: the
    NG5-lineage law still self-reports 11/11 in this worktree."""
    assert G.main() == 0
