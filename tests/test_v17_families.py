"""CRYPTO-V17 A8 families lane tests (SILRES + ATTN-PHASE).

Synthetic only: every expected number below is computed BY HAND from the
frozen proposal formulas (research/control/v17_run/d1/a4/proposal_P2.json
and research/control/v17_run/d1/a5/proposal_P1.json, blob SHAs pinned in
selection_freeze_v17.json).  No real data file is read, nothing is scored
outside ``tmp_path``, and no frozen module byte beyond the A8 lane's own
additive driver extensions is exercised differently from the D2 freeze.

Fixture map (task items a-d):

* (a) hand-computed formula values
      - test_silres_anchor_hand_computed        (rolling Q90/median, >=
      boundaries, AND mask, direction sign, warmup None)
      - test_attn_q_hand_computed               (composition double
      difference on a crafted 6-day panel, day t-1 law)
      - test_attn_state_path_hand_computed      (median crossing, strict >,
      warmup None, hold-through carry)
      - test_attn_neighbour_min_hold_hand_computed (2-day min hold)
* (b) availability law
      - test_silres_availability_no_forward_lookup
      - test_attn_availability_no_forward_lookup
* (c) controls structurally differ, mask duty preserved
      - test_silres_control_reshuffles_with_frozen_seed (event count per
      block preserved, positions move, deterministic, direction recomputed)
      - test_attn_control_rotation (frozen k_t = day_index mod 24 actually
      rotates; k=0 decision days coincide with the anchor window)
* (d) frozen spec JSONs + concretized diag contracts load and execute
      - test_family_specs_load_through_driver_schema
      - test_silres_spec_end_to_end_scored_and_sanitized
      - test_attn_phase_spec_end_to_end_scored_and_sanitized
      - test_diag_contracts_pass_persistability_gate
      - test_lag_zero_still_refused_without_declared_fill_price
"""

from __future__ import annotations

import copy
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.control.v17_run.driver import family_registry_v17 as reg
from research.control.v17_run.driver import run_v17_cell as d
from research.governance.diagnostic_persistability import (
    CONDITIONAL_REQUIRED_FIELDS,
    expected_artifacts_from_contract,
    validate_contract,
)

REPO = Path(__file__).resolve().parents[1]
FAMILIES_DIR = REPO / "research/control/v17_run/driver/families"
S0 = date(2025, 8, 22)


@reg.register("FAMTEST.h1_zero", example_only=False)
def _zero(panels, params):
    return {sym: [0.0] * len(rows) for sym, rows in panels.items()}


def _day(i: int) -> str:
    return (S0 + timedelta(days=i)).isoformat()


# ------------------------------------------------------------------------- #
# SILRES fixtures (H1 rows; only the columns the formulas read are varied)
# ------------------------------------------------------------------------- #
def _silres_row(idx: int, symbol: str, gap: float, n: int, dir_sign: int = 1) -> dict:
    day = idx // 24
    hour = idx % 24
    base = 100.0 + 0.01 * idx
    first = base
    last = base * (1.0 + 0.001 * dir_sign)
    return {
        "symbol": symbol,
        "hour_utc": f"{_day(day)}T{hour:02d}",
        "day_utc": _day(day),
        "n_trades": n,
        "vwap": base,
        "first_price": first,
        "last_price": last,
        "entry_gap_s": gap,
    }


def _silres_panels(specs_by_idx: dict, n_buckets: int, symbols=("BTCUSDT", "ETHUSDT")) -> dict:
    """specs_by_idx: idx -> (gap, n, dir_sign); defaults (1.0, 100, 1)."""
    return {
        sym: [
            _silres_row(i, sym, *specs_by_idx.get(i, (1.0, 100, 1)))
            for i in range(n_buckets)
        ]
        for sym in symbols
    }


# ------------------------------------------------------------------------- #
# (a) SILRES anchor: hand-computed trigger mask
# ------------------------------------------------------------------------- #
HAND_SPECS = {
    # idx: (entry_gap_s, n_trades, direction sign of last-first)
    9: (11.0, 200, 1),
    10: (9.0, 100, 1),
    11: (11.0, 200, -1),
    12: (11.0, 149, 1),
    13: (11.0, 200, 0),
}
ANCHOR_PARAMS = {"gap_percentile": 90.0, "resumption_multiple": 1.5, "warmup_buckets": 8}


def test_silres_anchor_hand_computed():
    panels = _silres_panels(HAND_SPECS, 16)
    series = reg.resolve("SILRES.anchor")(panels, ANCHOR_PARAMS)
    assert set(series) == {"BTCUSDT", "ETHUSDT"}
    for sym in panels:
        s = series[sym]
        assert len(s) == 16
        # warmup: no decision before the 8-bucket trailing window exists
        assert s[:8] == [None] * 8
        # b8: gap 10 >= Q90(10.0) boundary holds, but n=100 < 1.5x100=150 -> 0
        # b9: gap 11 >= 10.0, n 200 >= 150, up bucket -> +1
        # b10: gap 9 < Q90 of {10x7,11} = 10+0.3*(11-10) = 10.3 -> 0
        # b11: gap 11 >= 10.3, median{100x7,200}=100 -> 150<=200, down -> -1
        # b12: gap 11 >= Q90{9,10x5,11,11}=11.0 but n 149 < 1.5x100=150 -> 0
        # b13: gap 11 >= 11.0, n 200 >= 1.5x124.5=186.75, last==first -> 0.0
        # b14: gap 10 < Q90{9,10x2,11x5}=11.0 -> 0
        # b15: gap 10 < Q90{9,10x4,11x3}=11.0 -> 0
        assert s[8:] == [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0]


