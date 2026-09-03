"""V11 lane I-3 tests for the FROZEN A8-V11-OILEVER-DELEV family.

Covers the five mandated test groups:

(a) frozen-digest equality x3 -- the three plugin identities reproduce the
    ``selection_freeze.json`` ``arm_config_digest`` values EXACTLY;
(b) synthetic causal test -- a planted deleveraging premium gives the anchor
    book a positive expected forward spread and the sign-inverted control the
    exact flip;
(c) orthogonalisation -- after the frozen per-stamp cross-sectional OLS the
    residual signal has ~zero correlation vs the trailing-28d return
    (|rho| < 0.05 on synthetic data, both Pearson and Spearman);
(d) double-generation determinism -- identical books, identities and adapter
    result hashes across independent builds;
(e) PIT / no-leak -- completed-bar features only, the OI anchor is the last
    row strictly BEFORE the stamp, and a stamp whose last OI row is staler
    than the frozen 48h gate is UNAVAILABLE for that symbol (fail closed).

All fixtures are synthetic and deterministic; no real data is read and no
scored artifact is written (the lane is schedule-only).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

import research.adapter_v10.publish  # noqa: F401  (circular-import ordering)
from research.adapter_v10.protocol import ContractViolation
from research.adapter_v10.runner import run_strategy
from research.v11.families.oilever_delev import OileverDelevPlugin
from research.v11.families.oilever_delev import strategy as st
from research.v11.publication_identity import arm_config_digest

DAY_NS = st.DAY_NS
HOUR_NS = st.HOUR_NS

FROZEN_DIGESTS = {
    "OILEV-FLOW-28D-W": "d05c2e702c8ce02f24b843c1bd92c66451effb8c8cb73a27bd8376112ddff29a",
    "OILEV-STOCK-56D-W": "a1f29b683a263ecdd052016862f6bebc9831d3bf5df5e4f5f0cd4b1c92bac24d",
    "OILEV-FLOW-28D-W-INV": "b64b314fd116258323d9b72a0633999fe3a7e71ac87a0516d3cf60b61d09a04f",
}


# --------------------------------------------------------------------------- #
# Deterministic synthetic world (data-injected; no real data)
# --------------------------------------------------------------------------- #
def _day_ns(date_iso: str) -> int:
    moment = datetime.fromisoformat(date_iso).replace(tzinfo=timezone.utc)
    return int(moment.timestamp()) * 1_000_000_000


N_SYMBOLS = 21
SYMBOLS = tuple(f"SYM{i:02d}" for i in range(N_SYMBOLS))
BENCH = "BTCUSDT"
ALL_NAMES = tuple([BENCH, *SYMBOLS])

WORLD_START = "2025-05-01"          # bars + OI warmup (listing history / 56d)
MOMENTUM_START = "2025-07-01"       # momentum factor switches on (pre-window)
WORLD_END = "2026-08-18"            # bars cover the final force-flat stamp

#: Planted deleveraging premium: forward weekly return of symbol i.
#: The premium loads on the deleveraging-load h_i (low h = deleveraged wins)
#: with a small momentum continuation term; the frozen orthogonalisation
#: removes the momentum component from the traded signal.
PREMIUM_ALPHA = 3.0
MOMENTUM_CONTINUATION = 0.3


def _momentum(i: int) -> float:
    """Momentum factor z_i (linear in the symbol index; wide spread)."""
    return 0.03 * (i - 15)


def _hload(i: int) -> float:
    """Deleveraging-load h_i: two full cycles over the cohort, so the planted
    premium is orthogonal to the (linear-in-index) momentum factor -- exactly
    the separation the frozen orthogonalisation is supposed to expose."""
    return math.sin(2.0 * math.pi * 2.0 * (i - 11) / 10.0)


def _oi_rate(i: int) -> float:
    """Yearly OI-growth rate g_i = 2 z_i + h_i (momentum-contaminated flow)."""
    return 2.0 * _momentum(i) + 1.0 * _hload(i)


def _planted_forward_return(i: int, days: float) -> float:
    """Forward return over ``days`` under the planted premium (test-only)."""
    return days / 365.0 * (MOMENTUM_CONTINUATION * _momentum(i) - PREMIUM_ALPHA * _hload(i))


def _price(i: int, t_ns: int) -> float:
    """Momentum-only price path (trailing-28d return proportional to z_i)."""
    t0 = _day_ns(MOMENTUM_START)
    if t_ns <= t0:
        return 100.0
    return 100.0 * (1.0 + _momentum(i) * (t_ns - t0) / (365.0 * DAY_NS))


def _oi_level(i: int, t_ns: int) -> float:
    """OI level: a constant per-symbol offset (cancels in log-growth) times an
    exponential g_i trend, so the 28d log-growth is EXACTLY g_i * dt and the
    level always stays positive."""
    t0 = _day_ns(WORLD_START)
    years = (t_ns - t0) / (365.0 * DAY_NS)
    return (1000.0 + 7.0 * i) * math.exp(_oi_rate(i) * years)


def build_world(*, oi_cutoff_date: str | None = None):
    """Build synthetic bars / OI / settlements / tick sizes (deterministic).

    One completed 15m bar per UTC day (open 00:00, close stamp 00:15) so the
    covering bar of every Monday 00:00:00Z decision exists, and one OI
    snapshot per UTC day at 23:55 (the daily-last consolidated convention).

    ``oi_cutoff_date`` truncates EVERY symbol's OI series at that date (the
    staleness fail-closed fixture).
    """
    start_ns, end_ns = _day_ns(WORLD_START), _day_ns(WORLD_END)
    cutoff_ns = None if oi_cutoff_date is None else _day_ns(oi_cutoff_date)
    bars: dict[str, tuple[st.Bar, ...]] = {}
    oi: dict[str, tuple[tuple[int, float], ...]] = {}
    settles: dict[str, tuple[dict, ...]] = {}
    ticks: dict[str, float] = {}
    for index, name in enumerate(ALL_NAMES):
        bar_list = []
        day = start_ns
        while day <= end_ns:
            price = _price(index, day)
            bar_list.append(
                st.Bar(
                    ts_event_ns=day + 900_000_000_000,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1.0,
                    quote_volume=1000.0 + 10.0 * index,
                )
            )
            day += DAY_NS
        bars[name] = tuple(bar_list)
        oi_rows = []
        day = start_ns
        while day <= end_ns:
            if cutoff_ns is None or day < cutoff_ns:
                oi_rows.append((day + 23 * HOUR_NS + 55 * 60 * 1_000_000_000, _oi_level(index, day)))
            day += DAY_NS
        oi[name] = tuple(oi_rows)
        settles[name] = tuple(
            {"publish_ts_ns": day + 8 * HOUR_NS, "value": 0.0001 * (1 if index % 2 else -1)}
            for day in range(start_ns, end_ns + DAY_NS, DAY_NS)
        )
        ticks[name] = 0.01
    return bars, oi, settles, ticks


def build_plugins(world=None):
    """The three frozen arm plugins over one shared synthetic world."""
    if world is None:
        world = build_world()
    bars, oi, settles, ticks = world
    return {
        arm_id: OileverDelevPlugin(
            arm_id=arm_id,
            bars_by_symbol=bars,
            oi_by_symbol=oi,
            settlements_by_symbol=settles,
            tick_sizes=ticks,
        )
        for arm_id in st.ARM_IDS
    }


def _book_weights(book: dict) -> dict[str, float]:
    return {sym: float(w) for sym, w in book["weights"]}


def _expected_spread(weights: dict[str, float], symbol_index: dict[str, int], days: float) -> float:
    """Test-side expected forward spread of a book under the planted premium."""
    return math.fsum(
        weight * _planted_forward_return(symbol_index[sym], days)
        for sym, weight in sorted(weights.items())
    )


# --------------------------------------------------------------------------- #
# (a) Frozen identity digest equality x3
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("arm_id", sorted(FROZEN_DIGESTS))
def test_frozen_digest_equality(arm_id: str) -> None:
    plugin = build_plugins()[arm_id]
    identity = plugin.identity()
    assert identity.strategy_id == "A8-V11-OILEVER-DELEV.v1"
    assert identity.family_id == "A8-V11-OILEVER-DELEV"
    assert identity.arm_config_id == st.ARM_ROLES[arm_id]
    assert identity.direction == "long_short_beta_neutral"
    assert identity.window_start_iso == "2025-08-22T00:00:00Z"
    assert identity.window_end_iso == "2026-08-21T00:00:00Z"
    assert identity.benchmark_symbols_excluded == ("BTCUSDT",)
    assert identity.arm_id == arm_id
    digest = arm_config_digest(identity, arm_id=arm_id)
    assert digest == FROZEN_DIGESTS[arm_id]


def test_frozen_identities_distinct_and_replay_stable() -> None:
    plugins = build_plugins()
    digests_first = {
        arm: arm_config_digest(plugin.identity(), arm_id=arm)
        for arm, plugin in plugins.items()
    }
    digests_second = {
        arm: arm_config_digest(plugin.identity(), arm_id=arm)
        for arm, plugin in plugins.items()
    }
    assert digests_first == digests_second
    assert len(set(digests_first.values())) == 3
    for arm, digest in digests_first.items():
        assert digest == FROZEN_DIGESTS[arm]


def test_frozen_config_payload_exact() -> None:
    """The digest payload carries the exact frozen values, nothing else."""
    anchor = st.frozen_arm_config(st.ANCHOR_ARM)
    assert anchor == {
        "feature": st.FEATURE_FLOW,
        "book": "long deleveraged / short crowded quintiles, beta-neutral",
        "formation_days": 28,
        "holding_days": 7,
        "decision_clock": st.DECISION_CLOCK,
        "costs": st.COSTS,
        "falsification": "",
    }
    control = st.frozen_arm_config(st.CONTROL_ARM)
    assert control["book"] == "sign-inverted"
    assert control["falsification"] == "positive after-cost spread destroys mechanism"
    assert control["feature"] == st.FEATURE_FLOW
    neighbour = st.frozen_arm_config(st.NEIGHBOUR_ARM)
    assert neighbour["feature"] == st.FEATURE_STOCK
    assert neighbour["formation_days"] == 56
    with pytest.raises(ContractViolation):
        st.frozen_arm_config("NOT-AN-ARM")


# --------------------------------------------------------------------------- #
# (b) Synthetic causal test (planted deleveraging premium)
# --------------------------------------------------------------------------- #
def test_causal_anchor_positive_and_control_flips() -> None:
    plugins = build_plugins()
    schedule = plugins[st.ANCHOR_ARM].schedule()
    universe = plugins[st.ANCHOR_ARM].tradeable_universe()
    symbol_index = {name: int(name[3:]) for name in universe}
    baseline_stress = plugins[st.ANCHOR_ARM].baseline_stress()

    checked = 0
    for instant in schedule.instants:
        anchor = plugins[st.ANCHOR_ARM].targets_at(
            int(instant), universe=universe, stress=baseline_stress
        )
        control = plugins[st.CONTROL_ARM].targets_at(
            int(instant), universe=universe, stress=baseline_stress
        )
        if anchor["status"] != st.STATUS_OK:
            assert control["status"] != st.STATUS_OK
            continue
        checked += 1
        weights_anchor = _book_weights(anchor)
        weights_control = _book_weights(control)
        # exact sign flip end-to-end on the same names
        assert set(weights_anchor) == set(weights_control)
        assert all(
            weights_control[sym] == -weights_anchor[sym] for sym in weights_anchor
        )
        # dollar neutrality + gross target
        gross = math.fsum(abs(w) for w in weights_anchor.values())
        net = math.fsum(weights_anchor.values())
        assert abs(gross - 1.0) < 1e-9
        assert abs(net) < 1e-9
        # planted deleveraging premium: anchor spread > 0, control < 0
        spread_anchor = _expected_spread(weights_anchor, symbol_index, days=7.0)
        spread_control = _expected_spread(weights_control, symbol_index, days=7.0)
        assert spread_anchor > 0.0
        assert spread_control < 0.0
        assert abs(spread_anchor + spread_control) < 1e-12
        # long side is the deleveraged (low h-load) side
        longs = [sym for sym, w in weights_anchor.items() if w > 0]
        shorts = [sym for sym, w in weights_anchor.items() if w < 0]
        mean_h_longs = sum(_hload(symbol_index[s]) for s in longs) / len(longs)
        mean_h_shorts = sum(_hload(symbol_index[s]) for s in shorts) / len(shorts)
        assert mean_h_longs < mean_h_shorts
    assert checked >= 40  # the book trades on the overwhelming majority of stamps


def test_causal_neighbour_book_same_sign_semantics() -> None:
    """Neighbour trades the 56d stock feature with the same long-low book rule."""
    plugins = build_plugins()
    plugin = plugins[st.NEIGHBOUR_ARM]
    universe = plugin.tradeable_universe()
    stress = plugin.baseline_stress()
    books = 0
    for instant in plugin.schedule().instants:
        book = plugin.targets_at(int(instant), universe=universe, stress=stress)
        if book["status"] != st.STATUS_OK:
            continue
        books += 1
        weights = _book_weights(book)
        assert abs(math.fsum(weights.values())) < 1e-9
        diagnostics = book["diagnostics"]
        assert diagnostics["feature_kind"] == "stock"
        assert diagnostics["residual_rho_vs_trailing_return"] < 1e-6
    assert books >= 40


def test_oi_stock_percentile_mechanics() -> None:
    """56d own-history percentile: monotone series pins 1.0; a dip varies it."""
    stamp = 100 * DAY_NS
    series = tuple((day * DAY_NS, 100.0 + day) for day in range(1, 100))
    assert st.oi_stock_percentile(series, stamp) == pytest.approx(1.0)
    dipped = list(series)
    dipped[-1] = (stamp - DAY_NS, 40.0)  # last snapshot dips below the window
    value = st.oi_stock_percentile(tuple(dipped), stamp)
    assert 0.0 < value < 0.5
    # too little history -> fail closed
    assert st.oi_stock_percentile(series[:1], stamp) is None
    # stale current anchor -> fail closed
    assert st.oi_stock_percentile(series, stamp + 72 * HOUR_NS) is None


# --------------------------------------------------------------------------- #
# (c) Frozen momentum-orthogonalisation
# --------------------------------------------------------------------------- #
def test_residualisation_kills_cross_sectional_rho() -> None:
    """After the frozen OLS, residual-vs-return rho ~ 0 (Pearson AND Spearman)."""
    seed = 20260903
    for trial in range(8):
        n = 40
        values, returns = {}, {}
        for i in range(n):
            seed = (seed * 1103515245 + 12345) % (2**31)
            x = ((seed % 2000) - 1000) / 1000.0
            seed = (seed * 1103515245 + 12345) % (2**31)
            eps = ((seed % 200) - 100) / 1000.0
            returns[f"S{i:02d}"] = x
            values[f"S{i:02d}"] = 2.0 + 3.0 * x + eps  # strong momentum contamination
        out = st.residualise_against_return(values, returns)
        assert out is not None
        residuals, ols = out
        names = sorted(residuals)
        xs = [returns[s] for s in names]
        rs = [residuals[s] for s in names]
        assert abs(st.pearson_rho(rs, xs)) < 1e-8
        assert abs(st.spearman_rho(rs, xs)) < 0.05
        assert ols["n"] == n


def test_traded_signal_orthogonal_on_synthetic_world() -> None:
    """End-to-end: the plugin's traded residual has ~zero rho vs the return."""
    plugins = build_plugins()
    plugin = plugins[st.ANCHOR_ARM]
    universe = plugin.tradeable_universe()
    stress = plugin.baseline_stress()
    rhos = []
    for instant in plugin.schedule().instants:
        book = plugin.targets_at(int(instant), universe=universe, stress=stress)
        if book["status"] == st.STATUS_OK:
            rhos.append(abs(float(book["diagnostics"]["residual_rho_vs_trailing_return"])))
    assert len(rhos) >= 40
    assert max(rhos) < 0.05


