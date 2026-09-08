#!/usr/bin/env python3
"""A9 D2 feasibility measurement — FOREX-FREE-V5, counts/coverage/populations ONLY.

FORBIDDEN BY SCOPE AND HONORED HERE: no PnL, no strategy returns, no cost-adjusted
outcomes. The script computes (a) bar-existence schedules, (b) sign bits and trigger
booleans required to define decision/activation populations (P2 sequence agreement,
A6-P1 exact-zero direction check, A6-P2 |z|>=2 triggers), (c) fold populations,
(d) fill COUNTS x frozen cost ladder arithmetic, (e) control-schedule identity
fractions. No price magnitude, return magnitude or PnL value is emitted.

Basis: 16:00 America/New_York completed daily bar calendar per pair = the staged
1day snapshot date set (data_raw/forex_free_v1/*_1day_2018-09-01_a.json). Bar
completion instant = that date 16:00 NY in UTC (zoneinfo, DST-aware).
"""
import json, hashlib, math
from datetime import datetime, timedelta, date, timezone, time as dtime
from zoneinfo import ZoneInfo
from pathlib import Path
from collections import defaultdict

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v5/d2-a9-feasibility")
DATA = WT / "data_raw/forex_free_v1"
OUT = WT / "research/control/forex_free_v5_run/d2_a9_evidence/d2_a9_measure_output.json"

NY = ZoneInfo("America/New_York")
S0_START = datetime(2018, 4, 4, tzinfo=timezone.utc)
S0_END_CAP = datetime(2025, 7, 25, tzinfo=timezone.utc)   # entry instant must be < cap
S0_END_DAY = date(2025, 7, 24)

# frozen kernel constants (research/assets/forex_free_v3/scored_runner.py)
FOLD_BOUNDARIES = ["2020-03-01T00:00:00+00:00", "2022-05-01T00:00:00+00:00",
                   "2024-07-01T00:00:00+00:00", "2026-09-02T23:59:59+00:00"]
PURGE_DAYS = 14
MIN_DECISIONS_PER_ARM = 40
FOLD_POPULATED_MIN_TRADES = 30
NOTIONAL = 10000
BPS = 0.00015  # 1.5 bps per side at tier 1.0 (decimal fraction of notional)
TIERS = (1.0, 1.5, 2.0)

PAIR_OF = {"GB": "GBPUSD", "CA": "USDCAD", "AU": "AUDUSD", "NZ": "NZDUSD"}
EURUSD = "EURUSD"


def parse_iso(ts):
    return datetime.fromisoformat(ts)


def fold_of(entry_iso):
    t = parse_iso(entry_iso)
    for i in range(3):
        lo = parse_iso(FOLD_BOUNDARIES[i]); hi = parse_iso(FOLD_BOUNDARIES[i + 1])
        if lo <= t < hi:
            if t < lo + timedelta(days=PURGE_DAYS):
                return None  # purged
            return i
    return None  # warmup region (< B0) or beyond last boundary


def bar_instant(d):
    return datetime.combine(d, dtime(16, 0), tzinfo=NY).astimezone(timezone.utc)


def is_friday_close(inst):
    ny = inst.astimezone(NY)
    return ny.weekday() == 4  # Friday 16:00 NY -> session gate closes (hm == 16:00 not < 16:00)


# ---------- staged daily calendars ----------
def load_daily(pair):
    d = json.load(open(DATA / f"{pair}_1day_2018-09-01_a.json"))
    rows = d["values"]
    wk = [v["datetime"] for v in rows if datetime.strptime(v["datetime"], "%Y-%m-%d").weekday() >= 5]
    # frozen session-gate convention: provider weekend-stamped rows are NOT NY sessions
    rows = [v for v in rows if datetime.strptime(v["datetime"], "%Y-%m-%d").weekday() < 5]
    dates = [datetime.strptime(v["datetime"], "%Y-%m-%d").date() for v in rows]
    closes = {datetime.strptime(v["datetime"], "%Y-%m-%d").date(): float(v["close"]) for v in rows}
    dates.sort()
    return dates, closes, len(wk)


CAL = {}
CLO = {}
WKND = {}
for p in ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF"]:
    CAL[p], CLO[p], WKND[p] = load_daily(p)