def test_silres_neighbour_thresholds_differ_frozen():
    """Neighbour freezes P75 / 1.2x: the same fixture must fire MORE often
    than the P90 / 1.5x anchor (75th pct of ~constant windows is lower and
    1.2x100=120 <= 149)."""
    panels = _silres_panels(HAND_SPECS, 16)
    anchor = reg.resolve("SILRES.anchor")(panels, ANCHOR_PARAMS)["BTCUSDT"]
    neighbour = reg.resolve("SILRES.neighbour")(
        panels,
        {"gap_percentile": 75.0, "resumption_multiple": 1.2, "warmup_buckets": 8},
    )["BTCUSDT"]
    # b12 (n=149, up bucket): the window median (strictly-prior buckets
    # b4..b11) is 100, so the anchor refuses (1.5x100 = 150 > 149) while
    # the neighbour's frozen 1.2x100 = 120 <= 149 fires -> the neighbour is
    # NOT a re-label of the anchor thresholds
    assert neighbour[12] == 1.0 and anchor[12] == 0.0
    # b8 (n=100): both refuse (100 < 1.2x100=120 < 150)
    assert neighbour[8] == 0.0 and anchor[8] == 0.0
    # every neighbour decision value is in {-1, 0, +1} x float
    assert all(v in (None, 0.0, 1.0, -1.0) for v in neighbour)


# ------------------------------------------------------------------------- #
# (b) SILRES availability law
# ------------------------------------------------------------------------- #
def test_silres_availability_no_forward_lookup():
    panels = _silres_panels(HAND_SPECS, 16)
    s1 = reg.resolve("SILRES.anchor")(panels, ANCHOR_PARAMS)["BTCUSDT"]
    tampered = copy.deepcopy(panels)
    tampered["BTCUSDT"][9] = _silres_row(9, "BTCUSDT", 0.0, 999, 1)
    s2 = reg.resolve("SILRES.anchor")(tampered, ANCHOR_PARAMS)["BTCUSDT"]
    # series[i] is computed from rows <= i only: row 9 must not move any
    # value at index <= 8 (the driver's one-bar lag then guarantees the
    # decision at bucket d consumes rows with close_ts <= d-1)
    assert s2[:9] == s1[:9]
    assert s2[9] == 0.0 != s1[9]  # its own closed row IS consumed


# ------------------------------------------------------------------------- #
# (c) SILRES control: reshuffle with the frozen seed
# ------------------------------------------------------------------------- #
CONTROL_SPECS = {
    14: (50.0, 500, 1),
    15: (50.0, 500, 1),
    27: (50.0, 500, 1),
    28: (50.0, 500, 1),
    29: (50.0, 500, 1),
    38: (50.0, 500, 1),
}
CONTROL_PARAMS = {
    "gap_percentile": 90.0,
    "resumption_multiple": 1.5,
    "warmup_buckets": 12,
    "block_buckets": 12,
    "seed": 17040002,
}


def _event_positions(series):
    return {i for i, v in enumerate(series) if v is not None and v != 0.0}


def test_silres_control_reshuffles_with_frozen_seed():
    panels = _silres_panels(CONTROL_SPECS, 40)
    anchor = reg.resolve("SILRES.anchor")(panels, {
        "gap_percentile": 90.0, "resumption_multiple": 1.5, "warmup_buckets": 12,
    })
    control = reg.resolve("SILRES.control")(panels, CONTROL_PARAMS)
    # determinism: the frozen seed reproduces the placebo byte-for-byte
    again = reg.resolve("SILRES.control")(panels, CONTROL_PARAMS)
    assert again == control
    for sym in panels:
        a_events = _event_positions(anchor[sym])
        c_events = _event_positions(control[sym])
        # the anchor hand-fires exactly where the spikes were planted
        assert a_events == {14, 15, 27, 28, 29, 38}
        # mask duty preserved PER 720-style BLOCK (bijection within block)
        for start in range(0, 40, 12):
            block = range(start, min(start + 12, 40))
            assert len(a_events & set(block)) == len(c_events & set(block))
        # the reshuffle actually reshuffles: the placebo set differs from
        # the anchor set (frozen seed 17040002 on this fixture)
        assert c_events != a_events
        # no warmup None: the placebo needs no rolling statistics
        assert all(v is not None for v in control[sym])
        # every placebo event's direction is the RESAMPLED bucket's own
        # sign(last_price - first_price) -- all rising here -> +1
        assert all(control[sym][i] == 1.0 for i in c_events)
        # non-event buckets are exactly zero
        assert all(
            (control[sym][i] == 0.0) == (i not in c_events) for i in range(40)
        )


def test_silres_control_event_count_preserved_per_block_edge_block():
    """The trailing partial block (40 = 3x12 + 4) preserves counts too, and
    a block with zero anchor events stays event-free."""
    panels = _silres_panels(CONTROL_SPECS, 40)
    control = reg.resolve("SILRES.control")(panels, CONTROL_PARAMS)["BTCUSDT"]
    assert len(_event_positions(control) & set(range(36, 40))) == 1
    assert not (_event_positions(control) & set(range(0, 12)))


