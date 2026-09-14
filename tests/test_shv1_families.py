"""Synthetic hand-computed fixtures for the three SHADOW-V1 family adapters.

Every fixture is constructed so the correct ranks, books and weights are
computable by hand:
- ILLIQ: 10 synthetic symbols with engineered daily-return counts ->
  exact long/short quintile membership and +-0.25 weights;
- PREMFADE: 12 symbols (the min-eligibility boundary) with distinct
  constant premium levels -> exact tercile membership and +-0.125
  weights;
- CARRY: the 7 frozen universe symbols with distinct constant funding
  rates -> exact bottom-2/top-2 selection and +-0.20 weights.

Also covered: min-eligibility DataBlocked, previous-weights passthrough,
exit-policy strings, dollar neutrality, and the price-only mechanism
clause (feeding two different funding sets to illiq/premfade must
produce identical proposals).
"""

import datetime as dt
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from research.shadow_v1 import risk
from research.shadow_v1.data_feed import DataBlocked
from research.shadow_v1.families import (
    FAMILY_REGISTRY,
    BasislvPremfadeAdapter,
    FamilySnapshot,
    IlliqAmihudAdapter,
    XsectFundCarryAdapter,
)

WORKTREE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    WORKTREE_ROOT / "research" / "control" / "prospective_shadow_v1" / "identity" / "identity_recovery.json"
)

MONDAY = "2026-03-02T00:00:00Z"  # a Monday
WEDNESDAY = "2026-03-04T00:00:00Z"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

ILLIQ_ENGINE = {
    "min_listing_age_days": 7.0,
    "min_daily_dollar_volume": 1_000.0,
    "btc_beta_tolerance": 1e-6,
    "hard_gross_cap": 1.0,
    "hard_abs_net_cap": 0.0,
}


def to_iso(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime(ISO_FMT)


def parse_iso(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, ISO_FMT).replace(tzinfo=dt.timezone.utc)


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text())


def manifest_entry(family_id: str):
    for entry in load_manifest()["families"]:
        if entry["family_id"] == family_id:
            return entry
    raise AssertionError(f"family {family_id} not in identity manifest")


def build_adapter(cls, engine=None):
    entry = manifest_entry(cls.FAMILY_ID)
    config = cls.build_config(entry, engine or {})
    return cls(config, entry)


# ----------------------------------------------------------------------
# synthetic bar / bucket / funding generators (deterministic)
# ----------------------------------------------------------------------
INTERVAL = dt.timedelta(minutes=15)


def bar_grid_opens(start_utc: str, days: int):
    start = parse_iso(start_utc)
    return [start + k * INTERVAL for k in range(days * 96)]


def make_bars(symbol: str, opens, daily_close_levels, quote_volume: float):
    """One 15m bar per open slot; every bar inside a day closes at that
    day's engineered level, so daily aggregates are hand-checkable."""
    first_day = opens[0].date()
    bars = []
    for open_dt in opens:
        day_index = (open_dt.date() - first_day).days
        bars.append(
            {
                "open_time_utc": to_iso(open_dt),
                "close_time_utc": to_iso(open_dt + INTERVAL),
                "close_price": daily_close_levels[day_index],
                "quote_volume": quote_volume,
            }
        )
    return bars


def make_buckets(symbol: str, opens, premium: float, index_price: float = 100.0):
    """Completed 15m basis buckets with a constant premium level."""
    futures = index_price * (1.0 + premium)
    return [
        {
            "open_time_utc": to_iso(open_dt),
            "close_time_utc": to_iso(open_dt + INTERVAL),
            "futures_price": futures,
            "index_price": index_price,
        }
        for open_dt in opens
    ]


def make_funding(symbol: str, rate: float, first_day: dt.date, days: int):
    """Three settled funding events per day at 00:00 / 08:00 / 16:00 UTC."""
    rows = []
    for day_offset in range(days):
        day = first_day + dt.timedelta(days=day_offset)
        for hour in (0, 8, 16):
            rows.append(
                {
                    "funding_time_utc": to_iso(
                        dt.datetime(day.year, day.month, day.day, hour, tzinfo=dt.timezone.utc)
                    ),
                    "funding_rate": rate,
                }
            )
    return rows


