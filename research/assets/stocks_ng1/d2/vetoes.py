"""STOCKS-NG1 D2 veto engine: the FIFTEEN-entry veto set.

Names are the V13 D2 audit's veto set verbatim ($L1194-1213).  The V13
constructions that read the V9 multivintage accounting panel / the V10
timing and revision layers are rebuilt here as GENERIC family forms on
the consumption surfaces this cycle owns (EODHD prices + the pinned
Form-4 stream), per the dispatch packet: "generic factor constructions
tu EODHD prices + stream".  Every construction is a documented,
deterministic (entity, decision-close) -> float-or-None function; None =
UNMEASURED and fails the novelty gate closed (V13 rule, never a pass by
absence).

Construction register (V13 provenance -> generic NG1 form):

  1 momentum_63s      price form VERBATIM: adj[i]/adj[i-62]-1, i = last
                      bar <= t (through-t close, grid convention).
  2 semivariance_share price form VERBATIM: share of squared negative
                      log-returns in total squared log-returns over the
                      63 bars ending at i; needs >= 30 valid returns.
  3 vol_level         price form VERBATIM: sqrt(variance) of log-returns
                      over the same window; needs >= 30 valid returns.
  4 wc_stock_intensity V13 (AssetsCurrent-LiabilitiesCurrent)/Assets ->
                      generic: disposal-side share of the entity's
                      non-derivative transaction flow in the trailing 63
                      sessions (nndD/nnd).
  5 goodwill_bloat    V13 Goodwill/Assets -> generic: NON-open-market
                      share of the entity's non-derivative insider flow
                      in the trailing 63 sessions (rows coded other than
                      P/S: option exercises, grants, gifts, tax
                      withholding - contingent-claim value vs cash-
                      market value).  (Construction incident: the first
                      generic form - derivative-table share - had
                      provably empty support: the pinned stream carries
                      zero derivative-table rows; replaced before any
                      rho for this entry existed.)
  6 f1_accrual_flow   V13 dAR+dInv-dAP over Assets -> generic: net
                      non-derivative insider dollar flow (V_A - V_D)
                      normalized by ADV63 (days-of-flow), trailing 63
                      sessions.
  7 depletion_interaction V13 (RE_prior-RE_now-Cash)/Assets -> generic:
                      max drawdown of the adjusted close over the
                      trailing 252 sessions ending at i (depletion
                      state of the price series).
  8 cash_level        V13 Cash/Assets -> generic: log ADV63 dollar
                      volume (liquidity level).
  9 sector_exposure_form  V13 form VERBATILY: sector equal-weight mean
                      of the momentum_63s cross-section at t, computed
                      over all priced cohort entities of the sector.
 10 own_z_characteristic_form V10/V13 deseasonalized own_z -> generic:
                      z-score of the entity's current 63-session
                      acceptance-event count (distinct accessions)
                      against its own prior non-overlapping 63-session
                      block counts (>= 6 blocks, sd > 0).
 11 revision_direction_breadth_form V10/V13 share of down-moving
                      revision groups -> generic: share of the entity's
                      acceptance sessions in the trailing 800 calendar
                      days that are net-disposition sessions (vD > vA).
 12 v11_cadence_latency_form V11 share of late inter-arrivals ->
                      generic: share of the entity's in-window (800d)
                      acceptances whose calendar gap from the previous
                      acceptance exceeds 460 days.
 13 filing_event_reaction_shadow V13 form (5-bar SPY-residual initial
                      reaction sign at the entity's most recent
                      filer-event within 800d) -> generic with event =
                      the entity's most recent Form-4 acceptance
                      session; sign normalized to float.
 14 v12_chain_structure_form V12 deep_share over depth>=2 groups ->
                      generic: share of the entity's in-window (800d)
                      acceptance sessions carrying >= 2 distinct
                      accessions (multi-doc chain sessions); defined
                      iff >= 4 in-window sessions (MIN_GROUPS_Q).
 15 v12_death_event_form V12/V13 sector-peer death-event net leg
                      weight, DAILY-GRID ADAPTATION: the V13 builder
                      was defined only AT exact event dates (its n was
                      365-728 on the quarterly grid); on the daily grid
                      the faithful state form is the accumulated net
                      leg weight over death events in the trailing 800
                      calendar days ending at t.  Trigger set =
                      DEAD_PRICE_CONFIRMED cohort peers with a bar <=
                      death date within 800d; class ORDERLY +1 (gap <=
                      10d) else GAPPED -1; basket = same-sector
                      ALIVE_EVIDENCED peers with >= 63 bars through the
                      event date, dying names never held.
"""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from datetime import date, timedelta

