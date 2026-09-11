"""FOREX-NG1 D2 measurement tests (hand-computed fixtures).

Covers the three required fixture classes:

1. a hand-computed Spearman rho on a synthetic schedule pair;
2. fail-closed behaviour when a measurement cannot be proven (missing
   as-of vintage, missing warmup observation, census pin drift);
3. a Q-6 recent-window floor case on a synthetic A4 book.

Run:
    .venv/bin/python -m pytest tests/test_forex_ng1_d2.py -q
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import date, timedelta

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng1/d2"
if WORKTREE not in sys.path:
    sys.path.insert(0, WORKTREE)

import pytest  # noqa: E402

from research.assets.forex_ng1.d2 import books as B      # noqa: E402
from research.assets.forex_ng1.d2 import events as E     # noqa: E402
from research.assets.forex_ng1.d2 import rho as R        # noqa: E402
from research.assets.forex_ng1.d2.series import (        # noqa: E402
    VintagedSeries, parse_realtime_observations, s1_seasonal_naive,
)


# --------------------------------------------------------------------------- #
# 1. hand-computed rho
# --------------------------------------------------------------------------- #

GRID5 = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04",
         "2024-01-05"]


def test_spearman_hand_computed_with_ties():
    # a = [1, 0, -1, 1, 0]  b = [-1, 1, -1, -1, 1]
    # average-tie ranks: a -> [4.5, 2.5, 1, 4.5, 2.5]
    #                     b -> [2, 4.5, 2, 2, 4.5]
    # Pearson on ranks: cov = -2.5, var_a = 9, var_b = 7.5
    # rho = -2.5 / sqrt(9 * 7.5)
    expected = -2.5 / math.sqrt(67.5)
    got = R.spearman([1.0, 0.0, -1.0, 1.0, 0.0],
                     [-1.0, 1.0, -1.0, -1.0, 1.0])
    assert got is not None
    assert abs(got - expected) < 1e-12


def test_netsigned_variant_hand_computed():
    a_cells = {
        "2024-01-01|GBPUSD": 1, "2024-01-02|GBPUSD": -1,
        "2024-01-03|GBPUSD": -1, "2024-01-04|GBPUSD": 1,
    }
    b_cells = {
        "2024-01-01|GBPUSD": -1, "2024-01-02|GBPUSD": 1,
        "2024-01-02|USDCAD": 1,   # netsigns to +1 on 01-02 (shared pair
                                  # restricts the sum to GBPUSD)
        "2024-01-03|GBPUSD": 1, "2024-01-05|GBPUSD": -1,
    }
    cmp = R.compare_schedules(a_cells, b_cells, GRID5, ["GBPUSD"])
    v = cmp["variants"]["netsigned_union_dates_shared_pairs"]
    # shared pair GBPUSD only; net-signed per date:
    #   a = [+1, -1, -1, +1, 0]   b = [-1, +1, +1, 0, -1]
    # average-tie ranks: a = [4.5, 1.5, 1.5, 4.5, 3]
    #                     b = [1.5, 4.5, 4.5, 3, 1.5]
    # means 3.0; cov = -6.75; var_a = 9; var_b = 9
    # rho = -6.75 / 9 = -0.75 (hand-computed)
    assert abs(v["rho"] - (-0.75)) < 1e-12, v
    assert abs(cmp["max_abs_rho"] - 0.75) < 1e-12


def test_perfect_anticorrelation_and_constant_vector():
    a = {f"{d}|GBPUSD": (1 if i % 2 == 0 else -1)
         for i, d in enumerate(GRID5)}
    b = {f"{d}|GBPUSD": (-1 if i % 2 == 0 else 1)
         for i, d in enumerate(GRID5)}
    cmp = R.compare_schedules(a, b, GRID5, ["GBPUSD"])
    for v in cmp["variants"].values():
        assert v["rho"] is not None and abs(abs(v["rho"]) - 1.0) < 1e-12
    # a constant vector cannot produce a rho (recorded None)
    flat = {f"{d}|GBPUSD": 1 for d in GRID5}
    assert R.spearman([1.0] * 5, [1, 2, 3, 4, 5]) is None


# --------------------------------------------------------------------------- #
# 2. fail-closed unmeasured cases
# --------------------------------------------------------------------------- #

def _mk_rows(windows):
    # windows: {(obs, rs, re): value}
    return [{"obs": f"{obs}-01", "rs": date.fromisoformat(rs),
             "re": date.fromisoformat(re_), "value": val}
            for (obs, rs, re_), val in windows.items()]


def test_s1_failclosed_missing_asof_vintage():
    """The predictor input 2022-12 exists only in a vintage that had
    been superseded BEFORE the decision date -> no containing window
    at the decision instant -> None (fail-closed, never backfilled)."""
    rows = _mk_rows({
        ("2022-12", "2023-01-01", "2024-01-05"): 128.0,
        ("2023-01", "2023-02-01", "2025-06-01"): 129.0,
        ("2023-12", "2024-01-01", "2025-06-01"): 140.0,
    })
    vs = VintagedSeries("TEST", rows)
    s, detail = s1_seasonal_naive(vs, "2024-01", 143.0,
                                  date(2024, 3, 1))
    assert s is None
    assert detail["reason"] == "vintage_value_unavailable_asof"


def test_s1_failclosed_warmup_observation_missing():
    """Quarterly spacing: ref 2024-04 needs the previous observation
    (2024-01), same quarter last year (2023-04) and the observation
    before that (2023-01); with 2023-04 absent the event fails closed
    with the warmup reason."""
    rows = _mk_rows({
        ("2023-01", "2023-02-01", "2025-06-01"): 100.0,
        ("2024-01", "2024-02-01", "2025-06-01"): 104.0,
        ("2024-04", "2024-05-01", "2025-06-01"): 105.0,
    })
    vs = VintagedSeries("TESTQ", rows)
    assert vs.spacing == "quarterly"
    s, detail = s1_seasonal_naive(vs, "2024-04", 106.0,
                                  date(2024, 6, 3))
    assert s is None
    assert detail["reason"] == "warmup_obs_months_missing"


def test_s1_hand_computed_monthly():
    """i_hat = I(m-1) * I(m-12) / I(m-13) = 140 * 129/128 = 141.09375;
    s1 = 100 * (143/141.09375 - 1) = 1.351348... pp."""
    windows = {}
    base = date(2021, 1, 1)
    for k in range(0, 45):
        m = base.year * 12 + base.month - 1 + k
        obs = f"{m // 12:04d}-{m % 12 + 1:02d}"
        windows[(obs, "2021-01-01", "2025-06-01")] = float(100 + k)
    vs = VintagedSeries("TESTM", _mk_rows(windows))
    s, detail = s1_seasonal_naive(vs, "2024-06", 143.0,
                                  date(2024, 7, 15))
    expected = 100.0 * (143.0 / (140.0 * 129.0 / 128.0) - 1.0)
    assert s is not None and abs(s - expected) < 1e-12
    assert detail["reason"] == "ok"


def test_census_pin_drift_failclosed(tmp_path):
    census = {"instants": [{"economy": "GB",
                            "publication_date": "2024-01-01",
                            "is_first_release_of_period": True}],
              "total_instants": 1}
    p = tmp_path / "census.json"
    p.write_text(json.dumps(census))
    with pytest.raises(E.CensusError):
        E.load_census(str(p))          # sha256 != pinned -> fail-closed


def test_parse_realtime_rejects_current_vintage_table():
    with pytest.raises(ValueError):
        parse_realtime_observations([{"date": "2024-01-01",
                                      "value": "100.0"}])


# --------------------------------------------------------------------------- #
# 3. Q-6 recent-window floor case (synthetic A4 book)
# --------------------------------------------------------------------------- #

def _synth_grid(start: date, weeks: int):
    days, d = [], start
    while len(days) < weeks * 5:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def _gb_event(ref: str, operative: str, print_value: str) -> dict:
    return {"economy": "GB", "reference_period": ref,
            "publication_date": operative,
            "operative_vintaged_available_from": operative,
            "vintaged_first_value": print_value,
            "is_first_release_of_period": True}


def _monthly_series(start_k0: date, n_months: int, base=100.0):
    windows = {}
    k0 = start_k0.year * 12 + start_k0.month - 1
    for k in range(k0, k0 + n_months):
        obs = f"{k // 12:04d}-{k % 12 + 1:02d}"
        windows[(obs, "2000-01-01", "2099-12-31")] = base + (k - k0)
    return VintagedSeries("SYN", _mk_rows(windows))


def test_q6_recent_floor_case():
    """Two in-window GB events with entry days inside 2023-05-01..
    2025-04-30 -> recent_pair_decisions_eligible = 2 < floor 8
    (floor FAIL); a nine-event variant passes the same floor."""
    grid = _synth_grid(date(2022, 11, 1), 130)     # ~2.5 years of weeks
    grid_index = {d: i for i, d in enumerate(grid)}
    window_end = grid[-1]
    events = [
        _gb_event("2022-10", "2022-11-15", "104.0"),    # outside recent
        _gb_event("2023-05", "2023-06-15", "106.0"),    # recent
        _gb_event("2024-02", "2024-03-15", "108.0"),    # recent
    ]
    vs = _monthly_series(date(2020, 1, 1), 60)
    book = B.build_a4_book("SYN-A4", "s1_seasonal_naive", 0.10,
                           events, {"GB": vs}, grid, grid_index,
                           window_end)
    m = book["meta"]
    assert m["events_in_window"] == 3
    assert m["pair_decisions_eligible"] == 3
    assert m["recent_events"] == 2
    assert m["recent_pair_decisions_eligible"] == 2
    # Q-6 floor semantics (A4 floor = 8 eligible recent decisions)
    assert (m["recent_pair_decisions_eligible"] >= 8) is False
    # nine recent events clear the floor
    events9 = ([_gb_event("2022-10", "2022-11-15", "104.0")] +
               [_gb_event(f"2023-{mm:02d}", f"2023-{mm:02d}-15",
                          f"{110 + mm}.0") for mm in range(6, 13)] +
               [_gb_event(f"2024-{mm:02d}", f"2024-{mm:02d}-15",
                          f"{120 + mm}.0") for mm in range(1, 3)])
    book9 = B.build_a4_book("SYN-A4-9", "s1_seasonal_naive", 0.10,
                            events9, {"GB": vs}, grid, grid_index,
                            window_end)
    m9 = book9["meta"]
    assert m9["recent_pair_decisions_eligible"] == 9
    assert (m9["recent_pair_decisions_eligible"] >= 8) is True


def test_a4_entry_clock_and_exposure_cells():
    """Operative 2022-11-15 (a Tuesday) -> D(e) = first grid day
    STRICTLY after it (2022-11-16); H=5 exposure cells on
    11-16..11-22 (grid days i..i+4)."""
    grid = _synth_grid(date(2022, 11, 1), 6)
    grid_index = {d: i for i, d in enumerate(grid)}
    vs = _monthly_series(date(2020, 1, 1), 60)
    book = B.build_a4_book("SYN-CLOCK", "s1_seasonal_naive", 0.10,
                           [_gb_event("2022-10", "2022-11-15",
                                      "104.0")],
                           {"GB": vs}, grid, grid_index, grid[-1])
    days = sorted({k.split("|")[0] for k in book["cells"]})
    assert days == ["2022-11-16", "2022-11-17", "2022-11-18",
                    "2022-11-21", "2022-11-22"]
    assert all(v == 1 or v == -1 for v in book["cells"].values())


def test_sham7d_shift_and_collision():
    """A single fired event shifts +7 calendar days with the same sign;
    a collision with another fired day of the same pair reshuffles
    (+7 again)."""
    grid = _synth_grid(date(2022, 11, 1), 8)
    grid_index = {d: i for i, d in enumerate(grid)}
    vs = _monthly_series(date(2020, 1, 1), 60)
    events = [_gb_event("2022-10", "2022-11-15", "104.0")]
    anchor = B.build_a4_book("SYN-SHAM", "s1_seasonal_naive", 0.10,
                             events, {"GB": vs}, grid, grid_index,
                             grid[-1])
    sham = B.build_sham7d_book(anchor, grid, grid_index, grid[-1])
    src_entry = anchor["fired_records"][0]["entry"]
    src_days = sorted({k.split("|")[0] for k in anchor["cells"]})
    sham_days = sorted({k.split("|")[0] for k in sham["cells"]})
    shift = (date.fromisoformat(sham_days[0])
             - date.fromisoformat(src_days[0])).days
    assert src_entry == date.fromisoformat(src_days[0])
    assert shift == 7
    assert set(anchor["cells"].values()) == set(sham["cells"].values())

    # collision: a second fired event whose day equals the shifted day
    # forces the sham one further +7 (total +14)
    ev2 = [_gb_event("2022-10", "2022-11-15", "104.0"),
           _gb_event("2022-11", "2022-11-22", "105.0")]
    anchor2 = B.build_a4_book("SYN-SHAM2", "s1_seasonal_naive", 0.10,
                              ev2, {"GB": vs}, grid, grid_index,
                              grid[-1])
    sham2 = B.build_sham7d_book(anchor2, grid, grid_index, grid[-1])
    days2 = sorted({k.split("|")[0] for k in sham2["cells"]})
    d0 = date.fromisoformat(days2[0])
    s0 = min(r["entry"] for r in anchor2["fired_records"])
    # first source event's sham lands either on a fired day (+14) or
    # free (+7); assert it never collides with a fired anchor day
    fired = {r["entry"].isoformat() for r in anchor2["fired_records"]}
    for d in days2:
        assert d not in fired
    assert (d0 - s0).days in (7, 14)


def test_order_state_interval_rule_failclosed():
    """Exact-time CA instant falling INSIDE a GB date-only window is
    unprovable order: the month demotes to no-unique-OF (fail-closed),
    never an inferred opener."""
    def ev(eco, pub, exact):
        return {"economy": eco, "publication_date": pub,
                "publication_instant_utc": (
                    "2024-07-17T12:30:00Z" if exact else
                    f"{pub}T23:59:59Z"),
                "time_precision": (
                    "CALENDAR_TIME_UTC_EXACT" if exact else
                    "DATE_ONLY_CONSERVATIVE_END_OF_DAY")}
    month = [
        ev("US", "2024-07-11", False),
        ev("GB", "2024-07-17", False),   # date-only whole day
        ev("CA", "2024-07-17", True),    # 12:30Z inside GB's window
        ev("NZ", "2024-07-23", False),
    ]
    state = E.order_state(month)
    assert state["counts"]["us_anchored_months"] == 1
    assert state["counts"]["unique_of_months"] == 0
    assert state["counts"]["no_unique_of_months"] == 1
    assert state["counts"]["co_earliest_events"] == 2   # GB + CA tie


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
