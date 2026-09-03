#!/usr/bin/env python
"""FOREX-FREE-V1: load canonical Twelve Data H1 windows into normalized bars
for the frozen family modules. Digest-verified against the committed probe
request manifest; fail-closed on any missing/unverified file or bad bar.
Raw files stay in gitignored storage; nothing here commits data."""
import hashlib, json, os
from datetime import datetime

PAIRS = ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CHF", "USD/CAD"]

def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def load_pair_h1(pair, data_root, request_manifest=None, quarantine_ceiling=0.001):
    """Ascending, unique, validated H1 bars for one pair from canonical
    1h window files under <data_root>/forex_free_v1/. When request_manifest
    is given, every window file's sha256 must match a recorded request entry
    (fail-closed UNVERIFIED_FILE otherwise). OHLC-inconsistent bars (provider
    rounding artifacts) are QUARANTINED — excluded with reason, never silently
    accepted; more than quarantine_ceiling fraction per pair fails closed."""
    tag = pair.replace("/", "")
    raw = os.path.join(data_root, "forex_free_v1")
    if not os.path.isdir(raw):
        raise ValueError(f"NO_RAW_DIR: {raw}")
    names = sorted(f for f in os.listdir(raw)
                   if f.startswith(f"{tag}_1h_") and f.endswith("_a.json")
                   and "TRUNCATED" not in f)
    if not names:
        raise ValueError(f"NO_CANONICAL_FILES: {pair}")
    known = {r["sha256"] for r in request_manifest["requests"]} if request_manifest else None
    if request_manifest and "canonical_digest_ledger" in request_manifest:
        known = known | set(request_manifest["canonical_digest_ledger"]["digests"].values())
    rows, seen, quarantined = [], set(), []
    considered = 0
    for name in names:
        path = os.path.join(raw, name)
        if known is not None and sha256_file(path) not in known:
            raise ValueError(f"UNVERIFIED_FILE: {name}")
        j = json.loads(open(path).read())
        if isinstance(j, dict) and j.get("status") == "error":
            continue  # provider no-coverage window (e.g. before history start); recorded in the probe
        vals = j.get("values") if isinstance(j, dict) else None
        if vals is None:
            raise ValueError(f"BAD_WINDOW: {name}")
        for r in vals:
            dt = r.get("datetime")
            if dt in seen:
                continue  # boundary overlap between adjacent windows
            considered += 1
            try:
                bar = {"datetime": dt, "open": float(r["open"]), "high": float(r["high"]),
                       "low": float(r["low"]), "close": float(r["close"])}
                datetime.fromisoformat(dt)
            except (KeyError, TypeError, ValueError):
                raise ValueError(f"MALFORMED_BAR: {name} {dt}")
            if not (bar["high"] >= bar["low"] and bar["high"] >= bar["open"]
                    and bar["high"] >= bar["close"] and bar["low"] <= bar["open"]
                    and bar["low"] <= bar["close"] and bar["open"] > 0 and bar["close"] > 0):
                quarantined.append({"file": name, "bar": bar,
                                    "reason": "OHLC_INCONSISTENT_PROVIDER_ARTIFACT"})
                continue
            seen.add(dt)
            rows.append(bar)
    if considered and len(quarantined) / considered > quarantine_ceiling:
        raise ValueError(f"QUARANTINE_CEILING_EXCEEDED: {pair} {len(quarantined)}/{considered}")
    rows.sort(key=lambda r: r["datetime"])
    return rows, quarantined

def digest_bars(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()

def verify_against_coverage_audit(pair, rows, ctl_dir):
    """Cross-check loaded rows against the committed F2 coverage audit
    (first/last timestamps). Raises on mismatch."""
    from datetime import datetime as _dt
    tag = pair.replace("/", "")
    a = json.load(open(os.path.join(ctl_dir, f"audit_{tag}_1h.json")))
    got_f = rows[0]["datetime"][:16] if rows else None
    got_l = rows[-1]["datetime"][:16] if rows else None
    if got_f != a["first"][:16] or got_l != a["last"][:16]:
        raise ValueError(f"COVERAGE_MISMATCH: {pair} {got_f}..{got_l} vs {a['first']}..{a['last']}")
    return True