# ======================================================================
# registry
# ======================================================================
def test_registry_maps_all_three_families():
    assert sorted(FAMILY_REGISTRY) == [
        "BASISLV-PREMFADE-28D",
        "ILLIQ-AMIHUD-28D-W",
        "XSECT-FUND-CARRY-7D",
    ]


# ======================================================================
# ILLIQ-AMIHUD-28D-W
# ======================================================================
ILLIQ_SYMBOLS = [f"SYM{i}USDT" for i in range(10)]


def illiq_snapshot(symbols=ILLIQ_SYMBOLS, base_day="2026-02-01T00:00:00Z", days=29):
    """29 days of completed 15m bars; symbol i has exactly i days of +1%
    daily returns, so mean|r| (hence Amihud) strictly increases with i."""
    opens = bar_grid_opens(base_day, days)
    bars = {}
    for idx, symbol in enumerate(symbols):
        levels = [
            100.0 * (1.01 ** min(day, idx)) for day in range(days)
        ]
        bars[symbol] = make_bars(symbol, opens, levels, quote_volume=1000.0 * (idx + 1))
    return FamilySnapshot(bars=bars)


def test_illiq_exact_quintile_book_and_neutrality():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    proposal = adapter.decide(illiq_snapshot(), MONDAY, "2026-03-01T23:45:00Z", {})
    # amihud_i ~ i/(i+1): most illiquid = SYM9USDT, most liquid = SYM0USDT
    assert proposal.target_weights == {
        "SYM9USDT": 0.25,
        "SYM8USDT": 0.25,
        "SYM0USDT": -0.25,
        "SYM1USDT": -0.25,
    }
    assert proposal.diagnostics["long_book"] == ["SYM9USDT", "SYM8USDT"]
    assert proposal.diagnostics["short_book"] == ["SYM1USDT", "SYM0USDT"]
    assert sum(proposal.target_weights.values()) == 0.0  # exact dollar neutrality
    assert sum(abs(w) for w in proposal.target_weights.values()) == 1.0
    assert proposal.family_id == "ILLIQ-AMIHUD-28D-W"
    assert proposal.arm_id == "ILLIQ-AMIHUD-28D-W"
    # signal ordering by amihud descending
    values = list(proposal.signal_values.values())
    assert values == sorted(values, reverse=True)
    # all 10 symbols accounted for
    assert set(proposal.eligible_symbols) | set(proposal.rejected_symbols_with_reason) == set(
        ILLIQ_SYMBOLS
    )


def test_illiq_beta_neutral_book_with_equal_betas():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    snapshot = FamilySnapshot(
        bars=illiq_snapshot().bars,
        btc_betas={s: 1.0 for s in ILLIQ_SYMBOLS},
    )
    proposal = adapter.decide(snapshot, MONDAY, "2026-03-01T23:45:00Z", {})
    assert proposal.diagnostics["book_btc_beta"] == 0.0
    # and the frozen caps approve this book (beta-neutral, dollar-neutral)
    caps = risk.FamilyRiskCaps(
        family_id=IlliqAmihudAdapter.FAMILY_ID,
        target_gross=1.0,
        hard_gross_cap=1.0,
        hard_abs_net_cap=0.0,
        dollar_neutral=True,
        btc_beta_neutral=True,
        btc_beta_tolerance=1e-6,
    )
    approved, block = risk.check_and_apply(
        proposal.target_weights, caps, snapshot.btc_betas
    )
    assert not block.blocked
    assert approved == proposal.target_weights


