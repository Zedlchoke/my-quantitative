"""H-XSECT-FUNDING-PRICE-DIVERGENCE-v1 signal tests (frozen semantics, PLAN §16.2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.funding_price_divergence import (  # noqa: E402
    build_divergence_traded,
    compute_target_weights_funding_price_divergence as div,
)

DAY_MS = 86_400_000


@pytest.fixture()
def bundles(tmp_path):
    def _write(rows_by_symbol):
        root = tmp_path / "funding"
        for sym, rows in rows_by_symbol.items():
            d = root / sym
            d.mkdir(parents=True, exist_ok=True)
            (d / "funding.json").write_text(json.dumps({
                "requested_start_ms": min(t for t, _ in rows),
                "requested_end_ms": max(t for t, _ in rows),
                "rows": [{"fundingTime": str(t), "fundingRate": str(r)}
                         for t, r in sorted(rows)],
            }))
        return root

    return _write


T0 = 1_704_067_200_000  # 2024-01-01T00:00Z (ms)
T1 = T0 + DAY_MS
T2 = T0 + 2 * DAY_MS
CUTOFF_NS = T2 * 1_000_000

SKIP = {"status": "SKIP_INCOMPLETE",
        "reason_code": "divergence_panel_incomplete"}


def _closes(pairs_ms_px):
    """[(ts_ms, px)] -> {sym handled by caller} list of (ns, px) bars."""
    return [(t * 1_000_000, px) for t, px in pairs_ms_px]


def _panel_prices():
    """Hand-checkable panel: returns A +10%, B +5%, C 0%, D -5%, E -10%."""
    base = [(T0, 100.0), (T1, None)]
    rets = {"AUSDT": 110.0, "BUSDT": 105.0, "CUSDT": 100.0,
            "DUSDT": 95.0, "EUSDT": 90.0}
    return {s: _closes([(T0, 100.0), (T1, px)]) for s, px in rets.items()}


def _flat_funding(rate):
    return [(T0, rate), (T1, rate), (T2, rate)]


def test_rank_math_selection_and_weights(bundles):
    syms = ["AUSDT", "BUSDT", "CUSDT", "DUSDT", "EUSDT"]
    root = bundles({s: _flat_funding(0.0001 * i)
                    for i, s in enumerate(syms, start=1)})
    res = div(signal_cutoff_ns=CUTOFF_NS, price_lookback_days=1,
              funding_bundles_dir=root, daily_closes=_panel_prices(),
              traded_symbols=syms)
    assert res["status"] == "OK"
    # price pct: E .2, D .4, C .6, B .8, A 1.0; funding pct: A .2 .. E 1.0
    # score = p_pct - f_pct: A .8, B .4, C 0, D -.4, E -.8
    assert res["longs"] == [["BUSDT", pytest.approx(0.2)],
                            ["AUSDT", pytest.approx(0.2)]]
    assert res["shorts"] == [["EUSDT", pytest.approx(-0.2)],
                             ["DUSDT", pytest.approx(-0.2)]]
    book = res["longs"] + res["shorts"]
    assert abs(sum(abs(w) for _, w in book) - 0.80) < 1e-9
    assert abs(sum(w for _, w in book)) < 1e-9
    assert "CUSDT" not in {s for s, _ in book}


def test_pit_future_bar_and_future_settlement_excluded(bundles):
    syms = ["AUSDT", "BUSDT", "CUSDT", "DUSDT", "EUSDT"]
    funding = {s: _flat_funding(0.0001 * i) for i, s in enumerate(syms, start=1)}
    funding["EUSDT"].append((T0 + 10 * DAY_MS, -0.9999))  # future settlement
    root = bundles(funding)
    prices = _panel_prices()
    prices["DUSDT"].append(((T0 + 3 * DAY_MS) * 1_000_000, 1900.0))  # future bar
    res = div(signal_cutoff_ns=CUTOFF_NS, price_lookback_days=1,
              funding_bundles_dir=root, daily_closes=prices,
              traded_symbols=syms)
    # Uncontaminated answer must survive: a leak would put DUSDT long-side or
    # drop EUSDT out of the shorts entirely.
    assert res["longs"] == [["BUSDT", pytest.approx(0.2)],
                            ["AUSDT", pytest.approx(0.2)]]
    assert res["shorts"] == [["EUSDT", pytest.approx(-0.2)],
                             ["DUSDT", pytest.approx(-0.2)]]


def test_missing_input_skips_whole_panel(bundles):
    good_fund = {s: _flat_funding(0.0001 * i)
                 for i, s in enumerate(["AUSDT", "BUSDT", "CUSDT", "DUSDT"], 1)}
    prices = {s: _closes([(T0, 100.0), (T1, 101.0)])
              for s in good_fund}

    # (a) missing funding bundle file for one symbol
    res = div(signal_cutoff_ns=T1 * 1_000_000, price_lookback_days=1,
              funding_bundles_dir=bundles(good_fund), daily_closes=prices,
              traded_symbols=list(good_fund) + ["ZUSDT"])
    assert res == SKIP

    root = bundles(good_fund)

    # (b) symbol missing from daily_closes
    res = div(signal_cutoff_ns=T1 * 1_000_000, price_lookback_days=1,
              funding_bundles_dir=root, daily_closes={},
              traded_symbols=list(good_fund))
    assert res == SKIP

    # (c) insufficient completed bars: lookback 3 needs 4 closes, panel has 2
    res = div(signal_cutoff_ns=T1 * 1_000_000, price_lookback_days=3,
              funding_bundles_dir=root, daily_closes=prices,
              traded_symbols=list(good_fund))
    assert res == SKIP

    # (d) zero settled rows inside the funding window
    stale = {s: [(T0 - 30 * DAY_MS, 0.0001)] for s in good_fund}
    res = div(signal_cutoff_ns=T1 * 1_000_000, price_lookback_days=1,
              funding_bundles_dir=bundles(stale), daily_closes=prices,
              traded_symbols=list(good_fund))
    assert res == SKIP

    # (e) fewer than 4 symbols cannot form 2x2 legs
    res = div(signal_cutoff_ns=T1 * 1_000_000, price_lookback_days=1,
              funding_bundles_dir=root,
              daily_closes={k: v for k, v in list(prices.items())[:2]},
              traded_symbols=["AUSDT", "BUSDT"])
    assert res == SKIP


def test_reverse_swaps_sides_with_sign_flip(bundles):
    syms = ["AUSDT", "BUSDT", "CUSDT", "DUSDT", "EUSDT"]
    root = bundles({s: _flat_funding(0.0001 * i)
                    for i, s in enumerate(syms, start=1)})
    kw = dict(price_lookback_days=1, funding_bundles_dir=root,
              daily_closes=_panel_prices(), traded_symbols=syms)
    fwd = div(signal_cutoff_ns=CUTOFF_NS, **kw)
    rev = div(signal_cutoff_ns=CUTOFF_NS, reverse=True, **kw)
    assert {s for s, _ in fwd["longs"]} == {s for s, _ in rev["shorts"]}
    assert {s for s, _ in fwd["shorts"]} == {s for s, _ in rev["longs"]}
    f_long, r_short = dict(fwd["longs"]), dict(rev["shorts"])
    for s in f_long:
        assert r_short[s] == pytest.approx(-f_long[s])   # sign flip end-to-end


def test_weight_normalization_rescales_to_target_gross(bundles):
    syms = ["AUSDT", "BUSDT", "CUSDT", "DUSDT", "EUSDT"]
    root = bundles({s: _flat_funding(0.0001 * i)
                    for i, s in enumerate(syms, start=1)})
    res = div(signal_cutoff_ns=CUTOFF_NS, price_lookback_days=1,
              funding_bundles_dir=root, daily_closes=_panel_prices(),
              traded_symbols=syms, target_gross=0.40)
    book = res["longs"] + res["shorts"]
    assert abs(sum(abs(w) for _, w in book) - 0.40) < 1e-9
    assert all(abs(abs(w) - 0.10) < 1e-9 for _, w in book)


def test_tie_determinism_symbol_ascending_and_avg_ranks(bundles):
    # A,B share (+1% price, 0.0001 funding); C,D share (-1%, 0.0002).
    # Avg-rank ties -> price pct .875/.375, funding pct .25/.75 ->
    # scores A=B=.625, C=D=-.375 -> longs [A,B], shorts [C,D].
    prices = {}
    funding = {}
    for s, px, r in [("AUSDT", 101.0, 0.0001), ("BUSDT", 101.0, 0.0001),
                     ("CUSDT", 99.0, 0.0002), ("DUSDT", 99.0, 0.0002)]:
        prices[s] = _closes([(T0, 100.0), (T1, px)])
        funding[s] = _flat_funding(r)
    root = bundles(funding)
    outs = [
        div(signal_cutoff_ns=T1 * 1_000_000, price_lookback_days=1,
            funding_bundles_dir=root, daily_closes=prices,
            traded_symbols=list(prices)),
        div(signal_cutoff_ns=T1 * 1_000_000, price_lookback_days=1,
            funding_bundles_dir=root, daily_closes=prices,
            traded_symbols=["DUSDT", "BUSDT", "AUSDT", "CUSDT"]),  # shuffled
    ]
    expected = {"longs": [["AUSDT", pytest.approx(0.2)],
                          ["BUSDT", pytest.approx(0.2)]],
                "shorts": [["CUSDT", pytest.approx(-0.2)],
                           ["DUSDT", pytest.approx(-0.2)]]}
    for res in outs:
        assert res["status"] == "OK"
        assert res["longs"] == expected["longs"]
        assert res["shorts"] == expected["shorts"]


def test_funding_window_boundary_excludes_stale_settlement(bundles):
    # Equal prices force the funding leg to decide alone. AUSDT carries a huge
    # 0.9 rate one millisecond BEFORE the 3-day window opens; it must be
    # ignored or AUSDT could not remain the lowest-funding name.
    prices = {s: _closes([(T0, 100.0), (T1, 101.0)])
              for s in ["AUSDT", "BUSDT", "CUSDT", "DUSDT"]}
    ws = T2 - 3 * DAY_MS
    funding = {
        "AUSDT": [(ws - 1, 0.9)] + _flat_funding(0.0001),
        "BUSDT": _flat_funding(0.0002),
        "CUSDT": _flat_funding(0.0003),
        "DUSDT": _flat_funding(0.0004),
    }
    res = div(signal_cutoff_ns=CUTOFF_NS, price_lookback_days=1,
              funding_bundles_dir=bundles(funding), daily_closes=prices,
              traded_symbols=list(prices))
    assert res["status"] == "OK"
    assert [s for s, _ in res["longs"]] == ["BUSDT", "AUSDT"]
    assert [s for s, _ in res["shorts"]] == ["DUSDT", "CUSDT"]


def test_build_divergence_traded_sorted_non_benchmark():
    closes = {"SOLUSDT": [(0, 1.0)], "BTCUSDT": [(0, 1.0)],
              "ETHUSDT": [(0, 1.0)]}
    assert build_divergence_traded(closes) == ["ETHUSDT", "SOLUSDT"]
    assert build_divergence_traded({}, benchmark="ETHUSDT") == []
