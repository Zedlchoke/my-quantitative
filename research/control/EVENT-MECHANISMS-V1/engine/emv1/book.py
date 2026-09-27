"""E2/E3 core — event book sequencing, exclusions, decision records.

Laws implemented (G3_FREEZE + R2-1..R2-6):
- direction_session = first session of the name whose close (16:00 ET of the
  bar date) occurs strictly AFTER the event instant;
- entry = raw open of the NEXT session after the direction session;
- exit = raw close of session entry+H-1 (raw-session count); if the name
  lacks H sessions post-entry, exit at the name's LAST available bar and
  flag delisting_exit (disclosed, never dropped silently);
- window [entry .. exit] containing ANY div/split ex-date => EXCLUDED,
  counted (R2-2);
- B1 extreme-print bars and volume-0 bars are unfillable on entry/exit
  (X1/X2 + B1, raw basis per R2-1);
- fold-boundary force-flat: a window crossing its event's fold end exits at
  the last session strictly before the fold boundary, flagged forced_flat;
- NO return, expectancy or aggregate field is ever produced (R2-6):
  records carry prices and cost-band inputs only.

Decision at every step reads only sessions whose close is at or before the
information being used; the unfinished-window guard (guard.py) asserts this
for every windowed feature.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

from . import config as C
from . import clock
from .panel import NameSeries, Panel, dvmed60, band_class_bps

# Exclusion reason codes (measured, counted, disclosed — never silent).
X_NO_SESSION = "NO_SESSION_AFTER_ACCEPTANCE"     # no direction session exists
X_NO_ENTRY_SESSION = "NO_ENTRY_SESSION"          # direction exists, entry does not
X_CORP_ACTION_WINDOW = "CORP_ACTION_IN_WINDOW"   # R2-2 div/split ex-date in window
X_ENTRY_FILL = "ENTRY_BAR_UNFILLABLE_B1B2"       # extreme print or volume-0 entry bar
X_EXIT_FILL = "EXIT_BAR_UNFILLABLE_B1B2"         # extreme print or volume-0 exit bar
X_ZERO_DIRECTION = "ZERO_DIRECTION_SESSION_MOVE" # close == open on direction session
X_BELOW_DV_FLOOR = "BELOW_DV_FLOOR_AT_DECISION"  # frozen eligibility floor
X_FOLD_BOUNDARY_NO_WINDOW = "FOLD_BOUNDARY_NO_WINDOW"  # entry past fold end
X_EMPTY_PANEL = "NO_PANEL_FOR_TICKER"

DECISION_KEYS = (
    "event_id", "family_id", "arm_id", "cik", "ticker", "form",
    "acceptance_utc", "fold", "stratum", "bucket", "is_weekend",
    "direction_session", "direction", "entry_session", "entry_price",
    "exit_session", "exit_price", "hold_sessions", "exclusions_applied",
    "delisting_exit", "forced_flat", "control_variant", "draw",
    "dv_band_class", "dvmed60_decision", "cost_entry_bps_x1",
    "cost_exit_bps_x1", "ticker_reuse_risk",
)


def resolve_direction_entry(
    ns: Optional[NameSeries], instant_et
) -> Tuple[str, Optional[int], Optional[int]]:
    """Return (status, direction_idx, entry_idx).

    status in {"OK", X_NO_SESSION, X_NO_ENTRY_SESSION, X_EMPTY_PANEL}.
    Direction session = first session whose CLOSE instant > event instant.
    """
    if ns is None or len(ns) == 0:
        return X_EMPTY_PANEL, None, None
    from datetime import date as _date
    # first bar with close instant after the acceptance instant
    lo, hi, ans = 0, len(ns) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        d = _date.fromisoformat(ns.dates[mid])
        if clock.session_close_instant(d) > instant_et:
            ans = mid
            hi = mid - 1
        else:
            lo = mid + 1
    if ans is None:
        return X_NO_SESSION, None, None
    if ans + 1 >= len(ns):
        return X_NO_ENTRY_SESSION, ans, None
    return "OK", ans, ans + 1


def window_dates(ns: NameSeries, entry_i: int, exit_i: int) -> List[str]:
    return ns.dates[entry_i : exit_i + 1]


def corp_action_in_window(ca: dict, ticker: str, dates: Sequence[str]) -> bool:
    acts = ca.get(ticker)
    if not acts:
        return False
    dset = set(dates)
    for kind in ("div", "split"):
        for d in acts.get(kind, ()):
            if d in dset:
                return True
    return False


def build_decision(
    *,
    event_id: str,
    family_id: str,
    arm_id: str,
    cik: str,
    ticker: str,
    form: str,
    acceptance_utc: str,
    instant_et,            # the decision clock instant (ET-aware datetime)
    hold_sessions: int,
    panel: Panel,
    corp_actions: dict,
    stratum: Optional[str],
    bucket: str,
    is_weekend: bool,
    control_variant: str = "PRIMARY",
    draw: Optional[int] = None,
    direction_override: Optional[str] = None,   # A2 LONG-only
    ticker_reuse_risk: bool = False,
) -> Tuple[Optional[dict], Optional[dict]]:
    """Build one decision record, or an exclusion record (reason-coded).

    Returns (decision_record | None, exclusion_record | None).
    No return/aggregate field is ever produced (R2-6).
    """
    ns = panel.get(ticker)
    fold = clock.fold_of(acceptance_utc)
    if fold == "OUTSIDE":
        return None, {"event_id": event_id, "reason": "OUTSIDE_WINDOW", "fold": fold,
                      "ticker": ticker, "cik": cik}

    status, dir_i, entry_i = resolve_direction_entry(ns, instant_et)
    if status != "OK":
        return None, {"event_id": event_id, "reason": status, "fold": fold,
                      "ticker": ticker, "cik": cik}

    assert ns is not None and entry_i is not None and dir_i is not None
    # direction (A1): sign of RAW (close - open) of the direction session
    if direction_override is not None:
        direction = direction_override
    else:
        diff = ns.close[dir_i] - ns.open[dir_i]
        if diff > 0:
            direction = "LONG"
        elif diff < 0:
            direction = "SHORT"
        else:
            return None, {"event_id": event_id, "reason": X_ZERO_DIRECTION,
                          "fold": fold, "ticker": ticker, "cik": cik}

    # ---- hold window with fold force-flat + delisting clamp ----
    # Force-flat law: a window may never cross its event's fold end; the
    # position exits at the last session strictly before the boundary. If
    # even the ENTRY falls past the fold end, the event is not holdable in
    # its own fold -> excluded, counted.
    last_i = entry_i + hold_sessions - 1
    forced_flat = False
    delisting_exit = False
    fold_end_exclusive = next(hi for name, lo, hi in C.FOLDS if name == fold)
    ff_i = _last_idx_lt_date(ns, fold_end_exclusive)
    # Force-flat applies only when the name actually survives past the fold
    # boundary (a panel ending before the boundary is a delisting, not a
    # fold clamp).
    has_post_fold_bars = ff_i < len(ns) - 1
    if has_post_fold_bars and ff_i < entry_i:
        return None, {"event_id": event_id, "reason": X_FOLD_BOUNDARY_NO_WINDOW,
                      "fold": fold, "ticker": ticker, "cik": cik}
    if has_post_fold_bars and last_i > ff_i:
        last_i = ff_i
        forced_flat = True
    if last_i >= len(ns):
        last_i = len(ns) - 1
        delisting_exit = True

    # ---- exclusions on the window ----
    win_dates = window_dates(ns, entry_i, last_i)
    if corp_action_in_window(corp_actions, ticker, win_dates):
        return None, {"event_id": event_id, "reason": X_CORP_ACTION_WINDOW,
                      "fold": fold, "ticker": ticker, "cik": cik}
    if not ns.fill_ok[entry_i]:
        return None, {"event_id": event_id, "reason": X_ENTRY_FILL,
                      "fold": fold, "ticker": ticker, "cik": cik}
    if not ns.fill_ok[last_i]:
        return None, {"event_id": event_id, "reason": X_EXIT_FILL,
                      "fold": fold, "ticker": ticker, "cik": cik}

    # ---- cost-band inputs (frozen contract; feasibility, not PnL) ----
    dvmed = dvmed60(ns, entry_i - 1)  # last CLOSED session before entry
    band_class, base_bps = band_class_bps(dvmed)
    if dvmed is None or dvmed < C.DV_FLOOR:
        return None, {"event_id": event_id, "reason": X_BELOW_DV_FLOOR,
                      "fold": fold, "ticker": ticker, "cik": cik}

    rec = {
        "event_id": event_id,
        "family_id": family_id,
        "arm_id": arm_id,
        "cik": cik,
        "ticker": ticker,
        "form": form,
        "acceptance_utc": acceptance_utc,
        "fold": fold,
        "stratum": stratum,
        "bucket": bucket,
        "is_weekend": is_weekend,
        "direction_session": ns.dates[dir_i],
        "direction": direction,
        "entry_session": ns.dates[entry_i],
        "entry_price": ns.open[entry_i],          # raw open (R2-1)
        "exit_session": ns.dates[last_i],
        "exit_price": ns.close[last_i],           # raw close (R2-1)
        "hold_sessions": hold_sessions,
        "exclusions_applied": [],                 # none triggered for bookable events
        "delisting_exit": delisting_exit,
        "forced_flat": forced_flat,
        "control_variant": control_variant,
        "draw": draw,
        "dv_band_class": band_class,
        "dvmed60_decision": dvmed,
        "cost_entry_bps_x1": base_bps * C.OPEN_BAND_MULT,   # Q-2 open band (3.35x)
        "cost_exit_bps_x1": base_bps * C.MIDDAY_BAND_MULT,  # close ~ midday basis
        "ticker_reuse_risk": ticker_reuse_risk,
    }
    return rec, None


def _last_idx_lt_date(ns: NameSeries, cutoff_exclusive: str) -> int:
    """Last bar index with date < cutoff (fold force-flat boundary)."""
    lo, hi, ans = 0, len(ns) - 1, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if ns.dates[mid] < cutoff_exclusive:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def summarize_populations(records: Sequence[dict]) -> dict:
    """Fold populations per arm (feasibility numbers only, R2-6)."""
    out: Dict[str, Dict[str, int]] = {}
    for r in records:
        arm = r["arm_id"]
        out.setdefault(arm, {})
        out[arm][r["fold"]] = out[arm].get(r["fold"], 0) + 1
    for arm in out:
        out[arm]["TOTAL"] = sum(v for k, v in out[arm].items() if k != "TOTAL")
    return out


def summarize_exclusions(excl: Sequence[dict]) -> dict:
    out: Dict[str, Dict[str, int]] = {}
    for e in excl:
        out.setdefault(e["reason"], {})
        out[e["reason"]][e.get("fold", "?")] = out[e["reason"]].get(e.get("fold", "?"), 0) + 1
    for reason in out:
        out[reason]["TOTAL"] = sum(v for k, v in out[reason].items() if k != "TOTAL")
    return out