CALSUM = {p: {"first": str(CAL[p][0]), "last": str(CAL[p][-1]), "bars": len(CAL[p]),
              "weekend_stamped_rows_excluded": WKND[p]} for p in CAL}


def idx_of(pair, d):  # index in calendar
    return CAL[pair].index(d)


def bar_after(pair, inst):
    """first completed 16:00-NY bar date whose completion instant is strictly > inst"""
    ds = CAL[pair]
    lo, hi = 0, len(ds)
    while lo < hi:
        mid = (lo + hi) // 2
        if bar_instant(ds[mid]) <= inst:
            lo = mid + 1
        else:
            hi = mid
    return ds[lo] if lo < len(ds) else None


def bar_before(pair, inst):
    """last completed 16:00-NY bar date whose completion instant is strictly < inst"""
    ds = CAL[pair]
    lo, hi = 0, len(ds)
    while lo < hi:
        mid = (lo + hi) // 2
        if bar_instant(ds[mid]) < inst:
            lo = mid + 1
        else:
            hi = mid
    return ds[lo - 1] if lo > 0 else None


def next_bar(pair, d):
    i = idx_of(pair, d)
    return CAL[pair][i + 1] if i + 1 < len(CAL[pair]) else None


def bar_plus_sessions(pair, d, n):
    i = idx_of(pair, d) + n
    return CAL[pair][i] if i < len(CAL[pair]) else None


# ---------- clocks ----------
clocks = json.load(open(WT / "research/control/forex_free_v5_run/p3_conditioning_clocks_v5.json"))["clocks"]
by_eco = defaultdict(list)
for c in clocks:
    by_eco[c["economy"]].append(c)
for e in by_eco:
    by_eco[e].sort(key=lambda c: c["decision_date"])

ca_stamps_0830 = sum(1 for c in by_eco["CA"] if "T08:30:00Z" in c["available_time_utc"])

RESULTS = {"basis": {"calendars": CALSUM,
                     "ca_0830Z_stamps": ca_stamps_0830,
                     "n_clocks": len(clocks)}}


def counts_by_fold(entries):
    f = defaultdict(int)
    for e in entries:
        f[fold_of(e)] += 1
    return {"fold0": f[0], "fold1": f[1], "fold2": f[2],
            "purged": f[None], "pre_B0_warmup_unscored": 0}


def split_warmup(entries):
    b0 = parse_iso(FOLD_BOUNDARIES[0])
    pre = sum(1 for e in entries if parse_iso(e) < b0)
    c = counts_by_fold(entries)
    c["pre_B0_warmup_unscored"] = pre
    return c