# ------------------------------------------------------------------------- #
# ATTN-PHASE fixtures (H1 rows: SOL US-structured; majors uniform)
# ------------------------------------------------------------------------- #
def _attn_h1(n_days: int, *, sol_us_even=10.0, sol_us_odd=2.0, sol_off=1.0,
             sol_off_odd=4.0, btc=5, eth=3):
    def rows_for(sym: str) -> list:
        out = []
        for day in range(n_days):
            for hour in range(24):
                if sym == "SOLUSDT":
                    us = 14 <= hour <= 21
                    even = day % 2 == 0
                    if us:
                        n = int(sol_us_even if even else sol_us_odd)
                    else:
                        n = int(sol_off if even else sol_off_odd)
                elif sym == "BTCUSDT":
                    n = btc
                else:
                    n = eth
                base = 100.0 + 0.01 * (day * 24 + hour)
                out.append({
                    "symbol": sym,
                    "hour_utc": f"{_day(day)}T{hour:02d}",
                    "day_utc": _day(day),
                    "n_trades": n,
                    "vwap": base,
                    "first_price": base,
                    "last_price": base * 1.001,
                })
        return out
    return {
        "SOLUSDT": rows_for("SOLUSDT"),
        "BTCUSDT": rows_for("BTCUSDT"),
        "ETHUSDT": rows_for("ETHUSDT"),
    }


def _attn_frames(n_days: int) -> dict:
    """Minimal D1 frames (the formula reads only day_utc for the grid)."""
    return {
        sym: [{"symbol": sym, "day_utc": _day(i)} for i in range(n_days)]
        for sym in ("SOLUSDT", "BTCUSDT", "ETHUSDT")
    }


ANCHOR_WINDOW = {"window_start": 14, "window_end": 21}


def test_attn_q_hand_computed():
    """Hand world (6-day alternating panel, US window 14..21):

    even days: SOL US hours 10, others 1 -> total 8*10+16*1 = 96,
        s_h(US) = 10/96; majors n_BTC+n_ETH = 8 every hour, total 192,
        m_h = 8/192 = 1/24.
        q[even] = 8 x (10/96 - 1/24) = 8 x 0.0625 = 0.5
    odd days: SOL US hours 2, others 4 -> total 80, s_h(US) = 2/80 = 0.025
        q[odd]  = 8 x (0.025 - 1/24) = -0.133333...
    """
    h1 = _attn_h1(6)
    q = reg._attn_q_series(h1, [_day(i) for i in range(6)], 14, 21,
                           sham_rotation=False)
    assert q[0] == pytest.approx(0.5)
    assert q[1] == pytest.approx(-0.13333333333333333)
    assert q[4] == pytest.approx(0.5)
    # every q[x] is the composition of day x only (checked again in (b))


def test_attn_state_path_hand_computed():
    """md=2, mh=1 on q = [0.5, -0.1333, 0.5, -0.1333, 0.5, -0.1333]:

    t=1: warmup (t < md) -> None
    t=2: median{q0,q1} = 0.183333; fresh q1 = -0.1333 not > -> 0.0
    t=3: median{q1,q2} = 0.183333; fresh q2 = 0.5 > -> ON
    t=4: fresh q3 -> OFF ; t=5: fresh q4 -> ON
    """
    q = [0.5, -0.13333333333333333, 0.5, -0.13333333333333333, 0.5,
         -0.13333333333333333]
    path = reg._attn_state_path(q, 2, 1)
    assert path == [None, None, 0.0, 1.0, 0.0, 1.0]
    # strict crossing: fresh == median is OFF, never ON
    flat = reg._attn_state_path([0.2, 0.2, 0.2, 0.2], 2, 1)
    assert flat == [None, None, 0.0, 0.0]


def test_attn_neighbour_min_hold_hand_computed():
    """mh=2: once ON at t=2 the state survives the first OFF crossing
    (t=3) and may exit only at t=4 (2 complete held days)."""
    q = [0.10, 0.30, 0.05, 0.05, 0.05]
    with_hold = reg._attn_state_path(q, 2, 2)
    # t=2: med{0.10,0.30}=0.20 < 0.30 -> ON; t=3: raw OFF but 3-2=1 < 2 ->
    # held; t=4: med{0.05,0.05}=0.05, 0.05 not > 0.05 and 4-2=2 >= 2 -> OFF
    assert with_hold == [None, None, 1.0, 1.0, 0.0]
    without_hold = reg._attn_state_path(q, 2, 1)
    assert without_hold == [None, None, 1.0, 0.0, 0.0]


def test_attn_series_wrapper_alignment_and_universe_law():
    """series[i] = decision at day i+1 (driver one-bar lag); BTC/ETH pinned
    to zero; the formula refuses to run without the H1 rows."""
    panels = _attn_frames(6)
    h1 = _attn_h1(6)
    with pytest.raises(ValueError, match="h1"):
        reg.resolve("ATTN_PHASE.anchor")(panels, {**ANCHOR_WINDOW, "median_days": 60})
    out = reg.resolve("ATTN_PHASE.anchor")(
        panels, {**ANCHOR_WINDOW, "median_days": 2, "min_hold_days": 1}, h1=h1
    )
    assert set(out) == {"SOLUSDT", "BTCUSDT", "ETHUSDT"}
    assert out["SOLUSDT"] == [None, 0.0, 1.0, 0.0, 1.0, None]
    for ref in ("BTCUSDT", "ETHUSDT"):
        assert out[ref] == [0.0] * 6