def test_illiq_dv_filter_removes_most_liquid_symbol():
    # mean daily DV of SYM0USDT is 2687 x 1000 / 28 ~ 95,964; SYM1USDT is
    # roughly double. A 100,000 threshold removes exactly SYM0USDT.
    engine = dict(ILLIQ_ENGINE, min_daily_dollar_volume=100_000.0)
    adapter = build_adapter(IlliqAmihudAdapter, engine)
    proposal = adapter.decide(illiq_snapshot(), MONDAY, "2026-03-01T23:45:00Z", {})
    assert proposal.rejected_symbols_with_reason["SYM0USDT"] == "below_dv_filter"
    # 9 eligible -> quintile size 1
    assert proposal.diagnostics["quintile_size"] == 1
    assert proposal.target_weights == {"SYM9USDT": 0.5, "SYM1USDT": -0.5}


def test_illiq_pit_listing_rejection():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    snapshot = FamilySnapshot(
        bars=illiq_snapshot().bars,
        listing_utc={sym: "2020-01-01T00:00:00Z" for sym in ILLIQ_SYMBOLS}
        | {"SYM5USDT": "2026-02-28T00:00:00Z"},  # only 2 days before decision
    )
    proposal = adapter.decide(snapshot, MONDAY, "2026-03-01T23:45:00Z", {})
    assert proposal.rejected_symbols_with_reason["SYM5USDT"] == "pit_listing_too_recent"
    assert "SYM5USDT" not in proposal.target_weights


def test_illiq_incomplete_formation_rejected_per_symbol():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    snapshot = illiq_snapshot()
    # drop one day of bars for SYM3USDT (keep 28 days only)
    cutoff_day = parse_iso("2026-02-01T00:00:00Z") + dt.timedelta(days=7)
    snapshot = FamilySnapshot(
        bars={
            sym: ([b for b in bars if parse_iso(b["open_time_utc"]) >= cutoff_day]
                  if sym == "SYM3USDT" else bars)
            for sym, bars in snapshot.bars.items()
        }
    )
    proposal = adapter.decide(snapshot, MONDAY, "2026-03-01T23:45:00Z", {})
    assert "insufficient_formation_bars" in proposal.rejected_symbols_with_reason["SYM3USDT"]
    assert "SYM3USDT" not in proposal.target_weights


def test_illiq_minimum_names_data_blocked():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    four = ILLIQ_SYMBOLS[:4]
    with pytest.raises(DataBlocked):
        adapter.decide(illiq_snapshot(symbols=four), MONDAY, "2026-03-01T23:45:00Z", {})


def test_illiq_structural_quintile_minimum_with_five_names():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    # 5 genuinely identical symbols: amihud ties broken by symbol id
    # ascending, so the long book is the first and the short book the
    # last symbol id.
    symbols = [f"TIE{i}USDT" for i in range(5)]
    opens = bar_grid_opens("2026-02-01T00:00:00Z", 29)
    flat = [100.0] * 29
    bars = {sym: make_bars(sym, opens, flat, quote_volume=1000.0) for sym in symbols}
    proposal = adapter.decide(
        FamilySnapshot(bars=bars), MONDAY, "2026-03-01T23:45:00Z", {}
    )
    assert proposal.diagnostics["quintile_size"] == 1
    assert proposal.target_weights == {"TIE0USDT": 0.5, "TIE4USDT": -0.5}


def test_illiq_wrong_clock_refused():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    with pytest.raises(ValueError):
        adapter.decide(illiq_snapshot(), WEDNESDAY, "2026-03-03T23:45:00Z", {})


def test_illiq_cutoff_not_before_decision_blocked():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    with pytest.raises(DataBlocked):
        adapter.decide(illiq_snapshot(), MONDAY, MONDAY, {})


def test_illiq_previous_weights_passthrough():
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    previous = {"SYM9USDT": 0.25, "SYM0USDT": -0.25}
    proposal = adapter.decide(
        illiq_snapshot(), MONDAY, "2026-03-01T23:45:00Z", previous
    )
    assert proposal.previous_weights == previous


def test_illiq_exit_policy_has_no_stop_loss_or_take_profit():
    policy = IlliqAmihudAdapter.EXIT_POLICY
    assert policy == "scheduled weekly rebalance; rank removal; risk-cap block"
    for forbidden in ("stop-loss", "stop_loss", "take-profit", "take_profit"):
        assert forbidden not in policy