# ============================================================ A4-P1
def a4p1():
    res = {"anchor": {}, "control": {}, "neighbour": {}}
    dec_ok, unexec, weekend = [], [], []
    predata = defaultdict(int)
    eco_ok, eco_wk = defaultdict(int), defaultdict(int)
    for e, lst in by_eco.items():
        pair = PAIR_OF[e]
        for c in lst:
            a = parse_iso(c["available_time_utc"])
            b = bar_before(pair, a)
            aft = bar_after(pair, a)
            if b is None or aft is None or bar_instant(aft) > S0_END_CAP:
                unexec.append(c["decision_date"])
                if b is None:
                    predata[e] += 1
                continue
            entry = next_bar(pair, aft)
            if entry is None or bar_instant(entry) >= S0_END_CAP:
                unexec.append(c["decision_date"]); continue
            eco_ok[e] += 1
            dec_ok.append({"eco": e, "decision": bar_instant(aft), "entry": bar_instant(entry)})
            if is_friday_close(bar_instant(entry)):
                weekend.append(c["decision_date"]); eco_wk[e] += 1
    # session gate: weekend-dropped entries are NOT trades (runner drops fail-closed before fold metrics)
    trades = [d for d in dec_ok if not is_friday_close(d["entry"])]
    # trades executable end-to-end: exit bar must exist H sessions after the ENTRY bar
    def with_exit(trs, H):
        ok, noex = [], []
        for d in trs:
            ed = d["entry"].astimezone(NY).date()
            ex = bar_plus_sessions(PAIR_OF[d["eco"]], ed, H)
            (ok if ex is not None else noex).append(d)
        return ok, noex
    ok5, noex5 = with_exit(trades, 5)
    ok10, noex10 = with_exit(trades, 10)
    res["anchor"] = {
        "clocks_S0": 246,
        "decisions_executable_pre_gate": len(dec_ok),
        "decisions_lost_pre_data": dict(predata),
        "unexecutable_other": len(unexec) - sum(predata.values()),
        "unexecutable_list": unexec[:20],
        "per_economy_decisions": dict(eco_ok),
        "weekend_gate_dropped_entries": len(weekend),
        "weekend_gate_dropped_per_economy": dict(eco_wk),
        "trades_post_session_gate": len(trades),
        "trades_H5_exit_bar_missing": len(noex5),
        "trades_H5_executable": len(ok5),
        "fills_H5": 2 * len(ok5),
        "folds_H5": split_warmup([d["entry"].isoformat() for d in ok5]),
        "trades_H10_neighbour_executable": len(ok10),
        "fills_H10_neighbour": 2 * len(ok10),
        "folds_H10_neighbour": split_warmup([d["entry"].isoformat() for d in ok10]),
        "reaction_sign_computed": False,  # scope: not computed (not needed for schedule)
    }
    # control: first trading day >= a+35d outside +-5 sessions of every first-after bar of that economy
    firstafter = defaultdict(list)
    for e, lst in by_eco.items():
        pair = PAIR_OF[e]
        for c in lst:
            a = parse_iso(c["available_time_utc"])
            fa = bar_after(pair, a)
            if fa is not None:
                firstafter[e].append(fa)
    sess_idx = {e: {d: i for i, d in enumerate(CAL[PAIR_OF[e]])} for e in PAIR_OF}
    def outside_window(e, d):
        ix = sess_idx[e].get(d)
        if ix is None:
            return True
        for fa in firstafter[e]:
            j = sess_idx[e].get(fa)
            if j is not None and abs(ix - j) <= 5:
                return False
        return True
    ctrl_days, naive, dedup_viol, wk_drop_ctrl = set(), 0, 0, 0
    for e, lst in by_eco.items():
        pair = PAIR_OF[e]
        for c in lst:
            a = parse_iso(c["available_time_utc"])
            start = (a + timedelta(days=35)).date()
            ds = CAL[pair]
            lo, hi = 0, len(ds)
            while lo < hi:
                mid = (lo + hi) // 2
                if ds[mid] < start: lo = mid + 1
                else: hi = mid
            i = lo
            while i < len(ds) and not outside_window(e, ds[i]):
                i += 1
            if i < len(ds):
                naive += 1
                if ds[i] in ctrl_days: dedup_viol += 1
                ctrl_days.add(ds[i])
                ent = next_bar(pair, ds[i])
                if ent is not None and is_friday_close(bar_instant(ent)):
                    wk_drop_ctrl += 1
    anchor_dates = set(d["decision"].astimezone(NY).date() for d in dec_ok)
    overlap = ctrl_days & anchor_dates
    anchor_by_eco = defaultdict(set)
    for d in dec_ok:
        anchor_by_eco[d["eco"]].add(d["decision"].astimezone(NY).date())
    ctrl_by_eco = defaultdict(set)
    for e, lst in by_eco.items():
        pair = PAIR_OF[e]
        for c in lst:
            a = parse_iso(c["available_time_utc"])
            start = (a + timedelta(days=35)).date()
            ds = CAL[pair]
            lo, hi = 0, len(ds)
            while lo < hi:
                mid = (lo + hi) // 2
                if ds[mid] < start: lo = mid + 1
                else: hi = mid
            i = lo
            while i < len(ds) and not outside_window(e, ds[i]):
                i += 1
            if i < len(ds):
                ctrl_by_eco[e].add(ds[i])
    overlap_same_pair = sum(len(anchor_by_eco[e] & ctrl_by_eco[e]) for e in PAIR_OF)
    res["control"] = {
        "placebo_anchor_days_unique": len(ctrl_days),
        "per_print_naive_anchors": naive,
        "per_print_collisions_same_day": dedup_viol,
        "weekend_gate_dropped_placebo_entries": wk_drop_ctrl,
        "date_overlap_with_anchor_decisions_cross_pair": len(overlap),
        "date_overlap_with_anchor_same_pair": overlap_same_pair,
        "control_decision_population_note": "control dates are outside +-5 sessions of every print; anchor dates are print first-after bars",
    }
    return res


