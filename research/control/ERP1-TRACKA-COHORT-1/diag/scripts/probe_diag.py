"""DIAG byte probe: pip / price scale / tradability band FROM BYTES.

Same derivation law as the cycle's committed scripts/probe_pair.py (the
authoritative method), adapted to M1 BID/ASK day candles only — the
diagnostic sources carry no tick files (limitation recorded in the probe
report: no tick-vs-candle cross-check exists here; the census OHLC
invariants and the 24-byte layout assertions are the invariants
available on this corpus).

Method (identical to probe_pair.derive_scale):
  price scale : unique s in {1e3,1e4,1e5,1e6} with median(raw mid)/s
                inside the registered guard band AND sane spread-in-pips
                ([0.05, 20]) AND sane point ([1e-6, 1e-3]);
  point / pip : point = 1/scale; pip = 10 x point (byte-derived);
  band        : union(probe min*0.80 floor-to-pip, probe max*1.20
                ceil-to-pip, registered guard).

Probe window: 2024-10-26..2024-11-06 — the cycle's precedent window
(EU DST end 2024-10-27, US DST end 2024-11-03, two weekend rollovers),
inside the copied corpus.

Reads ONLY the diag namespace (sha-verified copies). Writes
diag/data_local/derived/probe_{SYM}.json and, on PROBE_PASS for a pair,
updates pair_configs_diag.json (fail-closed consumers).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import lzma
import math
import sys
from pathlib import Path

import numpy as np

DIAG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIAG / "scripts"))

from pair_config_diag import CONFIG_PATH, REGISTERED_GUARDS  # noqa: E402

RAW = DIAG / "data_local"
DERIVED = DIAG / "data_local" / "derived"
CANDLE_DTYPE = np.dtype([("sec", ">i4"), ("o", ">i4"), ("c", ">i4"),
                         ("l", ">i4"), ("h", ">i4"), ("v", ">f4")])
assert CANDLE_DTYPE.itemsize == 24

PROBE_START, PROBE_END = dt.date(2024, 10, 26), dt.date(2024, 11, 6)
CANDIDATE_SCALES = (1e3, 1e4, 1e5, 1e6)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def daterange(a: dt.date, b: dt.date):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def load_day(pair: str, side: str, name: str, man: dict) -> np.ndarray:
    """Sha-verify against the copied manifest, decode 24B records."""
    path = RAW / pair / side / name
    raw = path.read_bytes()
    key = f"M1/{side}/{name}"
    entry = man["files"].get(key)
    if entry is None or entry.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise SystemExit(f"FAIL_CLOSED manifest mismatch: {pair}/{key}")
    plain = lzma.decompress(raw)
    if len(plain) % CANDLE_DTYPE.itemsize:
        raise SystemExit(
            f"FAIL_CLOSED {pair}/{key}: decompressed len {len(plain)} not "
            f"multiple of {CANDLE_DTYPE.itemsize}")
    return np.frombuffer(plain, dtype=CANDLE_DTYPE)


def derive_scale(raw_mids, raw_spread, guard):
    med = float(np.median(raw_mids))
    spread_med = float(np.median(raw_spread))
    hits = []
    for s in CANDIDATE_SCALES:
        p_med = med / s
        if not (guard["band_lo"] <= p_med <= guard["band_hi"]):
            continue
        point = 1.0 / s
        pip = 10.0 * point
        spread_pips = spread_med / 10.0  # scale-free identity, kept explicit
        if not (0.05 <= spread_pips <= 20.0):
            continue
        if not (1e-6 <= point <= 1e-3):
            continue
        hits.append({"scale": s, "median_price": p_med, "point": point,
                     "pip": pip, "spread_pips_median": spread_pips})
    if len(hits) != 1:
        return None, hits
    return hits[0], hits


def probe_symbol(pair: str) -> dict:
    guard = REGISTERED_GUARDS[pair]
    man = json.loads((RAW / pair / "m1_manifest.json").read_text())
    rep = {
        "schema": "diag_probe@1",
        "symbol": pair,
        "window": [PROBE_START.isoformat(), PROBE_END.isoformat()],
        "window_rationale": (
            "cycle precedent window: EU DST end 2024-10-27 + US DST end "
            "2024-11-03 + two weekend rollovers"),
        "registered_guard": guard,
        "method_note": (
            "M1-candle-only probe (no tick corpus in the diagnostic "
            "sources): scale/pip/band derivation identical to "
            "probe_pair.derive_scale; the tick-vs-candle cross-check of "
            "the ancestor probe is NOT available here — recorded as a "
            "known limitation (FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK)"),
        "files": {},
        "days_missing": [],
        "layout": {"candle_files": 0, "candle_len_mod24_violations": 0},
        "ohlc_invariants": {"m1_checked": 0, "violations": 0},
        "scale_candidates": None,
        "band_derivation": None,
        "verdict": "PROBE_FAIL",
    }
    all_ask, all_bid = [], []
    for day in daterange(PROBE_START, PROBE_END):
        name = f"{day.isoformat()}.bi5"
        day_data = {}
        for side in ("BID", "ASK"):
            path = RAW / pair / side / name
            if not path.exists():
                rep["days_missing"].append(f"{day}:{side}")
                continue
            raw = path.read_bytes()
            entry = man["files"].get(f"M1/{side}/{name}")
            if entry is None or entry.get("sha256") != \
                    hashlib.sha256(raw).hexdigest():
                raise SystemExit(f"FAIL_CLOSED probe sha mismatch {pair}/{side}/{name}")
            rep["files"][f"M1/{side}/{name}"] = {
                "sha256": entry["sha256"], "bytes": entry["bytes"]}
            plain = lzma.decompress(raw)
            if len(plain) % CANDLE_DTYPE.itemsize:
                rep["layout"]["candle_len_mod24_violations"] += 1
                continue
            recs = np.frombuffer(plain, dtype=CANDLE_DTYPE)
            rep["layout"]["candle_files"] += 1
            day_data[side] = recs
            for sec, o, c, lo, hi, _v in recs:
                if not (lo <= min(o, c) and hi >= max(o, c) and lo <= hi):
                    rep["ohlc_invariants"]["violations"] += 1
                rep["ohlc_invariants"]["m1_checked"] += 1
        if "BID" in day_data and "ASK" in day_data:
            n = min(len(day_data["BID"]), len(day_data["ASK"]))
            b, a = day_data["BID"][:n], day_data["ASK"][:n]
            m = (a["o"].astype(np.int64) + b["o"].astype(np.int64)) / 2.0
            all_bid.extend(b["o"].astype(np.int64).tolist())
            all_ask.extend(a["o"].astype(np.int64).tolist())
            if n:
                all_bid.extend(b["c"].astype(np.int64).tolist())
                all_ask.extend(a["c"].astype(np.int64).tolist())
    if not all_bid:
        return rep
    bid = np.array(all_bid, dtype=np.int64)
    ask = np.array(all_ask, dtype=np.int64)
    mids = (ask + bid) / 2.0
    spreads = ask - bid
    hit, cands = derive_scale(mids, spreads, guard)
    rep["scale_candidates"] = {"accepted": hit, "all": cands}
    if hit is None:
        return rep
    scale, pip = hit["scale"], hit["pip"]

    probe_min = float(mids.min()) / scale
    probe_max = float(mids.max()) / scale

    def floor_pip(x):
        return math.floor(x / pip - 1e-9) * pip

    def ceil_pip(x):
        return math.ceil(x / pip + 1e-9) * pip

    band_lo = min(floor_pip(probe_min * 0.80), guard["band_lo"])
    band_hi = max(ceil_pip(probe_max * 1.20), guard["band_hi"])
    rep["band_derivation"] = {
        "method": ("union(probe min*0.80 floor-to-pip, probe max*1.20 "
                   "ceil-to-pip, registered guard)"),
        "probe_min_price": probe_min, "probe_max_price": probe_max,
        "pad_relative": 0.20,
        "band_lo": round(band_lo, 10), "band_hi": round(band_hi, 10),
        "covers_guard": bool(band_lo <= guard["band_lo"]
                             and band_hi >= guard["band_hi"]),
        "all_probe_prices_inside_band": bool(
            probe_min / pip >= band_lo / pip - 1e-9
            and probe_max / pip <= band_hi / pip + 1e-9),
    }
    ok = (
        rep["layout"]["candle_len_mod24_violations"] == 0
        and rep["ohlc_invariants"]["violations"] == 0
        and not rep["days_missing"]
        and rep["band_derivation"]["covers_guard"]
        and rep["band_derivation"]["all_probe_prices_inside_band"]
    )
    rep["derivation"] = {
        "price_scale": scale, "point_price_units": 1.0 / scale,
        "pip_price_units": pip,
        "pip_method": ("pip = 10 x point (byte-derived; EURUSD precedent "
                       "10x1e-5=1e-4)"),
        "proven": bool(ok),
    }
    rep["verdict"] = "PROBE_PASS" if ok else "PROBE_FAIL"
    return rep


def main() -> int:
    DERIVED.mkdir(parents=True, exist_ok=True)
    configs = {}
    if CONFIG_PATH.exists():
        configs = json.loads(CONFIG_PATH.read_text())
    all_ok = True
    for pair in sys.argv[1:] or list(REGISTERED_GUARDS):
        rep = probe_symbol(pair)
        out = DERIVED / f"probe_{pair}.json"
        out.write_text(json.dumps(rep, indent=1))
        d = rep.get("derivation", {})
        bd = rep.get("band_derivation") or {}
        print(json.dumps({
            "pair": pair, "verdict": rep["verdict"],
            "scale": d.get("price_scale"), "pip": d.get("pip_price_units"),
            "band": [bd.get("band_lo"), bd.get("band_hi")],
            "probe_min_max": [bd.get("probe_min_price"), bd.get("probe_max_price")],
            "ohlc_violations": rep["ohlc_invariants"]["violations"],
            "out": str(out)}))
        if rep["verdict"] != "PROBE_PASS":
            all_ok = False
            continue
        configs[pair] = {
            "symbol": pair,
            "pip": d["pip_price_units"],
            "price_scale": d["price_scale"],
            "band_lo": bd["band_lo"],
            "band_hi": bd["band_hi"],
            "derivation": {
                "proven": True,
                "probe_report": str(out.relative_to(DIAG)),
                "probe_report_sha256": sha256_file(out),
                "method_scale": ("unique guard-band candidate in "
                                 "{1e3,1e4,1e5,1e6}"),
                "method_pip": d["pip_method"],
                "method_band": bd["method"],
                "window": rep["window"],
                "registered_guard": rep["registered_guard"],
                "probe_min_price": bd["probe_min_price"],
                "probe_max_price": bd["probe_max_price"],
                "candle_only_probe": True,
            },
        }
    CONFIG_PATH.write_text(json.dumps(configs, indent=1))
    return 0 if all_ok else 3


if __name__ == "__main__":
    sys.exit(main())