from .core import (DD_WINDOW, MIN_GROUPS_Q, STALE_DAYS, last_bar_le)


def _win63_bars(C, cik, t_iso):
    """(i, ok-count, prefix tuple) for the 63-bar window ending at the
    last bar <= t; None when the window is unavailable."""
    s = C.series.get(cik)
    if s is None:
        return None
    i = bisect_right(s["dates"], t_iso) - 1
    if i < 62:
        return None
    return i


def veto_momentum(C, e, t):
    i = _win63_bars(C, e, t)
    if i is None:
        return None
    s = C.series[e]
    w0, w1 = s["adj"][i - 62], s["adj"][i]
    if w0 is None or w1 is None or w0 <= 0 or w1 <= 0:
        return None
    return w1 / w0 - 1.0


def _vol_core(C, e, t):
    i = _win63_bars(C, e, t)
    if i is None:
        return None
    s = C.series[e]
    s_lr, s_l2, s_dn, s_ok = s["pre"]
    lo = i - 62
    nret = s_ok[i] - s_ok[lo]
    if nret < 30:
        return None
    tot = s_l2[i] - s_l2[lo]
    dn = s_dn[i] - s_dn[lo]
    mu = (s_lr[i] - s_lr[lo]) / nret
    var = tot / nret - mu * mu
    return {"semi": (dn / tot if tot > 0 else None),
            "vol": (math.sqrt(var) if var > 0 else 0.0),
            "nret": nret}


def veto_semivariance(C, e, t):
    v = _vol_core(C, e, t)
    return None if v is None else v["semi"]


def veto_vol(C, e, t):
    v = _vol_core(C, e, t)
    return None if v is None else v["vol"]


def _sess_pfx(C, e, t, key, days=None, is_value=False):
    """Prefix-window sum of an entity aggregate; trailing 63 sessions by
    default, or a trailing calendar window."""
    from .exposures import _win63, _win_cal, _pfx, has_E
    if not has_E(C, e):
        return None
    b = _win_cal(C, e, t, days) if days else _win63(C, e, t)
    if b is None:
        return None
    return _pfx(C, e, key, b, is_value=is_value)


def veto_wc_stock_intensity(C, e, t):
    n_all = _sess_pfx(C, e, t, "nnd")
    if not n_all:
        return None
    n_d = _sess_pfx(C, e, t, "nndD")
    return n_d / n_all


def veto_goodwill_bloat(C, e, t):
    """V13 Goodwill/Assets -> generic: NON-open-market share of the
    entity's non-derivative insider flow in the trailing 63 sessions
    (rows coded other than P open-market purchase / S open-market sale:
    option exercises, grants, gifts, tax withholding - contingent-claim
    value vs cash-market value).

    CONSTRUCTION INCIDENT (recorded in the artifact): the first generic
    form (derivative-table share of all rows) was replaced BEFORE any
    rho for this entry existed: the pinned stream carries ZERO
    derivative-table rows (546,039 of 546,039 rows are table=
    nonDerivative; the derivative table is a separate, unstaged stream
    per the frozen parse contract), so that form had provably empty
    support on this cycle's consumption surfaces."""
    n_all = _sess_pfx(C, e, t, "rows_all")
    if not n_all:
        return None
    n_ps = _sess_pfx(C, e, t, "nPS")
    return 1.0 - (n_ps / n_all)


def veto_f1_accrual_flow(C, e, t):
    v_a = _sess_pfx(C, e, t, "vA", is_value=True)
    v_d = _sess_pfx(C, e, t, "vD", is_value=True)
    if v_a is None or v_d is None:
        return None
    from .core import adv63
    adv = adv63(C, e, t)
    if adv is None or adv <= 0:
        return None
    return (v_a - v_d) / adv


def veto_depletion_interaction(C, e, t, cache=None):
    """Max drawdown of the adjusted close over the trailing 252 sessions
    ending at the last bar <= t (partial window when history is shorter;
    needs >= 63 bars).  Cached per (e, i) on the context."""
    s = C.series.get(e)
    if s is None:
        return None
    i = bisect_right(s["dates"], t) - 1
    if i < 62:
        return None
    key = (e, i)
    cache = getattr(C, "_dd_cache", None)
    if cache is None:
        cache = C._dd_cache = {}
    if key in cache:
        return cache[key]
    adj = s["adj"]
    lo = max(0, i - DD_WINDOW + 1)
    peak = None
    mdd = 0.0
    for j in range(lo, i + 1):
        a = adj[j]
        if a is None or a <= 0:
            continue
        if peak is None or a > peak:
            peak = a
        dd = (peak - a) / peak if peak > 0 else 0.0
        if dd > mdd:
            mdd = dd
    out = mdd if peak is not None else None
    cache[key] = out
    return out


