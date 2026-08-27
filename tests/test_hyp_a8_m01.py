"""Wave-I M01 module tests: SYNTHETIC data only (PLAN.md section 8 I1).

Coverage, grouped as required by the implementation brief:

* determinism -- two independent builds produce identical canonical hashes;
* PIT guarantees -- signals at decision instant D consume only bars closed
  <= D, proven by hand-fixture aggregates AND post-cutoff perturbation
  invariance;
* fill timing -- fills land at the OPEN of the bar covering the UTC boundary,
  walk forward under the ``plus_1_event_delay`` stress cell, and never invent
  an event where the opening slot is missing;
* weight algebra -- unit gross, CAP=0.30 bound, continuous monotone weights,
  dollar-neutrality behaviour INCLUDING the clip-induced residual;
* funding accrual accounting hook -- native settlements injected as a fixture,
  sign convention LONG_PAYS_POSITIVE_RATE, half-open span semantics;
* condition-C2 strengthened negative control -- verbatim quotes carried as
  named constants, the price-placebo arm, and the wide-range flip probe;
* stress-parameter plumbing -- fee multiplier, tick slip, event delay,
  drop-one-symbol and drop-one-fold as pure parameter changes;
* the C1 field-population verifier against a synthetic REAL-layout parquet
  tree, both VERIFIED pass and forced FAIL_CLOSED paths.

No real catalog data is read, nothing is scored, PnL/PF/MDD never appear.
"""

from __future__ import annotations

import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import research.hyp_a8_m01 as m01  # noqa: E402
from research.hyp_a8_m01 import M01Bar  # noqa: E402

BASE_DAY = int(datetime(2025, 9, 1, tzinfo=timezone.utc).timestamp()) * 1_000_000_000
STEP = m01.BAR_INTERVAL_NS
DAY = m01.DAY_NS
CLOSE_SHAVE_NS = 100_000  # real Binance close stamps sit ~100us inside the grid

SYMBOLS = (
    "ALPHAUSDT",
    "BETAUSDT",
    "GAMMAUSDT",
    "DELTAUSDT",
    "EPSILONUSDT",
    "ZETAUSDT",
    "ETAUSDT",
    "THETAUSDT",
    "IOTAUSDT",
    "KAPPAUSDT",
)


def iso(ns: int) -> str:
    return m01.iso_from_ns(ns)


def day_from_iso(text: str) -> int:
    return m01.parse_iso_utc_ns(text)


def day_midnight(index: int) -> int:
    return BASE_DAY + index * DAY


# --------------------------------------------------------------------------- #
# Synthetic bar factory
# --------------------------------------------------------------------------- #
PRICE_SCALE = 10 ** 16


def _fixed16(value: float) -> bytes:
    return int(round(value * PRICE_SCALE)).to_bytes(16, "little", signed=True)


def block_bars(
    *,
    symbol: str,
    day_start_ns: int,
    flow_f: float,
    quote_volume: float = 96_000.0,
    n_bars: int = m01.BARS_PER_BLOCK,
    count: int = 11,
    open_px: float = 100.0,
    move_fraction: float = 0.0,
    range_spread: float = 0.001,
) -> list[M01Bar]:
    """One UTC-day block of completed 15m bars with controlled observables."""
    bars: list[M01Bar] = []
    price = open_px
    growth = (1.0 + move_fraction) ** (1.0 / max(1, n_bars))
    for i in range(n_bars):
        nxt = price * growth
        mid = (price + nxt) / 2.0
        ts_event = day_start_ns + (i + 1) * STEP - CLOSE_SHAVE_NS
        # Deterministic per-bar variation keeps every observable non-degenerate,
        # mirroring real exchange tape (C1 census rejects constant columns).
        jitter = 1.0 + 0.04 * ((i % 5) - 2)
        qty = jitter * quote_volume / n_bars / mid
        bars.append(
            M01Bar(
                ts_event_ns=ts_event,
                ts_init_ns=ts_event,
                open=price,
                high=max(price, nxt) * (1.0 + range_spread),
                low=min(price, nxt) * (1.0 - range_spread),
                close=nxt,
                volume=qty,
                quote_volume=qty * mid,
                count=count + i % 3,
                taker_buy_quote_volume=flow_f * qty * mid,
            )
        )
        price = nxt
    return bars


def rescale_taker(bar: M01Bar, target_share: float) -> M01Bar:
    """Return the same bar rewritten so taker share equals ``target_share``."""
    return M01Bar(
        ts_event_ns=bar.ts_event_ns,
        ts_init_ns=bar.ts_init_ns,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        quote_volume=bar.quote_volume,
        count=bar.count,
        taker_buy_quote_volume=target_share * bar.quote_volume,
    )


def multi_day_bars(
    *,
    symbol: str,
    days: int,
    flow_by_day_index,
    move_by_day_index=None,
    sym_index: int = 0,
    open_px: float = 100.0,
    **kwargs,
) -> list[M01Bar]:
    out: list[M01Bar] = []
    price = open_px
    for idx in range(days):
        flow = (
            flow_by_day_index(idx, sym_index)
            if _takes_two(flow_by_day_index)
            else (
                flow_by_day_index(idx)
                if callable(flow_by_day_index)
                else flow_by_day_index
            )
        )
        move = 0.0
        if move_by_day_index is not None:
            move = (
                move_by_day_index(idx, sym_index)
                if _takes_two(move_by_day_index)
                else (
                    move_by_day_index(idx)
                    if callable(move_by_day_index)
                    else move_by_day_index
                )
            )
        chunk = block_bars(
            symbol=symbol,
            day_start_ns=day_midnight(idx),
            flow_f=flow,
            open_px=price,
            move_fraction=move,
            **kwargs,
        )
        out.extend(chunk)
        price = chunk[-1].close
    return out


def _takes_two(fn) -> bool:
    """True when ``fn`` accepts ``(day_index, symbol_index)``."""
    import inspect

    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):  # pragma: no cover - exotic callables
        return False
    positional = [
        p
        for p in signature.parameters.values()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    required = [p for p in positional if p.default is p.empty]
    return len(positional) >= 2 and len(required) <= 2


def make_panel(
    *,
    symbols=SYMBOLS,
    days: int = 3,
    flow_pattern=None,
    move_pattern=None,
    **kwargs,
) -> dict[str, list[M01Bar]]:
    if flow_pattern is None:

        def flow_pattern(_i: int, s: int = 0) -> float:  # pragma: no cover
            return 0.35 + 0.03 * s  # cross-sectional dispersion, non-degenerate

    return {
        str(sym): multi_day_bars(
            symbol=str(sym),
            days=days,
            flow_by_day_index=lambda i, s=sym_index: flow_pattern(i, s),
            move_by_day_index=move_pattern,
            sym_index=sym_index,
            **kwargs,
        )
        for sym_index, sym in enumerate(symbols)
    }


def write_catalog(root: Path, panel: dict[str, list[M01Bar]]) -> Path:
    """Write bars into the real Nautilus layout under ``root``."""
    for sym, bars in panel.items():
        directory = (
            Path(root)
            / "data"
            / "binance_bar"
            / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        )
        write_bars_table(directory / "part-0.parquet", bars)
    return Path(root)


def write_bars_table(path: Path, bars: list[M01Bar]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "open": pa.array([_fixed16(b.open) for b in bars], pa.binary(16)),
                "high": pa.array([_fixed16(b.high) for b in bars], pa.binary(16)),
                "low": pa.array([_fixed16(b.low) for b in bars], pa.binary(16)),
                "close": pa.array([_fixed16(b.close) for b in bars], pa.binary(16)),
                "volume": pa.array([_fixed16(b.volume) for b in bars], pa.binary(16)),
                "quote_volume": pa.array([f"{b.quote_volume:.5f}" for b in bars]),
                "count": pa.array([b.count for b in bars], pa.uint64()),
                "taker_buy_base_volume": pa.array(["0.000"] * len(bars)),
                "taker_buy_quote_volume": pa.array(
                    [f"{b.taker_buy_quote_volume:.5f}" for b in bars]
                ),
                "ts_event": pa.array([b.ts_event_ns for b in bars], pa.uint64()),
                "ts_init": pa.array([b.ts_init_ns for b in bars], pa.uint64()),
            }
        ),
        path,
    )


def features_for(panel, day_ns: int, **kwargs):
    return {
        sym: m01.symbol_day_feature(bars, sym, day_ns, **kwargs)
        for sym, bars in panel.items()
    }


def weights_map(book) -> dict[str, float]:
    return {sym: float(w) for sym, w in book["weights"]}


def weights_map_row(row) -> dict[str, float]:
    return {sym: float(w) for sym, w in row["weights"]}


def rewrite_share(panel, symbol: str, share: float) -> dict[str, list[M01Bar]]:
    out = {sym: list(bars) for sym, bars in panel.items()}
    out[symbol] = [rescale_taker(bar, share) for bar in out[symbol]]
    return out