# ------------------------------------------------------------------------- #
# (b) ATTN availability law
# ------------------------------------------------------------------------- #
def test_attn_availability_no_forward_lookup():
    panels = _attn_frames(8)
    h1 = _attn_h1(8)
    params = {**ANCHOR_WINDOW, "median_days": 2, "min_hold_days": 1}
    s1 = reg.resolve("ATTN_PHASE.anchor")(panels, params, h1=h1)["SOLUSDT"]
    tampered = copy.deepcopy(h1)
    for row in tampered["SOLUSDT"]:
        if row["day_utc"] == _day(6):
            row["n_trades"] += 50  # shifts the day-6 composition, not a rescale
    s2 = reg.resolve("ATTN_PHASE.anchor")(panels, params, h1=tampered)["SOLUSDT"]
    # decisions for days 1..5 (series 0..4) consume days <= 4 only: a day-6
    # change must not move them (the driver's lag makes the decision at day
    # d consume series[d-1], i.e. days <= d-1)
    assert s2[:5] == s1[:5]
    # q[6] itself moved, so the day-7 decision (series[6]) reflects it
    q1 = reg._attn_q_series(h1, [_day(i) for i in range(8)], 14, 21,
                            sham_rotation=False)
    q2 = reg._attn_q_series(tampered, [_day(i) for i in range(8)], 14, 21,
                            sham_rotation=False)
    assert q2[6] != q1[6]


# ------------------------------------------------------------------------- #
# (c) ATTN control: the frozen rotation actually rotates
# ------------------------------------------------------------------------- #
def test_attn_control_rotation():
    n_days = 26  # decision days 1..25 -> k_t = t mod 24 hits 0 at t=24
    days = [_day(i) for i in range(n_days)]
    h1 = _attn_h1(n_days)
    anchor_q = reg._attn_q_series(h1, days, 14, 21, sham_rotation=False)
    control_q = reg._attn_q_series(h1, days, 14, 21, sham_rotation=True)
    # the frozen offset: k_t = day_index(t from 2025-08-22) mod 24
    assert [reg.day_index_from_origin(days[t]) % 24 for t in range(n_days)] == [
        t % 24 for t in range(n_days)
    ]
    # q[x] is consumed by decision x+1, rotated by k_{x+1}: identical iff
    # k_{x+1} == 0 (x=23 -> decision day 24), different otherwise (the
    # crafted profile is US-structured, so a non-zero rotation moves mass)
    assert control_q[23] == pytest.approx(anchor_q[23])
    moved = 0
    for x in range(n_days - 1):
        if x == 23:
            continue  # k_{x+1} = 0: the sham window equals the anchor window
        if control_q[x] != pytest.approx(anchor_q[x], rel=1e-9):
            moved += 1
    assert moved == n_days - 2  # every non-zero-offset decision moved
    # the rotation preserves each day's cross-sectional structure: the
    # rotated window is a permutation of hour slots over the same profile
    total = sum(
        row["n_trades"] for row in h1["SOLUSDT"] if row["day_utc"] == _day(2)
    )
    assert total == 8 * 10 + 16 * 1  # even day: untouched by the rotation
    # state machinery byte-identical: same median/min-hold law on the
    # rotated series (params are the anchor's)
    panels = _attn_frames(n_days)
    params = {**ANCHOR_WINDOW, "median_days": 2, "min_hold_days": 1}
    anchor_s = reg.resolve("ATTN_PHASE.anchor")(panels, params, h1=h1)["SOLUSDT"]
    control_s = reg.resolve("ATTN_PHASE.control")(
        panels,
        {**params, "sham_rotation": "day_index_mod_24",
         "rotation_origin": "2025-08-22"},
        h1=h1,
    )["SOLUSDT"]
    assert control_s != anchor_s  # the sham book is NOT the anchor book


# ------------------------------------------------------------------------- #
# (d) frozen spec JSONs load through the driver schema; end-to-end runs
# ------------------------------------------------------------------------- #
SPEC_DOCS = {
    "V17-A4-P2-SILRES": json.loads(
        (FAMILIES_DIR / "V17-A4-P2-SILRES.spec.json").read_text()
    ),
    "V17-a5-P1-ATTN-PHASE": json.loads(
        (FAMILIES_DIR / "V17-a5-P1-ATTN-PHASE.spec.json").read_text()
    ),
}


