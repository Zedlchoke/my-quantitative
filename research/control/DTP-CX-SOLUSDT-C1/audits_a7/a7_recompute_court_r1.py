#!/usr/bin/env python
"""A7 TERMINAL AUDIT — independent recompute of court R1 (I002 kill) census.

Independently implemented from the pinned definitions in court_machine@1.json
(pins_census): event |close/open-1| >= theta/1e4; oneshot greedy (event at m
consumes m+1); lag arrays sign(r_btc)*SOL-return*1e4 with presence rules.
Own reader, own data structures, own median code. thetas {10, 25}.
NO strategy PnL — feasibility census only (outcome-blind magnitudes).
"""
import csv, io, json, math, os, zipfile
from array import array

W = "/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/integration"
VROOT = W + "/research/control/DTP-CX-SOLUSDT-C1/data_local/vision"
BTCDIR = os.path.join(VROOT, "klines_um_BTCUSDT_1m")
SOLDIR = os.path.join(VROOT, "klines_um_SOLUSDT_1m")
THETAS = [10, 25]
BT_MONTHS = {"2023-05", "2023-07", "2023-09", "2023-11", "2024-01", "2024-03"}


def months():
    out = []
    for y in range(2020, 2027):
        for m in range(1, 13):
            tag = "%d-%02d" % (y, m)
            if "2020-09" <= tag <= "2026-08":
                out.append(tag)
    return out


def read_klines(path):
    """Independent reader: returns two parallel arrays (ts, open, close) then a dict."""
    ts = array("q"); op = array("d"); cl = array("d")
    with zipfile.ZipFile(path) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            rdr = csv.reader(io.TextIOWrapper(fh, "utf-8", newline=""))
            for row in rdr:
                if len(row) < 5:
                    continue
                t = row[0]
                if not t.isdigit():
                    continue  # header / junk
                t = int(t)
                if t >= 10 ** 14:
                    t //= 1000
                ts.append(t); op.append(float(row[1])); cl.append(float(row[4]))
    return dict(zip(ts, zip(op, cl))), ts, op, cl


def med(a):
    """Linear-interpolation median on sorted copy (independent implementation)."""
    n = len(a)
    if n == 0:
        return None
    s = sorted(a)
    idx = 0.5 * (n - 1)
    lo = int(math.floor(idx)); hi = min(lo + 1, n - 1)
    f = idx - lo
    return s[lo] * (1.0 - f) + s[hi] * f


def main():
    res = {"btc_rows_total": 0, "months": {}, "thetas": {}}
    lastc = {t: -10 ** 18 for t in THETAS}
    lag = {t: {"evaluable": 0, "same_min": array("d"), "next_cc": array("d"),
               "excluded": 0, "bt_eval": 0} for t in THETAS}
    cnt = {t: {"raw": 0, "oneshot": 0} for t in THETAS}
    first = None; last = None
    for tag in months():
        bpath = os.path.join(BTCDIR, "BTCUSDT-1m-%s.zip" % tag)
        spath = os.path.join(SOLDIR, "SOLUSDT-1m-%s.zip" % tag)
        btc, _, _, _ = read_klines(bpath)
        sol = {}
        if os.path.exists(spath):
            sol, _, _, _ = read_klines(spath)
        res["months"][tag] = {"btc": len(btc), "sol": len(sol)}
        res["btc_rows_total"] += len(btc)
        if btc:
            if first is None:
                first = min(btc)
            last = max(btc)
        in_bt = tag in BT_MONTHS
        mrow = {t: [0, 0] for t in THETAS}
        for m in sorted(btc):
            o, c = btc[m]
            r = c / o - 1.0
            ar = abs(r)
            sg = 1.0 if r >= 0 else -1.0
            sh = sol.get(m); sp = sol.get(m - 60000); sn = sol.get(m + 60000)
            for t in THETAS:
                if ar >= t / 1e4:
                    mrow[t][0] += 1
                    if m > lastc[t]:
                        mrow[t][1] += 1
                        lastc[t] = m + 60000
                        if sh is not None and sn is not None:
                            _, sc = sh
                            _, sc1 = sn
                            lag[t]["next_cc"].append(sg * (sc1 / sc - 1.0) * 1e4)
                            lag[t]["evaluable"] += 1
                            if in_bt:
                                lag[t]["bt_eval"] += 1
                            if sp is not None:
                                _, scp = sp
                                lag[t]["same_min"].append(sg * (sc / scp - 1.0) * 1e4)
                        else:
                            lag[t]["excluded"] += 1
        for t in THETAS:
            cnt[t]["raw"] += mrow[t][0]
            cnt[t]["oneshot"] += mrow[t][1]
    res["first_open_ms"] = first; res["last_open_ms"] = last
    for t in THETAS:
        e = lag[t]
        res["thetas"][t] = {
            "raw_total": cnt[t]["raw"],
            "oneshot_total": cnt[t]["oneshot"],
            "evaluable": e["evaluable"],
            "excluded": e["excluded"],
            "bt_evaluable": e["bt_eval"],
            "same_min_n": len(e["same_min"]),
            "same_min_median_bps": med(e["same_min"]),
            "next_cc_median_bps": med(e["next_cc"]),
        }
    out = W + "/research/control/DTP-CX-SOLUSDT-C1/audits_a7/a7_court_r1_recompute_machine@1.json"
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "months"}, indent=1))


if __name__ == "__main__":
    main()
