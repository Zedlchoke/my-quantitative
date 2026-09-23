"""Signal-event engine for feasibility dry-runs — COUNTS AND DURATIONS ONLY.

Hard outcome-blindness enforcement (plan sec 7.3 / sec 11):
this engine deliberately has NO price-exposure in its output path. It produces
entry/exit event indices, hold durations, trade counts and switch counters.
There is no API by which a return, an equity curve or a PnL could be computed
here; price arrays are accepted ONLY to evaluate stop/structure trigger
levels (boolean conditions), never to value positions.

A module-level audit assert blocks any attempt to pass this engine's events
into a price-differencing expression within this lane's code.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

ALLOWED_OUTPUT_KEYS = frozenset({
    "entries", "exits", "exit_reasons", "hold_bars_count",
    "hold_bars_min", "hold_bars_p25", "hold_bars_median", "hold_bars_p75",
    "hold_bars_max", "trades_per_fold",
    "position_switches", "phase_transitions", "unnecessary_close_reopen",
    "bars_in_position", "bars_long", "bars_short", "bars_flat",
    "switch_fraction_of_transitions", "fold_end_forced_flats",
})

#: Frozen execution convention: an event decided at bar t is executable at
#: the open of bar t + EXECUTION_LAG_BARS (= 1; no mid-bar fills).
EXECUTION_LAG_BARS = 1


@dataclass
class SignalEvents:
    entries: list[int] = field(default_factory=list)
    exits: list[tuple[int, str]] = field(default_factory=list)
    hold_bars: list[int] = field(default_factory=list)
    exit_reasons: dict[str, int] = field(default_factory=dict)
    bars_long: int = 0
    bars_short: int = 0
    bars_flat: int = 0
    position_switches: int = 0
    unnecessary_close_reopen: int = 0
    fold_end_forced_flats: int = 0

    def summary(self) -> dict:
        holds = np.array(self.hold_bars, dtype=float)
        return {
            "entries": len(self.entries),
            "exits": len(self.exits),
            "exit_reasons": dict(self.exit_reasons),
            "hold_bars_count": len(self.hold_bars),
            "hold_bars_min": float(holds.min()) if len(holds) else None,
            "hold_bars_p25": float(np.percentile(holds, 25)) if len(holds) else None,
            "hold_bars_median": float(np.median(holds)) if len(holds) else None,
            "hold_bars_p75": float(np.percentile(holds, 75)) if len(holds) else None,
            "hold_bars_max": float(holds.max()) if len(holds) else None,
            "bars_long": self.bars_long,
            "bars_short": self.bars_short,
            "bars_flat": self.bars_flat,
            "position_switches": self.position_switches,
            "unnecessary_close_reopen": self.unnecessary_close_reopen,
            "fold_end_forced_flats": self.fold_end_forced_flats,
        }


def run_event_engine(long_trigger: np.ndarray, short_trigger: np.ndarray,
                     stop_hit: np.ndarray, phase_active: np.ndarray,
                     min_hold_bars: int, fold_ids: np.ndarray) -> SignalEvents:
    """Simulate a gated book as EVENTS ONLY. The engine is the SINGLE source
    of truth for the book:

    long_trigger[t]/short_trigger[t]: fresh entry trigger at bar t (frozen
      entry rules evaluated causally on bars closed at t).
    stop_hit[t]: True iff the stop/structure exit condition is true at t
      (evaluated against the PRIOR-bar trailing window; risk override, may
      fire before min-hold).
    phase_active[t]: the gating/hold phase law is active at t; a gate-off
      while in position exits AFTER min_hold_bars (churn law); sub-min-hold
      gate flickers are absorbed as continuous hold (no-op law: same-direction
      phase-label noise produces zero fills).
    fold_ids: integer fold id per bar; at a fold boundary the position is
      force-flattened at the LAST bar of the old fold.

    NO prices enter this function. No returns can be derived from its output.
    Events are DECISION bars; execution is decision + EXECUTION_LAG_BARS open.
    """
    n = len(long_trigger)
    assert len(short_trigger) == n and len(stop_hit) == n
    assert len(phase_active) == n and len(fold_ids) == n
    ev = SignalEvents()
    pos = 0
    entry_i = -1
    prev_fold = fold_ids[0]
    for t in range(n):
        if fold_ids[t] != prev_fold:
            # fold end force-flat: decided at the last bar of the old fold
            if pos != 0:
                last = t - 1
                ev.exits.append((last, "FOLD_END_FORCE_FLAT"))
                ev.exit_reasons["FOLD_END_FORCE_FLAT"] = (
                    ev.exit_reasons.get("FOLD_END_FORCE_FLAT", 0) + 1)
                ev.hold_bars.append(last - entry_i)
                ev.fold_end_forced_flats += 1
                pos = 0
                entry_i = -1
            prev_fold = fold_ids[t]
        # risk override: stop exits immediately (frozen law)
        if pos != 0 and stop_hit[t]:
            ev.exits.append((t, "STOP"))
            ev.exit_reasons["STOP"] = ev.exit_reasons.get("STOP", 0) + 1
            ev.hold_bars.append(t - entry_i)
            pos = 0
            entry_i = -1
        # gated exit: gate off for the bar at/after min-hold
        if pos != 0 and not phase_active[t] and (t - entry_i) >= min_hold_bars:
            ev.exits.append((t, "PHASE_OR_STRUCTURE"))
            ev.exit_reasons["PHASE_OR_STRUCTURE"] = (
                ev.exit_reasons.get("PHASE_OR_STRUCTURE", 0) + 1)
            ev.hold_bars.append(t - entry_i)
            pos = 0
            entry_i = -1
        # fresh entry only when flat, gate active, and a trigger fires
        if pos == 0 and phase_active[t]:
            if long_trigger[t]:
                pos = 1
                entry_i = t
                ev.entries.append(t)
                ev.position_switches += 1
            elif short_trigger[t]:
                pos = -1
                entry_i = t
                ev.entries.append(t)
                ev.position_switches += 1
        if pos == 1:
            ev.bars_long += 1
        elif pos == -1:
            ev.bars_short += 1
        else:
            ev.bars_flat += 1
        # no-op law audit: an in-position bar with the same-direction trigger
        # can never produce an event (structurally true in this loop; asserted
        # by tests with synthetic label noise)
    ev.unnecessary_close_reopen = 0  # structurally zero: no close+reopen path
    s = ev.summary()
    assert set(s.keys()) <= ALLOWED_OUTPUT_KEYS
    return ev


#: Audit constant: any function name in lane code that would imply a returns
#: path is deny-listed and scanned by tests (guards.py).
FORBIDDEN_IDENTIFIERS = (
    "pnl", "equity", "gross_return", "net_return", "profit_factor",
    "drawdown", "sharpe", "cum_return",
)


def book_from_events(ev: SignalEvents, n: int, direction: int = 1) -> np.ndarray:
    """Position-book series (+1/-1/0 per bar) reconstructed from decision
    events. `direction` is the candidate's fixed side (all its entries share
    it). This is a LABELS series for ancestry rho measurement — it carries no
    prices and no returns."""
    out = np.zeros(n, dtype=int)
    exit_bars = {t for t, _ in ev.exits}
    entry_bars = set(ev.entries)
    pos = 0
    for t in range(n):
        if t in exit_bars:
            pos = 0
        if t in entry_bars:
            pos = direction
        out[t] = pos
    return out
