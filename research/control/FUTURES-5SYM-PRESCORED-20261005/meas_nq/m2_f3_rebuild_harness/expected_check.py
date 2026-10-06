#!/usr/bin/env python
"""Independent expected-value calculator for the synthetic F3 fixture.

PURE PYTHON (math / statistics only — no pandas, no numpy, no import of
rebuild_harness): re-derives the EXPECTED aggregate outputs by replaying the
generator law with its own independent code, then implementing the aggregate
formulas from their definitions.

Comparison law (documented in HARNESS_SPEC.md section 5):
  - integer / count / boolean / string fields: EXACT equality;
  - float aggregates: relative tolerance 1e-10 (the same real number computed
    through different summation orders / log-corr implementations may differ
    by a few ULP; anything above 1e-10 relative is a mismatch);
  - the closed-form crash depth is compared on the LOG axis (the harness and
    the committed k6gate recipe both report -100 * dd_log) at a coarse 1e-2
    relative tolerance (ideal unrounded law vs closes rounded to 2 decimals
    over 30 crash steps).
"""
import json
import math
import random
from datetime import date, timedelta

# ---- generator constants (mirror rebuild_harness.gen_synthetic law) ----
N_SESSIONS = 1044
START = date(2017, 1, 2)
ROLL_IDX = (300, 640, 900)
HOLE_START, HOLE_LEN = 500, 10
THIN_IDX = (760, 761)
RAMP_START, RAMP_LEN, RAMP_RET = 620, 40, 0.02
CRASH_START, CRASH_LEN, CRASH_RET = 660, 30, -0.02
RECOVERY_START, RECOVERY_LEN, RECOVERY_RET = 690, 40, 0.015
ERA_B_START = 700
BASE = 6000.0
WARMUP = 252
FOLDS = [("F1", "2010-06-06", "2012-12-31"),
         ("F2", "2013-01-01", "2017-12-31"),
         ("F3", "2018-01-01", "2021-12-31"),
         ("F4", "2022-01-01", "2026-09-30")]
QUIRK_INDEX = ERA_B_START + 3


def business_days(n):
    out, cur = [], START
    while len(out) < n:
        if cur.weekday() < 5:
            out.append(cur)
        cur += timedelta(days=1)
    return out


def replay():
    """Independent replay of the deterministic close path (same seed & law)."""
    rng = random.Random(20261005)
    days = business_days(N_SESSIONS)
    closes, vols, covs, close = [], [], [], BASE
    for i in range(N_SESSIONS):
        era_b = i >= ERA_B_START
        vol = 0.010 if era_b else 0.005
        if HOLE_START <= i < HOLE_START + HOLE_LEN:
            closes.append(None)
            vols.append(0)
            covs.append(0.0)
            continue
        if RAMP_START <= i < RAMP_START + RAMP_LEN:
            r = RAMP_RET
        elif CRASH_START <= i < CRASH_START + CRASH_LEN:
            r = CRASH_RET
        elif RECOVERY_START <= i < RECOVERY_START + RECOVERY_LEN:
            r = RECOVERY_RET
        else:
            u = rng.random()
            r = vol * (2.0 * u - 1.0)
        close = close * (1.0 + r)
        closes.append(round(close, 2))
        covs.append(0.10 if i in THIN_IDX else 0.95)
        vols.append(int(300000 * (3.0 if era_b else 1.0) * (0.5 + rng.random())))
    return days, closes, vols, covs


def rets_of(closes):
    out = [None]
    for i in range(1, len(closes)):
        a, b = closes[i - 1], closes[i]
        out.append(None if (a is None or b is None) else math.log(b / a))
    return out


