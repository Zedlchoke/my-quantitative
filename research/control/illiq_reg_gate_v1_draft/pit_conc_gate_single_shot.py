"""PIT-liquidity-concentration regime variable + single-shot gate replay.

DESCRIPTIVE ONLY. Thresholds are a mechanical quantile rule on PRE-WINDOW
stamps (2020-01-06..2024-08-19 Mondays, b20 catalog). The gate is applied to
the EXISTING diag boundary series exactly once (no iteration, no tuning).
"""
import json, math, glob, statistics, sys
import datetime as dt
from pathlib import Path
import pyarrow.parquet as pq

UTC = dt.timezone.utc
CTRL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1")
NS = Path("/Users/hoangminhlong/my-quantitative/research/control/illiq_reg_gate_v1_draft")
ALL_SYMS = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
            "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
            "ONGUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT","SOLUSDT"]

def d(ns): return dt.datetime.fromtimestamp(int(ns)/1e9, UTC)

def daily_dv(catalog, sym, t0, t1):
    directory = CTRL / catalog / "data" / "binance_bar" / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(glob.glob(str(directory / "*.parquet")))
    if not files: return {}
    per = {}
    for fp in files:
        t = pq.read_table(fp, columns=["ts_event", "quote_volume"])
        ts = t.column("ts_event").to_pylist(); qv = t.column("quote_volume").to_pylist()
        for i in range(len(ts)):
            day = d(ts[i]).date()
            if day < t0 or day >= t1: continue
            per[day] = per.get(day, 0.0) + float(qv[i])
    return per

def btc_closes(catalog, t0, t1):
    directory = CTRL / catalog / "data" / "binance_bar" / "BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(glob.glob(str(directory / "*.parquet")))
    per = {}
    for fp in files:
        t = pq.read_table(fp, columns=["ts_event", "close"])
        ts = t.column("ts_event").to_pylist(); cl = t.column("close").to_pylist()
        for i in range(len(ts)):
            day = d(ts[i]).date()
            if day < t0 or day >= t1: continue
            raw = cl[i]
            per[day] = int.from_bytes(raw, "little", signed=True)/10**16 if isinstance(raw,(bytes,bytearray)) else float(raw)
    return per

ELIG_DAYS = 28  # same listing-age law as the frozen engine's formation window

def pit_series(catalog, t0, t1):
    dv = {}
    first_day = {}
    for sym in ALL_SYMS:
        per = daily_dv(catalog, sym, t0, t1)
        if not per: continue
        first_day[sym] = min(per)
        for day, v in per.items():
            dv[(day, sym)] = v
    days = sorted(set(k[0] for k in dv))
    share, elig_n = {}, {}
    for day in days:
        el = [s for s in first_day if (day - first_day[s]).days >= ELIG_DAYS and dv.get((day, s))]
        tot = math.fsum(dv[(day, s)] for s in el)
        if tot <= 0 or "BTCUSDT" not in el: continue
        share[day] = dv[(day, "BTCUSDT")] / tot
        elig_n[day] = len(el)
    return share, elig_n

def rvol(closes, day, window=30):
    ds = [x for x in sorted(closes) if x <= day][-window-1:]
    if len(ds) < window + 1: return None
    rs = [math.log(closes[ds[i+1]]/closes[ds[i]]) for i in range(window)]
    return statistics.pstdev(rs) * math.sqrt(365)

# windows
pw0, pw1 = dt.date(2020, 1, 1), dt.date(2024, 8, 22)
s00, s01 = dt.date(2024, 4, 1), dt.date(2025, 10, 1)

share_pw, elig_pw = pit_series("catalog_live_crypto_b20", pw0, pw1)
closes_pw = btc_closes("catalog_live_crypto_b20", pw0, pw1)
share_s0r, elig_s0r = pit_series("catalog_live_crypto_s0r", s00, s01)
closes_s0r = btc_closes("catalog_live_crypto_s0r", s00, s01)

mondays = []
day = pw0
while day <= dt.date(2025, 9, 1):
    if day.weekday() == 0: mondays.append(day)
    day += dt.timedelta(days=1)

def conc_at(share, st, w):
    vals = [share[x] for x in sorted(share) if st - dt.timedelta(days=w) <= x < st]
    return math.fsum(vals)/len(vals) if vals else None

rows = {}
for st in mondays:
    sh = share_pw if st < pw1 else share_s0r
    cl = closes_pw if st < pw1 else closes_s0r
    if st >= pw1:
        # stitch: conc90 may need b20 history pre-2024-05
        pass
    c28, c90 = conc_at(sh, st, 28), conc_at(sh, st, 90)
    rows[st.isoformat()] = dict(conc28=c28, s90=(None if c28 is None or c90 is None else c28 - c90),
                                rvol=rvol(cl, st), elig=(elig_pw if st < pw1 else elig_s0r).get(st))

