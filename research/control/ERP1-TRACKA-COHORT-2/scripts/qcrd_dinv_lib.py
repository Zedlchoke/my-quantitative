"""ERP1-TRACKA-COHORT-2 — the two FROZEN candidate laws + declared twins.

IMPLEMENTATION-AUTHORITY LAW: every constant below is transcribed from the
frozen proposal texts — no re-derivation from memory, no re-tuning. Sources:

  [P3A] PROPOSER3_cohort2_REPORT.md, PROPOSAL A "TRACKA2-P3A-QCRD-H1"
        (research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/),
        field 5 verbatim:
          "Flow mass S_t = sum_m dlog m_m / sum_m |dlog m_m| in [-1,1] over
           the bar's 60 M1 returns (signed efficiency ratio of the bar).
           Spread state P_t = empirical percentile of median_M1(s) of bar t
           within the trailing same-hour pool: all H1 bars of the same
           clock-hour over the previous 60 calendar days (strictly past
           values only).
           Decision at tau_t (bar fully CLOSED): LONG next bar iff
           S_t >= +0.25 AND P_t <= 0.40; SHORT iff S_t <= -0.25 AND
           P_t <= 0.40; else flat."
        field 6 verbatim: "Hold exactly 1 H1 bar. Decision on every closed
        H1 bar with close time tau_t in [01:00, 19:00] UTC so the entry bar
        completes by the 20:00 UTC flat."
        field 2: premium band 0.8-2.5 bps (NOT implemented here — cost lane).
        field 10 / [SKEPTIC 3.1.3]: vol-content control = "P_t replaced by
        trailing realized-vol percentile of the same bar".
        F3 verbatim: "the wide-spread mirror (same law, P_t >= p60)".
  [P3B] PROPOSER3_cohort2_REPORT.md, PROPOSAL B "TRACKA2-P3B-DINV-1D",
        field 5 verbatim:
          "Traded-day bar = aggregation of the session's H1 bars
           00:00->20:00 UTC. r_d = day mid return (00:00->20:00).
           Flow mass S_d = sum_h dlog m_h / sum_h |dlog m_h| over the day's
           H1 bars. Spread state P_d = percentile of the day's median H1
           spread within the trailing 60 same-weekday days (strictly past;
           weekday enters only as PIT normalization pool, never as
           positioning).
           Decision at the 20:00 UTC close of day d (day CLOSED): LONG next
           traded day open iff S_d >= +0.20 AND P_d <= 0.40; SHORT iff
           S_d <= -0.20 AND P_d <= 0.40; else flat. Exit at next traded day
           20:00 close."
        F3: "the ungated same-law (drop P_d, keep S_d)"; F4: "wide-spread
        mirror (P_d >= p60)"; F5: "weekday-shuffle shadow (S_d reassigned to
        random weekdays preserving marginals)".
  [SK]  SKEPTIC_F0_cohort2_REPORT.md section 3.1/3.2/4 — the F-1 target-array
        representation (int8 over ALL dev H1 bars; P3-A "sign(S_t) held next
        bar, else 0"; P3-B "+/-1 held on the next traded day's 00:00->20:00
        session bars, flat otherwise"); "warmup 61 traded days flat"; and the
        declared twins reproduced above.

AMBIGUITY RESOLUTIONS (each quoted + resolved in falsifier/
FALSIFIER2_PREP_REPORT.md; encoded here, never re-chosen):
  R1  "the bar's 60 M1 returns": a valid H1 bar carries 60 M1 closes, which
      yield 59 intrabar minute-to-minute returns. Resolved to the 59
      intrabar returns over the bar's own 60 minute closes.
  R2  per-minute mid/spread taken at each minute CLOSE (m_m=(bid_c+ask_c)/2,
      s_m=(ask_c-bid_c)/m_m) — the minute's settled state, consistent with
      the plane's close conventions.
  R3  empirical percentile = searchsorted-left / len(pool) — the program's
      standing convention (tracka_lib.pct_full_panel).
  R4  [P3B] "trailing 60 same-weekday days" = the trailing 60 OCCURRENCES of
      that weekday (strictly past decided days), read literally; the P3-A
      text says "previous 60 calendar days" explicitly, the P3-B text does
      not — recorded as an ambiguity, resolved to the literal reading.
  R5  vol-content control pool geometry = the anchor's own same-hour
      60-calendar-day trailing pool (only the gated quantity changes, so
      the hour-marginal is held fixed).
  R6  M-T truncation points for P3-A are sampled on the family in-session
      mask 7..18 UTC and for P3-B on the traded-day decision mask
      (hour-19 bars) — per the dispatch.

HARD LAWS honored: NO PnL anywhere in this module (arrays only); no sealed
window input (consumers pass dev-loaded frames only); arrays are int8
{-1,0,+1} in the schedule_only/eng engine convention: array[i] = position
established at the close of bar i, filled at bar i+1's open.
"""
from __future__ import annotations