def sample_std(xs):
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def corr(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    den = math.sqrt(sxx * syy)
    return sxy / den if den > 0 else None


def acf1_abs_median(rs, win=252):
    vals = []
    for i in range(win, len(rs)):
        w = rs[i - win + 1:i + 1]
        if any(x is None for x in w):
            continue
        aa = [abs(x) for x in w]
        c = corr(aa[:-1], aa[1:])
        if c is not None:
            vals.append(c)
    return median(vals)


def dd_episodes(log_closes):
    """Independent drawdown-episode extraction (same definition as the
    harness and the committed k6gate recipe: cum = log_close - log_close[0];
    dd = cum - running_max(cum); episodes where dd < -0.10; depth_pct is the
    LOG-space depth x100 at the trough = -100 * dd[trough])."""
    c0 = log_closes[0]
    cum = [None if x is None else x - c0 for x in log_closes]
    peak, dd = [], None
    cur = cum[0]
    for v in cum:
        if v is not None and v > cur:
            cur = v
        peak.append(cur)
    dd = [None if v is None else v - p for v, p in zip(cum, peak)]
    eps, in_dd, start, trough = [], False, None, None
    for i, v in enumerate(dd):
        if v is None:
            continue                     # NaN dd: no comparison fires
        if not in_dd and v < -0.10:
            in_dd, start, trough = True, i, i
        elif in_dd:
            if v < dd[trough]:
                trough = i
            if v >= -1e-9:
                eps.append((start, trough, i))
                in_dd = False
    if in_dd:
        eps.append((start, trough, None))
    return eps, dd


def compute_expected(fdir):
    days, closes, vols, covs = replay()
    rs = rets_of(closes)
    log_closes = [None if c is None else math.log(c) for c in closes]

    depleted = {i for i in range(N_SESSIONS)
                if closes[i] is None or covs[i] < 0.25}
    n_nan_rets = sum(1 for r in rs if r is None)
    hole_dates = [str(days[i]) for i in range(HOLE_START, HOLE_START + HOLE_LEN)]
    roll_dates = [str(days[i]) for i in ROLL_IDX]
    crash_end = str(days[CRASH_START + CRASH_LEN - 1])

    yearly = {}
    for i in range(N_SESSIONS):
        y = days[i].year
        yearly.setdefault(y, {"n_sessions": 0, "rets": [], "vols": []})
        yearly[y]["n_sessions"] += 1
        if rs[i] is not None:
            yearly[y]["rets"].append(rs[i])
        yearly[y]["vols"].append(vols[i])   # hole sessions ship volume 0 too
    yearly_expected = {y: {"n_sessions": v["n_sessions"],
                           "n_nonnan_rets": len(v["rets"]),
                           "vol_ann_pct": (100 * sample_std(v["rets"]) * math.sqrt(252)
                                           if len(v["rets"]) > 2 else None),
                           "avg_daily_vol_contracts": (sum(v["vols"]) / len(v["vols"]))}
                       for y, v in yearly.items()}

    fold_counts = {}
    for name, lo, hi in FOLDS:
        n = sum(1 for i in range(N_SESSIONS) if lo <= str(days[i]) <= hi)
        fold_counts[name] = {"n_sessions": n,
                             "n_scoring_sessions_if_scored": max(0, n - WARMUP)}

    eps, dd = dd_episodes(log_closes)
    crash_trough_idx = CRASH_START + CRASH_LEN - 1
    crash_eps = None
    for s, t, e in eps:
        if t == crash_trough_idx:
            crash_eps = (s, t, e)
    ideal_log_depth = 100 * (-CRASH_LEN * math.log(1 + CRASH_RET))

    quirk_expected_date = str(days[QUIRK_INDEX] - timedelta(days=days[QUIRK_INDEX].weekday() + 1))

    return {"n_sessions": N_SESSIONS,
            "first": str(days[0]), "last": str(days[-1]),
            "n_depleted": len(depleted),
            "n_nan_rets": n_nan_rets,
            "clean_sessions_cov_ge_0.6": N_SESSIONS - len(depleted),
            "n_rolls": 3, "roll_dates": roll_dates,
            "yearly": yearly_expected,
            "folds": fold_counts,
            "acf1_abs_ret_252d_median": acf1_abs_median(rs),
            "crash_episode": (None if crash_eps is None else
                              {"start": str(days[crash_eps[0]]),
                               "trough": str(days[crash_eps[1]]),
                               "depth_pct": -100 * dd[crash_eps[1]]}),
            "closed_form": {"ideal_crash_log_depth_pct_unrounded": ideal_log_depth,
                            "crash_end_date": str(days[crash_trough_idx]),
                            "quirk_session_date": quirk_expected_date,
                            "quirk_index": QUIRK_INDEX}}


FLOAT_REL_TOL = 1e-10
COARSE_REL_TOL = 1e-2


def close_f(a, b, tol=FLOAT_REL_TOL):
    if a is None or b is None:
        return a is None and b is None
    if a == b:
        return True
    return abs(a - b) <= tol * max(abs(a), abs(b), 1e-300)


def compare(h, expected):
    checks, mismatches = [], []

    def chk(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
        if not ok:
            mismatches.append(f"{name}: {detail}")

    exp = {"panel.n_sessions": expected["n_sessions"],
           "panel.first": expected["first"],
           "panel.last": expected["last"],
           "panel.n_rolls": expected["n_rolls"],
           "panel.depleted_sessions": expected["n_depleted"],
           "panel.clean_sessions_cov_ge_0.6": expected["clean_sessions_cov_ge_0.6"],
           "a2.clean_sessions": expected["clean_sessions_cov_ge_0.6"],
           "a2.excluded_low_coverage": expected["n_depleted"],
           "crosscheck.max_abs_ret_diff": 0.0,
           "crosscheck.n_compared": expected["n_sessions"] - expected["n_nan_rets"]}
    got = {"panel.n_sessions": h["panel"]["n_sessions"],
           "panel.first": h["panel"]["first"],
           "panel.last": h["panel"]["last"],
           "panel.n_rolls": h["panel"]["n_rolls"],
           "panel.depleted_sessions": h["panel"]["depleted_sessions"],
           "panel.clean_sessions_cov_ge_0.6": h["panel"]["clean_sessions_cov_ge_0.6"],
           "a2.clean_sessions": h["a2"]["clean_sessions"],
           "a2.excluded_low_coverage": h["a2"]["excluded_low_coverage"],
           "crosscheck.max_abs_ret_diff": (h["crosscheck_provided_ret"] or {})["max_abs_ret_diff"],
           "crosscheck.n_compared": (h["crosscheck_provided_ret"] or {})["n_compared"]}
    for k, v in exp.items():
        g = got[k]
        ok = close_f(g, v) if isinstance(v, float) else g == v
        chk(f"exact[{k}]", ok, f"harness={g} expected={v}")

    chk("roll_dates", h["panel"]["roll_dates"] == expected["roll_dates"],
        f"{h['panel']['roll_dates']} vs {expected['roll_dates']}")
    chk("nan_ret_count(NaN-aware chain law)",
        h["crosscheck_provided_ret"]["n_nan_provided"] == expected["n_nan_rets"],
        f"harness={h['crosscheck_provided_ret']['n_nan_provided']} "
        f"expected={expected['n_nan_rets']} (hole 10 closes => 12 NaN rets incl. first)")
    chk("quirk_label_carried(1 row)",
        h.get("quirk_labeled_sessions") == 1,
        f"harness={h.get('quirk_labeled_sessions')}")

    for row in h["a1"]["yearly"]:
        y = int(row["year"])
        e = expected["yearly"].get(y)
        if e is None:
            continue
        chk(f"yearly[{y}].n_sessions", row["n_sessions"] == e["n_sessions"])
        chk(f"yearly[{y}].vol_ann_pct", close_f(row["vol_ann_pct"], e["vol_ann_pct"]),
            f"harness={row['vol_ann_pct']} expected={e['vol_ann_pct']}")
        chk(f"yearly[{y}].avg_vol", close_f(row["avg_daily_vol_contracts"],
                                            e["avg_daily_vol_contracts"]))

    for row in h["a2"]["fold_segments"]:
        e = expected["folds"].get(row["fold"])
        if e is None:
            continue
        chk(f"fold[{row['fold']}].n_sessions", row["n_sessions"] == e["n_sessions"])
        chk(f"fold[{row['fold']}].scoring",
            row["n_scoring_sessions_if_scored"] == e["n_scoring_sessions_if_scored"])

    eps = h["a1"]["drawdowns_ge10pct"]
    ce = expected["crash_episode"]
    chk("crash_episode_present", ce is not None and len(eps) >= 1,
        f"n_episodes={len(eps)} expected_crash={ce}")
    if ce is not None and eps:
        match = [e for e in eps if e["trough"] == ce["trough"]]
        chk("crash_episode_trough_date", bool(match),
            f"troughs={[e['trough'] for e in eps[:3]]} expected={ce['trough']}")
        if match:
            chk("crash_episode_depth(ULP-level)",
                close_f(match[0]["depth_pct"], ce["depth_pct"]),
                f"harness={match[0]['depth_pct']} expected={ce['depth_pct']}")
            chk("crash_episode_depth(coarse closed-form, log axis)",
                close_f(match[0]["depth_pct"],
                        expected["closed_form"]["ideal_crash_log_depth_pct_unrounded"],
                        COARSE_REL_TOL),
                f"harness={match[0]['depth_pct']} "
                f"ideal={expected['closed_form']['ideal_crash_log_depth_pct_unrounded']}")
            chk("crash_episode_recovers", match[0]["end"] not in (None, "unrecovered"),
                f"end={match[0]['end']}")

    chk("acf1_abs_ret_252d_median",
        close_f(h["a1"]["vol_clustering"]["acf1_abs_ret_252d_median"],
                expected["acf1_abs_ret_252d_median"]),
        f"harness={h['a1']['vol_clustering']['acf1_abs_ret_252d_median']} "
        f"expected={expected['acf1_abs_ret_252d_median']}")

    return {"schema": "meas_nq_selfcheck_results@1",
            "float_rel_tol": FLOAT_REL_TOL, "coarse_rel_tol": COARSE_REL_TOL,
            "n_checks": len(checks), "n_failed": len(mismatches),
            "checks": checks, "mismatches": mismatches,
            "all_match": not mismatches}