def test_residualisation_fail_closed_on_degenerate_cross_section() -> None:
    assert st.residualise_against_return({"A": 1.0, "B": 2.0}, {"A": 0.0, "B": 1.0}) is None
    same = {"A": 1.0, "B": 2.0, "C": 3.0}
    assert st.residualise_against_return(same, {"A": 1.0, "B": 1.0, "C": 1.0}) is None


# --------------------------------------------------------------------------- #
# (d) Double-generation determinism
# --------------------------------------------------------------------------- #
def test_double_generation_determinism() -> None:
    plugins_a = build_plugins()
    plugins_b = build_plugins()
    for arm_id in st.ARM_IDS:
        pa, pb = plugins_a[arm_id], plugins_b[arm_id]
        assert pa.identity() == pb.identity()
        assert arm_config_digest(pa.identity(), arm_id=arm_id) == FROZEN_DIGESTS[arm_id]
        assert pa.schedule().instants == pb.schedule().instants
        assert pa.schedule().sha256 == pb.schedule().sha256
        universe = pa.tradeable_universe()
        stress = pa.baseline_stress()
        for instant in pa.schedule().instants:
            assert pa.targets_at(int(instant), universe=universe, stress=stress) == (
                pb.targets_at(int(instant), universe=universe, stress=stress)
            )
    # full adapter path determinism (dummy run, unscored, no artifacts written)
    result_a = run_strategy(plugins_a[st.ANCHOR_ARM], write_artifact_file=False)
    result_b = run_strategy(plugins_b[st.ANCHOR_ARM], write_artifact_file=False)
    assert result_a["hashes"]["result_sha256"] == result_b["hashes"]["result_sha256"]
    assert result_a["scored"] is False


