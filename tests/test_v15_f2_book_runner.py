"""V15 I lane (i-family-2) -- TAKER-SAT book goldens + runner kernel pins.

A HAND-COMPUTED synthetic staged world (12 symbols, constant engineered
features, constant 100.0 prices, known funding stamps) exercises the frozen
runner end-to-end.  Every expected number below is derived BY HAND in the
comments and asserted exactly (pytest.approx at 1e-12); no real staged data
is read anywhere, nothing is scored, no PnL exists outside these fixtures.

Hand world (base tier, fee 5 bps + 1 tick of 0.01 on price 100 -> 6e-4 per
unit notional per fill):

  A_bar(SYMii) = 1.0 + 0.05*ii and flat OI -> S = A_bar/0.02, so the
  descending rank is SYM11..SYM00; SHORT top 5 = SYM07..SYM11, LONG bottom
  5 = SYM00..SYM04 (middle SYM05/SYM06 unheld), each |w| = 0.10.
  Mini fold T0 = 2025-01-20..2025-02-08 (covered dates), decisions Jan 20 /
  25 / 30 / Feb 4, force-flat Feb 8 00:00.

  entry cost = 10 * 0.10 * 6e-4 = 6e-4; carried decisions charge 0;
  exit cost = 6e-4; cost_total = 1.2e-3 with cost_holding_terms == 0.
  Constant prices -> price_pnl 0; 18 daily funding stamps at 1e-4 inside
  the held span -> per-long funding -1.8e-4, per-short +1.8e-4, balanced
  book nets 0; span nets: long -2.4e-4 (x5), short +1.2e-4 (x5);
  position PF = 6e-4 / 1.2e-3 = 0.5; net_return_sum = -1.2e-3;
  expectancy = -2.4e-4 over 5 realized boundaries; MDD = 1.2e-3.
"""

from __future__ import annotations

import math
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
from research.adapter_v10.protocol import ContractViolation

from research.v15.families.taker_sat import book as book_mod
from research.v15.families.taker_sat import features
from research.v15.families.taker_sat.frozen_identity import (
    ANCHOR_ARM,
    CONTROL_ARM,
    NEIGHBOUR_ARM,
)
from research.v15.families.taker_sat.features import StagedDataError
from research.v15.families.taker_sat.refusal_registry import RefusalRegistry
from research.v15.families.taker_sat.runner import run_arm

DAY_MS = 86_400_000
NS = 1_000_000_000

SYMS = [f"SYM{i:02d}" for i in range(12)]
TICKS = {sym: 0.01 for sym in SYMS}
FOLDS_MINI = [("T0", "2025-01-20", "2025-02-09")]
FOLDS_TWO = [("T0", "2025-01-20", "2025-01-30"), ("T1", "2025-01-30", "2025-02-09")]

LABELS = [
    f"{hour:02d}:{minute:02d}:00"
    for hour in range(24)
    for minute in (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)
]
METRICS_DAYS = [datetime(2024, 12, 28, tzinfo=timezone.utc) + timedelta(days=k) for k in range(42)]
LEG_RATE = 5.0e-4 + 0.01 / 100.0  # 6e-4
ENTRY_COST = 10 * 0.10 * LEG_RATE  # 6e-4


def _a_bar(sym: str) -> float:
    return 1.0 + 0.05 * int(sym[3:])


def _ms(moment: datetime) -> int:
    return int(moment.timestamp() * 1000)


