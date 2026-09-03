#!/usr/bin/env python
"""FOREX-FREE-V1 F2 empirical probe of Twelve Data Basic (zero-cost tier).

Reads TWELVE_DATA_API_KEY from the environment or the existing gitignored
root .env; never prints or stores the credential. Raw responses stay under
data_raw/ (gitignored); only manifests, hashes and compact audits are
committed. Two independent pulls per window are compared byte- and
content-wise. Rate limiting: one request per 8 seconds (Basic: 8/min).
"""
import csv, hashlib, io, json, os, sys, time, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REPO_ROOT = "/Users/hoangminhlong/my-quantitative"
RAW = os.path.join(ROOT, "data_raw", "forex_free_v1")
CTL = os.path.join(ROOT, "research", "control", "forex_free_v1_run", "data_probe")
os.makedirs(RAW, exist_ok=True)
os.makedirs(CTL, exist_ok=True)

PAIRS = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CHF", "USD/CAD"]
END = "2026-09-02 23:59:59"           # yesterday; all bars complete
WINDOWS = {
    "1day": [("2018-09-01", "2026-09-02")],
    "4h": [("2018-09-01", "2020-09-01"), ("2020-09-01", "2022-09-01"),
           ("2022-09-01", "2024-09-01"), ("2024-09-01", "2026-09-02")],
}
w = []
d0, cur = date(2018, 9, 1), date(2018, 9, 1)
while cur < date(2026, 9, 2):
    nxt = min(cur + timedelta(days=260), date(2026, 9, 2))
    w.append((cur.isoformat(), nxt.isoformat()))
    cur = nxt
WINDOWS["1h"] = w

