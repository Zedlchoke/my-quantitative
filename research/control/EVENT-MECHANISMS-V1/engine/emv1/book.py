"""E2/E3 core — event book sequencing, exclusions, decision records.

Laws implemented (G3_FREEZE + R2-1..R2-6 + r3 addendum):
- A1 direction_session = first session of the name whose close (16:00 ET of
  the bar date) occurs strictly AFTER the event instant;
- A1 entry = raw open of the NEXT session after the direction session;
- A2 entry (r3 D-1, R2-3 verbatim) = FIRST session whose 09:30 ET open is
  strictly after the acceptance instant; long-only; direction_session null;
- exit = raw close of session entry+H-1 (raw-session count); if the name
  lacks H sessions post-entry, exit at the name's LAST available bar and
  flag delisting_exit (disclosed, never dropped silently);
- window [entry .. exit] whose CALENDAR interval contains ANY div/split
  ex-date => EXCLUDED, counted (R2-2 + r3 AMB-15); ex-date tables resolve
  case-insensitively (r3 D-2);
- B1 extreme-print bars and volume-0 bars are unfillable on entry/exit
  (X1/X2 + B1, raw basis per R2-1); an unfillable ENTRY excludes+counts;
  an unfillable EXIT ROLLS FORWARD to the next clean bar (r3 AMB-7),
  exhausting at the last permissible bar flagged delisting_exit;
- fold assigned by ET-LOCAL acceptance date (r3 AMB-9, bookkeeping only);
- fold-boundary force-flat (lane I convention, unruled at r3): a window
  crossing its event's fold end exits at the last session strictly before
  the boundary, flagged forced_flat;
- direction tie (close==open, r3 AMB-11): direction 0 => EXCLUDED, counted;
- NO return, expectancy or aggregate field is ever produced (R2-6):
  records carry prices and cost-band inputs only.

Decision at every step reads only sessions whose close is at or before the
information being used; the unfinished-window guard (guard.py) asserts this
for every windowed feature.
"""
from __future__ import annotations

import math
from bisect import bisect_left
from typing import Dict, List, Optional, Sequence, Tuple

from . import config as C
from . import clock
from .panel import NameSeries, Panel, dvmed60, band_class_bps

# Exclusion reason codes (measured, counted, disclosed — never silent).
X_NO_SESSION = "NO_SESSION_AFTER_ACCEPTANCE"     # no direction session exists
X_NO_ENTRY_SESSION = "NO_ENTRY_SESSION"          # direction exists, entry does not
X_CORP_ACTION_WINDOW = "CORP_ACTION_IN_WINDOW"   # R2-2 div/split ex-date in window
X_ENTRY_FILL = "ENTRY_BAR_UNFILLABLE_B1B2"       # extreme print or volume-0 entry bar
X_ZERO_DIRECTION = "ZERO_DIRECTION_SESSION_MOVE" # close == open on direction session (r3 AMB-11: excluded+counted)
X_BELOW_DV_FLOOR = "BELOW_DV_FLOOR_AT_DECISION"  # frozen eligibility floor
X_FOLD_BOUNDARY_NO_WINDOW = "FOLD_BOUNDARY_NO_WINDOW"  # entry past fold end
X_EMPTY_PANEL = "NO_PANEL_FOR_TICKER"
# r3 AMB-7: an unfillable EXIT bar no longer excludes — the exit rolls
# forward to the next clean bar; exhaustion exits at the last permissible
# bar flagged delisting_exit. Notes recorded on the booked record:
NOTE_EXIT_ROLLED = "EXIT_ROLLED_B1X1"
NOTE_EXIT_ROLL_EXHAUSTED = "EXIT_ROLL_EXHAUSTED_AT_LAST_BAR"

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


def resolve_entry_open_anchored(
    ns: Optional[NameSeries], instant_et
) -> Tuple[str, Optional[int]]:
    """A2 entry law (R2-3 verbatim, r3 defect D-1): FIRST session whose
    09:30 ET OPEN occurs strictly after the acceptance instant.

    Returns (status, entry_idx); status in {"OK", X_NO_ENTRY_SESSION,
    X_EMPTY_PANEL}. The A2 anchor is long-only at that open — there is no
    A1-style direction session in the A2 law (record field stays null).
    """
    if ns is None or len(ns) == 0:
        return X_EMPTY_PANEL, None
    from datetime import date as _date
    lo, hi, ans = 0, len(ns) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        d = _date.fromisoformat(ns.dates[mid])
        if clock.session_open_instant(d) > instant_et:
            ans = mid
            hi = mid - 1
        else:
            lo = mid + 1
    if ans is None:
        return X_NO_ENTRY_SESSION, None
    return "OK", ans


