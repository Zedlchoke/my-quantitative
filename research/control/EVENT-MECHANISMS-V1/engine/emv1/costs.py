"""E7 — frozen band-cost ceiling arithmetic (PREREGISTERED ONLY, no PnL).

Cost law (applied unmodified, per G3_FREEZE shared control 5):
- per-side base band from the frozen band schedule (DVmed60 classes
  A/B/C = 10/15/25 bps per fill; thresholds $50M/$10M/$2M; below-$2M floor
  fails closed = unfillable, excluded+counted);
- cost exactly once per fill; entry and exit are separate fills;
- Q-2 conditional law: entries fill at session opens -> priced at the
  EXPENSIVE open band (3.35x midday; the 3.33x is the per-minute movement
  figure, the 3.35x the measured spread figure);
- stress grid x1.0 / x1.5 / x2.0 (x2.0 = the frozen PRIMARY stress;
  ceiling_bps_round_trip 100 = 25 bps x 2 fills x 2.0).
No expectancy/PnL is computed anywhere in this module (R2-6): outputs are
per-event cost bands and the required-gross-vs-count grid TEMPLATE.
"""
from __future__ import annotations

from typing import Dict, List

from . import config as C


def per_event_round_trip_bps(record: dict, power: float) -> float:
    """Per-event round-trip cost band at a stress power (bps of notional)."""
    entry = record["cost_entry_bps_x1"]
    exit_ = record["cost_exit_bps_x1"]
    return (entry + exit_) * power


def ceiling_grid(populations: Dict[str, int], band_class_counts: Dict[str, Dict[str, int]]) -> List[dict]:
    """Required per-event GROSS expectancy (bps) vs event count per arm —
    the G6 grid TEMPLATE. Required gross = round-trip band x power. No
    realized expectancy is computed (R2-6).

    band_class_counts: arm -> {class -> count} (measured fired population).
    """
    rows = []
    # band-C conservative bound (25 bps base) and the frozen ceiling figures
    rt_c_open = 25.0 * C.OPEN_BAND_MULT + 25.0 * C.MIDDAY_BAND_MULT  # 108.75 bps
    rt_c_midday = 25.0 * 2.0                                          # 50 bps (100 @ x2.0)
    for arm in sorted(populations):
        n = populations[arm]
        classes = band_class_counts.get(arm, {})
        for power in C.COST_STRESS_POWERS:
            rows.append({
                "arm_id": arm,
                "n_events": n,
                "power": power,
                "required_ceiling_bps_per_event_bandC_open_entry": round(rt_c_open * power, 2),
                "required_ceiling_bps_per_event_bandC_midday": round(rt_c_midday * power, 2),
                "frozen_ceiling_bps_round_trip_at_x2": 100,
                "band_class_counts": classes,
                "note": "TEMPLATE ONLY — preregistered arithmetic, no expectancy computed (R2-6)",
            })
    return rows
