#!/usr/bin/env python3
"""FOREX-FREE-V6 D2 A7 novelty audit: measured ancestry rho per proposal.

DECISION-SCHEDULE COMPUTATION ONLY.  No PnL, no costs, no scored output, no
fills beyond schedule instants (schedule fidelity per the D2 mandate).
Approach reused from the V5 precedent
(research/control/forex_free_v5_run/d2_a7_novelty_evidence/compute_schedule_rhos.py):
reconstruct signed exposure schedules, compare with Spearman rho variants,
Jaccard overlap and sign agreement.  Bar: max |rho| > 0.20 => ANCESTRY_VETO.

GATE STATISTIC (frozen for this audit, V5-precedent-aligned): the per-
proposal gate is max |Spearman rho| over the POOLED signed exposure-series
variants -- cellwise_signed_full_grid, cellwise_union_active,
netsigned_union_dates_shared_pairs -- per RULES 2.4 "pooled |rho|" and the
V5 verdict conventions (fire/0-1 indicators are NOT signed exposure series;
a NEGATIVE fire rho is anti-coincidence evidence, recorded as a novelty
signal, never gates; conditional co-firing and ancestor-support-restricted
signed rhos are computed and REPORTED as diagnostics/sensitivities with
their own over-bar flags, never silently dropped).

Exposure-cell convention (frozen for this audit, applied identically to BOTH
sides of every comparison): a decision date d carries cell (d, pair, side) if
the book holds the position AT d's 16:00 America/New_York close instant.
A position opened at close(f) and closed at close(x) occupies f..x-1.
A position opened at the open of the 16:00-NY bar of NY-date f (the V5 anchor
fill instant, identical to f's decision-close instant) occupies f..x-1 too.

Decision-close series: 16:00 America/New_York completed weekday bars derived
from the staged H1 snapshots (the only staged series at the frozen decision
clock; the provider 1day bars carry a different close cut - measured median
0.2% off - and are NOT the decision-close series).  Observable span therefore
starts at the H1 staging start (2020-01-30); dates before it produce no
exposure cells for ANY schedule (proposals and ancestors alike), so every
comparison below is measured on the shared observable span.  Recorded as a
coverage note + finding.
"""
import glob
import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v7/integration"
UTC = timezone.utc
NY = ZoneInfo("America/New_York")

PAIRS = ["GBPUSD", "USDCAD", "AUDUSD", "NZDUSD", "EURUSD", "USDJPY", "USDCHF"]
ECON_PAIR = {"GB": "GBPUSD", "CA": "USDCAD", "AU": "AUDUSD", "NZ": "NZDUSD"}
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)
S0_CAP = datetime(2025, 7, 25, 0, 0, tzinfo=UTC)   # V5 family entry/exit cap
MAX_FILL_LAG_DAYS = 4                              # inherited kernel constant

OUT = os.path.join(ROOT, "research/control/forex_free_v7_run/a7_prelaunch_evidence_r2/novelty_rerun_evidence")


def ny1600(d):
    return datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).astimezone(UTC)