def test_illiq_funding_never_changes_the_signal():
    """Price-only mechanism clause: funding data must not touch the book."""
    adapter = build_adapter(IlliqAmihudAdapter, ILLIQ_ENGINE)
    cutoff = "2026-03-01T23:45:00Z"
    without_funding = adapter.decide(illiq_snapshot(), MONDAY, cutoff, {})
    heavy_funding = FamilySnapshot(
        bars=illiq_snapshot().bars,
        funding_settlements={
            sym: make_funding(sym, 0.05, parse_iso(MONDAY).date() - dt.timedelta(days=8), 9)
            for sym in ILLIQ_SYMBOLS
        },
    )
    with_funding = adapter.decide(heavy_funding, MONDAY, cutoff, {})
    assert asdict(with_funding) == asdict(without_funding)


# ======================================================================
# BASISLV-PREMFADE-28D
# ======================================================================
PREMFADE_SYMBOLS = [f"PRE{i}USDT" for i in range(12)]


def premfade_snapshot(symbols=PREMFADE_SYMBOLS, base_day="2026-02-01T00:00:00Z", days=29):
    """29 days of 15m basis buckets; symbol i carries a constant premium
    level (i - (n-1)/2) x 1e-4 so the ascending rank is exactly i."""
    opens = bar_grid_opens(base_day, days)
    buckets = {}
    n = len(symbols)
    for idx, symbol in enumerate(symbols):
        premium = (idx - (n - 1) / 2.0) * 1e-4
        buckets[symbol] = make_buckets(symbol, opens, premium)
    return FamilySnapshot(basis_buckets=buckets)


def test_premfade_exact_tercile_book():
    adapter = build_adapter(BasislvPremfadeAdapter)
    proposal = adapter.decide(
        premfade_snapshot(), MONDAY, "2026-03-01T23:45:00Z", {}
    )
    assert proposal.target_weights == {
        "PRE0USDT": 0.125,
        "PRE1USDT": 0.125,
        "PRE2USDT": 0.125,
        "PRE3USDT": 0.125,
        "PRE8USDT": -0.125,
        "PRE9USDT": -0.125,
        "PRE10USDT": -0.125,
        "PRE11USDT": -0.125,
    }
    assert proposal.diagnostics["long_tier"] == ["PRE0USDT", "PRE1USDT", "PRE2USDT", "PRE3USDT"]
    assert proposal.diagnostics["short_tier"] == [
        "PRE8USDT",
        "PRE9USDT",
        "PRE10USDT",
        "PRE11USDT",
    ]
    assert sum(proposal.target_weights.values()) == 0.0
    assert sum(abs(w) for w in proposal.target_weights.values()) == 1.0
    # designed max |w| = 0.125 respected exactly at the 12-name boundary
    assert max(abs(w) for w in proposal.target_weights.values()) == 0.125
    assert proposal.eligible_symbols == tuple(PREMFADE_SYMBOLS)
    assert proposal.rejected_symbols_with_reason == {}


def test_premfade_min_eligibility_boundary_exactly_twelve():
    adapter = build_adapter(BasislvPremfadeAdapter)
    twelve = premfade_snapshot()
    proposal = adapter.decide(twelve, MONDAY, "2026-03-01T23:45:00Z", {})
    assert len(proposal.eligible_symbols) == 12
    eleven = premfade_snapshot(symbols=PREMFADE_SYMBOLS[1:])
    with pytest.raises(DataBlocked):
        adapter.decide(eleven, MONDAY, "2026-03-01T23:45:00Z", {})


