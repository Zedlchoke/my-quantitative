"""CRYPTO-V17 D2 stage 2: endpoint-series pulls + measured novelty for the two
event proposals (A6-P1 FUNDJUMP on fapi fundingRate; A6-P2 OICASCADE on
data.binance.vision daily metrics).

Lock discipline: acquires the machine-wide heavy lock with a bounded polite
retry (60 s spacing, hard 4 h deadline) - SHV1 scheduler policy for the
retryable RESOURCE_CONFLICT class, never contention, never unbounded spin.
Bounded downloads; OI raw zips deleted after in-memory reduction (raw
archives never persist); sha256 manifests recorded.
"""
import csv
import hashlib
import io
import json
import math
import statistics
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from research.governance import heavy_lock  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measure_novelty_panel import (daily as panel_daily, load as panel_load,  # noqa: E402
                                   pearson, spearman, hourly_proxies, f as to_f)

WORKTREE = Path(__file__).resolve().parents[4]
STAGING = WORKTREE / "v17_data" / "staging_v17"
D2 = WORKTREE / "research" / "control" / "v17_run" / "d2"
SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
S0_START_MS = 1755820800000            # 2025-08-22T00:00:00Z
WARMUP_START_MS = S0_START_MS - 119 * 86400000  # pre-S0 warmup for the OI P10 window (proposal-frozen 720 H4 closes)
S0_END_MS = S0_START_MS + 365 * 86400000 - 1
DAY_MS = 86400000

def sha(b): return hashlib.sha256(b).hexdigest()

def fetch(url, binary=False, retries=3):
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                b = r.read()
            return b if binary else json.loads(b)
        except Exception as e:
            last = e
            time.sleep(20 * (attempt + 1))
    raise last

# ---------------- funding ----------------

def pull_funding():
    out = {}
    for sym in ["BTCUSDT", "ETHUSDT"]:
        rows, start = [], 1754006400000  # 2025-08-01 buffer
        end = S0_END_MS
        while start < end:
            batch = fetch(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}&startTime={start}&endTime={end}&limit=1000")
            if not batch:
                break
            rows += batch
            start = batch[-1]["fundingTime"] + 1
            if len(batch) < 1000:
                break
        out[sym] = rows
        print(f"funding {sym}: {len(rows)} settlements", flush=True)
    p = D2 / "funding_history.json"
    p.write_text(json.dumps(out) + "\n")
    return out

# ---------------- OI metrics ----------------

def pull_oi_metrics():
    """Daily metrics zips -> per-H4 OI snapshot series per symbol; raw deleted.
    The reduced series is persisted (v17_data/oi_series_reduced.json + manifest
    in the control dir) so code fixes never re-pay the 1,095-file pull."""
    import urllib.request
    cache = WORKTREE / "v17_data" / "oi_series_reduced.json"
    mani = D2 / "oi_metrics_manifest.json"
    if cache.exists() and mani.exists():
        m = json.loads(mani.read_text())
        if m.get("files") == 1095:
            print("oi: reusing reduced series cache", flush=True)
            return json.loads(cache.read_text())
    d0 = datetime(2025, 8, 22, tzinfo=timezone.utc).date()
    oi = {}
    oi_snapshots = {}
    manifest = []
    for sym in SYMS:
        series = {}  # h4_bucket_start_ms -> last sum_open_interest
        for i in range(484):  # 365 S0 days + 119 pre-S0 warmup days (proposal P10 window needs 720 H4 closes)
            day = d0.fromordinal(d0.toordinal() + i - 119).isoformat()
            y, m, dd = day.split("-")
            url = f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{y}-{m}-{dd}.zip"
            raw = fetch(url, binary=True)
            manifest.append({"symbol": sym, "date": day, "url": url,
                             "bytes": len(raw), "sha256": sha(raw)})
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                name = [n for n in zf.namelist() if n.endswith((".csv",))][0]
                with zf.open(name) as fh:
                    text = io.TextIOWrapper(fh, encoding="utf-8")
                    for row in csv.DictReader(text):
                        # vision metrics schema: create_time is a UTC datetime
                        # string "YYYY-MM-DD HH:MM:SS" (schema error fixed per
                        # the SHV1 taxonomy - CODE_OR_SCHEMA_ERROR never retried
                        # blind; verified against a real downloaded file first)
                        tau = int(datetime.strptime(row["create_time"].strip(),
                                                    "%Y-%m-%d %H:%M:%S")
                                  .replace(tzinfo=timezone.utc).timestamp() * 1000)
                        if tau < WARMUP_START_MS or tau > S0_END_MS:
                            continue
                        h4 = tau // (4 * 3600 * 1000) * 4 * 3600 * 1000
                        v = row.get("sum_open_interest")
                        if v:
                            series[h4] = float(v)
            if (i + 1) % 60 == 0:
                print(f"oi {sym}: {i + 1}/365 days", flush=True)
        oi_snapshots[sym] = [series[k] for k in sorted(series)]
        print(f"oi {sym}: {len(series)} H4 snapshots", flush=True)
    (D2 / "oi_metrics_manifest.json").write_text(json.dumps(
        {"files": len(manifest), "sources": manifest}, indent=0) + "\n")
    cache.write_text(json.dumps(oi_snapshots))
    return oi_snapshots

