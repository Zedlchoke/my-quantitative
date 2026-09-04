"""V13R LIQEPIS delta lane -- fold-boundary force-flat remediation evidence.

TECHABORT under remediation (research/control/v13_run/
TECHABORT_liqepis_chain_attempt1.json): the first scored LIQEPIS-28D
invocation crashed BEFORE any scored metric existed with the frozen
runner's cross-fold holding ContractViolation -- "BOMEUSDT: established in
fold 0/F0 but closed in fold 1/F1 (1765757700000000000 ->
1766362500000000000)".  Root cause (this lane's diagnosis, pinned below):
the frozen fold calendar retains each fold's LAST effective Monday (only
2026-04-20 sits inside the 1-day calendar purge zone), so F0's
fold-terminal stamp 2025-12-15T00:00:00Z OPENED a new 12-leg book whose
next schedule boundary -- F1's first stamp 2025-12-22T00:00:00Z -- belongs
to another fold.  The crash stamps are the normal Monday 00:15:00Z close
fills (the forensic artifact carries raw ns only; there is NO missing-bar
fill slide -- BOMEUSDT carries zero gap slots in the staged window), and
the defect is purely structural: no fold-boundary force-flat existed at
the fold's last executable decision slot.

The fix (research/v13/families/liqepis/plugin.py, machinery only; science
surface empty): at a fold-terminal force-flat stamp -- derived from the
frozen calendar alone, on the frozen runner's own roll-forward attribution
-- the plugin returns the FLAT book ("the flat transition itself is the
boundary action", the OITD fold-terminal precedent; this family's own
``force_flat_span_end`` force-flat-at-fold-end clamp) after failing closed
unless every symbol's close-fill executes strictly inside the owning fold.

Evidence pinned here, on the REAL staged snapshot (the equal-twin frozen
90/90 snapshot the crashed run verified; read-only; NO PnL computed, no
artifacts written outside /tmp):

(a) the exact BOMEUSDT scenario -- forensic ns decode, zero-gap census,
    the pre-fix raised leg, and the corrected in-fold behavior;
(b) the fold-boundary sweep -- all 3 arms x all 6 accepted matrix cells,
    schedule-only traversal of the FROZEN runner boundary resolver: every
    holding closes in its establishment fold, every fold-terminal flat
    completes in-fold, the F0->F1 boundary realises flat;
(c) PIT mutation pins -- covered by the untouched test_v13i_liqepis_*
    suites (run unmodified in the lane gates);
(d) 3/3 arm-config digests UNCHANGED (d7af1b24 / 60280408 / 49ca153a);
(e) the OITD family cannot be hit by the same class: its frozen
    trailing-stamp purge removes exactly the stamps this delta neutralises
    (provably in-fold by construction).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pytest

from research.adapter_v10.metrics import attribution_buckets
from research.adapter_v10.protocol import (
    DEFAULT_WEIGHT_CAP_MAX,
    WEIGHT_TOL,
    ContractViolation,
)
from research.adapter_v10.runner import _collect_books, _resolve_boundaries
from research.v13.families.liqepis.plugin import (
    REASON_FOLD_TERMINAL_FORCE_FLAT,
    fold_terminal_force_flat_stamps,
)
from research.v13.families.liqepis.strategy import (
    ARM_IDS,
    BAR_INTERVAL_NS,
    DAY_NS,
    FOLD_WINDOWS,
    FIRST_STAMP_ISO,
    WINDOW_END_ISO,
    compute_targets_at,
    effective_schedule,
    fold_assignments,
    fold_end_ns,
    parse_iso_utc,
    stamp_calendar,
)

STAGED_ROOT = Path(
    os.environ.get(
        "V13R_LIQEPIS_DELTA_STAGED_ROOT",
        "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v13/e-exec-1/staged_data",
    )
)

#: The w13 freeze authority (digest verdict source of truth).
W13_FREEZE = Path("research/control/v13_run/w13_freeze.json")

#: The forensic raw-ns stamps of the TECHABORT message.
CRASH_ENTRY_NS = 1765757700000000000
CRASH_EXIT_NS = 1766362500000000000

DEC_08 = parse_iso_utc("2025-12-08T00:00:00Z")
DEC_15 = parse_iso_utc("2025-12-15T00:00:00Z")
DEC_22 = parse_iso_utc("2025-12-22T00:00:00Z")

EXPECTED_DIGESTS = {
    "LIQEPIS-28D": "d7af1b24b2e50555fd5994db79cd0975f5c72eef6c6091e0197654730e40faa6",
    "LIQEPIS-56D": "6028040889c20fcd72a6a53d3582269d322a8f43e524f3c1fcb0fae0342f9999",
    "LIQEPIS-SIGN-INV": "49ca153a3d320584620e5d1525716b484b359b8c6290d3c0612888675a8ab140",
}


def _iso(stamp_ns: int) -> str:
    return datetime.fromtimestamp(int(stamp_ns) / 1e9, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _rolled_fold_owner(
    calendar: list[int], members_by_fold: Mapping[int, list[int]]
) -> dict[int, int]:
    """Calendar instant -> owning fold, purged gaps trailing into their fold.

    Mirrors the frozen runner attribution
    (``research.adapter_v10.metrics.attribution_buckets`` roll-forward) with
    plain integer folds -- test-side plumbing only, no new accounting.
    """
    owner: dict[int, int] = {}
    current = None
    for stamp in calendar:
        for index, members in members_by_fold.items():
            if stamp in members:
                current = index
                break
        if current is None:
            raise ContractViolation(f"instant {_iso(stamp)} precedes every fold")
        owner[stamp] = current
    return owner


# --------------------------------------------------------------------------- #
# Shared real-snapshot fixture (loaded once; read-only staged equal-twin)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def real_plugins() -> dict[str, Any]:
    if not STAGED_ROOT.is_dir():
        pytest.fail(f"staged snapshot missing: {STAGED_ROOT}")
    from research.control.v13_run.tools.run_v13_cell import build_liqepis

    exec_root = Path(__file__).resolve().parents[1]
    return {
        arm_id: build_liqepis(STAGED_ROOT, arm_id, exec_root)[0]
        for arm_id in ARM_IDS
    }


@pytest.fixture(scope="module")
def bomeusdt_series():
    """The staged BOMEUSDT fusion series (read-only; gap census input)."""
    from research.v13.families.liqepis.audits import load_fusion_series

    return load_fusion_series(
        ["BOMEUSDT"], bars_root=str(STAGED_ROOT / "binance_bar_15m")
    )["BOMEUSDT"]


# --------------------------------------------------------------------------- #
# (d) digest verdict: 3/3 arm-config digests UNCHANGED
# --------------------------------------------------------------------------- #
def test_liqepis_arm_config_digests_unchanged() -> None:
    from research.control.v13_run.tools.run_v13_cell import family_registry

    registry = family_registry()
    freeze = {
        arm: str(value)
        for arm, value in json.loads(W13_FREEZE.read_text(encoding="utf-8"))[
            "arm_config_digests"
        ].items()
    }
    for arm_id in ARM_IDS:
        recomputed = registry["liqepis"]["digest"](arm_id)
        assert recomputed == EXPECTED_DIGESTS[arm_id], (
            f"{arm_id} digest drifted: {recomputed}"
        )
        assert recomputed == freeze[arm_id], (
            f"{arm_id} digest != w13 freeze record: "
            f"{recomputed} != {freeze[arm_id]}"
        )


# --------------------------------------------------------------------------- #
# The fold-terminal force-flat derivation (frozen calendar only)
# --------------------------------------------------------------------------- #
def test_fold_terminal_force_flat_stamps_are_exactly_f0_terminal() -> None:
    calendar = [int(v) for v in stamp_calendar()]
    members = {
        index: list(members_)
        for index, _l, members_, _p in fold_assignments(calendar)
    }
    owner = _rolled_fold_owner(calendar, members)
    derived = fold_terminal_force_flat_stamps()

    # the derivation recomputes from the frozen constants alone
    expected = []
    effective = set(effective_schedule(calendar)[0])
    for position, stamp in enumerate(calendar[:-1]):
        if stamp in effective and owner[calendar[position + 1]] != owner[stamp]:
            expected.append(stamp)
    assert derived == tuple(expected)

    # exactly F0's fold-terminal stamp 2025-12-15T00:00:00Z: F1's fold-
    # terminal stamp 2026-04-13 is followed by the purged 2026-04-20 (which
    # trails back into F1), and F2's fold-terminal stamp 2026-08-17 IS the
    # schedule-final force-flat edge the runner flattens itself.
    assert [_iso(t) for t in derived] == ["2025-12-15T00:00:00Z"]
    assert derived[0] == max(members[0])
    assert fold_end_ns(derived[0]) == parse_iso_utc("2025-12-21T00:00:00Z")
    # deterministic across recomputation
    assert fold_terminal_force_flat_stamps() == derived


def test_fold_calendar_and_schedule_bytes_unchanged() -> None:
    """The science surface the delta must NOT touch: pinned fold windows,
    51 effective Mondays at 17/17/17, the single purged stamp 2026-04-20."""
    calendar = stamp_calendar()
    assert len(calendar) == 52
    assert _iso(calendar[0]) == "2025-08-25T00:00:00Z"
    assert _iso(calendar[-1]) == "2026-08-17T00:00:00Z"
    effective, purged = effective_schedule(calendar)
    assert len(effective) == 51
    assert {
        label: [_iso(t) for t in stamps] for label, stamps in purged.items()
    } == {"F1": ["2026-04-20T00:00:00Z"]}
    counts = {
        label: len(members_)
        for _i, label, members_, _p in fold_assignments(calendar)
    }
    assert counts == {"F0": 17, "F1": 17, "F2": 17}
    assert FOLD_WINDOWS == (
        ("F0", "2025-08-22", "2025-12-21"),
        ("F1", "2025-12-22", "2026-04-21"),
        ("F2", "2026-04-22", "2026-08-21"),
    )


# --------------------------------------------------------------------------- #
# (a) the exact BOMEUSDT TECHABORT scenario
# --------------------------------------------------------------------------- #
def test_techabort_stamps_are_the_normal_monday_close_fills(
    real_plugins, bomeusdt_series
) -> None:
    """The forensic ns decode to the NORMAL Monday 00:15Z close fills -- no
    missing-bar slide; the defect was purely the fold boundary."""
    assert _iso(CRASH_ENTRY_NS) == "2025-12-15T00:15:00Z"
    assert _iso(CRASH_EXIT_NS) == "2025-12-22T00:15:00Z"
    assert CRASH_ENTRY_NS == DEC_15 + BAR_INTERVAL_NS
    assert CRASH_EXIT_NS == DEC_22 + BAR_INTERVAL_NS

    plugin = real_plugins["LIQEPIS-28D"]
    stress = plugin.baseline_stress()
    fills = plugin.fills_at(DEC_15, symbols=["BOMEUSDT"], stress=stress)
    assert fills[0].applied and fills[0].fill_open_ns == CRASH_ENTRY_NS
    fills_next = plugin.fills_at(DEC_22, symbols=["BOMEUSDT"], stress=stress)
    assert fills_next[0].applied and fills_next[0].fill_open_ns == CRASH_EXIT_NS

    # zero gap slots for BOMEUSDT across the whole staged window: the
    # "missing-bar fill slide" hypothesis is refuted at the data level
    assert not bool(np.isnan(bomeusdt_series.close).any())


def test_bomeusdt_was_the_newly_established_leg_at_the_fold_terminal_stamp(
    real_plugins,
) -> None:
    """Pre-fix mechanism, pinned from the frozen books: BOMEUSDT was NOT
    held at 2025-12-08 and WAS newly established (weight changed) at
    2025-12-15 -- exactly the leg the frozen cross-fold check raised on
    when the 2025-12-22 boundary closed it inside F1."""
    plugin = real_plugins["LIQEPIS-28D"]
    stress = plugin.baseline_stress()
    universe = plugin.tradeable_universe()
    book_08 = {
        sym: float(w)
        for sym, w in plugin.targets_at(DEC_08, universe=universe, stress=stress)[
            "weights"
        ]
    }
    # the frozen strategy primitive is UNTOUCHED by the delta: it still
    # computes the full 12-leg book at the fold-terminal stamp
    book_15_frozen = {
        sym: float(w)
        for sym, w in compute_targets_at(
            "LIQEPIS-28D",
            bars_by_symbol=real_plugins["LIQEPIS-28D"]._bars,
            stamp_ns=DEC_15,
            universe=universe,
        )["weights"]
    }
    assert "BOMEUSDT" not in book_08
    assert book_15_frozen.get("BOMEUSDT") == pytest.approx(1.0 / 12.0, abs=1e-12)
    assert len(book_15_frozen) == 12


def test_bomeusdt_scenario_now_realises_the_fold_terminal_flat(real_plugins) -> None:
    """Correct behavior, pinned: at F0's fold-terminal stamp the plugin
    offers the FLAT book (status OK -- the frozen runner refuses a
    FORCE_FLAT status at an open instant; zero legs; not a carry), so the
    fold realises flat at its last executable decision slot and no leg can
    straddle into F1."""
    plugin = real_plugins["LIQEPIS-28D"]
    stress = plugin.baseline_stress()
    universe = plugin.tradeable_universe()
    flat = plugin.targets_at(DEC_15, universe=universe, stress=stress)
    assert flat["status"] == "OK"
    assert flat["weights"] == []
    assert flat["carried_forward"] is False
    assert flat["reason_code"] == REASON_FOLD_TERMINAL_FORCE_FLAT
    assert flat["decision_ns"] == DEC_15
    assert flat["diagnostics"]["fold_terminal_force_flat"] is True
    assert flat["diagnostics"]["fold_end_ns"] == fold_end_ns(DEC_15)
    assert flat["diagnostics"]["n_flat_close_fills_executable"] == len(universe)

    # every other effective stamp keeps the frozen 12-leg book (spot pins:
    # the stamps either side of the flat)
    for stamp in (DEC_08, DEC_22):
        book = plugin.targets_at(stamp, universe=universe, stress=stress)
        assert book["diagnostics"]["reason_code"] is None
        assert len(book["weights"]) == 12


def _dense_synthetic_series() -> dict[str, Any]:
    """A dense fusion-bar frame (every 15m slot completed) over the frozen
    window + the neighbour warmup head."""
    from research.v13.families.liqepis.audits import tradeable_universe_symbols
    from research.v13.families.liqepis.strategy import FusionBarSeries

    universe = tradeable_universe_symbols()
    symbols = tuple(sorted(set(universe) | {"BTCUSDT"}))
    origin = parse_iso_utc(FIRST_STAMP_ISO) - 56 * DAY_NS
    end_ns = parse_iso_utc(WINDOW_END_ISO)
    n_slots = (end_ns - origin) // BAR_INTERVAL_NS + 1
    grid = origin + np.arange(n_slots, dtype=np.int64) * BAR_INTERVAL_NS
    series: dict[str, Any] = {}
    for index, sym in enumerate(symbols):
        price = 2.0 + 0.5 * index
        volume = 100.0 + 7.0 * index
        burst = (np.arange(n_slots) % 96) == (index % 96)
        close = np.full(n_slots, price, dtype=np.float64)
        vol = np.where(burst, volume * (1.5 + 0.1 * index), volume)
        series[sym] = FusionBarSeries(
            origin_ns=int(origin),
            close=close,
            volume=vol,
            available_ns=grid.copy(),
            _q_cache=close * vol,
        )
    return series


def test_fold_terminal_flat_fails_closed_when_a_fill_cannot_land_in_fold() -> None:
    """Fail-closed, at schedule time: blank every BOMEUSDT bar from the
    fold-terminal stamp up to the fold end -- the flat's close fill would
    land at/after the fold boundary, so the flat is REFUSED, never offered
    half-executable."""
    from research.v13.families.liqepis.audits import tradeable_universe_symbols
    from research.v13.families.liqepis.plugin import LiqepisPlugin
    from research.v13.families.liqepis.strategy import FusionBarSeries

    dense = _dense_synthetic_series()
    universe = tradeable_universe_symbols()

    origin = dense["BOMEUSDT"].origin_ns
    close = dense["BOMEUSDT"].close.copy()
    volume = dense["BOMEUSDT"].volume.copy()
    first_bad = DEC_15 + BAR_INTERVAL_NS
    lo = int((first_bad - origin) // BAR_INTERVAL_NS)
    hi = int((fold_end_ns(DEC_15) - origin) // BAR_INTERVAL_NS)  # exclusive
    close[lo:hi] = np.nan
    volume[lo:hi] = np.nan
    gapped = dict(dense)
    gapped["BOMEUSDT"] = FusionBarSeries(
        origin_ns=origin,
        close=close,
        volume=volume,
        available_ns=dense["BOMEUSDT"].available_ns,
        _q_cache=close * volume,
    )
    plugin = LiqepisPlugin(
        arm_id="LIQEPIS-28D",
        bars_by_symbol=gapped,
        tick_sizes={sym: 0.01 for sym in gapped},
    )
    with pytest.raises(ContractViolation, match="cannot execute inside the fold"):
        plugin.targets_at(
            DEC_15, universe=universe, stress=plugin.baseline_stress()
        )

    # a fully dark symbol refuses too (no executable close fill at all)
    dark = dict(dense)
    dark_close = np.full_like(dense["BOMEUSDT"].close, np.nan)
    dark["BOMEUSDT"] = FusionBarSeries(
        origin_ns=origin,
        close=dark_close,
        volume=np.zeros_like(dense["BOMEUSDT"].volume),
        available_ns=dense["BOMEUSDT"].available_ns,
        _q_cache=dark_close * 0.0,
    )
    plugin_dark = LiqepisPlugin(
        arm_id="LIQEPIS-28D",
        bars_by_symbol=dark,
        tick_sizes={sym: 0.01 for sym in dark},
    )
    with pytest.raises(ContractViolation, match="no executable close fill"):
        plugin_dark.targets_at(
            DEC_15, universe=universe, stress=plugin_dark.baseline_stress()
        )


# --------------------------------------------------------------------------- #
# (b) fold-boundary sweep: 3 arms x 6 accepted cells, schedule-only
# --------------------------------------------------------------------------- #
def _assert_in_fold_closure(
    boundaries: list[Mapping[str, Any]],
    owner_by_instant: Mapping[int, Any],
) -> dict[str, tuple[int, bool]]:
    """Weights-only walk mirroring the frozen cross-fold invariant.

    Mirrors ``research.adapter_v10.runner._account_boundaries``: at every
    boundary the live legs close (the roll), and a leg whose weight CHANGED
    at its establishing boundary (``is_new_entry``) must close inside its
    establishing fold.  No prices, no PnL -- the establishment fold and the
    close fold are attributed from the frozen fold calendar alone.
    """
    live: dict[str, tuple[int, bool]] = {}
    for boundary in boundaries:
        instant = int(boundary["decision_ns"])
        fold = int(owner_by_instant[instant].index)
        prior = {str(s): float(w) for s, w in dict(boundary["prior_weights"]).items()}
        target = {str(s): float(w) for s, w in dict(boundary["target_weights"]).items()}
        for sym, weight in sorted(prior.items()):
            if abs(weight) <= WEIGHT_TOL:
                continue
            est_fold, is_new = live.get(sym, (fold, False))
            if is_new and est_fold != fold:
                pytest.fail(
                    f"cross-fold holding for {sym}: established in fold "
                    f"{est_fold} but closed in fold {fold} at {_iso(instant)}"
                )
        live = {
            sym: (fold, abs(float(w) - prior.get(sym, 0.0)) > WEIGHT_TOL)
            for sym, w in target.items()
            if abs(float(w)) > WEIGHT_TOL
        }
    return live


def _sweep_arm(plugin: Any) -> dict[str, Any]:
    from research.control.v13_run.tools.run_v13_cell import derive_contract

    derivation, _contract = derive_contract(plugin)
    schedule = plugin.schedule()
    instants = [int(v) for v in schedule.instants]
    summary = {"cells": 0, "flat_boundaries": 0, "final_force_flat": 0}
    for cell in derivation.cells:
        universe = plugin.universe(cell.spec)
        stress = cell.spec
        folds = plugin.folds(stress=stress, instants=instants)
        owner = attribution_buckets(folds, instants)
        books = _collect_books(
            plugin,
            schedule=schedule,
            universe=universe,
            stress=stress,
            cap_max=DEFAULT_WEIGHT_CAP_MAX,
        )
        declared = {
            int(v) for fold in folds if not fold.dropped for v in fold.instants
        }
        gaps = set(instants) - declared
        boundaries = _resolve_boundaries(
            plugin,
            schedule=schedule,
            books=books,
            stress=stress,
            gap_instants=gaps,
        )
        assert len(boundaries) == len(instants)
        assert boundaries[-1]["action"] == "FORCE_FLAT"

        # the frozen invariant: every holding closes in its establishment
        # fold, and the final force-flat leaves the book empty
        tail = _assert_in_fold_closure(boundaries, owner)
        assert tail == {}

        for boundary in boundaries:
            instant = int(boundary["decision_ns"])
            target = {
                str(s): float(w) for s, w in dict(boundary["target_weights"]).items()
            }
            prior = {
                str(s): float(w) for s, w in dict(boundary["prior_weights"]).items()
            }
            payload_reason = books[instant].reason_code if instant in books else None

            if (
                payload_reason == REASON_FOLD_TERMINAL_FORCE_FLAT
                and not boundary["purge_gap"]
            ):
                # the fold-terminal flat: liquidates the fold's holdings and
                # every close fill lands strictly inside the owning fold
                assert target == {} and prior, "the flat must liquidate holdings"
                assert boundary["action"] == "OPEN_REBALANCE"
                assert boundary["carry_forward"] is False
                applied = [f for f in boundary["fills"] if f.applied]
                assert applied, "the flat must carry executable close fills"
                latest = max(int(f.fill_bar_close_ns) for f in applied)
                assert latest < int(fold_end_ns(instant)), (
                    f"fold-terminal flat fill {_iso(latest)} at/after fold end "
                    f"{_iso(fold_end_ns(instant))}"
                )
                summary["flat_boundaries"] += 1
            if boundary["action"] == "FORCE_FLAT":
                # the final edge: closes the last fold's holdings in-fold
                for record in (f for f in boundary["fills"] if f.applied):
                    assert int(record.fill_bar_close_ns) < int(fold_end_ns(instant))
                summary["final_force_flat"] += 1

        # F0 realises FLAT at its boundary: the first F1 stamp opens from a
        # book with NO carried legs (the fold-terminal flat liquidated them)
        first_f1 = min(int(v) for v in instants if owner[int(v)].label == "F1")
        first_f1_boundary = next(
            b for b in boundaries if int(b["decision_ns"]) == first_f1
        )
        assert dict(first_f1_boundary["prior_weights"]) == {}, (
            "F0 must realise flat at its fold-terminal force-flat"
        )
        summary["cells"] += 1
    return summary


def test_fold_boundary_sweep_all_arms_all_cells_real_snapshot(real_plugins) -> None:
    """(b) Schedule-only sweep on the REAL staged snapshot: all 3 arms x
    all 6 accepted matrix cells -- every holding closes in its
    establishment fold; every fold-terminal force-flat completes in-fold;
    F0 realises flat.  NO PnL, NO artifacts (nothing is written)."""
    totals = {"cells": 0, "flat_boundaries": 0, "final_force_flat": 0}
    for arm_id in ARM_IDS:
        summary = _sweep_arm(real_plugins[arm_id])
        assert summary["cells"] == 6
        # five cells keep F0 (one fold-terminal flat each); in the
        # drop_one_fold cell every F0 stamp is a carried gap, so the flat
        # stamp is answered but never acted on there
        assert summary["flat_boundaries"] == 5
        assert summary["final_force_flat"] == 6  # one per cell
        for key in totals:
            totals[key] += summary[key]
    assert totals == {"cells": 18, "flat_boundaries": 15, "final_force_flat": 18}


def test_real_snapshot_traversal_pin_all_arms(real_plugins) -> None:
    """The frozen runner-compatibility pin still passes for all 3 arms on
    the real snapshot (every mandatory targets_at query is answered)."""
    from research.control.v13_run.tools.run_v13_cell import verify_runner_traversal

    for arm_id in ARM_IDS:
        pin = verify_runner_traversal(real_plugins[arm_id])
        assert pin["ok"] is True, pin["problems"]
        assert len(pin["cells_probed"]) == 6


# --------------------------------------------------------------------------- #
# (e) the same class cannot hit OITD (read-only precedent check)
# --------------------------------------------------------------------------- #
def test_oitd_boundary_handling_is_provably_in_fold() -> None:
    """OITD's frozen trailing-stamp purge removes exactly the stamps whose
    next schedule boundary leaves the fold, so no OITD book can ever be
    opened at a fold-terminal stamp and every OITD open closes in-fold by
    construction (the precedent this delta restores for LIQEPIS)."""
    from research.v13.families.oitd.strategy import (
        fold_assignments as oitd_fold_assignments,
    )
    from research.v13.families.oitd.strategy import (
        purge_fold_members as oitd_purge_fold_members,
    )
    from research.v13.families.oitd.strategy import (
        stamp_calendar as oitd_calendar,
    )

    calendar = [int(v) for v in oitd_calendar()]
    purged_assignments = oitd_purge_fold_members(
        oitd_fold_assignments(calendar), purge_days=1
    )
    retained: set[int] = set()
    members: dict[int, list[int]] = {}
    for index, _label, kept, _gaps in purged_assignments:
        retained.update(int(v) for v in kept)
        members[int(index)] = [int(v) for v in kept]
    owner = _rolled_fold_owner(calendar, members)

    # the purge strips EXACTLY the fold-terminal stamps (the LIQEPIS flat
    # set plus the final edge): 2025-12-15, 2026-04-20, 2026-08-17
    stripped = sorted(set(calendar) - retained)
    assert [_iso(t) for t in stripped] == [
        "2025-12-15T00:00:00Z",
        "2026-04-20T00:00:00Z",
        "2026-08-17T00:00:00Z",
    ]
    # therefore every retained (book-opening) stamp's next boundary is
    # same-fold: the cross-fold class is structurally impossible for OITD
    for position, stamp in enumerate(calendar[:-1]):
        if stamp in retained:
            assert owner[calendar[position + 1]] == owner[stamp], (
                f"OITD book open at {_iso(stamp)} could close cross-fold"
            )