def test_premfade_btc_benchmark_excluded():
    adapter = build_adapter(BasislvPremfadeAdapter)
    snapshot = premfade_snapshot()
    snapshot = FamilySnapshot(
        basis_buckets=dict(
            snapshot.basis_buckets, **{"BTCUSDT": make_buckets("BTCUSDT", bar_grid_opens("2026-02-01T00:00:00Z", 29), 0.0)}
        )
    )
    proposal = adapter.decide(snapshot, MONDAY, "2026-03-01T23:45:00Z", {})
    assert proposal.rejected_symbols_with_reason["BTCUSDT"] == "benchmark_excluded"
    assert "BTCUSDT" not in proposal.target_weights
    assert len(proposal.eligible_symbols) == 12
    # 11 non-BTC names + BTC excluded -> below min_eligible -> DataBlocked
    eleven = premfade_snapshot(symbols=PREMFADE_SYMBOLS[1:])
    with_btc = FamilySnapshot(
        basis_buckets=dict(
            eleven.basis_buckets, **{"BTCUSDT": make_buckets("BTCUSDT", bar_grid_opens("2026-02-01T00:00:00Z", 29), 0.0)}
        )
    )
    with pytest.raises(DataBlocked):
        adapter.decide(with_btc, MONDAY, "2026-03-01T23:45:00Z", {})


def test_premfade_incomplete_buckets_rejected():
    adapter = build_adapter(BasislvPremfadeAdapter)
    snapshot = premfade_snapshot()
    trimmed = dict(snapshot.basis_buckets)
    # 13th complete symbol keeps min_eligible satisfiable while PRE4USDT
    # is disqualified for a truncated formation grid.
    trimmed["PRE12USDT"] = make_buckets(
        "PRE12USDT", bar_grid_opens("2026-02-01T00:00:00Z", 29), -0.01
    )
    trimmed["PRE4USDT"] = trimmed["PRE4USDT"][: 96 * 20]  # 20 days only
    proposal = adapter.decide(
        FamilySnapshot(basis_buckets=trimmed), MONDAY, "2026-03-01T23:45:00Z", {}
    )
    assert "insufficient_formation_buckets" in proposal.rejected_symbols_with_reason["PRE4USDT"]
    assert "PRE4USDT" not in proposal.target_weights
    assert len(proposal.eligible_symbols) == 12


def test_premfade_funding_never_changes_the_signal():
    adapter = build_adapter(BasislvPremfadeAdapter)
    cutoff = "2026-03-01T23:45:00Z"
    without_funding = adapter.decide(premfade_snapshot(), MONDAY, cutoff, {})
    heavy_funding = FamilySnapshot(
        basis_buckets=premfade_snapshot().basis_buckets,
        funding_settlements={
            sym: make_funding(sym, -0.03, parse_iso(MONDAY).date() - dt.timedelta(days=8), 9)
            for sym in PREMFADE_SYMBOLS
        },
    )
    with_funding = adapter.decide(heavy_funding, MONDAY, cutoff, {})
    assert asdict(with_funding) == asdict(without_funding)


def test_premfade_wrong_clock_refused():
    adapter = build_adapter(BasislvPremfadeAdapter)
    with pytest.raises(ValueError):
        adapter.decide(premfade_snapshot(), WEDNESDAY, "2026-03-03T23:45:00Z", {})


def test_premfade_previous_weights_passthrough_and_policy():
    adapter = build_adapter(BasislvPremfadeAdapter)
    previous = {"PRE0USDT": 0.125}
    proposal = adapter.decide(
        premfade_snapshot(), MONDAY, "2026-03-01T23:45:00Z", previous
    )
    assert proposal.previous_weights == previous
    assert proposal.exit_policy == "scheduled weekly rebalance; rank removal; risk-cap block"
    assert proposal.exit_policy == BasislvPremfadeAdapter.EXIT_POLICY


def test_premfade_frozen_caps_approve_the_book():
    adapter = build_adapter(BasislvPremfadeAdapter)
    proposal = adapter.decide(premfade_snapshot(), MONDAY, "2026-03-01T23:45:00Z", {})
    entry = manifest_entry("BASISLV-PREMFADE-28D")
    caps = risk.caps_from_identity_params(
        "BASISLV-PREMFADE-28D", entry["score_affecting_parameters"]
    )
    approved, block = risk.check_and_apply(proposal.target_weights, caps)
    assert not block.blocked
    assert approved == proposal.target_weights