def parse_stamp(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


# ------------------------------------------------------------------ data ---
def load_daily_closes(pair):
    inst = defaultdict(dict)
    files = sorted(glob.glob(f"{ROOT}/data_raw/forex_free_v1/{pair}_1h_*_a.json"))
    if not files:
        raise RuntimeError(f"no H1 snapshot files for {pair}")
    for f in files:
        d = json.load(open(f))
        if d.get("status") != "ok":
            continue
        for v in d["values"]:
            ts = datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            loc = ts.astimezone(NY)
            if loc.hour == 16 and loc.minute == 0 and loc.weekday() < 5:
                if loc.date() in inst and inst[loc.date()][ts] != float(v["close"]):
                    raise RuntimeError(f"conflicting 16:00-NY close {pair} {loc.date()}")
                inst[loc.date()][ts] = float(v["close"])
    out = {}
    for d, m in inst.items():
        want = ny1600(d)
        if want in m:
            out[d] = m[want]
    return out


SERIES = {}      # pair -> list of dates
CLOSES = {}      # pair -> {date: close}
RET = {}         # pair -> {date: logret}
for _p in PAIRS:
    CLOSES[_p] = load_daily_closes(_p)
    SERIES[_p] = sorted(CLOSES[_p])
    _r = {}
    for _i in range(1, len(SERIES[_p])):
        _a, _b = SERIES[_p][_i - 1], SERIES[_p][_i]
        _r[_b] = math.log(CLOSES[_p][_b] / CLOSES[_p][_a])
    RET[_p] = _r
COMMON7 = sorted(set.intersection(*[set(SERIES[p]) for p in PAIRS]))
COMMON_RET = sorted(set.intersection(*[set(RET[p]) for p in PAIRS]))


def sidx(pair, d):
    return SERIES[pair].index(d)


# ----------------------------------------------------------------- clocks --
def load_clocks(path):
    rows = json.load(open(path))["clocks"]
    out = []
    for r in rows:
        out.append({"economy": r["economy"],
                    "decision_date": date.fromisoformat(r["decision_date"]),
                    "available": parse_stamp(r["available_time_utc"]),
                    "afdd": (date.fromisoformat(r["available_for_daily_decision_date"])
                             if "available_for_daily_decision_date" in r else None),
                    "sha": r["archive_sha256"]})
    return out


CLK_V6 = load_clocks(f"{ROOT}/research/control/forex_free_v6_run/p3_conditioning_clocks_v6.json")
CLK_V5 = load_clocks(f"{ROOT}/research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json")


def cond_date_v6(c):
    """V6 conditionable decision date: CA rows at their published
    available_for_daily_decision_date; GB/AU/NZ DAY rows at decision_date."""
    return c["afdd"] if c["economy"] == "CA" else c["decision_date"]


# ------------------------------------------------------------- schedule type
class Sched:
    def __init__(self, name):
        self.name = name
        self.cells = {}        # (date, pair) -> side
        self.trades = []       # schedule-fidelity records
        self.counts = defaultdict(int)

    def add(self, d, pair, side):
        self.cells[(d, pair)] = side


def overlap_walk_ok(entry_close, exit_close, cur_exit_close):
    """max one position per pair: a new trade is taken iff its entry instant
    does not precede the still-open position's exit instant."""
    return cur_exit_close is None or entry_close >= cur_exit_close


def s0_exit_ok(exit_close):
    """S0-span parity with the V5 family cap: a schedule trade whose exit
    decision close lies after the S0 end (16:00-NY of 2025-07-24) is
    excluded and counted -- V5 anchors exits at the span cap; the V6
    proposals are held to the same evidenced-window boundary."""
    return exit_close <= ny1600(S0_END)


# ------------------------------------------------- V6 proposal anchor arms --
def sched_a4p1(sham=False, k=5):
    """FXFV6-A4-P1 anchor: own-economy clocks, direction = sign of the pair's
    reaction R = ln(close(D0)/close(D_prev)); fill close(D1); hold k sessions.
    Sham variant: conditionable date shifted +7 calendar days."""
    s = Sched("FXFV6-A4-P1_sham+7d" if sham else "FXFV6-A4-P1_anchor")
    cur_exit = {}
    for c in sorted(CLK_V6, key=lambda x: (cond_date_v6(x), x["economy"])):
        pair = ECON_PAIR[c["economy"]]
        d0 = cond_date_v6(c)
        if sham:
            d0 = d0 + timedelta(days=7)
        s.counts["clocks"] += 1
        ser = SERIES[pair]
        if d0 not in CLOSES[pair]:
            s.counts["d0_not_in_series"] += 1
            continue
        i0 = ser.index(d0)
        if i0 < 1:
            s.counts["no_prev_session"] += 1
            continue
        i_prev = i0 - 1
        if i_prev < 5:  # warmup: 5 decision closes ending at close(D_prev)
            s.counts["warmup_short"] += 1
            continue
        R = math.log(CLOSES[pair][ser[i0]] / CLOSES[pair][ser[i_prev]])
        side = 0 if R == 0.0 else (1 if R > 0 else -1)
        if side == 0:
            s.counts["zero_signal"] += 1
            continue
        if i0 + 1 >= len(ser):
            s.counts["no_next_session"] += 1
            continue
        i1 = i0 + 1
        if i1 + k >= len(ser):
            s.counts["exit_beyond_series"] += 1
            continue
        entry_close = ny1600(ser[i1])
        exit_close = ny1600(ser[i1 + k])
        if not s0_exit_ok(exit_close):
            s.counts["s0_exit_excluded"] += 1
            continue
        if not overlap_walk_ok(entry_close, exit_close, cur_exit.get(pair)):
            s.counts["collision_skipped"] += 1
            continue
        cur_exit[pair] = exit_close
        for j in range(i1, i1 + k):
            s.add(ser[j], pair, side)
        s.trades.append({"economy": c["economy"], "clock_decision_date": str(c["decision_date"]),
                         "D0": str(d0), "D1": str(ser[i1]), "exit": str(ser[i1 + k]),
                         "side": side, "R": R})
        s.counts["trades"] += 1
    return s


def sched_a4p2(sham=False, k=5):
    """FXFV6-A4-P2 anchor: the 88 GB clocks on EURUSD/USDJPY/USDCHF; per-pair
    own reaction direction; fill close(D1); hold k sessions."""
    s = Sched("FXFV6-A4-P2_sham+7d" if sham else "FXFV6-A4-P2_anchor")
    cur_exit = {}
    gb = sorted([c for c in CLK_V6 if c["economy"] == "GB"], key=lambda x: x["decision_date"])
    for c in gb:
        d0 = c["decision_date"]
        if sham:
            d0 = d0 + timedelta(days=7)
        for pair in ["EURUSD", "USDJPY", "USDCHF"]:
            s.counts["pair_events"] += 1
            ser = SERIES[pair]
            if d0 not in CLOSES[pair]:
                s.counts["d0_not_in_series"] += 1
                continue
            i0 = ser.index(d0)
            if i0 < 1:
                s.counts["no_prev_session"] += 1
                continue
            i_prev = i0 - 1
            if i_prev < 5:
                s.counts["warmup_short"] += 1
                continue
            R = math.log(CLOSES[pair][ser[i0]] / CLOSES[pair][ser[i_prev]])
            side = 0 if R == 0.0 else (1 if R > 0 else -1)
            if side == 0:
                s.counts["zero_signal"] += 1
                continue
            if i0 + 1 >= len(ser):
                s.counts["no_next_session"] += 1
                continue
            i1 = i0 + 1
            if i1 + k >= len(ser):
                s.counts["exit_beyond_series"] += 1
                continue
            entry_close = ny1600(ser[i1])
            exit_close = ny1600(ser[i1 + k])
            if not s0_exit_ok(exit_close):
                s.counts["s0_exit_excluded"] += 1
                continue
            key = pair
            if not overlap_walk_ok(entry_close, exit_close, cur_exit.get(key)):
                s.counts["collision_skipped"] += 1
                continue
            cur_exit[key] = exit_close
            for j in range(i1, i1 + k):
                s.add(ser[j], pair, side)
            s.trades.append({"economy": "GB", "D0": str(d0), "pair": pair,
                             "D1": str(ser[i1]), "exit": str(ser[i1 + k]), "side": side})
            s.counts["trades"] += 1
    return s


def _a6_state(pair, iA):
    """A6-P1 state at pair decision index iA: (rv5, rv20, trend10) or None."""
    if iA < 25:
        return None
    ser = SERIES[pair]
    r5 = [RET[pair][ser[j]] for j in range(iA - 4, iA + 1)]
    r20 = [RET[pair][ser[j]] for j in range(iA - 24, iA - 4)]
    t10 = math.fsum(RET[pair][ser[j]] for j in range(iA - 9, iA + 1))
    return float(np.std(r5, ddof=1)), float(np.std(r20, ddof=1)), t10


def sched_a6p1(state="compression", sham=False):
    """FXFV6-A6-P1 anchor: post-print vol state gates pre-print trend
    continuation on the print-currency pairs; A = conditionable date;
    entry fill close(next decision day); 5-session hold."""
    s = Sched(f"FXFV6-A6-P1_{state}" + ("_sham+7d" if sham else "_anchor"))
    cur_exit = {}
    for c in sorted(CLK_V6, key=lambda x: (cond_date_v6(x), x["economy"])):
        pair = ECON_PAIR[c["economy"]]
        A = cond_date_v6(c)
        if sham:
            a7 = A + timedelta(days=7)
            cand = [d for d in SERIES[pair] if d >= a7]
            if not cand:
                s.counts["sham_beyond_series"] += 1
                continue
            A = cand[0]
        s.counts["clocks"] += 1
        ser = SERIES[pair]
        if A not in CLOSES[pair]:
            s.counts["A_not_in_series"] += 1
            continue
        st = _a6_state(pair, ser.index(A))
        if st is None:
            s.counts["warmup_short"] += 1
            continue
        rv5, rv20, t10 = st
        if rv20 == 0:
            s.counts["rv20_zero"] += 1
            continue
        ratio = rv5 / rv20
        if state == "compression":
            on = ratio <= 0.9
        else:
            on = ratio >= 1.1
        if not on:
            s.counts["dead_zone_or_state_off"] += 1
            continue
        side = 0 if t10 == 0.0 else (1 if t10 > 0 else -1)
        if side == 0:
            s.counts["zero_trend"] += 1
            continue
        iA = ser.index(A)
        if iA + 1 >= len(ser):
            s.counts["no_entry_session"] += 1
            continue
        ie = iA + 1
        if ie + 5 >= len(ser):
            s.counts["exit_beyond_series"] += 1
            continue
        entry_close = ny1600(ser[ie])
        exit_close = ny1600(ser[ie + 5])
        if not s0_exit_ok(exit_close):
            s.counts["s0_exit_excluded"] += 1
            continue
        if not overlap_walk_ok(entry_close, exit_close, cur_exit.get(pair)):
            s.counts["collision_skipped"] += 1
            continue
        cur_exit[pair] = exit_close
        for j in range(ie, ie + 5):
            s.add(ser[j], pair, side)
        s.trades.append({"economy": c["economy"], "A": str(A), "ratio": round(ratio, 4),
                         "trend10": t10, "entry": str(ser[ie]), "exit": str(ser[ie + 5]),
                         "side": side})
        s.counts["trades"] += 1
    return s


def _pc1_share(i):
    """PC1 eigenvalue share of the 7x7 correlation matrix of trailing 20
    returns of the 7 pairs on COMMON_RET indices (i-19..i)."""
    if i < 19:
        return None
    M = np.array([[RET[p][COMMON_RET[j]] for j in range(i - 19, i + 1)] for p in PAIRS])
    C = np.corrcoef(M)
    w = np.linalg.eigvalsh(C)
    w = np.clip(w, 0.0, None)
    tot = w.sum()
    if tot <= 0:
        return None
    return float(w.max() / tot)


def sched_a6p2(state_shift=0):
    """FXFV6-A6-P2 anchor: dollar-factor concentration (PC1 share >= 75th pct
    of its trailing 252-day reference) gates a cross-pair 10-day fade,
    noise-floored; entry fill close(next common decision day); 5-session hold.
    state_shift>0 implements the +N decision-day shifted-state placebo."""
    s = Sched("FXFV6-A6-P2_anchor" if state_shift == 0
              else f"FXFV6-A6-P2_placebo_state+{state_shift}d")
    raw = {}
    for i in range(19, len(COMMON_RET)):
        raw[i] = _pc1_share(i)
    cur_exit = {}
    n_state = 0
    for i in range(272, len(COMMON_RET)):
        t = COMMON_RET[i]
        if not (S0_START <= t <= S0_END):
            continue
        si = raw.get(i)
        if si is None:
            s.counts["state_undefined"] += 1
            continue
        ref_idx = [j for j in range(i - 252, i) if raw.get(j) is not None]
        if len(ref_idx) < 252:
            s.counts["reference_incomplete"] += 1
            continue
        ref = np.array([raw[j] for j in ref_idx])
        thr = float(np.percentile(ref, 75))
        use = raw[i - state_shift] if (i - state_shift) in raw else None
        if use is None:
            s.counts["shifted_state_undefined"] += 1
            continue
        high = use >= thr
        if not high:
            continue
        n_state += 1
        if i + 1 >= len(COMMON_RET):
            s.counts["no_entry_session"] += 1
            continue
        ie = i + 1
        if ie + 5 >= len(COMMON_RET):
            s.counts["exit_beyond_series"] += 1
            continue
        if not s0_exit_ok(ny1600(COMMON_RET[ie + 5])):
            s.counts["s0_exit_excluded"] += 1
            continue
        legs = 0
        for pair in PAIRS:
            r10 = [RET[pair][COMMON_RET[j]] for j in range(i - 9, i + 1)]
            v20 = float(np.std([RET[pair][COMMON_RET[j]] for j in range(i - 19, i + 1)], ddof=1))
            cum10 = math.fsum(r10)
            floor = 0.25 * v20 * math.sqrt(10)
            if abs(cum10) < floor or cum10 == 0:
                s.counts["noise_floor_or_zero"] += 1
                continue
            side = -1 if cum10 > 0 else 1
            entry_close = ny1600(COMMON_RET[ie])
            exit_close = ny1600(COMMON_RET[ie + 5])
            if not overlap_walk_ok(entry_close, exit_close, cur_exit.get(pair)):
                s.counts["collision_skipped"] += 1
                continue
            cur_exit[pair] = exit_close
            for j in range(ie, ie + 5):
                s.add(COMMON_RET[j], pair, side)
            legs += 1
        s.counts["trigger_days"] += 1
        s.counts["leg_entries"] += legs
    s.counts["high_state_days"] = n_state
    return s


# ------------------------------------------------------ V5 ancestor arms ---
def sched_v5_family(clk, sham=False):
    """FXFV5-A6-P1 anchor law (family_a6p1.py verbatim schedule semantics):
    F = last decision bar strictly before the availability instant a;
    D = one session before F; X = first bar strictly after a;
    direction = -sign(sum of the 10 log returns strictly before D);
    enter at F's decision instant, exit at X's; exposure cells F..X-1.
    sham=True: a -> a+7 calendar days, window dropped if ANY evidenced clock
    instant (all economies) lies strictly inside (F, X)."""
    s = Sched("FXFV5-A6-P1_neighbour_sham" if sham else "FXFV5-A6-P1_anchor")
    all_instants = sorted(c["available"] for c in CLK_V5)
    cur_exit_ts = {}
    cur_entry_day = {}
    for c in sorted(clk, key=lambda x: (x["available"], x["economy"])):
        pair = ECON_PAIR[c["economy"]]
        a = c["available"] + (timedelta(days=7) if sham else timedelta(0))
        ser = SERIES[pair]
        s.counts["candidates"] += 1
        f_candidates = [d for d in ser if ny1600(d) < a]
        if not f_candidates:
            s.counts["f_missing"] += 1
            continue
        i_f = len(f_candidates) - 1
        if i_f < 1:
            s.counts["no_decision_bar"] += 1
            continue
        i_d = i_f - 1
        x_candidates = [d for d in ser if ny1600(d) > a]
        if not x_candidates:
            s.counts["x_missing"] += 1
            continue
        i_x = ser.index(x_candidates[0])
        if i_d < 11:
            s.counts["warmup_void"] += 1
            continue
        if ny1600(ser[i_f]) >= S0_CAP or ny1600(ser[i_x]) > S0_CAP:
            s.counts["s0_cap_excluded"] += 1
            continue
        closes_prev = [CLOSES[pair][ser[j]] for j in range(i_d - 11, i_d)]
        x_sum = math.fsum(math.log(closes_prev[j] / closes_prev[j - 1]) for j in range(1, 11))
        side = 0 if x_sum == 0 else (-1 if x_sum > 0 else 1)
        if side == 0:
            s.counts["zero_direction"] += 1
            continue
        if sham:
            f_ts, x_ts = ny1600(ser[i_f]), ny1600(ser[i_x])
            if any(f_ts < inst < x_ts for inst in all_instants):
                s.counts["sham_dropped"] += 1
                continue
        if ny1600(ser[i_f]) - ny1600(ser[i_d]) > timedelta(days=MAX_FILL_LAG_DAYS):
            s.counts["fill_lag"] += 1
            continue
        entry_ts = ny1600(ser[i_f])
        if cur_exit_ts.get(pair) is not None and entry_ts < cur_exit_ts[pair]:
            s.counts["governor_open"] += 1
            continue
        eday = ser[i_f]
        if cur_entry_day.get(pair) == eday:
            s.counts["governor_same_day"] += 1
            continue
        cur_exit_ts[pair] = ny1600(ser[i_x])
        cur_entry_day[pair] = eday
        for j in range(i_f, i_x):
            s.add(ser[j], pair, side)
        s.trades.append({"economy": c["economy"], "available": iso(c["available"]),
                         "F": str(ser[i_f]), "X": str(ser[i_x]), "side": side})
        s.counts["trades"] += 1
    return s


# ------------------------------------------------------ carry ancestors ----
def load_ledger_reader(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    dedup, order = {}, []
    for r in rows:
        key = (r.get("area"), r.get("effective_date"))
        if key not in dedup:
            order.append(key)
        dedup[key] = r
    by_area = defaultdict(list)
    for key in order:
        r = dedup[key]
        area = r.get("area")
        ann = r.get("announcement") or {}
        raw_avail = ann.get("operative_available_time_utc")
        if raw_avail is None:
            continue
        avail = parse_stamp(raw_avail)
        eff = parse_stamp(r["effective_time_utc"]) if r.get("effective_time_utc") else None
        val = r.get("new_value")
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            continue
        by_area[area].append((eff, avail, float(val)))
    for area in by_area:
        by_area[area].sort(key=lambda x: (x[0] or datetime(1, 1, 1, tzinfo=UTC), x[1]))

    def policy_rate(area, t):
        best = None
        for eff, avail, val in by_area.get(area, []):
            if avail > t:
                continue
            if eff is not None and eff > t:
                continue
            best = val
        return best

    def differential(b, q, t):
        rb, rq = policy_rate(b, t), policy_rate(q, t)
        return None if rb is None or rq is None else rb - rq

    return differential


def sched_carry(differential, gated=False):
    """Carry-region ancestor: direction = sign(as-of policy-rate differential)
    per decision day.  gated=False: unconditional always-in (widest form of
    the forbidden region, 'vol-gated or not').  gated=True: a disclosed
    daily-return-std reconstruction of the V3 vol gate (S_T < B_T, 20-day
    blocks x 10, 220-day warmup; the V3 neighbour estimator reading)."""
    s = Sched("ancestry_carry_v3gate_recon" if gated else "ancestry_carry_unconditional")
    AREAS = {"GBPUSD": ("GB", "US"), "USDCAD": ("US", "CA"), "AUDUSD": ("AU", "US"),
             "NZDUSD": ("NZ", "US"), "EURUSD": ("EMU", "US"), "USDJPY": ("US", "JP"),
             "USDCHF": ("US", "CH")}
    # per-pair rolling per-day vol estimator for the gated variant
    est = {}
    for pair in PAIRS:
        ser = SERIES[pair]
        e = {}
        for i in range(19, len(ser)):
            e[ser[i]] = float(np.std([RET[pair][ser[j]] for j in range(i - 18, i + 1)], ddof=1))
        est[pair] = e
    for pair in PAIRS:
        b, q = AREAS[pair]
        ser = SERIES[pair]
        for i, d in enumerate(ser):
            if not (S0_START <= d <= S0_END):
                continue
            t = ny1600(d)
            diff = differential(b, q, t)
            if diff is None or diff == 0:
                continue
            side = 1 if diff > 0 else -1
            if gated:
                if d not in est[pair]:
                    continue
                # S_T = mean of the per-day estimator over the 20 most recent
                # completed days ending at d; B_T = median of the 10 prior
                # non-overlapping 20-day block means; LOW iff S_T < B_T.
                w_days = ser[i - 19:i + 1]
                if any(x not in est[pair] for x in w_days):
                    continue
                S_T = float(np.mean([est[pair][x] for x in w_days]))
                blocks = []
                ok = True
                for bi in range(10):
                    blk = ser[i - 19 - 20 * (bi + 1):i - 19 - 20 * bi]
                    if len(blk) < 20 or any(x not in est[pair] for x in blk):
                        ok = False
                        break
                    blocks.append(float(np.mean([est[pair][x] for x in blk])))
                if not ok:
                    continue
                B_T = float(np.median(blocks))
                if not (S_T < B_T):
                    continue
            s.add(d, pair, side)
    return s


# ------------------------------------------- session-family reconstructions
def sched_sessions():
    """Four forbidden session families reconstructed as daily-clock-observable
    patterns (the intraday session timing itself is NOT daily-clock
    observable; these are the exposure-shape proxies, rules disclosed):
      london_open_continuation : continue the prior decision day's move
      late_ny_fade             : fade the current day's move
      tokyo_london_expansion   : continuation in the direction of the day's
                                 move when |r| exceeds its trailing 20-day
                                 median |r| (range expansion day)
      london_am_break          : continuation in the direction of the day's
                                 move (breakout book)
    Exposure cell (d, pair, side) at the decision close instant of d."""
    out = {}
    for name in ["london_open_continuation", "late_ny_fade",
                 "tokyo_london_expansion", "london_am_break"]:
        s = Sched(f"ancestry_session_{name}")
        out[name] = s
    for pair in PAIRS:
        ser = SERIES[pair]
        absr = {}
        for i in range(20, len(ser)):
            d = ser[i]
            if not (S0_START <= d <= S0_END):
                continue
            med = float(np.median([abs(RET[pair][ser[j]]) for j in range(i - 19, i + 1)]))
            absr[d] = med
        for i in range(2, len(ser)):
            d = ser[i]
            if not (S0_START <= d <= S0_END):
                continue
            r_prev = RET[pair][d]
            r_day = r_prev  # r_t is the return ENDING at t
            sp = 0 if r_prev == 0 else (1 if r_prev > 0 else -1)
            # continuation of the PRIOR day's move held over day d:
            prev_r = RET[pair][ser[i - 1]]
            sc = 0 if prev_r == 0 else (1 if prev_r > 0 else -1)
            if sc != 0:
                out["london_open_continuation"].add(d, pair, sc)
            if sp != 0:
                out["late_ny_fade"].add(d, pair, -sp)
                out["london_am_break"].add(d, pair, sp)
                if d in absr and abs(RET[pair][d]) > absr[d]:
                    out["tokyo_london_expansion"].add(d, pair, sp)
    return out


# ------------------------------------------ V4 commodity-bloc risk-off -----
def sched_commodity_bloc():
    """FXFV4-A6-P1 anchor reconstruction (V5 precedent sched_f1, mean
    estimator): S_t = 0.5*(r_AUD + r_NZD - r_USDCAD); z_t vs trailing 60
    completed days strictly before t; trigger z <= -1; frozen 5-leg map;
    5-session hold entered next session -> exposure cells t+1..t+5."""
    trig = Sched("FXFV4-A6-P1_anchor_triggerday")
    exp = Sched("FXFV4-A6-P1_anchor_exposure")
    tri = ["AUDUSD", "NZDUSD", "USDCAD"]
    days = sorted(set.intersection(*[set(RET[p]) for p in tri]))
    days = [d for d in days if S0_START <= d <= S0_END]
    svals = []
    for d in days:
        svals.append(0.5 * (RET["AUDUSD"][d] + RET["NZDUSD"][d] - RET["USDCAD"][d]))
    all_days = [d for d in COMMON7 if S0_START <= d <= S0_END]
    idx_all = {d: i for i, d in enumerate(all_days)}
    for i in range(60, len(days)):
        win = svals[i - 60:i]
        mu = float(np.mean(win))
        sd = float(np.std(win, ddof=0))
        if sd == 0:
            continue
        z = (svals[i] - mu) / sd
        if z <= -1.0:
            t = days[i]
            m = {"AUDUSD": -1, "NZDUSD": -1, "USDCAD": 1, "USDJPY": -1, "USDCHF": -1}
            for p, sd_ in m.items():
                trig.add(t, p, sd_)
            j = idx_all.get(t)
            if j is not None:
                for kk in range(1, 6):
                    if j + kk < len(all_days):
                        for p, sd_ in m.items():
                            exp.add(all_days[j + kk], p, sd_)
    return trig, exp


# ------------------------------------------------------------ comparisons --
def to_map(sched, pairs=None):
    m = defaultdict(dict)
    for (d, p), v in sched.cells.items():
        if pairs is not None and p not in pairs:
            continue
        m[d][p] = v
    return m


def spearman(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return None
    rx = _ranks(x)
    ry = _ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def _ranks(v):
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v))
    sv = v[order]
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def compare(name_a, sched_a, name_b, sched_b):
    pairs_a = set(p for _, p in sched_a.cells)
    pairs_b = set(p for _, p in sched_b.cells)
    shared = sorted(pairs_a & pairs_b)
    res = {"a": name_a, "b": name_b,
           "n_cells_a": len(sched_a.cells), "n_cells_b": len(sched_b.cells),
           "pairs_a": sorted(pairs_a), "pairs_b": sorted(pairs_b),
           "shared_pairs": shared, "variants": {}}
    rhos = []
    if shared:
        # V1/V2: full shared-calendar grid, per pair its own observable dates
        xs, ys, xf, yf = [], [], [], []
        for p in shared:
            for d in SERIES[p]:
                if not (S0_START <= d <= S0_END):
                    continue
                va = sched_a.cells.get((d, p), 0)
                vb = sched_b.cells.get((d, p), 0)
                xs.append(float(va))
                ys.append(float(vb))
                xf.append(1.0 if (d, p) in sched_a.cells else 0.0)
                yf.append(1.0 if (d, p) in sched_b.cells else 0.0)
        r1 = spearman(xs, ys)
        r2 = spearman(xf, yf)
        res["variants"]["cellwise_signed_full_grid"] = {
            "n": len(xs), "rho": None if r1 is None else round(r1, 4)}
        res["variants"]["context_fire_full_grid"] = {
            "n": len(xf), "rho": None if r2 is None else round(r2, 4),
            "note": "context only (0/1 indicator, not a signed exposure series): negative = anti-coincidence (V5 precedent: 'good novelty signal'); excluded from the pooled gate"}
        if r1 is not None:
            rhos.append(abs(r1))
        # V3: per-date net signed sum over shared pairs (union date grid)
        dates = sorted(set(d for d, p in sched_a.cells if p in shared) |
                       set(d for d, p in sched_b.cells if p in shared))
        ma, mb = to_map(sched_a, shared), to_map(sched_b, shared)
        xa = [float(sum(ma.get(d, {}).values())) for d in dates]
        yb = [float(sum(mb.get(d, {}).values())) for d in dates]
        r3 = spearman(xa, yb)
        res["variants"]["netsigned_union_dates_shared_pairs"] = {
            "n": len(dates), "rho": None if r3 is None else round(r3, 4)}
        if r3 is not None:
            rhos.append(abs(r3))
        # V4: cellwise on the union of active (d,p) keys
        keys = sorted(set((d, p) for d, p in sched_a.cells if p in shared) |
                      set((d, p) for d, p in sched_b.cells if p in shared))
        xa = [float(sched_a.cells.get(k, 0)) for k in keys]
        yb = [float(sched_b.cells.get(k, 0)) for k in keys]
        r4 = spearman(xa, yb)
        res["variants"]["cellwise_union_active"] = {
            "n": len(keys), "rho": None if r4 is None else round(r4, 4)}
        if r4 is not None:
            rhos.append(abs(r4))
        # V5: SIGNED rho on the SHARED (co-exposed) cells only -- DIAGNOSTIC:
        # conditional on co-firing, so not a "pooled" statistic (RULES 2.4);
        # reported for the directional-kinship record, never gates
        inter_keys = sorted(set(sched_a.cells) & set(sched_b.cells))
        inter_keys = [k for k in inter_keys if k[1] in shared]
        if len(inter_keys) >= 3:
            xa = [float(sched_a.cells[k]) for k in inter_keys]
            yb = [float(sched_b.cells[k]) for k in inter_keys]
            r5 = spearman(xa, yb)
            res["variants"]["diagnostic_cellwise_signed_shared_cells_only"] = {
                "n": len(inter_keys), "rho": None if r5 is None else round(r5, 4),
                "note": "diagnostic only: conditional on co-firing; excluded from the pooled gate"}
        # V6: pooled signed rho restricted to B's (ancestor's) schedule
        # support, zeros retained for A -- the exposure-overlap question on
        # the region where the forbidden book actually is.  Pooled (zeros
        # in); reported as a sensitivity with its own over-bar flag.
        supp_b = sorted(k for k in sched_b.cells if k[1] in shared)
        if len(supp_b) >= 3:
            xa = [float(sched_a.cells.get(k, 0)) for k in supp_b]
            yb = [float(sched_b.cells[k]) for k in supp_b]
            r6 = spearman(xa, yb)
            res["variants"]["sensitivity_cellwise_signed_ancestor_support"] = {
                "n": len(supp_b), "rho": None if r6 is None else round(r6, 4),
                "note": "sensitivity: pooled on the ancestor's support; reported with margin, flagged if |rho| > bar"}
        # Jaccard + sign agreement
        ka = set((d, p) for d, p in sched_a.cells if p in shared)
        kb = set((d, p) for d, p in sched_b.cells if p in shared)
        inter = ka & kb
        union = ka | kb
        res["exposure_set_overlap"] = {
            "n_a": len(ka), "n_b": len(kb), "intersection": len(inter),
            "jaccard": round(len(inter) / len(union), 4) if union else None,
            "containment_b_in_a": round(len(inter) / len(kb), 4) if kb else None,
            "containment_a_in_b": round(len(inter) / len(ka), 4) if ka else None}
        if inter:
            same = sum(1 for k in inter
                       if sched_a.cells[k] == sched_b.cells[k])
            res["sign_agreement_shared_cells"] = {
                "n": len(inter), "same_sign": same,
                "rate": round(same / len(inter), 4)}
    else:
        # no shared pairs: date-level fire overlap is CONTEXT ONLY (a 0/1
        # indicator is not a signed exposure series; its NEGATIVE value is
        # anti-coincidence evidence, not ancestry) -- never a gate statistic
        dates = sorted(set(d for d, _ in sched_a.cells) | set(d for d, _ in sched_b.cells))
        xa = [1.0 if any((d, p) in sched_a.cells for p in PAIRS) else 0.0 for d in dates]
        yb = [1.0 if any((d, p) in sched_b.cells for p in PAIRS) else 0.0 for d in dates]
        r = spearman(xa, yb)
        res["variants"]["context_date_fire_no_shared_pairs"] = {
            "n": len(dates), "rho": None if r is None else round(r, 4),
            "note": "context only: positive = co-firing, negative = anti-coincidence; excluded from the gate"}
        da = set(d for d, _ in sched_a.cells)
        db = set(d for d, _ in sched_b.cells)
        inter = da & db
        res["exposure_date_overlap"] = {
            "n_a": len(da), "n_b": len(db), "intersection": len(inter),
            "jaccard": round(len(inter) / len(da | db), 4) if (da | db) else None}
    res["max_abs_rho"] = round(max(rhos), 4) if rhos else None
    worst = None
    for k, vv in res["variants"].items():
        rv = vv.get("rho")
        if rv is None:
            continue
        if worst is None or abs(rv) > abs(worst[1]):
            worst = (k, rv)
    res["max_abs_rho_variant"] = None if worst is None else worst[0]
    return res


Sched.pairs_all = lambda self: set(p for _, p in self.cells)


# ------------------------------------------------------------------- main --

# ============================ V7 proposal schedules (D2 novelty) ===========
H1 = {}   # pair -> sorted list of 1h bar datetimes (UTC)
H1C = {}  # pair -> {datetime: close}
def _load_h1():
    import glob as _g
    for pair in PAIRS:
        rows = []
        for f in sorted(_g.glob(f"{ROOT}/data_raw/forex_free_v1/{pair}_1h_*_a.json")):
            d = json.load(open(f))
            if d.get("status") != "ok":
                continue
            for v in d["values"]:
                rows.append((datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC),
                             float(v["close"])))
        rows.sort()
        H1[pair] = [r[0] for r in rows]
        H1C[pair] = dict(rows)