# ============================================================ A4-P2
def a4p2():
    res = {}
    # reaction sign bits per clock (signal input only; no magnitudes emitted)
    def rsign(pair, a):
        b = bar_before(pair, a); aft = bar_after(pair, a)
        if b is None or aft is None:
            return None
        return 0 if CLO[pair][aft] == CLO[pair][b] else (1 if CLO[pair][aft] > CLO[pair][b] else -1)
    sig = {}
    for e, lst in by_eco.items():
        pair = PAIR_OF[e]
        for c in lst:
            sig[(e, c["decision_date"])] = rsign(pair, parse_iso(c["available_time_utc"]))
    # donor latest completed reaction sign before a decision instant
    def donor_sign_before(e_donor, inst):
        pair = PAIR_OF[e_donor]; best = None
        for c in by_eco[e_donor]:
            a = parse_iso(c["available_time_utc"])
            fa = bar_after(pair, a)
            if fa is not None and bar_instant(fa) < inst:
                best = sig[(e_donor, c["decision_date"])]
        return best
    seq_total, agree, zero_break, unexec_seq, wk_drop = defaultdict(int), defaultdict(int), defaultdict(int), [], defaultdict(int)
    anchor_trades = []
    for e, lst in by_eco.items():
        pair = PAIR_OF[e]
        for prev, cur in zip(lst, lst[1:]):
            seq_total[e] += 1
            s_prev, s_cur = sig[(e, prev["decision_date"])], sig[(e, cur["decision_date"])]
            if s_prev is None or s_cur is None:
                unexec_seq.append(cur["decision_date"]); continue
            if s_prev == 0 or s_cur == 0:
                zero_break[e] += 1; continue
            if s_cur == s_prev:
                agree[e] += 1
                a = parse_iso(cur["available_time_utc"])
                aft = bar_after(pair, a)
                entry = next_bar(pair, aft)
                if entry is None or bar_instant(entry) >= S0_END_CAP:
                    unexec_seq.append(cur["decision_date"]); continue
                if is_friday_close(bar_instant(entry)):
                    wk_drop[e] += 1; continue
                anchor_trades.append({"eco": e, "decision": bar_instant(aft).isoformat(),
                                      "entry": bar_instant(entry).isoformat(), "dir": int(s_cur),
                                      "seq_span_days": (parse_iso(cur["decision_date"]) - parse_iso(prev["decision_date"])).days})
    # Q=15 / Q=30 exit existence + folds (exit = Q sessions after ENTRY bar)
    def with_exit(trs, Q):
        ok, noex = [], []
        for t in trs:
            ed = parse_iso(t["entry"]).astimezone(NY).date()
            ex = bar_plus_sessions(PAIR_OF[t["eco"]], ed, Q)
            (ok if ex is not None else noex).append(t)
        return ok, noex
    wk_drop_total = sum(wk_drop.values())
    ok15, noex15 = with_exit(anchor_trades, 15); ok30, noex30 = with_exit(anchor_trades, 30)
    gap_adjacent = sum(1 for t in anchor_trades if t["seq_span_days"] > 45)
    res["anchor"] = {
        "sequences_S0_total": dict(seq_total), "sequences_total": sum(seq_total.values()),
        "sign_agreement_entries_pre_gate": dict(agree), "agreement_entries_total": len(anchor_trades),
        "weekend_gate_dropped_per_economy": dict(wk_drop),
        "weekend_gate_dropped_total": wk_drop_total,
        "trades_post_gate": len(anchor_trades),
        "zero_reaction_breaks": dict(zero_break),
        "unexecutable_seq_decisions": len(unexec_seq),
        "gap_adjacent_sequences_span_gt_45d": gap_adjacent,
        "trades_Q15_exit_missing": len(noex15), "trades_Q15_executable": len(ok15),
        "fills_Q15": 2 * len(ok15),
        "folds_Q15": split_warmup([t["entry"] for t in ok15]),
        "trades_Q30_neighbour_executable": len(ok30),
        "folds_Q30_neighbour": split_warmup([t["entry"] for t in ok30]),
    }
    # implied agreement-rate floor: trades needed >= 40
    res["anchor"]["implied_agreement_rate_pct"] = round(100.0 * len(anchor_trades) / max(1, sum(seq_total.values())), 1)
    # control: pseudo-sequence with donor mapping GB->CA, CA->AU, AU->NZ, NZ->GB
    donor_map = {"GB": "CA", "CA": "AU", "AU": "NZ", "NZ": "GB"}
    ctrl_trades, donor_skip, ctrl_wk = [], 0, 0
    for e, lst in by_eco.items():
        pair = PAIR_OF[e]
        for prev, cur in zip(lst, lst[1:]):
            s_prev, s_cur = sig[(e, prev["decision_date"])], sig[(e, cur["decision_date"])]
            if s_cur is None or s_cur == 0:
                continue
            a = parse_iso(cur["available_time_utc"]); aft = bar_after(pair, a)
            if aft is None: continue
            inst = bar_instant(aft)
            ds = donor_sign_before(donor_map[e], inst)
            if ds is None or ds == 0:
                donor_skip += 1; continue
            if ds == s_cur:
                entry = next_bar(pair, aft)
                if entry is None or bar_instant(entry) >= S0_END_CAP: continue
                if is_friday_close(bar_instant(entry)):
                    ctrl_wk += 1; continue
                ctrl_trades.append({"decision": inst.isoformat(), "entry": bar_instant(entry).isoformat(), "dir": int(s_cur)})
    anchor_by_date = {t["decision"]: t["dir"] for t in anchor_trades}
    co = [t for t in ctrl_trades if t["decision"] in anchor_by_date]
    same_dir = sum(1 for t in co if anchor_by_date[t["decision"]] == t["dir"])
    only_ctrl = sum(1 for t in ctrl_trades if t["decision"] not in anchor_by_date)
    only_anch = sum(1 for d in anchor_by_date if d not in {t["decision"] for t in ctrl_trades})
    res["control_pseudo_sequence"] = {
        "control_trades": len(ctrl_trades),
        "weekend_gate_dropped": ctrl_wk,
        "donor_unavailable_skips": donor_skip,
        "co_traded_dates_with_anchor": len(co),
        "same_direction_on_co_dates": same_dir,
        "direction_identity_pct_on_co_dates": round(100.0 * same_dir / max(1, len(co)), 1),
        "control_only_dates": only_ctrl,
        "anchor_only_dates": only_anch,
        "schedule_identity_pct_dates": round(100.0 * len(co) / max(1, len(set(anchor_by_date) | {t["decision"] for t in ctrl_trades})), 1),
        "folds_Q15": split_warmup([t["entry"] for t in ctrl_trades]),
    }
    return res


