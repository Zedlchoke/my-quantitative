"""CHR3F window-fold subclass of the FROZEN IlliqAmihudPlugin.

Derivation discipline (disclosed): the frozen plugin hard-binds its fold map
(F0/F1/F2 = 2025-08..2026-08 calendar thirds) via the module function
fold_label_for_stamp; replication windows therefore cannot pass through it
unmodified, and editing the frozen file is forbidden. This subclass overrides
EXACTLY the fold-partitioning surface (folds / fold_instants / targets_at
fold lookup), mapping stamps to chronological calendar-thirds of the
REPLICATION window with the same force-flat policy. All mechanics
(compute_stamp_features, build_quintile_book, fills, costs, funding, stress)
remain the frozen module's code, called verbatim."""
from __future__ import annotations
from typing import Any, Sequence
from datetime import datetime, timezone

from research.adapter_v10.protocol import ContractViolation, FoldSpec, StressSpec
from research.v11.families.illiq_amihud.plugin import IlliqAmihudPlugin
from research.v11.families.illiq_amihud.strategy import STATUS_OK
from research.v11.families.illiq_amihud.strategy import (
    compute_stamp_features, build_quintile_book,
)


def thirds(window: tuple[str, str]) -> list[tuple[str, str, str]]:
    d0 = datetime.fromisoformat(window[0].replace("Z", "+00:00"))
    d1 = datetime.fromisoformat(window[1].replace("Z", "+00:00"))
    span = (d1 - d0).total_seconds()
    out = []
    for i, lab in enumerate(("F1", "F2", "F3")):
        a = d0.fromtimestamp(d0.timestamp() + span * i / 3, tz=timezone.utc)
        b = d0.fromtimestamp(d0.timestamp() + span * (i + 1) / 3, tz=timezone.utc)
        out.append((lab, a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")))
    return out


class Chr3fIlliqPlugin(IlliqAmihudPlugin):
    """Window-fold binding set post-construction via bind_window()."""

    def bind_window(self, window: tuple[str, str]) -> None:
        self._chr3f_folds = thirds(window)

    def _fold_label(self, stamp_ns: int):
        day = datetime.fromtimestamp(stamp_ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%d")
        for label, a, b in self._chr3f_folds:
            if a <= day < b or (label == self._chr3f_folds[-1][0] and day == b):
                return label
        return None

    def fold_instants(self) -> dict[str, tuple[int, ...]]:
        out: dict[str, list[int]] = {}
        for stamp in self._stamps:
            label = self._fold_label(stamp)
            if label is None:
                raise ContractViolation(f"stamp {stamp} outside every window fold")
            out.setdefault(label, []).append(int(stamp))
        return {label: tuple(v) for label, v in sorted(out.items())}

    def folds(self, *, stress: StressSpec, instants: Sequence[int]) -> tuple[FoldSpec, ...]:
        buckets: dict[str, list[int]] = {}
        for stamp in sorted(int(v) for v in instants):
            label = self._fold_label(stamp)
            if label is None:
                raise ContractViolation(f"decision stamp {stamp} outside every window fold")
            buckets.setdefault(label, []).append(stamp)
        out = []
        for index, (label, _a, _b) in enumerate(self._chr3f_folds):
            members = tuple(buckets.get(label, ()))
            if not members:
                raise ContractViolation(f"window fold {label} has no decision stamps")
            dropped = (stress.dropped_fold_index is not None
                       and index == int(stress.dropped_fold_index))
            out.append(FoldSpec(index=index, label=label, instants=members,
                                purge_days=0, dropped=dropped))
        return tuple(out)

    def targets_at(self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec) -> dict[str, Any]:
        # frozen targets_at body; fold lookup swapped to the window map.
        fold = self._fold_label(int(instant_ns))
        if fold is None:
            raise ContractViolation(f"stamp {instant_ns} outside every window fold")
        members = self.fold_instants()[fold]
        if int(instant_ns) == int(members[-1]) and int(instant_ns) != int(self.schedule().instants[-1]):
            return {"status": STATUS_OK, "weights": {},
                    "reason_code": "FOLD_BOUNDARY_FORCE_FLAT",
                    "diagnostics": {"fold": fold, "force_flat": True}}
        stamp = compute_stamp_features(
            bars_by_symbol=self._bars, universe=universe,
            benchmark_symbol=self._benchmark, decision_ns=int(instant_ns),
            formation_days=int(self._arm["formation_days"]))
        book = build_quintile_book(features=stamp.features, betas=stamp.betas,
                                   arm_sign=int(self._arm["sign"]))
        diagnostics = dict(stamp.diagnostics)
        diagnostics.update({k: v for k, v in book.get("diagnostics", {}).items()})
        return {"status": str(book["status"]), "weights": dict(book["weights"]),
                "reason_code": book.get("reason_code"), "diagnostics": diagnostics}