@pytest.fixture(name="cohort_catalog")
def fixture_cohort_catalog(tmp_path):
    """Real-layout tree carrying exactly the TEN frozen universe symbols."""
    panel = make_panel(days=3, flow_pattern=lambda i, s: 0.3 + 0.03 * s)
    renamed = {
        m01.FROZEN_TRADING_COHORT[idx]: bars for idx, (_, bars) in enumerate(panel.items())
    }
    return write_catalog(tmp_path / "catalog", renamed)


# --------------------------------------------------------------------------- #
# Calendar / clock primitives
# --------------------------------------------------------------------------- #
def test_decision_days_exclude_window_start_and_count_365():
    days = m01.decision_days(
        window_start_iso="2025-08-21T00:00:00Z",
        window_end_iso="2026-08-21T00:00:00Z",
    )
    assert len(days) == 365
    assert days[0] == day_from_iso("2025-08-22T00:00:00Z")
    assert days[-1] == day_from_iso("2026-08-21T00:00:00Z")


def test_decision_days_floor_and_ceiling_partial_edges_per_contract_window_rule():
    days = m01.decision_days(
        window_start_iso="2025-08-21T14:30:00Z",  # measured A8 variant
        window_end_iso="2025-08-24T13:00:00Z",
    )
    assert days == [
        day_from_iso(stamp)
        for stamp in (
            "2025-08-22T00:00:00Z",
            "2025-08-23T00:00:00Z",
            "2025-08-24T00:00:00Z",
        )
    ]


def test_decision_days_need_at_least_two_boundaries():
    with pytest.raises(m01.SpecViolation):
        m01.decision_days(
            window_start_iso="2025-08-22T01:00:00Z",
            window_end_iso="2025-08-22T20:00:00Z",
        )


def test_block_window_is_exclusive_low_inclusive_high():
    d = day_from_iso("2025-09-03T00:00:00Z")
    lo, hi = m01.block_window_ns(d)
    assert (lo, hi) == (d - DAY, d)
    bars = block_bars(symbol="XUSDT", day_start_ns=d - DAY, flow_f=0.5, n_bars=96)
    assert len([b for b in bars if lo < b.ts_event_ns <= hi]) == 96
    # the NEXT block's bars fall outside by close stamp, never shift
    nxt = block_bars(symbol="XUSDT", day_start_ns=d, flow_f=0.5, n_bars=96)
    assert not [b for b in nxt if lo < b.ts_event_ns <= hi]
    with pytest.raises(m01.SpecViolation):
        m01.block_window_ns(d + STEP)


# --------------------------------------------------------------------------- #
# Catalog reader on a REAL-layout parquet tree (synthesised locally)
# --------------------------------------------------------------------------- #
def test_read_bars_decodes_real_layout_sorts_and_carries_flow_fields(tmp_path):
    panel = make_panel(symbols=("SOLOUSDT",), days=2, flow_pattern=lambda i, s: 0.75)
    root = write_catalog(tmp_path, panel)
    bars = m01.read_bars_15m(root, "SOLOUSDT", iso(day_midnight(0)), iso(day_midnight(2)))
    stamps = [b.ts_event_ns for b in bars]
    assert stamps == sorted(stamps)
    assert len(bars) == 192
    first = bars[0]
    assert math.isfinite(first.open) and abs(first.open - 100.0) < 1e-6
    assert first.count == 11
    assert first.taker_buy_quote_volume == pytest.approx(0.75 * first.quote_volume, rel=1e-6)
    assert first.ts_init_ns == first.ts_event_ns


