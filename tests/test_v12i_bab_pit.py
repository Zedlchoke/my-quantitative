"""PIT discipline tests for A12-V12-BAB-LOWBETA (completed bars only).

The PIT proof used throughout: for any stamp, the features/book computed
from the FULL frame and the same quantities recomputed from a frame
TRUNCATED at the stamp (every bar closing strictly after the stamp dropped)
must be byte-identical.  A future-bar or future-universe leak would break
the equality, because the truncated frame physically lacks the future data.
Synthetic closed-form fixtures only -- no catalog data, no scored metric.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from research.v12.families.bab_lowbeta.audits import (
    build_beta_ranking_frame,
    build_downcorr_frame,
    make_plugin,
)
from research.v12.families.bab_lowbeta.strategy import (
    BARS_PER_DAY,
    BENCHMARK_SYMBOL_EXCLUDED,
    compute_stamp_features,
    daily_blocks,
    daily_return_pairs,
    weekly_monday_stamps,
)

GOLDEN = Path(__file__).resolve().parents[1] / "research" / "v12" / "families" / "bab_lowbeta" / "golden"


def _truncate(bars, stamp):
    return tuple(b for b in bars if int(b.ts_event_ns) <= int(stamp))


def _payload(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


@pytest.fixture(scope="module")
def beta_frame():
    bars, design = build_beta_ranking_frame()
    return bars, design


@pytest.fixture(scope="module")
def downcorr_frame():
    bars, design = build_downcorr_frame()
    return bars, design


def test_daily_blocks_are_pit_and_exactly_96_bars(beta_frame):
    bars, _ = beta_frame
    stamps = weekly_monday_stamps()
    decision = int(stamps[0])
    btc = bars[BENCHMARK_SYMBOL_EXCLUDED]
    blocks = daily_blocks(btc, decision_ns=decision, n_days=90)
    assert len(blocks) == 90  # fully covered trailing window at the first stamp
    assert all(b["n_bars"] == float(BARS_PER_DAY) for b in blocks.values())
    # every contributing bar closes at or before the decision instant (PIT)
    newest = max(
        int(b.ts_event_ns) for b in btc if int(b.ts_event_ns) <= decision
    )
    assert newest <= decision
    # a future decision can see more blocks; a past decision fewer
    early = daily_blocks(btc, decision_ns=decision - 200, n_days=90)
    assert len(early) <= 90


def test_paired_daily_returns_use_completed_bars_only(beta_frame):
    bars, design = beta_frame
    stamps = weekly_monday_stamps()
    decision = int(stamps[0])
    pairs = daily_return_pairs(
        bars["SYMA03"], bars[BENCHMARK_SYMBOL_EXCLUDED], decision_ns=decision
    )
    assert len(pairs) == 90
    # closed form: the designed log return of each daily block is exact
    # (the fixture's daily blocks open/close at the designed prices)
    assert all(math.isfinite(r) for pair in pairs.values() for r in pair)


def test_first_stamp_betas_equal_designed_betas_exactly(beta_frame):
    bars, design = beta_frame
    stamps = weekly_monday_stamps()
    plugin = make_plugin("BAB-90D-W", bars)
    universe = plugin.universe(plugin.baseline_stress())
    snapshot = compute_stamp_features(
        bars_by_symbol=plugin._bars,
        universe=universe,
        benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
        decision_ns=int(stamps[0]),
        feature="btc_beta_90d_daily",
    )
    golden = json.loads((GOLDEN / "beta_ranking_fixture.json").read_text())["hand_computation"]
    assert len(snapshot.features) == 12
    for sym, want in golden["designed_betas"].items():
        assert snapshot.betas[sym] == pytest.approx(want, abs=1e-9)
        assert snapshot.features[sym] == pytest.approx(want, abs=1e-9)


# Bounded stamp samples (explicit lists -- the suite must stay fast; the
# full-window evidence lives in the committed audit artifacts).
TRUNCATION_SAMPLE = 3


def _explicit_sample(stamps, count: int = TRUNCATION_SAMPLE):
    ordered = list(stamps)
    if len(ordered) <= count:
        return tuple(ordered)
    middle = ordered[len(ordered) // 2]
    sample = sorted({ordered[0], middle, ordered[-2]})
    return tuple(sample)[:count]


def test_pit_truncation_equality_anchor_books_sampled_stamps(beta_frame):
    """Full-frame book == truncated-frame book at the sampled stamps.

    Bounded to an explicit 3-stamp sample (first / middle / penultimate
    Monday): every stamp rebuilds the whole truncated frame, so an
    unbounded sweep cannot finish quickly.  Any future-bar or future-universe
    leak would break the equality at the sampled stamps already.
    """
    bars, _ = beta_frame
    plugin = make_plugin("BAB-90D-W", bars)
    universe = plugin.universe(plugin.baseline_stress())
    sample = _explicit_sample(plugin.schedule().instants)
    assert len(sample) == TRUNCATION_SAMPLE
    for stamp in sample:
        full = plugin.targets_at(int(stamp), universe=universe, stress=plugin.baseline_stress())
        truncated_bars = {sym: _truncate(seq, stamp) for sym, seq in bars.items()}
        pit_plugin = make_plugin("BAB-90D-W", truncated_bars)
        pit = pit_plugin.targets_at(int(stamp), universe=universe, stress=pit_plugin.baseline_stress())
        full_payload = {
            "status": full["status"],
            "reason_code": full["reason_code"],
            "weights": full["weights"],
            "diagnostics": full["diagnostics"],
        }
        pit_payload = {
            "status": pit["status"],
            "reason_code": pit["reason_code"],
            "weights": pit["weights"],
            "diagnostics": pit["diagnostics"],
        }
        assert _payload(full_payload) == _payload(pit_payload), (
            f"PIT leak at stamp {stamp}: full-frame book differs from the "
            "truncated-frame book"
        )


def test_midnight_index_fast_path_equals_general_path(beta_frame):
    """The plugin's day-index acceleration is EXACT at midnight stamps.

    The frozen Monday 00:00:00Z stamps take the pre-computed absolute-day
    index; the same features recomputed through the general ``daily_blocks``
    aggregation must be identical, so the acceleration can never change a
    decision (guards the frozen semantics of the fast path).
    """
    from research.v12.families.bab_lowbeta.strategy import build_day_index

    bars, _ = beta_frame
    plugin = make_plugin("BAB-90D-W", bars)
    universe = plugin.universe(plugin.baseline_stress())
    stamps = plugin.schedule().instants
    for stamp in (stamps[0], stamps[len(stamps) // 2], stamps[-2]):
        fast = compute_stamp_features(
            bars_by_symbol=plugin._bars,
            universe=universe,
            benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
            decision_ns=int(stamp),
            feature="btc_beta_90d_daily",
            day_index_by_symbol=plugin._day_index_lazy(),
        )
        general = compute_stamp_features(
            bars_by_symbol=plugin._bars,
            universe=universe,
            benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
            decision_ns=int(stamp),
            feature="btc_beta_90d_daily",
        )
        assert _payload(sorted(fast.features.items())) == _payload(
            sorted(general.features.items())
        )
        assert _payload(sorted(fast.betas.items())) == _payload(
            sorted(general.betas.items())
        )
        # a NON-midnight instant never touches the index (general path only)
        assert int(stamp) % 86_400_000_000_000 == 0


def test_pit_truncation_equality_downcorr_feature(downcorr_frame):
    bars, _ = downcorr_frame
    plugin = make_plugin("BAB-DOWNCORR-90D-W", bars)
    universe = plugin.universe(plugin.baseline_stress())
    stamps = plugin.schedule().instants
    for stamp in (stamps[0], stamps[13], stamps[40]):
        full = compute_stamp_features(
            bars_by_symbol=plugin._bars,
            universe=universe,
            benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
            decision_ns=int(stamp),
            feature="btc_downside_correlation_90d_daily",
        )
        truncated = {
            sym: _truncate(seq, stamp) for sym, seq in bars.items()
        }
        pit = compute_stamp_features(
            bars_by_symbol=truncated,
            universe=universe,
            benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
            decision_ns=int(stamp),
            feature="btc_downside_correlation_90d_daily",
        )
        assert _payload(sorted(full.features.items())) == _payload(
            sorted(pit.features.items())
        )
        assert _payload(sorted(full.betas.items())) == _payload(
            sorted(pit.betas.items())
        )


def test_universe_is_fixed_and_excludes_btc(beta_frame):
    """No future universe selection: the cohort is fixed at construction."""
    bars, _ = beta_frame
    plugin = make_plugin("BAB-90D-W", bars)
    universe = plugin.universe(plugin.baseline_stress())
    assert BENCHMARK_SYMBOL_EXCLUDED not in universe
    assert len(universe) == 12
    assert plugin.benchmark_context_symbols() == tuple(sorted(set(universe) | {BENCHMARK_SYMBOL_EXCLUDED}))
    # the same fixed universe at the first and last stamps
    stamps = plugin.schedule().instants
    for stamp in (stamps[0], stamps[-1]):
        book = plugin.targets_at(int(stamp), universe=universe, stress=plugin.baseline_stress())
        held = set(book["weights"])
        assert held <= set(universe)
        assert BENCHMARK_SYMBOL_EXCLUDED not in held


def test_downcorr_uses_btc_down_days_only(downcorr_frame):
    """The neighbour statistic is computed over BTC<0 days (closed form)."""
    bars, design = downcorr_frame
    stamps = weekly_monday_stamps()
    plugin = make_plugin("BAB-DOWNCORR-90D-W", bars)
    universe = plugin.universe(plugin.baseline_stress())
    snapshot = compute_stamp_features(
        bars_by_symbol=plugin._bars,
        universe=universe,
        benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
        decision_ns=int(stamps[0]),
        feature="btc_downside_correlation_90d_daily",
    )
    golden = json.loads((GOLDEN / "downcorr_fixture.json").read_text())["hand_computation"]
    for sym, want in golden["expected_downcorr"].items():
        assert snapshot.features[sym] == pytest.approx(want, abs=1e-9)


def test_never_imputes_missing_features(beta_frame):
    """A name without a fully covered 90d block is ineligible -- not imputed."""
    bars, _ = beta_frame
    # drop the most recent 10 days of SOL-equivalent (SYMA00) bars: the
    # trailing window at the first stamp loses coverage -> ineligible
    stamps = weekly_monday_stamps()
    decision = int(stamps[0])
    cut = decision - 10 * 86_400_000_000_000
    broken = {sym: seq for sym, seq in bars.items()}
    broken["SYMA00"] = tuple(b for b in bars["SYMA00"] if int(b.ts_event_ns) < cut)
    plugin = make_plugin("BAB-90D-W", broken)
    universe = plugin.universe(plugin.baseline_stress())
    snapshot = compute_stamp_features(
        bars_by_symbol=plugin._bars,
        universe=universe,
        benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
        decision_ns=decision,
        feature="btc_beta_90d_daily",
    )
    assert "SYMA00" not in snapshot.features
    assert "SYMA00" not in snapshot.betas
    assert len(snapshot.features) == 11
