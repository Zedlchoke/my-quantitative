#!/usr/bin/env python
"""fibv1-a2 .bi5 tick decoder + proofs (FOREX-INTRA-BIDASK-V1, lane a2-source).

Candidate format (to be VERIFIED from bytes, never assumed):
  .bi5 = LZMA-compressed stream of fixed-stride 20-byte records:
    int32 ms-offset-within-hour, int32 ASK, int32 BID,
    float32 ask-volume, float32 bid-volume (big-endian candidate);
    price scale candidate 1e5 points (all 5 lane pairs are USD-quote, no JPY).

Usage:
  decode_bi5.py --selftest                 # tool validation on synthetic fixture
  decode_bi5.py FILE.bi5 [FILE.bi5 ...] --out decode_report.json

This tool validates the DECODER (fixture) and decodes fetched bytes. It never
invents market data: with no fetched bytes, source decode stays NOT_RUN.
"""

import argparse
import json
import lzma
import math
import os
import struct
from datetime import datetime, timezone

STRIDE_CANDIDATE = 20
SCALE_CANDIDATE = 100_000.0
HOUR_MS = 3_600_000


def decompress_bi5(raw):
    """Try LZMA decode variants; return (payload, method) or raise."""
    errors = []
    for name, kwargs in (
        ("lzma.FORMAT_AUTO", dict(format=lzma.FORMAT_AUTO)),
        ("lzma.FORMAT_ALONE", dict(format=lzma.FORMAT_ALONE)),
        ("lzma.FORMAT_XZ", dict(format=lzma.FORMAT_XZ)),
    ):
        try:
            return lzma.decompress(raw, **kwargs), name
        except lzma.LZMAError as e:
            errors.append(f"{name}: {e}")
    raise ValueError("all LZMA variants failed: " + " | ".join(errors))


def gcd_list(nums):
    g = 0
    for n in nums:
        g = math.gcd(g, n)
    return g


def decode_records(payload, stride=STRIDE_CANDIDATE):
    """Decode payload into raw tuples (ms, int_a, int_b, vol_a, vol_b)."""
    if len(payload) % stride != 0:
        raise ValueError(f"payload length {len(payload)} not divisible by stride {stride}")
    n = len(payload) // stride
    out = []
    for i in range(n):
        rec = payload[i * stride:(i + 1) * stride]
        ms, ia, ib, va, vb = struct.unpack(">iii ff", rec)
        out.append((ms, ia, ib, va, vb))
    return out


def analyze_file(raw, file_hour_utc=None, scale=SCALE_CANDIDATE):
    payload, method = decompress_bi5(raw)
    res = {
        "compressed_bytes": len(raw),
        "payload_bytes": len(payload),
        "lzma_method": method,
        "stride": STRIDE_CANDIDATE,
        "stride_divisible": len(payload) % STRIDE_CANDIDATE == 0,
        "scale": scale,
        "ticks": 0,
        "ask_gt_bid": 0, "bid_gt_ask": 0, "bid_eq_ask": 0,
        "monotonic_violations": 0,
        "offset_out_of_hour_range": 0,
        "negative_offsets": 0,
        "duplicate_rows": 0,
        "nonpositive_price": 0,
        "price_min_ask": None, "price_max_ask": None,
        "price_min_bid": None, "price_max_bid": None,
        "vol_min": None, "vol_max": None,
    }
    if not res["stride_divisible"]:
        res["error"] = "stride mismatch; candidate rejected for this file"
        return res
    recs = decode_records(payload)
    res["ticks"] = len(recs)
    prev_ms = None
    seen_rows = set()
    min_ask = min_bid = None
    max_ask = max_bid = None
    vol_min = vol_max = None
    for ms, ia, ib, va, vb in recs:
        ask = ia / scale
        bid = ib / scale
        if ask > bid:
            res["ask_gt_bid"] += 1
        elif bid > ask:
            res["bid_gt_ask"] += 1
        else:
            res["bid_eq_ask"] += 1
        if ask <= 0 or bid <= 0:
            res["nonpositive_price"] += 1
        if prev_ms is not None and ms <= prev_ms:
            res["monotonic_violations"] += 1
        prev_ms = ms
        if ms < 0:
            res["negative_offsets"] += 1
        if ms < 0 or ms >= HOUR_MS:
            res["offset_out_of_hour_range"] += 1
        if (ms, ia, ib) in seen_rows:
            res["duplicate_rows"] += 1
        seen_rows.add((ms, ia, ib))
        min_ask = ask if min_ask is None else min(min_ask, ask)
        max_ask = ask if max_ask is None else max(max_ask, ask)
        min_bid = bid if min_bid is None else min(min_bid, bid)
        max_bid = bid if max_bid is None else max(max_bid, bid)
        vol_min = min(va, vb) if vol_min is None else min(vol_min, va, vb)
        vol_max = max(va, vb) if vol_max is None else max(vol_max, va, vb)
    res["price_min_ask"], res["price_max_ask"] = min_ask, max_ask
    res["price_min_bid"], res["price_max_bid"] = min_bid, max_bid
    res["vol_min"], res["vol_max"] = vol_min, vol_max
    res["orientation_measured"] = (
        "field@4 >= field@8 in majority -> field@4=ASK, field@8=BID"
        if res["ask_gt_bid"] >= res["bid_gt_ask"]
        else "field@8 > field@4 in majority -> field@8=ASK, field@4=BID"
    )
    return res