# --------------------------------------------------------------------------- #
# (e) PIT / no-leak / staleness fail-closed
# --------------------------------------------------------------------------- #
def test_oi_anchor_is_last_row_strictly_before_stamp() -> None:
    series = (
        (1 * DAY_NS, 10.0),
        (2 * DAY_NS, 20.0),
        (3 * DAY_NS, 30.0),
    )
    # a row exactly AT the stamp is never used; the previous row wins
    assert st.oi_anchor_before(series, 3 * DAY_NS) == 20.0
    assert st.oi_anchor_before(series, 3 * DAY_NS + 1) == 30.0
    assert st.oi_anchor_before(series, 1 * DAY_NS) is None  # nothing strictly before
    # nonpositive rows are refused
    assert st.oi_anchor_before(((1 * DAY_NS, 0.0),), 2 * DAY_NS) is None
    assert st.oi_anchor_before((), 2 * DAY_NS) is None


def test_oi_staleness_fails_closed_beyond_48h() -> None:
    series = ((1 * DAY_NS, 10.0),)
    fresh = 1 * DAY_NS + 47 * HOUR_NS
    stale = 1 * DAY_NS + 49 * HOUR_NS
    assert st.oi_anchor_before(series, fresh) == 10.0
    assert st.oi_anchor_before(series, stale) is None  # UNAVAILABLE, fail closed


