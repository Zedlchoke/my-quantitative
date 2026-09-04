"""V13 I lane (i-family-2) -- hand-computed goldens + causal-control identity
for A13-V13-A5-LIQEPIS (plan section 9 evidence items a and e).

The committed golden fixture
``research/v13/families/liqepis/golden/liqepis_causal_fixture.json``
encodes a tiny offline synthetic world: 13 symbols carry a UNIFORM
dollar-volume flow (q_b = 1.0 -- the proposal's uniform baseline) over the
whole 5376-slot window with exactly ONE engineered burst bar per symbol
(q = k, k = 1..13, at ``stamp - 96`` slots), so every episodicity value is
hand-computable as ``H(k) = (k^2 + N - 1) / N^2`` over N = 2688 (anchor) /
5376 (neighbour) slots; ``close = 1.0`` everywhere so ``q = volume``
exactly.  Hand truth:

* the anchor book's LONG leg is exactly the six smoothest names
  (SYM00..SYM05) and the SHORT leg the six burstiest (SYM07..SYM12),
  SYM06 flat, equal |weight| = 1/12;
* the uniform-baseline episodicity is exactly 1/2688 (proposal section 1);
* with hand-assigned forward weekly returns (+3% smooth / 0% middle /
  -3% bursty) the anchor book return is exactly +0.03;
* the sign-inverted control flips BOTH legs end-to-end, its weights are
  the EXACT negation of the anchor's, and its book return is exactly
  -0.03;
* a below-13-eligible variant fails closed with ``EligibilityShortfall``;
* the preregistered falsification rule (control passing while the anchor
  passes => tilt artifact, family falsified; control never promotable) is
  encoded in :mod:`research.v13.families.liqepis.gate_runner`.

The regressed anchor target payload is committed byte-for-byte as
``anchor_targets_golden.json`` and must regenerate identically.

All data synthetic; no real data is read and no scored metric exists.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.v13.families.liqepis.gate_runner import (
    CONTROL_NEVER_PROMOTABLE,
    VERDICT_FALSIFIED_TILT,
    VERDICT_FAMILY_ADVANCES,
    VERDICT_REJECTED_ANCHOR,
    VERDICT_REJECTED_NEIGHBOUR,
    evaluate_family_gate,
    incremental_gate,
)
from research.v13.families.liqepis.strategy import (
    ANCHOR_ARM,
    BAR_INTERVAL_NS,
    CONTROL_ARM,
    EligibilityShortfall,
    FORMATION_BARS_ANCHOR,
    FORMATION_BARS_NEIGHBOUR,
    NEIGHBOUR_ARM,
    episodicity_at,
    compute_targets_at,
    series_from_rows,
    stamp_calendar,
)

GOLDEN_DIR = Path("research/v13/families/liqepis/golden")


def load_fixture() -> dict:
    with open(GOLDEN_DIR / "liqepis_causal_fixture.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_world(
    fixture: dict,
    *,
    drop_boundaries: dict[str, int] | None = None,
    volume_override: dict[str, dict[int, float]] | None = None,
    close_override: dict[str, dict[int, float]] | None = None,
    late_available: dict[str, dict[int, int]] | None = None,
):
    """Reconstruct the synthetic world from the fixture's own constants."""
    stamp = int(fixture["stamp_ns"])
    origin = int(fixture["series_origin_ns"])
    interval = int(fixture["bar_interval_ns"])
    total_slots = (
        int(fixture["formation_bars_neighbour"]) + int(fixture["bars_after_stamp"])
    )
    burst = int(fixture["burst_boundary_ns"])
    uniform = float(fixture["uniform_q"])
    drops = drop_boundaries or {}
    vols = volume_override or {}
    closes = close_override or {}
    late = late_available or {}
    world = {}
    for sym in fixture["symbols"]:
        k = int(fixture["burst_multiplier_by_symbol"][sym])
        rows = []
        for j in range(total_slots):
            b = origin + j * interval
            if b in drops.get(sym, {}):
                continue
            volume = float(k) if b == burst else uniform
            close = 1.0
            avail = b
            if b in vols.get(sym, {}):
                volume = vols[sym][b]
            if b in closes.get(sym, {}):
                close = closes[sym][b]
            if b in late.get(sym, {}):
                avail = late[sym][b]
            rows.append((b, avail, close, volume))
        world[sym] = series_from_rows(rows)
    return world, stamp, list(fixture["symbols"])


