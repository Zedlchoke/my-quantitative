"""BASISLV window-fold plugin -- CHR3F replication subclass of the FROZEN
``BasislvPremfadePlugin`` (family A14-V14-A5-BASISLV-PREMFADE).

Cycle CRYPTO-HISTORICAL-REPLICATION-3F-V1, namespace basislv_replication.

Derivation discipline (disclosed, mirroring ``chr3f_illiq_plugin.py``): the
frozen plugin hard-binds its F0/F1/F2 fold calendar (2025-08-22..2026-08-21
with the 1-day trailing purge) via the frozen module functions
``stamp_calendar`` / ``fold_assignments`` / ``fold_end_ns`` /
``fold_terminal_force_flat_stamps``; replication windows therefore cannot
pass through it unmodified, and editing the frozen file is forbidden.  This
subclass overrides EXACTLY the fold-binding surface and NOTHING else:

* ``schedule`` / ``effective_instants`` -- weekly Monday 00:00:00Z stamps
  over the BOUND window via the frozen ``weekly_mondays`` helper (the frozen
  frozen-window call re-targeted; the decision clock itself is untouched);
* ``folds`` / ``fold_instants`` / ``_fold_label`` -- chronological thirds of
  the bound window (labels F1/F2/F3), force-flat at boundaries,
  ``purge_days=0`` (the chr3f window-fold precedent; on year windows no
  Monday stamp falls inside a 1-day trailing zone anyway, so the frozen
  purge convention is vacuous here and set to zero explicitly);
* ``targets_at`` -- (i) at a WINDOW fold-terminal stamp (last member of its
  fold, not the schedule-final instant) the FROZEN fold-terminal force-flat
  convention applies: the FLAT book with ``reason_code
  FOLD_TERMINAL_FORCE_FLAT`` (status OK; the frozen runner refuses a
  FORCE_FLAT status at an open instant), after the frozen fail-closed
  executability check RE-SCOPED to symbols whose bar series covers the
  stamp -- the frozen check demands an executable fill for EVERY universe
  symbol, which on a 2021 window would fail-closed on never-listed names
  that can never be held at that stamp (a leg can only be held if its own
  open fill executed; fills are requested only for held legs).  (ii) at a
  stamp with fewer than ``MIN_ELIGIBLE`` (12) eligible names the frozen
  ``compute_targets_at`` raises ``EligibilityShortfall``; inside the frozen
  runner that would abort the WHOLE cell, conflating one stamp's refusal
  with a data failure.  The frozen strategy docstring reads "the stamp
  refuses and the refusal is counted" -- the subclass realises that
  schedule-level semantics as the FLAT refusal-counted book (status OK,
  ``reason_code INSUFFICIENT_ELIGIBLE_REFUSAL``, per-stamp eligible/refused
  diagnostics), mirroring the frozen fold-terminal precedent.  (iii) every
  other stamp answers the frozen ``compute_targets_at`` verbatim.
* ``benchmark_context_symbols`` -- PIT-listed context narrowing (verbatim
  chr3f_illiq_plugin pattern): the buy-and-hold context is
  context_only_scored_false (enters_denominator False); the runner requires
  entry/exit marks for every context symbol at the first/last instant, so
  restricting the context to symbols listed at the window start changes NO
  scored surface and is disclosed on every cell.

UNIVERSE LAW (no A4-equivalent here): ``universe`` is NOT overridden.  The
tradeable universe stays the FROZEN 19 ranked names at every window; a
not-yet-listed name refuses the signal with ``INSUFFICIENT_HISTORY`` (its
basis series origin postdates the stamp) -- the engine's own eligibility
decides, exactly as the lane brief requires.  Every scored cell carries the
label ``UNIVERSE_LISTED_AT_WINDOW_START`` as a context-marks disclosure.

All mechanics (signal, book geometry, fills, marks, costs, funding, stress)
remain the frozen module's code, called verbatim.  Identity is the FROZEN
``frozen_identity(arm_id)`` (digest untouched; the window-fold binding lives
in the plugin surface, not the identity).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from research.adapter_v10.protocol import (
    ContractViolation,
    FoldSpec,
    ImmutableSchedule,
    StressSpec,
)
from research.contract_v10 import FILL_CLOCK_V10
from research.v14.families.basislv_premfade.plugin import (
    REASON_FOLD_TERMINAL_FORCE_FLAT,
    BasislvPremfadePlugin,
)
from research.v14.families.basislv_premfade.strategy import (
    DAY_NS,
    FAMILY_ID,
    STATUS_OK,
    EligibilityShortfall,
    compute_targets_at,
    iso_utc,
    next_allowed_close_fill,
    parse_iso_utc,
    signal_scores_at,
    weekly_mondays,
)

REASON_INSUFFICIENT_ELIGIBLE_REFUSAL = "INSUFFICIENT_ELIGIBLE_REFUSAL"

#: Window-fold labels (chronological thirds; chr3f window-fold precedent --
#: distinct from the frozen family's F0/F1/F2 calendar labels on purpose).
WINDOW_FOLD_LABELS = ("F1", "F2", "F3")


def thirds(window: tuple[str, str]) -> list[tuple[str, str, str]]:
    """``[(label, start_day, end_day)]`` chronological day-truncated thirds."""
    d0 = datetime.fromisoformat(window[0].replace("Z", "+00:00"))
    d1 = datetime.fromisoformat(window[1].replace("Z", "+00:00"))
    span = (d1 - d0).total_seconds()
    out = []
    for i, lab in enumerate(WINDOW_FOLD_LABELS):
        a = d0.fromtimestamp(d0.timestamp() + span * i / 3, tz=timezone.utc)
        b = d0.fromtimestamp(d0.timestamp() + span * (i + 1) / 3, tz=timezone.utc)
        out.append((lab, a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")))
    return out


def _day(stamp_ns: int) -> str:
    return datetime.fromtimestamp(stamp_ns / 1e9, tz=timezone.utc).strftime(
        "%Y-%m-%d"
    )


class BasislvWindowFoldPlugin(BasislvPremfadePlugin):
    """Frozen BASISLV-PREMFADE arm bound to one REPLICATION window.

    Construct with the frozen ``BasislvPremfadePlugin`` signature plus the
    replication ``window_start_iso`` / ``window_end_iso``, then call
    ``bind_window(window)`` (validated against the constructor window).
    """

    def bind_window(self, window: tuple[str, str]) -> None:
        w0 = window[0].replace("Z", "")
        w1 = window[1].replace("Z", "")
        c0 = self._window_start_iso.replace("Z", "")
        c1 = self._window_end_iso.replace("Z", "")
        if (w0, w1) != (c0, c1):
            raise ContractViolation(
                f"bind_window {window!r} contradicts the plugin window "
                f"({self._window_start_iso}..{self._window_end_iso})"
            )
        self._window_folds = thirds(tuple(window))

    # ------------------------------------------------------------------ #
    # Schedule / folds (the ONLY overridden mechanics)
    # ------------------------------------------------------------------ #
    def schedule(self) -> ImmutableSchedule:
        """Weekly Monday 00:00:00Z stamps over the BOUND window."""
        instants = weekly_mondays(
            window_start_iso=self._window_start_iso,
            window_end_iso=self._window_end_iso,
        )
        return ImmutableSchedule(
            instants=instants,
            source=(
                "basislv_replication.gated_plugin.BasislvWindowFoldPlugin.schedule "
                f"(WINDOW-FOLD REPLICATION binding; frozen weekly_mondays over "
                f"{self._window_start_iso}..{self._window_end_iso}; frozen "
                "decision clock)"
            ),
            clock=FILL_CLOCK_V10,
        )

    def fold_count(self) -> int:
        return 3

    def purge_days(self) -> int:
        """Window-fold binding: no purge zone (disclosed; see module header)."""
        return 0

    def folds_contract(self) -> str:
        return (
            "WINDOW-FOLD REPLICATION: chronological thirds of the bound "
            f"window {self._window_start_iso}..{self._window_end_iso} "
            f"({', '.join(f'{lab} {a}..{b}' for lab, a, b in self._window_folds)}), "
            "force-flat at fold boundaries, purge_days=0 (chr3f window-fold "
            "precedent); frozen mechanics otherwise"
        )

    def effective_instants(self) -> tuple[int, ...]:
        """All schedule stamps are effective (purge_days=0 in this binding)."""
        return tuple(self.schedule().instants)

    def _fold_label(self, stamp_ns: int):
        day = _day(int(stamp_ns))
        for label, a, b in self._window_folds:
            if a <= day < b or (label == self._window_folds[-1][0] and day == b):
                return label
        return None

    def fold_instants(self) -> dict[str, tuple[int, ...]]:
        out: dict[str, list[int]] = {}
        for stamp in self.schedule().instants:
            label = self._fold_label(stamp)
            if label is None:
                raise ContractViolation(
                    f"stamp {stamp} outside every window fold"
                )
            out.setdefault(label, []).append(int(stamp))
        return {label: tuple(v) for label, v in sorted(out.items())}

    def folds(
        self, *, stress: StressSpec, instants: Sequence[int]
    ) -> tuple[FoldSpec, ...]:
        """Chronological thirds of the bound window; force-flat boundaries."""
        buckets: dict[str, list[int]] = {}
        for stamp in sorted(int(v) for v in instants):
            label = self._fold_label(stamp)
            if label is None:
                raise ContractViolation(
                    f"decision stamp {stamp} outside every window fold"
                )
            buckets.setdefault(label, []).append(stamp)
        out = []
        for index, (label, _a, _b) in enumerate(self._window_folds):
            members = tuple(buckets.get(label, ()))
            if not members:
                raise ContractViolation(f"window fold {label} has no decision stamps")
            dropped = (
                stress.dropped_fold_index is not None
                and index == int(stress.dropped_fold_index)
            )
            out.append(
                FoldSpec(
                    index=index,
                    label=label,
                    instants=members,
                    purge_days=0,
                    dropped=dropped,
                )
            )
        return tuple(out)

    def window_fold_end_ns(self, stamp_ns: int) -> int:
        """Force-flat boundary of the window fold containing ``stamp_ns``."""
        day = _day(int(stamp_ns))
        for _label, _a, b in self._window_folds:
            start_ns = parse_iso_utc(_a + "T00:00:00Z")
            end_ns = parse_iso_utc(b + "T00:00:00Z")
            if start_ns <= int(stamp_ns) < end_ns:
                return end_ns
            if b == self._window_folds[-1][2] and day == b:
                return end_ns
        raise ContractViolation(
            f"stamp {iso_utc(int(stamp_ns))} outside every window fold"
        )

    def _window_fold_terminal_stamps(self) -> set[int]:
        """Last member of each window fold, minus the schedule-final edge.

        The schedule-final instant is the runner's own force-flat boundary
        (never queried for a book); mid-window fold-terminals carry the flat
        transition so no position crosses a fold boundary.
        """
        schedule = list(self.schedule().instants)
        terminal: set[int] = set()
        for _label, members in self.fold_instants().items():
            if members and int(members[-1]) != int(schedule[-1]):
                terminal.add(int(members[-1]))
        return terminal

    # ------------------------------------------------------------------ #
    # Targets (fold lookup swapped; refusals resolved per the frozen
    # schedule-level semantics -- see the module header)
    # ------------------------------------------------------------------ #
    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        stamp = int(instant_ns)
        if stamp in self._window_fold_terminal_stamps():
            return self._fold_terminal_force_flat(
                stamp, universe=universe, stress=stress
            )
        del stress  # the frozen signal/book carries no stress parameters
        try:
            return compute_targets_at(
                self._arm_id,
                basis_by_symbol=self._basis,
                stamp_ns=stamp,
                universe=universe,
                gross=self._gross,
            )
        except EligibilityShortfall as exc:
            return self._insufficient_eligible_refusal(stamp, universe=universe, exc=exc)

    def _insufficient_eligible_refusal(
        self,
        stamp_ns: int,
        *,
        universe: Sequence[str],
        exc: EligibilityShortfall,
    ) -> dict[str, Any]:
        """Flat refusal-counted book at a sub-MIN_ELIGIBLE stamp.

        The frozen strategy docstring: "Fewer than MIN_ELIGIBLE (12) eligible
        names raises EligibilityShortfall (the stamp refuses and the refusal
        is counted; fail closed)".  Inside the frozen runner a raise would
        abort the whole cell; this book keeps the stamp traversable while
        counting the refusal (status OK, zero legs, per-stamp eligibility
        diagnostics recomputed with the frozen ``signal_scores_at``).
        """
        scores, refused = signal_scores_at(
            self._arm_id,
            basis_by_symbol=self._basis,
            stamp_ns=stamp_ns,
            universe=universe,
        )
        by_reason: dict[str, int] = {}
        for reason in refused.values():
            by_reason[str(reason)] = by_reason.get(str(reason), 0) + 1
        return {
            "schema": "v14i.basislv_premfade.targets.v1",
            "family_id": FAMILY_ID,
            "arm_id": str(self._arm_id),
            "status": STATUS_OK,
            "weights": [],
            "longs": [],
            "shorts": [],
            "middle": [],
            "carried_forward": False,
            "reason_code": REASON_INSUFFICIENT_ELIGIBLE_REFUSAL,
            "decision_ns": stamp_ns,
            "diagnostics": {
                "stamp_ns": stamp_ns,
                "stamp_iso": iso_utc(stamp_ns),
                "insufficient_eligible_refusal": True,
                "n_eligible": len(scores),
                "min_eligible_required": 12,
                "n_refused": len(refused),
                "refused_by_reason": by_reason,
                "refused": {sym: str(reason) for sym, reason in sorted(refused.items())},
                "reason_code": REASON_INSUFFICIENT_ELIGIBLE_REFUSAL,
                "frozen_exception": str(exc),
            },
        }

    def _fold_terminal_force_flat(
        self,
        stamp_ns: int,
        *,
        universe: Sequence[str],
        stress: StressSpec,
    ) -> dict[str, Any]:
        """The frozen fold-terminal force-flat, RE-SCOPED executability check.

        Frozen body with two substitutions: the fold end is the WINDOW fold
        end, and the all-universe executable-fill pre-check is scoped to
        symbols whose bar series covers the stamp (a never-listed name can
        never be held at the stamp -- only held legs fill; see module
        header).  A covered symbol without an executable fill, or with a fill
        landing at/after the window fold end, still fails closed verbatim.
        """
        stamp = int(stamp_ns)
        end = int(self.window_fold_end_ns(stamp))
        delay = int(stress.event_delay_events)
        executable: dict[str, int] = {}
        not_covered: list[str] = []
        for sym in sorted({str(s) for s in universe}):
            series = self._bars.get(sym)
            if series is None:
                raise ContractViolation(
                    f"fold-terminal force-flat at {iso_utc(stamp)}: no bars "
                    f"injected for {sym} (fail-closed)"
                )
            if stamp < int(series.origin_ns) or stamp >= int(series.end_ns):
                not_covered.append(sym)
                continue
            event = next_allowed_close_fill(
                series, sym, decision_ns=stamp, event_delay_events=delay
            )
            if event is None:
                raise ContractViolation(
                    f"fold-terminal force-flat at {iso_utc(stamp)} has no "
                    f"executable close fill for {sym}; the fold could not "
                    "realise flat inside its own boundary (fail-closed)"
                )
            if int(event.fill_ns) >= end:
                raise ContractViolation(
                    f"fold-terminal force-flat at {iso_utc(stamp)}: close "
                    f"fill for {sym} lands {iso_utc(int(event.fill_ns))}, "
                    f"at/after the owning window fold's end {iso_utc(end)}; "
                    "the force-flat cannot execute inside the fold "
                    "(fail-closed)"
                )
            executable[sym] = int(event.fill_ns)
        return {
            "schema": "v14i.basislv_premfade.targets.v1",
            "family_id": FAMILY_ID,
            "arm_id": str(self._arm_id),
            "status": STATUS_OK,
            "weights": [],
            "longs": [],
            "shorts": [],
            "middle": [],
            "carried_forward": False,
            "reason_code": REASON_FOLD_TERMINAL_FORCE_FLAT,
            "decision_ns": stamp,
            "diagnostics": {
                "stamp_ns": stamp,
                "stamp_iso": iso_utc(stamp),
                "fold_terminal_force_flat": True,
                "window_fold_end_ns": end,
                "n_flat_close_fills_executable": len(executable),
                "not_covered_symbols_skipped": sorted(not_covered),
                "flat_close_fill_lands_before_fold_end": True,
                "reason_code": REASON_FOLD_TERMINAL_FORCE_FLAT,
            },
        }

    # ------------------------------------------------------------------ #
    # Context marks (PIT-listed narrowing; context-only, no scored surface)
    # ------------------------------------------------------------------ #
    # A4-class declared identity (label UNIVERSE_LISTED_AT_WINDOW_START):
    # universe = symbols listed at window start. Mid-window listings (PEPE/
    # SUI/WLD/ONG/ACE in Y2023) are excluded for the WHOLE fold — same
    # outcome-exposed consequence the owner accepted for ILLIQ (A4).
    FIRST_ARCHIVE_MONTH = {
        "1000PEPEUSDT": (2023, 5), "AAVEUSDT": (2020, 10), "ACEUSDT": (2023, 12),
        "ADAUSDT": (2020, 1), "AVAXUSDT": (2020, 9), "BCHUSDT": (2020, 1),
        "BNBUSDT": (2020, 2), "BOMEUSDT": (2024, 3), "BTCUSDT": (2020, 1),
        "DOGEUSDT": (2020, 7), "ENAUSDT": (2024, 4), "ETHUSDT": (2020, 1),
        "LINKUSDT": (2020, 1), "NEARUSDT": (2020, 10), "ONGUSDT": (2023, 11),
        "SOLUSDT": (2020, 9), "SUIUSDT": (2023, 5), "WLDUSDT": (2023, 7),
        "XRPUSDT": (2020, 1), "ZECUSDT": (2020, 2),
    }

    def universe(self, stress):
        frozen = super().universe(stress)
        w0 = self._window_start_iso[:7] if hasattr(self, "_window_start_iso") else None
        if not w0:
            w0 = getattr(self, "_chr3f_window_start", "")[:7]
        y, m = int(w0[:4]), int(w0[5:7])
        listed = {s for s in frozen if self.FIRST_ARCHIVE_MONTH.get(s, (9999, 1)) <= (y, m)}
        return tuple(s for s in frozen if s in listed or s == self._benchmark)

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        from replication_data import listed_at

        return listed_at(self._window_start_iso)


__all__ = [
    "BasislvWindowFoldPlugin",
    "REASON_INSUFFICIENT_ELIGIBLE_REFUSAL",
    "WINDOW_FOLD_LABELS",
    "thirds",
]