def test_read_bars_rejects_duplicate_close_stamp_fail_closed(tmp_path):
    panel = make_panel(symbols=("DUPLUSDT",), days=1)
    root = write_catalog(tmp_path, panel)
    part_dir = (
        root / "data" / "binance_bar" / "DUPLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    pq.write_table(pq.read_table(part_dir / "part-0.parquet"), part_dir / "part-1.parquet")
    with pytest.raises(m01.DataIntegrityError, match="duplicate close stamp"):
        m01.read_bars_15m(root, "DUPLUSDT", iso(BASE_DAY), iso(BASE_DAY + DAY))


def test_read_bars_clips_out_of_window_close_stamps(tmp_path):
    panel = make_panel(symbols=("CLIPUSDT",), days=2)
    root = write_catalog(tmp_path, panel)
    bars = m01.read_bars_15m(
        root, "CLIPUSDT", iso(day_midnight(1)), iso(day_midnight(2))
    )
    assert len(bars) == 96
    assert bars[0].ts_event_ns >= day_midnight(1)


def test_read_bars_missing_directory_fails_closed(tmp_path):
    with pytest.raises(m01.CatalogUnavailable):
        m01.read_bars_15m(tmp_path, "GHOSTUSDT", iso(BASE_DAY), iso(BASE_DAY + DAY))


def test_load_block_universe_pads_one_warmup_day_before_window_edge(tmp_path):
    panel = make_panel(symbols=("WARMUSDT",), days=3)
    root = write_catalog(tmp_path, panel)
    loaded = m01.load_block_universe(
        root,
        ["WARMUSDT"],
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    bars = loaded["WARMUSDT"]
    assert bars[0].ts_event_ns < day_midnight(1)
    assert len(bars) == 3 * m01.BARS_PER_BLOCK


# --------------------------------------------------------------------------- #
# Feature construction + eligibility ladder
# --------------------------------------------------------------------------- #
def test_feature_aggregates_hand_computed_over_ninety_six_bars():
    day_start = day_midnight(0)
    bars = block_bars(
        symbol="HANDUSDT",
        day_start_ns=day_start,
        flow_f=0.75,
        quote_volume=96_000.0,
        count=4,
        open_px=200.0,
    )
    feat = m01.symbol_day_feature(bars, "HANDUSDT", day_start + DAY)
    total_q = sum(b.quote_volume for b in bars)
    total_t = sum(b.taker_buy_quote_volume for b in bars)
    assert feat.n_bars == 96 and feat.eligible and feat.ineligible_reason is None
    assert feat.quote_volume == pytest.approx(total_q)
    assert feat.taker_buy_quote_volume == pytest.approx(total_t)
    assert feat.imbalance_f == pytest.approx(total_t / total_q)
    assert feat.imbalance_f == pytest.approx(0.75, rel=1e-9)
    assert feat.imbalance_a == pytest.approx(2 * 0.75 - 1.0, rel=1e-9)
    assert feat.block_open == pytest.approx(200.0)
    assert feat.block_close == pytest.approx(200.0, rel=1e-6)  # move_fraction = 0
    assert feat.traded_value_proxy == pytest.approx(sum(b.close * b.volume for b in bars))
    assert feat.range_fraction == pytest.approx(
        sum((b.high - b.low) / b.close for b in bars)
    )


def test_ineligible_when_block_size_is_not_ninety_six():
    day_start = day_midnight(0)
    bars = block_bars(symbol="SHORTUSDT", day_start_ns=day_start, flow_f=0.5)[:95]
    feat = m01.symbol_day_feature(bars, "SHORTUSDT", day_start + DAY)
    assert not feat.eligible and feat.n_bars == 95
    assert feat.ineligible_reason == m01.INELIGIBLE_BLOCK_SIZE


def test_ineligible_on_nonpositive_block_quote_volume():
    day_start = day_midnight(0)
    bars = [
        M01Bar(
            ts_event_ns=day_start + (i + 1) * STEP - CLOSE_SHAVE_NS,
            ts_init_ns=day_start + (i + 1) * STEP - CLOSE_SHAVE_NS,
            open=10.0,
            high=10.0,
            low=10.0,
            close=10.0,
            volume=0.0,
            quote_volume=0.0,
            count=0,
            taker_buy_quote_volume=0.0,
        )
        for i in range(96)
    ]
    feat = m01.symbol_day_feature(bars, "ZEROUSDT", day_start + DAY)
    assert feat.ineligible_reason == m01.INELIGIBLE_NONPOSITIVE_QUOTE_VOLUME


def test_ineligible_when_taker_share_exceeds_total():
    day_start = day_midnight(0)
    bars = [
        rescale_taker(b, 1.25)
        for b in block_bars(symbol="OORUSDT", day_start_ns=day_start, flow_f=0.5)
    ]
    feat = m01.symbol_day_feature(bars, "OORUSDT", day_start + DAY)
    assert feat.imbalance_f > 1.0
    assert feat.ineligible_reason == m01.INELIGIBLE_FLOW_RATIO_OUT_OF_RANGE


def test_neighbour_arm_marks_symbol_ineligible_without_usable_sigma():
    day_start = day_midnight(0)
    bars = block_bars(symbol="SIGREQUSDT", day_start_ns=day_start, flow_f=0.5)
    ok = m01.symbol_day_feature(
        bars, "SIGREQUSDT", day_start + DAY, prewindow_sigma=0.02, require_prewindow_sigma=True
    )
    bad = m01.symbol_day_feature(
        bars, "SIGREQUSDT", day_start + DAY, prewindow_sigma=None, require_prewindow_sigma=True
    )
    assert ok.eligible is True
    assert bad.ineligible_reason == m01.INELIGIBLE_PREWINDOW_SIGMA_UNUSABLE
    assert not bad.eligible


def test_assert_signal_pit_flags_any_future_close_stamp():
    day_start = day_midnight(0)
    good = block_bars(symbol="PITUSDT", day_start_ns=day_start, flow_f=0.5)
    m01.assert_signal_pit(good, decision_ns=day_start + DAY, context="ok")
    leaky = good[:-1] + [
        M01Bar(
            ts_event_ns=day_start + DAY + STEP,
            ts_init_ns=day_start + DAY + STEP,
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=1.0,
            quote_volume=1.0,
            count=1,
            taker_buy_quote_volume=1.0,
        )
    ]
    with pytest.raises(m01.DataIntegrityError, match="lookahead"):
        m01.assert_signal_pit(leaky, decision_ns=day_start + DAY, context="leak")


# --------------------------------------------------------------------------- #
# Weight algebra
# --------------------------------------------------------------------------- #
MILD_RAW = {f"L{i}": v for i, v in enumerate(
    [0.10, 0.07, 0.04, 0.02, -0.02, -0.05, -0.08, -0.08]  # sums to exactly zero
)}
EXTREME_RAW = {f"C{i}": v for i, v in enumerate(
    [12.0, 3.0, 2.0, 1.0, -1.0, -1.0, -2.0, -2.5]
)}


def test_emit_targets_hits_unit_gross_within_tolerance_and_respects_cap():
    targets, diag = m01.emit_targets(EXTREME_RAW)
    gross = sum(abs(w) for _, w in targets)
    assert gross == pytest.approx(1.0, abs=1e-12)
    assert diag["gross_residual"] < 1e-12
    for _, w in targets:
        assert abs(w) <= m01.CAP + 1e-12
    assert diag["lambda"] > 0.0
    assert [sym for sym, _ in targets] == sorted(EXTREME_RAW)


def test_dollar_neutrality_exact_when_no_clip_binds():
    targets, diag = m01.emit_targets(MILD_RAW)
    lam = diag["lambda"]
    assert all(abs(w) < m01.CAP - 1e-6 for _, w in targets)
    assert diag["clip_bound_active"] is False
    assert lam == pytest.approx(1.0 / sum(abs(v) for v in MILD_RAW.values()), rel=1e-6)
    assert diag["net_exposure"] == pytest.approx(0.0, abs=1e-12)


def test_clipped_extremes_leave_reported_nonzero_net_exposure():
    targets, diag = m01.emit_targets(EXTREME_RAW)
    clipped = [(s, w) for s, w in targets if abs(w) >= m01.CAP - 1e-12]
    assert clipped, "extreme dispersion must bind the CAP on at least one leg"
    reported = sum(w for _, w in targets)
    assert diag["net_exposure"] == pytest.approx(reported, abs=1e-9)
    assert abs(diag["net_exposure"]) <= m01.CAP + 1e-12


def test_solve_lambda_rejects_degenerate_books_and_infeasible_gross():
    with pytest.raises(m01.BookInfeasibleError):
        m01.solve_lambda({k: 0.0 for k in "abcdefgh"}, cap=m01.CAP, gross=m01.GROSS_TARGET)
    with pytest.raises(m01.BookInfeasibleError):
        m01.solve_lambda({"a": 1.0, "b": -1.0}, cap=m01.CAP, gross=m01.GROSS_TARGET)
    with pytest.raises(m01.SpecViolation):
        m01.solve_lambda({"a": 1.0}, cap=-1.0, gross=1.0)
    with pytest.raises(m01.SpecViolation):
        m01.solve_lambda({"a": 1.0}, cap=0.3, gross=0.0)


def test_cross_sectional_z_zero_mean_and_constant_vector_handling():
    z = m01.cross_sectional_z({k: float(v) for k, v in zip("abcdefgh", range(8))})
    assert sum(z.values()) == pytest.approx(0.0, abs=1e-12)
    assert m01.cross_sectional_z({k: 0.42 for k in "abcdefgh"}) == {k: 0.0 for k in "abcdefgh"}
    assert m01.cross_sectional_z({"only": 3.0}) == {"only": 0.0}


def test_book_below_min_eligible_skips_and_reports_reason():
    day_start = day_midnight(0)
    panel = make_panel(days=1, flow_pattern=lambda i, s: 0.2 + 0.03 * s)
    feats = features_for(panel, day_start + DAY)
    seven = dict(list(feats.items())[:7])
    book = m01.compute_targets(features=seven)
    assert book["status"] == m01.STATUS_SKIP_BELOW_MIN_ELIGIBLE
    assert book["carried_forward"] is True
    assert book["weights"] == [] and book["longs"] == [] and book["shorts"] == []


def test_compute_targets_payload_shape_is_runner_compatible():
    day_start = day_midnight(0)
    panel = make_panel(days=1, flow_pattern=lambda i, s: 0.2 + 0.03 * s)
    book = m01.compute_targets(features=features_for(panel, day_start + DAY))
    for key in ("status", "longs", "shorts", "weights", "diagnostics", "n_eligible"):
        assert key in book
    assert book["status"] == "OK" and book["n_eligible"] == 10
    longs = {s for s, _ in book["longs"]}
    shorts = {s for s, _ in book["shorts"]}
    assert longs and shorts and not (longs & shorts)
    assert longs | shorts == set(weights_map(book))


def test_anchor_sign_longs_heaviest_aggressive_sellers():
    day_start = day_midnight(0)

    def pattern(_i: int, s: int) -> float:
        return 0.85 if s < 5 else 0.15  # first five sold aggressively

    panel = make_panel(days=1, flow_pattern=pattern)
    wm = weights_map(m01.compute_targets(features=features_for(panel, day_start + DAY)))
    ranked = sorted(SYMBOLS, key=lambda s: wm[s])
    # Contrarian sign: aggressive BUYERS carry the most NEGATIVE weight,
    # aggressive SELLERS the most positive.
    assert set(ranked[:5]) == set(SYMBOLS[:5])
    assert set(ranked[5:]) == set(SYMBOLS[5:])
    assert wm[SYMBOLS[0]] == min(wm.values())
    assert wm[SYMBOLS[9]] == max(wm.values())


def test_reverse_flag_flips_every_weight_sign_without_changing_bounds():
    day_start = day_midnight(0)
    panel = make_panel(days=1, flow_pattern=lambda i, s: 0.2 + 0.03 * s)
    feats = features_for(panel, day_start + DAY)
    plain = weights_map(m01.compute_targets(features=dict(feats)))
    flipped = weights_map(m01.compute_targets(features=dict(feats), reverse=True))
    assert plain.keys() == flipped.keys()
    for sym, weight in plain.items():
        assert flipped[sym] == pytest.approx(-weight, abs=1e-12)


def test_determinism_identical_inputs_identical_hashes():
    pattern_a = lambda i, s: 0.25 + 0.04 * ((s + i) % 5)  # noqa: E731
    panel_a = make_panel(days=2, flow_pattern=pattern_a)
    panel_b = make_panel(days=2, flow_pattern=lambda i, s: 0.25 + 0.04 * ((s + i) % 5))
    sched_a = m01.build_rebalance_schedule(
        bars_by_symbol=panel_a,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    sched_b = m01.build_rebalance_schedule(
        bars_by_symbol=panel_b,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    assert sched_a["schedule_sha256"] == sched_b["schedule_sha256"]
    feats = features_for(panel_a, day_midnight(2))
    assert m01.payload_sha256(feats) == m01.payload_sha256(dict(reversed(list(feats.items()))))
    book_one = m01.compute_targets(features=feats)
    book_two = m01.compute_targets(
        features={sym: m01.symbol_day_feature(panel_b[sym], sym, day_midnight(2)) for sym in panel_b}
    )
    assert m01.payload_sha256(book_one["weights"]) == m01.payload_sha256(book_two["weights"])


# --------------------------------------------------------------------------- #
# PIT guarantees
# --------------------------------------------------------------------------- #
def test_signal_hash_invariant_to_post_cutoff_perturbation():
    base = make_panel(days=3, flow_pattern=lambda i, s: 0.2 + 0.05 * (s % 4))
    decision = day_midnight(2)
    tampered = {sym: list(bars) for sym, bars in base.items()}
    for sym in SYMBOLS[:3]:
        last = tampered[sym][-1]  # belongs to the day AFTER the decision instant
        tampered[sym][-1] = M01Bar(
            ts_event_ns=last.ts_event_ns,
            ts_init_ns=last.ts_init_ns,
            open=last.open,
            high=last.high * 1.99,
            low=last.low * 0.01,
            close=last.close * 3.0,
            volume=last.volume * 50.0,
            quote_volume=last.quote_volume * 999.0,
            count=last.count + 1000,
            taker_buy_quote_volume=last.taker_buy_quote_volume * 99.0,
        )
    base_feats = features_for(base, decision)
    pert_feats = features_for(tampered, decision)
    assert m01.payload_sha256(base_feats) == m01.payload_sha256(pert_feats)
    assert m01.payload_sha256(
        m01.compute_targets(features=base_feats)["signals"]["raw"]
    ) == m01.payload_sha256(m01.compute_targets(features=pert_feats)["signals"]["raw"])
    sched_base = m01.build_rebalance_schedule(
        bars_by_symbol=base,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    sched_pert = m01.build_rebalance_schedule(
        bars_by_symbol=tampered,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    assert sched_base["rows"][0]["features_sha256"] == sched_pert["rows"][0]["features_sha256"]


def test_perturbing_the_decision_blocks_own_last_bar_does_move_the_signal():
    """Guardrail for the invariance test above: the final bar of the block closes
    AT the decision instant and therefore IS visible to the signal."""
    base = make_panel(days=1, flow_pattern=lambda i, s: 0.5)
    shifted = {sym: list(bars) for sym, bars in base.items()}
    victim = SYMBOLS[0]
    last = shifted[victim][-1]
    shifted[victim][-1] = rescale_taker(last, 0.95)  # same close stamp, new flow
    decision = day_midnight(1)
    base_imb = m01.compute_targets(features=features_for(base, decision))["signals"]["imbalances"]
    new_imb = m01.compute_targets(features=features_for(shifted, decision))["signals"]["imbalances"]
    assert base_imb[victim] != new_imb[victim]


def test_every_contributing_bar_closed_at_or_before_decision_instant():
    panel = make_panel(days=2, flow_pattern=lambda i, s: 0.4)
    decision = day_midnight(2)
    for sym, bars in panel.items():
        block = [b for b in bars if decision - DAY < b.ts_event_ns <= decision]
        assert len(block) == 96
        assert max(b.ts_event_ns for b in block) <= decision
        m01.assert_signal_pit(block, decision_ns=decision, context=sym)
        assert m01.symbol_day_feature(bars, sym, decision).eligible


# --------------------------------------------------------------------------- #
# Fill timing
# --------------------------------------------------------------------------- #
def test_fill_event_is_open_of_bar_covering_boundary():
    panel = make_panel(symbols=("FILLUSDT",), days=2, flow_pattern=lambda i, s: 0.5)
    bars = panel["FILLUSDT"]
    boundary = day_midnight(1)
    event = m01.resolve_fill_event(bars, "FILLUSDT", decision_ns=boundary)
    assert event is not None and event.event_offset == 0
    assert event.fill_open_ns <= boundary < event.fill_bar_close_ns
    chosen = [b for b in bars if b.ts_event_ns == event.fill_bar_close_ns][0]
    assert event.price == chosen.open
    assert event.fill_open_ns == m01.bar_open_ns(chosen)


def test_event_delay_walks_exactly_that_many_allowed_events():
    panel = make_panel(symbols=("DLYUSDT",), days=2, flow_pattern=lambda i, s: 0.5)
    bars = panel["DLYUSDT"]
    boundary = day_midnight(1)
    zero = m01.resolve_fill_event(bars, "DLYUSDT", decision_ns=boundary)
    one = m01.resolve_fill_event(bars, "DLYUSDT", decision_ns=boundary, event_delay_events=1)
    two = m01.resolve_fill_event(bars, "DLYUSDT", decision_ns=boundary, event_delay_events=2)
    assert one.fill_bar_close_ns == zero.fill_bar_close_ns + STEP
    assert two.fill_bar_close_ns == zero.fill_bar_close_ns + 2 * STEP
    assert (one.event_offset, two.event_offset) == (1, 2)
    with pytest.raises(m01.SpecViolation):
        m01.resolve_fill_event(bars, "DLYUSDT", decision_ns=boundary, event_delay_events=-1)


def test_missing_opening_slot_yields_no_event_never_a_substitute():
    boundary = day_midnight(1)
    bars = block_bars(
        symbol="HOLEUSDT",
        day_start_ns=boundary + 2 * STEP,
        flow_f=0.5,
        n_bars=94,
    )
    assert m01.resolve_fill_event(bars, "HOLEUSDT", decision_ns=boundary) is None
    later = m01.resolve_fill_event(
        bars, "HOLEUSDT", decision_ns=boundary, event_delay_events=0
    )
    assert later is None  # delay never invents an event either


def test_schedule_opens_daily_and_force_flats_at_final_scored_boundary():
    # One EXTRA covered day guarantees the final-boundary fill event exists.
    panel = make_panel(days=5, flow_pattern=lambda i, s: 0.3 + 0.05 * (s % 3))
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(4)),
    )
    actions = [row["action"] for row in sched["rows"]]
    assert actions.count("OPEN_REBALANCE") == 2
    assert actions[-1] == m01.FORCE_FLAT_STATUS
    assert sched["rows"][-1]["decision_ns"] == day_midnight(4)
    assert sched["rows"][-1]["weights"] == []
    assert sched["final_weights"] == {}
    assert sched["opening_rebalances"] == 2 and sched["unfilled_symbols"] == []
    for row in sched["rows"]:
        assert row["fills"], "every leg must record its fill attempt"
        assert all(entry["status"] == "FILLED_NEXT_EVENT" for entry in row["fills"])
        assert all(entry["applied"] for entry in row["fills"])


def test_require_all_fills_skips_whole_rebalance_when_a_leg_has_no_event():
    panel = make_panel(days=4, flow_pattern=lambda i, s: 0.4 + 0.05 * (s % 2))
    panel = dict(panel)
    intact = multi_day_bars(symbol="HOLEUSDT", days=4, flow_by_day_index=lambda _i: 0.45)
    boundary = day_midnight(2)
    panel["HOLEUSDT"] = [
        bar for bar in intact if not (m01.bar_open_ns(bar) <= boundary < bar.ts_event_ns)
    ]  # eligible block at D2 survives; its OWN opening slot does not
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    skipped_rows = [
        row for row in sched["rows"] if row["reason_code"] == m01.STATUS_SKIP_REQUIRE_ALL_FILLS
    ]
    assert sched["skipped_rebalances"] == 1
    assert len(skipped_rows) == 1
    for row in sched["rows"]:
        assert not row["fills"] or not any(entry["applied"] for entry in row["fills"])
    assert "HOLEUSDT" in sched["unfilled_symbols"]
    assert sched["holding_spans"] == []  # nothing ever traded -> nothing accrued


def test_force_flat_missing_event_stays_explicitly_unfilled():
    panel = make_panel(days=3, flow_pattern=lambda i, s: 0.45 + 0.05 * (s % 3))
    panel = dict(panel)
    stuck_bars = multi_day_bars(
        symbol="STUCKUSDT", days=3, flow_by_day_index=lambda _i: 0.45
    )
    # Remove exactly the bar whose interval covers the D3 force-flat boundary;
    # the D2 open rebalance stays fully tradable for every leg.
    boundary_open = day_midnight(3)
    stuck_bars = [
        bar
        for bar in stuck_bars
        if not (m01.bar_open_ns(bar) <= boundary_open < bar.ts_event_ns)
    ]
    panel["STUCKUSDT"] = stuck_bars
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    flat_row = sched["rows"][-1]
    stuck = [entry for entry in flat_row["fills"] if entry["symbol"] == "STUCKUSDT"]
    assert stuck and stuck[0]["status"] == "NO_EVENT_AT_BOUNDARY"
    assert not stuck[0]["applied"]
    assert sched["rows"][0]["status"] == "OK"  # the D2 open did trade
    assert sched["holding_spans"], "an unflatten-able book must leave accrual spans"


def test_turnover_accounted_per_side_through_force_flat():
    panel = make_panel(days=4, flow_pattern=lambda i, s: 0.3 + 0.09 * ((i + s) % 2))
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(4)),
    )
    prior = weights_map_row(sched["rows"][-2])
    assert sched["rows"][-1]["turnover_one_side"] == pytest.approx(
        sum(abs(w) for w in prior.values()), abs=1e-12
    )


# --------------------------------------------------------------------------- #
# Cost primitives + stress plumbing
# --------------------------------------------------------------------------- #
def test_baseline_cost_rate_is_preregistered_five_bp_plus_one_adverse_tick():
    assert m01.TAKER_FEE_FLOOR_BPS == 5.0 and m01.ADVERSE_TICK_SLIP_FLOOR == 1
    rate = m01.fill_cost_rate(price=100.0, tick_size=0.01)
    assert rate == pytest.approx(5e-4 + 0.01 / 100.0)
    fee_only = m01.fill_cost_rate(
        price=100.0, tick_size=0.01, stress=m01.StressParams(tick_slip_ticks=0)
    )
    assert fee_only == pytest.approx(5e-4)


def test_fee_slippage_x1_5_cell_scales_the_fee_component_only():
    base = m01.fill_cost_rate(price=100.0, tick_size=0.01)
    stressed = m01.fill_cost_rate(
        price=100.0, tick_size=0.01, stress=m01.StressParams(fee_multiplier=1.5)
    )
    # Preregistration multiplies the taker FEE; the adverse tick stays additive.
    assert stressed == pytest.approx(1.5 * 5e-4 + 1 * 0.01 / 100.0)
    assert stressed > base and base == pytest.approx(5e-4 + 1 * 0.01 / 100.0)


def test_tick_slip_requires_positive_tick_size_fail_closed():
    with pytest.raises(m01.SpecViolation):
        m01.fill_cost_rate(price=100.0, tick_size=None, stress=m01.StressParams(tick_slip_ticks=2))
    with pytest.raises(m01.SpecViolation):
        m01.fill_cost_rate(price=100.0, tick_size=0.0)
    tripled = m01.fill_cost_rate(
        price=50.0, tick_size=0.01, stress=m01.StressParams(tick_slip_ticks=3)
    )
    assert tripled == pytest.approx(5e-4 + 3 * 0.01 / 50.0)


def test_rebalance_cost_sums_delta_times_rate_and_fails_closed_without_prices():
    cost = m01.rebalance_cost(
        {"A": 0.2, "B": -0.2},
        {"A": -0.2, "B": 0.2},
        prices={"A": 100.0, "B": 200.0},
        tick_sizes={"A": 0.01, "B": 0.05},
    )
    expected = 0.4 * (5e-4 + 0.01 / 100.0) + 0.4 * (5e-4 + 0.05 / 200.0)
    assert cost == pytest.approx(expected)
    with pytest.raises(m01.SpecViolation):
        m01.rebalance_cost({"A": 0.1}, {"A": 0.2}, prices={})


def test_drop_one_symbol_filter_and_fail_closed_edges():
    survivors = m01.apply_stress_filter(
        list(SYMBOLS), m01.StressParams(drop_symbols=("IOTAUSDT",))
    )
    assert survivors == sorted(set(SYMBOLS) - {"IOTAUSDT"})
    with pytest.raises(m01.SpecViolation):
        m01.apply_stress_filter(list(SYMBOLS), m01.StressParams(drop_symbols=("NOPEUSDT",)))
    with pytest.raises(m01.SpecViolation):
        m01.apply_stress_filter(list(SYMBOLS)[:3], m01.StressParams(drop_symbols=(SYMBOLS[0],)))


def test_drop_one_symbol_leaves_schedulable_cohort_minus_name():
    panel = make_panel(days=4, flow_pattern=lambda i, s: 0.3 + 0.04 * s)
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
        stress=m01.StressParams(drop_symbols=("IOTAUSDT",)),
    )
    assert "IOTAUSDT" not in sched["cohort"]
    assert sched["stress"]["drop_symbols"] == ["IOTAUSDT"]
    assert sched["skipped_rebalances"] == 0
    traded_rows = [row for row in sched["rows"] if row["action"] == "OPEN_REBALANCE"]
    assert all(len(row["fills"]) == 9 for row in traded_rows)


def test_chronological_folds_partition_purge_and_support_drop_one_fold():
    days = m01.decision_days(
        window_start_iso="2025-08-21T00:00:00Z",
        window_end_iso="2026-08-21T00:00:00Z",
    )
    folds = m01.chronological_folds(days, folds=3)
    assert [label for _, label, _ in folds] == ["F1", "F2", "F3"]
    members_flat = [d for _, _, members in folds for d in members]
    assert members_flat == sorted(members_flat)
    assert len(set(members_flat)) == len(set(days)) - 3  # one purge day per fold
    for (_, _, earlier), (_, _, later) in zip(folds, folds[1:]):
        assert max(earlier) < min(later)
    dropped = m01.chronological_folds(
        days, folds=3, stress=m01.StressParams(dropped_fold_index=1)
    )
    assert [label for _, label, _ in dropped] == ["F1", "F3"]
    with pytest.raises(m01.SpecViolation):
        m01.chronological_folds(days[:3], folds=3)


def test_plus_one_event_delay_cell_shifts_every_offset_and_hash():
    panel = make_panel(days=4, flow_pattern=lambda i, s: 0.4 + 0.04 * (s % 2))
    kwargs = dict(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    base = m01.build_rebalance_schedule(**kwargs)
    delayed = m01.build_rebalance_schedule(
        **kwargs, stress=m01.StressParams(event_delay_events=1)
    )
    filled_base = [
        entry
        for row in base["rows"]
        for entry in row["fills"]
        if entry["status"] == "FILLED_NEXT_EVENT"
    ]
    filled_delayed = [
        entry
        for row in delayed["rows"]
        for entry in row["fills"]
        if entry["status"] == "FILLED_NEXT_EVENT"
    ]
    assert {entry["event_offset"] for entry in filled_base} == {0}
    assert {entry["event_offset"] for entry in filled_delayed} == {1}
    assert base["schedule_sha256"] != delayed["schedule_sha256"]


def test_traded_notional_helper_counts_flats_and_sign_changes():
    assert m01.traded_notional({}, {"A": 0.25}) == pytest.approx(0.25)
    assert m01.traded_notional({"A": 0.25}, {}) == pytest.approx(0.25)
    assert m01.traded_notional({"A": 0.2}, {"A": -0.3}) == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# Negative controls, neighbour M01-N and condition-C2 strengthening
# --------------------------------------------------------------------------- #
def test_verbatim_quotations_survive_as_named_module_constants():
    assert m01.SELECTION_FREEZE_C2_VERBATIM.startswith("C2 negative control strengthened")
    assert "participation-INDEPENDENT wide-range days" in m01.SELECTION_FREEZE_C2_VERBATIM
    assert "plain contrarian weighting of price" in m01.A7N_M01_CONTROL_DEFECT_QUOTE_VERBATIM
    assert "all-long/all-short net-exposed book" in m01.A7N_M01_CONTROL_DEFECT_QUOTE_VERBATIM
    assert "strict-later-event fill clock fleet-wide" in (
        m01.A7N_M01_REQUIRED_BEFORE_FREEZE_QUOTE_VERBATIM
    )
    assert "cross-sectional day mean" in m01.SPEC_NEGATIVE_CONTROL_SUBSTITUTION_QUOTE_VERBATIM
    assert "OPEN of the 15-minute bar whose open timestamp equals" in m01.SPEC_FILL_CLOCK_QUOTE_VERBATIM


def test_control_and_neighbour_vocabularies_are_exact():
    assert m01.CONTROL_MODES == ("anchor", "a8_spec_daymean", "c2_price_contrarian_placebo")
    assert m01.NEIGHBOUR_MODES == ("cross_sectional_z", "prewindow_dispersion")
    with pytest.raises(m01.SpecViolation):
        m01.compute_day_signals({}, control_mode="momentum")
    with pytest.raises(m01.SpecViolation):
        m01.compute_day_signals({}, neighbour_mode="winsorised")


def test_a8_spec_daymean_control_reproduces_the_quoted_defect():
    """The frozen section-3.9 control assigns ONE common signed level to every
    eligible name, so the bisected book is NET EXPOSED -- precisely the defect
    quoted verbatim from the A7-N challenge and carried as a module constant."""
    day_start = day_midnight(0)
    def asym(_i: int, s: int) -> float:
        return 0.55 if s < 6 else 0.45  # six buyers, four sellers

    panel = make_panel(days=1, flow_pattern=asym)
    feats = features_for(panel, day_start + DAY)
    anchor = m01.compute_targets(features=dict(feats))
    control = m01.compute_targets(features=dict(feats), control_mode=m01.CONTROL_A8_SPEC_DAYMEAN)
    assert anchor["status"] == control["status"] == "OK"
    cw = weights_map(control)
    leg = round(m01.GROSS_TARGET / len(cw), m01.WEIGHT_ROUNDING_DECIMALS)
    assert set(cw.values()) == {leg}
    assert control["diagnostics"]["net_exposure"] == pytest.approx(1.0, abs=1e-9)
    assert weights_map(anchor) != cw
    day_mean = control["signals"]["day_mean"]
    assert day_mean == pytest.approx(sum(f.imbalance_a for f in feats.values()) / len(feats))
    balanced = m01.compute_targets(
        features=features_for(make_panel(days=1, flow_pattern=lambda i, s: 0.5), day_start + DAY),
        control_mode=m01.CONTROL_A8_SPEC_DAYMEAN,
    )
    assert balanced["status"] in (
        m01.STATUS_SKIP_INFEASIBLE_BOOK,
        m01.STATUS_SKIP_BELOW_MIN_ELIGIBLE,
    )
    assert balanced["carried_forward"] is True


def test_c2_price_placebo_is_blind_to_flow_but_sensitive_to_price():
    """Flow-only perturbation leaves the placebo byte-identical; a pure price
    path change moves it -- isolating 'flow vs plain contrarian price'."""
    day_start = day_midnight(0)

    def pattern(_i: int, s: int) -> float:
        return 0.70 if s < 5 else 0.30

    base = make_panel(days=1, flow_pattern=pattern, move_pattern=lambda _i: 0.0)
    flow_flipped = {
        sym: [rescale_taker(bar, 0.2 if idx < 5 else 0.8) for bar in bars]
        for idx, (sym, bars) in enumerate(base.items())
    }
    price_shifted = {
        sym: [
            _scale_prices(bar, (1.0 + 0.01 * (1 + idx)) ** (k / 96.0))
            for k, bar in enumerate(bars)
        ]
        for idx, (sym, bars) in enumerate(base.items())
    }

    base_feat = features_for(base, day_start + DAY)
    flow_feat = features_for(flow_flipped, day_start + DAY)
    price_feat = features_for(price_shifted, day_start + DAY)

    placebo = lambda f: m01.compute_targets(  # noqa: E731
        features=f, control_mode=m01.CONTROL_C2_PRICE_CONTRARIAN_PLACEBO
    )
    base_raw = m01.payload_sha256(placebo(base_feat)["signals"]["raw"])
    assert base_raw == m01.payload_sha256(placebo(flow_feat)["signals"]["raw"])
    assert base_raw != m01.payload_sha256(placebo(price_feat)["signals"]["raw"])
    assert placebo(base_feat)["signals"]["notes"] == ["c2_strengthened_price_contrarian_placebo"]


def _scale_prices(bar: M01Bar, scale: float) -> M01Bar:
    return M01Bar(
        ts_event_ns=bar.ts_event_ns,
        ts_init_ns=bar.ts_init_ns,
        open=bar.open * scale,
        high=bar.high * scale,
        low=bar.low * scale,
        close=bar.close * scale,
        volume=bar.volume / scale,
        quote_volume=bar.quote_volume,
        count=bar.count,
        taker_buy_quote_volume=bar.taker_buy_quote_volume,
    )


def test_c2_control_and_anchor_share_pipeline_bounds_but_diverge_in_books():
    day_start = day_midnight(0)
    panel = make_panel(
        days=1,
        flow_pattern=lambda _i, s: 0.70 - 0.05 * s,
        move_pattern=lambda _i, s=0: 0.002 * (s - 5),
    )
    feats = features_for(panel, day_start + DAY)
    anchor = m01.compute_targets(features=dict(feats))
    placebo = compute_targetsguard(dict(feats))
    aw, pw = weights_map(anchor), weights_map(placebo)
    assert any(abs(aw[s] - pw[s]) > 1e-9 for s in aw)
    for book in (anchor, placebo):
        assert book["status"] == "OK"
        assert book["diagnostics"]["gross_realised"] == pytest.approx(1.0, abs=1e-12)
        for _, weight in weights_map(book).items():
            assert abs(weight) <= m01.CAP + 1e-12
    del day_start


def compute_targetsguard(feats):
    """Local alias keeping the C2 arm call explicit in the assertion test."""
    return m01.compute_targets(features=feats, control_mode=m01.CONTROL_C2_PRICE_CONTRARIAN_PLACEBO)


def test_wide_range_flip_probe_detects_flip_and_records_split_rule():
    records = {d: {"range_fraction": float(r)} for d, r in zip(range(6), [1, 1, 2, 8, 9, 9])}
    pnl = {0: 1.0, 1: 1.0, 2: 0.5, 3: -0.8, 4: -1.2, 5: -0.9}
    probe = m01.wide_range_flip_probe(day_pnl=pnl, day_records=records)
    assert probe["split_rule"] == m01.STRATUM_SPLIT_RULE
    assert probe["probe"] == "wide_range_flip_capability"
    assert probe["sign_flip"] is True
    assert probe["strata"][0]["n_days"] == 3
    assert probe["strata"][1]["n_days"] == 3
    assert probe["strata"][0]["mean"] > 0.0 > probe["strata"][1]["mean"]
    calm = m01.wide_range_flip_probe(day_pnl={d: 0.1 for d in range(6)}, day_records=records)
    assert calm["sign_flip"] is False
    assert "post-hoc diagnostic only" in calm["diagnostic_note"]


def test_strata_probe_is_diagnostic_only_and_never_touches_targets():
    day_start = day_midnight(0)
    panel = make_panel(days=1, flow_pattern=lambda i, s: 0.3 + 0.03 * s)
    feats = features_for(panel, day_start + DAY)
    records = m01.daily_cross_section_records({int(day_start + DAY): feats})
    m01.split_days_by_participation(records, value_key="mean_range_fraction")
    m01.wide_range_flip_probe(
        day_pnl={int(d): 1.0 for d in records},
        day_records=records,
        value_key="mean_range_fraction",
    )
    probe_pnl = {int(d): float(idx) for idx, d in enumerate(sorted(records))}
    probe = m01.wide_range_flip_probe(
        day_pnl=probe_pnl, day_records=records, value_key="mean_range_fraction"
    )
    assert probe["probe"] == "wide_range_flip_capability"
    before = m01.payload_sha256(m01.compute_targets(features=dict(feats))["weights"])
    after = m01.payload_sha256(m01.compute_targets(features=dict(feats))["weights"])
    assert before == after


def test_daily_cross_section_records_summary_fields():
    day_start = day_midnight(0)
    panel = make_panel(days=1, flow_pattern=lambda i, s: 0.3 + 0.03 * s)
    records = m01.daily_cross_section_records({int(day_start + DAY): features_for(panel, day_start + DAY)})
    record = records[int(day_start + DAY)]
    assert record["n_eligible"] == 10.0
    assert record["mean_range_fraction"] > 0.0
    assert record["mean_abs_imbalance"] > 0.0
    assert record["mean_abs_block_move"] == pytest.approx(0.0, abs=1e-9)


def test_neighbour_m01_n_divides_each_imbalance_by_sigma_over_sqrt_96():
    day_start = day_midnight(0)
    panel = make_panel(days=1, flow_pattern=lambda _i, s: 0.5 + 0.04 * s)
    feats = features_for(panel, day_start + DAY)
    sigma = {sym: 0.02 for sym in SYMBOLS}
    anchor = m01.compute_targets(features=dict(feats))
    neighbour = m01.compute_targets(
        features=dict(feats),
        neighbour_mode=m01.NEIGHBOUR_PREWINDOW_DISPERSION,
        prewindow_sigma=sigma,
    )
    assert neighbour["signals"]["notes"] == ["m01_n_prewindow_flow_dispersion_denominator"]
    denom = {sym: sigma[sym] / math.sqrt(m01.BARS_PER_BLOCK) for sym in SYMBOLS}
    for sym, raw_value in neighbour["signals"]["raw"].items():
        expect = -(anchor["signals"]["imbalances"][sym] / denom[sym])
        assert raw_value == pytest.approx(expect, rel=1e-12)
    assert neighbour["diagnostics"]["gross_realised"] == pytest.approx(1.0, abs=1e-12)
    assert set(weights_map(neighbour)) == set(SYMBOLS)


def test_neighbour_arm_fails_closed_without_pinned_sigma():
    day_start = day_midnight(0)
    panel = make_panel(days=1, flow_pattern=lambda _i, s: 0.5 + 0.01 * s)
    feats = features_for(panel, day_start + DAY)
    with pytest.raises(m01.SpecViolation, match="pinned pre-window sigma"):
        m01.compute_targets(features=dict(feats), neighbour_mode=m01.NEIGHBOUR_PREWINDOW_DISPERSION)
    with pytest.raises(m01.SpecViolation):
        m01.compute_targets(
            features=dict(feats),
            neighbour_mode=m01.NEIGHBOUR_PREWINDOW_DISPERSION,
            prewindow_sigma={sym: None for sym in SYMBOLS},
        )


def test_driver_builds_neighbor_arm_with_auto_derived_sigma_table():
    panel = make_panel(days=32, flow_pattern=lambda i, s: 0.40 + 0.05 * ((s + i) % 2))
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(30)),
        window_end_iso=iso(day_midnight(32)),
        neighbour_mode=m01.NEIGHBOUR_PREWINDOW_DISPERSION,
        prewindow_end_ns=day_midnight(30),
    )
    traded = [row for row in sched["rows"] if row["action"] == "OPEN_REBALANCE"]
    assert traded and traded[0]["status"] == "OK"
    assert traded[0]["n_eligible"] == 10
    assert sched["neighbour_mode"] == m01.NEIGHBOUR_PREWINDOW_DISPERSION


