#!/usr/bin/env python
"""DTP-CX-SOLUSDT-C1 skeptic court (lane SKP) — I002 feasibility falsifier census.

ONE-SHOT PINNED REPRESENTATION (committed before any run; no re-derivation):
  - theta grid bps: {10, 15, 20, 25, 30, 40, 50} (dispatch-mandated).
  - BTC 1m event: |close/open - 1| >= theta/1e4 on completed bars.
  - One-shot (non-overlap), PER THETA independently: scanning ascending, an
    event at bar m consumes bar m+1; next candidate m >= last_consumed+1.
    Mirrors I002 §1 "no stacking" with a 1-bar horizon. Raw (overlap-allowed)
    qualifying-bar counts also recorded, semantics declared.
  - BTC 5m slot bar: open = open of first existing 1m bar in the 300000 ms slot,
    close = close of last existing 1m bar in the slot; event + one-shot on
    slots, per theta (event slot k consumes slot k+1). Counts only.
  - Lag feasibility (conditional event-magnitude census — lawful falsifier per
    PWS precedent; NOT PnL; no strategy code is written):
      same_min_bps = sign(r_btc) * (sol_close(m)/sol_close(m-1) - 1) * 1e4
                     (overlaps the BTC signal bar — informational only;
                     requires SOL bars m and m-1 present)
      next_cc_bps  = sign(r_btc) * (sol_close(m+1)/sol_close(m) - 1) * 1e4
                     (upper bound: includes the close(m)->open(m+1) gap;
                     requires SOL bars m and m+1 present)
      next_oc_bps  = sign(r_btc) * (sol_close(m+1)/sol_open(m+1) - 1) * 1e4
                     (EXECUTABLE capture proxy: entry at first tradable quote
                     after BTC close ~= SOL open(m+1); exit close(m+1))
  - Ceiling x power grid (P-29 one-line kill): per theta, veto (K-COST) if
    net_bps_per_RT <= 0 at ANY multiplier (template strict rule) using
      primary RT ladder = out-window DECLARED (12.0 / 18.0 / 24.0 bps;
      FILL_QUALITY_CLASS_declared — binding for a full-span dev window), and
      sensitivity ladder = in-window MEASURED (11.92 / 17.88 / 23.84);
    power floor: oneshot event count >= 100 (master §6.5 crypto intraday),
    reported full-span and inside the 6 bookTicker measured months.
  - Representation rho (K-ANC), measured on the representation's own decision
    grid = BTC 1m bar clock AFTER warmup (200-bar SMA warmup), one-shot,
    committed, reproducible:
      d(m)  = sign(r_btc(m)) * 1{oneshot event at theta} at event minutes,
              else 0   (I002 decision/entry-state series)
      g1(m) = sign(close(m) - SMA200(close))  (EOS1-E1-style BTC own-price
              SMA200 state gate; SMA over last 200 available 1m closes)
      g2(m) = sign(sum of last 30 one-minute BTC returns)  (BTC momentum
              sign-run gate, k=30 pinned; PWS-I001 dead-class representative)
      rho_full  = Pearson(d, g) over all post-warmup grid minutes
      rho_event = Pearson(d, g) restricted to minutes where d != 0
      rho_bt_*  = same, restricted to the 6 bookTicker measured months
      VETO bar: |rho| > 0.20; skeptic uses stricter max(|rho_full|,|rho_event|).
Streaming: month-by-month over staged zips; never loads the full corpus.
"""
import csv, io, json, math, os, zipfile
from collections import deque

VROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
         "integration/research/control/DTP-CX-SOLUSDT-C1/data_local/vision")
BTCDIR = os.path.join(VROOT, "klines_um_BTCUSDT_1m")
SOLDIR = os.path.join(VROOT, "klines_um_SOLUSDT_1m")
OUT = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
       "integration/research/control/DTP-CX-SOLUSDT-C1/council/skeptic")

THETAS_BPS = [10, 15, 20, 25, 30, 40, 50]
BT_MONTHS = {"2023-05", "2023-07", "2023-09", "2023-11", "2024-01", "2024-03"}
RT_DECLARED = {1.0: 12.0, 1.5: 18.0, 2.0: 24.0}
RT_MEASURED = {1.0: 11.92, 1.5: 17.88, 2.0: 23.84}
K_FLOOR = 100
SMA_WINDOW = 200
MOM_WINDOW = 30
RHO_BAR = 0.20