def _iso_date(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d")


def build_world(
    root: Path,
    *,
    oi_steps: dict[str, tuple[str, float, float]] | None = None,
    funding_stamps: list[tuple[datetime, float]] | None = None,
    missing_bars: set[tuple[str, datetime]] | None = None,
    bar_price_overrides: dict[tuple[str, datetime], float] | None = None,
    metrics_days: list[datetime] | None = None,
    symbols: list[str] | None = None,
) -> Path:
    """Write a tiny synthetic staged root (metrics/klines/funding parquet)."""
    symbols = list(symbols or SYMS)
    metrics_days = list(metrics_days or METRICS_DAYS)
    oi_steps = dict(oi_steps or {})
    (root / "metrics").mkdir(parents=True)
    (root / "klines").mkdir(parents=True)
    (root / "funding").mkdir(parents=True)
    for sym in symbols:
        ratio = math.exp(_a_bar(sym))
        step = oi_steps.get(sym)
        rows = []
        for day in metrics_days:
            date_str = _iso_date(day)
            oi = 100.0
            if step is not None and date_str >= step[0]:
                oi = step[2]
            elif step is not None:
                oi = step[1]
            for label in LABELS:
                rows.append(
                    {
                        "create_time": f"{date_str} {label}",
                        "symbol": sym,
                        "sum_open_interest": 1000.0,
                        "sum_open_interest_value": oi,
                        "count_toptrader_long_short_ratio": 1.0,
                        "sum_toptrader_long_short_ratio": 1.0,
                        "count_long_short_ratio": 1.0,
                        "sum_taker_long_short_vol_ratio": ratio,
                    }
                )
        frame = pd.DataFrame(rows)
        frame["ts"] = pd.to_datetime(frame["create_time"], format="%Y-%m-%d %H:%M:%S")
        frame.to_parquet(root / "metrics" / f"{sym}.parquet", index=False)

        bars = []
        day = datetime(2025, 1, 19, tzinfo=timezone.utc)
        while day <= datetime(2025, 2, 9, tzinfo=timezone.utc):
            for slot in range(96):
                open_time = day + timedelta(minutes=15 * slot)
                if missing_bars and (sym, open_time) in missing_bars:
                    continue
                price = 100.0
                if bar_price_overrides and (sym, open_time) in bar_price_overrides:
                    price = bar_price_overrides[(sym, open_time)]
                open_ms = _ms(open_time)
                bars.append(
                    {
                        "open_time_ms": open_ms,
                        "open": price,
                        "high": price,
                        "low": price,
                        "close": price,
                        "volume": 1.0,
                        "close_time_ms": open_ms + 899_999,
                    }
                )
            day += timedelta(days=1)
        pd.DataFrame(bars).to_parquet(root / "klines" / f"{sym}.parquet", index=False)

        if funding_stamps is None:
            # 18 daily stamps at 00:00:00.002, Jan 21 .. Feb 7 (1e-4 each)
            stamps = [
                (
                    datetime(2025, 1, day, tzinfo=timezone.utc)
                    + timedelta(milliseconds=2),
                    1e-4,
                )
                for day in range(21, 32)
            ] + [
                (
                    datetime(2025, 2, day, tzinfo=timezone.utc)
                    + timedelta(milliseconds=2),
                    1e-4,
                )
                for day in range(1, 8)
            ]
        else:
            stamps = list(funding_stamps)
        pd.DataFrame(
            {
                "funding_time_ms": [_ms(t) for t, _r in stamps],
                "funding_rate": [r for _t, r in stamps],
            }
        ).to_parquet(root / "funding" / f"{sym}.parquet", index=False)
    return root


LONGS = ["SYM00", "SYM01", "SYM02", "SYM03", "SYM04"]
SHORTS = ["SYM07", "SYM08", "SYM09", "SYM10", "SYM11"]


def _book_weights(cell: dict, index: int) -> dict[str, float]:
    return {
        sym: weight for sym, weight in cell["books"][index]["weights"]
    }


# --------------------------------------------------------------------------- #
# Pure book goldens
# --------------------------------------------------------------------------- #
def test_v15f2_build_book_golden_5v5_fade():
    scores = {sym: 50.0 + 2.5 * int(sym[3:]) for sym in SYMS}
    payload = book_mod.build_book(scores)
    assert payload["reason_code"] == book_mod.REASON_OK
    assert payload["n_available"] == 12
    weights = dict(payload["weights"])
    assert set(weights) == set(LONGS) | set(SHORTS)
    for sym in LONGS:
        assert weights[sym] == 0.10
    for sym in SHORTS:
        assert weights[sym] == -0.10
    assert payload["gross"] == pytest.approx(1.0)
    assert payload["max_abs_weight"] == pytest.approx(0.10)
    ranks = dict(payload["ranks"])
    assert ranks["SYM11"] == 1  # extreme buy-side saturation -> SHORT side
    assert ranks["SYM00"] == 12
    assert dict(payload["shorts"])["SYM11"] == -0.10
    assert dict(payload["longs"])["SYM00"] == 0.10
    for sym in ("SYM05", "SYM06"):
        assert sym not in weights  # middle of the cross-section unheld


def test_v15f2_build_book_tie_break_symbol_ascending():
    scores = {sym: float(10 - int(sym[3:])) for sym in SYMS}
    scores["SYM05"] = scores["SYM06"]  # exact tie in the middle
    payload = book_mod.build_book(scores)
    ranks = dict(payload["ranks"])
    assert ranks["SYM05"] < ranks["SYM06"]  # name ascending on equal values
    scores2 = {sym: 1.0 for sym in SYMS}  # all tied: full name ordering
    payload2 = book_mod.build_book(scores2)
    ranks2 = dict(payload2["ranks"])
    ordered = sorted(SYMS, key=lambda s: ranks2[s])
    assert ordered == sorted(SYMS)


def test_v15f2_build_book_below_min_available_stays_flat():
    scores = {sym: 1.0 + 0.1 * i for i, sym in enumerate(SYMS[:9])}
    payload = book_mod.build_book(scores)
    assert payload["weights"] == {}
    assert payload["reason_code"] == book_mod.REASON_INSUFFICIENT_AVAILABLE
    assert payload["gross"] == 0.0


def test_v15f2_transition_cost_charged_once_per_fill():
    new = {"SYM00": 0.10, "SYM07": -0.10}
    once = book_mod.transition_cost(
        {}, new, prices={"SYM00": 100.0, "SYM07": 100.0},
        tick_sizes=TICKS, taker_fee_bps=5.0, slip_ticks=1,
    )
    assert once == pytest.approx(2 * 0.10 * LEG_RATE)
    # identical books are carried: exactly zero cost
    carried = book_mod.transition_cost(
        new, new, prices={"SYM00": 100.0, "SYM07": 100.0},
        tick_sizes=TICKS, taker_fee_bps=5.0, slip_ticks=1,
    )
    assert carried == 0.0
    # a flip charges both legs exactly once: |dw| = 0.2
    flip = book_mod.transition_cost(
        {"SYM00": 0.10}, {"SYM00": -0.10}, prices={"SYM00": 100.0},
        tick_sizes=TICKS, taker_fee_bps=5.0, slip_ticks=1,
    )
    assert flip == pytest.approx(0.2 * LEG_RATE)


# --------------------------------------------------------------------------- #
# Runner kernel: hand world (module-scoped synthetic staged root)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def world(tmp_path_factory) -> Path:
    return build_world(tmp_path_factory.mktemp("v15f2_world"))


def _run(world_root: Path, arm_id: str = ANCHOR_ARM, **kwargs):
    kwargs.setdefault("tick_sizes", TICKS)
    kwargs.setdefault("universe", SYMS)
    kwargs.setdefault("folds", FOLDS_MINI)
    return run_arm(arm_id, world_root, scored=False, **kwargs)


def test_v15f2_anchor_cell_hand_golden(world):
    cell = _run(world)
    scored = cell["scored_metrics"]
    assert cell["scored"] is False
    assert cell["arm_id"] == ANCHOR_ARM
    assert cell["role"] == "anchor"
    # fills: 10 entries + 10 exits; each fill charged exactly once
    assert scored["n_fills"] == 20
    assert scored["n_positions"] == 10
    assert scored["n_decisions"] == 40  # 4 decision dates x 10 names
    assert scored["cost_fills"] == pytest.approx(2 * ENTRY_COST)
    assert scored["cost_holding_terms"] == 0.0
    assert scored["cost_total"] == pytest.approx(1.2e-3)
    assert scored["price_pnl_sum"] == 0.0
    assert scored["funding_sum"] == pytest.approx(0.0)  # balanced 5v5 book
    assert scored["net_return_sum"] == pytest.approx(-1.2e-3)
    assert scored["expectancy_per_day"] == pytest.approx(-2.4e-4)
    assert scored["max_drawdown"] == pytest.approx(1.2e-3)
    # gains: 5 shorts x (1.8e-4 - 1.2e-4) = 3e-4; losses: 5 longs x 3e-4
    assert scored["position_pf"] == pytest.approx(0.2)
    assert scored["daily_hit_rate"] == 0.0
    assert scored["score_valid"] is True
    assert scored["remediated_kernel"] is True
    # realized rows: entry / 3 carried / exit
    rows = cell["daily_returns"]
    assert len(rows) == 5
    assert [round(r["net_return_per_unit"], 12) for r in rows] == pytest.approx(
        [-6e-4, 0.0, 0.0, 0.0, -6e-4]
    )
    assert [r["carried_boundary"] for r in rows] == [False, True, True, True, False]
    # per-span hand accounting (each span carries entry + exit cost legs)
    spans = {p["symbol"]: p for p in cell["positions"]}
    for sym in LONGS:
        span = spans[sym]
        assert span["signed_weight"] == 0.10
        assert span["price_pnl_per_unit"] == 0.0
        assert span["funding_cashflow_per_unit"] == pytest.approx(-1.8e-4)
        assert span["cost_allocated_per_unit"] == pytest.approx(2 * 0.10 * LEG_RATE)
        assert span["net_pnl_per_unit"] == pytest.approx(
            -1.8e-4 - 2 * 0.10 * LEG_RATE
        )
    for sym in SHORTS:
        span = spans[sym]
        assert span["funding_cashflow_per_unit"] == pytest.approx(1.8e-4)
        assert span["net_pnl_per_unit"] == pytest.approx(
            1.8e-4 - 2 * 0.10 * LEG_RATE
        )
    # book shape at the first decision
    weights = _book_weights(cell, 0)
    assert {s for s, w in weights.items() if w > 0} == set(LONGS)
    assert {s for s, w in weights.items() if w < 0} == set(SHORTS)
    # force-flat: the final book is empty and every span closed at the purge
    assert cell["books"][-1]["kind"] == "force_flat"
    assert cell["books"][-1]["weights"] == []
    final_ns = cell["books"][-1]["fill_ns"]
    assert all(p["exit_ns"] <= final_ns for p in cell["positions"])
    assert all(p["exit_ns"] >= p["entry_ns"] for p in cell["positions"])
    # fold nets + concentration
    assert cell["fold_signs"]["fold_net_sums"] == {"T0": pytest.approx(-1.2e-3)}
    assert cell["fold_signs"]["fold_positive"] == [False]
    shares = cell["per_symbol"]["positive_pnl_share_by_symbol"]
    assert all(shares[s] == pytest.approx(0.2) for s in SHORTS)
    assert cell["per_symbol"]["largest_symbol_positive_pnl_share"] == pytest.approx(0.2)
    assert "result_sha256" in cell["hashes"]
    assert cell["refusals"]["count"] == 0
    assert cell["defect_cells"]["count"] == 0


def test_v15f2_deterministic_double_generation(world):
    first = _run(world)
    second = _run(world)
    assert first == second
    assert first["hashes"]["result_sha256"] == second["hashes"]["result_sha256"]


def test_v15f2_no_lookahead_cell_mutation_is_inert(world, tmp_path):
    """Mutating metrics dated AFTER every window the schedule can read
    (the last decision Feb 4 reads at most Feb 1) cannot move the cell."""
    mutated_root = tmp_path / "mutated"
    mutated_root.mkdir()
    for sym in SYMS:
        src = world / "metrics" / f"{sym}.parquet"
        frame = pd.read_parquet(src)
        mask = frame["create_time"] >= "2025-02-02"
        frame.loc[mask, "sum_taker_long_short_vol_ratio"] = 4.999
        (mutated_root / "metrics").mkdir(parents=True, exist_ok=True)
        frame.to_parquet(mutated_root / "metrics" / f"{sym}.parquet", index=False)
    for sub in ("klines", "funding"):
        shutil.copytree(world / sub, mutated_root / sub)
    # a late funding stamp beyond the final force-flat is equally inert
    base = _run(world)
    mutated = _run(mutated_root)
    assert mutated["hashes"] == base["hashes"]


def test_v15f2_stress_tier_hand_golden(world):
    cell = _run(world, stress_tier="stress")
    scored = cell["scored_metrics"]
    stress_leg = 7.5e-4 + 3 * 0.01 / 100.0  # fee x1.5 + 3 ticks on price 100
    assert scored["cost_total"] == pytest.approx(2 * 10 * 0.10 * stress_leg)
    assert scored["net_return_sum"] == pytest.approx(-2 * 10 * 0.10 * stress_leg)
    assert scored["cost_holding_terms"] == 0.0
    assert cell["cost_model"]["fee_multiplier"] == 1.5
    assert cell["cost_model"]["slip_ticks"] == 3
    assert cell["cost_model"]["delay_days"] == 1
    # decision fills move to the NEXT day's 00:00 open; the force-flat exit
    # stays AT the fold boundary (the fold contract is binding)
    ns_day = 86_400 * NS
    entry_fill = scored["fills"][0]["ts_ns"]
    exit_fill = max(f["ts_ns"] for f in scored["fills"])
    assert entry_fill - cell["books"][0]["decision_ns"] == ns_day
    assert exit_fill == cell["books"][-1]["fill_ns"]  # Feb 8, NOT delayed
    # funding still counted once: same 18 stamps inside the shifted span
    spans = {p["symbol"]: p for p in cell["positions"]}
    assert spans["SYM00"]["funding_cashflow_per_unit"] == pytest.approx(-1.8e-4)


def test_v15f2_funding_once_per_stamp_boundary(world, tmp_path):
    """Half-open interval chaining attributes each settlement stamp to
    EXACTLY ONE held interval: a stamp at an interval's lo bound belongs to
    that interval, a stamp at its hi bound to the NEXT one."""
    from research.v15.families.taker_sat.runner import _funding_sum

    rows = [(20, 1e-4), (25, 1e-4), (30, 1e-4)]
    assert _funding_sum(rows, 20, 25) == pytest.approx(1e-4)  # lo stamp counted
    assert _funding_sum(rows, 25, 30) == pytest.approx(1e-4)  # the 25 stamp HERE
    assert _funding_sum(rows, 30, 35) == pytest.approx(1e-4)  # the 30 stamp HERE
    assert _funding_sum(rows, 35, 40) == 0.0  # hi stamps never leak back
    chained = math.fsum(
        _funding_sum(rows, lo, lo + 5) for lo in (20, 25, 30, 35)
    )
    assert chained == pytest.approx(3e-4)  # 3 stamps, each counted exactly once
    # world-level: 18 stamps over the held span; the balanced 5v5 book nets
    # zero per realized row while spans carry the signed legs
    cell = _run(world)
    spans = {p["symbol"]: p for p in cell["positions"]}
    assert spans["SYM00"]["funding_cashflow_per_unit"] == pytest.approx(-1.8e-4)
    assert spans["SYM07"]["funding_cashflow_per_unit"] == pytest.approx(1.8e-4)
    rows_out = cell["daily_returns"][1:4]
    assert all(r["funding_cashflow_per_unit"] == pytest.approx(0.0) for r in rows_out)


def test_v15f2_rank_swap_partial_turnover_cost(tmp_path):
    """An OI step for SYM05 (unheld middle) landing inside Jan 25's window
    but outside Jan 20's drops its saturation below the long side: at Jan 25
    exactly one long (SYM04) swaps out and SYM05 swaps in (2 fills).  As the
    window slides fully past the step (Jan 30 reads [Jan 18, Jan 27], both
    endpoints at the new level), the churn vanishes and the swap reverts --
    the churn denominator keeps modulating the book through time."""
    root = build_world(tmp_path / "swap", oi_steps={"SYM05": ("2025-01-18", 100.0, 110.0)})
    cell = _run(root)
    scored = cell["scored_metrics"]
    assert scored["n_fills"] == 24  # 10 entry + 2 + 2 swaps + 10 exit
    assert scored["n_positions"] == 12
    assert scored["cost_total"] == pytest.approx(2 * ENTRY_COST + 4 * 0.10 * LEG_RATE)
    # the book changes at BOTH the Jan 25 and Jan 30 decisions
    assert cell["books"][1]["carried_forward"] is False
    weights_2 = _book_weights(cell, 1)
    assert "SYM04" not in weights_2
    assert weights_2["SYM05"] == 0.10
    swaps_in = [f for f in scored["fills"] if f["ts_ns"] == cell["books"][1]["fill_ns"]]
    assert sorted(f["symbol"] for f in swaps_in) == ["SYM04", "SYM05"]
    assert all(f["cost"] == pytest.approx(0.10 * LEG_RATE) for f in swaps_in)
    assert cell["books"][2]["carried_forward"] is False
    weights_3 = _book_weights(cell, 2)
    assert "SYM05" not in weights_3
    assert weights_3["SYM04"] == 0.10
    swaps_out = [f for f in scored["fills"] if f["ts_ns"] == cell["books"][2]["fill_ns"]]
    assert sorted(f["symbol"] for f in swaps_out) == ["SYM04", "SYM05"]
    # the Feb 4 decision then carries the standard book unchanged
    assert cell["books"][3]["carried_forward"] is True
    assert _book_weights(cell, 3) == _book_weights(cell, 0)


def test_v15f2_next_allowed_fill_uses_next_same_day_bar(tmp_path):
    missing = {( "SYM00", datetime(2025, 1, 20, tzinfo=timezone.utc))}
    overrides = {( "SYM00", datetime(2025, 1, 20, tzinfo=timezone.utc, minute=15)): 100.5}
    root = build_world(
        tmp_path / "latebar", missing_bars=missing, bar_price_overrides=overrides
    )
    cell = _run(root)
    entry = [f for f in cell["scored_metrics"]["fills"] if f["symbol"] == "SYM00" and f["weight_delta"] > 0]
    assert entry[0]["price"] == pytest.approx(100.5)  # 00:15 open, same UTC day
    # the position realizes from its actual fill price to the next boundary
    span = next(p for p in cell["positions"] if p["symbol"] == "SYM00")
    assert span["entry_price"] == pytest.approx(100.5)
    assert span["price_pnl_per_unit"] == pytest.approx(0.10 * (100.0 - 100.5) / 100.5)


def test_v15f2_hole_refusals_shrink_cross_section_and_can_flatten(tmp_path):
    """3 symbols with a 2-of-10-day window hole at the FIRST decision only:
    9 available < 10 -> that cycle stays flat (registry + no fills); the
    next decision is fully populated and trades."""
    root = build_world(tmp_path / "holes")
    for sym in ("SYM00", "SYM01", "SYM02"):
        path = root / "metrics" / f"{sym}.parquet"
        frame = pd.read_parquet(path)
        mask = frame["create_time"].str.startswith(("2025-01-10", "2025-01-11"))
        frame = frame[~mask]
        frame.to_parquet(path, index=False)
    cell = _run(root)
    by_reason = cell["refusals"]["by_reason"]
    assert by_reason == {
        "HOLE_FRACTION_EXCEEDED": 3,
        "INSUFFICIENT_AVAILABLE_NAMES": 1,
    }
    assert cell["books"][0]["weights"] == []
    assert cell["books"][0]["reason_code"] == "INSUFFICIENT_AVAILABLE_NAMES"
    # first fills happen at the SECOND decision boundary
    first_fill_ns = min(f["ts_ns"] for f in cell["scored_metrics"]["fills"])
    assert first_fill_ns == cell["books"][1]["fill_ns"]
    assert cell["scored_metrics"]["n_fills"] == 20
    assert cell["scored_metrics"]["n_positions"] == 10
    # the flat first cycle charges nothing
    assert cell["daily_returns"][0]["cost_charged_per_unit"] == 0.0


def test_v15f2_force_flat_folds_no_cross_fold_holding(tmp_path):
    root = build_world(tmp_path / "twofolds")
    cell = run_arm(
        ANCHOR_ARM,
        root,
        scored=False,
        tick_sizes=TICKS,
        universe=SYMS,
        folds=FOLDS_TWO,
    )
    rows = cell["daily_returns"]
    assert len(rows) == 6  # Jan 20, 25, 29(ff), 30, Feb 4, Feb 8(ff)
    assert [r["fold_label"] for r in rows] == ["T0", "T0", "T0", "T1", "T1", "T1"]
    assert [round(r["net_return_per_unit"], 12) for r in rows] == pytest.approx(
        [-6e-4, 0.0, -6e-4, -6e-4, 0.0, -6e-4]
    )
    assert cell["scored_metrics"]["cost_total"] == pytest.approx(4 * ENTRY_COST)
    assert cell["scored_metrics"]["n_positions"] == 20
    assert cell["scored_metrics"]["n_fills"] == 40
    # no position spans across the fold boundary: T0 spans end at the Jan 29
    # force-flat; T1 spans start at the Jan 30 re-entry
    from research.v11.families.oilever_delev.strategy import parse_iso_utc

    t0_end = parse_iso_utc("2025-01-30T00:00:00Z")
    for p in cell["positions"]:
        if p["fold_label"] == "T0":
            assert p["entry_ns"] < t0_end and p["exit_ns"] < t0_end
        else:
            assert p["entry_ns"] >= t0_end and p["exit_ns"] > t0_end
    # flat inside the T0->T1 gap: the Jan 29 force-flat book is empty
    assert cell["books"][2]["weights"] == []
    # per-fold nets are separately accounted
    assert cell["fold_signs"]["fold_net_sums"]["T0"] == pytest.approx(-1.2e-3)
    assert cell["fold_signs"]["fold_net_sums"]["T1"] == pytest.approx(-1.2e-3)
    # the Jan 29 stamp falls in the flat gap and is never counted: the T0
    # span holds [Jan 20, Jan 29) -> 8 stamps; the T1 span [Jan 30, Feb 8)
    # -> 9 stamps; 17 of the 18 stamps hit a live position
    t0_span = next(
        p for p in cell["positions"]
        if p["symbol"] == "SYM00" and p["fold_label"] == "T0"
    )
    t1_span = next(
        p for p in cell["positions"]
        if p["symbol"] == "SYM00" and p["fold_label"] == "T1"
    )
    assert t0_span["funding_cashflow_per_unit"] == pytest.approx(-8e-5)
    assert t1_span["funding_cashflow_per_unit"] == pytest.approx(-9e-5)


def test_v15f2_control_arm_runs_same_book_on_raw_feature(world):
    anchor = _run(world)
    control = _run(world, arm_id=CONTROL_ARM)
    assert control["arm_id"] == CONTROL_ARM
    assert control["role"] == "causal_negative_control"
    # identical hand world -> identical books, identical kernel arithmetic
    assert control["scored_metrics"]["n_fills"] == 20
    assert control["scored_metrics"]["cost_total"] == pytest.approx(1.2e-3)
    assert [b["weights"] for b in control["books"]] == [b["weights"] for b in anchor["books"]]
    assert control["hashes"] != anchor["hashes"]  # distinct arm payloads
    neighbour = _run(world, arm_id=NEIGHBOUR_ARM)
    assert neighbour["role"] == "neighbour"
    assert neighbour["scored_metrics"]["cost_total"] == pytest.approx(1.2e-3)


def test_v15f2_malformed_staged_inputs_fail_closed(world, tmp_path):
    # funding rate beyond the documented cap
    bad_funding = build_world(
        tmp_path / "badfund",
        funding_stamps=[(datetime(2025, 1, 22, tzinfo=timezone.utc), 0.05)],
    )
    with pytest.raises(StagedDataError):
        _run(bad_funding)
    # duplicate kline stamps
    dup = build_world(tmp_path / "dupbar")
    path = dup / "klines" / "SYM00.parquet"
    frame = pd.read_parquet(path)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame.to_parquet(path, index=False)
    with pytest.raises(StagedDataError):
        _run(dup)
    # missing klines file
    miss = build_world(tmp_path / "missbar")
    (miss / "klines" / "SYM03.parquet").unlink()
    with pytest.raises(StagedDataError):
        _run(miss)
    # missing metrics file
    miss_m = build_world(tmp_path / "missmetrics")
    (miss_m / "metrics" / "SYM03.parquet").unlink()
    with pytest.raises(StagedDataError):
        _run(miss_m)


def test_v15f2_refusal_registry_digest_is_stable_and_append_once():
    registry = RefusalRegistry()
    assert registry.record("2025-01-20", "SYM00", "HOLE_FRACTION_EXCEEDED")
    assert not registry.record("2025-01-20", "SYM00", "HOLE_FRACTION_EXCEEDED")
    registry.record("2025-01-20", "", "INSUFFICIENT_AVAILABLE_NAMES")
    digest = registry.digest()
    assert len(digest) == 64
    again = RefusalRegistry.from_payload(registry.to_payload())
    assert again.digest() == digest
    assert again.count_by_reason() == {
        "HOLE_FRACTION_EXCEEDED": 1,
        "INSUFFICIENT_AVAILABLE_NAMES": 1,
    }
    other = RefusalRegistry()
    other.record("2025-01-25", "SYM01", "WINDOW_ENDPOINT_MISSING")
    assert other.digest() != digest