# ======================================================================
# XSECT-FUND-CARRY-7D
# ======================================================================
CARRY_UNIVERSE = [
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
]


def carry_snapshot(funding_by_symbol=None, days=9):
    """Settled funding for the frozen 7-symbol universe; symbol i has a
    constant rate (i - 3) x 1e-4 so ascending rank is exactly i."""
    first_day = parse_iso(MONDAY).date() - dt.timedelta(days=days - 1)
    funding = {}
    for idx, symbol in enumerate(CARRY_UNIVERSE):
        rate = (idx - 3) * 1e-4
        funding[symbol] = make_funding(symbol, rate, first_day, days)
    if funding_by_symbol:
        funding.update(funding_by_symbol)
    return FamilySnapshot(funding_settlements=funding)


def test_carry_exact_bottom2_top2_book():
    adapter = build_adapter(XsectFundCarryAdapter)
    proposal = adapter.decide(carry_snapshot(), MONDAY, MONDAY, {})
    # rates (i - 3) x 1e-4: bottom two = ETH/SOL (long),
    # top two = LINK/ADA (short); BNB/XRP/DOGE are the flat middle.
    assert proposal.target_weights == {
        "ETHUSDT": 0.2,
        "SOLUSDT": 0.2,
        "LINKUSDT": -0.2,
        "ADAUSDT": -0.2,
    }
    assert proposal.diagnostics["long_book"] == ["ETHUSDT", "SOLUSDT"]
    assert proposal.diagnostics["short_book"] == ["LINKUSDT", "ADAUSDT"]
    for middle in ("BNBUSDT", "XRPUSDT", "DOGEUSDT"):
        assert middle not in proposal.target_weights
    assert sum(proposal.target_weights.values()) == 0.0
    assert sum(abs(w) for w in proposal.target_weights.values()) == 0.8
    assert proposal.exit_policy == "scheduled daily rebalance; rank removal; risk-cap block"


def test_carry_btc_is_benchmark_context_only():
    adapter = build_adapter(XsectFundCarryAdapter)
    snapshot = carry_snapshot(
        funding_by_symbol={
            "BTCUSDT": make_funding("BTCUSDT", -0.09, parse_iso(MONDAY).date() - dt.timedelta(days=8), 9)
        }
    )
    proposal = adapter.decide(snapshot, MONDAY, MONDAY, {})
    assert proposal.rejected_symbols_with_reason["BTCUSDT"] == "benchmark_context_not_traded"
    assert "BTCUSDT" not in proposal.target_weights
    assert set(proposal.target_weights) <= set(CARRY_UNIVERSE)


def test_carry_tie_broken_by_symbol_ascending_at_short_boundary():
    adapter = build_adapter(XsectFundCarryAdapter)
    # BNB and XRP share the same rate (-1e-4): ascending (rate, symbol)
    # puts BNBUSDT before XRPUSDT on the tie; the top-two short book is
    # LINK/ADA and the tie only reorders the flat middle.
    rates = {sym: (idx - 3) * 1e-4 for idx, sym in enumerate(CARRY_UNIVERSE)}
    rates["BNBUSDT"] = rates["XRPUSDT"]
    funding = {
        sym: make_funding(sym, rate, parse_iso(MONDAY).date() - dt.timedelta(days=8), 9)
        for sym, rate in rates.items()
    }
    proposal = adapter.decide(
        FamilySnapshot(funding_settlements=funding), MONDAY, MONDAY, {}
    )
    assert proposal.diagnostics["short_book"] == ["LINKUSDT", "ADAUSDT"]
    assert set(proposal.eligible_symbols) == set(CARRY_UNIVERSE)