def months():
    out = []
    for y in range(2020, 2027):
        for m in range(1, 13):
            tag = f"{y}-{m:02d}"
            if "2020-09" <= tag <= "2026-08":
                out.append(tag)
    return out


def read_klines(path):
    """Stream one monthly zip -> dict open_time_ms -> (open, close); skips header row."""
    d = {}
    with zipfile.ZipFile(path) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
            for row in csv.reader(text):
                if not row or row[0] == "open_time":
                    continue
                try:
                    t = int(row[0])
                    if t >= 10**14:  # us guard (L-TRACKB1-1)
                        t //= 1000
                    d[t] = (float(row[1]), float(row[4]))
                except (ValueError, IndexError):
                    continue
    return d


def pct(arr):
    if not arr:
        return {"p10": None, "p25": None, "median": None, "p75": None, "p90": None}
    s = sorted(arr)
    n = len(s)

    def q(p):
        idx = p * (n - 1)
        lo = int(math.floor(idx))
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return s[lo] * (1 - frac) + s[hi] * frac

    return {"p10": q(0.10), "p25": q(0.25), "median": q(0.50), "p75": q(0.75), "p90": q(0.90)}


def pearson(n, sx, sy, sxy, sx2, sy2):
    if n < 2:
        return None
    cov = sxy - sx * sy / n
    vx = sx2 - sx * sx / n
    vy = sy2 - sy * sy / n
    if vx <= 0 or vy <= 0:
        return None
    return cov / math.sqrt(vx * vy)


class Acc:
    __slots__ = ("n", "sx", "sy", "sxy", "sx2", "sy2")

    def __init__(self):
        self.n = 0; self.sx = 0.0; self.sy = 0.0; self.sxy = 0.0; self.sx2 = 0.0; self.sy2 = 0.0

    def add(self, x, y):
        self.n += 1; self.sx += x; self.sy += y
        self.sxy += x * y; self.sx2 += x * x; self.sy2 += y * y

    def rho(self):
        return pearson(self.n, self.sx, self.sy, self.sxy, self.sx2, self.sy2)