def test_trailing_return_uses_only_completed_bars_before_stamp() -> None:
    bars = (
        st.Bar(ts_event_ns=1 * DAY_NS, open=1, high=1, low=1, close=100.0),
        st.Bar(ts_event_ns=29 * DAY_NS, open=1, high=1, low=1, close=110.0),
    )
    # the 29d bar is at the stamp edge: strictly-before lookups exclude it
    assert st.trailing_return(bars, 30 * DAY_NS) == pytest.approx(0.10)
    assert st.trailing_return(bars, 29 * DAY_NS) is None  # past bar missing


def test_stale_oi_symbol_dropped_from_signal() -> None:
    """A symbol whose OI ended >48h before a stamp is UNAVAILABLE there."""
    world = build_world()
    plugins_fresh = build_plugins(world)
    plugin = plugins_fresh[st.ANCHOR_ARM]
    universe = plugin.tradeable_universe()
    stress = plugin.baseline_stress()
    late_stamp = st.weekly_mondays()[-3]

    stale_world = build_world(oi_cutoff_date="2026-06-01")
    # keep every symbol's OI intact EXCEPT SYM20 (single-symbol staleness)
    stale_oi = dict(stale_world[1])
    for name in stale_oi:
        if name != "SYM20":
            stale_oi[name] = world[1][name]
    plugins_stale = {
        arm_id: OileverDelevPlugin(
            arm_id=arm_id,
            bars_by_symbol=stale_world[0],
            oi_by_symbol=stale_oi,
            settlements_by_symbol=stale_world[2],
            tick_sizes=stale_world[3],
        )
        for arm_id in st.ARM_IDS
    }
    stale_plugin = plugins_stale[st.ANCHOR_ARM]

    fresh_book = plugin.targets_at(int(late_stamp), universe=universe, stress=stress)
    stale_book = stale_plugin.targets_at(int(late_stamp), universe=universe, stress=stress)
    assert fresh_book["status"] == st.STATUS_OK
    assert stale_book["status"] == st.STATUS_OK
    fresh_diag = fresh_book["diagnostics"]
    stale_diag = stale_book["diagnostics"]
    assert fresh_diag["n_complete"] == 10
    assert stale_diag["n_complete"] == 9
    # the stale symbol's anchor is UNAVAILABLE at the stamp (fail closed),
    # while the fresh world's SYM20 anchor is present
    assert st.oi_flow_growth(stale_world[1]["SYM20"], int(late_stamp)) is None
    assert st.oi_flow_growth(world[1]["SYM20"], int(late_stamp)) is not None
    # ...and it can never appear in the stale stamp's signal cross-section
    stale_names = {sym for sym, _ in stale_book["weights"]}
    fresh_names = {sym for sym, _ in fresh_book["weights"]}
    assert "SYM20" not in stale_names
    assert stale_names != fresh_names or "SYM20" not in fresh_names