pw_stamps = [k for k in sorted(rows) if k < "2024-08-22"]
s_vals = sorted(v["s90"] for v in (rows[k] for k in pw_stamps) if v["s90"] is not None)
v_vals = sorted(v["rvol"] for v in (rows[k] for k in pw_stamps) if v["rvol"] is not None)
def q(sv, p): return sv[min(len(sv)-1, max(0, int(p*len(sv))))]
BAND_ON, BAND_OFF = q(s_vals, 0.70), q(s_vals, 0.90)     # s90 <= p70 -> ON ; s90 >= p90 -> OFF
VOL_FLOOR, VOL_HYST = q(v_vals, 0.10), 0.10              # rvol >= p10 -> ON ; OFF below floor*(1-h)

# single-shot gate walk (frozen rule), state starts ON
cstate = True
for k in sorted(rows):
    v = rows[k]
    s = v["s90"]
    if s is None:
        v["conc_state"] = cstate
    else:
        if s >= BAND_OFF: cstate = False
        elif s <= BAND_ON: cstate = True
        v["conc_state"] = cstate
vs = True
for k in sorted(rows):
    rv = rows[k]["rvol"]
    if rv is None: rows[k]["vol_state"] = vs
    else:
        if rv >= VOL_FLOOR: vs = True
        elif rv < VOL_FLOOR*(1-VOL_HYST): vs = False
        rows[k]["vol_state"] = vs

gate = {k: (bool(rows[k]["conc_state"]) and bool(rows[k]["vol_state"])) for k in rows}

def gated_metrics(tag):
    a = json.load(open(CTRL/f"illiq_diag/{tag}/results/artifact.json"))
    daily = a["daily_returns"]
    gross_eq, g_peak, g_worst = 0.0, 0.0, 0.0
    net_eq, n_peak, n_worst = 0.0, 0.0, 0.0
    off_days, on_ret, off_ret = 0, [], []
    for r in daily:
        st = d(r["decision_ns"]).date().isoformat()
        g = gate.get(st, True)
        if not g:
            off_days += 1; off_ret.append(r["net_return_per_unit"])
        else:
            on_ret.append(r["net_return_per_unit"])
            net_eq += r["net_return_per_unit"]
            n_peak = max(n_peak, net_eq); n_worst = max(n_worst, n_peak - net_eq)
    return dict(tag=tag, gated_net_sum=net_eq, gated_mdd=n_worst, off_boundaries=off_days,
                off_return_sum=math.fsum(off_ret), n=len(daily))

res = dict(
    band_on=BAND_ON, band_off=BAND_OFF, vol_floor=VOL_FLOOR, vol_hyst=VOL_HYST,
    n_prewindow=len(pw_stamps),
    prewindow_s90=dict(p10=q(s_vals,0.1), p50=q(s_vals,0.5), p70=BAND_ON, p90=BAND_OFF,
                       min=s_vals[0], max=s_vals[-1]),
    prewindow_rvol=dict(p10=VOL_FLOOR, p50=q(v_vals,0.5), p90=q(v_vals,0.9), min=v_vals[0], max=v_vals[-1]),
    gated={t: gated_metrics(t) for t in ["S0R-ANCHOR-A5","Y2024P-ANCHOR-A4","Y2021-ANCHOR-v2"]},
    stamp_rows=rows, gate=gate,
)
json.dump(res, open(NS/"pit_conc_gate_single_shot.json","w"), indent=1, default=str)

# console digest
print("THRESHOLDS: s90 ON<=%.6f OFF>=%.6f | rvol floor>=%.4f hyst %.2f | prewindow n=%d" %
      (BAND_ON, BAND_OFF, VOL_FLOOR, VOL_HYST, len(pw_stamps)))
print("GATED REPLAY (single-shot, descriptive):")
for t, m in res["gated"].items(): print(" ", json.dumps(m))
for tag in ["Y2021","2024-01","2024-03","2024-05","2024-07","2024-09","2024-11","2025-01","2025-03","2025-05","2025-07"]:
    ks = [k for k in sorted(rows) if k.startswith(tag)]
    if ks:
        v0 = rows[ks[0]]
        print(tag, "s90=%.4f rvol=%.3f conc_state=%s vol=%s elig=%s" %
              (v0["s90"] if v0["s90"] is not None else float("nan"),
               v0["rvol"] if v0["rvol"] is not None else float("nan"),
               str(bool(v0["conc_state"])), v0["vol_state"], v0.get("elig")))
off = [k for k in sorted(gate) if not gate[k]]
print("OFF stamps total:", len(off), "of", len(gate))
print("OFF stamps in S0R window:", [k for k in off if k >= "2024-08-22"])