def test_family_specs_load_through_driver_schema():
    silres = d.load_selection(FAMILIES_DIR / "V17-A4-P2-SILRES.spec.json")
    attn = d.load_selection(FAMILIES_DIR / "V17-a5-P1-ATTN-PHASE.spec.json")
    assert silres[0] == "CRYPTO-V17" and attn[0] == "CRYPTO-V17"
    (s_spec,) = silres[1]
    (a_spec,) = attn[1]
    # frozen selection-freeze bindings (arms, universe, clock)
    assert (s_spec.family_id, s_spec.clock, s_spec.universe) == (
        "V17-A4-P2-SILRES", "H1", ("BTCUSDT", "ETHUSDT"))
    assert (a_spec.family_id, a_spec.clock, a_spec.universe) == (
        "V17-a5-P1-ATTN-PHASE", "D1", ("BTCUSDT", "ETHUSDT", "SOLUSDT"))
    assert {arm.kind for arm in s_spec.arms} == {"anchor", "neighbour", "control"}
    assert {arm.kind for arm in a_spec.arms} == {"anchor", "neighbour", "control"}
    # SILRES frozen fills/holding: lag 0 (next-bucket vwap = position bucket),
    # K=2 anchor, K=4 neighbour override, control = anchor mechanics
    assert (s_spec.lag_buckets, s_spec.holding_buckets, s_spec.fill_price) == (
        0, 2, "vwap")
    by_kind = {arm.kind: arm for arm in s_spec.arms}
    assert by_kind["anchor"].exposure["formula_id"] == "SILRES.anchor"
    assert by_kind["anchor"].exposure["params"] == {
        "gap_percentile": 90.0, "resumption_multiple": 1.5, "warmup_buckets": 720}
    assert by_kind["neighbour"].holding_override == 4
    assert by_kind["neighbour"].exposure["params"] == {
        "gap_percentile": 75.0, "resumption_multiple": 1.2, "warmup_buckets": 720}
    assert by_kind["control"].exposure["formula_id"] == "SILRES.control"
    assert by_kind["control"].exposure["params"]["seed"] == 17040002
    assert by_kind["control"].exposure["params"]["block_buckets"] == 720
    assert by_kind["control"].holding_override is None  # K=2 like the anchor
    # ATTN-PHASE frozen fills/booking: day bucket-0 vwap, state machine
    assert (a_spec.lag_buckets, a_spec.holding_buckets) == (0, 1)
    assert a_spec.fill_price == "h1_bucket0_vwap" and a_spec.booking == "state_machine"
    a_by_kind = {arm.kind: arm for arm in a_spec.arms}
    assert a_by_kind["anchor"].exposure["params"] == {
        "window_start": 14, "window_end": 21, "median_days": 60, "min_hold_days": 1}
    assert a_by_kind["neighbour"].exposure["params"] == {
        "window_start": 13, "window_end": 22, "median_days": 90, "min_hold_days": 2}
    assert a_by_kind["control"].exposure["params"]["sham_rotation"] == "day_index_mod_24"
    assert a_by_kind["control"].exposure["params"]["rotation_origin"] == "2025-08-22"
    # all six formulas resolve; the example stays example-only
    for arm in (*s_spec.arms, *a_spec.arms):
        assert callable(reg.resolve(arm.exposure["formula_id"]))
        assert not reg.is_example_only(arm.exposure["formula_id"])
    assert reg.is_example_only("EXAMPLE_TEST_ONLY.h1_vwap_revert")


