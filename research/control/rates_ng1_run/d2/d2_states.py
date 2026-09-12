"""RATES-NG1 D2 state reconstruction: representation mapping + the
decision-STATE series of the four D1 proposals and of the five
ancestry shadows (P-12 commit-1 artifact).

Scope law: this module builds decision-STATE series only.  No outcome,
no PnL, no cost number and no correlation value is computed here.

Representation mapping law (identical for all four proposals, per
their representation_identity blocks):

- grid: p2_grid_census.json -- 2170 common-grid sessions
  (curve row AND all four ETP bars), 1918 bookable instants after the
  252-session warmup carve-out; each instant materializes
  {decision_session, decision_utc, readable_bar_date, session_index}.
- readable-bar law (V7 close+1): the state input of an instant is
  read at that instant's ``readable_bar_date`` (the previous grid
  session); no same-day reads.
- event clock (lane A4 and the shadow event clock): the 3555 P2
  auction-announcement mappings in p2_auction_eligibility.json, joined
  to p0_auction_census.json by cusip for issueDate.
- day-event PIT law (P1 clock): a day-dated official date (auction,
  issue) is crossed at the FIRST common-grid session STRICTLY AFTER
  it; the same-day close is refused.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from typing import Callable, Mapping, Sequence

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.rates_ng1 import plane_adapter as pa  # noqa: E402

from research.control.rates_ng1_run.d2 import d2_frozen_defaults as fd

SCHEMA = "rates_ng1_run/d2_states@1"

NULL = None  # explicit "state undefined at this instant" marker


# ------------------------------------------------------------------ #
# Pure calendar helpers
# ------------------------------------------------------------------ #
def first_grid_index_strictly_after(day_iso: str,
                                    grid_dates: Sequence[str]) -> int | None:
    """First common-grid session index STRICTLY after ``day_iso``
    (the P1 day-event PIT law); None when the grid has no later
    session."""
    for i, d in enumerate(grid_dates):
        if d > day_iso:
            return i
    return None


def month_of(iso_date: str) -> str:
    return iso_date[:7]


# ------------------------------------------------------------------ #
# Pure state builders (synthetic-fixture friendly)
# ------------------------------------------------------------------ #
def build_dgs10_level_lookup(
        observations: Sequence[Mapping[str, object]],
) -> tuple[Callable[[str], float | None], dict]:
    """Lookup ``level(iso_date) -> float`` = last DGS10 observation at
    or before the date (PIT-readable stale fact), or None when the
    last observation is older than the frozen staleness bound.
    Observations with non-numeric values are skipped (never inferred).
    """
    stale = int(fd.DGS10_LEVEL["max_staleness_calendar_days"])
    pts: list[tuple[str, float]] = []
    for obs in observations:
        raw = str(obs.get("value", "")).strip()
        try:
            val = float(raw)
        except ValueError:
            continue
        pts.append((str(obs["date"]), val))
    pts.sort()

    def level(iso_date: str) -> float | None:
        best: tuple[str, float] | None = None
        for d, v in pts:
            if d <= iso_date:
                best = (d, v)
            else:
                break
        if best is None:
            return None
        age = (dt.date.fromisoformat(iso_date)
               - dt.date.fromisoformat(best[0])).days
        if age > stale:
            return None
        return best[1]

    meta = {"observations_used": len(pts)}
    return level, meta


def shadow_dgs10_level_state(
        grid_dates: Sequence[str],
        instants: Sequence[Mapping[str, object]],
        level_fn: Callable[[str], float | None]) -> list[float | None]:
    """Shadow (a) dgs10_level_trailing_state decision-state series.

    At each bookable instant (grid index j = session_index): +1 if the
    DGS10 level at the readable bar is strictly above the median of
    the trailing ``trailing_window_sessions`` grid sessions ending at
    that readable bar (inclusive); else -1; None when any needed level
    is undefined.
    """
    win = int(fd.DGS10_LEVEL["trailing_window_sessions"])
    # Level at each grid session's own date (a grid session date d is
    # PIT-readable at the NEXT session's instant; the trailing window
    # below ends at the instant's readable bar = grid_dates[j-1]).
    lvl_by_grid = [level_fn(d) for d in grid_dates]
    out: list[float | None] = []
    for inst in instants:
        j = int(inst["session_index"])
        b = j - 1  # readable bar sits at grid index j-1
        if b - win + 1 < 0:
            out.append(None)
            continue
        window = [lvl_by_grid[k] for k in range(b - win + 1, b + 1)]
        cur = lvl_by_grid[b]
        if cur is None or any(v is None for v in window):
            out.append(None)
            continue
        med = float(sorted(window)[win // 2]) if win % 2 == 1 else (
            float(window[win // 2 - 1] + window[win // 2]) / 2.0)
        out.append(1.0 if cur > med else -1.0)
    return out


def shadow_reaction_direction_state(
        grid_dates: Sequence[str],
        instants: Sequence[Mapping[str, object]],
        event_indices: Sequence[int],
        level_fn: Callable[[str], float | None]) -> list[float | None]:
    """Shadow (b) fx_reaction_direction decision-state series.

    ``event_indices``: grid session_index of each event's P2 decision
    session.  Reaction sign at an event = sign(level(b_e) -
    level(b_prev)) where b_e is the readable bar of the event's
    decision instant (grid index j-1) and b_prev the one before it
    (grid index j-2).  The sign is held over
    ``holding_sessions`` grid sessions starting at the event's
    decision session; later events overwrite earlier ones
    (last-write-wins).  Instants outside every window carry 0.0.
    """
    hold = int(fd.FX_REACTION_DIRECTION["holding_sessions"])
    pos: dict[int, float] = {}
    for j in sorted({int(e) for e in event_indices}):
        if j - 2 < 0:
            continue
        cur = level_fn(grid_dates[j - 1])
        prev = level_fn(grid_dates[j - 2])
        if cur is None or prev is None or cur == prev:
            sign = 0.0
        else:
            sign = 1.0 if cur > prev else -1.0
        for k in range(j, min(j + hold, len(grid_dates))):
            pos[k] = sign
    out: list[float | None] = []
    for inst in instants:
        j = int(inst["session_index"])
        out.append(pos.get(j, 0.0))
    return out


def shadow_release_order_state(
        grid_dates: Sequence[str],
        instants: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]]) -> list[float | None]:
    """Shadow (c) fx_release_order decision-state series.

    Within each announcement month: the first announced event's
    security type sets the month's order sign (Bill -> +1, coupon ->
    -1), active from that event's P2 decision session (first grid
    session strictly after the announcement) to month end; 0 before.
    """
    first_by_month: dict[str, tuple[str, str]] = {}
    for ev in events:
        m = month_of(str(ev["announcementDate"]))
        cur = first_by_month.get(m)
        if cur is None or str(ev["announcementDate"]) < cur[0]:
            first_by_month[m] = (str(ev["announcementDate"]),
                                 str(ev["securityType"]))
    month_sign: dict[str, float] = {}
    month_start_idx: dict[str, int] = {}
    for m, (ann, stype) in first_by_month.items():
        month_sign[m] = (float(fd.FX_RELEASE_ORDER["bill_first_sign"])
                         if stype == "Bill"
                         else float(fd.FX_RELEASE_ORDER["coupon_first_sign"]))
        idx = first_grid_index_strictly_after(ann, grid_dates)
        month_start_idx[m] = idx if idx is not None else len(grid_dates)
    out: list[float | None] = []
    for inst in instants:
        j = int(inst["session_index"])
        session = str(inst["decision_session"])
        m = month_of(session)
        start = month_start_idx.get(m)
        if start is None or j < start:
            out.append(0.0)
        else:
            out.append(month_sign[m])
    return out


def shadow_momentum_63s_state(
        grid_dates: Sequence[str],
        instants: Sequence[Mapping[str, object]],
        leg_closes: Mapping[str, Mapping[str, float]]) -> list[float | None]:
    """Shadow (d) momentum_63s decision-state series.

    Per leg: sign of the RAW-close return from the readable bar 63
    grid sessions before the instant's readable bar to the instant's
    readable bar.  Pooled state = equal-weight mean of the four leg
    signs; None when any leg lacks either close.
    """
    lb = int(fd.MOMENTUM_63S["lookback_sessions"])
    out: list[float | None] = []
    for inst in instants:
        j = int(inst["session_index"])
        b = j - 1
        b0 = b - lb
        if b0 < 0:
            out.append(None)
            continue
        d_hi, d_lo = grid_dates[b], grid_dates[b0]
        signs: list[float] = []
        for leg in fd.ETP_LEGS:
            closes = leg_closes.get(leg, {})
            p_hi, p_lo = closes.get(d_hi), closes.get(d_lo)
            if p_hi is None or p_lo is None or p_lo == 0.0:
                signs = []
                break
            ret = p_hi / p_lo - 1.0
            signs.append(1.0 if ret > 0 else (-1.0 if ret < 0 else 0.0))
        out.append(sum(signs) / len(signs) if signs else None)
    return out


def shadow_dow_tue_state(
        instants: Sequence[Mapping[str, object]]) -> list[float | None]:
    """Shadow (e) generic_dow_tue decision-state series: +1 on
    Tuesday decision sessions, 0 otherwise."""
    out: list[float | None] = []
    for inst in instants:
        d = dt.date.fromisoformat(str(inst["decision_session"]))
        out.append(float(fd.GENERIC_DOW_TUE["tuesday_sign"])
                   if d.weekday() == 1
                   else float(fd.GENERIC_DOW_TUE["other_day_sign"]))
    return out


def proposal_state_a4_p1(
        grid_dates: Sequence[str],
        instants: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]]) -> list[float | None]:
    """RATESNG1-A4-P1 own decision state: settlement-window
    concentration bucket sign (frozen defaults in
    fd.A4_P1_CONCENTRATION)."""
    k1 = int(fd.A4_P1_CONCENTRATION["k1_sessions"])
    k2 = int(fd.A4_P1_CONCENTRATION["k2_sessions"])
    # Per event: (issueDate, announcement PIT decision session index).
    issues: list[tuple[str, int]] = []
    for ev in events:
        ann_j = first_grid_index_strictly_after(str(ev["announcementDate"]),
                                                grid_dates)
        if ann_j is None:
            continue
        issues.append((str(ev["issueDate"]), ann_j))
    issues.sort(key=lambda t: t[1])
    ann_js = [t[1] for t in issues]  # ascending (sort invariant check)
    if ann_js != sorted(ann_js):
        raise AssertionError("issues not sorted by announcement index")
    counts: list[float] = []
    for inst in instants:
        j = int(inst["session_index"])
        session = str(inst["decision_session"])
        lo = grid_dates[max(0, j - k1)]
        hi = grid_dates[min(len(grid_dates) - 1, j + k2)]
        c = 0
        for iss, ann_j in issues:
            # PIT filter: announced at or before this decision session
            # (the event's announcement decision session index <= j;
            # issues sorted by ann_j so we can break early).
            if ann_j > j:
                break
            if lo <= iss <= hi:
                c += 1
        counts.append(float(c))
    med = _median(counts)
    return [(1.0 if c > med else (-1.0 if c < med else 0.0))
            for c in counts]


def proposal_state_a4_p2(
        grid_dates: Sequence[str],
        instants: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]]) -> list[float | None]:
    """RATESNG1-A4-P2 own decision state: pipeline stage sign of the
    nearest event (frozen defaults in fd.A4_P2_STAGE)."""
    signs = fd.A4_P2_STAGE["stage_signs"]
    hold = int(fd.A4_P2_STAGE["settlement_era_sessions"])
    bounds: list[tuple[int, int, int, int]] = []  # ann_j, auc_j, iss_j, end_j
    for ev in events:
        ann_j = first_grid_index_strictly_after(
            str(ev["announcementDate"]), grid_dates)
        auc_j = first_grid_index_strictly_after(str(ev["auctionDate"]),
                                                grid_dates)
        iss_j = first_grid_index_strictly_after(str(ev["issueDate"]),
                                                grid_dates)
        if ann_j is None or auc_j is None or iss_j is None:
            continue
        bounds.append((ann_j, auc_j, iss_j, iss_j + hold))
    bounds.sort()
    ann_list = [b[0] for b in bounds]
    out: list[float | None] = []
    for inst in instants:
        j = int(inst["session_index"])
        # nearest event: latest ann_j <= j (bounds sorted by ann_j;
        # bisect-style linear scan is fine at this size).
        cur = None
        for b in bounds:
            if b[0] <= j:
                cur = b
            else:
                break
        if cur is None:
            out.append(0.0)
            continue
        ann_j, auc_j, iss_j, end_j = cur
        if j < auc_j:
            out.append(float(signs["announcement"]))
        elif j < iss_j:
            out.append(float(signs["auction"]))
        elif j < end_j:
            out.append(float(signs["settlement"]))
        else:
            out.append(0.0)
    return out


def _ols_residual_series(
        y: Sequence[float | None], x: Sequence[float | None],
        min_past: int) -> list[float | None]:
    """PIT-expanding OLS-with-intercept residual of ``y`` on ``x``:
    at instant i the coefficients are fitted on the strictly-past
    defined pairs only; the residual at i uses those coefficients.
    Instants before the first legal fit are None."""
    out: list[float | None] = []
    sx: list[float] = []
    sy: list[float] = []
    n = len(y)
    for i in range(n):
        if len(sx) >= min_past:
            mx = sum(sx) / len(sx)
            my = sum(sy) / len(sy)
            sxx = sum((a - mx) ** 2 for a in sx)
            sxy = sum((a - mx) * (b - my) for a, b in zip(sx, sy))
            if sxx > 0.0:
                beta = sxy / sxx
                alpha = my - beta * mx
                if y[i] is not None and x[i] is not None:
                    out.append(float(y[i]) - (alpha + beta * float(x[i])))
                    sx.append(float(x[i]))
                    sy.append(float(y[i]))
                else:
                    out.append(None)
                continue
        if y[i] is not None and x[i] is not None:
            sx.append(float(x[i]))
            sy.append(float(y[i]))
        out.append(None)
    return out


def _median(vals: Sequence[float]) -> float:
    s = sorted(vals)
    n = len(s)
    if n == 0:
        raise ValueError("median of empty series")
    return float(s[n // 2]) if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def proposal_state_a5_p1(
        grid_dates: Sequence[str],
        instants: Sequence[Mapping[str, object]],
        curve_by_date: Mapping[str, Mapping[str, float]]) -> list[float | None]:
    """RATESNG1-A5-P1 own decision state: curvature-gated slope sign
    on the level-orthogonalized curve shape (frozen defaults in
    fd.A5_P1_CURVATURE_GATED_SLOPE)."""
    t_slope = fd.A5_P1_CURVATURE_GATED_SLOPE["slope_tenors"]
    t_curv = fd.A5_P1_CURVATURE_GATED_SLOPE["curvature_tenors"]
    t_lvl = fd.A5_P1_CURVATURE_GATED_SLOPE["level_tenor"]
    min_past = int(fd.A5_P1_CURVATURE_GATED_SLOPE["min_past_points"])

    def val(d: str, tenor: str) -> float | None:
        v = curve_by_date.get(d, {}).get(tenor)
        return None if v is None else float(v)

    slope: list[float | None] = []
    curv: list[float | None] = []
    lvl: list[float | None] = []
    for inst in instants:
        b = str(inst["readable_bar_date"])
        y2, y10, y30 = val(b, "2 Yr"), val(b, "10 Yr"), val(b, "30 Yr")
        if None in (y2, y10, y30):
            slope.append(None)
            curv.append(None)
            lvl.append(None)
            continue
        slope.append(y30 - y2)
        curv.append(y2 - 2.0 * y10 + y30)
        lvl.append(y10)
    res_s = _ols_residual_series(slope, lvl, min_past)
    res_c = _ols_residual_series(curv, lvl, min_past)
    defined_s = [v for v in res_s if v is not None]
    defined_c = [v for v in res_c if v is not None]
    if not defined_s or not defined_c:
        return [None] * len(instants)
    cut_s, cut_c = _median(defined_s), _median(defined_c)
    out: list[float | None] = []
    for a, b in zip(res_s, res_c):
        if a is None or b is None:
            out.append(None)
        elif a > cut_s and b > cut_c:
            out.append(1.0)
        elif a < cut_s and b < cut_c:
            out.append(-1.0)
        else:
            out.append(0.0)
    return out


def proposal_state_a5_p2(
        instants: Sequence[Mapping[str, object]],
        curve_by_date: Mapping[str, Mapping[str, float]]) -> list[float | None]:
    """RATESNG1-A5-P2 own decision state: level-orthogonalized
    front-versus-belly residual sign (frozen defaults in
    fd.A5_P2_FRONT_VS_BELLY)."""
    front_t = fd.A5_P2_FRONT_VS_BELLY["front_tenor"]
    belly_t = fd.A5_P2_FRONT_VS_BELLY["belly_tenor"]
    lvl_t = fd.A5_P2_FRONT_VS_BELLY["level_tenor"]
    min_past = int(fd.A5_P2_FRONT_VS_BELLY["min_past_points"])
    resid_raw: list[float | None] = []
    lvl: list[float | None] = []
    for inst in instants:
        b = str(inst["readable_bar_date"])
        f = curve_by_date.get(b, {}).get(front_t)
        bl = curve_by_date.get(b, {}).get(belly_t)
        lv = curve_by_date.get(b, {}).get(lvl_t)
        if None in (f, bl, lv):
            resid_raw.append(None)
            lvl.append(None)
        else:
            resid_raw.append(float(f) - float(bl))
            lvl.append(float(lv))
    res = _ols_residual_series(resid_raw, lvl, min_past)
    defined = [v for v in res if v is not None]
    if not defined:
        return [None] * len(instants)
    cut = _median(defined)
    return [None if v is None else
            (1.0 if v > cut else (-1.0 if v < cut else 0.0))
            for v in res]


# ------------------------------------------------------------------ #
# Plane-backed loaders (representation mapping, verify-on-read)
# ------------------------------------------------------------------ #
def load_representation(worktree_root: str) -> dict:
    """Load the shared P2 representation (grid census + auction
    mappings + census join) and the plane-verified series inputs.
    Every consumption goes through consume_via_plane (frozen-set gate,
    digest verify-on-read); any drift raises BLOCKED_DATA."""
    root = worktree_root
    plane = pa.RatesNG1Plane(
        manifest_path=os.path.join(
            root, "research", "control", "rates_ng1_run",
            "substrate_manifest.json"),
        raw_root=os.path.join(
            root, "research", "assets", "rates_ng1", "raw_substrate"))

    with open(os.path.join(root, "research", "control", "rates_ng1_run",
                           "p2_grid_census.json"), "r",
              encoding="utf-8") as fh:
        grid_census = json.load(fh)
    with open(os.path.join(root, "research", "control", "rates_ng1_run",
                           "p2_auction_eligibility.json"), "r",
              encoding="utf-8") as fh:
        elig = json.load(fh)
    with open(os.path.join(root, "research", "control", "rates_ng1_run",
                           "p0_auction_census.json"), "r",
              encoding="utf-8") as fh:
        auc = json.load(fh)

    instants = grid_census["census"]["bookable_instants"]
    grid_dates = list(grid_census["census"]["grid_dates"])
    mappings = list(elig["mappings"])
    census_events = {str(ev["cusip"]): ev
                     for ev in auc["census"]["events"]}
    events: list[dict] = []
    for m in mappings:
        ev = census_events[str(m["cusip"])]
        events.append({
            "cusip": str(m["cusip"]),
            "announcementDate": str(m["announcementDate"]),
            "auctionDate": str(m["auctionDate"]),
            "issueDate": str(ev["issueDate"]),
            "securityType": str(m["securityType"]),
            "event_index": int(m["event_index"]),
        })
    events.sort(key=lambda e: (e["announcementDate"], e["event_index"]))

    # DGS10 through the plane (verify-on-read).
    res = plane.consume_via_plane(fd.DGS10_LEVEL["entry"])
    dgs10_obs = json.loads(
        open(plane.raw_path(fd.DGS10_LEVEL["entry"]), "rb").read()
        .decode("utf-8"))["observations"]
    level_fn, level_meta = build_dgs10_level_lookup(dgs10_obs)

    # Curve tenor series on the grid (per-year official CSVs).
    tenors = ("2 Yr", "5 Yr", "10 Yr", "30 Yr")
    years = sorted({int(d[:4]) for d in grid_dates})
    curve_by_date: dict[str, dict[str, float]] = {}
    for y in years:
        rows = plane.curve_rows_for_year(y)
        for r in rows:
            d = r["date"]
            if d not in set(grid_dates):
                continue
            rec: dict[str, float] = {}
            for t in tenors:
                raw = (r.get(t) or "").strip()
                try:
                    rec[t] = float(raw)
                except ValueError:
                    pass
            curve_by_date[d] = rec

    # ETP RAW closes (per leg).
    leg_closes: dict[str, dict[str, float]] = {}
    for leg in fd.ETP_LEGS:
        rows = plane.etp_rows(leg)
        leg_closes[leg] = {str(r["date"]): float(r["close"]) for r in rows}

    # Event decision sessions are materialized by P2 on the FULL
    # 2170-session grid (2018 announcements land in the warmup region,
    # before the first bookable instant); index them against
    # grid_dates, not bookable_instants.  Every mapping is re-verified
    # against the P1 day-event PIT law (research/assets/rates_ng1/
    # clock.py::first_decision_after_pit semantics: the decision
    # session is the first grid session STRICTLY after the announced
    # NY day) via the O(1) equivalent property below.
    grid_idx_by_date = {d: i for i, d in enumerate(grid_dates)}
    event_indices = []
    for m in mappings:
        ann = str(m["announcementDate"])
        idx = grid_idx_by_date.get(str(m["decision_session"]))
        if idx is None:
            raise ValueError(
                f"mapping decision_session {m['decision_session']!r} is "
                "not a session on the P2 common grid")
        if grid_dates[idx] <= ann or (idx > 0 and grid_dates[idx - 1] > ann):
            raise ValueError(
                f"mapping for announcement {ann} violates the P1 "
                "first-session-strictly-after PIT law")
        event_indices.append(idx)
    return {
        "plane": plane,
        "grid_dates": grid_dates,
        "instants": instants,
        "mappings": mappings,
        "events": events,
        "event_indices": event_indices,
        "level_fn": level_fn,
        "level_meta": level_meta,
        "curve_by_date": curve_by_date,
        "leg_closes": leg_closes,
        "consumed": {
            "dgs10_entry": fd.DGS10_LEVEL["entry"],
            "dgs10_sha256": res["sha256_measured"],
        },
    }