_load_h1()


def load_clocks_v7(path):
    rows = json.load(open(path))["clocks"]
    out = []
    for r in rows:
        T = parse_stamp(r["event_available_time_utc"])
        pc = r["precision_class"]
        w0 = T if pc.startswith("INSTANT") else (T.replace(hour=0, minute=0, second=0) + timedelta(days=1))
        out.append({"clock_id": r["clock_id"], "economy": r["economy"],
                    "pair": r["nonrep_pair"],
                    "decision_date": date.fromisoformat(r["decision_date"]),
                    "w0": w0, "w1": w0 + timedelta(hours=24),
                    "precision_class": pc})
    return out


CLK_V7 = load_clocks_v7(f"{ROOT}/research/control/forex_free_v7_run/p2_conditioning_clocks_v7.json")


def r_W(pair, w0, w1):
    """reaction return across W on the 1h bars (last close / first close - 1)."""
    bars = H1[pair]
    import bisect as _b
    i0 = _b.bisect_left(bars, w0)
    if i0 >= len(bars) or bars[i0] > w1:
        return None
    i1 = _b.bisect_right(bars, w1) - 1
    if i1 < i0:
        return None
    c0, c1 = H1C[pair].get(bars[i0]), H1C[pair].get(bars[i1])
    if not c0 or not c1:
        return None
    return c1 / c0 - 1.0