# -- synthetic staging through the REAL loader path (csv + sha manifest) -- #
def _write_silres_csv(directory: Path, symbol: str, n_days: int) -> None:
    spikes = {726, 750, 774, 798}
    path = directory / d.PANEL_FILE.format(symbol=symbol)
    lines = [",".join(d.H1_SCHEMA)]
    for idx in range(n_days * 24):
        day, hour = idx // 24, idx % 24
        gap, n = (50.0, 200) if idx in spikes else (1.0, 100)
        base = 100.0 + 0.01 * idx
        vwap = base * 1.0001
        row = {
            "symbol": symbol, "hour_utc": f"{_day(day)}T{hour:02d}",
            "day_utc": _day(day), "n_trades": n, "buy_count": 50,
            "sell_count": 50, "buy_qty": 10.0, "sell_qty": 10.0,
            "buy_quote": 10.0 * vwap, "sell_quote": 10.0 * vwap,
            "quote_total": 20.0 * vwap, "qty_total": 20.0, "vwap": vwap,
            "first_price": base, "last_price": base * 1.001,
            "high_price": base * 1.002, "low_price": base * 0.999,
            "max_trade_quote": 5.0, "sum_qty_squared": 400.0,
            "n_price_moves": 60, "sum_squared_log_ret": 0.001,
            "gap_sum_s": 2.5, "gap_count": 10, "entry_gap_s": gap,
            "run_close_dir": "buy", "run_close_len": 3, "run_switch_count": 2,
            "max_run_buy": 5, "max_run_sell": 4,
            "first_ts_ms": 1_724_000_000_000 + idx * 3_600_000,
            "last_ts_ms": 1_724_000_063_000 + idx * 3_600_000,
        }
        lines.append(",".join(
            repr(row[c]) if isinstance(row[c], float) else str(row[c])
            for c in d.H1_SCHEMA
        ))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_attn_csv(directory: Path, symbol: str, n_days: int) -> None:
    path = directory / d.PANEL_FILE.format(symbol=symbol)
    lines = [",".join(d.H1_SCHEMA)]
    idx = 0
    for day in range(n_days):
        for hour in range(24):
            if symbol == "SOLUSDT":
                if 14 <= hour <= 21:
                    n = 30 if day % 2 == 0 else 3
                else:
                    n = 5
            else:
                n = 10
            base = 100.0 + 0.05 * idx  # ~1.2%/day drift: gross >> T2.0 cost
            vwap = base * 1.0001
            row = {
                "symbol": symbol, "hour_utc": f"{_day(day)}T{hour:02d}",
                "day_utc": _day(day), "n_trades": n, "buy_count": 50,
                "sell_count": 50, "buy_qty": 10.0, "sell_qty": 10.0,
                "buy_quote": 10.0 * vwap, "sell_quote": 10.0 * vwap,
                "quote_total": 20.0 * vwap, "qty_total": 20.0, "vwap": vwap,
                "first_price": base, "last_price": base * 1.001,
                "high_price": base * 1.002, "low_price": base * 0.999,
                "max_trade_quote": 5.0, "sum_qty_squared": 400.0,
                "n_price_moves": 60, "sum_squared_log_ret": 0.001,
                "gap_sum_s": 2.5, "gap_count": 10, "entry_gap_s": 0.3,
                "run_close_dir": "buy", "run_close_len": 3,
                "run_switch_count": 2, "max_run_buy": 5, "max_run_sell": 4,
                "first_ts_ms": 1_724_000_000_000 + idx * 3_600_000,
                "last_ts_ms": 1_724_000_063_000 + idx * 3_600_000,
            }
            lines.append(",".join(
                repr(row[c]) if isinstance(row[c], float) else str(row[c])
                for c in d.H1_SCHEMA
            ))
            idx += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _stage(tmp_path: Path, spec: d.FamilySpec, n_days: int) -> dict:
    panel_dir = tmp_path / "staging"
    writer = _write_attn_csv if spec.clock == "D1" else _write_silres_csv
    for sym in spec.universe:
        writer(panel_dir, sym, n_days)
    doc = {
        "schema": "v17_run_artifact_v1",
        "artifact": "staging_panel_manifest",
        "symbols": list(spec.universe),
        "window": [_day(0), _day(n_days - 1)],
        "panel_sha256": {
            sym: d.sha256_bytes(
                (panel_dir / d.PANEL_FILE.format(symbol=sym)).read_bytes()
            )
            for sym in spec.universe
        },
        "hourly_rows": {sym: n_days * 24 for sym in spec.universe},
    }
    (panel_dir / "panel_manifest_v17_published.json").write_text(
        json.dumps(doc, sort_keys=True, indent=1), encoding="utf-8")
    manifest = d.load_manifest(
        panel_dir / "panel_manifest_v17_published.json")
    manifest["_panel_dir"] = panel_dir
    return manifest


SCORED_CATEGORIES = {
    "identity.jsonl", "per_period_series.jsonl", "per_symbol_breakdown.jsonl",
    "per_fold_breakdown.jsonl", "stress_tiers.jsonl", "drop_one_inputs.jsonl",
    "benchmark_context.jsonl", "margins_to_fail.jsonl", "counters.jsonl",
    "reproduction_inputs.jsonl",
}
HEAD = "0" * 40


def test_silres_spec_end_to_end_scored_and_sanitized(tmp_path, monkeypatch):
    _, (spec,) = d.load_selection(FAMILIES_DIR / "V17-A4-P2-SILRES.spec.json")
    manifest = _stage(tmp_path, spec, n_days=34)  # 816 buckets >= warmup 720
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    out = tmp_path / "out"
    result = d.run_family(spec, manifest, d.repo_root(), out,
                          sanitized=False, base_dir=tmp_path, code_freeze_sha=HEAD)
    # non-vacuous on every arm; the kernel charged cost once per fill
    for arm_id, res in result["arms"].items():
        assert res["kernel"]["n_round_trips"] > 0
        assert res["kernel"]["remediated_kernel"] is True
        assert res["kernel"]["cost_holding_terms"] == 0.0
    arm_files = {
        p.name for p in (out / "results/v17/V17-A4-P2-SILRES/anchor").iterdir()
    }
    # the 10 mandatory categories + the family's sham rows (not-applicable
    # marker per diag/sham_control_calendar@1, D2 re-freeze)
    assert arm_files == SCORED_CATEGORIES | {"sham_control_calendar.jsonl"}
    for arm_id in ("anchor", "neighbour", "control"):
        sham = [json.loads(ln) for ln in (
            out / f"results/v17/V17-A4-P2-SILRES/{arm_id}/sham_control_calendar.jsonl"
        ).read_text().splitlines() if ln.strip()]
        assert sham == [{
            "cycle_id": "CRYPTO-V17", "arm_id": arm_id,
            "calendar": "NOT_APPLICABLE:RESHUFFLED_INTERVAL_PLACEBO",
            "note": spec.sham_calendar["note"],
        }]
    # the anchor triggers exactly on the planted sparse spikes (both symbols
    # independently; 4 events per symbol in the >=720 zone)
    anchor = result["arms"]["anchor"]
    control = result["arms"]["control"]
    assert anchor["kernel"]["n_round_trips"] >= 4
    # the control preserves the anchor's sparse mask duty (same event count
    # modulo purge/off-grid refusals) while differing from it structurally
    assert control["kernel"]["n_round_trips"] > 0
    # margins carry arm identity (P-3 attribution)
    for arm_id in ("anchor", "neighbour", "control"):
        margins = [json.loads(ln) for ln in (
            out / f"results/v17/V17-A4-P2-SILRES/{arm_id}/margins_to_fail.jsonl"
        ).read_text().splitlines() if ln.strip()]
        assert [m["gate_id"] for m in margins] == ["G1", "G2", "G3", "G4", "G5"]
        assert all(m["arm_id"] == arm_id for m in margins)
    dsr = out / "results/v17/V17-A4-P2-SILRES/dsr_per_period_series.jsonl"
    assert dsr.exists()
    # sanitized dry-run: decisions only, non-vacuous, no outcome fields
    san = tmp_path / "san"
    summary = d.run_family(spec, manifest, d.repo_root(), san,
                           sanitized=True, base_dir=tmp_path, code_freeze_sha=HEAD)
    assert sum(summary["decisions"].values()) > 0
    for arm_id in ("anchor", "neighbour", "control"):
        recs = [json.loads(ln) for ln in (
            san / f"research/control/v17_run/q_dry_run/V17-A4-P2-SILRES/{arm_id}"
            / "decisions.jsonl").read_text().splitlines() if ln.strip()]
        assert recs and all(
            set(r) == {"cycle_id", "family_id", "arm_id", "date", "hour",
                       "decision_taken", "symbol"} for r in recs)
    # determinism: two scored runs are byte-identical
    out2 = tmp_path / "out2"
    d.run_family(spec, manifest, d.repo_root(), out2,
                 sanitized=False, base_dir=tmp_path, code_freeze_sha=HEAD)
    for rel in ("anchor", "neighbour", "control"):
        for name in arm_files:
            a = out / "results/v17/V17-A4-P2-SILRES" / rel / name
            b = out2 / "results/v17/V17-A4-P2-SILRES" / rel / name
            assert a.read_bytes() == b.read_bytes()