def test_prewindow_sigma_math_slot_shortfall_and_hash_pin():
    edge = day_midnight(m01.PREWINDOW_DAYS)
    bars = multi_day_bars(
        symbol="SIGUSDT",
        days=m01.PREWINDOW_DAYS,
        flow_by_day_index=lambda _i: 0.5,
    )
    alternated = [
        rescale_taker(bar, 0.40 if k % 2 == 0 else 0.60) for k, bar in enumerate(bars)
    ]
    sigma = m01.prewindow_sigma_i(alternated, prewindow_end_ns=edge)
    vals = [
        2 * b.taker_buy_quote_volume / b.quote_volume - 1.0 for b in alternated
    ]
    mean = sum(vals) / len(vals)
    variance = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
    assert sigma == pytest.approx(math.sqrt(variance))
    pin = m01.prewindow_sigma_table({"SIGUSDT": alternated}, prewindow_end_ns=edge)
    assert pin["sha256"] == m01.payload_sha256(pin["sigma_i"])
    assert pin["sigma_i"]["SIGUSDT"] == pytest.approx(sigma)
    again = m01.prewindow_sigma_table({"SIGUSDT": alternated}, prewindow_end_ns=edge)
    assert again["sha256"] == pin["sha256"]
    truncated = alternated[:-5]
    assert m01.prewindow_sigma_i(truncated, prewindow_end_ns=edge) is None
    relaxed = m01.prewindow_sigma_i(
        truncated, prewindow_end_ns=edge, slots_expected=None
    )  # diagnostics-only relaxation still yields a number
    assert relaxed == pytest.approx(sigma)


