"""V9 multi-family signal unit tests (A3): hand fixtures + PIT invariance.

Covers the three new signal families (research.v9_ts_trend,
research.v9_residual_mr, research.v9_vol_shock) plus their runner wiring:

* family math on tiny crafted panels with known expected weights
  (both-sides / single-sided / flat books, dead-zone edges, beta
  fallback, shock threshold edge, control inversion),
* no-lookahead invariance: targets at cutoff T are unchanged by ANY
  perturbation of post-cutoff data (and of a bar stamped exactly AT T --
  the families read strictly-before-cutoff only),
* runner wiring: --signal-family choices, V9 provenance generation
  mapping + v9p provenance exemptions, warmup floors, dispatcher routing
  with derived diagnostics rows and fail-closed unknown-family abort.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research import portfolio_runner as pr  # noqa: E402
from research.provenance_v6p import (  # noqa: E402
    ATTESTATION_FILENAME,
    BASELINE_FILENAME,
    _provenance_exempt,
)
from research.v9_residual_mr import (  # noqa: E402
    compute_targets as residual_mr_targets,
    estimate_beta,
    daily_returns as residual_daily_returns,
    residual_z_scores,
)
from research.v9_ts_trend import (  # noqa: E402
    compute_targets as ts_trend_targets,
    trailing_return,
    trend_scores,
)
from research.v9_vol_shock import (  # noqa: E402
    aggregate_daily_dollar_volume,
    compute_targets as vol_shock_targets,
    select_shocked_universe,
    shock_ratios,
)

DAY = 86_400_000_000_000
CUTOFF = 40 * DAY


def closes_from(values: list[float], start_index: int = 0) -> list[tuple[int, float]]:
    return [((start_index + i) * DAY, v) for i, v in enumerate(values)]


# --------------------------------------------------------------------------- #
# TS-TREND hand fixtures
# --------------------------------------------------------------------------- #
def ts_panel() -> dict[str, list[tuple[int, float]]]:
    """Day-indexed closes; cutoff = day 40 => ref leg day 26, last day 39."""
    return {
        "AAAUSDT": closes_from([100.0] * 27 + [110.0, 120.0, 130.0, 140.0]),
        "BBBUSDT": closes_from([100.0] * 27 + [102.0, 104.0, 107.0, 110.0]),
        "CCCUSDT": closes_from([100.0] * 40),
        "DDDUSDT": closes_from([100.0] * 27 + [90.0, 80.0, 70.0, 60.0]),
        "EEEUSDT": closes_from([100.0] * 27 + [95.0, 92.0, 91.0, 90.0]),
        "FFFUSDT": closes_from([100.0] * 40),
    }


def test_ts_trend_basic_both_sides_equal_weight():
    out = ts_trend_targets(
        daily_closes=ts_panel(), signal_cutoff_ns=CUTOFF,
        traded_symbols=list(ts_panel()),
    )
    assert out == {"status": "OK",
                   "longs": [["AAAUSDT", 0.2], ["BBBUSDT", 0.2]],
                   "shorts": [["DDDUSDT", -0.2], ["EEEUSDT", -0.2]]}
    scores = trend_scores(daily_closes=ts_panel(), signal_cutoff_ns=CUTOFF,
                          traded_symbols=["AAAUSDT", "FFFUSDT"])
    assert scores["AAAUSDT"] == pytest.approx(0.4, abs=1e-12)
    assert scores["FFFUSDT"] == pytest.approx(0.0, abs=1e-12)


def test_ts_trend_dead_zone_edges():
    panel = {
        "UPUSDT": closes_from([100.0] * 27 + [103.0, 104.0, 105.0, 106.0]),
        "DNUSDT": closes_from([100.0] * 27 + [97.0, 96.0, 95.0, 94.0]),
        "FLATUSDT": closes_from([100.0] * 40),
    }
    syms = list(panel)
    zero_dz = ts_trend_targets(daily_closes=panel, signal_cutoff_ns=CUTOFF,
                               traded_symbols=syms)
    assert {s for s, _ in zero_dz["longs"]} == {"UPUSDT"}
    assert {s for s, _ in zero_dz["shorts"]} == {"DNUSDT"}
    assert [s for s, _ in (*zero_dz["longs"], *zero_dz["shorts"])].count(
        "FLATUSDT") == 0

    # dead_zone=0.05: +6% still long, -6% still short; exactly-zero stays
    # flat under strict inequalities on BOTH sides.
    gated = ts_trend_targets(daily_closes=panel, signal_cutoff_ns=CUTOFF,
                             traded_symbols=syms, dead_zone=0.05)
    assert {s for s, _ in gated["longs"]} == {"UPUSDT"}
    assert {s for s, _ in gated["shorts"]} == {"DNUSDT"}

    narrow = ts_trend_targets(
        daily_closes={
            "TINYUPUSDT": closes_from([100.0] * 27
                                       + [101.0, 102.0, 103.0, 104.0]),
            "FLATUSDT": closes_from([100.0] * 40),
        },
        signal_cutoff_ns=CUTOFF,
        traded_symbols=["TINYUPUSDT", "FLATUSDT"],
        dead_zone=0.05,
    )
    assert narrow == {"status": "OK", "longs": [], "shorts": []}


def test_ts_trend_single_sided_uses_full_gross():
    panel = {
        "UP1USDT": closes_from([100.0] * 27 + [110.0, 120.0, 130.0, 140.0]),
        "UP2USDT": closes_from([100.0] * 27 + [102.0, 104.0, 107.0, 110.0]),
        "FLATUSDT": closes_from([100.0] * 40),
    }
    out = ts_trend_targets(daily_closes=panel, signal_cutoff_ns=CUTOFF,
                           traded_symbols=list(panel))
    assert out == {"status": "OK",
                   "longs": [["UP1USDT", 0.4], ["UP2USDT", 0.4]],
                   "shorts": []}
    solo = ts_trend_targets(
        daily_closes={**panel, "UP2USDT": closes_from([100.0] * 40)},
        signal_cutoff_ns=CUTOFF,
        traded_symbols=["UP1USDT", "UP2USDT", "FLATUSDT"],
    )
    assert solo == {"status": "OK", "longs": [["UP1USDT", 0.8]],
                    "shorts": []}


def test_ts_trend_none_active_flat_and_empty_universe_skip():
    panel = {f"S{i}USDT": closes_from([100.0] * 40) for i in range(3)}
    out = ts_trend_targets(daily_closes=panel, signal_cutoff_ns=CUTOFF,
                           traded_symbols=list(panel))
    assert out == {"status": "OK", "longs": [], "shorts": []}
    skipped = ts_trend_targets(daily_closes={}, signal_cutoff_ns=CUTOFF,
                               traded_symbols=[])
    assert skipped == {"status": "SKIP_INCOMPLETE",
                       "reason_code": "v9_ts_trend_empty_universe"}


def test_ts_trend_insufficient_history_stays_inactive():
    panel = {
        "LATEUSDT": closes_from([50.0, 60.0, 70.0], start_index=37),
        "UPUSDT": closes_from([100.0] * 27 + [110.0, 120.0, 130.0, 140.0]),
    }
    out = ts_trend_targets(daily_closes=panel, signal_cutoff_ns=CUTOFF,
                           traded_symbols=list(panel))
    assert out == {"status": "OK", "longs": [["UPUSDT", 0.8]], "shorts": []}
    assert trend_scores(daily_closes=panel, signal_cutoff_ns=CUTOFF,
                        traded_symbols=["LATEUSDT"])["LATEUSDT"] is None
    # Strictly-before semantics: a close stamped exactly AT the cutoff is
    # invisible to the trailing computation (the 999 print never enters).
    assert trailing_return(
        [(10 * DAY, 100.0), (19 * DAY, 150.0), (20 * DAY, 999.0)],
        cutoff_ns=20 * DAY, lookback_days=5) == pytest.approx(0.5)


def test_ts_trend_control_inversion_swaps_sides():
    base = ts_trend_targets(daily_closes=ts_panel(),
                            signal_cutoff_ns=CUTOFF,
                            traded_symbols=list(ts_panel()))
    ctrl = ts_trend_targets(daily_closes=ts_panel(),
                            signal_cutoff_ns=CUTOFF,
                            traded_symbols=list(ts_panel()), reverse=True)
    assert {s for s, _ in ctrl["longs"]} == {s for s, _ in base["shorts"]}
    assert {s for s, _ in ctrl["shorts"]} == {s for s, _ in base["longs"]}
    assert all(w > 0 for _, w in ctrl["longs"])
    assert all(w < 0 for _, w in ctrl["shorts"])


# --------------------------------------------------------------------------- #
# No-lookahead invariance (all three families)
# --------------------------------------------------------------------------- #
def test_ts_trend_no_lookahead_invariance():
    base_panel = ts_panel()
    base = ts_trend_targets(daily_closes=base_panel,
                            signal_cutoff_ns=CUTOFF,
                            traded_symbols=list(base_panel))
    mutated = {sym: list(series) for sym, series in base_panel.items()}
    # wild post-cutoff moves appended after the cutoff...
    for sym in mutated:
        mutated[sym].extend([
            ((41 + i) * DAY, 999.0 if i % 2 else 1.0) for i in range(10)
        ])
    # ...AND a perturbation stamped exactly AT the cutoff instant.
    mutated["AAAUSDT"] = [
        (ts, px) for ts, px in mutated["AAAUSDT"] if ts != CUTOFF
    ] + [(CUTOFF, 12345.0)]
    after = ts_trend_targets(daily_closes=mutated, signal_cutoff_ns=CUTOFF,
                             traded_symbols=list(mutated))
    assert after == base


def test_residual_mr_no_lookahead_invariance():
    panel = residual_fixture_panel()
    base = residual_mr_targets(
        daily_closes=panel, benchmark_closes=panel["BTCUSDT"],
        signal_cutoff_ns=CUTOFF, traded_symbols=["SSUSDT", "TTUSDT"])
    mutated = {sym: list(series) for sym, series in panel.items()}
    for sym in mutated:
        mutated[sym].extend([
            ((41 + i) * DAY, 777.0 if i % 2 else 3.0) for i in range(12)
        ])
    mutated["BTCUSDT"] = [
        (ts, px) for ts, px in mutated["BTCUSDT"] if ts != CUTOFF
    ] + [(CUTOFF, 555.0)]
    after = residual_mr_targets(
        daily_closes=mutated, benchmark_closes=mutated["BTCUSDT"],
        signal_cutoff_ns=CUTOFF, traded_symbols=["SSUSDT", "TTUSDT"])
    assert after == base


def test_vol_shock_no_lookahead_invariance():
    panel, volumes = vol_shock_fixture()
    base = vol_shock_targets(
        daily_closes=panel, dollar_volume=volumes,
        signal_cutoff_ns=CUTOFF, traded_symbols=list(panel))
    mutated_panel = {sym: list(series) for sym, series in panel.items()}
    mutated_volumes = {sym: list(series) for sym, series in volumes.items()}
    for sym in mutated_panel:
        mutated_panel[sym].extend([
            ((41 + i) * DAY, 900.0 if i % 2 else 2.0) for i in range(8)
        ])
    for sym in mutated_volumes:
        mutated_volumes[sym].extend(
            [((41 + i) * DAY, 10**9) for i in range(8)])
    mutated_volumes["SHKUSDT"].append((CUTOFF, 42.0))
    after = vol_shock_targets(
        daily_closes=mutated_panel, dollar_volume=mutated_volumes,
        signal_cutoff_ns=CUTOFF, traded_symbols=list(mutated_panel))
    assert after == base


# --------------------------------------------------------------------------- #
# RESIDUAL-MR hand fixtures
# --------------------------------------------------------------------------- #
def residual_fixture_panel() -> dict[str, list[tuple[int, float]]]:
    """BTC alternating +-1%; SS/TT carry +-0.002 residuals on the last 5."""
    btc = [100.0]
    ss, tt = [100.0], [100.0]
    for i in range(1, 31):
        r = 0.01 if i % 2 else -0.01
        e = 0.002 if i >= 26 else 0.0
        btc.append(btc[-1] * (1 + r))
        ss.append(ss[-1] * (1 + r + e))
        tt.append(tt[-1] * (1 + r - e))
    return {
        "BTCUSDT": closes_from(btc),
        "SSUSDT": closes_from(ss),
        "TTUSDT": closes_from(tt),
    }


def test_residual_mr_z_selection_and_slot_weights():
    panel = residual_fixture_panel()
    out = residual_mr_targets(
        daily_closes=panel, benchmark_closes=panel["BTCUSDT"],
        signal_cutoff_ns=CUTOFF, traded_symbols=["SSUSDT", "TTUSDT"])
    # SS has positive residual momentum (winner) -> SHORT; TT fades up.
    assert out == {"status": "OK", "longs": [["TTUSDT", 0.2]],
                   "shorts": [["SSUSDT", -0.2]]}
    z = residual_z_scores(
        daily_closes=panel, benchmark_closes=panel["BTCUSDT"],
        signal_cutoff_ns=CUTOFF, traded_symbols=["SSUSDT", "TTUSDT"])
    assert z["SSUSDT"]["n_obs"] == 30
    assert z["SSUSDT"]["beta"] == pytest.approx(1.0, abs=0.05)
    assert z["SSUSDT"]["z"] == pytest.approx(2.4494897428, abs=0.5)
    assert z["TTUSDT"]["z"] == pytest.approx(-2.4494897428, abs=0.5)


def test_residual_mr_exact_beta_and_fallbacks():
    btc = [100.0]
    for i in range(1, 26):
        btc.append(btc[-1] * (1 + (0.01 if i % 2 else -0.01)))
    double = [100.0]
    for i in range(1, len(btc)):
        r = btc[i] / btc[i - 1] - 1.0
        double.append(double[-1] * (1 + 2 * r))
    panel = {"BTCUSDT": closes_from(btc), "DBLUSDT": closes_from(double)}
    beta, n_obs = estimate_beta(
        residual_daily_returns(panel["DBLUSDT"], cutoff_ns=CUTOFF),
        residual_daily_returns(panel["BTCUSDT"], cutoff_ns=CUTOFF),
    )
    assert beta == pytest.approx(2.0, abs=1e-9)
    assert n_obs == 25

    short_history = {"BTCUSDT": closes_from(btc),
                     "TENUSDT": closes_from(double[:11])}
    beta10, n10 = estimate_beta(
        residual_daily_returns(short_history["TENUSDT"], cutoff_ns=CUTOFF),
        residual_daily_returns(short_history["BTCUSDT"], cutoff_ns=CUTOFF),
    )
    assert (beta10, n10) == (1.0, 10)

    flat_btc = {"BTCUSDT": closes_from([100.0] * 30)}
    flat_sym = {"SYMUSDT": closes_from([100.0] * 29 + [101.0])}
    beta_flat, _ = estimate_beta(
        residual_daily_returns(flat_sym["SYMUSDT"], cutoff_ns=CUTOFF),
        residual_daily_returns(flat_btc["BTCUSDT"], cutoff_ns=CUTOFF),
    )
    assert beta_flat == 1.0  # degenerate benchmark variance fallback


def test_residual_mr_zero_dispersion_ineligible():
    const = {
        "BTCUSDT": closes_from([100.0] * 31),
        "FLATUSDT": closes_from([100.0] * 31),
    }
    # All aligned returns are exactly zero -> residuals constant -> std 0.
    z = residual_z_scores(daily_closes=const,
                          benchmark_closes=const["BTCUSDT"],
                          signal_cutoff_ns=CUTOFF,
                          traded_symbols=["FLATUSDT"])
    assert z["FLATUSDT"]["z"] is None
    out = residual_mr_targets(daily_closes=const,
                              benchmark_closes=const["BTCUSDT"],
                              signal_cutoff_ns=CUTOFF,
                              traded_symbols=["FLATUSDT"])
    assert out == {"status": "OK", "longs": [], "shorts": []}


def test_residual_mr_fewer_eligible_scale_down_proportionally():
    panel = residual_fixture_panel()
    # Third eligible symbol with mild positive z ranks between SS and TT.
    mild = [100.0]
    btc = panel["BTCUSDT"]
    for i in range(1, len(btc)):
        r = btc[i][1] / btc[i - 1][1] - 1.0
        e = 0.001 if i >= 28 else 0.0
        mild.append(mild[-1] * (1 + r + e))
    trio = {**panel, "MMUSDT": closes_from(mild)}
    out = residual_mr_targets(
        daily_closes=trio, benchmark_closes=trio["BTCUSDT"],
        signal_cutoff_ns=CUTOFF,
        traded_symbols=["SSUSDT", "TTUSDT", "MMUSDT"])
    longs = [s for s, _ in out["longs"]]
    shorts = [s for s, _ in out["shorts"]]
    assert len(longs) + len(shorts) == 3
    assert not set(longs) & set(shorts)
    assert all(abs(w) == pytest.approx(0.2) for _, w in
               (*out["longs"], *out["shorts"]))
    total_gross = sum(abs(w) for _, w in (*out["longs"], *out["shorts"]))
    assert total_gross == pytest.approx(0.6)  # proportional scale-down


def test_residual_mr_missing_benchmark_fails_closed():
    panel = residual_fixture_panel()
    out = residual_mr_targets(daily_closes=panel, benchmark_closes=[],
                              signal_cutoff_ns=CUTOFF,
                              traded_symbols=["SSUSDT", "TTUSDT"])
    assert out == {"status": "SKIP_INCOMPLETE",
                   "reason_code": "v9_residual_mr_missing_benchmark"}


def test_residual_mr_control_inverts_z_sign():
    panel = residual_fixture_panel()
    base = residual_mr_targets(daily_closes=panel,
                               benchmark_closes=panel["BTCUSDT"],
                               signal_cutoff_ns=CUTOFF,
                               traded_symbols=["SSUSDT", "TTUSDT"])
    ctrl = residual_mr_targets(daily_closes=panel,
                               benchmark_closes=panel["BTCUSDT"],
                               signal_cutoff_ns=CUTOFF,
                               traded_symbols=["SSUSDT", "TTUSDT"],
                               reverse=True)
    assert {s for s, _ in ctrl["longs"]} == {s for s, _ in base["shorts"]}
    assert {s for s, _ in ctrl["shorts"]} == {s for s, _ in base["longs"]}


# --------------------------------------------------------------------------- #
# VOL-SHOCK hand fixtures
# --------------------------------------------------------------------------- #
def vol_shock_fixture():
    """SHK shocked (dv spike on ref day) with rising price; LOSER shocked
    with falling price; MID/ZZZ carry no dollar-volume history at all."""
    def daily_closes(values):
        return closes_from(values)

    bars = []
    for day in range(1, 30):
        vol = 400.0 if day == 29 else 100.0
        bars.append((day * DAY - 12 * 3600 * 10**9, 100.0, 100.0, 100.0,
                     100.0, vol))
    panel = {
        "SHKUSDT": daily_closes([100.0] * 37 + [110.0, 121.0, 133.1]),
        "LOSERUSDT": daily_closes([100.0] * 37 + [90.0, 81.0, 72.9]),
        "MIDUSDT": daily_closes([100.0] * 40),
        "ZZZUSDT": daily_closes([100.0] * 39 + [300.0]),
    }
    shocked_dv = aggregate_daily_dollar_volume(bars)
    volumes = {"SHKUSDT": shocked_dv, "LOSERUSDT": shocked_dv}
    return panel, volumes


def test_vol_shock_shock_ratio_math_and_threshold_edge():
    bars = []
    for day in range(1, 24):
        vol = 150.0 if day == 23 else 100.0
        bars.append((day * DAY - 12 * 3600 * 10**9, 100.0, 100.0, 100.0,
                     100.0, vol))
    dv = aggregate_daily_dollar_volume(bars)
    ratios = shock_ratios(dollar_volume={"XUSDT": dv},
                          signal_cutoff_ns=24 * DAY)
    # ref day = day 23 (last strictly before cutoff); baseline excludes it.
    assert ratios["XUSDT"] == pytest.approx(1.5)
    assert select_shocked_universe(ratios) == ["XUSDT"]  # >= 1.5 included
    out = vol_shock_targets(
        daily_closes={"AUSDT": closes_from([100.0] * 30)},
        dollar_volume={"AUSDT": [(d * DAY, 100.0) for d in range(1, 23)]
                       + [(23 * DAY, 149.0)]},
        signal_cutoff_ns=24 * DAY, traded_symbols=["AUSDT"])
    assert out == {"status": "OK", "longs": [], "shorts": []}


def test_vol_shock_top6_bottom6_control_with_eight_symbols():
    def series(ret: float) -> list[tuple[int, float]]:
        values = [100.0] * 28
        values += [100.0 * (1 + ret * k / 3) for k in range(1, 4)]
        return closes_from(values)

    shocks = {"AUSDT": 2.00, "BUSDT": 1.90, "CUSDT": 1.80, "DUSDT": 1.70,
              "EUSDT": 1.60, "FUSDT": 1.55, "GUSDT": 1.52, "HUSDT": 1.40}
    returns = {"AUSDT": 0.10, "BUSDT": 0.09, "CUSDT": -0.08, "DUSDT": 0.07,
               "EUSDT": -0.06, "FUSDT": 0.05, "GUSDT": 0.04, "HUSDT": 0.50}
    panel = {sym: series(returns[sym]) for sym in shocks}
    dv = {sym: [(d * DAY, 100.0) for d in range(1, 22)]
          + [(22 * DAY, 100.0 * ratio)] for sym, ratio in shocks.items()}
    kwargs = dict(signal_cutoff_ns=31 * DAY, traded_symbols=list(shocks))

    base = vol_shock_targets(daily_closes=panel, dollar_volume=dv, **kwargs)
    universe = select_shocked_universe(shocks)
    assert universe == ["AUSDT", "BUSDT", "CUSDT", "DUSDT", "EUSDT", "FUSDT"]
    # Long the 2 highest 3d returns among shocked, short the 2 lowest.
    assert [s for s, _ in base["longs"]] == ["AUSDT", "BUSDT"]
    assert [s for s, _ in base["shorts"]] == ["CUSDT", "EUSDT"]
    assert all(w == pytest.approx(0.2) for _, w in base["longs"])
    assert all(w == pytest.approx(-0.2) for _, w in base["shorts"])

    ctrl = vol_shock_targets(daily_closes=panel, dollar_volume=dv,
                             reverse=True, **kwargs)
    # Bottom-6 by shock, still gated >= 1.5: drops HUSDT (1.40).
    assert select_shocked_universe(shocks, reverse=True) == \
        ["GUSDT", "FUSDT", "EUSDT", "DUSDT", "CUSDT"]
    assert [s for s, _ in ctrl["longs"]] == ["DUSDT", "FUSDT"]
    assert [s for s, _ in ctrl["shorts"]] == ["CUSDT", "EUSDT"]


def test_vol_shock_weights_four_slots_and_fewer_case():
    panel, volumes = vol_shock_fixture()
    out = vol_shock_targets(daily_closes=panel, dollar_volume=volumes,
                            signal_cutoff_ns=CUTOFF,
                            traded_symbols=list(panel))
    # Exactly two shocked candidates: continuation long + losing short;
    # ZZZ/MID carry no usable dollar-volume history.
    assert out == {"status": "OK", "longs": [["SHKUSDT", 0.2]],
                   "shorts": [["LOSERUSDT", -0.2]]}

    single = vol_shock_targets(
        daily_closes={"SOLOUSDT": closes_from([100.0] * 29 + [130.0])},
        dollar_volume={"SOLOUSDT": [(d * DAY, 100.0) for d in range(1, 21)]
                       + [(21 * DAY, 500.0)]},
        signal_cutoff_ns=30 * DAY, traded_symbols=["SOLOUSDT"])
    assert single == {"status": "OK", "longs": [["SOLOUSDT", 0.2]],
                      "shorts": []}


def test_vol_shock_aggregates_dollar_volume_per_utc_day():
    bars = [
        (0 * DAY + 1 * 3600 * 10**9, 10.0, 10.0, 10.0, 10.0, 2.0),
        (0 * DAY + 2 * 3600 * 10**9, 20.0, 20.0, 20.0, 20.0, 3.0),
        (1 * DAY + 1 * 3600 * 10**9, 5.0, 5.0, 5.0, 5.0, 10.0),
    ]
    dv = aggregate_daily_dollar_volume(bars)
    assert dv == [(0 * DAY, 10.0 * 2.0 + 20.0 * 3.0), (1 * DAY, 50.0)]
    assert aggregate_daily_dollar_volume([]) == []


# --------------------------------------------------------------------------- #
# Runner wiring: choices, provenance generation, warmup floors, dispatcher
# --------------------------------------------------------------------------- #
@pytest.fixture()
def family_env(monkeypatch):
    saved = {key: os.environ.get(key)
             for key in (pr.SIGNAL_FAMILY_ENV, pr.CONTROL_MOMENTUM_ENV)}
    yield monkeypatch
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_signal_family_choices_include_v9_families():
    for family in ("ts_trend", "residual_mr", "vol_shock"):
        assert family in pr.SIGNAL_FAMILY_CHOICES
        assert family in pr.STRATEGY_KIND_CHOICES
        assert pr.PROVENANCE_GENERATIONS[family] == \
            Path("research/audits/v9p")
    args = pr.build_parser().parse_args(["--signal-family", "vol_shock"])
    assert args.signal_family == "vol_shock"
    with pytest.raises(SystemExit):
        pr.build_parser().parse_args(["--signal-family", "bogus"])


def test_provenance_exempt_declares_v9p_baseline_and_attestation():
    exempt = _provenance_exempt(REPO)
    assert str(Path("research/audits/v9p") / BASELINE_FILENAME) in exempt
    assert str(Path("research/audits/v9p") / ATTESTATION_FILENAME) in exempt


def test_v9_warmup_floors(family_env):
    family_env.delenv(pr.SIGNAL_FAMILY_ENV, raising=False)
    assert pr.effective_warmup_days(3) == 10  # default behavior preserved
    family_env.setenv(pr.SIGNAL_FAMILY_ENV, "ts_trend")
    assert pr.effective_warmup_days(14) == 21
    assert pr.effective_warmup_days(3) == 21
    family_env.setenv(pr.SIGNAL_FAMILY_ENV, "residual_mr")
    assert pr.effective_warmup_days(3) == 35
    family_env.setenv(pr.SIGNAL_FAMILY_ENV, "vol_shock")
    assert pr.effective_warmup_days(3) == 28


def _dispatch_call(panel, *, volume_provider=None, **kwargs):
    base = lambda **_k: {"status": "BASE_NEVER_CALLED"}  # noqa: E731
    wrapped = pr._signal_family_dispatch(base, funding_bundles_dir="/unused",
                                         volume_provider=volume_provider)
    payload = {
        "daily_closes": panel,
        "signal_cutoff_ns": CUTOFF,
        "lookback_days": kwargs.pop("lookback", 14),
        "reverse": kwargs.pop("reverse", False),
        **kwargs,
    }
    return wrapped(**payload)


def test_dispatcher_routes_ts_trend_with_diagnostics(family_env):
    family_env.setenv(pr.SIGNAL_FAMILY_ENV, "ts_trend")
    panel = ts_panel()
    out = _dispatch_call(panel)
    row = out.pop(pr.V9_DIAGNOSTICS_KEY)
    assert out == {"status": "OK",
                   "longs": [["AAAUSDT", 0.2], ["BBBUSDT", 0.2]],
                   "shorts": [["DDDUSDT", -0.2], ["EEEUSDT", -0.2]]}
    assert row["derived_diagnostics"] is True
    assert row["family"] == "ts_trend"
    assert row["lookback_days"] == 14
    assert row["per_symbol"]["AAAUSDT"]["trailing_return"] == \
        pytest.approx(0.4, abs=1e-12)
    assert row["skipped_reason"] is None
    assert [s for s, _ in row["selected_longs"]] == ["AAAUSDT", "BBBUSDT"]


def test_dispatcher_routes_residual_mr_and_vol_shock(family_env):
    family_env.setenv(pr.SIGNAL_FAMILY_ENV, "residual_mr")
    panel = residual_fixture_panel()
    out = _dispatch_call(panel)
    row = out.pop(pr.V9_DIAGNOSTICS_KEY)
    assert out == {"status": "OK", "longs": [["TTUSDT", 0.2]],
                   "shorts": [["SSUSDT", -0.2]]}
    assert row["family"] == "residual_mr"
    assert row["per_symbol"]["SSUSDT"]["n_obs"] == 30
    assert row["per_symbol"]["SSUSDT"]["z"] > 0 > \
        row["per_symbol"]["TTUSDT"]["z"]

    family_env.setenv(pr.SIGNAL_FAMILY_ENV, "vol_shock")
    vs_panel, volumes = vol_shock_fixture()

    def provider(symbols, start_ns, end_ns):
        return {
            sym: [(t, v) for t, v in (volumes.get(sym) or [])
                  if start_ns <= t <= end_ns]
            for sym in symbols
        }

    out_vs = _dispatch_call(vs_panel, volume_provider=provider)
    row_vs = out_vs.pop(pr.V9_DIAGNOSTICS_KEY)
    assert out_vs == {"status": "OK", "longs": [["SHKUSDT", 0.2]],
                      "shorts": [["LOSERUSDT", -0.2]]}
    assert row_vs["family"] == "vol_shock"
    assert row_vs["per_symbol"]["SHKUSDT"]["shock_ratio"] == \
        pytest.approx(4.0)
    assert row_vs["per_symbol"]["ZZZUSDT"]["shock_ratio"] is None


def test_unknown_family_fails_closed(family_env):
    family_env.setenv(pr.SIGNAL_FAMILY_ENV, "totally_bogus_family")
    with pytest.raises(pr.RunnerError):
        _dispatch_call(ts_panel())
    dummy_engine = {
        "build_daily_panel": lambda **k: {},
        "run_shared_capital_backtest": lambda **k: {},
        "compute_target_weights": lambda **k: {},
    }
    from datetime import datetime, timezone

    start = datetime(2026, 1, 5, tzinfo=timezone.utc)
    with pytest.raises(pr.RunnerError):
        pr.execute_experiment(
            engine=dummy_engine, traded_symbols=["AAAUSDT"],
            benchmark_symbol="BTCUSDT", window_start=start,
            window_end=start, lookback_days=14, reverse=False, folds=1)


def test_momentum_default_survives_unset_family_env(family_env):
    family_env.delenv(pr.SIGNAL_FAMILY_ENV, raising=False)
    seen = {}

    def base(**kwargs):
        seen.update(kwargs)
        return {"status": "OK", "longs": [], "shorts": []}

    wrapped = pr._signal_family_dispatch(base, funding_bundles_dir="/unused")
    out = wrapped(signal_cutoff_ns=CUTOFF, lookback_days=3,
                  reverse=False, daily_closes={})
    assert out["status"] == "OK"
    assert seen["signal_cutoff_ns"] == CUTOFF
