"""Gated variant of the CHR3F window-fold plugin — the ONLY new strategy
surface in ILLIQ-REG-V1, and a pure suppressor: at a GATE_OFF stamp it
returns the engine's own skip status (exactly the MIN_ELIGIBLE /
SKIP_NO_SELECTION semantics — flat week, no new fill logic); otherwise it
delegates verbatim to the frozen mechanics via Chr3fIlliqPlugin.

No frozen file is imported-and-modified; this subclass lives in the cycle
namespace and composes the frozen classes (same derivation discipline as
chr3f_illiq_plugin.py itself discloses).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # never drop __pycache__ into READ-ONLY trees
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import wiring  # noqa: E402

V11_ROOT = wiring.CHR3F_CTRL / "recovered" / "v11_root"
for p in (str(V11_ROOT), str(wiring.CHR3F_CTRL)):
    if p not in sys.path:
        sys.path.insert(0, p)

from chr3f_illiq_plugin import Chr3fIlliqPlugin  # noqa: E402
from research.adapter_v10.protocol import StressSpec  # noqa: E402
from research.v11.families.illiq_amihud.strategy import STATUS_SKIP  # noqa: E402

GATE_OFF_REASON = "GATE_OFF"


class IlliqRegGatedPlugin(Chr3fIlliqPlugin):
    """Chr3fIlliqPlugin + per-stamp gate suppression (plan SS3 apply law)."""

    def bind_gate(self, gate_by_stamp_ns: dict[int, bool]) -> None:
        missing = [ns for ns in self.schedule().instants
                   if int(ns) not in gate_by_stamp_ns]
        if missing:
            raise wiring.WiringError(
                f"gate map missing {len(missing)} schedule stamps "
                f"(first {missing[0]}) — fail-closed")
        self._gate_by_stamp_ns = {int(k): bool(v)
                                  for k, v in gate_by_stamp_ns.items()}

    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        if not getattr(self, "_gate_by_stamp_ns", {}).get(int(instant_ns), False):
            return {
                "status": STATUS_SKIP,
                "weights": {},
                "reason_code": GATE_OFF_REASON,
                "diagnostics": {"gate": "OFF"},
            }
        return super().targets_at(instant_ns, universe=universe, stress=stress)

    def gate_counts(self) -> dict[str, int]:
        g = getattr(self, "_gate_by_stamp_ns", {})
        on = sum(1 for v in g.values() if v)
        return {"stamps": len(g), "gate_on": on, "gate_off": len(g) - on}
