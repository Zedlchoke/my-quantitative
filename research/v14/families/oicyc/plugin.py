"""Adapter plugin joining A14-V14-A8-OICYC to the generic adapter (V14 I lane).

THIN family-specific plugin (the lane's only family-aware wiring module):
it wraps the frozen primitives in
:mod:`research.v14.families.oicyc.strategy` without re-implementing any
adapter semantics -- universe filtering, drop-one stress, baseline cell
construction, fold assembly and the LONG_PAYS_POSITIVE_RATE funding
accrual all come from :class:`research.adapter_v10.base.GenericStrategyBase`.

Data is injected at construction time (synthetic fixtures or a read-only,
SHA-verified load of the workspace snapshot; see ``audits.py`` for the
SHA-verified loaders).  This plugin never reads real data itself and never
scores.  The three frozen arms are three plugin instances of this one
class, differing only in ``arm_id``; every instance carries the
preregistered CONFIRMATORY status metadata (plan Section 1.1) so the V14
driver records it in the verdict and denominator.

PLUGIN INTERFACE (consumed mechanically by the V14 driver adapted from
``research/control/v13_run/tools/run_v13_cell.py``):

* ``identity()``       -- the frozen per-arm identity (digest-pinned);
* ``cost_model()``     -- the generic CostModel on the frozen V10 floors
  with REAL per-instrument tick sizes (L-V14-0: cost charged exactly once
  per fill through ``GenericStrategyBase.rebalance_cost_between``, never
  per holding-day, never per stamp on open positions);
* ``tradeable_universe()`` / ``minimum_tradeable_names()`` /
  ``benchmark_context_symbols()`` -- the frozen 19-name cohort minus the
  context-only benchmark leg;
* ``schedule()``       -- the frozen weekly Monday 00:00:00Z stamps (52);
* ``folds(...)`` / ``decision_instants(...)`` -- the pinned F0/F1/F2
  calendar folds with the 1-day calendar-zone purge (51 effective
  Mondays); ACCEPTS a dropped fold (L-V11-1);
* ``targets_at(...)``  -- ONE book per arm: the frozen chained hysteresis
  book at every schedule instant;
* ``fills_at(...)`` / ``marks_at(...)`` -- the pinned slot-open fill and
  covering-bar mark conventions;
* ``settlements(...)`` -- native funding settlements (COST ONLY);
* ``status_metadata()`` -- the CONFIRMATORY carry-through block;
* preflight digests    -- ``plugin_interface_report()`` and the frozen
  identity digest report, for the driver's preflight record.

State: the hysteresis book chain is MEMOISED per (decision stamp, stress
signature, universe) by replaying the retained decision stamps in
chronological order from the flat start, so any single-stamp query is
independent of call order and two plugin instances built from the same
injected data produce byte-identical books (determinism is test-pinned).

Traversal (V13R freeze delta, OITD precedent): the frozen generic runner
queries ``targets_at`` at EVERY non-final schedule instant
(``research.adapter_v10.runner._collect_books``) while never OPENING a
book at a non-fold-claimed instant (``_resolve_boundaries`` marks those
``ACTION_PURGE_GAP_CARRY``).  At such a NON-decision instant (the purged
2026-04-20 stamp, a dropped fold's stamps) the hysteresis book CARRIES:
the plugin returns the PREVIOUS retained decision's book byte-equal -- no
signal is computed at that stamp.  When no retained decision precedes the
stamp the carried book is the flat start (status OK, zero legs).  Instants
OFF the frozen Monday schedule still refuse fail-closed (the frozen runner
never queries them).  Fail-closed refusals at RETAINED decision stamps
(availability violations, eligibility shortfalls, incomplete
cross-sections) are unchanged.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import (
    ContractViolation,
    CostModel,
    FillRecord,
    FillStatusVocabulary,
    FoldSpec,
    ImmutableSchedule,
    SettlementPoint,
    StressSpec,
)
from research.pit_hooks_v10 import normalize_info_series
from research.v11.families.oilever_delev.strategy import (
    Bar,
    covering_bar,
)
from research.v14.families.oicyc.strategy import (
    ADVERSE_TICK_SLIP_FLOOR,
    ARM_ROLES,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    CONFIRMATORY,
    DECISION_CLOCK,
    FAMILY_ID,
    FILL_CLOCK,
    MIN_ELIGIBLE,
    PURGE_DAYS,
    SECTION_1_1_DISCLOSURE,
    STATUS_OK,
    TAKER_FEE_FLOOR_BPS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    assert_first_stamp_warmup,
    compute_targets_at,
    effective_schedule,
    fold_assignments,
    frozen_identity,
    iso_utc,
    next_allowed_fill,
    stamp_calendar,
)

PLUGIN_SCHEMA = "v14i.oicyc.plugin.v1"

#: Reason code of the FLAT carried book at a non-decision instant with no
#: preceding retained decision (the chain is at its flat start -- e.g. the
#: drop-one-fold cell's F0 stamps).
REASON_CARRIED_FLAT_START = "NON_DECISION_INSTANT_CARRIED_FLAT_START"

#: Reason/diagnostics code at a fold's last retained decision stamp: the
#: FOLD-TERMINAL FORCE-FLAT action (the liqepis V13R precedent, "the flat
#: transition itself is the boundary action").  The purge zone alone cannot
#: force-flat the fold's last LIVE stamp (its fill would straddle into the
#: next fold), so the plugin returns the FLAT book there: the fold realises
#: flat at its last executable decision slot and the next fold starts from
#: flat.  Counted and reported SEPARATELY from discretionary decisions
#: (OICYC.md decision clock).
REASON_FOLD_TERMINAL_FORCE_FLAT = "FOLD_TERMINAL_FORCE_FLAT"

#: The ONE declared execution lag (pinned; see strategy.next_allowed_fill).
DECLARED_EXECUTION_LAG = (
    "orders release at decision + 15m; fill reference = the OPEN of the "
    "first completed 15m bar whose slot-open >= release (the 00:15Z slot "
    "for a Monday 00:00:00Z decision); stress +1 event delay shifts the "
    "fill to the NEXT slot's open; the fill's readability horizon is its "
    "slot-open instant (a record stamped 00:30Z is NOT readable by the "
    "00:15Z fill -- pinned by mutation test)"
)


def _fold_terminal_force_flat_payload(arm_id: str, instant_ns: int) -> dict[str, Any]:
    """The FLAT book at a fold's last retained decision stamp.

    Status stays ``OK`` (the frozen runner refuses a ``FORCE_FLAT`` status
    at an OPEN instant and force-flattens the final schedule instant
    itself); zero legs with the explicit force-flat reason code.  The
    CONFIRMATORY block is carried like any other payload.
    """
    stamp = int(instant_ns)
    return {
        "schema": "v14i.oicyc.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": str(arm_id),
        "status": STATUS_OK,
        "weights": [],
        "longs": [],
        "shorts": [],
        "carried_forward": False,
        "reason_code": REASON_FOLD_TERMINAL_FORCE_FLAT,
        "decision_ns": stamp,
        "confirmatory": {
            "status": CONFIRMATORY,
            "authority": "PLAN_crypto_v14.md Section 1.1; OICYC.md sections 2/12",
            "disclosure": SECTION_1_1_DISCLOSURE,
        },
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "action": REASON_FOLD_TERMINAL_FORCE_FLAT,
            "flat_start": False,
        },
    }


def _fold_terminal_stamps(instants: Sequence[int]) -> set[int]:
    """The last retained stamp of each pinned fold (force-flat points)."""
    return {
        int(members[-1])
        for _index, _label, members, _purged in fold_assignments(list(instants))
        if members
    }


def _carried_flat_start_payload(arm_id: str, instant_ns: int) -> dict[str, Any]:
    """The FLAT carried book at a non-decision instant with no prior decision.

    Same payload schema as ``strategy.compute_targets_at`` with zero legs:
    the hysteresis chain is at its flat start, so the carried book is flat.
    Status stays ``OK`` (the frozen runner refuses a ``FORCE_FLAT`` status
    at an OPEN instant and force-flattens the final schedule instant
    itself); ``carried_forward`` is True with the explicit reason code.
    """
    stamp = int(instant_ns)
    return {
        "schema": "v14i.oicyc.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": str(arm_id),
        "status": STATUS_OK,
        "weights": [],
        "longs": [],
        "shorts": [],
        "carried_forward": True,
        "reason_code": REASON_CARRIED_FLAT_START,
        "decision_ns": stamp,
        "confirmatory": {
            "status": CONFIRMATORY,
            "authority": "PLAN_crypto_v14.md Section 1.1; OICYC.md sections 2/12",
            "disclosure": SECTION_1_1_DISCLOSURE,
        },
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "carried": True,
            "flat_start": True,
        },
    }


class OicycPlugin(GenericStrategyBase):
    """Adapter-facing view of one configured OICYC frozen arm."""

    def __init__(
        self,
        *,
        arm_id: str,
        oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
        bars_by_symbol: Optional[Mapping[str, Sequence[Bar]]] = None,
        settlements_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
        tick_sizes: Optional[Mapping[str, float]] = None,
        benchmark_symbol: str = BENCHMARK_SYMBOL,
        context_only_symbols: Sequence[str] = (BENCHMARK_SYMBOL,),
        window_start_iso: str = WINDOW_START_ISO,
        window_end_iso: str = WINDOW_END_ISO,
        cap: float = CAP_MAX,
        gross: float = 1.0,
        assert_warmup: bool = True,
    ) -> None:
        arm_id = str(arm_id)
        if arm_id not in ARM_ROLES:
            raise ContractViolation(
                f"unknown arm_id {arm_id!r}; expected {sorted(ARM_ROLES)}"
            )
        if not oi_by_symbol:
            raise ContractViolation("plugin needs the staged-OI bundle")
        self._arm_id = arm_id
        self._oi: dict[str, tuple[tuple[int, float], ...]] = {
            str(sym): tuple((int(t), float(v)) for t, v in series)
            for sym, series in sorted(oi_by_symbol.items())
        }
        for sym, series in self._oi.items():
            if not series:
                raise ContractViolation(
                    f"symbol {sym} injected an empty OI series"
                )
            times = [t for t, _ in series]
            if list(times) != sorted(set(times)):
                raise ContractViolation(
                    f"OI series for {sym} must be strictly increasing"
                )
        self._bars: dict[str, tuple[Bar, ...]] = {
            str(sym): tuple(bars)
            for sym, bars in sorted((bars_by_symbol or {}).items())
            if bars
        }
        if not self._bars:
            raise ContractViolation("plugin needs injected completed bars")
        missing_bars = sorted(set(self._oi) - set(self._bars))
        if missing_bars:
            raise ContractViolation(
                f"OI symbols without injected completed bars: {missing_bars}"
            )
        self._context_only = {str(s) for s in context_only_symbols}
        unknown_context = sorted(self._context_only - set(self._bars))
        if unknown_context:
            raise ContractViolation(
                f"context-only symbols have no injected bars: {unknown_context}"
            )
        pinned = str(benchmark_symbol)
        if pinned not in self._context_only:
            raise ContractViolation(
                f"the pinned benchmark leg {pinned} must be declared context-only"
            )
        if pinned in self._oi:
            raise ContractViolation(
                "the pinned benchmark leg can never be a tradeable candidate"
            )
        self._benchmark_symbol = pinned
        self._settlements_raw = {
            str(k): tuple(v) for k, v in (settlements_by_symbol or {}).items()
        }
        self._tick_sizes = {str(k): float(v) for k, v in (tick_sizes or {}).items()}
        self._window_start_iso = str(window_start_iso)
        self._window_end_iso = str(window_end_iso)
        self._cap = float(cap)
        self._gross = float(gross)
        self._chain_cache: dict[tuple[int, str, tuple[str, ...]], dict[str, Any]] = {}
        if assert_warmup:
            self._warmup = assert_first_stamp_warmup(
                self._oi, universe=self.tradeable_universe()
            )
        else:
            self._warmup = {}

    # ------------------------------------------------------------------ #
    # Identity / costs / status metadata
    # ------------------------------------------------------------------ #
    def identity(self):
        """The FROZEN V14 identity of this arm (digest equality test-pinned)."""
        return frozen_identity(self._arm_id)

    def cost_model(self) -> CostModel:
        """Generic adapter cost model on the frozen V10 floors.

        L-V14-0: costs are charged on FILLS ONLY through the inherited
        ``rebalance_cost_between`` -- never per holding-day, never per
        stamp on open positions -- at the frozen taker-fee floor plus the
        adverse-tick slippage floor with the injected REAL tick sizes.
        """
        return CostModel(
            taker_fee_bps=float(TAKER_FEE_FLOOR_BPS),
            adverse_tick_slip_floor=int(ADVERSE_TICK_SLIP_FLOOR),
            default_tick_sizes=dict(self._tick_sizes),
        )

    def status_metadata(self) -> dict[str, Any]:
        """The CONFIRMATORY carry-through block (plan Section 1.1).

        The driver records this verbatim in the verdict record and in the
        observed/published denominator accounting for every scored cell of
        this family.
        """
        return {
            "scored_status": CONFIRMATORY,
            "family_id": FAMILY_ID,
            "arm_id": self._arm_id,
            "arm_role": ARM_ROLES[self._arm_id],
            "authority": "PLAN_crypto_v14.md Section 1.1; OICYC.md sections 2/12",
            "disclosure": SECTION_1_1_DISCLOSURE,
            "denominator_note": (
                "all three scored cells of this family are counted as "
                "CONFIRMATORY in the observed/published denominators"
            ),
            "gates_unrelaxed": True,
            "control_never_promotable": True,
        }

    def plugin_interface_report(self) -> dict[str, Any]:
        """Preflight digest block for the V14 driver's preflight record."""
        identity = self.identity()
        model = self.cost_model()
        return {
            "schema": PLUGIN_SCHEMA,
            "family_id": FAMILY_ID,
            "arm_id": self._arm_id,
            "arm_role": ARM_ROLES[self._arm_id],
            "strategy_id": identity.strategy_id,
            "arm_config_id": identity.arm_config_id,
            "direction": identity.direction,
            "window": [identity.window_start_iso, identity.window_end_iso],
            "matrix_cohort_hint": identity.matrix_cohort_hint,
            "funding_sign_convention": identity.funding_sign_convention,
            "benchmark_excluded": list(identity.benchmark_symbols_excluded),
            "cost_model": {
                "taker_fee_bps": float(model.taker_fee_bps),
                "adverse_tick_slip_floor": int(model.adverse_tick_slip_floor),
                "tick_sizes": dict(sorted(self._tick_sizes.items())),
            },
            "tradeable_universe": list(self.tradeable_universe()),
            "minimum_tradeable_names": int(self.minimum_tradeable_names()),
            "benchmark_context_symbols": list(self.benchmark_context_symbols()),
            "schedule_instants": len(self.schedule().instants),
            "decision_clock": DECISION_CLOCK,
            "fill_clock": FILL_CLOCK,
            "declared_execution_lag": self.declared_execution_lag(),
            "fold_count": int(self.fold_count()),
            "purge_days": int(self.purge_days()),
            "gross_cap": float(self._gross),
            "weight_cap_abs": float(self._cap),
            "warmup_rows_at_first_stamp": dict(sorted(self._warmup.items())),
            "status_metadata": self.status_metadata(),
        }

    # ------------------------------------------------------------------ #
    # Universe / schedule / folds
    # ------------------------------------------------------------------ #
    def tradeable_universe(self) -> tuple[str, ...]:
        """Every injected OI candidate except the pinned benchmark leg."""
        return tuple(sorted(set(self._oi) - self._context_only))

    def minimum_tradeable_names(self) -> int:
        """Frozen breadth floor: both terciles need >= 4 of n//3 members."""
        return int(MIN_ELIGIBLE)

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Tradeable cohort PLUS the pinned context-only benchmark leg."""
        return tuple(sorted(set(self.tradeable_universe()) | self._context_only))

    def schedule(self) -> ImmutableSchedule:
        """Weekly Monday 00:00:00Z stamps; the ONE declared execution lag."""
        return ImmutableSchedule(
            instants=tuple(stamp_calendar()),
            source=(
                "research.v14.families.oicyc.strategy.stamp_calendar "
                f"(V11 weekly_mondays reuse; {self._window_start_iso}.."
                f"{self._window_end_iso}; {DECISION_CLOCK})"
            ),
            clock=FILL_CLOCK,
        )

    def declared_execution_lag(self) -> str:
        """The pinned fill-availability convention (documentation hook)."""
        return DECLARED_EXECUTION_LAG

    def fold_count(self) -> int:
        return 3

    def purge_days(self) -> int:
        return int(PURGE_DAYS)

    def fold_label(self, index: int) -> str:
        """Frozen fold labels F0/F1/F2 (pinned calendar windows)."""
        return f"F{int(index)}"

    def folds(
        self, *, stress: StressSpec, instants: Sequence[int]
    ) -> tuple[FoldSpec, ...]:
        """Pinned F0/F1/F2 calendar folds (1-day calendar-zone purge).

        ACCEPTS a dropped fold (L-V11-1): the dropped fold's stamps leave
        the retained schedule and become runner gap instants.
        """
        out: list[FoldSpec] = []
        for index, label, members, _purged in fold_assignments(list(instants)):
            dropped = (
                stress.dropped_fold_index is not None
                and index == int(stress.dropped_fold_index)
            )
            out.append(
                FoldSpec(
                    index=int(index),
                    label=str(label),
                    instants=tuple(members),
                    purge_days=int(self.purge_days()),
                    dropped=bool(dropped),
                )
            )
        return tuple(out)

    def decision_instants(self, *, stress: StressSpec) -> tuple[int, ...]:
        """Retained decision stamps: effective members of NON-dropped folds."""
        instants: list[int] = []
        for fold in self.folds(stress=stress, instants=list(stamp_calendar())):
            if fold.dropped:
                continue
            instants.extend(int(v) for v in fold.instants)
        return tuple(sorted(instants))

    # ------------------------------------------------------------------ #
    # Targets (chained hysteresis books; memoised, call-order independent)
    # ------------------------------------------------------------------ #
    def _chained_weights(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> tuple[dict[str, float], dict[str, Any]]:
        universe_key = tuple(sorted(str(s) for s in universe))
        stress_key = stress.signature().__repr__()
        key = (int(instant_ns), stress_key, universe_key)
        instants = self.decision_instants(stress=stress)
        if key in self._chain_cache:
            cached_weights, cached_payload = self._chain_cache[key]
            return dict(cached_weights), dict(cached_payload)
        prev: dict[str, float] = {}
        terminals = _fold_terminal_stamps(instants)
        for stamp in instants:
            if int(stamp) in terminals:
                # FOLD-TERMINAL FORCE-FLAT: the fold realises flat at its
                # last executable decision slot; no discretionary book is
                # opened here and the next fold starts from flat.
                payload = _fold_terminal_force_flat_payload(self._arm_id, stamp)
            else:
                payload = compute_targets_at(
                    self._arm_id,
                    oi_by_symbol=self._oi,
                    stamp_ns=int(stamp),
                    universe=universe,
                    prev_book=prev,
                    gross=self._gross,
                )
            stamp_key = (int(stamp), stress_key, universe_key)
            self._chain_cache[stamp_key] = (
                {
                    str(sym): float(w)
                    for sym, w in payload["weights"]
                    if abs(float(w)) > 0.0
                },
                dict(payload),
            )
            prev = dict(self._chain_cache[stamp_key][0])
        if int(instant_ns) in instants:
            cached_weights, cached_payload = self._chain_cache[key]
            return dict(cached_weights), dict(cached_payload)
        # NON-decision SCHEDULE instant (the purged 2026-04-20 stamp, a
        # dropped fold's stamps): the frozen hysteresis convention CARRIES
        # the book.  The frozen generic runner queries targets_at at every
        # non-final schedule instant (_collect_books) yet never OPENS a
        # book at a non-fold-claimed instant (_resolve_boundaries marks
        # those ACTION_PURGE_GAP_CARRY), so the answer it needs here is
        # the PREVIOUS retained decision's book, byte-equal, and NO signal
        # is computed at this stamp.  Fail-closed refusals at RETAINED
        # decision stamps are unchanged.
        if int(instant_ns) not in set(stamp_calendar()):
            raise ContractViolation(
                f"{iso_utc(int(instant_ns))} is not a frozen schedule stamp; "
                "the hysteresis chain answers only the frozen weekly Monday "
                "decision stamps"
            )
        prior_stamps = [int(s) for s in instants if int(s) < int(instant_ns)]
        if prior_stamps:
            carried_weights, carried_payload = self._chain_cache[
                (prior_stamps[-1], stress_key, universe_key)
            ]
            return dict(carried_weights), dict(carried_payload)
        return {}, _carried_flat_start_payload(self._arm_id, int(instant_ns))

    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        """Frozen chained hysteresis target book (fail-closed on breadth).

        At a RETAINED decision stamp this is the frozen chained book.  At a
        NON-decision instant (purged stamp / dropped-fold stamp) the book
        CARRIES: the previous retained decision's book byte-equal (flat
        start when none precedes); no signal is computed there.
        """
        _weights, payload = self._chained_weights(
            int(instant_ns), universe=universe, stress=stress
        )
        return payload

    # ------------------------------------------------------------------ #
    # Fills / marks (the pinned next-allowed-fill convention)
    # ------------------------------------------------------------------ #
    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        """Fill at the first slot-open >= decision + 15m (pinned convention)."""
        out: list[FillRecord] = []
        for sym in sorted(set(symbols)):
            event = next_allowed_fill(
                self._bars.get(sym) or (),
                sym,
                decision_ns=int(instant_ns),
                event_delay_events=int(stress.event_delay_events),
            )
            if event is None:
                out.append(FillRecord(symbol=sym, decision_ns=int(instant_ns)))
            else:
                out.append(
                    FillRecord(
                        symbol=sym,
                        decision_ns=int(instant_ns),
                        status=FillStatusVocabulary.APPLIED,
                        applied=True,
                        price=float(event.price),
                        fill_open_ns=int(event.fill_open_ns),
                        fill_bar_close_ns=int(event.fill_bar_close_ns),
                        event_offset=int(event.event_offset),
                    )
                )
        return tuple(out)

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        """Valuation mark = open of the bar covering the instant."""
        out: dict[str, Optional[float]] = {}
        for sym in sorted(set(symbols)):
            bar = covering_bar(self._bars.get(sym) or (), int(instant_ns))
            out[sym] = None if bar is None else float(bar.open)
        return out

    # ------------------------------------------------------------------ #
    # Funding (native, per-symbol; COST ONLY, accrual inherited from base)
    # ------------------------------------------------------------------ #
    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        """Native settlement points injected from the funding bundles."""
        raw = self._settlements_raw.get(str(symbol), ())
        points = normalize_info_series(
            [dict(p) if isinstance(p, Mapping) else p for p in raw]
        )
        return tuple(
            SettlementPoint(publish_ts_ns=int(p.publish_ts_ns), value=float(p.value))
            for p in points
        )


__all__ = [
    "DECLARED_EXECUTION_LAG",
    "OicycPlugin",
    "PLUGIN_SCHEMA",
    "REASON_CARRIED_FLAT_START",
    "REASON_FOLD_TERMINAL_FORCE_FLAT",
    "effective_schedule",
]