# --------------------------------------------------------------------------- #
# Native funding accrual accounting hook
# --------------------------------------------------------------------------- #
SETTLE_BASE = day_midnight(1)


def test_funding_cashflows_long_pays_positive_rate_short_receives():
    holdings = [
        m01.HoldingSpan("LONGLEG", 0.25, SETTLE_BASE - DAY, SETTLE_BASE + DAY),
        m01.HoldingSpan("SHORTLEG", -0.10, SETTLE_BASE - DAY, SETTLE_BASE + DAY),
    ]
    settlements = [
        {"publish_ts_ns": SETTLE_BASE + 3_600_000_000_000, "value": 0.0001}
    ]
    flows = {flow.symbol: flow for flow in m01.funding_cashflows(holdings, settlements)}
    assert flows["LONGLEG"].cashflow_per_unit_capital == pytest.approx(-0.25 * 0.0001)
    assert flows["SHORTLEG"].cashflow_per_unit_capital == pytest.approx(+0.10 * 0.0001)
    assert flows["LONGLEG"].rate == pytest.approx(0.0001)
    assert flows["LONGLEG"].sign_convention == m01.FUNDING_SIGN_CONVENTION == (
        m01.FUNDING_SIGN_CONVENTION
    )
    assert m01.FUNDING_SIGN_CONVENTION == "LONG_PAYS_POSITIVE_RATE"