# ---------------- novelty ----------------

def align_daily_from_hourly(ex_hourly_by_sym, sym_rows):
    out = {}
    for sym, ex in ex_hourly_by_sym.items():
        rows = sym_rows[sym]
        acc = defaultdict(list)
        for v, r in zip(ex, rows):
            acc[r["day_utc"]].append(v)
        out[sym] = [statistics.fmean(acc[k]) if acc[k] else 0.0
                    for k in sorted(acc)]
    return out

def measure(name, ex_by_sym, panel_syms, extra_proxies):
    d = {s: panel_daily(panel_load(s)) for s in panel_syms}
    ks = sorted(d[panel_syms[0]])
    names = ["cdf_disp", "run_imb", "run_persist", "taker_sat", "ret",
             "tsmom28", "dvol_shock", "amihud", "dvol_level_log",
             "avg_ticket_ratio", "elite"]
    rhos = {}
    for pname in names:
        pr = {s: [d[s][k].get(pname) for k in ks] for s in panel_syms}
        # F2 remediation: hourly-grid endpoint exposures are daily-aggregated
        # (per symbol-day mean) via align_daily_from_hourly BEFORE panel-proxy
        # comparison - the committed bytes had lost this call (A7 finding F2)
        ex = align_daily_from_hourly(ex_by_sym, {s: panel_load(s) for s in ex_by_sym})
        rhos["panel_daily:" + pname] = {"pearson": pooled_abs(ex, pr, pearson),
                                        "spearman": pooled_abs(ex, pr, spearman)}
    for pname, pr in extra_proxies.items():
        ex = {}
        for s in ex_by_sym:
            series = ex_by_sym[s]
            ex[s] = series[:len(pr[s])] if len(series) >= len(pr[s]) else series + [None] * (len(pr[s]) - len(series))
        rhos["endpoint:" + pname] = {"pearson": pooled_abs(ex, pr, pearson),
                                     "spearman": pooled_abs(ex, pr, spearman)}
    abs_pairs = [(k, max(abs(v["pearson"] or 0), abs(v["spearman"] or 0)))
                 for k, v in rhos.items()]
    worst = max(abs_pairs, key=lambda kv: kv[1])
    return {"rhos": rhos,
            "worst_proxy": worst[0], "worst_pooled_abs_rho": round(worst[1], 4),
            "proxies_over_020": sum(1 for _, a in abs_pairs if a > 0.20),
            "verdict": "VETO_MEASURED" if any(a > 0.20 for _, a in abs_pairs) else "NOVELTY_PASS"}

def pooled_abs(x_by_sym, y_by_sym, fn):
    xs, ys = [], []
    for s in x_by_sym:
        xs += x_by_sym[s]
        ys += y_by_sym[s]
    return fn(xs, ys)

def fundjump_exposure(funding):
    """A6-P1 spec: hourly signed event exposure on the H1 grid."""
    ex = {}
    level_by_hour = {}
    for sym, rows in funding.items():
        rows = [r for r in rows if S0_START_MS <= r["fundingTime"] <= S0_END_MS]
        deltas = [f for f in (float(r["fundingRate"]) for r in rows)]
        series, lvl = [], []
        for i, r in enumerate(rows):
            if i == 0:
                continue
            d_i = float(r["fundingRate"]) - float(rows[i - 1]["fundingRate"])
            win = deltas[max(0, i - 270):i]  # 90d * 3/day
            if len(win) < 180:
                continue
            q90 = sorted(abs(x) for x in win)[min(len(win) - 1, int(len(win) * 0.90))]
            if abs(d_i) >= q90:
                k = r["fundingTime"]
                k_next = rows[i + 1]["fundingTime"] if i + 1 < len(rows) else k + 8 * 3600 * 1000
                series.append((k, k_next, -1.0 if d_i > 0 else 1.0))
        # paint hourly grid
        p_rows = panel_load(sym)
        grid = []
        for r in p_rows:
            T = int(r["last_ts_ms"])
            v = 0.0
            for (k, k_next, sgn) in series:
                if k <= T < k_next:
                    v = sgn
                    break
            grid.append(v)
            lvl.append(0.0)
        # funding LEVEL proxy aligned to hours (carry family)
        lev = []
        idx = 0
        for r in p_rows:
            T = int(r["last_ts_ms"])
            while idx + 1 < len(rows) and rows[idx + 1]["fundingTime"] <= T:
                idx += 1
            lev.append(float(rows[idx]["fundingRate"]) if rows else None)
        ex[sym] = grid
        level_by_hour[sym] = lev
    return ex, level_by_hour