def veto_cash_level(C, e, t):
    from .core import adv63
    adv = adv63(C, e, t)
    if adv is None or adv <= 0:
        return None
    return math.log(adv)


def veto_sector_form(C, e, t):
    """Sector equal-weight mean of momentum_63s at t over all priced
    cohort entities of the sector (V13 form).  One pass per date builds
    every sector's mean (cached on the context)."""
    sec = C.bookable.get(e, {}).get("sector", "")
    per_date = getattr(C, "_sector_mean_by_date", None)
    if per_date is None:
        per_date = C._sector_mean_by_date = {}
    if t in per_date:
        return per_date[t].get(sec)
    sums = {}
    for e2 in sorted(C.series):
        sec2 = C.bookable.get(e2, {}).get("sector", "")
        if not sec2:
            continue
        v = veto_momentum(C, e2, t)
        if v is not None:
            acc = sums.setdefault(sec2, [0.0, 0])
            acc[0] += v
            acc[1] += 1
    per_date[t] = {k: (sv / n) for k, (sv, n) in sums.items()}
    return per_date[t].get(sec)


def veto_own_z(C, e, t):
    """z of the current 63-session acceptance-event count against the 8
    prior non-overlapping 63-session blocks (own-history
    deseasonalization); needs >= 6 blocks and sd > 0."""
    from .exposures import _win63, _pfx, has_E
    if not has_E(C, e):
        return None
    gi = C.sess_idx[t]
    E = C.E[e]
    b = _win63(C, e, t)
    if b is None:
        return None
    cur = _pfx(C, e, "docs", b)
    # prior block k (k = 0..7) covers grid session indices
    # [gi - 125 - 63k, gi - 63 - 63k]: strictly prior to and
    # non-overlapping with the current window [gi-62, gi]
    blocks = []
    for k in range(8):
        hi_k = gi - 63 - 63 * k
        lo_k = hi_k - 62
        lo_e = bisect_left(E["sess_idx"], lo_k)
        hi_e = bisect_right(E["sess_idx"], hi_k)
        if hi_e <= lo_e:
            blocks.append(0)
            continue
        blocks.append(E["cum"]["docs"][hi_e - 1]
                      - (E["cum"]["docs"][lo_e - 1] if lo_e > 0 else 0))
    if len(blocks) < 6:
        return None
    mean = sum(blocks) / len(blocks)
    var = sum((x - mean) ** 2 for x in blocks) / len(blocks)
    sd = math.sqrt(var)
    if sd <= 0:
        return None
    return (cur - mean) / sd


def veto_breadth(C, e, t):
    tot = _sess_pfx(C, e, t, "sess_nd", days=STALE_DAYS)
    if not tot:
        return None
    dn = _sess_pfx(C, e, t, "sess_netD", days=STALE_DAYS)
    return dn / tot


def veto_cadence(C, e, t):
    tot = _sess_pfx(C, e, t, "gap_n", days=STALE_DAYS)
    if not tot:
        return None
    lt = _sess_pfx(C, e, t, "gap_late", days=STALE_DAYS)
    return lt / tot


def _residual_reaction(C, e, arr_iso):
    """5-bar close-to-close SPY-residual initial reaction at event date
    (V13 residual_reaction semantics on the generic stream event)."""
    s = C.series.get(e)
    if s is None:
        return None
    i0 = bisect_right(s["dates"], arr_iso) - 1
    if i0 < 0 or i0 + 5 >= len(s["dates"]):
        return None
    r_ent = 1.0
    for k in range(1, 6):
        p0, p1 = s["close"][i0 + k - 1], s["close"][i0 + k]
        if p0 is None or p1 is None or p0 <= 0 or p1 <= 0:
            return None
        r_ent *= p1 / p0
    r_ben = 1.0
    for k in range(1, 6):
        d0, d1 = s["dates"][i0 + k - 1], s["dates"][i0 + k]
        b0 = C.spy_close.get(d0)
        b1 = C.spy_close.get(d1)
        if b0 is None or b1 is None or b0 <= 0:
            return None
        r_ben *= b1 / b0
    r = (r_ent - 1.0) - (r_ben - 1.0)
    if r > 0:
        return 1.0
    if r < 0:
        return -1.0
    return None


