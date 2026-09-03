"""V12 I lane -- hand-computed causal fixtures for OILEV-V2 (deliverable 5).

The committed golden fixture
``research/v12/families/oilev_v2/golden/causal_fixture.json`` encodes a
tiny synthetic world where LOW-OI-flow (deleveraged) names outperform:
ten symbols carry engineered 28d log OI growth from -0.40 to +0.40 and
hand-assigned forward weekly returns (+3%.. for the lowest-growth names,
-3%.. for the highest).  Hand truth:

* the anchor book's LONG leg is exactly the four lowest-growth names and
  the SHORT leg the four highest (equal |weight| = 0.125 each);
* the long-minus-short weekly book return is exactly +0.02;
* the sign-inverted control flips BOTH legs end-to-end and its book
  return is exactly -0.02 (the exact negation);
* a below-9-eligible variant fails closed with ``EligibilityShortfall``.

The regressed anchor target payload is committed byte-for-byte as
``anchor_targets_golden.json`` and must regenerate identically.

All data synthetic; no real data is read and no scored metric exists.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.v12.families.oilev_v2.strategy import (
    ANCHOR_ARM,
    CONTROL_ARM,
    NEIGHBOUR_ARM,
    compute_targets_at,
    signal_scores_at,
)
from research.v12.oilev_v2_book import EligibilityShortfall

GOLDEN_DIR = Path("research/v12/families/oilev_v2/golden")
DAY_NS = 86_400_000_000_000


def load_fixture() -> dict:
    with open(GOLDEN_DIR / "causal_fixture.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_world(fixture: dict) -> tuple[dict[str, tuple[tuple[int, float], ...]], int, list[str]]:
    """Reconstruct the synthetic OI world from the fixture's own constants."""
    base = float(fixture["base_oi"])
    start_ns = int(fixture["oi_start_iso"] and _iso_ns(fixture["oi_start_iso"]))
    offset = int(fixture["oi_row_offset_ns"])
    n_rows = int(fixture["n_daily_rows"])
    world: dict[str, tuple[tuple[int, float], ...]] = {}
    for sym, spec in sorted(fixture["per_symbol"].items()):
        g = math.exp(float(spec["target_log_growth_28d"]) / 28.0)
        rows = tuple(
            (start_ns + d * DAY_NS + offset, round(base * g ** d, 6))
            for d in range(n_rows)
        )
        world[sym] = rows
    return world, int(fixture["stamp_ns"]), sorted(fixture["per_symbol"])


def _iso_ns(iso: str) -> int:
    dt = datetime.fromisoformat(str(iso)[:-1]).replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * 1_000_000_000


def test_fixture_stamp_is_a_frozen_schedule_stamp() -> None:
    fixture = load_fixture()
    from research.v12.families.oilev_v2.strategy import stamp_calendar

    assert int(fixture["stamp_ns"]) in stamp_calendar()


def test_anchor_long_leg_matches_hand_computed_ranking() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    hand = fixture["hand_computed"]["anchor_arm"]
    book = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    assert [sym for sym, _w in book["longs"]] == hand["longs"]
    assert [sym for sym, _w in book["shorts"]] == hand["shorts"]
    weights = {sym: w for sym, w in book["weights"]}
    for sym in hand["longs"]:
        assert weights[sym] == pytest.approx(hand["per_name_weight"])
    for sym in hand["shorts"]:
        assert weights[sym] == pytest.approx(-hand["per_name_weight"])
    # the two middle names are never held
    for middle in ("SYM04", "SYM05"):
        assert weights.get(middle, 0.0) == 0.0
        assert middle not in [s for s, _ in book["longs"] + book["shorts"]]


def test_low_oi_flow_names_outperform_book_return_is_hand_value() -> None:
    """Long-minus-short weekly return equals the hand-computed +0.02."""
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    hand = fixture["hand_computed"]["anchor_arm"]
    book = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    fwd = {
        sym: float(spec["forward_week_return"])
        for sym, spec in fixture["per_symbol"].items()
    }
    book_return = sum(
        float(w) * fwd[str(sym)] for sym, w in book["weights"]
    )
    assert book_return == pytest.approx(hand["book_week_return"], abs=1e-12)
    assert hand["book_week_return"] > 0.0  # low-OI-flow names outperformed


