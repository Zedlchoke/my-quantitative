"""Turnover law (plan §6) — anti-churn target router over cached regimes.

Laws implemented (frozen before any candidate PnL; constants from the plan,
to be mirrored by the A6 freeze):
1. Regime confirmation: the persisted-regime machine (confirm 2 / dwell 6 /
   cooldown 3) is the first gate — already inside the rebuilt timeline.
2. Transition buffer: a persisted switch changes the TARGET only after
   BUFFER_REGIME_BARS (=1) further regime bar — implemented as a k-bar
   delay of the label series (identical to attribution counterfactual b).
3. No-op law: while invested, the router keeps emitting the ENTRY
   specialist's strategy string, so an engine reconciliation (and any fill)
   happens ONLY on a direction change (or fold force-flat). A specialist
   switch mid-position takes effect at the NEXT entry. Specialist parameter
   changes mid-position never fire.
4. Direction flips (long<->short) close then open — both fills costed (the
   engine does this natively via reconciliation + entry).
5. Counters reported SEPARATELY: regime switches (timeline) vs position
   switches (engine trade opens); plus label-changes that did NOT change
   direction (no-op target updates).

Engine compatibility: targets are strategy-name strings exactly like V2;
arm B equivalence therefore uses the unbuffered, mapping-only path
(original V2 mechanics) — see arms_rsmv1.py.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field

from .data import Bars
from .engine import targets_from_regime
from .strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT

BUFFER_REGIME_BARS = 1  # frozen k=1 (plan §6.2)


def direction_of(strategy: str | None) -> int:
    """Signed direction of a TARGET/strategy name.

    V2 anchor names dispatch directly; A4 specialist names dispatch through
    the library's authoritative SPECIALIST_DIRECTIONS (run-1 incident: this
    function read every specialist name as 0/FLAT and the no-op pass
    collapsed all specialist routing to FLAT). Unknown non-FLAT names fail
    CLOSED to 0 — they can never silently route a position.
    """
    if strategy in (TREND_LONG, MR_LONG):
        return 1
    if strategy == TREND_SHORT:
        return -1
    if strategy in (FLAT, None, ""):
        return 0
    from .specialists import SPECIALIST_DIRECTIONS

    return SPECIALIST_DIRECTIONS.get(strategy, 0)


def buffered_labels(
    regime_ts: list[int], persisted: list[str], k: int = BUFFER_REGIME_BARS
) -> tuple[list[int], list[str]]:
    """Honor a persisted switch k regime bars LATE.

    Delay law: the label that became known at regime-bar close ts[i] is
    applied only from ts[i+k] onward — pairing regime_ts[k:] with
    persisted[:n-k]. (The opposite pairing, ts[:n-k] with persisted[k:],
    would APPLY A FUTURE LABEL EARLIER — lookahead — and is forbidden.)
    """
    if k <= 0:
        return regime_ts, persisted
    return regime_ts[k:], persisted[: len(persisted) - k]


@dataclass
class RouterReport:
    regime_switches: int = 0
    noop_target_updates: int = 0  # label changed, direction did not
    direction_changes_desired: int = 0
    position_switch_cap_note: str = "position switches counted from trades"


@dataclass
class TargetRouter:
    """Maps (persisted label -> specialist strategy name per asset) into
    engine target strings under the no-op law.

    mapping: label -> strategy name (already resolved per regime/fold by the
    selection law; UNK -> FLAT).
    """

    mapping: dict
    regime_ts: list[int]
    persisted: list[str]
    period_ns: int
    buffer_regime_bars: int = BUFFER_REGIME_BARS
    report: RouterReport = field(default_factory=RouterReport)

    def build(self, exec_bars: Bars) -> list[str | None]:
        ts, labels = buffered_labels(
            self.regime_ts, self.persisted, self.buffer_regime_bars
        )
        raw = targets_from_regime(
            exec_bars, ts, labels, self.period_ns, self.mapping
        )
        # No-op law pass: while the direction of the desired target equals
        # the direction of the current emitted target, keep the CURRENT
        # string (no reconciliation, no fill, specialist switch deferred).
        out: list[str | None] = [None] * len(raw)
        cur: str | None = None
        cur_d = 0
        prev_raw_d = 0
        for i, tgt in enumerate(raw):
            if tgt is None:
                out[i] = None
                continue
            d = direction_of(tgt)
            if cur is None or d != cur_d:
                cur = tgt
                cur_d = d
            else:
                # direction unchanged: label may still have changed (noop)
                if d != 0 and d == prev_raw_d and tgt != cur:
                    self.report.noop_target_updates += 1
            if i > 0 and direction_of(raw[i - 1]) != d:
                self.report.direction_changes_desired += 1
            prev_raw_d = d
            out[i] = cur
        self.report.regime_switches = sum(
            1 for j in range(1, len(labels)) if labels[j] != labels[j - 1]
        )
        return out


def position_switches(trades: list[dict]) -> int:
    """Actual position opens (each trade open = one position switch)."""
    return len(trades)


def reversal_count(trades: list[dict]) -> int:
    n = 0
    for j in range(1, len(trades)):
        if trades[j]["direction"] != trades[j - 1]["direction"]:
            n += 1
    return n


def v2_jev_only_trade_cap(cell: str) -> int:
    """Turnover rejection law cap (plan §6.8): arm C FAILS the cell if its
    position-switch count >= V2 JEV_ONLY trade count on that cell."""
    return {"BTC_H1": 978, "BTC_H4": 1060, "SPY_D1": 343}[cell]
