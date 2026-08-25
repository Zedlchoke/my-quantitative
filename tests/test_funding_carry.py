"""H-XSECT-FUNDING-CARRY-v1 signal tests (frozen semantics, PLAN §8)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.funding_carry import (  # noqa: E402
    compute_target_weights_funding_carry as carry,
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


CUTOFF = 1_767_225_600_000_000_000 // 1_000  # 2026-01-01T00:00Z in ms *1e3? keep ms-space consistent


def test_rank_order_and_weight_sum(bundles):
    t0 = 1704067200000  # 2024-01-01
    syms = {"AUSDT": 0.0001, "BUSDT": -0.0002, "CUSDT": 0.0003, "DUSDT": 0.0002,
            "EUSDT": 0.0}
    root = bundles({s: [(t0 + i * DAY_MS, r) for i in range(3)]
                    for s, r in syms.items()})
    cutoff_ns = (t0 + 2 * DAY_MS) * 1_000_000
    res = carry(signal_cutoff_ns=cutoff_ns, lookback_days=3,
                funding_bundles_dir=root,
                traded_symbols=list(syms), target_gross=0.8)
    assert res["status"] == "OK"
    longs = [s for s, _ in res["longs"]]
    shorts = [s for s, _ in res["shorts"]]
    assert longs == ["BUSDT", "EUSDT"]                    # lowest means
    assert sorted(shorts) == ["CUSDT", "DUSDT"]           # highest means
    gross = sum(abs(w) for _, w in res["longs"] + res["shorts"])
    net = sum(w for _, w in res["longs"] + res["shorts"])
    assert abs(gross - 0.8) < 1e-9          # target_gross respected
    assert abs(net) < 1e-9                  # dollar-neutral book
    assert all(abs(abs(w) - 0.20) < 1e-9 for _, w in res["longs"] + res["shorts"])


def test_pit_future_settlements_excluded(bundles):
    t0 = 1704067200000
    future_t = t0 + 10 * DAY_MS
    root = bundles({
        "AUSDT": [(t0, 0.0001), (future_t, 0.9999)],   # future spike ignored
        "BUSDT": [(t0, 0.0002)],
        "CUSDT": [(t0, 0.0003)],
        "DUSDT": [(t0, 0.0004)],
    })
    cutoff_ns = (t0 + 2 * DAY_MS) * 1_000_000
    res = carry(signal_cutoff_ns=cutoff_ns, lookback_days=3,
                funding_bundles_dir=root,
                traded_symbols=["AUSDT", "BUSDT", "CUSDT", "DUSDT"])
    assert res["status"] == "OK"
    # AUSDT mean uses only the settled past row (0.0001) -> it is the bottom.
    assert res["longs"][0][0] == "AUSDT"
    assert abs(res["longs"][0][1] - 0.2) < 1e-9


def test_missing_symbol_skips_whole_cross_section(bundles):
    t0 = 1704067200000
    root = bundles({"AUSDT": [(t0, 0.0001)]})
    res = carry(signal_cutoff_ns=(t0 + DAY_MS) * 1_000_000, lookback_days=1,
                funding_bundles_dir=root,
                traded_symbols=["AUSDT", "BUSDT", "CUSDT", "DUSDT"])
    assert res == {"status": "SKIP_INCOMPLETE",
                   "reason_code": "funding_panel_incomplete"}


def test_reverse_swaps_sides_exactly(bundles):
    t0 = 1704067200000
    syms = {"AUSDT": 0.0001, "BUSDT": 0.0002, "CUSDT": 0.0003, "DUSDT": 0.0004}
    root = bundles({s: [(t0, r)] for s, r in syms.items()})
    kw = dict(lookback_days=1, funding_bundles_dir=root,
              traded_symbols=list(syms))
    fwd = carry(signal_cutoff_ns=(t0 + DAY_MS) * 1_000_000, **kw)
    rev = carry(signal_cutoff_ns=(t0 + DAY_MS) * 1_000_000, reverse=True, **kw)
    assert {s for s, _ in fwd["longs"]} == {s for s, _ in rev["shorts"]}
    assert {s for s, _ in fwd["shorts"]} == {s for s, _ in rev["longs"]}
    f_long = dict(fwd["longs"]); r_short = dict(rev["shorts"])
    for s in f_long:
        # swapped side also flips the position sign (long +w -> short -w)
        assert r_short[s] == pytest.approx(-f_long[s])


def test_tie_deterministic_by_symbol(bundles):
    t0 = 1704067200000
    syms = {"ZUSDT": 0.0001, "YUSDT": 0.0001, "XUSDT": 0.0005, "WUSDT": 0.0005}
    root = bundles({s: [(t0, r)] for s, r in syms.items()})
    res = carry(signal_cutoff_ns=(t0 + DAY_MS) * 1_000_000, lookback_days=1,
                funding_bundles_dir=root, traded_symbols=list(syms))
    assert [s for s, _ in res["longs"]] == ["YUSDT", "ZUSDT"]