def test_inv_arm_flips_signs_exactly() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    anchor = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    control = compute_targets_at(
        CONTROL_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    hand = fixture["hand_computed"]
    assert [sym for sym, _w in control["longs"]] == hand["control_inv_arm"]["longs"]
    assert [sym for sym, _w in control["longs"]] == hand["anchor_arm"]["shorts"]
    assert [sym for sym, _w in control["shorts"]] == hand["anchor_arm"]["longs"]
    w_anchor = {sym: float(w) for sym, w in anchor["weights"]}
    w_control = {sym: float(w) for sym, w in control["weights"]}
    assert set(w_anchor) == set(w_control)
    for sym in w_anchor:
        assert w_control[sym] == pytest.approx(-w_anchor[sym], abs=1e-15)
    # and the control's book return is the exact negation
    fwd = {
        sym: float(spec["forward_week_return"])
        for sym, spec in fixture["per_symbol"].items()
    }
    control_return = sum(float(w) * fwd[str(sym)] for sym, w in control["weights"])
    assert control_return == pytest.approx(
        hand["control_inv_arm"]["book_week_return"], abs=1e-12
    )


def test_neighbour_oi_stock_arm_respects_hand_computed_level_ranking() -> None:
    """56d OI-stock percentile ranks a designed cross-section by hand.

    Standalone synthetic world (the golden fixture's monotone growth gives
    every symbol an own-history percentile of exactly 1.0 by construction,
    which is itself the hand-checkable degenerate case asserted first).
    Here symbol ``SYM{i:02d}`` carries ``i`` window values strictly below
    its current level and ``55 - i`` above, so the frozen percentile is
    exactly ``(i + 1) / 56`` -- strictly increasing in ``i`` and unique
    per symbol.  Hand truth: longs = SYM00..03, shorts = SYM06..09.
    """
    from research.v11.families.oilever_delev.strategy import oi_stock_percentile

    # hand-checkable fixture-world case: monotone GROWING series puts the
    # current level at the top of its own 56d window (percentile exactly
    # 1.0); monotone DECLINING series puts it at the bottom (1/56)
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    scores = signal_scores_at(
        NEIGHBOUR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    for sym, value in scores.items():
        if sym <= "SYM04":  # engineered decline
            assert value == pytest.approx(1.0 / 56.0), sym
        else:  # engineered growth
            assert value == pytest.approx(1.0), sym
    # the resulting neighbour book therefore holds the same legs as the
    # anchor arm on this world (decliners long, growers short; the five-way
    # ties break lexicographically to SYM00..03 / SYM06..09)
    book = compute_targets_at(
        NEIGHBOUR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    assert [sym for sym, _w in book["longs"]] == ["SYM00", "SYM01", "SYM02", "SYM03"]
    assert [sym for sym, _w in book["shorts"]] == ["SYM06", "SYM07", "SYM08", "SYM09"]

    # designed percentile world: no row at or after the stamp is ever
    # planted (the `now` anchor is the stamp - 1d 23:55 row, d = 89)
    day = DAY_NS
    start = stamp - 90 * day
    row = lambda d: start + d * day + 23 * 3600 * 1_000_000_000 + 55 * 60 * 1_000_000_000
    designed: dict[str, tuple[tuple[int, float], ...]] = {}
    for i in range(10):
        sym = f"SYM{i:02d}"
        k_below = i  # of the 55 non-anchor window rows, i sit below `now`
        rows = []
        for d in range(90):  # d = 0..89; d = 89 is the PIT anchor row
            t = row(d)
            if d < 34:
                value = 100.0  # before the 56d window
            elif d == 89:
                value = 100.0  # `now`
            elif (d - 34) < k_below:
                value = 50.0  # below now
            else:
                value = 200.0  # above now
            rows.append((t, value))
        designed[sym] = tuple(rows)
    percentile_universe = sorted(designed)
    p_scores = signal_scores_at(
        NEIGHBOUR_ARM, oi_by_symbol=designed, stamp_ns=stamp, universe=percentile_universe
    )
    for i in range(10):
        assert p_scores[f"SYM{i:02d}"] == pytest.approx((i + 1) / 56.0)
    book = compute_targets_at(
        NEIGHBOUR_ARM, oi_by_symbol=designed, stamp_ns=stamp, universe=percentile_universe
    )
    assert [sym for sym, _w in book["longs"]] == ["SYM00", "SYM01", "SYM02", "SYM03"]
    assert [sym for sym, _w in book["shorts"]] == ["SYM06", "SYM07", "SYM08", "SYM09"]


def test_below_nine_eligible_fails_closed() -> None:
    fixture = load_fixture()
    world, stamp, _universe = build_world(fixture)
    short_universe = list(fixture["shortfall_fixture"]["symbols"])
    assert len(short_universe) == int(fixture["shortfall_fixture"]["n_eligible"]) == 8
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=short_universe
        )
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            CONTROL_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=short_universe
        )


def test_anchor_targets_regenerate_byte_identical_to_golden() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    targets = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    canonical = json.dumps(targets, sort_keys=True, separators=(",", ":"), default=str)
    golden_text = (GOLDEN_DIR / "anchor_targets_golden.json").read_text(
        encoding="utf-8"
    )
    assert canonical == golden_text