def veto_filing_reaction(C, e, t):
    from .exposures import has_E
    if not has_E(C, e):
        return None
    E = C.E[e]
    cut = (date.fromisoformat(t) - timedelta(days=STALE_DAYS)).isoformat()
    hi = bisect_right(E["sess_d"], t) - 1
    if hi < 0 or E["sess_d"][hi] < cut:
        return None
    a = E["sess_d"][hi]
    cache = getattr(C, "_reaction_cache", None)
    if cache is None:
        cache = C._reaction_cache = {}
    if (e, a) not in cache:
        cache[(e, a)] = _residual_reaction(C, e, a)
    return cache[(e, a)]


def veto_chain_structure(C, e, t):
    from .exposures import has_E
    if not has_E(C, e):
        return None
    E = C.E[e]
    cut = (date.fromisoformat(t) - timedelta(days=STALE_DAYS)).isoformat()
    hi = bisect_right(E["sess_d"], t) - 1
    if hi < 0:
        return None
    lo = bisect_left(E["sess_d"], cut)
    n = hi - lo + 1
    if n < MIN_GROUPS_Q:
        return None
    multi = E["cum"]["sess_multi"][hi] - (
        E["cum"]["sess_multi"][lo - 1] if lo > 0 else 0)
    return multi / n


def build_death_event_weights(C):
    """Veto 15 state construction (see module docstring).  Returns
    {cik: (sorted_event_dates, prefix_net_weights)} over ALL cohort
    entities receiving any peer-death leg weight."""
    events = []
    excl = {"no_bar_within_800d": 0, "unmapped_sector": 0}
    for trig in C.death_triggers:
        e, T, last_bar = trig["cik"], trig["T"], trig["last_bar"]
        if last_bar is None:
            excl["no_bar_within_800d"] += 1
            continue
        gap = (date.fromisoformat(T) - date.fromisoformat(last_bar)).days
        if gap > STALE_DAYS or gap < 0:
            excl["no_bar_within_800d"] += 1
            continue
        sec = C.bookable[e]["sector"]
        if not sec:
            excl["unmapped_sector"] += 1
            continue
        cls = 1 if gap <= 10 else -1
        events.append((T, sec, cls, e))

    from .core import bars_through
    groups = {}
    for T, sec, cls, name in events:
        groups.setdefault((sec, cls, T), []).append(name)
    weights = {}
    n_ev = 0
    for (sec, cls, T), names in sorted(
            groups.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
        basket = [p for p in sorted(C.bookable)
                  if C.bookable[p]["cls"] == "ALIVE_EVIDENCED"
                  and C.bookable[p]["sector"] == sec
                  and p not in set(names)
                  and bars_through(C, p, T) >= 63]
        n_ev += 1
        if not basket:
            continue
        wgt = float(cls) / len(basket)
        for p in basket:
            weights[(p, T)] = weights.get((p, T), 0.0) + wgt
    per_ent = {}
    for (p, T), w in weights.items():
        per_ent.setdefault(p, []).append((T, w))
    out = {}
    for p in per_ent:
        lst = sorted(per_ent[p])
        ds = [x[0] for x in lst]
        pref = [0.0]
        for _T, w in lst:
            pref.append(pref[-1] + w)
        out[p] = (ds, pref)
    C.death_form = {"weights_index": out, "triggers": len(events),
                    "events_defined": n_ev, "excluded": excl}
    return C.death_form


def veto_death_event_form(C, e, t):
    idx = getattr(C, "death_form", None)
    if idx is None:
        idx = build_death_event_weights(C)
    rec = idx["weights_index"].get(e)
    if rec is None:
        return None
    ds, pref = rec
    cut = (date.fromisoformat(t) - timedelta(days=STALE_DAYS)).isoformat()
    hi = bisect_right(ds, t)          # events with date <= t
    lo = bisect_left(ds, cut)         # events with date >= t-800d
    if hi <= lo:
        return None
    return pref[hi] - pref[lo]


VETO_BUILDERS = {
    "momentum_63s": veto_momentum,
    "semivariance_share": veto_semivariance,
    "vol_level": veto_vol,
    "wc_stock_intensity": veto_wc_stock_intensity,
    "goodwill_bloat": veto_goodwill_bloat,
    "f1_accrual_flow": veto_f1_accrual_flow,
    "depletion_interaction": veto_depletion_interaction,
    "cash_level": veto_cash_level,
    "sector_exposure_form": veto_sector_form,
    "own_z_characteristic_form": veto_own_z,
    "revision_direction_breadth_form": veto_breadth,
    "v11_cadence_latency_form": veto_cadence,
    "filing_event_reaction_shadow": veto_filing_reaction,
    "v12_chain_structure_form": veto_chain_structure,
    "v12_death_event_form": veto_death_event_form,
}