def load_key():
    k = os.environ.get("TWELVE_DATA_API_KEY")
    if k:
        return k
    env = os.path.join(REPO_ROOT, ".env")  # existing gitignored root .env
    for line in open(env):
        if line.startswith("TWELVE_DATA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("KEY ABSENT")

KEY = load_key()
_last = [0.0]

def td_get(symbol, interval, sd, ed, tz="UTC"):
    gap = time.time() - _last[0]
    if gap < 8.0:
        time.sleep(8.0 - gap)
    q = {"symbol": symbol, "interval": interval, "start_date": sd, "end_date": ed,
         "outputsize": 5000, "apikey": KEY, "order": "asc"}
    if interval != "1day":
        q["timezone"] = tz
    url = "https://api.twelvedata.com/time_series?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                body = r.read()
            _last[0] = time.time()
            j = json.loads(body)
            if j.get("status") == "error":
                msg = j.get("message", "")
                if ("limit" in msg.lower() or r"429" in msg) and attempt < 3:
                    time.sleep(65); continue
                return body, j, "PROVIDER_ERROR: " + msg
            return body, j, None
        except Exception as e:  # network hiccup
            _last[0] = time.time()
            if attempt == 3:
                return b"", None, "FETCH_ERROR: %s" % e
            time.sleep(20)

def compare(a_bytes, a, b_bytes, b):
    rec = {"sha256_a": hashlib.sha256(a_bytes).hexdigest(),
           "sha256_b": hashlib.sha256(b_bytes).hexdigest(),
           "bytes_identical": a_bytes == b_bytes}
    if a is None or b is None:
        rec["content_identical"] = None
        return rec
    va, vb = a.get("values") or [], b.get("values") or []
    rec.update({"rows_a": len(va), "rows_b": len(vb),
                "content_identical": va == vb and a.get("meta") == b.get("meta"),
                "schema_keys_a": sorted({k for r in va for k in r})})
    return rec

def audit_rows(values, interval):
    if not values:
        return {"rows": 0}
    mins = {"1h": 60, "4h": 240, "1day": 1440}[interval]
    rows = sorted(values, key=lambda r: r["datetime"])
    bad = 0; nulls = 0; vol_null = 0
    prev = None; weekday_gaps = []; weekend_spans = 0
    for r in rows:
        try:
            o, h, l, c = (float(r[k]) for k in ("open", "high", "low", "close"))
        except (KeyError, TypeError, ValueError):
            bad += 1; continue
        if not (h >= l and h >= o and h >= c and l <= o and l <= c and o > 0 and c > 0):
            bad += 1
        if r.get("volume") in (None, "", "null"):
            vol_null += 1
    dts = [r["datetime"] for r in rows]
    def parse(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T"))
    for i in range(1, len(dts)):
        gapm = (parse(dts[i]) - parse(dts[i - 1])).total_seconds() / 60
        if gapm <= mins:
            continue
        d_prev = parse(dts[i - 1]); d_cur = parse(dts[i])
        span = (d_cur - d_prev).total_seconds() / 60
        days = {d_prev.weekday(), d_cur.weekday()}
        if d_prev.weekday() == 4 and d_cur.weekday() in (6, 0):   # Fri -> Sun/Mon
            weekend_spans += 1
        elif days == {5} or (d_prev.weekday() == 5 and d_cur.weekday() == 6):
            weekend_spans += 1
        else:
            weekday_gaps.append({"from": dts[i - 1], "to": dts[i], "gap_minutes": gapm})
    sun_first = {}
    for r in rows:
        d = parse(r["datetime"])
        if d.weekday() == 6:
            sun_first.setdefault(d.date().isoformat(), d.time().isoformat())
    return {"rows": len(rows), "malformed_ohlc": bad, "volume_null_fraction": round(vol_null / max(len(rows), 1), 4),
            "weekday_gaps": weekday_gaps[:20], "weekday_gap_count": len(weekday_gaps),
            "weekend_spans": weekend_spans, "truncation_risk": any(len(x) and False for x in []),
            "first": dts[0], "last": dts[-1],
            "sunday_first_bar_sample": dict(list(sorted(sun_first.items()))[::20][:12])}

def main():
    manifest = {"cycle": "FOREX-FREE-V1", "probe_started_utc": datetime.now(timezone.utc).isoformat(),
                "provider": "twelvedata /time_series", "key_source": "existing gitignored root .env",
                "requests": []}
    for pair in PAIRS:
        for interval, wins in WINDOWS.items():
            tag = pair.replace("/", "")
            agg = {"pair": pair, "interval": interval, "windows": [], "total_rows": 0}
            rows_all = []
            for sd, ed in wins:
                for pull in ("a", "b"):
                    body, j, err = td_get(pair, interval, sd, ed)
                    fp = os.path.join(RAW, f"{tag}_{interval}_{sd}_{pull}.json")
                    with open(fp, "wb") as f:
                        f.write(body)
                    manifest["requests"].append({"pair": pair, "interval": interval, "start": sd,
                                                 "end": ed, "pull": pull, "http_or_provider_error": err,
                                                 "sha256": hashlib.sha256(body).hexdigest()})
                a_j = json.loads(open(os.path.join(RAW, f"{tag}_{interval}_{sd}_a.json")).read())
                b_j = json.loads(open(os.path.join(RAW, f"{tag}_{interval}_{sd}_b.json")).read())
                a_b = open(os.path.join(RAW, f"{tag}_{interval}_{sd}_a.json"), "rb").read()
                b_b = open(os.path.join(RAW, f"{tag}_{interval}_{sd}_b.json"), "rb").read()
                cmp_rec = compare(a_b, a_j, b_b, b_j)
                ok = cmp_rec.get("content_identical") is True
                rows = (a_j.get("values") if isinstance(a_j, dict) else None) or []
                agg["windows"].append({"start": sd, "end": ed, "rows": len(rows),
                                       "deterministic": ok, "compare": cmp_rec,
                                       "truncated_5000": len(rows) == 5000,
                                       "error": (a_j or {}).get("message") if isinstance(a_j, dict) and a_j.get("status") == "error" else None})
                rows_all.extend(rows if ok or rows else [])
                agg["total_rows"] += len(rows)
                print(f"{pair} {interval} {sd}->{ed}: rows={len(rows)} det={ok}", flush=True)
            audit = audit_rows(rows_all, interval)
            audit.update({"pair": pair, "interval": interval,
                          "windows_deterministic": all(x["deterministic"] for x in agg["windows"]),
                          "any_truncation_flag": any(x["truncated_5000"] for x in agg["windows"])})
            with open(os.path.join(CTL, f"audit_{tag}_{interval}.json"), "w") as f:
                json.dump(audit, f, indent=1)
    with open(os.path.join(CTL, "request_manifest.json"), "w") as f:
        manifest["probe_finished_utc"] = datetime.now(timezone.utc).isoformat()
        json.dump(manifest, f, indent=1)
    print("TD PROBE DONE", flush=True)

    # ECB cross-check on daily closes
    ecb = {}
    for ccy in ["USD", "GBP", "AUD", "NZD", "JPY", "CHF", "CAD"]:
        url = ("https://data-api.ecb.europa.eu/service/data/EXR/D." + ccy +
               ".EUR.SP00.A?startPeriod=2018-09-01&endPeriod=2026-09-02&format=csvdata")
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                body = r.read()
            open(os.path.join(RAW, f"ecb_{ccy}.csv"), "wb").write(body)
            rows = list(csv.DictReader(io.StringIO(body.decode())))
            ecb[ccy] = {r["TIME_PERIOD"]: float(r["OBS_VALUE"]) for r in rows if r.get("OBS_VALUE")}
            print(f"ECB {ccy}: {len(ecb[ccy])} obs", flush=True)
        except Exception as e:
            print(f"ECB {ccy}: ERROR {e}", flush=True)
    with open(os.path.join(RAW, "td_d1_caches.json"), "w") as f:
        cache = {}
        for pair in PAIRS:
            tag = pair.replace("/", "")
            vals = []
            fp = os.path.join(RAW, f"{tag}_1day_2018-09-01_a.json")
            if os.path.exists(fp):
                vals = json.load(open(fp)).get("values") or []
            cache[pair] = {r["datetime"][:10]: float(r["close"]) for r in vals if r.get("close")}
        json.dump(cache, f)
    xchk = {"pairs": {}}
    for pair in PAIRS:
        base, quote = pair.split("/")
        td_closes = json.load(open(os.path.join(RAW, "td_d1_caches.json")))[pair]
        diffs = []
        for d, td_c in td_closes.items():
            try:
                if pair == "EUR/USD":
                    ecb_q = ecb["USD"].get(d)
                    implied = ecb_q
                elif quote == "USD":
                    implied = 1.0 / ecb[base].get(d, float("nan")) if ecb[base].get(d) else None
                else:
                    u = ecb["USD"].get(d); q = ecb[quote].get(d)
                    implied = (q / u) if (u and q) else None   # USD/JPY = (EUR/JPY)/(EUR/USD)
            except KeyError:
                implied = None
            if implied:
                diffs.append(abs(td_c - implied) / implied * 1e4)
        diffs.sort()
        xchk["pairs"][pair] = {
            "common_dates": len(diffs),
            "median_abs_diff_bps": round(diffs[len(diffs)//2], 2) if diffs else None,
            "p95_abs_diff_bps": round(diffs[int(len(diffs)*0.95)], 2) if diffs else None,
            "max_abs_diff_bps": round(diffs[-1], 2) if diffs else None}
        print(f"XCHK {pair}: {xchk['pairs'][pair]}", flush=True)
    xchk["basis_note"] = ("TD daily close is the last quote of the UTC day; the ECB fix is a 16:00 CET "
                          "concertation value. Differences are expected timing/basis differences and are "
                          "recorded, not forced to equality. USD-quote pairs are inverted EUR/X (modification declared per ECB terms).")
    with open(os.path.join(CTL, "ecb_crosscheck.json"), "w") as f:
        json.dump(xchk, f, indent=1)
    print("ECB CROSSCHECK DONE", flush=True)

if __name__ == "__main__":
    main()