def test_funding_accrues_only_inside_half_open_span():
    settle = SETTLE_BASE + 60_000_000_000
    span = m01.HoldingSpan("LEG", 0.5, SETTLE_BASE, SETTLE_BASE + DAY)
    assert m01.funding_cashflows([span], [{"publish_ts_ns": SETTLE_BASE - 1, "value": 0.001}]) == []
    assert m01.funding_cashflows([span], [{"publish_ts_ns": SETTLE_BASE, "value": 0.001}]) == []
    inner = m01.funding_cashflows([span], [{"publish_ts_ns": settle, "value": 0.001}])
    assert len(inner) == 1 and inner[0].settle_ts_ns == settle
    at_end = m01.funding_cashflows([span], [{"publish_ts_ns": SETTLE_BASE + DAY, "value": 0.002}])
    assert at_end[0].settle_ts_ns == SETTLE_BASE + DAY  # inclusive upper edge
    zero_weight_never_accrues = m01.funding_cashflows(
        [m01.HoldingSpan("FLAT", 0.0, SETTLE_BASE, SETTLE_BASE + DAY)], [{"publish_ts_ns": settle, "value": 0.001}]
    )
    assert zero_weight_never_accrues == []
    del settle


def test_settlement_series_validation_sorts_and_rejects_duplicates():
    span = m01.HoldingSpan("LEG", 0.5, SETTLE_BASE, SETTLE_BASE + DAY)
    with pytest.raises(Exception):
        m01.funding_cashflows(
            [span],
            [
                {"publish_ts_ns": SETTLE_BASE + 1, "value": 0.0001},
                {"publish_ts_ns": SETTLE_BASE + 1, "value": 0.0002},
            ],
        )
    unsorted = m01.funding_cashflows(
        [span],
        [
            {"publish_ts_ns": SETTLE_BASE + 20, "value": 0.0002},
            {"publish_ts_ns": SETTLE_BASE + 10, "value": 0.0001},
        ],
    )
    assert [flow.rate for flow in unsorted] == [0.0001, 0.0002]
    tuples = m01.funding_cashflows(
        [span],
        [
            (SETTLE_BASE + 10, 0.0001),
            (SETTLE_BASE + 20, 0.0002),
        ],
    )
    assert len(tuples) == 2
    normalized = m01.normalize_settlements([(SETTLE_BASE + 5, 0.001)])
    assert normalized[0].publish_ts_ns == SETTLE_BASE + 5