import bisect
import datetime as dt

import numpy as np
import pandas as pd

# ---- frozen constants (transcribed; sources in the module docstring) ----
MASS_P3A = 0.25            # [P3A field 5] "S_t >= +0.25" / "S_t <= -0.25"
GATE_P3A = 0.40            # [P3A field 5] "P_t <= 0.40"
GATE_MIRROR = 0.60         # [P3A F3 / P3B F4] "P >= p60" wide mirror
POOL_CAL_DAYS_P3A = 60     # [P3A field 5] "previous 60 calendar days"
MASS_P3B = 0.20            # [P3B field 5] "S_d >= +0.20" / "S_d <= -0.20"
GATE_P3B = 0.40            # [P3B field 5] "P_d <= 0.40"
POOL_OCC_P3B = 60          # [P3B field 5] "trailing 60 same-weekday days" (R4)
WARMUP_TRADED_DAYS = 61    # [SK 3.1.1 / 3.2.1 / 4] "warmup 61 traded days flat"
SEC_DAY = 86400

P3A_MODES = ("anchor", "mirror_wide", "volgate", "ungated", "index_shift_pool")
P3B_MODES = ("anchor", "mirror_wide", "ungated", "weekday_shuffle")


# ------------------------------------------------------------------ utils --

def epoch_secs(df) -> np.ndarray:
    """UTC epoch seconds from a frame column 'ts' (tz-aware or naive
    datetime; an integer column is taken to already BE epoch seconds)."""
    s = df["ts"]
    if pd.api.types.is_datetime64_any_dtype(s):
        if s.dt.tz is None:
            s = s.dt.tz_localize("UTC")
        return (s.dt.tz_convert("UTC").dt.tz_localize(None)
                .to_numpy().astype("datetime64[s]").astype("int64"))
    return s.to_numpy(dtype="int64")


