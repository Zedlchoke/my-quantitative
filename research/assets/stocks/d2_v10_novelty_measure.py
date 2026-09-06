"""PLAN_stocks_v10 D2 novelty + control-identifiability measurement (A1).

Feature/RANK ARITHMETIC ONLY — zero PnL (V5/V9 D2 audit discipline).

For each of the six D1 proposals, the ANCHOR exposure is computed exactly as
its exposure_definition states (with one measured convention: group-level
exposures aggregate to the entity level by MEAN over qualifying groups, so
rank correlation against entity-level veto entries is defined), on the frozen
30 quarterly decision dates. Pooled Spearman (midrank ties) vs each of the
NINE veto entries; plus anchor-vs-control and anchor-vs-neighbour rank
correlations for the pre-selection identifiability gates.

Universe: entity-decision pairs where the proposal exposure is defined, on
the bookable pool (ALIVE_EVIDENCED + DEAD_PRICE_CONFIRMED), >= 63 price bars
through the decision session. No band computation, no returns.
"""

from __future__ import annotations

import json
import math
import sys
from bisect import bisect_left
from datetime import date, timedelta
from pathlib import Path

V10 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v10/integration")
V9 = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration")
PRICES = V9 / ".staging_prices_v9/eod"
BENCH = V9 / ".staging_prices_v9/benchmarks"
TIMING = V10 / ".staging_sec_v10/v10_timing_observables.jsonl"
REVISION = V10 / ".staging_sec_v10/v10_revision_observables.jsonl"
PANEL = V9 / ".staging_sec_v9/multivintage_panel.jsonl"
COHORT = V10 / "research/control/stocks_free_v9_run/cohort_v9.json"
CENSUS = V10 / "research/control/stocks_free_v6_run/p0a_coverage_census.json"
OUT = V10 / "research/control/stocks_free_v10_run/audits/d2_v10_novelty_measure.json"

STALE_DAYS = 800
VETO_NAMES = [
    "momentum_63s", "semivariance_share", "vol_level", "wc_stock_intensity",
    "goodwill_bloat", "f1_accrual_flow", "depletion_interaction",
    "cash_level", "sector_exposure_form",
]
# fields pulled from the panel for the accounting veto entries (prefix match)
NEEDED_FIELDS = [
    "us-gaap:AssetsCurrent", "us-gaap:LiabilitiesCurrent",
    "us-gaap:Goodwill", "us-gaap:Assets",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    "us-gaap:RetainedEarningsAccumulatedDeficit",
    "us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet",
    "us-gaap:AccountsPayableCurrent",
]


def dd(s: str) -> date:
    return date.fromisoformat(s)