def test_derive_holding_spans_follow_applied_fills_only():
    panel = make_panel(days=3, flow_pattern=lambda i, s: 0.35 + 0.05 * (s % 3))
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    spans = sched["holding_spans"]
    assert spans
    for span in spans:
        assert span["end_ns"] > span["start_ns"]
        assert abs(span["signed_weight"]) <= m01.CAP + 1e-12
        assert span["symbol"] in sched["cohort"]
    assert all(span["end_ns"] <= day_midnight(3) + STEP for span in spans)


def test_funding_hook_integration_hand_computed_single_settlement():
    panel = make_panel(days=3, flow_pattern=lambda _i, s: 0.5 + 0.05 * s)
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    spans = [
        m01.HoldingSpan(span["symbol"], span["signed_weight"], span["start_ns"], span["end_ns"])
        for span in sched["holding_spans"]
    ]
    settle_ts = day_midnight(2) + 8 * 3_600 * 1_000_000_000  # inside held span
    flows = m01.funding_cashflows(spans, [{"publish_ts_ns": settle_ts, "value": 0.0002}])
    manual = {
        -span.signed_weight * 0.0002
        for span in spans
        if span.start_ns < settle_ts <= span.end_ns
    }
    assert manual
    assert {round(flow.cashflow_per_unit_capital, 18) for flow in flows} == {
        round(value, 18) for value in manual
    }


# --------------------------------------------------------------------------- #
# End-to-end schedule integration (still no scoring)
# --------------------------------------------------------------------------- #
def test_full_schedule_structure_bounds_and_hashes():
    panel = make_panel(
        days=7,
        flow_pattern=lambda i, s: 0.35 + 0.07 * ((s + 2 * i) % 5),
        move_pattern=lambda i: 0.002 * ((-1) ** i),
    )
    sched = m01.build_rebalance_schedule(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(6)),
    )
    assert sched["family_id"] == m01.FAMILY_ID
    assert sched["cohort"] == sorted(SYMBOLS)
    opens = [row for row in sched["rows"] if row["action"] == "OPEN_REBALANCE"]
    assert len(opens) == 4
    for row in opens:
        weights = weights_map_row(row)
        assert set(weights) == set(SYMBOLS)
        assert sum(abs(w) for w in weights.values()) == pytest.approx(1.0, abs=1e-9)
        assert max(abs(w) for w in weights.values()) <= m01.CAP + 1e-12
        assert len(row["fills"]) == len(SYMBOLS)
        assert row["signal_sha256"] and row["features_sha256"]
    flat = sched["rows"][-1]
    assert flat["action"] == "FORCE_FLAT" and flat["decision_ns"] == day_midnight(6)
    assert flat["turnover_one_side"] == pytest.approx(
        sum(abs(w) for w in weights_map_row(opens[-1]).values()), abs=1e-9
    )
    assert sched["skipped_rebalances"] == 0 and sched["unfilled_symbols"] == []
    rebuild = m01.build_rebalance_schedule(
        bars_by_symbol=make_panel(
            days=7,
            flow_pattern=lambda i, s: 0.35 + 0.07 * ((s + 2 * i) % 5),
            move_pattern=lambda i: 0.002 * ((-1) ** i),
        ),
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(6)),
    )
    assert rebuild["schedule_sha256"] == sched["schedule_sha256"]


def test_three_arms_produce_three_distinct_schedules_over_same_clocks():
    panel = make_panel(days=4, flow_pattern=lambda i, s: 0.4 + 0.02 * s)
    kwargs = dict(
        bars_by_symbol=panel,
        window_start_iso=iso(day_midnight(1)),
        window_end_iso=iso(day_midnight(3)),
    )
    anchor = m01.build_rebalance_schedule(**kwargs)
    placebo = m01.build_rebalance_schedule(**kwargs, control_mode=m01.CONTROL_C2_PRICE_CONTRARIAN_PLACEBO)
    daymean = m01.build_rebalance_schedule(**kwargs, control_mode=m01.CONTROL_A8_SPEC_DAYMEAN)
    assert len({anchor["schedule_sha256"], placebo["schedule_sha256"], daymean["schedule_sha256"]}) == 3
    for sched in (anchor, placebo, daymean):
        assert sched["control_mode"] in m01.CONTROL_MODES
        decisions = [row["decision_ns"] for row in sched["rows"]]
        assert decisions == sorted(decisions)
        assert sched["rows"][-1]["action"] == "FORCE_FLAT"


