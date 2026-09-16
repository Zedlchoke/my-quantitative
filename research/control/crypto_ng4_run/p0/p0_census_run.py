#!/usr/bin/env python
"""CRYPTO-NG4 P0 census lane (plan plans/PLAN_crypto_ng4.md section 4, F1-F7).

Role: A3/A8-P0, lane p0-census, cycle CRYPTO-NG4.

Gates implemented here:
  F1  panel + OI digest re-pin (S4 CADS store) + X1 shadow-battery byte
      re-pin from git (NG1 29-shape inventory blob, NG3 d2_verdict).
      Fail-closed: unresolvable X1 bytes => X1 NOT_RUN.
  F2  keyless fapi fundingRate re-proof per series (BTCUSDT/ETHUSDT/
      SOLUSDT): bounded recent window (~500 settlements), measured cadence
      interval histogram, boundary convention pinned. Network LIGHT:
      3 GETs, no key, no signature, no credential ever echoed.
  F3  symbol/pair census: 3 panels x 8,760 H1 rows; 3 pairs.
  F4  fold-boundary span census, fail-closed: first/last bar must measure
      2025-08-22T00:00Z .. 2026-08-21T23:00Z EXACTLY on every panel.
      ANY mismatch => verdict CRYPTO_NG4_BLOCKED_SOURCE_OR_SCHEMA;
      boundaries are never recomputed or shifted. Also pins SOL RV24
      regime constants (outcome-independent).
  F5  cost kernel contract re-pin reference (L-V14-0) pointing at the M0
      fixtures committed in this worktree.
  F6  reproducibility: the census is deterministic; a rerun is
      byte-identical (funding samples are read from the pinned bytes on
      rerun; only `--fetch-funding` touches the network).
  F7  prospective readiness note: FDF-V1 wire-format census paths listed;
      collectors NOT started by this lane.

Run:
  .venv/bin/python research/control/crypto_ng4_run/p0/p0_census_run.py \
      [--fetch-funding] [--store-root PATH]

Deterministic outputs (byte-identical across reruns):
  p0_verdict.json, p0_manifest.json, sol_rv24_constants.json,
  x1_inventory/manifest.json
Non-deterministic log (NOT part of the F6 comparison): p0_run_log.json
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # worktree root
P0_DIR = Path(__file__).resolve().parent
X1_DIR = P0_DIR / "x1_inventory"
FUNDING_DIR = P0_DIR / "funding"

DEFAULT_STORE_ROOT = "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store"

# --- Frozen plan constants (plans/PLAN_crypto_ng4.md section 4; NEVER shifted) --- #
PANEL_PINS = {
    "panel_BTCUSDT_h1.csv": "111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1",
    "panel_ETHUSDT_h1.csv": "ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b",
    "panel_SOLUSDT_h1.csv": "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107",
}
OI_PIN = "f26a61e45a0f79322140c66a1a8862b6d933e0a831d7559af459ef638fbefbd3"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
EXPECTED_ROWS = 8760  # 365 x 24 H1 bars
EXPECTED_FIRST_HOUR = "2025-08-22T00"
EXPECTED_LAST_HOUR = "2026-08-21T23"

X1_NG1_GIT_BLOB = "6411e6854c422214a92e5bdd0a11d0413659c5c1"
X1_NG1_BRANCH = "orca/crypto-ng1-integration"
X1_NG1_PATH = "research/control/crypto_ng1_run/d2/d2_novelty_panel_ng1.json"
X1_NG1_SHAPES = 29
X1_NG3_BRANCH = "orca/crypto-ng3-integration"
X1_NG3_PATH = "research/control/crypto_ng3_run/d2/d2_verdict.json"

FOLD_BOUNDARIES = {
    "panel_window_start": "2025-08-22T00:00Z",
    "panel_window_end": "2026-08-21T23:00Z",
    "first_decidable_day_index": 61,
    "folds": [
        {"fold": "FOLD-1", "start": "2025-10-22T00:00Z", "end": "2026-01-05T23:00Z"},
        {"fold": "FOLD-2", "start": "2026-01-06T00:00Z", "end": "2026-03-22T23:00Z"},
        {"fold": "FOLD-3", "start": "2026-03-23T00:00Z", "end": "2026-06-06T23:00Z"},
        {"fold": "FOLD-4", "start": "2026-06-07T00:00Z", "end": "2026-08-21T23:00Z"},
    ],
}

FUNDING_SAMPLE_LIMIT = 500
FAPI_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"

RV24_LOOKBACK_DAYS = 180
RV24_WINDOW = 24

# L-V14-0 cost kernel contract references committed in THIS worktree (F5).
COST_KERNEL = "L-V14-0"
COST_REFS = [
    "tests/test_crypto_ng4_m0_crypto_fixtures.py",
    "research/control/crypto_ng4_run/m0/contract_frozen.json",
    "research/control/crypto_ng4_run/m0/m0_contract.py",
    "plans/PLAN_crypto_ng4.md",
]

VERDICT_PASS = "PASS"
VERDICT_BLOCKED = "CRYPTO_NG4_BLOCKED_SOURCE_OR_SCHEMA"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# F1: panel re-pin + X1 byte re-pin
# --------------------------------------------------------------------------- #

def resolve_cads_object(store_root: str, address: str) -> Path:
    path = Path(store_root) / "objects" / address[:2] / address
    if not path.is_file():
        raise FileNotFoundError(f"CADS object absent: {address} at {path}")
    actual = sha256_file(path)
    if actual != address:
        raise ValueError(f"CADS integrity failure: {address} re-hashed to {actual}")
    return path


def f1_panels(store_root: str) -> dict:
    panels = {}
    for name, address in PANEL_PINS.items():
        path = resolve_cads_object(store_root, address)
        text = path.read_text(encoding="utf-8")
        lines = text.strip().split("\n")
        header = lines[0].split(",")
        rows = lines[1:]
        sym_col = header.index("symbol")
        hour_col = header.index("hour_utc")
        symbols_in_file = {r.split(",")[sym_col] for r in rows}
        if len(symbols_in_file) != 1:
            raise ValueError(
                f"panel {name} contains multiple symbols: {sorted(symbols_in_file)}"
            )
        sym = symbols_in_file.pop()
        hours = [r.split(",")[hour_col] for r in rows]
        panels[sym] = {
            "pin_name": name,
            "address": address,
            "store_path": str(path),
            "bytes": path.stat().st_size,
            "rows": len(rows),
            "first_hour": hours[0],
            "last_hour": hours[-1],
        }
    oi_path = resolve_cads_object(store_root, OI_PIN)
    oi = json.loads(oi_path.read_text(encoding="utf-8"))
    oi_census = {k: len(v) for k, v in sorted(oi.items())}
    return {
        "panels": panels,
        "oi_series": {
            "address": OI_PIN,
            "store_path": str(oi_path),
            "bytes": oi_path.stat().st_size,
            "symbols": oi_census,
            "role": "NON_SCORED_D2_DIAGNOSTIC_ONLY",
        },
    }


def git_blob_bytes(branch: str, git_path: str) -> tuple[bytes, str]:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{branch}:{git_path}"],
        capture_output=True, check=True,
    ).stdout
    blob_id = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", f"{branch}:{git_path}"],
        capture_output=True, check=True, text=True,
    ).stdout.strip()
    return out, blob_id


def f1_x1_repins() -> dict:
    """Re-pin X1 shadow battery bytes from git. Fail-closed on any mismatch."""
    ng1_bytes, ng1_blob = git_blob_bytes(X1_NG1_BRANCH, X1_NG1_PATH)
    ng1 = json.loads(ng1_bytes)
    veto_panel = ng1["veto_panel"]
    if len(veto_panel) != X1_NG1_SHAPES:
        raise ValueError(
            f"X1 NG1 inventory: expected {X1_NG1_SHAPES} shapes, found {len(veto_panel)}"
        )
    if ng1_blob != X1_NG1_GIT_BLOB:
        raise ValueError(
            f"X1 NG1 git blob {ng1_blob} != pinned {X1_NG1_GIT_BLOB}"
        )

    ng3_bytes, ng3_blob = git_blob_bytes(X1_NG3_BRANCH, X1_NG3_PATH)
    ng3 = json.loads(ng3_bytes)

    X1_DIR.mkdir(parents=True, exist_ok=True)
    ng1_out = X1_DIR / "d2_novelty_panel_ng1.json"
    ng3_out = X1_DIR / "d2_verdict.json"
    ng1_out.write_bytes(ng1_bytes)
    ng3_out.write_bytes(ng3_bytes)

    x1 = {
        "ng1_inventory": {
            "source": f"{X1_NG1_BRANCH}:{X1_NG1_PATH}",
            "git_blob": ng1_blob,
            "pinned_path": str(ng1_out),
            "pinned_sha256": sha256_file(ng1_out),
            "bytes": len(ng1_bytes),
            "shapes": len(veto_panel),
            "schema": ng1.get("schema"),
            "cycle_id": ng1.get("cycle_id"),
        },
        "ng3_verdict": {
            "source": f"{X1_NG3_BRANCH}:{X1_NG3_PATH}",
            "git_blob": ng3_blob,
            "pinned_path": str(ng3_out),
            "pinned_sha256": sha256_file(ng3_out),
            "bytes": len(ng3_bytes),
            "schema": ng3.get("schema", ng3.get("task_id")),
            "cycle_id": ng3.get("cycle_id"),
        },
        "x1_status": "REPINNED",
    }
    write_json(X1_DIR / "manifest.json", x1)
    return x1


# --------------------------------------------------------------------------- #
# F2: funding re-proof (keyless, LIGHT: one GET per symbol)
# --------------------------------------------------------------------------- #

def fetch_funding(symbol: str) -> bytes:
    url = f"{FAPI_FUNDING_URL}?symbol={symbol}&limit={FUNDING_SAMPLE_LIMIT}"
    req = urllib.request.Request(url, headers={"User-Agent": "cng4-p0-census/1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"fapi HTTP {resp.status} for {symbol}")
        return resp.read()


def funding_proof(sample_bytes: bytes) -> dict:
    rows = json.loads(sample_bytes)
    times = [int(r["fundingTime"]) for r in rows]
    rates = [float(r["fundingRate"]) for r in rows]
    times_sorted = sorted(times)
    if times_sorted != times:
        raise ValueError(f"funding sample not time-ascending: {rows[0]['symbol']}")
    diffs_ms = [b - a for a, b in zip(times, times[1:])]
    interval_h = Counter(round(d / 3_600_000.0, 6) for d in diffs_ms)
    cadence_h = (
        8.0 if interval_h.get(8.0, 0) == len(diffs_ms)
        else max(interval_h.items(), key=lambda kv: kv[1])[0]
    )
    # Materiality: exchange stamps carry millisecond offsets (…001/…002),
    # so exact-key != 8.0 catches jitter. A stress adjustment (4h/1h) is a
    # MATERIAL deviation: more than 60s away from the nominal 8h.
    material = {
        str(k): v for k, v in sorted(interval_h.items())
        if abs(k - 8.0) * 3_600_000.0 > 60_000.0
    }
    rate_types = Counter(r.get("rateType", "MISSING") for r in rows)
    return {
        "settlements": len(rows),
        "first_funding_time_ms": times[0],
        "last_funding_time_ms": times[-1],
        "measured_cadence_hours_nominal": cadence_h,
        "interval_histogram_hours": {str(k): v for k, v in sorted(interval_h.items())},
        "material_non_8h_interval_counts": material,
        "rate_types": dict(sorted(rate_types.items())),
        "rate_min": min(rates),
        "rate_max": max(rates),
        "boundary_rule": "INCLUSIVE: a settlement timestamped exactly at entry or exit is charged (plan F2); sample timestamps pinned for later accounting",
    }


def f2_funding(fetch: bool) -> dict:
    FUNDING_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for sym in SYMBOLS:
        sample_path = FUNDING_DIR / f"{sym}_funding_sample.json"
        if fetch:
            raw = fetch_funding(sym)
            sample_path.write_bytes(raw)
        if not sample_path.is_file():
            raise FileNotFoundError(
                f"funding sample absent for {sym}; run with --fetch-funding"
            )
        raw = sample_path.read_bytes()
        proof = funding_proof(raw)
        out[sym] = {
            "pinned_path": str(sample_path),
            "pinned_sha256": sha256_bytes(raw),
            "bytes": len(raw),
            "source": FAPI_FUNDING_URL,
            "auth": "KEYLESS_PUBLIC",
            **proof,
        }
    return out


# --------------------------------------------------------------------------- #
# F4: SOL RV24 regime constants (outcome-independent)
# --------------------------------------------------------------------------- #

def percentile(sorted_vals, p: float) -> float:
    """Linear-interpolation percentile (numpy 'linear' method), independent impl."""
    n = len(sorted_vals)
    if n == 0:
        raise ValueError("empty series")
    if n == 1:
        return float(sorted_vals[0])
    pos = (n - 1) * (p / 100.0)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def sol_rv24_constants(panel_rows) -> dict:
    import math

    prices = [float(r["last_price"]) for r in panel_rows]
    cut = RV24_LOOKBACK_DAYS * 24  # 4320 H1 bars
    window_prices = prices[: cut + 1]
    rets = [
        math.log(b / a)
        for a, b in zip(window_prices, window_prices[1:])
    ]
    rvs = []
    acc = sum(r * r for r in rets[:RV24_WINDOW])
    rvs.append(math.sqrt(acc))
    for i in range(RV24_WINDOW, len(rets)):
        acc += rets[i] * rets[i] - rets[i - RV24_WINDOW] * rets[i - RV24_WINDOW]
        rvs.append(math.sqrt(acc))
    srt = sorted(rvs)
    p333 = percentile(srt, 33.3)
    p667 = percentile(srt, 66.7)
    p90 = percentile(srt, 90.0)
    labels = {"LOW": p333, "MID": p667, "HIGH": p90}
    return {
        "schema": "crypto_ng4_run/p0/sol_rv24_constants@1",
        "source_panel": "S4:binance-daily-h1-panels panel_SOLUSDT_h1.csv "
                        "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107",
        "price_field": "last_price",
        "lookback_days": RV24_LOOKBACK_DAYS,
        "definition": "trailing-24h RV = sqrt(sum of 24 squared hourly H1 log "
                      "returns) over the panel's first 180 days",
        "n_returns": len(rets),
        "n_rv": len(rvs),
        "rv_min": srt[0],
        "rv_max": srt[-1],
        "percentiles": {"P33.3": p333, "P66.7": p667, "P90": p90},
        "thresholds": labels,
        "label_rule": "rv <= P33.3 => LOW; <= P66.7 => MID; <= P90 => HIGH; "
                      "> P90 => STRESS",
        "role": "outcome-independent constants; no PnL or gate depends here",
    }


# --------------------------------------------------------------------------- #
# Main census
# --------------------------------------------------------------------------- #

def read_panel_rows(path: Path) -> list[dict]:
    import csv

    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def span_census(rows, expected_first: str, expected_last: str, expected_rows: int = EXPECTED_ROWS):
    """Fold-boundary span census for one panel (plan F4, fail-closed).

    Returns (per_panel_report, ok). ANY mismatch => ok False; boundaries
    are never recomputed or shifted.
    """
    first = rows[0]["hour_utc"]
    last = rows[-1]["hour_utc"]
    ok = len(rows) == expected_rows and first == expected_first and last == expected_last
    return {
        "rows": len(rows),
        "first_hour": first,
        "last_hour": last,
        "expected_first_hour": expected_first,
        "expected_last_hour": expected_last,
        "span_exact": ok,
    }, ok


def run(store_root: str, fetch_funding_flag: bool) -> int:
    incidents: list[str] = []
    f_gates: dict[str, str] = {}

    # ---- F1 ---- #
    x1_status = "REPINNED"
    try:
        f1 = f1_panels(store_root)
        x1 = f1_x1_repins()
        f_gates["F1"] = "PASS"
    except Exception as exc:  # fail-closed
        f1, x1 = {"panels": {}, "oi_series": {}}, {"x1_status": "NOT_RUN"}
        x1_status = "NOT_RUN"
        f_gates["F1"] = "FAIL"
        incidents.append(f"F1: {type(exc).__name__}: {exc}")
        f1["panels"] = {}
        verdict = {
            "schema": "crypto_ng4_run/p0/verdict@1",
            "cycle_id": "CRYPTO-NG4",
            "lane": "p0-census",
            "role": "A3/A8-P0",
            "verdict": VERDICT_BLOCKED,
            "gates": f_gates,
            "x1_status": x1_status,
            "incidents": incidents,
        }
        write_json(P0_DIR / "p0_verdict.json", verdict)
        return 1

    # ---- F3: symbol/pair census ---- #
    rows_by_symbol = {}
    f3 = {"symbols": [], "pairs": [], "panels": {}}
    for sym, meta in sorted(f1["panels"].items()):
        rows = read_panel_rows(Path(meta["store_path"]))
        rows_by_symbol[sym] = rows
        syms = {r["symbol"] for r in rows}
        f3["panels"][sym] = {
            "rows": len(rows),
            "symbols_in_panel": sorted(syms),
            "columns": sorted(rows[0].keys()),
        }
        f3["symbols"].append(sym)
    f3["pairs"] = [f"{a}-{b}" for a, b in itertools.combinations(SYMBOLS, 2)]
    f3["panel_rows_expected"] = EXPECTED_ROWS

    # ---- F4: fold-boundary span census (fail-closed) ---- #
    span = {}
    f4_ok = True
    for sym, rows in sorted(rows_by_symbol.items()):
        report, ok = span_census(rows, EXPECTED_FIRST_HOUR, EXPECTED_LAST_HOUR)
        span[sym] = report
        f4_ok = f4_ok and ok

    sol_constants = None
    try:
        sol_constants = sol_rv24_constants(rows_by_symbol["SOLUSDT"])
        # Hand-check one value: independent recompute of P66.7 via numpy.
        import math

        import numpy as np

        prices = [float(r["last_price"]) for r in rows_by_symbol["SOLUSDT"]]
        rets = np.diff(np.log(np.array(prices[: RV24_LOOKBACK_DAYS * 24 + 1])))
        rvs_np = np.sqrt(
            np.convolve(rets * rets, np.ones(RV24_WINDOW), mode="valid")
        )
        p667_np = float(np.percentile(rvs_np, 66.7))
        if abs(p667_np - sol_constants["percentiles"]["P66.7"]) > 1e-12:
            raise ValueError(
                f"RV24 hand-check mismatch: numpy {p667_np} vs impl "
                f"{sol_constants['percentiles']['P66.7']}"
            )
        sol_constants["hand_check"] = {
            "method": "numpy.percentile(66.7) on numpy-recomputed RV series",
            "value": p667_np,
            "abs_diff": abs(p667_np - sol_constants["percentiles"]["P66.7"]),
            "agree": True,
        }
    except Exception as exc:
        f4_ok = False
        incidents.append(f"F4 sol_rv24: {type(exc).__name__}: {exc}")
    if sol_constants is not None:
        write_json(P0_DIR / "sol_rv24_constants.json", sol_constants)

    if f4_ok:
        f_gates["F4"] = "PASS"
    else:
        f_gates["F4"] = "FAIL"

    # ---- F2: funding ---- #
    try:
        funding = f2_funding(fetch_funding_flag)
        f_gates["F2"] = "PASS"
    except Exception as exc:
        funding = {}
        f_gates["F2"] = "FAIL"
        incidents.append(f"F2: {type(exc).__name__}: {exc}")

    # ---- F5: cost kernel reference re-pin ---- #
    cost_refs = []
    for rel in COST_REFS:
        p = REPO_ROOT / rel
        cost_refs.append(
            {
                "path": rel,
                "exists": p.is_file(),
                "sha256": sha256_file(p) if p.is_file() else None,
            }
        )
    f5 = {
        "kernel": COST_KERNEL,
        "law": "cost charged exactly once per fill (4 fills per round trip), "
               "measured taker + half-spread; stress multiplier 2.0 on booked "
               "PnL; costs broken out fills vs holding; funding as a cost line "
               "only (complete per F2)",
        "references": cost_refs,
    }
    f_gates["F5"] = "PASS" if all(r["exists"] for r in cost_refs) else "FAIL"

    # ---- F7: prospective readiness (this lane starts NO collectors) ---- #
    f7 = {
        "prospective_sources": ["Coinbase", "Kraken", "Deribit"],
        "status": "D2_NON_SCORED_CONTROLS_ONLY",
        "wire_format_census_paths": [
            "research/control/crypto_ng4_run/p0/p0_verdict.json#F7",
            "research/control/ng6_ng7_ng4_dossiers_2026-09/"
            "cng4-a3-prospective-contract-dossier.json",
        ],
        "collectors_started_by_this_lane": False,
        "note": "nothing prospective ever joins history; collection contract "
                "frozen in the A3 dossier (FDF-V1 measured census is a D2 "
                "downstream task, NOT this lane's scope)",
    }
    f_gates["F7"] = "PASS"

    # ---- Verdict ---- #
    verdict = VERDICT_PASS if all(v == "PASS" for v in f_gates.values()) else VERDICT_BLOCKED
    if x1_status != "REPINNED":
        verdict = VERDICT_BLOCKED

    f3["symbols"] = sorted(f3["symbols"])
    f3["pairs"] = sorted(set(f3["pairs"]))
    f3["n_pairs"] = len(f3["pairs"])

    manifest = {
        "schema": "crypto_ng4_run/p0/manifest@1",
        "cycle_id": "CRYPTO-NG4",
        "lane": "p0-census",
        "base_sha_expected": "3524509d5ac2213dd083e4341b1152af8e5e0833",
        "store_root": store_root,
        "f1_panels_oi": f1,
        "f1_x1_inventory": x1,
        "f2_funding": funding,
        "f3_census": f3,
        "f4_fold_boundaries": FOLD_BOUNDARIES,
        "f4_span_census": span,
        "f5_cost_kernel": f5,
        "f7_prospective": f7,
    }
    write_json(P0_DIR / "p0_manifest.json", manifest)

    verdict_doc = {
        "schema": "crypto_ng4_run/p0/verdict@1",
        "cycle_id": "CRYPTO-NG4",
        "lane": "p0-census",
        "role": "A3/A8-P0",
        "verdict": verdict,
        "gates": dict(sorted(f_gates.items())),
        "x1_status": x1_status,
        "f1_panels": {s: m["address"] for s, m in sorted(f1["panels"].items())},
        "f1_oi_address": f1["oi_series"].get("address"),
        "f3": {"symbols": f3["symbols"], "n_pairs": f3["n_pairs"], "pairs": f3["pairs"]},
        "f4_fold_boundaries": FOLD_BOUNDARIES,
        "f4_span_exact_all_panels": f4_ok,
        "f2_funding_digests": {s: funding[s]["pinned_sha256"] for s in sorted(funding)},
        "f5_cost_kernel": COST_KERNEL,
        "f7_collectors_started": False,
        "incidents": incidents,
    }
    write_json(P0_DIR / "p0_verdict.json", verdict_doc)
    write_json(P0_DIR / "p0_run_log.json", {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fetch_funding": fetch_funding_flag,
        "verdict": verdict,
        "note": "non-deterministic provenance log; NOT part of the F6 "
                "byte-identical comparison",
    })
    print(json.dumps({"verdict": verdict, "gates": verdict_doc["gates"]}, indent=1))
    return 0 if verdict == VERDICT_PASS else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--store-root", default=DEFAULT_STORE_ROOT)
    ap.add_argument("--fetch-funding", action="store_true")
    args = ap.parse_args()
    sys.exit(run(args.store_root, args.fetch_funding))