# ============================================================ A6-P1
def a6p1():
    all_clocks = [(e, c) for e in PAIR_OF for c in by_eco[e]]
    all_clocks.sort(key=lambda x: x[1]["available_time_utc"])

    def build(shift_days):
        dec, unexec, weekend, refused_span, warmup_fail, zero_dir, gap_lag = [], [], [], [], [], 0, 0
        for e, c in all_clocks:
            pair = PAIR_OF[e]
            a = parse_iso(c["available_time_utc"]) + timedelta(days=shift_days)
            X = bar_after(pair, a); F = bar_before(pair, a)
            if F is None or X is None:
                unexec.append(c["decision_date"]); continue
            Di = idx_of(pair, F)
            if Di == 0:
                unexec.append(c["decision_date"]); continue
            D = CAL[pair][Di - 1]
            if bar_instant(F) >= S0_END_CAP:
                unexec.append(c["decision_date"]); continue
            # warmup: >=11 closes strictly before D
            if Di - 1 < 11:
                warmup_fail.append(c["decision_date"]); continue
            # fill lag D->F <= 4 calendar days
            if (bar_instant(F) - bar_instant(D)).days > 4:
                gap_lag += 1; continue
            # direction: -sign(10-day sum); exact zero -> NO_TRADE (boolean check only)
            if shift_days == 0:
                cl = [CLO[pair][CAL[pair][Di - 1 - k]] for k in range(11)]
                s = sum(math.log(cl[i] / cl[i + 1]) for i in range(10))
                if s == 0.0:
                    zero_dir += 1; continue
            # fold force-flat: window F..X crossing internal boundary -> refused (kernel governs)
            span_refused = False
            for b in FOLD_BOUNDARIES[1:3]:
                bb = parse_iso(b)
                if bar_instant(F) < bb < bar_instant(X):
                    span_refused = True
            if span_refused:
                refused_span.append(c["decision_date"]); continue
            if is_friday_close(bar_instant(F)):
                weekend.append(c["decision_date"]); continue
            dec.append({"eco": e, "decision": bar_instant(D).isoformat(),
                        "entry": bar_instant(F).isoformat(), "exit": bar_instant(X).isoformat()})
        return dec, {"unexecutable": len(unexec), "warmup_lt11_fails": len(warmup_fail),
                     "exact_zero_direction_NO_TRADE": zero_dir,
                     "fill_lag_gt4d_fails": gap_lag,
                     "fold_force_flat_refused_spans": len(refused_span),
                     "weekend_gate_dropped": len(weekend)}
    dec, diag = build(0)
    # governor overlap check per pair (entry/exit windows must not overlap)
    open_pos, gov_blocks = set(), 0
    kept = []
    for t in sorted(dec, key=lambda x: x["entry"]):
        if t["eco"] in open_pos:
            gov_blocks += 1; continue
        open_pos.add(t["eco"])
    # positions release at exit: process chronologically
    open_until = {}
    kept, gov_blocks = [], 0
    for t in sorted(dec, key=lambda x: x["entry"]):
        e = t["eco"]
        if e in open_until and parse_iso(t["decision"]) < open_until[e]:
            gov_blocks += 1; continue
        open_until[e] = parse_iso(t["exit"])
        kept.append(t)
    res = {"anchor": {"clocks": len(all_clocks), "decisions_trades": len(kept),
                      "fills": 2 * len(kept), "diagnostics": diag,
                      "folds": split_warmup([t["entry"] for t in kept]),
                      "governor_blocks": gov_blocks}}
    # control: +7d sham, valid iff no evidenced clock of any of the 4 economies strictly inside (F', X')
    sham_dec, sham_dropped, sham_diag_none = [], 0, 0
    avail_insts = [parse_iso(c["available_time_utc"]) for _, c in all_clocks]
    for e, c in all_clocks:
        pair = PAIR_OF[e]
        a = parse_iso(c["available_time_utc"]) + timedelta(days=7)
        X = bar_after(pair, a); F = bar_before(pair, a)
        if F is None or X is None or bar_instant(F) >= S0_END_CAP:
            continue
        if any(bar_instant(F) < av < bar_instant(X) for av in avail_insts):
            sham_dropped += 1; continue
        Di = idx_of(pair, F)
        if Di == 0 or Di - 1 < 11:
            continue
        if is_friday_close(bar_instant(F)):
            continue
        D = CAL[pair][Di - 1]
        sham_dec.append(bar_instant(F).isoformat())
    res["control_sham"] = {
        "valid_sham_decisions": len(sham_dec),
        "sham_dropped_clock_inside_window": sham_dropped,
        "folds": split_warmup(sham_dec),
        "date_overlap_with_anchor": len(set(sham_dec) & {t["entry"] for t in kept}),
    }
    # stale-calendar benchmark: anchored to c_prev (first clock per economy skipped)
    bench = 0
    for e in PAIR_OF:
        bench += max(0, len(by_eco[e]) - 1)
    res["benchmark_stale_calendar"] = {"schedule_population_upper_bound": bench}
    return res