def test_fixture_stamp_is_a_frozen_schedule_stamp() -> None:
    fixture = load_fixture()
    assert int(fixture["stamp_ns"]) in stamp_calendar()


def test_uniform_baseline_hhi_is_the_proposal_constant() -> None:
    """A symbol with zero bursts carries H = 1/2688 exactly (proposal sec. 1)."""
    fixture = load_fixture()
    stamp = int(fixture["stamp_ns"])
    interval = int(fixture["bar_interval_ns"])
    origin = stamp - (int(fixture["formation_bars_anchor"]) - 1) * interval
    rows = [
        (origin + j * interval, origin + j * interval, 1.0, 1.0)
        for j in range(int(fixture["formation_bars_anchor"]))
    ]
    value, reason = episodicity_at(
        series_from_rows(rows), stamp, formation_bars=FORMATION_BARS_ANCHOR
    )
    assert reason is None
    assert value == pytest.approx(1.0 / FORMATION_BARS_ANCHOR, rel=0.0)
    assert value == 1.0 / FORMATION_BARS_ANCHOR  # exact: all terms binary


def test_anchor_hhi_matches_hand_computed_values_exactly() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    hand = fixture["hand_computed"]["anchor_arm"]["h_by_symbol"]
    for sym in universe:
        value, reason = episodicity_at(
            world[sym], stamp, formation_bars=FORMATION_BARS_ANCHOR
        )
        assert reason is None
        # exact equality: the hand formula and the module evaluate the same
        # correctly-rounded float64 expression over integer-exact sums
        assert value == hand[sym], sym


def test_neighbour_hhi_matches_hand_computed_56d_values() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    hand = fixture["hand_computed"]["neighbour_arm"]
    value_low, _ = episodicity_at(
        world["SYM00"], stamp, formation_bars=FORMATION_BARS_NEIGHBOUR
    )
    value_high, _ = episodicity_at(
        world["SYM12"], stamp, formation_bars=FORMATION_BARS_NEIGHBOUR
    )
    assert value_low == hand["h_SYM00"]
    assert value_high == hand["h_SYM12"]
    assert value_low < value_high  # ordering preserved across the window


def test_anchor_book_matches_hand_computed_legs_and_weights() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    hand = fixture["hand_computed"]["anchor_arm"]
    book = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    assert [sym for sym, _w in book["longs"]] == hand["longs"]
    assert [sym for sym, _w in book["shorts"]] == hand["shorts"]
    assert book["middle"] == hand["middle"]
    weights = {sym: w for sym, w in book["weights"]}
    for sym in hand["longs"]:
        assert weights[sym] == hand["per_name_weight"]
    for sym in hand["shorts"]:
        assert weights[sym] == -hand["per_name_weight"]
    # 12 held names, gross 1.0 (to rounding), max |w| = 1/12 <= 0.30
    assert len(weights) == 12
    assert abs(sum(weights.values())) <= 1e-9
    assert max(abs(w) for w in weights.values()) <= 0.30


def test_anchor_book_return_is_the_hand_value_plus_0_03() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    hand = fixture["hand_computed"]["anchor_arm"]
    fwd = fixture["forward_week_return_by_symbol"]
    book = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    book_return = sum(float(w) * fwd[str(sym)] for sym, w in book["weights"])
    assert book_return == pytest.approx(hand["book_week_return"], abs=1e-12)
    assert hand["book_week_return"] == 0.03  # smooth names outperform (hand)