def test_universe_wide_staleness_skips_stamp_fail_closed() -> None:
    """Every symbol stale at a stamp -> the stamp is refused (SKIP, no book)."""
    stale_world = build_world(oi_cutoff_date="2026-01-01")
    plugin = build_plugins(stale_world)[st.ANCHOR_ARM]
    universe = plugin.tradeable_universe()
    stress = plugin.baseline_stress()
    late_stamp = st.weekly_mondays()[-1]
    book = plugin.targets_at(int(late_stamp), universe=universe, stress=stress)
    assert book["status"] == st.STATUS_SKIP
    assert book["weights"] == []
    assert book["carried_forward"] is True
    assert book["diagnostics"]["reason_code"] is not None


def test_no_leak_future_bars_do_not_change_books() -> None:
    """Perturbing every bar AFTER a stamp leaves that stamp's book untouched."""
    world_a = build_world()
    bars_a, oi_a, settles_a, ticks_a = world_a
    cut = _day_ns("2026-01-05")  # a mid-window Monday
    bars_b: dict[str, tuple[st.Bar, ...]] = {}
    for name, series in bars_a.items():
        mutated = []
        for bar in series:
            if bar.ts_event_ns > cut:
                mutated.append(
                    st.Bar(
                        ts_event_ns=bar.ts_event_ns,
                        open=bar.open * 1.5,
                        high=bar.high * 1.5,
                        low=bar.low * 1.5,
                        close=bar.close * 1.5,
                        volume=bar.volume,
                        quote_volume=bar.quote_volume * 7.0,
                    )
                )
            else:
                mutated.append(bar)
        bars_b[name] = tuple(mutated)
    plugin_a = OileverDelevPlugin(
        arm_id=st.ANCHOR_ARM, bars_by_symbol=bars_a, oi_by_symbol=oi_a,
        settlements_by_symbol=settles_a, tick_sizes=ticks_a,
    )
    plugin_b = OileverDelevPlugin(
        arm_id=st.ANCHOR_ARM, bars_by_symbol=bars_b, oi_by_symbol=oi_a,
        settlements_by_symbol=settles_a, tick_sizes=ticks_a,
    )
    universe = plugin_a.tradeable_universe()
    stress = plugin_a.baseline_stress()
    for instant in plugin_a.schedule().instants:
        if int(instant) > cut:
            break
        assert plugin_a.targets_at(int(instant), universe=universe, stress=stress) == (
            plugin_b.targets_at(int(instant), universe=universe, stress=stress)
        )