# ============================================================ A6-P2
def a6p2():
    legs = ["GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]
    edates, ecloses = CAL[EURUSD], CLO[EURUSD]
    rets = []  # (date, ret_signz info) — only booleans kept
    trig_days = []
    N = 120
    for i in range(N + 1, len(edates)):
        d = edates[i]
        if d > S0_END_DAY:
            break
        r = math.log(ecloses[d] / ecloses[edates[i - 1]])
        window = [math.log(ecloses[edates[i - 1 - k]] / ecloses[edates[i - 2 - k]]) for k in range(N)]
        mu = sum(window) / N
        var = sum((x - mu) ** 2 for x in window) / (N - 1)
        sd = math.sqrt(var)
        if sd > 0 and abs(r / sd) >= 2.0:
            trig_days.append(d)
    # per-leg schedule with governor (1-NY-day hold, next-session entry):
    # a leg is blocked at a trigger decision instant t iff its open position's
    # entry stamp <= t < exit stamp (consecutive-day triggers are blocked).
    leg_entries = defaultdict(list)
    weekend_drops = 0; refused_span = []; unexec = 0; gov_blocks = 0
    open_pos = {}  # leg -> (entry_stamp, exit_stamp)
    trades_per_leg = defaultdict(int)
    all_entry_insts = []
    for d in trig_days:
        i = idx_of(EURUSD, d)
        t_dec = bar_instant(d)
        nxt = edates[i + 1] if i + 1 < len(edates) else None
        if nxt is None or bar_instant(nxt) >= S0_END_CAP:
            unexec += 1; continue
        for l in legs:
            if l in open_pos:
                e_s, x_s = open_pos[l]
                if e_s <= t_dec < x_s:
                    gov_blocks += 1; continue
            # entry on leg's OWN calendar: first leg-session >= nxt
            lc = CAL[l]
            lo, hi = 0, len(lc)
            while lo < hi:
                mid = (lo + hi) // 2
                if lc[mid] < nxt: lo = mid + 1
                else: hi = mid
            if lo >= len(lc):
                unexec += 1; continue
            ed = lc[lo]
            exd = lc[lo + 1] if lo + 1 < len(lc) else None
            if exd is None:
                unexec += 1; continue
            if is_friday_close(bar_instant(ed)):
                weekend_drops += 1; continue
            span_ref = False
            for b in FOLD_BOUNDARIES[1:3]:
                bb = parse_iso(b)
                if bar_instant(ed) < bb < bar_instant(exd):
                    span_ref = True
            if span_ref:
                refused_span.append(str(ed)); continue
            open_pos[l] = (bar_instant(ed), bar_instant(exd))
            trades_per_leg[l] += 1
            all_entry_insts.append(bar_instant(ed).isoformat())
    total_trades = sum(trades_per_leg.values())
    # control: hash-parity flip on triggered (decision_ts, pair); decision stamp = trigger bar
    flips = 0; legs_triggered = 0
    for d in trig_days:
        i = idx_of(EURUSD, d)
        for l in legs:
            ds = f"{bar_instant(d).isoformat()}|{l[:3]}/{l[3:]}|FXFV5-A6-P2-CTRL"
            h = int(hashlib.sha256(ds.encode()).hexdigest(), 16)
            legs_triggered += 1
            if h % 2 == 0: flips += 1
    # neighbour: 2-day cumulative trigger
    trig2 = 0
    for i in range(N + 2, len(edates)):
        d = edates[i]
        if d > S0_END_DAY: break
        r2 = math.log(ecloses[d] / ecloses[edates[i - 2]])
        window = [math.log(ecloses[edates[i - 1 - k]] / ecloses[edates[i - 2 - k]]) for k in range(N)]
        mu = sum(window) / N; var = sum((x - mu) ** 2 for x in window) / (N - 1)
        sd = math.sqrt(var)
        if sd > 0 and abs(r2 / sd) >= 2.0:
            trig2 += 1
    res = {"anchor": {
                "evaluations_note": "every post-warmup NY-day is an evaluation for each of 6 legs",
                "evaluation_days_post_warmup_in_S0": sum(1 for d in edates if d > edates[N + 1] and d <= S0_END_DAY),
                "trigger_days_absz_ge_2": len(trig_days),
                "trigger_day_list_first15": [str(x) for x in trig_days[:15]],
                "leg_trades_total": total_trades,
                "leg_trades_per_pair": dict(trades_per_leg),
                "round_trips": total_trades,
                "fills": 2 * total_trades,
                "governor_blocks_leg_still_in_position": gov_blocks,
                "weekend_gate_dropped": weekend_drops,
                "fold_force_flat_refused_spans": len(refused_span),
                "unexecutable": unexec,
                "folds": split_warmup(all_entry_insts)},
            "control_sign_shuffled": {
                "triggered_leg_entries_scored_for_flip": legs_triggered,
                "flipped": flips,
                "flip_pct": round(100.0 * flips / max(1, legs_triggered), 1),
                "direction_identity_pct": round(100.0 * (legs_triggered - flips) / max(1, legs_triggered), 1),
                "trigger_day_identity_with_anchor_pct": 100.0},
            "neighbour_2day_trigger_days": trig2}
    return res


# ============================================================ AU gaps + warmup exposure
def au_and_warmup():
    # AU quarterly slots in S0
    q = []
    y, qq = 2018, 2
    while (y, qq) <= (2025, 3):
        q.append((y, qq)); qq += 1
        if qq == 5: y += 1; qq = 1
    have = set()
    for c in by_eco["AU"]:
        d = parse_iso(c["decision_date"])
        have.add((d.year, (d.month - 1) // 3 + 1))
    missing = [f"{a}Q{b}" for (a, b) in q if (a, b) not in have]
    months_s0 = (2025 - 2018) * 12 + (7 - 4) + 1
    # pre-data clocks (before first bar of the pair)
    pre = {}
    for e in PAIR_OF:
        pair = PAIR_OF[e]
        first = CAL[pair][0]
        pre[e] = sum(1 for c in by_eco[e] if parse_iso(c["decision_date"]).date() < first
                     or (parse_iso(c["decision_date"]).date() - first).days <= 2)
    return {"au_quarters_S0": len(q), "au_quarters_evidenced": len(have),
            "au_quarters_unevidenced": missing,
            "au_months_S0": months_s0, "au_evidenced_months": 23,
            "clocks_before_pair_data_start_approx": pre,
            "pair_data_first_dates": {PAIR_OF[e]: str(CAL[PAIR_OF[e]][0]) for e in PAIR_OF}}


# ============================================================ cost arithmetic (counts only)
def cost_block(name, round_trips, fills_per_rt=2):
    per_side = {t: NOTIONAL * BPS * t for t in TIERS}  # 1.5 bps decimal x notional x tier
    per_rt = {t: 2 * per_side[t] for t in TIERS}
    return {"name": name, "round_trips": round_trips, "fills": round_trips * fills_per_rt,
            "rt_cost_usd_by_tier": {str(t): round(per_rt[t], 4) for t in TIERS},
            "rt_cost_bps_by_tier": {"1.0": 3.0, "1.5": 4.5, "2.0": 6.0},
            "aggregate_cost_usd_tier2": round(round_trips * 6.0, 2),
            "break_even_note": "per-trade gross move must exceed 6.0 bps RT at tier 2.0; 1-session FX daily sigma scale is tens of bps (documented scale, not computed here), so the ladder is not arithmetically binding; edge thinness is the declared risk"}


def main():
    out = {"basis": RESULTS["basis"]}
    a1 = a4p1()
    a2 = a4p2()
    b1 = a6p1()
    b2 = a6p2()
    out["A4_P1"] = a1
    out["A4_P2"] = a2
    out["A6_P1"] = b1
    out["A6_P2"] = b2
    out["AU_and_warmup_exposure"] = au_and_warmup()
    out["cost_blocks"] = [
        cost_block("A4-P1 anchor H5", a1["anchor"]["trades_H5_executable"]),
        cost_block("A4-P1 control placebo (per-print naive)", a1["control"]["per_print_naive_anchors"]),
        cost_block("A4-P2 anchor Q15", a2["anchor"]["trades_Q15_executable"]),
        cost_block("A4-P2 control pseudo", a2["control_pseudo_sequence"]["control_trades"]),
        cost_block("A6-P1 anchor", b1["anchor"]["decisions_trades"]),
        cost_block("A6-P1 control sham", b1["control_sham"]["valid_sham_decisions"]),
        cost_block("A6-P2 anchor 6-leg", b2["anchor"]["leg_trades_total"]),
    ]
    json.dump(out, open(OUT, "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