def test_neighbour_book_supports_the_anchor_book_on_the_fixture() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    anchor = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    neighbour = compute_targets_at(
        NEIGHBOUR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    assert [s for s, _ in neighbour["longs"]] == [s for s, _ in anchor["longs"]]
    assert [s for s, _ in neighbour["shorts"]] == [s for s, _ in anchor["shorts"]]


def test_control_book_is_the_exact_sign_flip_of_the_anchor() -> None:
    """Evidence (e): the inverted book IS the anchor book with flipped signs."""
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    anchor = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    control = compute_targets_at(
        CONTROL_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    hand = fixture["hand_computed"]
    assert [sym for sym, _w in control["longs"]] == hand["control_inv_arm"]["longs"]
    assert [sym for sym, _w in control["longs"]] == hand["anchor_arm"]["shorts"]
    assert [sym for sym, _w in control["shorts"]] == hand["anchor_arm"]["longs"]
    w_anchor = {sym: float(w) for sym, w in anchor["weights"]}
    w_control = {sym: float(w) for sym, w in control["weights"]}
    assert set(w_anchor) == set(w_control)
    for sym in w_anchor:
        assert w_control[sym] == -w_anchor[sym]  # EXACT float negation
    fwd = fixture["forward_week_return_by_symbol"]
    control_return = sum(float(w) * fwd[str(sym)] for sym, w in control["weights"])
    assert control_return == pytest.approx(
        hand["control_inv_arm"]["book_week_return"], abs=1e-12
    )
    assert hand["control_inv_arm"]["book_week_return"] == -0.03


def test_below_thirteen_eligible_fails_closed() -> None:
    fixture = load_fixture()
    world, stamp, _universe = build_world(fixture)
    short_universe = list(fixture["shortfall_fixture"]["symbols"])
    assert len(short_universe) == int(fixture["shortfall_fixture"]["n_eligible"]) == 12
    for arm in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
        with pytest.raises(EligibilityShortfall):
            compute_targets_at(
                arm, bars_by_symbol=world, stamp_ns=stamp, universe=short_universe
            )


def test_anchor_targets_regenerate_byte_identical_to_golden() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    targets = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    canonical = json.dumps(targets, sort_keys=True, separators=(",", ":"), default=str)
    golden_text = (GOLDEN_DIR / "anchor_targets_golden.json").read_text(
        encoding="utf-8"
    )
    assert canonical == golden_text


# --------------------------------------------------------------------------- #
# Evidence (e, second half): the preregistered falsification rule
# --------------------------------------------------------------------------- #
def test_incremental_gate_requires_two_of_three_folds() -> None:
    assert incremental_gate([True, True, False])["passed"] is True
    assert incremental_gate([True, False, False])["passed"] is False
    assert incremental_gate([True, True, True])["passed"] is True
    with pytest.raises(Exception):
        incremental_gate([True, False])


def test_gate_family_advances_when_control_fails_and_neighbour_supports() -> None:
    verdict = evaluate_family_gate(
        anchor_fold_positive=[True, True, False],
        control_fold_positive=[False, False, True],
        neighbour_fold_positive=[True, True, False],
    )
    assert verdict["verdict"] == VERDICT_FAMILY_ADVANCES
    assert verdict["control_never_promotable"] is True


def test_gate_falsifies_when_inverted_control_reproduces_the_anchor() -> None:
    """The preregistered rule: control passes while anchor passes => falsified."""
    verdict = evaluate_family_gate(
        anchor_fold_positive=[True, True, False],
        control_fold_positive=[True, True, False],  # inversion ALSO passes
        neighbour_fold_positive=[True, True, False],
    )
    assert verdict["verdict"] == VERDICT_FALSIFIED_TILT
    assert "tilt" in verdict["reason"]
    assert verdict["control_never_promotable"] is True


def test_gate_rejects_when_anchor_fails_or_neighbour_flips() -> None:
    anchor_fail = evaluate_family_gate(
        anchor_fold_positive=[True, False, False],
        control_fold_positive=[False, False, False],
        neighbour_fold_positive=[True, True, False],
    )
    assert anchor_fail["verdict"] == VERDICT_REJECTED_ANCHOR
    neighbour_flip = evaluate_family_gate(
        anchor_fold_positive=[True, True, False],
        control_fold_positive=[False, False, False],
        neighbour_fold_positive=[True, False, False],  # 1/3 positive: sign fragile
    )
    assert neighbour_flip["verdict"] == VERDICT_REJECTED_NEIGHBOUR