def window_dates(ns: NameSeries, entry_i: int, exit_i: int) -> List[str]:
    return ns.dates[entry_i : exit_i + 1]


def corp_action_in_window(ca: dict, ticker: str, dates: Sequence[str]) -> bool:
    """R2-2 check on the FINAL window, r3-canonical (AMB-13/AMB-15):
    - the window is the full CALENDAR interval [first .. last] of the
      window's session dates — an ex-date on a non-session day inside the
      interval still contaminates;
    - the name's ex-date table is resolved case-insensitively (D-2): exact
      key first, then the casefolded key.
    """
    acts = ca.get(ticker)
    if acts is None:
        acts = ca.get(ticker.lower())
    if not acts:
        return False
    start, end = dates[0], dates[-1]
    for kind in ("div", "split"):
        ds = acts.get(kind, ())
        i = bisect_left(ds, start)
        if i < len(ds) and ds[i] <= end:
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
    fold = clock.fold_of_et(acceptance_utc)
    if fold == "OUTSIDE":
        return None, {"event_id": event_id, "reason": "OUTSIDE_WINDOW", "fold": fold,
                      "ticker": ticker, "cik": cik}

    if direction_override is not None:
        # A2 (r3 D-1): entry = FIRST session open strictly after the
        # acceptance instant; long-only; no A1-style direction session.
        status, entry_i = resolve_entry_open_anchored(ns, instant_et)
        if status != "OK":
            return None, {"event_id": event_id, "reason": status, "fold": fold,
                          "ticker": ticker, "cik": cik}
        dir_i = None
        direction = direction_override
    else:
        status, dir_i, entry_i = resolve_direction_entry(ns, instant_et)
        if status != "OK":
            return None, {"event_id": event_id, "reason": status, "fold": fold,
                          "ticker": ticker, "cik": cik}
        # direction (A1): sign of RAW (close - open) of the direction session
        diff = ns.close[dir_i] - ns.open[dir_i]
        if diff > 0:
            direction = "LONG"
        elif diff < 0:
            direction = "SHORT"
        else:
            # r3 AMB-11 CANONICAL: tie -> excluded, counted
            return None, {"event_id": event_id, "reason": X_ZERO_DIRECTION,
                          "fold": fold, "ticker": ticker, "cik": cik}

    assert ns is not None and entry_i is not None
    # ---- entry-bar fillability (r3 order: entry laws first) ----
    if not ns.fill_ok[entry_i]:
        return None, {"event_id": event_id, "reason": X_ENTRY_FILL,
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
    # the maximum permissible exit index under the clamps above
    exit_cap = ff_i if forced_flat else len(ns) - 1

    # ---- exit fillability: r3 AMB-7 roll-forward (no longer an exclusion) ----
    notes: List[str] = []
    if not ns.fill_ok[last_i]:
        while last_i < exit_cap and not ns.fill_ok[last_i]:
            last_i += 1
        if not ns.fill_ok[last_i]:
            # exhausted at the last permissible bar: exit there, flagged
            delisting_exit = True
            notes.append(NOTE_EXIT_ROLL_EXHAUSTED)
        else:
            notes.append(NOTE_EXIT_ROLLED)

    # ---- exclusions on the FINAL window (r3 AMB-13: after the roll) ----
    win_dates = window_dates(ns, entry_i, last_i)
    if corp_action_in_window(corp_actions, ticker, win_dates):
        return None, {"event_id": event_id, "reason": X_CORP_ACTION_WINDOW,
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
        "direction_session": ns.dates[dir_i] if dir_i is not None else None,
        "direction": direction,
        "entry_session": ns.dates[entry_i],
        "entry_price": ns.open[entry_i],          # raw open (R2-1)
        "exit_session": ns.dates[last_i],
        "exit_price": ns.close[last_i],           # raw close (R2-1)
        "hold_sessions": hold_sessions,
        "exclusions_applied": notes,              # exit-roll notes; [] = clean window
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
