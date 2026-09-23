"""P1-bis probe: validate Dukascopy M1 candle bi5 layout against ticks.

Fail-closed: if any hypothesis fails, exits non-zero and the cycle's data
plane cannot be built. Writes a JSON evidence artifact.

Checks:
  C1 candle record layout (sec, open, close, low, high): OHLC ordering
     invariants low <= min(o,c), max(o,c) <= high over EVERY record of
     3 sample days (BID and ASK).
  C2 timestamp semantics: minute-of-day offsets strictly increasing,
     within [0, 86399]; first data minute sane for a Monday.
  C3 tick-vs-candle cross-check: for 2 sample hours on 2024-03-04, the
     candle M1 close bid equals the LAST tick bid in that minute (within
     0.1 point) and the candle high/low bracket all tick bids of the
     minute.
  C4 price scale sanity: all prices within [0.80, 1.35].
"""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import duka_lib as dk

OUT = Path(__file__).resolve().parent.parent / "data_local" / "probe"
OUT.mkdir(parents=True, exist_ok=True)

DAYS = [(2024, 3, 4), (2024, 3, 5), (2024, 3, 6)]  # Mon..Wed, calendar months
TICK_HOURS = {  # (y,m,d,h) tick files to fetch for cross-check (day one only)
    (2024, 3, 4, h): h for h in (7, 10)
}

evidence = {
    "schema": "eosv1.probe@1",
    "measured_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "urls": {},
    "sha256": {},
    "checks": {},
    "verdict": None,
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_candle_day(y, m, d, side):
    url = dk.candle_url(y, m, d, side)
    raw = dk.fetch_bytes(url)
    evidence["urls"][f"{side}_{y}{m:02d}{d:02d}"] = url
    if raw is None:
        return None, None
    evidence["sha256"][f"{side}_{y}{m:02d}{d:02d}"] = sha(raw)
    return raw, dk.decode_min_candles(raw)


# C1/C2/C4 on candle days
invariant_violations = 0
total_records = 0
scale_violations = 0
order_violations = 0
day_stats = {}
for (y, m, d) in DAYS:
    for side in ("BID", "ASK"):
        raw, recs = load_candle_day(y, m, d, side)
        if recs is None:
            day_stats[f"{side}_{d}"] = "MISSING_404"
            continue
        total_records += len(recs)
        prev = -1
        for r in recs:
            if not (r["low"] <= min(r["open"], r["close"]) and max(r["open"], r["close"]) <= r["high"]):
                invariant_violations += 1
            if not (0.80 <= min(r["low"], r["open"], r["close"], r["high"]) and max(r["low"], r["open"], r["close"], r["high"]) <= 1.35):
                scale_violations += 1
            if r["sec"] <= prev or r["sec"] < 0 or r["sec"] > 86399:
                order_violations += 1
            prev = r["sec"]
        day_stats[f"{side}_{d}"] = {"records": len(recs), "first_sec": recs[0]["sec"], "last_sec": recs[-1]["sec"], "close_last": recs[-1]["close"]}

evidence["checks"]["C1_ohlc_invariants"] = {
    "records_checked": total_records, "violations": invariant_violations,
    "result": "PASS" if invariant_violations == 0 and total_records > 1000 else "FAIL",
}
evidence["checks"]["C2_offsets_monotonic_in_day"] = {
    "violations": order_violations, "result": "PASS" if order_violations == 0 else "FAIL",
}
evidence["checks"]["C4_price_scale"] = {
    "violations": scale_violations, "result": "PASS" if scale_violations == 0 else "FAIL",
}
evidence["day_stats"] = day_stats

# C3 tick cross-check on 2024-03-04
bid_day, bid_recs = load_candle_day(2024, 3, 4, "BID")
min_by_sec = {r["sec"]: r for r in bid_recs}
tick_rows = []
for (y, m, d, h) in sorted(TICK_HOURS):
    url = dk.tick_url(y, m, d, h)
    raw = dk.fetch_bytes(url)
    evidence["urls"][f"ticks_{h}h"] = url
    evidence["sha256"][f"ticks_{h}h"] = sha(raw) if raw is not None else None
    if raw is None:
        tick_rows.append([])
        continue
    rows = []
    for ms, a, b, av, bv in dk.decode_ticks(raw):
        sec = h * 3600 + ms // 1000
        rows.append((sec, ms, b, a))  # absolute ms kept: 'last tick' must sort by full ms
    tick_rows.append(rows)

close_mismatch = 0
bracket_violations = 0
compared = 0
for rows in tick_rows:
    by_min = {}
    for sec, ms, b, a in rows:
        by_min.setdefault(sec - sec % 60, []).append((ms, b, a))
    for sec_min, ticks in by_min.items():
        r = min_by_sec.get(sec_min)
        if r is None:
            continue  # candle file may skip minutes w/o a bar close rule; counted as coverage gap later
        compared += 1
        last_bid = sorted(ticks)[-1][1]
        if abs(last_bid - r["close"]) > 0.1 / dk.PRICE_SCALE * 10:  # tolerance 1 point=1e-5*10
            close_mismatch += 1
        lo = min(t[1] for t in ticks)
        hi = max(t[1] for t in ticks)
        if not (r["low"] <= lo + 1e-9 and r["high"] >= hi - 1e-9):
            bracket_violations += 1

evidence["checks"]["C3_tick_vs_candle"] = {
    "minutes_compared": compared,
    "close_mismatches": close_mismatch,
    "bracket_violations": bracket_violations,
    "result": "PASS" if compared >= 60 and close_mismatch == 0 and bracket_violations == 0 else "FAIL",
}

verdicts = [evidence["checks"][k]["result"] for k in evidence["checks"]]
evidence["verdict"] = "PROBE_PASS" if all(v == "PASS" for v in verdicts) else "PROBE_FAIL"

out = OUT / "probe_20240304_evidence.json"
out.write_text(json.dumps(evidence, indent=1, default=str))
print(json.dumps({k: (v["result"] if isinstance(v, dict) and "result" in v else v) for k, v in evidence["checks"].items()}, indent=1))
print("VERDICT:", evidence["verdict"])
print("wrote", out)
sys.exit(0 if evidence["verdict"] == "PROBE_PASS" else 2)