def build_fixture(tmp_path):
    """Synthetic .bi5 fixture with KNOWN records -> proves the tool decodes correctly."""
    recs = [
        (0, 1_100_010, 1_100_000, 1.5, 1.2),          # ask 11.0001, bid 11.0000 @ 1e5
        (1200, 1_100_020, 1_100_010, 2.0, 1.1),
        (2500, 1_100_005, 1_099_995, 0.5, 0.4),
        (3_599_999, 1_100_030, 1_100_025, 3.0, 2.5),  # last ms of the hour
    ]
    payload = b"".join(struct.pack(">iii ff", *r) for r in recs)
    raw = lzma.compress(payload, format=lzma.FORMAT_ALONE)
    with open(tmp_path, "wb") as f:
        f.write(raw)
    return raw, recs


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "fixture.bi5")
        raw, recs = build_fixture(p)
        with open(p, "rb") as f:
            data = f.read()
        assert data == raw
        res = analyze_file(data)
        checks = {
            "lzma_decode_ok": res["lzma_method"].startswith("lzma.FORMAT_"),
            "stride_divisible": res["stride_divisible"] is True,
            "tick_count": res["ticks"] == len(recs),
            "ask_gt_bid_count": res["ask_gt_bid"] == 4 and res["bid_gt_ask"] == 0,
            "bid_eq_ask_count": res["bid_eq_ask"] == 0,
            "monotonic_clean": res["monotonic_violations"] == 0,
            "offset_range_clean": res["offset_out_of_hour_range"] == 0,
            "price_scale_recovery": abs(res["price_min_ask"] - 11.00005) < 1e-6
            and abs(res["price_max_ask"] - 11.0003) < 1e-6
            and abs(res["price_min_bid"] - 10.99995) < 1e-6,
            "volume_recovery": abs(res["vol_min"] - 0.4) < 1e-6 and abs(res["vol_max"] - 3.0) < 1e-6,
            "duplicate_detection_zero": res["duplicate_rows"] == 0,
            "orientation_ask_first": "field@4=ASK" in res["orientation_measured"],
        }
        # also prove duplicate + monotonic detection fires on a bad stream
        bad = b"".join(struct.pack(">iii ff", *r) for r in [recs[0], recs[0], recs[1], recs[1]])
        res_bad = analyze_file(lzma.compress(bad, format=lzma.FORMAT_ALONE))
        checks["duplicate_detection_fires"] = res_bad["duplicate_rows"] == 2
        checks["monotonic_detection_fires"] = res_bad["monotonic_violations"] >= 2
        report = {
            "tool_selftest": "fixture-based; validates the DECODER ONLY, never the source",
            "fixture_records": len(recs),
            "checks": checks,
            "all_pass": all(checks.values()),
            "fixture_analysis": res,
        }
        print(json.dumps(report, indent=2))
        return 0 if report["all_pass"] else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        rc = selftest()
        if args.out:
            pass
        raise SystemExit(rc)
    if not args.files:
        print(json.dumps({
            "source_decode": "NOT_RUN",
            "reason": "no fetched .bi5 bytes exist in this lane (transport blocked); nothing decoded",
        }, indent=2))
        return
    report = {"files": []}
    for f in args.files:
        with open(f, "rb") as fh:
            raw = fh.read()
        try:
            res = analyze_file(raw)
        except Exception as e:
            res = {"file": f, "error": f"{type(e).__name__}: {e}"}
        res["file"] = f
        report["files"].append(res)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