def test_attn_phase_spec_end_to_end_scored_and_sanitized(tmp_path, monkeypatch):
    _, (spec,) = d.load_selection(FAMILIES_DIR / "V17-a5-P1-ATTN-PHASE.spec.json")
    manifest = _stage(tmp_path, spec, n_days=100)  # >= 91-day neighbour warmup
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    out = tmp_path / "out"
    result = d.run_family(spec, manifest, d.repo_root(), out,
                          sanitized=False, base_dir=tmp_path, code_freeze_sha=HEAD)
    for arm_id in ("anchor", "neighbour", "control"):
        res = result["arms"][arm_id]
        assert res["kernel"]["n_round_trips"] > 0
        assert res["kernel"]["cost_holding_terms"] == 0.0
    arm_dir = out / "results/v17/V17-a5-P1-ATTN-PHASE/anchor"
    assert {p.name for p in arm_dir.iterdir()} == (
        SCORED_CATEGORIES | {"sham_control_calendar.jsonl"})
    for arm_id in ("anchor", "neighbour", "control"):
        sham = [json.loads(ln) for ln in (
            out / f"results/v17/V17-a5-P1-ATTN-PHASE/{arm_id}/sham_control_calendar.jsonl"
        ).read_text().splitlines() if ln.strip()]
        assert sham[0]["calendar"] == "SHAM_SESSION_ROTATION:k_t=day_index_mod_24"
        assert sham[0]["arm_id"] == arm_id
    # universe law: the reference symbols never trade -> zero contribution
    per_symbol = [json.loads(ln) for ln in (
        arm_dir / "per_symbol_breakdown.jsonl").read_text().splitlines()
        if ln.strip()]
    contrib = {r["symbol"]: r["contribution_pnl"] for r in per_symbol}
    assert contrib["BTCUSDT"] == 0.0 and contrib["ETHUSDT"] == 0.0
    assert contrib["SOLUSDT"] != 0.0  # the book actually traded SOL
    # state-machine force-flat: no booked trip escapes its fold / the purge;
    # the day-99 episodes (ON at the fold's last member day) force-flat at
    # that fold's last tradable H1 bucket vwap
    folds, purged = d.build_folds(100)
    fold_by_day = {day: f for f in folds for day in f.member_days}
    state = d.compute_family(spec, d.load_panels(
        d.repo_root(), manifest, spec.universe),
        base_dir=tmp_path, allow_example=False)
    anchor_trips = state["arms"]["anchor"]["trips"]
    assert anchor_trips
    for trip in anchor_trips:
        window = set(range(trip["entry_bucket"], trip["exit_bucket"] + 1))
        assert not (window & purged)
        assert window <= set(fold_by_day[trip["decision_bucket"]].member_days)
        if trip.get("forced_exit"):
            fold = fold_by_day[trip["decision_bucket"]]
            assert trip["exit_bucket"] == max(fold.member_days)
            assert trip["exit_price"] > 0.0
    forced = [t for t in anchor_trips if t.get("forced_exit")]
    assert forced  # the odd-day episodes are ON at day 99 (F2's last day)
    # min-hold 2 (neighbour): every neighbour episode spans >= 2 days
    neighbour_trips = state["arms"]["neighbour"]["trips"]
    assert neighbour_trips
    normal = [t for t in neighbour_trips if not t.get("forced_exit")]
    assert all(t["exit_bucket"] - t["entry_bucket"] >= 2 for t in normal)
    # anchor (min-hold 1) is allowed 1-day episodes: at least one exists
    assert any(
        t["exit_bucket"] - t["entry_bucket"] == 1
        for t in state["arms"]["anchor"]["trips"] if not t.get("forced_exit")
    )
    # the sham book differs from the anchor book structurally
    anchor_pnl = result["arms"]["anchor"]["kernel"]
    control_pnl = result["arms"]["control"]["kernel"]
    assert (anchor_pnl["n_round_trips"], anchor_pnl["cost_fills"]) != (
        control_pnl["n_round_trips"], control_pnl["cost_fills"])
    # sanitized dry-run non-vacuous
    san = tmp_path / "san"
    summary = d.run_family(spec, manifest, d.repo_root(), san,
                           sanitized=True, base_dir=tmp_path, code_freeze_sha=HEAD)
    assert sum(summary["decisions"].values()) > 0


