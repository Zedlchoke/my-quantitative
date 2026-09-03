"""PIT / no-leak fixtures for the A8-V11-ILLIQ-AMIHUD plugin.

Proves, on hermetic synthetic tapes:

* the target book at a stamp is invariant to ANY mutation of bars that close
  strictly AFTER that stamp (no lookahead);
* completed-bar boundary semantics: a bar closing exactly AT the stamp lands
  in the latest daily block, a bar closing one microsecond later is invisible;
* execution fills exactly one declared lag (24h) after the decision stamp on
  the covering bar's open, and stress walks exactly ``event_delay_events``
  further completed events;
* a symbol only becomes eligible once its listing history satisfies the
  frozen formation window (listing PIT);
* BTCUSDT is context-only: never tradeable, never in a book;
* the frozen folds force the book flat at each fold boundary.

The plugin is bar-width agnostic (blocks are derived from close stamps), so
the light tapes below use one bar per day; the fill clock test uses a 15m
grid where the declared lag is exact.
"""

import math
from dataclasses import dataclass

from research.adapter_v10.protocol import StressSpec
from research.v11.families.illiq_amihud import IlliqAmihudPlugin
from research.v11.families.illiq_amihud.strategy import (
    DAY_NS,
    amihud_feature,
    daily_blocks,
    weekly_monday_stamps,
)

MINUTE_NS = 60 * 1_000_000_000
BAR_NS = 15 * MINUTE_NS


@dataclass(frozen=True)
class Bar:
    ts_event_ns: int
    open: float
    close: float
    quote_volume: float


def _daily_frame(*, n_days: int, start_day: int, n_symbols: int = 12):
    """One bar per UTC day, closing 15m before the next midnight.

    Symbol day returns load on the shared BTC factor with a fixed positive
    beta plus small idiosyncratic noise, so the frozen beta hedge is well
    conditioned on the fixture.
    """
    btc_day_returns = [
        0.001 * math.sin(0.11 * day) + 0.0004 * math.cos(0.041 * day)
        for day in range(n_days)
    ]
    bars = {}
    for i in range(n_symbols):
        # betas mixed (not monotone in illiquidity) so the hedge tilt stays
        # well inside (0, 1) on the fixture
        beta = 1.0 + 0.1 * (((i * 7) % 5) - 2) / 2.0
        seq = []
        px = 100.0 + i
        for day in range(n_days):
            ts = (start_day + day) * DAY_NS + DAY_NS - BAR_NS
            ret = beta * btc_day_returns[day] + 0.0007 * math.sin(0.31 * day + 0.17 * i)
            nxt = px * (1.0 + ret)
            seq.append(
                Bar(
                    ts_event_ns=ts,
                    open=px,
                    close=nxt,
                    quote_volume=1_000_000.0 / (1.0 + i),
                )
            )
            px = nxt
        bars[f"SYM{i:02d}"] = tuple(seq)
    seq = []
    px = 50_000.0
    for day in range(n_days):
        ts = (start_day + day) * DAY_NS + DAY_NS - BAR_NS
        nxt = px * (1.0 + btc_day_returns[day])
        seq.append(Bar(ts_event_ns=ts, open=px, close=nxt, quote_volume=1e9))
        px = nxt
    bars["BTCUSDT"] = tuple(seq)
    return bars


def _intraday_frame(*, n_days: int, start_day: int, symbols=("SYM03", "BTCUSDT")):
    """A true 15m grid tape (for the declared-lag fill clock)."""
    bars = {}
    for name in symbols:
        i = int(name[3:5]) if name.startswith("SYM") else 0
        base = 100.0 + i if name.startswith("SYM") else 50_000.0
        vol = 1_000_000.0 / (1.0 + i) if name.startswith("SYM") else 1e9
        seq = []
        px = base
        for day in range(n_days):
            for slot in range(96):
                ts = (start_day + day) * DAY_NS + (slot + 1) * BAR_NS
                ret = 0.0004 * math.sin(0.7 * day + 0.05 * slot + i)
                nxt = px * (1.0 + ret)
                seq.append(Bar(ts_event_ns=ts, open=px, close=nxt, quote_volume=vol))
                px = nxt
        bars[name] = tuple(seq)
    return bars


def _plugin(bars, arm_id="ILLIQ-AMIHUD-28D-W"):
    return IlliqAmihudPlugin(
        bars_by_symbol=bars,
        arm_id=arm_id,
        tick_sizes={sym: 0.01 for sym in bars},
    )


def test_book_invariant_to_future_bar_mutations():
    """Mutating every bar that closes after a stamp cannot move its book."""
    stamps = weekly_monday_stamps()
    start_day = (stamps[0] - 120 * DAY_NS) // DAY_NS
    bars = _daily_frame(n_days=120 + 12 * 7 + 10, start_day=start_day)
    plugin = _plugin(bars)
    universe = plugin.universe(plugin.baseline_stress())
    stamp = plugin.schedule().instants[10]
    baseline = plugin.targets_at(
        stamp, universe=universe, stress=plugin.baseline_stress()
    )
    assert baseline["status"] == "OK" and baseline["weights"]
    mutated = {}
    for sym, seq in bars.items():
        mutated[sym] = tuple(
            Bar(
                ts_event_ns=bar.ts_event_ns,
                open=bar.open * 10.0 if bar.ts_event_ns > stamp else bar.open,
                close=bar.close * 10.0 if bar.ts_event_ns > stamp else bar.close,
                quote_volume=bar.quote_volume,
            )
            for bar in seq
        )
    mutated_plugin = _plugin(mutated)
    after = mutated_plugin.targets_at(
        stamp, universe=universe, stress=mutated_plugin.baseline_stress()
    )
    assert after["weights"] == baseline["weights"]
    assert after["status"] == baseline["status"]