def sigma_20d(pair, i):
    """stdev (ddof=1) of the trailing 20 daily close-to-close log-returns
    ending at series index i (inclusive)."""
    if i < 20:
        return None
    ser = SERIES[pair]
    rs = [RET[pair][ser[j]] for j in range(i - 19, i + 1)]
    return float(np.std(rs, ddof=1))


def _funded_decision(w1):
    """first 16:00-NY at/after w1 (F-A7-PL-1 remediation)."""
    dd = w1.astimezone(NY).date()
    cand = datetime.combine(dd, datetime.min.time(), tzinfo=NY).replace(hour=16)
    while cand.astimezone(UTC) < w1:
        cand = cand + timedelta(days=1)
    return cand.astimezone(NY).date()


def _entry_hold(s, pair, d_entry, side, k, cur_exit):
    ser = SERIES[pair]
    if d_entry not in CLOSES[pair]:
        s.counts["entry_not_in_series"] += 1
        return False
    ie = ser.index(d_entry)
    if ie + k >= len(ser):
        s.counts["exit_beyond_series"] += 1
        return False
    entry_close, exit_close = ny1600(ser[ie]), ny1600(ser[ie + k])
    if not s0_exit_ok(exit_close):
        s.counts["s0_exit_excluded"] += 1
        return False
    if not overlap_walk_ok(entry_close, exit_close, cur_exit.get(pair)):
        s.counts["collision_skipped"] += 1
        return False
    cur_exit[pair] = exit_close
    for j in range(ie, ie + k):
        s.add(ser[j], pair, side)
    s.counts["trades"] += 1
    return True