# --------------------------------------------------------------------------- #
# Frozen clocks / adapter plumbing
# --------------------------------------------------------------------------- #
def test_schedule_is_52_mondays_pinned() -> None:
    plugin = build_plugins()[st.ANCHOR_ARM]
    schedule = plugin.schedule()
    assert len(schedule.instants) == 52
    assert st.iso_utc(schedule.instants[0]) == "2025-08-25T00:00:00Z"
    assert st.iso_utc(schedule.instants[-1]) == "2026-08-17T00:00:00Z"
    for instant in schedule.instants:
        moment = datetime.fromtimestamp(instant / 1e9, tz=timezone.utc)
        assert moment.weekday() == 0
        assert moment.hour == 0 and moment.minute == 0 and moment.second == 0


def test_folds_match_pinned_calendar_windows() -> None:
    plugin = build_plugins()[st.ANCHOR_ARM]
    folds = plugin.folds(stress=plugin.baseline_stress(), instants=list(plugin.schedule().instants))
    assert [fold.label for fold in folds] == ["F0", "F1", "F2"]
    assert [fold.index for fold in folds] == [0, 1, 2]
    labels = {fold.label: st.iso_utc(fold.instants[0])[:10] for fold in folds}
    ends = {fold.label: st.iso_utc(fold.instants[-1])[:10] for fold in folds}
    assert labels["F0"] == "2025-08-25" and ends["F0"] == "2025-12-08"
    assert labels["F1"] == "2025-12-22" and ends["F1"] == "2026-04-13"
    assert labels["F2"] == "2026-04-27" and ends["F2"] == "2026-08-10"
    # purge strips exactly the trailing instant of each fold window
    covered = [instant for fold in folds for instant in fold.instants]
    assert len(covered) == 49


def test_adapter_run_end_to_end_unscored() -> None:
    """The generic runner traverses the plugin; nothing is scored or written."""
    plugin = build_plugins()[st.ANCHOR_ARM]
    result = run_strategy(plugin, write_artifact_file=False)
    assert result["scored"] is False
    assert result["universe"] == sorted(SYMBOLS)
    assert result["benchmark_symbols_excluded"] == ["BTCUSDT"]
    assert len(result["books"]) == 51  # every non-final instant carries a book
    ok_books = [book for book in result["books"] if book["status"] == st.STATUS_OK]
    assert len(ok_books) >= 40
    for book in ok_books:
        gross = math.fsum(abs(w) for _s, w in book["weights"])
        assert abs(gross - 1.0) < 1e-9
        assert all(abs(w) <= 0.30 + 1e-9 for _s, w in book["weights"])
    assert result["fold_metrics"], "fold table must exist"
    assert [row["fold_label"] for row in result["fold_metrics"]] == ["F0", "F1", "F2"]
