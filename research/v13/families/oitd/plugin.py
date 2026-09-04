"""Adapter plugin joining A13-V13-A8-OITD to the generic adapter (V13 I lane).

THIN family-specific plugin (the lane's only family-aware wiring module):
it wraps the frozen primitives in
:mod:`research.v13.families.oitd.strategy` without re-implementing any
adapter semantics -- universe filtering, drop-one stress, baseline cell
construction, fold assembly and the LONG_PAYS_POSITIVE_RATE funding
accrual all come from :class:`research.adapter_v10.base.GenericStrategyBase`.

Data is injected at construction time (synthetic fixtures or a read-only
load of the workspace snapshot; see ``audits.py`` for the audit-only
loaders).  This plugin never reads real data itself and never scores.
The three frozen arms are three plugin instances of this one class,
differing only in ``arm_id``; the causal control instance is constructed
WITHOUT the OI/mark bundles (its signal layer refuses them outright --
the numerator is deleted by construction).

State: the hysteresis book chain is MEMOISED per (decision stamp, stress
signature, universe) by replaying the retained decision stamps in
chronological order from the flat start, so any single-stamp query is
independent of call order and two plugin instances built from the same
injected data produce byte-identical books (determinism is test-pinned).

Traversal (V13R freeze delta): the frozen generic runner queries
``targets_at`` at EVERY non-final schedule instant
(``research.adapter_v10.runner._collect_books``) while never OPENING a
book at a non-fold-claimed instant (``_resolve_boundaries`` marks those
``ACTION_PURGE_GAP_CARRY``).  At such a NON-decision instant (a purged
fold-terminal Monday, a dropped fold's stamps) the hysteresis book
CARRIES: the plugin returns the PREVIOUS retained decision's book
byte-equal -- no signal is computed at that stamp.  When no retained
decision precedes the stamp the carried book is the flat start (status
OK, zero legs).  Instants OFF the frozen Monday schedule still refuse
fail-closed (the frozen runner never queries them).  Fail-closed
refusals at RETAINED decision stamps
(availability violations, eligibility shortfalls, insufficient OI
stamps mid-window) are unchanged.  This mirrors the frozen V12 family
plugins, whose ``targets_at`` answers every mandatory runner query while
the runner itself decides which instants are gaps.
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
from research.v13.families.oitd.strategy import (
    ADVERSE_TICK_SLIP_FLOOR,
    ARM_ROLES,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    DECISION_CLOCK,
    FAMILY_ID,
    FILL_CLOCK,
    MIN_ELIGIBLE,
    PURGE_DAYS,
    STATUS_OK,
    TAKER_FEE_FLOOR_BPS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    compute_targets_at,
    fold_assignments,
    frozen_identity,
    iso_utc,
    next_allowed_fill,
    purge_fold_members,
    stamp_calendar,
)

PLUGIN_SCHEMA = "v13i.oitd.plugin.v1"

#: Reason code of the FLAT carried book at a non-decision instant with no
#: preceding retained decision (the chain is at its flat start -- e.g. the
#: drop-one-fold cell's F0 stamps).
REASON_CARRIED_FLAT_START = "NON_DECISION_INSTANT_CARRIED_FLAT_START"

#: The ONE declared execution lag (pinned; see strategy.next_allowed_fill).
DECLARED_EXECUTION_LAG = (
    "orders release at decision + 15m; fill reference = the OPEN of the "
    "first completed 15m bar whose slot-open >= release (the 00:15Z slot "
    "for a Monday 00:00:00Z decision); stress +1 event delay shifts the "
    "fill to the NEXT slot's open; the fill's readability horizon is its "
    "slot-open instant (a record stamped 00:30Z is NOT readable by the "
    "00:15Z fill -- pinned by mutation test)"
)

BASELINE_NAME = "baseline"


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
        "schema": "v13i.oitd.targets.v1",
        "family_id": FAMILY_ID,
        "arm_id": str(arm_id),
        "status": STATUS_OK,
        "weights": [],
        "longs": [],
        "shorts": [],
        "carried_forward": True,
        "reason_code": REASON_CARRIED_FLAT_START,
        "decision_ns": stamp,
        "diagnostics": {
            "stamp_ns": stamp,
            "stamp_iso": iso_utc(stamp),
            "carried": True,
            "flat_start": True,
        },
    }


class OitdPlugin(GenericStrategyBase):
    """Adapter-facing view of one configured OITD frozen arm."""

    def __init__(
        self,
        *,
        arm_id: str,
        day_turnover_by_symbol: Mapping[str, Mapping[int, float]],
        bars_by_symbol: Optional[Mapping[str, Sequence[Bar]]] = None,
        oi_by_symbol: Optional[Mapping[str, Sequence[tuple[int, float]]]] = None,
        mark_by_symbol: Optional[Mapping[str, Sequence[tuple[int, float]]]] = None,
        settlements_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
        tick_sizes: Optional[Mapping[str, float]] = None,
        benchmark_symbol: str = BENCHMARK_SYMBOL,
        context_only_symbols: Sequence[str] = (BENCHMARK_SYMBOL,),
        window_start_iso: str = WINDOW_START_ISO,
        window_end_iso: str = WINDOW_END_ISO,
        cap: float = CAP_MAX,
        gross: float = 1.0,
    ) -> None:
        arm_id = str(arm_id)
        if arm_id not in ARM_ROLES:
            raise ContractViolation(
                f"unknown arm_id {arm_id!r}; expected {sorted(ARM_ROLES)}"
            )
        if not day_turnover_by_symbol:
            raise ContractViolation("plugin needs at least one symbol of day turnover")
        self._arm_id = arm_id
        self._turnover: dict[str, dict[int, float]] = {
            str(sym): {int(d): float(v) for d, v in dict(days).items()}
            for sym, days in sorted(day_turnover_by_symbol.items())
        }
        for sym, days in self._turnover.items():
            if not days:
                raise ContractViolation(f"symbol {sym} injected an empty turnover map")
            keys = sorted(days)
            if keys != sorted(set(keys)):
                raise ContractViolation(f"turnover days for {sym} must be unique")
        is_control = arm_id == "CTL-FLOW-ONLY"
        if is_control and (oi_by_symbol or mark_by_symbol):
            raise ContractViolation(
                "CTL-FLOW-ONLY is constructed WITHOUT the OI/mark bundles "
                "(the numerator is deleted by construction)"
            )
        self._oi: dict[str, tuple[tuple[int, float], ...]] = {
            str(sym): tuple((int(t), float(v)) for t, v in series)
            for sym, series in sorted((oi_by_symbol or {}).items())
        }
        self._mark: dict[str, tuple[tuple[int, float], ...]] = {
            str(sym): tuple((int(t), float(v)) for t, v in series)
            for sym, series in sorted((mark_by_symbol or {}).items())
        }
        for label, bundle in (("OI", self._oi), ("mark", self._mark)):
            for sym, series in bundle.items():
                if not series:
                    raise ContractViolation(
                        f"symbol {sym} injected an empty {label} series"
                    )
                times = [t for t, _ in series]
                if list(times) != sorted(set(times)):
                    raise ContractViolation(
                        f"{label} series for {sym} must be strictly increasing"
                    )
        self._bars: dict[str, tuple[Bar, ...]] = {
            str(sym): tuple(bars)
            for sym, bars in sorted((bars_by_symbol or {}).items())
            if bars
        }
        if not self._bars:
            raise ContractViolation("plugin needs injected completed bars")
        missing_bars = sorted(set(self._turnover) - set(self._bars))
        if missing_bars:
            raise ContractViolation(
                f"symbols without injected completed bars: {missing_bars}"
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
        if pinned in self._turnover:
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
        self._chain_cache: dict[tuple[int, str, tuple[str, ...]], dict[str, float]] = {}

    # ------------------------------------------------------------------ #
    # Identity / costs
    # ------------------------------------------------------------------ #
    def identity(self):
        """The FROZEN V13 identity of this arm (digest equality test-pinned)."""
        return frozen_identity(self._arm_id)

    def cost_model(self) -> CostModel:
        """Generic adapter cost model on the frozen V10 floors."""
        return CostModel(
            taker_fee_bps=float(TAKER_FEE_FLOOR_BPS),
            adverse_tick_slip_floor=int(ADVERSE_TICK_SLIP_FLOOR),
            default_tick_sizes=dict(self._tick_sizes),
        )

    # ------------------------------------------------------------------ #
    # Universe / schedule / folds
    # ------------------------------------------------------------------ #
    def tradeable_universe(self) -> tuple[str, ...]:
        """Every injected turnover candidate except the pinned benchmark leg."""
        return tuple(sorted(set(self._turnover) - self._context_only))

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
                "research.v13.families.oitd.strategy.stamp_calendar "
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
        """Pinned F0/F1/F2 calendar folds; ACCEPTS a dropped fold (L-V11-1)."""
        purged = purge_fold_members(
            fold_assignments(list(instants)), purge_days=self.purge_days()
        )
        out: list[FoldSpec] = []
        for index, label, members, _gaps in purged:
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
        """Retained decision stamps: purged members of NON-dropped folds."""
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
        for stamp in instants:
            payload = compute_targets_at(
                self._arm_id,
                day_turnover_by_symbol=self._turnover,
                stamp_ns=int(stamp),
                universe=universe,
                prev_book=prev,
                oi_by_symbol=self._oi or None,
                mark_by_symbol=self._mark or None,
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
        # NON-decision SCHEDULE instant (a purged fold-terminal Monday, a
        # dropped fold's stamps): the frozen hysteresis convention CARRIES
        # the book.  The frozen generic runner queries targets_at at every
        # non-final schedule instant (_collect_books) yet never OPENS a
        # book at a non-fold-claimed instant (_resolve_boundaries marks
        # those ACTION_PURGE_GAP_CARRY), so the answer it needs here is
        # the PREVIOUS retained decision's book, byte-equal, and NO signal
        # is computed at this stamp.  Fail-closed refusals at RETAINED
        # decision stamps are unchanged: the replay above raises on
        # availability violations and eligibility shortfalls exactly as
        # before (a carry query inside an unreadable chain refuses too).
        if int(instant_ns) not in set(stamp_calendar()):
            # off-schedule instants are never queried by the frozen runner
            # and never carry: the chain answers only the frozen Monday
            # stamps (unchanged fail-closed pin)
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
        # No retained decision precedes the stamp (the chain is at its flat
        # start -- e.g. the drop-one-fold cell's F0 stamps): the carried
        # book IS the flat book.  Status stays OK (the runner refuses a
        # FORCE_FLAT status at an OPEN instant and force-flattens the final
        # schedule instant itself).
        return {}, _carried_flat_start_payload(self._arm_id, int(instant_ns))

    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        """Frozen chained hysteresis target book (fail-closed on breadth).

        At a RETAINED decision stamp this is the frozen chained book.  At a
        NON-decision instant (purged Monday / dropped-fold stamp) the book
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
    # Funding (native, per-symbol; accrual inherited from the base)
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
    "OitdPlugin",
    "PLUGIN_SCHEMA",
    "REASON_CARRIED_FLAT_START",
]