def sched_v7_a4p1(k=4, sham=False, economies=("GB", "CA")):
    """FXFV7-A4-P1 anchor: position = sign(r_W) on the NON-reporting pair at
    the funded decision; hold k sessions. Sham: event +7 calendar days."""
    s = Sched("FXFV7-A4-P1_sham+7d" if sham else "FXFV7-A4-P1_anchor_k%d" % k)
    cur_exit = {}
    for c in sorted(CLK_V7, key=lambda x: (x["decision_date"], x["economy"], x["pair"])):
        if c["economy"] not in economies:
            continue
        s.counts["clocks"] += 1
        w0, w1 = c["w0"], c["w1"]
        if sham:
            w0 += timedelta(days=7); w1 += timedelta(days=7)
        d_entry = _funded_decision(w1)
        rw = r_W(c["pair"], w0, w1)
        if rw is None:
            s.counts["rw_unavailable"] += 1
            continue
        side = 0 if rw == 0 else (1 if rw > 0 else -1)
        if side == 0:
            s.counts["zero_signal"] += 1
            continue
        _entry_hold(s, c["pair"], d_entry, side, k, cur_exit)
    return s


def sched_v7_a4p2(theta=1.0, k=3, sham=False):
    """FXFV7-A4-P2 anchor: |o| = |r_W|/sigma_20d >= theta gates a fade
    -sign(r_W) on the NON-reporting pair at the funded decision; hold k."""
    s = Sched("FXFV7-A4-P2_sham+7d" if sham else "FXFV7-A4-P2_anchor_t%.1f_k%d" % (theta, k))
    cur_exit = {}
    for c in sorted(CLK_V7, key=lambda x: (x["decision_date"], x["economy"], x["pair"])):
        s.counts["clocks"] += 1
        w0, w1 = c["w0"], c["w1"]
        if sham:
            w0 += timedelta(days=7); w1 += timedelta(days=7)
        d_entry = _funded_decision(w1)
        rw = r_W(c["pair"], w0, w1)
        if rw is None:
            s.counts["rw_unavailable"] += 1
            continue
        ser = SERIES[c["pair"]]
        if d_entry not in CLOSES[c["pair"]]:
            s.counts["entry_not_in_series"] += 1
            continue
        sig = sigma_20d(c["pair"], ser.index(d_entry))
        if sig is None or sig == 0:
            s.counts["sigma_unavailable"] += 1
            continue
        o = rw / sig
        s.counts["clocks_with_rw_and_sigma"] += 1
        if abs(o) < theta:
            s.counts["gate_below_theta_flat"] += 1
            continue
        side = -1 if rw > 0 else 1
        _entry_hold(s, c["pair"], d_entry, side, k, cur_exit)
    return s