def session_day_ordinals(ts: np.ndarray):
    """Per-row (day_epoch, ordinal) over SESSION days = days having >= 1 bar
    with hour <= 19 (the SignalPlane.traded_days convention)."""
    day = ts // SEC_DAY
    hour = (ts // 3600) % 24
    session = hour <= 19
    uniq = np.unique(day[session])
    ord_of = {int(d): i for i, d in enumerate(uniq)}
    ord_arr = np.full(len(ts), -1, dtype=np.int64)
    for i in range(len(ts)):
        if session[i]:
            ord_arr[i] = ord_of[int(day[i])]
    return day, ord_arr, ord_of


class _PooledPct:
    """Same-clock-hour trailing percentile engine (per-hour buckets,
    incremental insert/evict, values deduplicated by insertion identity)."""

    def __init__(self, ts, hour, win_lo_days, win_hi_excl_days=0.0):
        self.ts = ts
        self.hour = hour
        self.lo = int(round(win_lo_days * SEC_DAY))
        self.hi = int(round(win_hi_excl_days * SEC_DAY))

    def run(self, values: np.ndarray) -> np.ndarray:
        n = len(self.ts)
        out = np.full(n, np.nan)
        for h in np.unique(self.hour):
            idx = np.flatnonzero(self.hour == h)
            tsh = self.ts[idx]
            hist_vals: list = []      # sorted pool values
            hist_items: list = []     # (ts, value) ts-ascending, parallel set
            ptr = 0
            for k in range(len(idx)):
                i = idx[k]
                t = int(self.ts[i])
                hi_cut = t - self.hi
                while ptr < k and tsh[ptr] < hi_cut:
                    v = float(values[idx[ptr]])
                    if not np.isnan(v):
                        bisect.insort(hist_vals, v)
                        hist_items.append((int(tsh[ptr]), v))
                    ptr += 1
                lo_cut = t - self.lo
                while hist_items and hist_items[0][0] < lo_cut:
                    _, v0 = hist_items.pop(0)
                    j = bisect.bisect_left(hist_vals, v0)
                    if j < len(hist_vals) and hist_vals[j] == v0:
                        hist_vals.pop(j)
                v = float(values[i])
                if np.isnan(v):
                    continue
                if hist_vals:
                    out[i] = bisect.bisect_left(hist_vals, v) / len(hist_vals)
        return out


def pooled_pct(ts, hour, values, win_lo_days, win_hi_excl_days=0.0):
    """Public wrapper (R3 percentile; strictly-past same-hour pool)."""
    return _PooledPct(ts, hour, win_lo_days, win_hi_excl_days).run(values)


# ------------------------------------------------- P3-A QCRD-H1 (H1 law) --

def qcrd_h1_target(df, mass: float = MASS_P3A, gate: float = GATE_P3A,
                   mode: str = "anchor",
                   warmup_days: int = WARMUP_TRADED_DAYS) -> np.ndarray:
    """P3-A TRACKA2-P3A-QCRD-H1 target array over the H1 plane.

    df requires columns: ts, m1_sum_dl, m1_sum_abs_dl, m1_med_spread,
    m1_nmin (per-bar M1 aggregates built by build_t2_planes.py; the
    aggregates of bar t cover ONLY bar t's own 60 minutes — intrabar, no
    future rows are read).

    Array convention: tgt[i] = sign(S_i) when the frozen law fires at the
    just-closed bar i (filled at bar i+1 open), else 0  [SK section 4].
    """
    for col in ("m1_sum_dl", "m1_sum_abs_dl", "m1_med_spread", "m1_nmin"):
        if col not in df.columns:
            raise KeyError(f"qcrd_h1_target: missing M1 aggregate column {col}")
    ts = epoch_secs(df)
    hour = (ts // 3600) % 24
    day, dord, _ = session_day_ordinals(ts)

    sum_dl = df["m1_sum_dl"].to_numpy(dtype=float)
    sum_adl = df["m1_sum_abs_dl"].to_numpy(dtype=float)
    nmin = df["m1_nmin"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        s_mass = np.where(sum_adl > 0, sum_dl / sum_adl, np.nan)
    complete = nmin == 60                      # R1: full-minute bars only
    s_mass = np.where(complete, s_mass, np.nan)

    if mode == "anchor":
        pct = pooled_pct(ts, hour, df["m1_med_spread"].to_numpy(dtype=float),
                         POOL_CAL_DAYS_P3A)
        gate_ok = pct <= gate                       # [P3A] "P_t <= 0.40"
    elif mode == "mirror_wide":
        pct = pooled_pct(ts, hour, df["m1_med_spread"].to_numpy(dtype=float),
                         POOL_CAL_DAYS_P3A)
        gate_ok = pct >= GATE_MIRROR                # [P3A F3] "P_t >= p60"
    elif mode == "volgate":
        # [P3A field 10 / SK 3.1.3]: P_t -> trailing realized-vol percentile;
        # pool geometry unchanged (R5). rv = sum |dlog m| of the same bar.
        pct = pooled_pct(ts, hour, sum_adl, POOL_CAL_DAYS_P3A)
        gate_ok = pct <= gate
    elif mode == "ungated":
        gate_ok = np.ones(len(ts), dtype=bool)      # [P3A F3-analog] drop P_t
    elif mode == "index_shift_pool":
        # declared twin: index-shift of the percentile pool window by one
        # calendar day ([ts-61d, ts-1d) instead of [ts-60d, ts)).
        pct = pooled_pct(ts, hour, df["m1_med_spread"].to_numpy(dtype=float),
                         POOL_CAL_DAYS_P3A + 1, win_hi_excl_days=1.0)
        gate_ok = pct <= gate
    else:
        raise ValueError(f"unknown P3-A mode {mode}")

    decision_clock = (hour >= 0) & (hour <= 18)     # [P3A field 6] tau_t in
    # [01:00,19:00] UTC  <=>  bar-open hour in [0,18]
    warm = dord >= warmup_days                      # [SK] 61 traded days flat
    fire = decision_clock & warm & complete & np.isfinite(s_mass)
    fire = fire & np.asarray(gate_ok, dtype=bool)

    tgt = np.zeros(len(ts), dtype=np.int8)
    tgt[fire & (s_mass >= mass)] = 1                # [P3A] "LONG next bar iff
    tgt[fire & (s_mass <= -mass)] = -1              #  S_t >= +0.25 ..." / SHORT
    return tgt


# --------------------------------------------- P3-B DINV-1D (traded day) --

def dinv_day_table(df):
    """Per-session-day observables for P3-B, strictly from closed bars.

    Returns (rows, bar_day, bar_ord, ord_of) where rows[j] is a dict:
      day, ord, weekday, dec capable (hour-0 AND hour-19 session bars
      present), i0 (hour-0 bar), i_close (hour-19 bar), idx (session-bar
      indices, hours 0..19), med_s_close, s_d (flow mass over the day's H1
      mid closes; R1/R2 conventions: 20 H1 closes -> 19 intraday returns).
    """
    ts = epoch_secs(df)
    hour = (ts // 3600) % 24
    bar_day, bar_ord, ord_of = session_day_ordinals(ts)
    mid_close = ((df["b_c"].to_numpy(dtype=float)
                  + df["a_c"].to_numpy(dtype=float)) / 2.0)
    s_close = df["s_close"].to_numpy(dtype=float)

    session = hour <= 19
    day_bars: dict = {}
    for i in np.flatnonzero(session):
        day_bars.setdefault(int(bar_day[i]), []).append(int(i))

    rows = []
    for d in sorted(day_bars):
        idx = day_bars[d]
        hours = hour[idx]
        has0 = bool((hours == 0).any())
        has19 = bool((hours == 19).any())
        mids = mid_close[idx]
        with np.errstate(invalid="ignore", divide="ignore"):
            lg = np.log(mids)
        dlog = np.diff(lg)
        s_d = float(dlog.sum() / np.abs(dlog).sum()) if len(dlog) \
            and np.abs(dlog).sum() > 0 else np.nan
        rows.append({
            "day": d,
            "ord": ord_of[d],
            "weekday": dt.datetime.fromtimestamp(
                int(d) * SEC_DAY, tz=dt.timezone.utc).weekday(),
            "dec_capable": has0 and has19 and len(idx) >= 2,
            "i0": idx[int(np.argmax(hours == 0))] if has0 else -1,
            "i_close": idx[int(np.argmax(hours == 19))] if has19 else -1,
            "idx": idx,
            "med_s_close": float(np.median(s_close[idx])),
            "s_d": s_d,
        })
    return rows, bar_day, bar_ord, ord_of


def dinv_1d_target(df, mass: float = MASS_P3B, gate: float = GATE_P3B,
                   mode: str = "anchor",
                   warmup_days: int = WARMUP_TRADED_DAYS,
                   pool_occ: int = POOL_OCC_P3B,
                   seed: int = 20260926) -> np.ndarray:
    """P3-B TRACKA2-P3B-DINV-1D target array over the H1 plane.

    df requires columns: ts, b_c, a_c, s_close. Decisions at traded-day
    closes (20:00 UTC); the position vector must produce the fill at the
    NEXT session day's OPEN (00:00 bar or first session bar present) and
    hold through its 00:00->20:00 session  [P3B field 6 "LONG next traded
    day open"; SK section 4 "+/-1 held on the next traded day's
    00:00->20:00 session bars, flat otherwise"].

    Array encoding (engine fills bar i from array[i-1], never fills on
    non-session bars, force-flattens at the day-close bar): the sign is
    written on (i) the decision day's day-close bar and every later
    non-session bar of that day (hours 20..23), (ii) every bar of any
    intervening non-session day (weekend pre-open bars), and (iii) the
    position day's 00:00..18 session bars. None of the carry bars are
    fill-eligible, so no position is ever opened before the position day's
    open, and the day-close law exits at its 20:00 close. Decision-day
    evening bars carry the NEW decision; the position day's session bars
    the old one — the engine's day-close flatten keeps day books separate.
    """
    if mode not in P3B_MODES:
        raise ValueError(f"unknown P3-B mode {mode}")
    ts = epoch_secs(df)
    hour = (ts // 3600) % 24
    bar_day = ts // SEC_DAY
    rows, bar_day_unused, bar_ord, ord_of = dinv_day_table(df)

    dec = [r for r in rows if r["dec_capable"]]
    s_vals = np.array([r["s_d"] for r in dec], dtype=float)
    if mode == "weekday_shuffle":
        # [P3B F5 / SK 3.2.2] deterministic seeded reassignment preserving
        # the S_d marginal exactly (a permutation of the same values).
        rng = np.random.default_rng(seed)
        s_vals = s_vals[rng.permutation(len(s_vals))]
    for r, sv in zip(dec, s_vals):
        r["s_use"] = float(sv)

    tgt = np.zeros(len(ts), dtype=np.int8)
    session_days = [r["day"] for r in rows]           # chronological
    next_session = {session_days[j]: (session_days[j + 1]
                                      if j + 1 < len(session_days) else None)
                    for j in range(len(session_days))}
    # all bars (any hour) grouped by calendar day — for the carry encoding
    bars_of_day: dict = {}
    for i in range(len(ts)):
        bars_of_day.setdefault(int(bar_day[i]), []).append(i)

    for j, r in enumerate(dec):
        if r["ord"] < warmup_days:                     # [SK] warmup flat
            continue
        # pool: trailing <=pool_occ same-weekday DECIDED days, strictly past
        pool = [q["med_s_close"] for q in dec[:j]
                if q["weekday"] == r["weekday"]][-pool_occ:]
        if not pool:
            continue                                   # fail-closed flat
        pool_sorted = np.sort(np.asarray(pool, dtype=float))
        p_d = float(np.searchsorted(pool_sorted, r["med_s_close"],
                                    side="left") / len(pool_sorted))  # R3
        if mode in ("anchor", "weekday_shuffle"):
            gate_ok = p_d <= gate                      # [P3B] "P_d <= 0.40"
        elif mode == "mirror_wide":
            gate_ok = p_d >= GATE_MIRROR               # [P3B F4]
        elif mode == "ungated":
            gate_ok = True                             # [P3B F3] drop P_d
        s = r["s_use"]
        if not np.isfinite(s):
            continue
        if not (abs(s) >= mass and gate_ok):
            continue
        sign = 1 if s > 0 else -1
        nxt = next_session.get(r["day"])
        # (i) decision bar + decision-day evening carry
        if r["i_close"] >= 0:
            tgt[r["i_close"]] = sign
        for i in bars_of_day.get(int(r["day"]), []):
            if hour[i] > 19:
                tgt[i] = sign
        if nxt is None:
            continue
        # (ii) intervening non-session days (weekend pre-open carry)
        mid_days = [d for d in sorted(bars_of_day)
                    if r["day"] < d < nxt]
        for d in mid_days:
            for i in bars_of_day[d]:
                tgt[i] = sign
        # (iii) position-day session bars 00:00..18
        if nxt in ord_of:
            for i in bars_of_day.get(int(nxt), []):
                if 0 <= hour[i] <= 18:
                    tgt[i] = sign
    return tgt


# ------------------------------ TRACKA1-M3 spread-gated-fade shadow ------

def f_m3_spread_gated_fade(p, spread15: np.ndarray,
                           lo_q: float = 0.3, hi_q: float = 0.7,
                           pool_traded_days: int = 20,
                           gate_q: float = 0.60) -> np.ndarray:
    """TRACKA1-M3 shadow: spread <= same-hour p60 gate on the band-fade law.

    Spec [SK section 4, item 4]: "(spread <= same-hour p60 gate on the
    band-fade law ...: absorb prev-day-band breaks only when just-closed
    break hour's median spread <= trailing 20-trading-day same-hour p60)".
    Conventions (declared in FALSIFIER2_PREP_REPORT.md): base law =
    R-ANCHOR (tracka_lib.f_rangeexp_anchor_shift labels; the certified PIT
    family form); FADE-mode days only (the M3 candidate gated the fade
    arm); a break entry at bar i is absorbed iff spread15[i] (median of the
    hour's four 15m s_open values, built on the SAME dev grid) <=
    quantile(pool, 0.60) over the same-hour values of the previous
    20 traded days, strictly past; NaN spread or empty pool => no entry
    (fail-closed). Exits follow the family law unchanged.

    p = tracka_lib.SignalPlane on the dev-masked ANC H1 plane;
    spread15 = float array aligned to p.ts. Returns int8 array.
    """
    import tracka_lib as T

    days, labels, pdh, pdl = T.anchor_day_labels(p, lo_q, hi_q)
    traded = list(p.traded_days())
    rank = {int(d): i for i, d in enumerate(traded)}
    # pool source: same-hour values grouped by hour, each (day, value)
    by_hour: dict = {}
    for i in range(len(p.ts)):
        if not np.isnan(spread15[i]):
            by_hour.setdefault(int(p.hour[i]), []).append(
                (int(p.day[i]), float(spread15[i])))

    def gate_ok(i: int) -> bool:
        v = spread15[i]
        if np.isnan(v):
            return False
        r = rank.get(int(p.day[i]))
        if r is None or r < 1:
            return False
        pool = [val for (d, val) in by_hour.get(int(p.hour[i]), [])
                if d in rank and 0 <= r - rank[d] - 1 < pool_traded_days]
        if not pool:
            return False
        return bool(v <= float(np.quantile(np.asarray(pool), gate_q)))

    tgt = np.zeros(len(p.ts), dtype=np.int8)
    pos = 0
    cur_day = -1
    for i in range(len(p.ts)):
        if p.skip[i]:
            continue
        d = p.day[i]
        if d != cur_day:
            cur_day, pos = d, 0
        if labels.get(d) != "fade":                 # gate ON the fade arm only
            tgt[i] = 0
            continue
        if p.hour[i] < 7 or p.hour[i] > 18:
            tgt[i] = 0
            continue
        pd_h = pdh.get(d)
        pd_l = pdl.get(d)
        if pd_h is None or pd_l is None:
            tgt[i] = 0
            continue
        if pos == 0:
            if p.b_c[i] > pd_h:
                if gate_ok(i):
                    pos = -1                        # absorb: fade the break
            elif p.b_c[i] < pd_l:
                if gate_ok(i):
                    pos = 1
        else:
            mid = (pd_h + pd_l) / 2
            if abs(p.b_c[i] - mid) < (pd_h - pd_l) / 4:
                pos = 0
        tgt[i] = pos
    return tgt