# --------------------------------------------------------------------------- #
# C1 field-population verification against a synthetic real-layout tree
# --------------------------------------------------------------------------- #
def test_c1_verified_when_every_frozen_symbol_present(cohort_catalog):
    report = m01.verify_field_population(cohort_catalog)
    assert report["directories_present_count"] == len(m01.FROZEN_TRADING_COHORT)
    assert report["universe_symbols_missing_from_disk"] == []
    assert report["symbols_on_disk_outside_universe"] == []
    assert report["columns_present_everywhere"] is True
    assert report["errors"] == []
    assert report["verdict"] == "VERIFIED"
    assert set(report["verdict_by_field"].values()) == {"VERIFIED"}
    assert list(report["verdict_by_field"]) == list(m01.COLUMNS_REQUIRED)
    scored_scopes = [key for key in report["aggregate"] if key.startswith("scored_window")]
    assert scored_scopes
    for scope in report["aggregate"].values():
        assert scope["symbols_scanned"] == len(m01.FROZEN_TRADING_COHORT)
        assert scope["taker_gt_quote_rows"] == 0
        for field in m01.COLUMNS_REQUIRED:
            stat = scope["fields"][field]
            assert stat["rows"] > 0
            assert stat["non_null_share"] == 1.0
            assert stat["negative_count"] == 0
            assert stat["varies_flag"] is True


def test_c1_reports_missing_universe_symbols_and_extra_dirs(tmp_path):
    partial = make_panel(symbols=SYMBOLS[:3], days=1)
    renamed = {
        m01.FROZEN_TRADING_COHORT[idx]: bars for idx, (_, bars) in enumerate(partial.items())
    }
    extra = {"BTCUSDT": renamed[m01.FROZEN_TRADING_COHORT[0]]}
    root = write_catalog(tmp_path / "catalog", {**renamed, **extra})
    report = m01.verify_field_population(root)
    assert report["universe_symbols_missing_from_disk"] == list(m01.FROZEN_TRADING_COHORT)[3:]
    assert "BTCUSDT" in report["symbols_on_disk_outside_universe"]
    assert report["verdict"] == "FAIL_CLOSED"
    assert set(report["verdict_by_field"].values()) == {"FAIL_CLOSED"}


def test_c1_window_scope_filters_rows_by_close_stamp(cohort_catalog):
    lo = day_midnight(0)
    hi = day_midnight(2)  # midnight-aligned scope over ONE completed block per name
    report = m01.verify_field_population(
        cohort_catalog,
        window_start_iso=iso(lo),
        window_end_iso=iso(hi),
    )
    stat = report["per_symbol"][m01.FROZEN_TRADING_COHORT[0]]
    scoped_key = [key for key in stat["scopes"] if key.startswith("scored_window")][0]
    assert stat["scopes"][scoped_key]["rows_total"] == 2 * m01.BARS_PER_BLOCK
    assert stat["scopes"]["full_history_on_disk"]["rows_total"] == 3 * m01.BARS_PER_BLOCK
    assert report["aggregate"][scoped_key]["rows_total_scope"] == (
        2 * m01.BARS_PER_BLOCK * len(m01.FROZEN_TRADING_COHORT)
    )


def test_c1_scoped_seconds_truncation_is_reported_not_hidden(cohort_catalog):
    """ISO-second truncation of caller windows is a declared caveat (AMB-05):
    an edge clipped mid-second silently drops whole bars from a scope."""
    lo = day_midnight(0)
    sub_second_hi = day_midnight(1) - CLOSE_SHAVE_NS // 2
    report = m01.verify_field_population(
        cohort_catalog, window_start_iso=iso(lo), window_end_iso=iso(sub_second_hi)
    )
    stat = report["per_symbol"][m01.FROZEN_TRADING_COHORT[0]]
    scoped_key = [key for key in stat["scopes"] if key.startswith("scored_window")][0]
    assert stat["scopes"][scoped_key]["rows_total"] < m01.BARS_PER_BLOCK


def test_c1_fails_closed_when_required_column_absent(cohort_catalog):
    victim = (
        cohort_catalog
        / "data"
        / "binance_bar"
        / f"{m01.FROZEN_TRADING_COHORT[3]}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    part = victim / "part-0.parquet"
    table = pq.read_table(part)
    pq.write_table(table.drop_columns(["count"]), victim / "part-bad.parquet")
    part.unlink()
    report = m01.verify_field_population(cohort_catalog)
    assert report["columns_present_everywhere"] is False
    assert report["verdict"] == "FAIL_CLOSED"
    assert report["verdict_by_field"][m01.COUNT_COLUMN] == "FAIL_CLOSED"
    assert any("absent from parquet schema" in err for err in report["errors"])


def test_c1_fails_closed_on_degenerate_never_varying_field(cohort_catalog):
    victim = (
        cohort_catalog
        / "data"
        / "binance_bar"
        / f"{m01.FROZEN_TRADING_COHORT[5]}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    part = victim / "part-0.parquet"
    table = pq.read_table(part)
    constant = pa.table(
        {
            name: table.column(name)
            for name in table.column_names
            if name != "count"
        }
        | {"count": pa.array([1] * table.num_rows, pa.uint64())}
    )
    pq.write_table(constant, victim / "part-degenerate.parquet")
    part.unlink()
    report = m01.verify_field_population(cohort_catalog)
    assert report["verdict_by_field"][m01.COUNT_COLUMN] == "FAIL_CLOSED"
    assert report["verdict"] == "FAIL_CLOSED"
    stat = report["per_symbol"][m01.FROZEN_TRADING_COHORT[5]]["scopes"][
        "full_history_on_disk"
    ][m01.COUNT_COLUMN]
    assert stat["varies_flag"] is False
    assert stat["non_null_share"] == 1.0  # present yet degenerate => still closed


def test_c1_fails_closed_when_taker_exceeds_quote_volume(cohort_catalog):
    victim = (
        cohort_catalog
        / "data"
        / "binance_bar"
        / f"{m01.FROZEN_TRADING_COHORT[7]}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    part = victim / "part-0.parquet"
    table = pq.read_table(part)
    quotes = [float(value) for value in table.column("quote_volume").to_pylist()]
    inflated = pa.table(
        {
            name: table.column(name)
            for name in table.column_names
            if name != "taker_buy_quote_volume"
        }
        | {"taker_buy_quote_volume": pa.array([f"{q * 3:.5f}" for q in quotes])}
    )
    pq.write_table(inflated, victim / "part-inflated.parquet")
    part.unlink()
    report = m01.verify_field_population(cohort_catalog)
    scope = report["per_symbol"][m01.FROZEN_TRADING_COHORT[7]]["scopes"][
        "full_history_on_disk"
    ]
    assert scope["taker_gt_quote_rows"] == scope["rows_total"]
    assert report["verdict_by_field"][m01.TAKER_COLUMN] == "FAIL_CLOSED"
    assert report["verdict"] == "FAIL_CLOSED"
    assert report["aggregate"]["full_history_on_disk"]["taker_gt_quote_rows"] > 0


def test_c1_detects_null_like_values_inside_a_column(cohort_catalog):
    victim = (
        cohort_catalog
        / "data"
        / "binance_bar"
        / f"{m01.FROZEN_TRADING_COHORT[9]}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    part = victim / "part-0.parquet"
    table = pq.read_table(part)
    quotes = ["nan"] * table.num_rows  # unparsable floats read as null-like
    broken = pa.table(
        {
            name: table.column(name)
            for name in table.column_names
            if name != "taker_buy_quote_volume"
        }
        | {"taker_buy_quote_volume": pa.array(quotes)}
    )
    pq.write_table(broken, victim / "part-broken.parquet")
    part.unlink()
    report = m01.verify_field_population(cohort_catalog)
    stat = report["per_symbol"][m01.FROZEN_TRADING_COHORT[9]]["scopes"][
        "full_history_on_disk"
    ][m01.TAKER_COLUMN]
    assert stat["null_like_count"] == table.num_rows
    assert stat["non_null_share"] == 0.0
    assert report["verdict_by_field"][m01.TAKER_COLUMN] == "FAIL_CLOSED"


def test_c1_cli_main_writes_sorted_json_artifact(cohort_catalog, tmp_path, capsys):
    out = tmp_path / "c1.json"
    rc = m01.main(
        [
            "--catalog-root",
            str(cohort_catalog),
            "--out",
            str(out),
            "--verify-fields",
            "--scan-window-start",
            iso(day_midnight(0)),
            "--scan-window-end",
            iso(day_midnight(1)),
        ]
    )
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert '"artifact": "i1_c1_field_verification"' in text
    assert '"verdict": "VERIFIED"' in text
    stdout = capsys.readouterr().out
    assert '"verdict_by_field"' in stdout