def sched_v7_a6p1(H=20, hold=5):
    """FXFV7-A6-P1 anchor: weekly grid (every 5th common decision day),
    strength = trailing H-day log-return, long top-3 / short bottom-3, hold."""
    s = Sched("FXFV7-A6-P1_anchor_h%d" % H)
    cur_exit = {}
    ser = COMMON_RET
    # grid anchor: first common day with H-day history + 65-day warmup,
    # then every 5th trading day (convention disclosed)
    i0 = max(H, 65)
    grid = list(range(i0, len(ser), 5))
    for i in grid:
        t = ser[i]
        if not (S0_START <= t <= S0_END):
            continue
        strengths = []
        for pair in PAIRS:
            sp = SERIES[pair]
            if t not in CLOSES[pair]:
                continue
            j = sp.index(t)
            if j < H:
                continue
            strengths.append((math.fsum(RET[pair][sp[j - q]] for q in range(H)), pair))
        if len(strengths) < 6:
            s.counts["panel_incomplete"] += 1
            continue
        strengths.sort()
        book = {}
        for q, (_, pair) in enumerate(strengths):
            book[pair] = 1 if q >= len(strengths) - 3 else (-1 if q < 3 else 0)
        for pair, side in book.items():
            if side == 0:
                continue
            _entry_hold(s, pair, t, side, hold, cur_exit)
        s.counts["grid_days"] += 1
    return s