def midrank(xs):
    items = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(items):
        j = i
        while j + 1 < len(items) and xs[items[j + 1]] == xs[items[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[items[k]] = r
        i = j + 1
    return ranks


def spearman(a, b):
    n = len(a)
    if n < 10:
        return None
    ra, rb = midrank(a), midrank(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    if va == 0 or vb == 0:
        return None
    return cov / (va * vb)


def main() -> int:
    cohort = json.loads(COHORT.read_text())
    bookable = {}
    for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
        for m in cohort["members"][cls]:
            bookable[m["cik"]] = {"sector": m.get("sector", ""), "ticker": m.get("ticker", "")}
    dates = json.loads(CENSUS.read_text())["decision_dates"]
    gates = [dd(d) for d in dates]

    # global trading calendar from the SPY benchmark series
    spy = None
    for p in BENCH.glob("*.json"):
        try:
            arr = json.loads(p.read_text())
        except Exception:
            continue
        if isinstance(arr, list) and len(arr) > 500:
            spy = arr
            break
    sessions = [dd(r["date"]) for r in sorted(spy, key=lambda r: r["date"])]
    sess_idx = {d: i for i, d in enumerate(sessions)}

    # ---------------- price series (raw close, adjusted close, volume) -----
    series = {}
    for p in PRICES.glob("CIK*.json"):
        cik = p.name.split("__")[0]
        if cik not in bookable:
            continue
        try:
            arr = json.loads(p.read_text())
        except Exception:
            continue
        arr = [r for r in arr if r.get("close") is not None]
        if len(arr) < 63:
            continue
        arr.sort(key=lambda r: r["date"])
        series[cik] = {
            "dates": [dd(r["date"]) for r in arr],
            "close": [r["close"] for r in arr],
            "adj": [r.get("adjusted_close") for r in arr],
            "vol": [r.get("volume", 0) for r in arr],
        }

    def last_bar(cik, t, key="close"):
        s = series[cik]
        i = bisect_left(s["dates"], t)
        if i >= len(s["dates"]):
            i = len(s["dates"]) - 1
        if s["dates"][i] >= t:
            i -= 1
        return i, (s[key][i] if i >= 0 else None)

    def has_bars(cik, t, n=63):
        s = series[cik]
        i = bisect_left(s["dates"], t)
        return i >= n

    def adv63(cik, t):
        s = series[cik]
        i, _ = last_bar(cik, t, "close")
        if i < 62:
            return None
        tot = 0.0
        for k in range(i - 62, i + 1):
            tot += s["close"][k] * s["vol"][k]
        return tot / 63.0

    def prior_window(cik, t, n=63):
        s = series[cik]
        i, _ = last_bar(cik, t, "adj")
        if i < n:
            return None
        return s["adj"][i - n + 1:i + 1]

    # ---------------- as-of engine for panel fields (veto entries) ---------
    print("[d2] streaming panel for veto fields...", flush=True)
    fields = {}  # (cik, field) -> sorted [(avail, eff, v)]
    want = set(NEEDED_FIELDS)
    with open(PANEL, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            f = r["f"]
            if f in want and r["e"] in bookable and isinstance(r["v"], (int, float)):
                fields.setdefault((r["e"], f), []).append((r["avail"], r["eff"], r["v"]))

    def asof(cik, f, t, prior_annual=None):
        lst = fields.get((cik, f))
        if not lst:
            return None
        lo = 0
        hi = len(lst)
        while lo < hi:
            mid = (lo + hi) // 2
            if lst[mid][0] < t.isoformat():
                lo = mid + 1
            else:
                hi = mid
        if lo == 0:
            return None
        if prior_annual is None:
            return lst[lo - 1][2]
        # walk back to the latest annual (Dec) eff strictly in prior years
        for k in range(lo - 1, -1, -1):
            av, eff, v = lst[k]
            if eff[5:7] == "12" and int(eff[:4]) < prior_annual[0]:
                return v
        return None

    def latest_annual_year(cik, f, t):
        lst = fields.get((cik, f))
        if not lst:
            return None
        best = None
        for av, eff, v in lst:
            if av < t.isoformat() and eff[5:7] == "12":
                y = int(eff[:4])
                if best is None or y > best:
                    best = y
        return best

    # ---------------- observable layers ------------------------------------
    print("[d2] loading timing layer...", flush=True)
    tim = {}
    with open(TIMING, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e = r["e"]
            if e in bookable:
                tim.setdefault(e, []).append(
                    (r["first_avail"], r["eff"], r["own_z"], r["cohort_z"], r["first_lag_days"]))

    print("[d2] loading revision layer...", flush=True)
    rev = {}
    with open(REVISION, buffering=1 << 20) as fh:
        for line in fh:
            r = json.loads(line)
            e = r["e"]
            if e in bookable:
                rev.setdefault(e, []).append(r)

    # ---------------- per-proposal exposure computation --------------------
    def elig_bars(cik, t):
        return cik in series and has_bars(cik, t)

    def a4_h1_pairs():
        # exposure = -own_z of latest qualifying group; mean over qualifying groups
        out = {}
        for t in gates:
            for e, lst in tim.items():
                vals = []
                for av, eff, oz, cz, lag in lst:
                    delta = (t - dd(av)).days
                    if delta >= 0 and delta <= STALE_DAYS and oz is not None:
                        vals.append(-oz)
                if vals and elig_bars(e, t):
                    out[(e, t)] = sum(vals) / len(vals)
        return out

    def a4_h1_control():
        out = {}
        for t in gates:
            for e, lst in tim.items():
                vals = []
                for av, eff, oz, cz, lag in lst:
                    delta = (t - dd(av)).days
                    if 0 <= delta <= STALE_DAYS:
                        vals.append(-lag)
                if vals and elig_bars(e, t):
                    out[(e, t)] = sum(vals) / len(vals)
        return out

    def a4_h2_pairs(window_sessions=63):
        out = {}
        for t in gates:
            gi = sess_idx[t]
            for e, lst in tim.items():
                best = None
                for av, eff, oz, cz, lag in lst:
                    avd = dd(av)
                    if avd >= t:
                        continue
                    k = sess_idx.get(avd)
                    if k is None:
                        k = bisect_left(sessions, avd)
                    age = gi - (k + 1)
                    if 0 <= age <= window_sessions and oz is not None:
                        if best is None or av > best[0]:
                            best = (av, -oz)
                if best and elig_bars(e, t):
                    out[(e, t)] = best[1]
        return out

    def a5_pairs(value_fn, flat_only=False, down_only=False, up_only=False):
        out = {}
        for t in gates:
            for e, lst in rev.items():
                q = []
                for r in lst:
                    delta = (t - dd(r["last_avail"])).days
                    if delta < 0 or delta > STALE_DAYS:
                        continue
                    d = r["rev_dir"]
                    if flat_only and d != 0:
                        continue
                    if down_only and d != -1:
                        continue
                    if up_only and d != 1:
                        continue
                    q.append(value_fn(r))
                if len(q) >= 4 and elig_bars(e, t):
                    out[(e, t)] = sum(q) / len(q)
        return out

    def max_eff_per_field(rows, t):
        # keep only max-eff group per field among qualifying rows
        best = {}
        for r in rows:
            delta = (t - dd(r["last_avail"])).days
            if delta < 0 or delta > STALE_DAYS:
                continue
            f = r["f"]
            if f not in best or r["eff"] > best[f]["eff"]:
                best[f] = r
        return list(best.values())

    def a5_h1_pairs():
        out = {}
        for t in gates:
            for e, lst in rev.items():
                q = max_eff_per_field(lst, t)
                if len(q) < 4 or not elig_bars(e, t):
                    continue
                down = sum(1 for r in q if r["rev_dir"] == -1)
                out[(e, t)] = down / len(q)
        return out

    def a5_h1_control():
        out = {}
        for t in gates:
            for e, lst in rev.items():
                q = max_eff_per_field(lst, t)
                if len(q) < 4 or not elig_bars(e, t):
                    continue
                up = sum(1 for r in q if r["rev_dir"] == 1)
                out[(e, t)] = up / len(q)
        return out

    def a6_h1_pairs(stale_shift=None):
        out = {}
        for t in gates:
            gi = sess_idx[t]
            # window set W(t)
            w = []
            for e, lst in rev.items():
                for r in lst:
                    avd = dd(r["last_avail"])
                    if avd >= t:
                        continue
                    k = bisect_left(sessions, avd)
                    age = gi - k
                    lo = 504 if stale_shift else 0
                    hi = 252 if stale_shift else 0
                    if stale_shift:
                        if not (lo >= age > hi):
                            continue
                    else:
                        if age > 252:
                            continue
                    m = r["rev_mag"]
                    w.append((e, r["rev_dir"], m))
            if len(w) < 30:
                continue
            mags = [abs(m) for _, _, m in w if m is not None]
            mags.sort()
            p75 = mags[int(0.75 * (len(mags) - 1))] if mags else None
            acc = {}
            for e, d, m in w:
                if d == 0:
                    continue
                if m is None:
                    s = 1.0 * (1 if d == 1 else -1)
                elif p75:
                    s = (1 if d == 1 else -1) * min(m / p75, 1.0)
                else:
                    continue
                acc.setdefault(e, []).append(s)
            for e, vals in acc.items():
                if elig_bars(e, t):
                    out[(e, t)] = sum(vals) / len(vals)
        return out

    def a6_h2_pairs():
        out = {}
        for t in gates:
            for e, lst in rev.items():
                # P* = latest period with any group first_avail < gate
                # vintage stamps of P*: 1 + amend_count for depth>=2 groups;
                # single-vintage groups come from the timing layer
                tg = tim.get(e, [])
                best_first = None
                best_eff = None
                for av, eff, oz, cz, lag in tg:
                    if dd(av) < t and (best_first is None or av > best_first):
                        best_first, best_eff = av, eff
                if best_eff is None:
                    continue
                stamps = 0
                n = 0
                for av, eff, oz, cz, lag in tg:
                    if eff == best_eff and dd(av) < t:
                        n += 1
                        stamps += 1
                for r in lst:
                    if r["eff"] == best_eff and dd(r["last_avail"]) < t:
                        stamps += r["amend_count"]
                if n >= 10 and elig_bars(e, t):
                    out[(e, t)] = stamps / n
        return out

    # ---------------- veto entries -----------------------------------------
    def veto_momentum():
        out = {}
        for t in gates:
            for e in series:
                w = prior_window(e, t, 63)
                if w is None or w[0] <= 0 or w[-1] <= 0:
                    continue
                out[(e, t)] = w[-1] / w[0] - 1.0
        return out

    def veto_vol(kind):
        out = {}
        for t in gates:
            for e in series:
                w = prior_window(e, t, 63)
                if w is None:
                    continue
                rets = [math.log(w[i] / w[i - 1]) for i in range(1, len(w)) if w[i - 1] > 0 and w[i] > 0]
                if len(rets) < 30:
                    continue
                if kind == "vol":
                    mu = sum(rets) / len(rets)
                    out[(e, t)] = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
                else:
                    dn = sum(r * r for r in rets if r < 0)
                    tot = sum(r * r for r in rets)
                    out[(e, t)] = dn / tot if tot > 0 else None
        return out

    def veto_ratio(num_f, den_f="us-gaap:Assets", flow=False):
        out = {}
        for t in gates:
            for e in bookable:
                den = asof(e, den_f, t)
                if not den:
                    continue
                if flow:
                    # 3-leg accrual-flow: (dAR + dINV - dAP) / Assets,
                    # fiscal-matched annual (Dec) legs — the V9 F1 spec form
                    y = latest_annual_year(e, "us-gaap:AccountsReceivableNetCurrent", t)
                    if y is None:
                        continue
                    num = 0.0
                    ok = True
                    for f, sign in (("us-gaap:AccountsReceivableNetCurrent", 1),
                                    ("us-gaap:InventoryNet", 1),
                                    ("us-gaap:AccountsPayableCurrent", -1)):
                        cur = asof(e, f, t)
                        pri = asof(e, f, t, prior_annual=(y, None))
                        if cur is None or pri is None:
                            ok = False
                            break
                        num += sign * (cur - pri)
                    if not ok:
                        continue
                    out[(e, t)] = num / den
                    continue
                if isinstance(num_f, tuple):
                    # wc stock: (AssetsCurrent - LiabilitiesCurrent)/Assets —
                    # unpack BEFORE any asof call (A7 HIGH-1 remediation: the
                    # tuple must never reach asof as a key)
                    num = asof(e, num_f[0], t)
                    if num is None:
                        continue
                    num2 = asof(e, num_f[1], t)
                    if num2 is None:
                        continue
                    out[(e, t)] = (num - num2) / den
                    continue
                num = asof(e, num_f, t)
                if num is None:
                    continue
                out[(e, t)] = num / den
        return out

    def veto_depletion():
        """The depletion-runway ancestor form exactly: (RE(prior FY) - RE(now)
        - Cash(now)) / Assets(now), fiscal-matched annual (Dec) legs
        (A7 HIGH-2 remediation: this veto was previously measured on an
        accrual-flow-minus-cash proxy; RE is the defining field)."""
        out = {}
        RE = "us-gaap:RetainedEarningsAccumulatedDeficit"
        for t in gates:
            for e in bookable:
                assets = asof(e, "us-gaap:Assets", t)
                if not assets:
                    continue
                y = latest_annual_year(e, RE, t)
                if y is None:
                    continue
                re_now = asof(e, RE, t)
                re_prior = asof(e, RE, t, prior_annual=(y, None))
                cash = asof(e, "us-gaap:CashAndCashEquivalentsAtCarryingValue", t)
                if re_now is None or re_prior is None or cash is None:
                    continue
                out[(e, t)] = (re_prior - re_now - cash) / assets
        return out

    def veto_sector_form():
        # sector prior-63s equal-weight mean return as the entity exposure
        mom = veto_momentum()
        sec_ret = {}
        for (e, t), v in mom.items():
            sec_ret.setdefault((bookable[e]["sector"], t), []).append(v)
        for k in sec_ret:
            sec_ret[k] = sum(sec_ret[k]) / len(sec_ret[k])
        return {k: sec_ret.get((bookable[k[0]]["sector"], k[1]), 0.0) for k in mom}

    print("[d2] computing veto exposures...", flush=True)
    vetoes = {
        "momentum_63s": veto_momentum(),
        "semivariance_share": veto_vol("semi"),
        "vol_level": veto_vol("vol"),
        "wc_stock_intensity": veto_ratio(("us-gaap:AssetsCurrent", "us-gaap:LiabilitiesCurrent")),
        "goodwill_bloat": veto_ratio("us-gaap:Goodwill"),
        "f1_accrual_flow": veto_ratio(("us-gaap:AccountsReceivableNetCurrent",), flow=True),
        "depletion_interaction": veto_depletion(),
        "cash_level": veto_ratio("us-gaap:CashAndCashEquivalentsAtCarryingValue"),
    }
    vetoes["sector_exposure_form"] = veto_sector_form()

    print("[d2] computing proposal exposures...", flush=True)
    proposals = {
        "SFV10-A4-H1": {"anchor": a4_h1_pairs(), "control": a4_h1_control(), "neighbour": None, "ctrl_gate": 0.95},
        "SFV10-A4-H2": {"anchor": a4_h2_pairs(), "control": None, "neighbour": None, "ctrl_gate": None},
        "SFV10-A5-H1": {"anchor": a5_h1_pairs(), "control": a5_h1_control(), "neighbour": None, "ctrl_gate": 0.70},
        "SFV10-A5-H2": {"anchor": a5_pairs(lambda r: r["inter_arrival_days"]),
                        "control": a5_pairs(lambda r: r["inter_arrival_days"], flat_only=True),
                        "neighbour": None, "ctrl_gate": 0.70},
        "SFV10-A6-H1": {"anchor": a6_h1_pairs(), "control": a6_h1_pairs(stale_shift=True), "neighbour": None, "ctrl_gate": None},
        "SFV10-A6-H2": {"anchor": a6_h2_pairs(), "control": None, "neighbour": None, "ctrl_gate": None},
    }

    print("[d2] correlating...", flush=True)
    results = {}
    for pid, p in proposals.items():
        anchor = p["anchor"]
        entry = {"pairs": len(anchor), "veto_rho": {}, "n_per_veto": {}}
        for vn, vm in vetoes.items():
            common = [k for k in anchor if k in vm and anchor[k] is not None and vm[k] is not None]
            ra = [anchor[k] for k in common]
            rb = [vm[k] for k in common]
            rho = spearman(ra, rb)
            entry["veto_rho"][vn] = None if rho is None else round(rho, 4)
            entry["n_per_veto"][vn] = len(common)
        valid = [abs(v) for v in entry["veto_rho"].values() if v is not None]
        entry["max_abs_veto_rho"] = max(valid) if valid else None
        entry["vetoes_measured"] = len(valid)
        # fail-closed: ALL NINE forbidden-ancestor entries must be measured;
        # a null veto (NOT_RUN) makes the novelty gate FAIL, never pass-open
        entry["novelty_pass_le_020"] = (
            len(valid) == 9 and max(valid) <= 0.20)
        if p["control"] is not None and anchor:
            common = [k for k in anchor if k in p["control"]
                      and anchor[k] is not None and p["control"][k] is not None]
            rho = spearman([anchor[k] for k in common], [p["control"][k] for k in common])
            entry["anchor_vs_control_rho"] = None if rho is None else round(rho, 4)
            entry["control_pairs"] = len(common)
            g = p["ctrl_gate"]
            if g is not None and rho is not None:
                entry["control_identifiable"] = bool(abs(rho) < g)
            else:
                entry["control_identifiable"] = None
        else:
            entry["anchor_vs_control_rho"] = None
            entry["control_identifiable"] = None
        results[pid] = entry
        print(f"[d2] {pid}: pairs={entry['pairs']} max|rho|={entry['max_abs_veto_rho']} "
              f"ctrl_rho={entry.get('anchor_vs_control_rho')}", flush=True)

    audit = {
        "schema": "stocks_free_v10_run/d2_v10_novelty_measure@1",
        "built_at_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "producer_role": "A1 (PLAN_stocks_v10 sec3 D2 measured novelty + control identifiability)",
        "discipline": "feature/rank arithmetic only; zero PnL; universe = entity-decision pairs where the proposal exposure is defined on the bookable pool with >= 63 price bars; Spearman midrank ties, pooled",
        "measured_conventions": [
            "group-level proposal exposures aggregate to entity level by MEAN over qualifying groups (rank correlation requires an entity-level scalar)",
            "event age (A4-H2) measured on the global benchmark session calendar",
            "fiscal-matched veto flows use latest annual (Dec) legs",
        ],
        "decision_dates": dates,
        "results": results,
        "verdict_rule": "INELIGIBLE_NOVELTY if max|rho| > 0.20 vs any veto; INELIGIBLE_CONTROL_UNIDENTIFIABLE if |anchor-control rho| >= the proposal's declared gate (0.70 for A5-H1/A5-H2, 0.95 for A4-H1); placebo-by-construction controls (A4-H2 lexicographic, A6-H1 stale declared-open, A6-H2 composition) report measured rho without a hard gate",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=1) + "\n")
    print("[d2] written", OUT, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