# ------------------------------------------------------------------------- #
# (d) concretized diagnostic contracts bind through the governance gate
# ------------------------------------------------------------------------- #
def test_diag_contracts_pass_persistability_gate():
    for family_id, conditioned in (
        ("V17-A4-P2-SILRES", False),
        ("V17-a5-P1-ATTN-PHASE", True),
    ):
        doc = json.loads(
            (FAMILIES_DIR / f"{family_id}.diag_contract.json").read_text())
        contract = doc["contract"]
        assert contract["cycle_id"] == "CRYPTO-V17"
        assert contract["calendar_conditioned"] is conditioned
        verdict, findings = validate_contract(contract)
        assert verdict == "DIAGNOSTIC_CONTRACT_PASS"
        assert not [f for f in findings if f["severity"] == "HIGH"]
        # the recorded verdict block matches a fresh run of the gate
        assert doc["validate_contract"]["verdict"] == verdict
        assert doc["validate_contract"]["findings"] == findings
        # the artifact list derives from the contract and carries the canon
        artifacts, problems = expected_artifacts_from_contract(contract)
        assert not problems
        categories = {a["category"] for a in artifacts}
        # the sham rows derive from the contract iff the frozen predicate
        # applies (SILRES persists them under the accepted LOW finding)
        assert ("sham_control_calendar" in categories) is conditioned
        assert "dsr_per_period_series" in categories
        for a in artifacts:
            if a["category"] == "sham_control_calendar":
                assert a["required_fields"] == list(
                    CONDITIONAL_REQUIRED_FIELDS["sham_control_calendar"])
                assert a["artifact"].startswith(f"results/v17/{family_id}/")
        if conditioned:
            # ATTN-PHASE: the sham rows carry the frozen rotation descriptor
            spec_doc = SPEC_DOCS[family_id]["families"][0]
            assert (spec_doc["sham_calendar"]["calendar"]
                    == doc["concretization"]["sham_row_marker"]
                    == "SHAM_SESSION_ROTATION:k_t=day_index_mod_24")
        else:
            # SILRES: persist under the frozen predicate with the
            # not-applicable marker (accepted LOW, disclosed)
            spec_doc = SPEC_DOCS[family_id]["families"][0]
            assert (spec_doc["sham_calendar"]["calendar"]
                    == doc["concretization"]["sham_row_marker"]
                    == "NOT_APPLICABLE:RESHUFFLED_INTERVAL_PLACEBO")
            lows = [f for f in findings if f["severity"] == "LOW"
                    and f["category"] == "sham_control_calendar"]
            assert lows and "not applicable" in lows[0]["detail"]
    # the driver's canon mirrors the governance canon for the conditional
    assert set(d.CANON_FIELDS["sham_control_calendar"]) == set(
        CONDITIONAL_REQUIRED_FIELDS["sham_control_calendar"])


def test_lag_zero_still_refused_without_declared_fill_price():
    base = {
        "family_id": "SYNTH-LAG0", "clock": "H1",
        "universe": ["BTCUSDT"],
        "entry": {"lag_buckets": 0}, "exit": {"holding_buckets": 1},
        "arms": [
            {"arm_id": "a", "kind": "anchor",
             "exposure": {"type": "panel_formula",
                          "formula_id": "FAMTEST.h1_zero", "params": {}}},
            {"arm_id": "b", "kind": "neighbour",
             "exposure": {"type": "panel_formula",
                          "formula_id": "FAMTEST.h1_zero", "params": {}}},
            {"arm_id": "c", "kind": "control",
             "exposure": {"type": "panel_formula",
                          "formula_id": "FAMTEST.h1_zero", "params": {}}},
        ],
    }
    with pytest.raises(d.DriverError, match="lag_buckets"):
        d._parse_family(copy.deepcopy(base), base_dir=Path("/"))
    base["fill_price"] = "vwap"
    spec = d._parse_family(base, base_dir=Path("/"))
    assert spec.lag_buckets == 0 and spec.fill_price == "vwap"
    # and the unsupported fill price / booking / clock combos refuse
    bad = copy.deepcopy(base)
    bad["fill_price"] = "twap"
    with pytest.raises(d.DriverError, match="fill_price"):
        d._parse_family(bad, base_dir=Path("/"))
    bad = copy.deepcopy(base)
    bad["booking"] = "state_machine"
    with pytest.raises(d.DriverError, match="state_machine"):
        d._parse_family(bad, base_dir=Path("/"))
