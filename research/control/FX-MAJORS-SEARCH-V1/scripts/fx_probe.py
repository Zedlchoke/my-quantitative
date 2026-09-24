"""Per-pair bi5 probe: verify candle layout AND price scale against ticks.

Fail-closed: any check fails -> the pair's corpus cannot be built.
Checks per pair (GBPUSD, USDJPY):
  P1 candle 24B layout: OHLC invariants over 3 days x BID/ASK
  P2 minute offsets monotonic in [0,86399]
  P3 price scale: all values inside the pair's plausible band
  P4 tick-vs-candle cross-check: M1 close == last tick of the minute
"""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fx_lib as fx

OUT = Path(__file__).resolve().parent.parent / "data_local" / "probe"
OUT.mkdir(parents=True, exist_ok=True)
DAYS = [(2024, 3, 4), (2024, 3, 5), (2024, 3, 6)]
TICK_HOURS = (7, 10)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ev = {"schema": "fxm.probe@1", "pairs": {}}
    fetcher = fx.KeepAliveFetcher()
    all_pass = True
    for pair, meta in fx.PAIRS.items():
        scale = meta["scale"]
        lo, hi = meta["range"]
        inv = off = rng_v = 0
        total = 0
        stats = {}
        for (y, m, d) in DAYS:
            for side in ("BID", "ASK"):
                raw = fetcher.fetch(fx.candle_path(pair, y, m, d, side))
                if raw is None:
                    stats[f"{side}_{d}"] = "MISSING_404"
                    continue
                recs = fx.decode_min_candles(raw, scale)
                total += len(recs)
                prev = -1
                for r in recs:
                    if not (r["low"] <= min(r["open"], r["close"]) and max(r["open"], r["close"]) <= r["high"]):
                        inv += 1
                    vals = (r["open"], r["close"], r["low"], r["high"])
                    if not (lo <= min(vals) and max(vals) <= hi):
                        rng_v += 1
                    if r["sec"] <= prev or not (0 <= r["sec"] <= 86399):
                        off += 1
                    prev = r["sec"]
                stats[f"{side}_{d}"] = {"records": len(recs), "last_close": recs[-1]["close"]}
        # P4 tick cross-check on day one
        bid_raw = fetcher.fetch(fx.candle_path(pair, DAYS[0][0], DAYS[0][1], DAYS[0][2], "BID"))
        candles = {r["sec"]: r["close"] for r in fx.decode_min_candles(bid_raw, scale)}
        cmpd = mis = 0
        for h in TICK_HOURS:
            traw = fetcher.fetch(fx.tick_path(pair, DAYS[0][0], DAYS[0][1], DAYS[0][2], h))
            if traw is None:
                continue
            bymin = {}
            for ms, a, b in fx.decode_ticks(traw, scale):
                bymin.setdefault((h * 3600 + ms // 1000) // 60 * 60, []).append((ms, b))
            for msec, tks in bymin.items():
                c = candles.get(msec)
                if c is None:
                    continue
                cmpd += 1
                if abs(sorted(tks)[-1][1] - c) > meta["pip"] / 10:
                    mis += 1
        checks = {
            "P1_ohlc": {"violations": inv, "records": total, "result": "PASS" if inv == 0 and total > 1000 else "FAIL"},
            "P2_offsets": {"violations": off, "result": "PASS" if off == 0 else "FAIL"},
            "P3_scale": {"violations": rng_v, "result": "PASS" if rng_v == 0 else "FAIL",
                          "sample_last_close": stats.get(f"BID_{DAYS[0][2]}", {}).get("last_close")},
            "P4_tick_crosscheck": {"minutes": cmpd, "mismatches": mis,
                                    "result": "PASS" if cmpd >= 60 and mis == 0 else "FAIL"},
        }
        verdict = "PROBE_PASS" if all(c["result"] == "PASS" for c in checks.values()) else "PROBE_FAIL"
        all_pass &= verdict == "PROBE_PASS"
        ev["pairs"][pair] = {"checks": checks, "verdict": verdict, "day_stats": stats}
        print(pair, verdict, {k: v["result"] for k, v in checks.items()}, flush=True)

    ev["verdict"] = "ALL_PROBE_PASS" if all_pass else "PROBE_FAIL"
    (OUT / "probe_pairs_evidence.json").write_text(json.dumps(ev, indent=1, default=str))
    print("VERDICT:", ev["verdict"])
    sys.exit(0 if all_pass else 2)


if __name__ == "__main__":
    main()