def sched_v7_a6p2(q=80, hold=5):
    """FXFV7-A6-P2 anchor: lead EURUSD idiosyncratic move d_t =
    r_EURUSD,t - panel-mean(r_t); expanding q-th pct of |d| (min 60 obs);
    trigger -> all 6 followers sign(d_t) entered next session, hold,
    episode-level non-overlap."""
    s = Sched("FXFV7-A6-P2_anchor_q%d" % q)
    ser = COMMON_RET
    d_hist = []
    d_map = {}
    for i in range(len(ser)):
        t = ser[i]
        rs = [RET[p][t] for p in PAIRS if t in RET[p]]
        if len(rs) < 7:
            continue
        mu = float(np.mean(rs))
        d_t = RET["EURUSD"][t] - mu
        d_map[i] = d_t
    cur_exit = {}
    open_until = -1
    idx_ser = {i: t for i, t in enumerate(ser)}
    hist = []
    for i in sorted(d_map):
        if i <= open_until:
            hist.append(abs(d_map[i]))
            continue
        if len(hist) >= 60:
            thr = float(np.percentile(hist, q))
            if abs(d_map[i]) >= thr:
                t = ser[i]
                side = 1 if d_map[i] > 0 else -1
                if i + 1 < len(ser):
                    d_entry = ser[i + 1]
                    legs = 0
                    for pair in PAIRS:
                        if pair == "EURUSD":
                            continue
                        if _entry_hold(s, pair, d_entry, side, hold, cur_exit):
                            legs += 1
                    if legs:
                        s.counts["trigger_days"] += 1
                        open_until = i + hold
        hist.append(abs(d_map[i]))
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    out_meta = {
        "schema": "forex_free_v7_d2_a7n_ancestry_rho_computation_v1",
        "computed_utc": datetime.now(UTC).isoformat(),
        "convention": "daily completed 16:00 America/New_York decision bars derived from staged H1 snapshots (V6-precedent machinery, ported verbatim)",
        "exposure_cell_convention": "cell (decision_date, pair, side) iff held at that date's 16:00-NY close; opened close(f), closed close(x) -> cells f..x-1",
        "observable_span_note": "staged H1 snapshots begin 2020-01-30; all schedules produce no cells before it; comparisons measured on the shared observable span within S0",
        "no_pnl": "schedule construction and rank correlations only",
        "bar": 0.20,
        "gate_statistic": "max |Spearman rho| over POOLED signed variants (cellwise_signed_full_grid, cellwise_union_active, netsigned_union_dates_shared_pairs)",
    }
    P = {
        "FXFV7-A4-P1_anchor_k4": sched_v7_a4p1(4, False),
        "FXFV7-A4-P2_anchor_t1.0_k3": sched_v7_a4p2(1.0, 3, False),
        "FXFV7-A6-P1_anchor_h20": sched_v7_a6p1(20, 5),
        "FXFV7-A6-P2_anchor_q80": sched_v7_a6p2(80, 5),
    }
    differential = load_ledger_reader(f"{ROOT}/research/control/forex_free_v5_run/announcement_ledger_v5_extension.jsonl")
    A = {
        "V6_A4P1_anchor_k5": sched_a4p1(False, 5),
        "V6_A4P1_neighbour_k10": sched_a4p1(False, 10),
        "V6_A4P1_sham+7d": sched_a4p1(True, 5),
        "V6_A6P2_anchor": sched_a6p2(0),
        "V5_anchor": sched_v5_family(CLK_V5, False),
        "V5_sham": sched_v5_family(CLK_V5, True),
        "carry_unconditional": sched_carry(differential, False),
        "carry_v3gate_recon": sched_carry(differential, True),
    }
    sess = sched_sessions()
    A.update({f"session_{k}": v for k, v in sess.items()})
    trig, exp = sched_commodity_bloc()
    A["V4_commodity_bloc_trigger"] = trig
    A["V4_commodity_bloc_exposure"] = exp

    sched_dump = {}
    for nm, s in list(P.items()) + list(A.items()):
        sched_dump[nm] = {"n_cells": len(s.cells), "counts": dict(s.counts),
                          "pairs": sorted(set(p for _, p in s.cells))}
    json.dump(sched_dump, open(f"{OUT}/schedule_summary.json", "w"), indent=1)
    json.dump({nm: {f"{d}|{p}": v for (d, p), v in s.cells.items()} for nm, s in P.items()},
              open(f"{OUT}/schedule_cells_proposals_v7.json", "w"))
    json.dump({nm: {f"{d}|{p}": v for (d, p), v in s.cells.items()} for nm, s in A.items()},
              open(f"{OUT}/schedule_cells_ancestors.json", "w"))

    comps = {}
    gate = {}
    for pn, ps in P.items():
        best = ("", 0.0)
        for an, s in A.items():
            key = f"{pn}__vs__{an}"
            comps[key] = compare(pn, ps, an, s)
            rhos = []
            for v in ("cellwise_signed_full_grid", "cellwise_union_active",
                      "netsigned_union_dates_shared_pairs"):
                r = comps[key]["variants"].get(v, {}).get("rho")
                if r is not None:
                    rhos.append(abs(r))
            mx = max(rhos) if rhos else 0.0
            comps[key]["pooled_max_abs_rho"] = round(mx, 4)
            if mx > best[1]:
                best = (an, mx)
        gate[pn] = {"gate_statistic": "max |Spearman rho| over POOLED signed variants",
                    "worst_ancestor": best[0], "max_pooled_abs_rho": round(best[1], 4),
                    "bar": 0.20, "verdict": "PASS_novel" if best[1] <= 0.20 else "ANCESTRY_VETO"}
    json.dump(comps, open(f"{OUT}/comparisons_vs_ancestors.json", "w"), indent=1)

    # intra-proposal wave-diversity (context)
    names = list(P)
    intra = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            key = f"{names[i]}__vs__{names[j]}"
            intra[key] = compare(names[i], P[names[i]], names[j], P[names[j]])
    json.dump(intra, open(f"{OUT}/comparisons_intra_proposals.json", "w"), indent=1)

    verdict = {"schema": "forex_free_v7_d2_novelty_gate_v1",
               "bar": 0.20, "gate": gate,
               "ancestors": list(A), "proposals": list(P),
               "meta": out_meta}
    json.dump(verdict, open(f"{OUT}/novelty_gate.json", "w"), indent=1)
    print(json.dumps(gate, indent=1))


if __name__ == "__main__":
    main()