def test_carry_lookback_window_boundaries():
    adapter = build_adapter(XsectFundCarryAdapter)
    decision_day = parse_iso(MONDAY).date()
    # only a settlement exactly at the decision stamp: NOT usable (strictly
    # before required) -> insufficient history
    snapshot = carry_snapshot(
        funding_by_symbol={
            "ADAUSDT": [
                {
                    "funding_time_utc": MONDAY,
                    "funding_rate": -0.5,
                }
            ]
        }
    )
    proposal = adapter.decide(snapshot, MONDAY, MONDAY, {})
    assert (
        proposal.rejected_symbols_with_reason["ADAUSDT"] == "insufficient_funding_history"
    )
    # a settlement exactly 7 days before the decision IS inside the window
    boundary = to_iso(
        dt.datetime.combine(
            decision_day - dt.timedelta(days=7), dt.time(0, 0), tzinfo=dt.timezone.utc
        )
    )
    snapshot2 = carry_snapshot(
        funding_by_symbol={"ADAUSDT": [{"funding_time_utc": boundary, "funding_rate": 0.4}]}
    )
    proposal2 = adapter.decide(snapshot2, MONDAY, MONDAY, {})
    assert "ADAUSDT" in proposal2.signal_values


def test_carry_min_eligibility_data_blocked():
    adapter = build_adapter(XsectFundCarryAdapter)
    # only three universe names carry settled funding -> 3 < 4 required
    funding = {
        sym: make_funding(sym, (idx - 3) * 1e-4, parse_iso(MONDAY).date() - dt.timedelta(days=8), 9)
        for idx, sym in enumerate(CARRY_UNIVERSE[:3])
    }
    with pytest.raises(DataBlocked):
        adapter.decide(
            FamilySnapshot(funding_settlements=funding), MONDAY, MONDAY, {}
        )


def test_carry_four_eligible_still_trades():
    adapter = build_adapter(XsectFundCarryAdapter)
    funding = {
        sym: make_funding(sym, (idx - 3) * 1e-4, parse_iso(MONDAY).date() - dt.timedelta(days=8), 9)
        for idx, sym in enumerate(CARRY_UNIVERSE[:4])
    }
    proposal = adapter.decide(
        FamilySnapshot(funding_settlements=funding), MONDAY, MONDAY, {}
    )
    # ETH/SOL long (bottom), XRP/BNB short (top two of the four remaining)
    assert set(proposal.target_weights) == {
        "ETHUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "BNBUSDT",
    }
    assert proposal.target_weights == {
        "ETHUSDT": 0.2,
        "SOLUSDT": 0.2,
        "BNBUSDT": -0.2,
        "XRPUSDT": -0.2,
    }
    assert proposal.rejected_symbols_with_reason == {
        sym: "insufficient_funding_history" for sym in CARRY_UNIVERSE[4:]
    }


def test_carry_wrong_clock_refused():
    adapter = build_adapter(XsectFundCarryAdapter)
    with pytest.raises(ValueError):
        adapter.decide(carry_snapshot(), "2026-03-02T12:00:00Z", "2026-03-02T11:45:00Z", {})


def test_carry_previous_weights_passthrough():
    adapter = build_adapter(XsectFundCarryAdapter)
    previous = {"ETHUSDT": 0.2, "LINKUSDT": -0.2}
    proposal = adapter.decide(carry_snapshot(), MONDAY, MONDAY, previous)
    assert proposal.previous_weights == previous


def test_carry_identity_caps_approve_the_book():
    adapter = build_adapter(XsectFundCarryAdapter)
    proposal = adapter.decide(carry_snapshot(), MONDAY, MONDAY, {})
    entry = manifest_entry("XSECT-FUND-CARRY-7D")
    caps = risk.caps_from_identity_params(
        "XSECT-FUND-CARRY-7D", entry["score_affecting_parameters"]
    )
    assert caps.target_gross == 0.8
    assert caps.hard_gross_cap == 1.0
    assert caps.hard_abs_net_cap == 0.1
    assert caps.max_abs_weight == 0.2
    approved, block = risk.check_and_apply(proposal.target_weights, caps)
    assert not block.blocked
    assert approved == proposal.target_weights