def test_completed_bar_boundary_is_inclusive_at_the_stamp():
    """A bar closing exactly AT the stamp enters block k=1; a later one is invisible."""
    stamps = weekly_monday_stamps()
    decision = stamps[5]
    at_stamp = Bar(ts_event_ns=decision, open=100.0, close=101.0, quote_volume=1e6)
    one_ns_late = Bar(
        ts_event_ns=decision + 1, open=100.0, close=101.0, quote_volume=1e6
    )
    blocks = daily_blocks([at_stamp], decision_ns=decision, n_days=28)
    assert 1 in blocks and blocks[1]["n_bars"] == 1.0
    blocks_late = daily_blocks([one_ns_late], decision_ns=decision, n_days=28)
    assert blocks_late == {}
    # and the feature itself never sees the unclosed bar
    assert amihud_feature([one_ns_late], decision_ns=decision, formation_days=28) is None


def test_fill_uses_exactly_one_declared_lag_and_stress_walks_events():
    stamps = weekly_monday_stamps()
    start_day = (stamps[0] - 120 * DAY_NS) // DAY_NS
    bars = _intraday_frame(n_days=120 + 4 * 7, start_day=start_day)
    plugin = _plugin(bars)
    decision = plugin.schedule().instants[2]
    baseline = plugin.baseline_stress()
    delayed = StressSpec(
        name="stress_fee_x1_5_plus_2_ticks_plus_1_event",
        fee_multiplier=1.5,
        tick_slip_ticks=3,
        event_delay_events=1,
        drop_symbols=(),
        dropped_fold_index=None,
    )
    sym = "SYM03"
    base_fill = plugin.fills_at(decision, symbols=[sym], stress=baseline)[0]
    assert base_fill.applied
    assert base_fill.fill_open_ns - decision == DAY_NS  # the declared 24h lag
    assert base_fill.fill_bar_close_ns == decision + DAY_NS + BAR_NS
    delayed_fill = plugin.fills_at(decision, symbols=[sym], stress=delayed)[0]
    assert delayed_fill.applied
    assert delayed_fill.event_offset == 1
    assert delayed_fill.fill_open_ns - decision == DAY_NS + BAR_NS


def test_listing_pit_eligibility_defers_until_history_is_sufficient():
    """A symbol with less than the formation window of history is ineligible."""
    stamps = weekly_monday_stamps()
    start_day = (stamps[0] - 60 * DAY_NS) // DAY_NS
    bars = _daily_frame(n_days=60 + 4 * 7, start_day=start_day)
    plugin = _plugin(bars)
    universe = plugin.universe(plugin.baseline_stress())
    sym_bars = bars["SYM05"]
    first_stamp = plugin.schedule().instants[0]
    # the full tape satisfies the listing gate at the first stamp
    assert (
        amihud_feature(sym_bars, decision_ns=int(first_stamp), formation_days=28)
        is not None
    )
    # a freshly-listed tail (2 days of bars) must stay ineligible
    fresh = sym_bars[-2:]
    assert (
        amihud_feature(fresh, decision_ns=int(first_stamp), formation_days=28)
        is None
    )


def test_benchmark_is_context_only_and_folds_force_flat_at_boundaries():
    stamps = weekly_monday_stamps()
    start_day = (stamps[0] - 120 * DAY_NS) // DAY_NS
    bars = _daily_frame(n_days=120 + 52 * 7 + 10, start_day=start_day)
    plugin = _plugin(bars)
    universe = plugin.universe(plugin.baseline_stress())
    assert "BTCUSDT" not in universe
    assert "BTCUSDT" in plugin.benchmark_context_symbols()
    identity = plugin.identity()
    assert identity.benchmark_symbols_excluded == ("BTCUSDT",)
    fold_instants = plugin.fold_instants()
    assert set(fold_instants) == {"F0", "F1", "F2"}
    stamps_by_fold = {fold: list(members) for fold, members in fold_instants.items()}
    assert sum(len(v) for v in stamps_by_fold.values()) == len(plugin.schedule())
    for fold, members in stamps_by_fold.items():
        boundary = members[-1]
        if boundary == plugin.schedule().instants[-1]:
            continue  # the generic runner owns the terminal force-flat edge
        book = plugin.targets_at(
            boundary, universe=universe, stress=plugin.baseline_stress()
        )
        assert book["status"] == "OK"
        assert book["weights"] == {}
        assert book["reason_code"] == "FOLD_BOUNDARY_FORCE_FLAT"
        mid = members[len(members) // 2]
        mid_book = plugin.targets_at(
            mid, universe=universe, stress=plugin.baseline_stress()
        )
        assert mid_book["reason_code"] != "FOLD_BOUNDARY_FORCE_FLAT"