def oicascade_exposure(oi):
    """A6-P2 spec: bottom-decile 24h OI drop AND negative 24h return -> long 24h."""
    ex = {}
    oi_level = {}
    for sym in SYMS:
        p_rows = panel_load(sym)
        h4_snap = oi[sym]
        # map H1 bucket -> its H4 bucket's OI + 24h-ago OI
        vals = sorted({int(r["last_ts_ms"]) // (4 * 3600 * 1000) * 4 * 3600 * 1000 for r in p_rows})
        def oi_at(ts_h4):
            i = min(len(h4_snap) - 1, ts_h4 // (4 * 3600 * 1000) - vals[0] // (4 * 3600 * 1000)) if h4_snap else None
            return h4_snap[i] if (h4_snap and i is not None and 0 <= i < len(h4_snap)) else None
        # r_OI series on H4 closes with 120d rolling P10
        r_series = []
        for j, v in enumerate(vals):
            cur = oi_at(v); prev = oi_at(v - DAY_MS)
            if cur and prev:
                r_series.append((v, cur / prev - 1.0))
            else:
                r_series.append((v, None))
        events = set()
        hist = [x for _, x in r_series if x is not None]
        for j, (v, r) in enumerate(r_series):
            if r is None or j < 480:  # 120d * 6 H4/day warmup
                continue
            win = [x for _, x in r_series[max(0, j - 720):j] if x is not None]
            if not win:
                continue
            p10 = sorted(win)[max(0, int(len(win) * 0.10) - 1)]
            # 24h panel return
            day_rows = [r2 for r2 in p_rows
                        if int(r2["last_ts_ms"]) // DAY_MS == v // DAY_MS]
            prev_rows = [r2 for r2 in p_rows
                         if int(r2["last_ts_ms"]) // DAY_MS == (v - DAY_MS) // DAY_MS]
            if not day_rows or not prev_rows:
                continue
            r24 = (to_f(day_rows[-1]["last_price"]) / to_f(prev_rows[-1]["last_price"]) - 1.0) \
                if to_f(prev_rows[-1]["last_price"]) else 0.0
            if r <= p10 and r24 < 0:
                events.add(v)
        # paint H4->H1 grid: long the 24h AFTER an event bucket
        grid = []
        for r in p_rows:
            T = int(r["last_ts_ms"])
            v = T // (4 * 3600 * 1000) * 4 * 3600 * 1000
            grid.append(-1.0 if any(e <= T < e + DAY_MS for e in events) else 0.0)
        ex[sym] = grid
        oi_level[sym] = [oi_at(T // (4 * 3600 * 1000) * 4 * 3600 * 1000) for T in
                         (int(r["last_ts_ms"]) for r in p_rows)]
    return ex, oi_level

def main():
    deadline = time.time() + 4 * 3600
    attempts = 0
    while True:
        attempts += 1
        try:
            cm = heavy_lock.acquire(
                cycle_id="CRYPTO-V17", role="D2_ENDPOINT_NOVELTY_PULL",
                worktree=str(WORKTREE),
                command=[sys.executable, str(Path(__file__).resolve())],
                expected_artifacts=[str(D2 / "d2_novelty_endpoint_v17.json")])
            break
        except heavy_lock.LockBusyError as e:
            if time.time() > deadline:
                print(f"GIVING UP after {attempts} attempts: {e}", flush=True)
                sys.exit(3)
            if attempts % 10 == 1:
                print(f"lock busy ({e}); retrying in 60 s", flush=True)
            time.sleep(60)
    with cm as lock:
        try:
            funding = pull_funding()
            oi = pull_oi_metrics()
            ex_f, lev = fundjump_exposure(funding)
            proxies_f = {"funding_level_carry": lev}
            r1 = measure("FUNDJUMP", ex_f, ["BTCUSDT", "ETHUSDT"], proxies_f)
            print("FUNDJUMP:", r1["verdict"], r1["worst_proxy"], r1["worst_pooled_abs_rho"], flush=True)
            ex_o, oil = oicascade_exposure(oi)
            proxies_o = {"oi_level": oil}
            r2 = measure("OICASCADE", ex_o, SYMS, proxies_o)
            print("OICASCADE:", r2["verdict"], r2["worst_proxy"], r2["worst_pooled_abs_rho"], flush=True)
            out = {
                "schema": "v17_run_artifact_v1", "artifact": "d2_novelty_endpoint",
                "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "method": "exposure per frozen proposal spec on pulled keyless endpoint series (fapi fundingRate; vision daily metrics, 1095 files sha-manifested, raw deleted) vs forbidden-family proxies (panel + endpoint levels)",
                "results": {"V17-A6-P1-FUNDJUMP": r1, "V17-A6-P2-OICASCADE": r2},
                "verdicts": {"V17-A6-P1-FUNDJUMP": r1["verdict"],
                             "V17-A6-P2-OICASCADE": r2["verdict"]},
            }
            (D2 / "d2_novelty_endpoint_v17.json").write_text(json.dumps(out, indent=1) + "\n")
            print("d2_novelty_endpoint written", flush=True)
        except Exception:
            import traceback
            tail = "\n".join(traceback.format_exc().strip().splitlines()[-12:])
            lock.release(status="FAILED", note=f"stderr tail: {tail}")
            raise

if __name__ == "__main__":
    main()