def main():
    res = {
        "schema": "dtp/skp_court_machine_i002_census@1",
        "cycle_id": "DTP-CX-SOLUSDT-C1",
        "lane": "skp (economic skeptic)",
        "census_class": "OUTCOME-BLIND FEASIBILITY FALSIFIER (conditional event-magnitude census; PWS precedent). NOT PnL. No strategy code written.",
        "theta_grid_bps": THETAS_BPS,
        "pins": {
            "event_def": "|close/open-1| >= theta on completed 1m BTC bar",
            "oneshot": "per-theta: event at bar m consumes m+1; next candidate >= last_consumed+1 (I002 §1 no-stacking, 1-bar horizon)",
            "raw_def": "all qualifying bars, overlap allowed (disclosed, not binding)",
            "slot5m": "300000 ms slot bar = first-open -> last-close of existing 1m bars; one-shot on slots, per theta",
            "lag_census": "close-to-close 1m klines both legs + executable open(m+1)->close(m+1) capture proxy; gap/missing evaluations excluded and counted",
            "rt_primary": "out-window DECLARED ladder 12.0/18.0/24.0 bps (FILL_QUALITY_CLASS_declared, binding full-span); in-window MEASURED 11.92/17.88/23.84 sensitivity",
            "power_floor": ">=100 closed RT (master §6.5 crypto intraday)",
            "rho_representation": "d = sign(r_btc)*1{oneshot event} else 0 on BTC 1m clock post-200-bar warmup; g1 = sign(close - SMA200(close,200)); g2 = sign(sum last 30 1m returns); Pearson full grid + event subset + bookTicker-month subsets; VETO if max(|rho_full|,|rho_event|) > 0.20",
            "immutability": "computed once from sha-pinned bytes (see staging manifest); never re-derived after any outcome",
        },
        "staging": {},
        "btc_corpus_census": {"per_month": {}},
        "events_1m": {},
        "events_5m": {},
        "lag_census": {},
        "grid": {},
        "rho": {},
    }

    man = json.load(open(os.path.join(BTCDIR, "MANIFEST_sha256.json")))
    res["staging"] = {
        "dataset": "klines_um_BTCUSDT_1m",
        "n_files_staged": man["n_files_staged"],
        "n_files_expected": man["n_files_expected"],
        "checksum_match": man["checksum_match"],
        "bytes_total": man["bytes_total"],
        "free_before_gib": round(man["free_before_bytes"] / 1024**3, 2),
        "free_after_gib": round(man["free_after_bytes"] / 1024**3, 2),
        "manifest": "research/control/DTP-CX-SOLUSDT-C1/data_local/vision/klines_um_BTCUSDT_1m/MANIFEST_sha256.json",
    }

    ml = months()
    lastc_1m = {t: -10**18 for t in THETAS_BPS}
    lastc_5m = {t: -10**18 for t in THETAS_BPS}
    lag = {t: {"evaluable": 0, "same_min": [], "next_cc": [], "next_oc": [],
               "excluded": 0, "bt_evaluable": 0} for t in THETAS_BPS}
    cnt = {t: {"raw": 0, "oneshot": 0, "raw5": 0, "oneshot5": 0,
               "per_month_raw": {}, "per_month_oneshot": {},
               "per_month_raw5": {}, "per_month_oneshot5": {}} for t in THETAS_BPS}
    rho = {t: {"g1_full": Acc(), "g1_event": Acc(), "g2_full": Acc(), "g2_event": Acc(),
               "g1_bt_full": Acc(), "g1_bt_event": Acc()} for t in THETAS_BPS}
    sma_q = deque(maxlen=SMA_WINDOW)
    mom_q = deque(maxlen=MOM_WINDOW)
    grid_bars = 0
    btc_rows_total = 0
    btc_first = None
    btc_last = None
    sol_missing_months = []

    for tag in ml:
        bpath = os.path.join(BTCDIR, f"BTCUSDT-1m-{tag}.zip")
        spath = os.path.join(SOLDIR, f"SOLUSDT-1m-{tag}.zip")
        btc = read_klines(bpath)
        sol = read_klines(spath) if os.path.exists(spath) else {}
        if not sol:
            sol_missing_months.append(tag)
        if btc_first is None and btc:
            btc_first = min(btc)
        if btc:
            btc_last = max(btc)
        btc_rows_total += len(btc)
        res["btc_corpus_census"]["per_month"][tag] = {
            "btc_rows": len(btc), "sol_rows": len(sol),
            "btc_first": min(btc) if btc else None, "btc_last": max(btc) if btc else None,
        }
        bts = sorted(btc)
        in_bt = tag in BT_MONTHS
        month_1m = {t: [0, 0, 0] for t in THETAS_BPS}  # raw, oneshot, evaluable
        month_5m = {t: [0, 0] for t in THETAS_BPS}
        slots = {}
        for m in bts:
            o, c = btc[m]
            r = c / o - 1.0
            ar = abs(r)
            sg = 1.0 if r >= 0 else -1.0
            # 5m slot aggregation (order-safe: first open, last close)
            slot = m - (m % 300000)
            if slot not in slots:
                slots[slot] = [o, c]
            else:
                slots[slot][1] = c
            # gates on the BTC decision clock
            sma_q.append(c)
            mom_q.append(r)
            g1 = None
            g2 = None
            if len(sma_q) == SMA_WINDOW:
                g1 = 1.0 if c - (sum(sma_q) / SMA_WINDOW) >= 0 else -1.0
            if len(mom_q) == MOM_WINDOW:
                g2 = 1.0 if sum(mom_q) >= 0 else -1.0
            # lag inputs
            sol_here = sol.get(m)
            sol_prev = sol.get(m - 60000)
            sol_next = sol.get(m + 60000)
            # per-theta event logic
            for t in THETAS_BPS:
                if ar >= t / 1e4:
                    month_1m[t][0] += 1  # raw (overlap allowed)
                    if m > lastc_1m[t]:
                        month_1m[t][1] += 1  # oneshot
                        lastc_1m[t] = m + 60000  # next 1m bar timestamp
                        # rho d and gates (post-warmup grid)
                        if g1 is not None and g2 is not None:
                            ra = rho[t]
                            ra["g1_event"].add(sg, g1)
                            ra["g2_event"].add(sg, g2)
                            if in_bt:
                                ra["g1_bt_event"].add(sg, g1)
                        # lag census
                        if sol_here is not None and sol_next is not None:
                            so, sc = sol_here
                            so1, sc1 = sol_next
                            nxt_cc = sg * (sc1 / sc - 1.0) * 1e4
                            nxt_oc = sg * (sc1 / so1 - 1.0) * 1e4
                            lag[t]["next_cc"].append(nxt_cc)
                            lag[t]["next_oc"].append(nxt_oc)
                            lag[t]["evaluable"] += 1
                            month_1m[t][2] += 1
                            if in_bt:
                                lag[t]["bt_evaluable"] += 1
                            if sol_prev is not None:
                                same_min = sg * (sc / sol_prev[1] - 1.0) * 1e4
                                lag[t]["same_min"].append(same_min)
                        else:
                            lag[t]["excluded"] += 1
            # rho full-grid: one contribution per (post-warmup bar, theta).
            # After the event loop above, lastc_1m[t] == m+60000 iff bar m was
            # an oneshot event at theta t (exact recompute of d).
            if g1 is not None and g2 is not None:
                grid_bars += 1
                for t in THETAS_BPS:
                    d = sg if (ar >= t / 1e4 and lastc_1m[t] == m + 60000) else 0.0
                    ra = rho[t]
                    ra["g1_full"].add(d, g1)
                    ra["g2_full"].add(d, g2)
                    if in_bt:
                        ra["g1_bt_full"].add(d, g1)
        # 5m slot events, per theta, chronological
        for slot in sorted(slots):
            so_, sc_ = slots[slot]
            a5 = abs(sc_ / so_ - 1.0)
            for t in THETAS_BPS:
                if a5 >= t / 1e4:
                    month_5m[t][0] += 1
                    if slot > lastc_5m[t]:
                        month_5m[t][1] += 1
                        lastc_5m[t] = slot + 300000
        for t in THETAS_BPS:
            cnt[t]["raw"] += month_1m[t][0]
            cnt[t]["oneshot"] += month_1m[t][1]
            cnt[t]["per_month_raw"][tag] = month_1m[t][0]
            cnt[t]["per_month_oneshot"][tag] = month_1m[t][1]
            cnt[t]["raw5"] += month_5m[t][0]
            cnt[t]["oneshot5"] += month_5m[t][1]
            cnt[t]["per_month_raw5"][tag] = month_5m[t][0]
            cnt[t]["per_month_oneshot5"][tag] = month_5m[t][1]
        print(f"{tag}: btc_rows={len(btc)} done", flush=True)

    res["btc_corpus_census"]["rows_total_btc"] = btc_rows_total
    res["btc_corpus_census"]["first_open_ms"] = btc_first
    res["btc_corpus_census"]["last_open_ms"] = btc_last
    res["btc_corpus_census"]["grid_bars_post_warmup_rho"] = grid_bars
    res["btc_corpus_census"]["sol_missing_months"] = sol_missing_months

    for t in THETAS_BPS:
        e = lag[t]
        dist = {
            "same_min_bps": {**pct(e["same_min"]), "mean": (sum(e["same_min"]) / len(e["same_min"])) if e["same_min"] else None, "n": len(e["same_min"])},
            "next_cc_bps": {**pct(e["next_cc"]), "mean": (sum(e["next_cc"]) / len(e["next_cc"])) if e["next_cc"] else None, "n": len(e["next_cc"])},
            "next_oc_bps": {**pct(e["next_oc"]), "mean": (sum(e["next_oc"]) / len(e["next_oc"])) if e["next_oc"] else None, "n": len(e["next_oc"])},
        }
        res["lag_census"][str(t)] = {
            "oneshot_events": cnt[t]["oneshot"],
            "evaluable": e["evaluable"],
            "excluded_gap_or_missing_sol": e["excluded"],
            "distributions": dist,
            "oneshot_evaluable_in_bookTicker_window": e["bt_evaluable"],
        }
        cap_exec = dist["next_oc_bps"]["mean"]
        cap_cc = dist["next_cc_bps"]["mean"]
        rows = []
        for basis_name, ladder in (("declared_out_window_PRIMARY", RT_DECLARED),
                                   ("in_window_measured_sensitivity", RT_MEASURED)):
            cells = []
            for mult in (1.0, 1.5, 2.0):
                rt = ladder[mult]
                net_exec = cap_exec - rt
                cells.append({"mult": mult, "rt_bps": rt, "capture_basis": "next_oc_executable",
                              "net_bps_per_RT": round(net_exec, 4),
                              "net_upperbound_cc_bps": round(cap_cc - rt, 4),
                              "veto": net_exec <= 0})
            power = {
                "oneshot_events_full_span": cnt[t]["oneshot"],
                "oneshot_evaluable_full_span": e["evaluable"],
                "oneshot_evaluable_bookTicker_window": e["bt_evaluable"],
                "K_floor": K_FLOOR,
                "power_ok_full_span": cnt[t]["oneshot"] >= K_FLOOR,
                "power_ok_bookTicker_window": e["bt_evaluable"] >= K_FLOOR,
            }
            veto_any = any(c["veto"] for c in cells)
            rows.append({"basis": basis_name, "cells": cells,
                         "veto_K_COST_strict_any_mult": veto_any,
                         "power": power,
                         "jointly_empty_full_span": veto_any or not power["power_ok_full_span"],
                         "jointly_empty_bookTicker_window": veto_any or not power["power_ok_bookTicker_window"]})
        res["grid"][str(t)] = {
            "theta_bps": t,
            "capture_executable_mean_bps": round(cap_exec, 4),
            "capture_close_to_close_mean_bps": round(cap_cc, 4),
            "rows": rows,
        }
        res["events_1m"][str(t)] = {
            "raw_total": cnt[t]["raw"], "oneshot_total": cnt[t]["oneshot"],
            "per_month_raw": cnt[t]["per_month_raw"], "per_month_oneshot": cnt[t]["per_month_oneshot"],
        }
        res["events_5m"][str(t)] = {
            "raw_total": cnt[t]["raw5"], "oneshot_total": cnt[t]["oneshot5"],
            "per_month_raw": cnt[t]["per_month_raw5"], "per_month_oneshot": cnt[t]["per_month_oneshot5"],
        }
        ra = rho[t]
        out = {}
        for key in ("g1_full", "g1_event", "g2_full", "g2_event", "g1_bt_full", "g1_bt_event"):
            out[key] = {"rho": ra[key].rho(), "n": ra[key].n}
        out["max_abs_rho_g1"] = max(abs(out["g1_full"]["rho"] or 0), abs(out["g1_event"]["rho"] or 0))
        out["max_abs_rho_g2"] = max(abs(out["g2_full"]["rho"] or 0), abs(out["g2_event"]["rho"] or 0))
        out["K_ANC_VETO_any_proxy"] = (out["max_abs_rho_g1"] > RHO_BAR or out["max_abs_rho_g2"] > RHO_BAR)
        res["rho"][str(t)] = out

    with open(os.path.join(OUT, "court_machine@1.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("WROTE court_machine@1.json", flush=True)
    for t in THETAS_BPS:
        g = res["grid"][str(t)]
        r_ = res["rho"][str(t)]
        lc = res["lag_census"][str(t)]
        print(f"theta={t}: oneshot={lc['oneshot_events']} bt_win={lc['oneshot_evaluable_in_bookTicker_window']} "
              f"cap_exec={g['capture_executable_mean_bps']} cap_cc={g['capture_close_to_close_mean_bps']} "
              f"veto_declared={g['rows'][0]['veto_K_COST_strict_any_mult']} power_full={g['rows'][0]['power']['power_ok_full_span']} "
              f"rho_g1={r_['max_abs_rho_g1']:.4f} rho_g2={r_['max_abs_rho_g2']:.4f} KANC={r_['K_ANC_VETO_any_proxy']}", flush=True)


if __name__ == "__main__":
    main()
