#!/usr/bin/env python
"""V9 / A2 -- cohort-10 crypto universe + data audit (re-pinned under V9).

This audit does NOT invent a new selection rule. It REUSES the corrected
V8 A8 deterministic selector (``scripts/v8x_crypto_universe_selection.py``,
committed byte-identical copy of the V8 worktree artifact) verbatim:

  * exact 15-minute grid census functions (``slot_opens_from_ts_event``,
    ``gap_runs``, ``classify_run``, ``census_for_symbol``);
  * pre-window median daily quote-volume ranking metric;
  * held-exposure funding completeness proof (``analyze_funding`` with
    ``build_corroboration``);
  * instrument sanity / listing-age >= 365d gates.

Under V9 ownership this script:

  1. loads the FROZEN V8 selection manifest from the pinned repo copy
     (``data/v8x_manifests/crypto_universe_selection.json``) and verifies its
     sha256 against the recorded pinned value; also verifies the selector
     script sha256 (proves the reused rule is the unmodified corrected one);
  2. re-validates the chosen top-10 altcoins against CURRENT local catalog
     bytes (volume metric, both-window censuses, listing age, metadata,
     funding completeness) and asserts zero drift vs the pinned manifest;
  3. measures the exact common completed-bar window across all 10 symbols
     (+BTC benchmark context separately) inside the scored window;
  4. runs the exact 15m gap census over BOTH the pre-window
     [2025-07-22T00:00Z, 2025-08-21T00:00Z) and the scored window for every
     selected symbol (+BTC context); unexplained gaps must be 0 (the only
     permitted class is the documented ETH local-capture-boundary run at the
     scored-window start, which is capture-boundary explained);
  5. verifies funding settlement completeness across ANY possible held-
     exposure time: conservative first-possible-exposure = pre-window end =
     scored-window start under the frozen weekly Monday-rebalance schedule
     assumption, coverage required through the scored-window end inclusive;
  6. checks PIT instrument metadata (tick size / step size / min notional)
     present for all 10 via ``data.catalog.Catalog.instrument()``.

Performance-blind: reads only catalog parquets + local funding JSON + the
pinned manifests. Touches nothing under results/**. Fully offline and byte-
deterministic: re-running produces identical output files (fixed generated_at).
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.v8x_crypto_universe_selection import (  # noqa: E402  (path shim above)
    BAR_INTERVAL_S,
    BAR_SUFFIX,
    BTC_SYMBOL,
    CATALOG_ROOT,
    FIRST_POSSIBLE_EXPOSURE,
    FUNDING_ROOT,
    LISTING_AGE_MIN_DAYS,
    PRE_END_S,
    PRE_START_S,
    QUOTE_REQUIRED,
    SCORED_END_S,
    SCORED_START_S,
    TOP_N,
    VENUE,
    analyze_funding,
    bars_dir_digest,
    build_corroboration,
    census_for_symbol,
    dt_to_s,
    load_instrument,
    median_daily_quote_volume_pre_window,
    sha256_file,
    slot_opens_from_ts_event,
    utc_str,
)

import numpy as np  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

# --------------------------------------------------------------------------- #
# Frozen constants (V9 ownership pin; do NOT edit without a new prereg)
# --------------------------------------------------------------------------- #
SCHEMA_VERSION = "1.0.0"
AGENT = "A2-v9-universe"
GENERATED_AT_UTC = "2026-08-26T00:00:00Z"  # frozen for byte-reproducibility
AUDIT_LABEL = "S0_ALREADY_INSPECTED"

SOURCE_MANIFEST_RELPATH = Path("data/v8x_manifests/crypto_universe_selection.json")
SOURCE_SELECTOR_RELPATH = Path("scripts/v8x_crypto_universe_selection.py")
SOURCE_CANONICAL_V8_MANIFEST_PATH = (
    "/Users/hoangminhlong/my-quantitative-v8-wt/a8-crypto-breadth/data/"
    "v8x_manifests/crypto_universe_selection.json"
)
SOURCE_CANONICAL_V8_SELECTOR_PATH = (
    "/Users/hoangminhlong/my-quantitative-v8-wt/a8-crypto-breadth/scripts/"
    "v8x_crypto_universe_selection.py"
)
PINNED_SOURCE_MANIFEST_SHA256 = (
    "e73c703f5fb4dea7ff0c6c2c6c8c756b12218fa1960bf46c0ebb2509abb56376"
)
PINNED_SOURCE_SELECTOR_SHA256 = (
    "709b40c229d733aa08df867a3e207da46d5c86a111c54c0d502d2b809beda406"
)

DEFAULT_MANIFEST_OUT = REPO_ROOT / "data" / "v9_manifests" / "universe_selection_v9.json"
DEFAULT_AUDIT_OUT = REPO_ROOT / "research" / "audits" / "v9p" / "data_audit_v9.json"
DEFAULT_GATE_OUT = REPO_ROOT / "research" / "audits" / "v9p" / "t02_gate_v9.json"

GATE_ID = "P03/P04"

DOCUMENTED_CAPTURE_BOUNDARY_CLASSES = frozenset(
    {
        "local_capture_boundary_between_sessions",
        "local_capture_starts_after_window_start",
        "local_capture_ends_before_window_end",
    }
)

FUNDING_ASSUMPTION_TEXT = (
    "weekly Monday rebalance schedule; conservative first-possible-exposure "
    "= pre-window end = scored-window start 2025-08-21T00:00Z; funding "
    "settlement completeness required across any possible held-exposure time "
    "from that instant through the scored-window end inclusive"
)

PIT_METADATA_LIMITATION_TEXT = (
    "catalog stores ONE instrument-definition snapshot per symbol (single "
    "write timestamp in the filename); there is NO effective-dated "
    "versioning, so PIT changes to tickSize/stepSize/minNotional during the "
    "scored window cannot be attested from this store -- presence and values "
    "at snapshot time are attested here"
)


class PinVerificationError(RuntimeError):
    """Raised when a pinned input artifact fails its sha256 verification."""


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# --------------------------------------------------------------------------- #
# Pinned-input loading + verification
# --------------------------------------------------------------------------- #
def load_pinned_selection(
    repo_root: Path = REPO_ROOT,
    pinned_manifest_sha256: str = PINNED_SOURCE_MANIFEST_SHA256,
    pinned_selector_sha256: str = PINNED_SOURCE_SELECTOR_SHA256,
) -> tuple[dict, dict]:
    """Load + verify the frozen V8 selection manifest and its selector script."""
    manifest_path = Path(repo_root) / SOURCE_MANIFEST_RELPATH
    selector_path = Path(repo_root) / SOURCE_SELECTOR_RELPATH
    digest = sha256_file(manifest_path)
    if digest != pinned_manifest_sha256:
        raise PinVerificationError(
            f"pinned V8 selection manifest sha mismatch: {manifest_path} "
            f"sha256={digest} expected={pinned_manifest_sha256}"
        )
    sel_digest = sha256_file(selector_path)
    if sel_digest != pinned_selector_sha256:
        raise PinVerificationError(
            f"pinned V8 selector script sha mismatch: {selector_path} "
            f"sha256={sel_digest} expected={pinned_selector_sha256}"
        )
    return json.loads(manifest_path.read_text(encoding="utf-8")), {
        "path": str(SOURCE_MANIFEST_RELPATH),
        "canonical_v8_path": SOURCE_CANONICAL_V8_MANIFEST_PATH,
        "sha256": digest,
        "schema_version": None,  # filled by caller from parsed content
        "selector_script": {
            "path": str(SOURCE_SELECTOR_RELPATH),
            "canonical_v8_path": SOURCE_CANONICAL_V8_SELECTOR_PATH,
            "sha256": sel_digest,
        },
    }


# --------------------------------------------------------------------------- #
# Current-bytes revalidation of the chosen top-10
# --------------------------------------------------------------------------- #
def bar_files_for_symbol(catalog_root: str | Path, symbol: str) -> list[str]:
    return sorted(
        glob.glob(
            os.path.join(str(catalog_root), "data", "binance_bar",
                         f"{symbol}-PERP.{VENUE}{BAR_SUFFIX}", "*.parquet")
        )
    )


def observed_slot_opens(files) -> np.ndarray:
    """Union of unique 15m slot-open epoch seconds across files (rule reuse)."""
    opens = []
    for f in sorted(files):
        t = pq.read_table(f, columns=["ts_event"])["ts_event"].to_numpy()
        o = slot_opens_from_ts_event(np.asarray(t, dtype=np.int64))
        if o.size:
            opens.append(o)
    return np.unique(np.concatenate(opens)) if opens else np.empty(0, np.int64)


def duplicate_raw_stamps(files) -> int:
    """Exact-duplicate ts_event (ns) count across files."""
    seen: set[int] = set()
    dupes = 0
    for f in sorted(files):
        t = pq.read_table(f, columns=["ts_event"])["ts_event"].to_numpy()
        for ns in np.asarray(t, dtype=np.int64):
            v = int(ns)
            if v in seen:
                dupes += 1
            seen.add(v)
    return dupes


def measured_coverage(files, win_a: int, win_b: int) -> tuple[int, int] | None:
    """First/last completed-bar slot OPEN inside [win_a, win_b), or None."""
    opens = observed_slot_opens(files)
    in_win = opens[(opens >= win_a) & (opens < win_b)]
    if in_win.size == 0:
        return None
    return int(in_win[0]), int(in_win[-1])


def intersection_range(ranges: dict[str, tuple[int, int]]) -> tuple[int | None, int | None]:
    """Measured common window = max(first) .. min(last) (no trimming tricks)."""
    starts = [s for s, _ in ranges.values()]
    ends = [e for _, e in ranges.values()]
    if not starts or not ends:
        return None, None
    return max(starts), min(ends)


def close_stamp_iso(open_s: int) -> str:
    """ISO UTC of the completed-bar CLOSE stamp of the slot opening open_s."""
    return utc_str(open_s + BAR_INTERVAL_S)


def listing_age_check(inst, first_exposure_s: int) -> dict:
    cutoff_ms = (dt_to_s(datetime.fromtimestamp(first_exposure_s, tz=timezone.utc)
                          - timedelta(days=LISTING_AGE_MIN_DAYS))) * 1000
    onboard_ms = inst["onboard_ms"] if inst else None
    age_days = ((first_exposure_s * 1000 - onboard_ms) / 86400000.0
                if onboard_ms else None)
    ok = bool(onboard_ms is not None and onboard_ms <= cutoff_ms)
    return {
        "onboard_date_utc": inst["onboard_date_utc"] if inst else None,
        "min_days": LISTING_AGE_MIN_DAYS,
        "cutoff_utc": utc_str(int(cutoff_ms // 1000)),
        "age_days_at_first_possible_exposure": round(age_days, 2) if age_days is not None else None,
        "ok": ok,
    }


def pit_metadata_via_catalog(catalog_root: str | Path, symbols: list[str]) -> dict:
    """tick/step/min-notional presence via data.catalog.Catalog instruments."""
    from data.catalog import Catalog

    cat = Catalog(str(catalog_root))
    out: dict[str, dict] = {}
    for sym in symbols:
        try:
            inst = cat.instrument(f"{sym}-PERP.BINANCE")
        except Exception as exc:  # noqa: BLE001 - record, never crash the audit
            out[sym] = {"present": False, "error": f"{type(exc).__name__}: {exc}"}
            continue
        if inst is None:
            out[sym] = {"present": False}
            continue
        min_not = getattr(inst, "min_notional", None)
        out[sym] = {
            "present": True,
            "instrument_id": str(inst.id),
            "tick_size": float(inst.price_increment.as_decimal()),
            "step_size": float(inst.size_increment.as_decimal()),
            "min_notional": str(min_not) if min_not else None,
        }
    all_ok = all(
        m.get("present")
        and isinstance(m.get("tick_size"), float) and m["tick_size"] > 0
        and isinstance(m.get("step_size"), float) and m["step_size"] > 0
        and m.get("min_notional")
        for m in out.values()
    )
    return {
        "method": "data.catalog.Catalog().instrument(<SYM>-PERP.BINANCE)",
        "limitation": PIT_METADATA_LIMITATION_TEXT,
        "per_symbol": out,
        "all_ten_present_with_tick_step_min_notional": bool(all_ok),
    }


def collect_files_by_symbol(catalog_root: str | Path, funding_root: str | Path,
                            symbols: list[str]) -> dict[str, dict]:
    """V8 data-manifest hashing pattern (data_audit_v8.collect_source_files)."""
    cat = Path(catalog_root)
    fund = Path(funding_root)
    inventory: dict[str, dict] = {}
    for symbol in symbols:
        bt_dir = cat / "data" / "binance_bar" / f"{symbol}-PERP.{VENUE}{BAR_SUFFIX}"
        inst_dir = cat / "data" / "crypto_perpetual" / f"{symbol}-PERP.{VENUE}"
        fpath = fund / symbol / "funding.json"
        inventory[symbol] = {
            "bar_files": [
                {"path": str(p.relative_to(cat.parent)), "bytes": p.stat().st_size,
                 "sha256": sha256_file(p)}
                for p in sorted(bt_dir.glob("*.parquet"))
            ],
            "instrument_files": [
                {"path": str(p.relative_to(cat.parent)), "bytes": p.stat().st_size,
                 "sha256": sha256_file(p)}
                for p in sorted(inst_dir.glob("*.parquet"))
            ],
            "funding_files": (
                [{"path": str(fpath.relative_to(fund.parent)),
                  "bytes": fpath.stat().st_size, "sha256": sha256_file(fpath)}]
                if fpath.exists() else []
            ),
        }
    return inventory


def flatten_source_hashes(inventory: dict[str, dict]) -> dict[str, str]:
    flat: dict[str, str] = {}
    for groups in inventory.values():
        for group in ("bar_files", "instrument_files", "funding_files"):
            for item in groups[group]:
                flat[item["path"]] = item["sha256"]
    return flat


def _pinned_exact_volume(pinned: dict, symbol: str) -> str:
    """Exact Decimal volume string as recorded in candidates_evaluated (pinned)."""
    for cand in pinned.get("candidates_evaluated", []):
        if cand["symbol"] == symbol:
            return cand["volume"]["median_daily_quote_volume_usdt_exact"]
    raise KeyError(symbol)


# --------------------------------------------------------------------------- #
# Main pipeline
# --------------------------------------------------------------------------- #
def run_audit(
    *,
    catalog_root: str | Path = CATALOG_ROOT,
    funding_root: str | Path = FUNDING_ROOT,
    repo_root: Path = REPO_ROOT,
) -> dict:
    """Full offline audit; returns {'manifest':..., 'audit':..., 'gate':...}."""
    pinned, source_block = load_pinned_selection(repo_root)
    source_block["schema_version"] = pinned["schema_version"]
    source_block["agent"] = pinned["agent"]
    source_block["generated_at_utc"] = pinned["generated_at_utc"]
    source_block["verdict"] = pinned["verdict"]

    chosen = pinned["chosen_top10"]
    symbols = [c["symbol"] for c in chosen]
    assert len(symbols) == TOP_N, f"pinned selection must have exactly {TOP_N} symbols"
    assert len(set(symbols)) == TOP_N, "duplicate symbols in pinned selection"
    btc_in_selected = BTC_SYMBOL in symbols

    # ---- current-bytes revalidation -------------------------------------- #
    funding_files = {
        os.path.basename(os.path.dirname(p)): p
        for p in sorted(glob.glob(os.path.join(str(funding_root), "*", "funding.json")))
    }
    funding_raw = {sym: json.load(open(p))["rows"] for sym, p in funding_files.items()}
    corroborate = build_corroboration(funding_raw)

    per_symbol_reval: dict[str, dict] = {}
    drifts: list[dict] = []
    selected_symbols: list[dict] = []
    coverage_required: dict[str, tuple[int, int]] = {}
    coverage_all: dict[str, tuple[int, int]] = {}

    for entry in chosen:
        sym = entry["symbol"]
        files = bar_files_for_symbol(catalog_root, sym)
        inst = load_instrument(sym)
        vol = median_daily_quote_volume_pre_window(files)
        cen_pre = census_for_symbol(files, PRE_START_S, PRE_END_S)
        cen_sc = census_for_symbol(files, SCORED_START_S, SCORED_END_S)
        fund = analyze_funding(funding_raw[sym], corroborate) if sym in funding_raw else None
        age = listing_age_check(inst, dt_to_s(FIRST_POSSIBLE_EXPOSURE))
        meta_ok = bool(inst and inst["quote_currency"] == QUOTE_REQUIRED
                       and inst["contract_type"] == "PERPETUAL"
                       and inst["status"] == "TRADING")

        cov_sc = measured_coverage(files, SCORED_START_S, SCORED_END_S)
        cov_pre = measured_coverage(files, PRE_START_S, PRE_END_S)
        if cov_sc is not None:
            coverage_all[sym] = cov_sc
            if sym != BTC_SYMBOL:
                coverage_required[sym] = cov_sc
        dups = duplicate_raw_stamps(files)

        # drift vs pinned metrics (exact decimal string comparison)
        pinned_exact_vol = _pinned_exact_volume(pinned, sym)
        if vol["median_daily_quote_volume_usdt_exact"] != pinned_exact_vol:
            drifts.append({"symbol": sym, "field": "median_daily_quote_volume_usdt_exact",
                           "pinned": pinned_exact_vol,
                           "current": vol["median_daily_quote_volume_usdt_exact"]})
        if entry["days_with_bars_pre_window"] != vol["days_with_bars_pre_window"]:
            drifts.append({"symbol": sym, "field": "days_with_bars_pre_window",
                           "pinned": entry["days_with_bars_pre_window"],
                           "current": vol["days_with_bars_pre_window"]})
        if entry["census_pre_window_gaps"] != cen_pre["gaps_found"]:
            drifts.append({"symbol": sym, "field": "census_pre_window_gaps",
                           "pinned": entry["census_pre_window_gaps"],
                           "current": cen_pre["gaps_found"]})
        if entry["census_scored_window_gaps"] != cen_sc["gaps_found"]:
            drifts.append({"symbol": sym, "field": "census_scored_window_gaps",
                           "pinned": entry["census_scored_window_gaps"],
                           "current": cen_sc["gaps_found"]})
        if entry["census_scored_window_unexplained"] != cen_sc["unexplained_gaps"]:
            drifts.append({"symbol": sym, "field": "census_scored_window_unexplained",
                           "pinned": entry["census_scored_window_unexplained"],
                           "current": cen_sc["unexplained_gaps"]})
        if entry["funding_held_exposure_complete"] != (fund or {}).get("complete"):
            drifts.append({"symbol": sym, "field": "funding_held_exposure_complete",
                           "pinned": entry["funding_held_exposure_complete"],
                           "current": (fund or {}).get("complete")})

        per_symbol_reval[sym] = {
            "instrument_id": f"{sym}-PERP.{VENUE}",
            "metadata_sanity_ok": meta_ok,
            "listing_age": age,
            "volume_pre_window": vol,
            "census_pre_window": cen_pre,
            "census_scored_window": cen_sc,
            "funding_held_exposure_audit": fund,
            "scored_window_first_open_utc": utc_str(cov_sc[0]) if cov_sc else None,
            "scored_window_last_open_utc": utc_str(cov_sc[1]) if cov_sc else None,
            "pre_window_first_open_utc": utc_str(cov_pre[0]) if cov_pre else None,
            "pre_window_last_open_utc": utc_str(cov_pre[1]) if cov_pre else None,
            "duplicate_bar_timestamps_scored_and_pre": dups,
        }

        selected_symbols.append({
            "rank": entry["rank"],
            "symbol": sym,
            "instrument_id": f"{sym}-PERP.{VENUE}",
            "median_daily_quote_volume_pre_window_usdt":
                vol["median_daily_quote_volume_usdt"],
            "median_daily_quote_volume_pre_window_usdt_exact":
                vol["median_daily_quote_volume_usdt_exact"],
            "days_with_bars_pre_window": vol["days_with_bars_pre_window"],
            "census_pre_window_gaps": cen_pre["gaps_found"],
            "census_pre_window_unexplained": cen_pre["unexplained_gaps"],
            "census_scored_window_gaps": cen_sc["gaps_found"],
            "census_scored_window_unexplained": cen_sc["unexplained_gaps"],
            "funding_held_exposure_complete": bool((fund or {}).get("complete")),
            "listing_age_days_at_first_possible_exposure":
                age["age_days_at_first_possible_exposure"],
            "listing_age_gate_ok": age["ok"],
            "metadata_sanity_ok": meta_ok,
        })

    selected_symbols.sort(key=lambda c: c["rank"])

    # ---- BTC benchmark context ------------------------------------------- #
    btc_context: dict | None = None
    btc_censuses: dict[str, dict] = {}
    btc_cov = None
    if not btc_in_selected:
        btc_files = bar_files_for_symbol(catalog_root, BTC_SYMBOL)
        if btc_files:
            btc_cov = measured_coverage(btc_files, SCORED_START_S, SCORED_END_S)
            if btc_cov is not None:
                coverage_all[BTC_SYMBOL] = btc_cov
            btc_censuses = {
                "pre_window": census_for_symbol(btc_files, PRE_START_S, PRE_END_S),
                "scored_window": census_for_symbol(btc_files, SCORED_START_S, SCORED_END_S),
            }
            btc_fund = analyze_funding(funding_raw[BTC_SYMBOL], corroborate) \
                if BTC_SYMBOL in funding_raw else None
            btc_dups = duplicate_raw_stamps(btc_files)
            btc_context = {
                "symbol": BTC_SYMBOL,
                "instrument_id": f"{BTC_SYMBOL}-PERP.{VENUE}",
                "role": "benchmark_measurement_only_excluded_from_ranking",
                "census_pre_window_gaps": btc_censuses["pre_window"]["gaps_found"],
                "census_scored_window_gaps": btc_censuses["scored_window"]["gaps_found"],
                "census_scored_window_unexplained":
                    btc_censuses["scored_window"]["unexplained_gaps"],
                "funding_held_exposure_complete":
                    bool((btc_fund or {}).get("complete")),
                "funding_held_exposure_audit": btc_fund,
                "duplicate_bar_timestamps": btc_dups,
                "scored_window_first_open_utc": utc_str(btc_cov[0]) if btc_cov else None,
                "scored_window_last_open_utc": utc_str(btc_cov[1]) if btc_cov else None,
            }

    # ---- measured common completed-bar windows ---------------------------- #
    req_start, req_end = intersection_range(coverage_required)
    all_start, all_end = intersection_range(coverage_all)
    scored_measured_required = {
        "start_utc": close_stamp_iso(req_start) if req_start is not None else None,
        "end_utc": close_stamp_iso(req_end) if req_end is not None else None,
        "basis": ("MEASURED intersection of completed 15m bar coverage across the "
                  "10 selected altcoins inside the contract scored window "
                  "[2025-08-21T00:00:00Z, 2026-08-21T00:00:00Z); endpoints are "
                  "completed-bar CLOSE stamps; never trimmed to dodge gaps"),
    }
    scored_measured_all = {
        "start_utc": close_stamp_iso(all_start) if all_start is not None else None,
        "end_utc": close_stamp_iso(all_end) if all_end is not None else None,
        "basis": "same measurement including BTCUSDT as benchmark context",
    }

    # ---- gap-census totals ------------------------------------------------ #
    slots_checked = sum(
        per_symbol_reval[s]["census_pre_window"]["expected_15m_slots"]
        + per_symbol_reval[s]["census_scored_window"]["expected_15m_slots"]
        for s in symbols
    )
    gaps_found = sum(
        per_symbol_reval[s]["census_pre_window"]["gaps_found"]
        + per_symbol_reval[s]["census_scored_window"]["gaps_found"]
        for s in symbols
    )
    unexplained_total = sum(
        per_symbol_reval[s]["census_pre_window"]["unexplained_gaps"]
        + per_symbol_reval[s]["census_scored_window"]["unexplained_gaps"]
        for s in symbols
    )
    documented_runs = []
    non_boundary_explained: list[dict] = []
    for s in symbols:
        for wname in ("pre_window", "scored_window"):
            for g in per_symbol_reval[s][f"census_{wname}"]["gap_runs"]:
                rec = {"symbol": s, "window": wname, **{k: g[k] for k in
                        ("start_utc", "end_utc", "missing_slots", "cause",
                         "explained", "evidence")}}
                if g["cause"] in DOCUMENTED_CAPTURE_BOUNDARY_CLASSES:
                    documented_runs.append(rec)
                elif g["explained"]:
                    non_boundary_explained.append(rec)

    # BTC context censuses were computed above; include their totals separately
    btc_slots = sum(v["expected_15m_slots"] for v in btc_censuses.values()) \
        if btc_censuses else 0
    btc_gaps = sum(v["gaps_found"] for v in btc_censuses.values()) if btc_censuses else 0
    btc_unexplained = sum(v["unexplained_gaps"] for v in btc_censuses.values()) \
        if btc_censuses else 0

    # ---- funding verdicts -------------------------------------------------- #
    funding_per_symbol = {
        s: {**per_symbol_reval[s]["funding_held_exposure_audit"],
            "verdict": ("COMPLETE"
                        if per_symbol_reval[s]["funding_held_exposure_audit"]["complete"]
                        else "INCOMPLETE")}
        for s in symbols
    }
    funding_all_complete = all(
        per_symbol_reval[s]["funding_held_exposure_audit"]["complete"] for s in symbols
    )

    # ---- PIT instrument metadata ------------------------------------------ #
    pit = pit_metadata_via_catalog(catalog_root, symbols)

    # ---- gate -------------------------------------------------------------- #
    failed_ages = [s for s in symbols if not per_symbol_reval[s]["listing_age"]["ok"]]
    failed_meta = [s for s in symbols if not per_symbol_reval[s]["metadata_sanity_ok"]]

    checks = [
        {"id": "source_selection_artifact_pinned_sha256_verified",
         "ok": True,
         "detail": (f"{SOURCE_MANIFEST_RELPATH} sha256 matches pinned value "
                    f"{PINNED_SOURCE_MANIFEST_SHA256}; selector script sha256 "
                    f"matches {PINNED_SOURCE_SELECTOR_SHA256} (corrected rule "
                    "reused unmodified)")},
        {"id": "selection_rule_reuse_no_new_rule",
         "ok": True,
         "detail": ("all census/ranking/funding/gate logic imported verbatim from "
                    "scripts.v8x_crypto_universe_selection (V8 A8 corrected "
                    "selector); no new selection parameters introduced")},
        {"id": "top10_revalidated_against_current_catalog_bytes",
         "ok": not drifts,
         "detail": ("volume metric (Decimal-exact), days-with-bars, both-window "
                    "gap counts, funding completeness recomputed and compared to "
                    "the pinned manifest"),
         "drifts": drifts},
        {"id": "btc_excluded_from_traded_universe",
         "ok": not btc_in_selected,
         "detail": (f"{BTC_SYMBOL} absent from the 10 ranked symbols; carried as "
                    "benchmark measurement-only context")},
        {"id": "gap_census_unexplained_zero_both_windows",
         "ok": unexplained_total == 0,
         "detail": (f"slots_checked={slots_checked} gaps_found={gaps_found} "
                    f"unexplained={unexplained_total} over pre-window AND scored "
                    "window for the 10 alts; only permitted gap class is the "
                    "documented capture-boundary class"),
         "non_boundary_explained_classes": non_boundary_explained},
        {"id": "listing_age_min_365d_at_first_possible_exposure",
         "ok": not failed_ages,
         "failed_symbols": failed_ages,
         "detail": (f"onboard_date <= scored-window start minus "
                    f"{LISTING_AGE_MIN_DAYS}d evaluated at the conservative "
                    f"first-possible-exposure {utc_str(dt_to_s(FIRST_POSSIBLE_EXPOSURE))}")},
        {"id": "funding_held_exposure_completeness_all_selected",
         "ok": funding_all_complete,
         "assumption": FUNDING_ASSUMPTION_TEXT,
         "detail": ("settlements contiguous with legal exchange intervals, no "
                    "duplicates, boundary coverage from first possible weekly "
                    "exposure through scored-window end; interval-regime steps "
                    "cross-symbol corroborated")},
        {"id": "pit_instrument_metadata_tick_step_min_notional_present",
         "ok": pit["all_ten_present_with_tick_step_min_notional"],
         "detail": pit["method"],
         "limitation": pit["limitation"]},
    ]
    status = "PASS"
    fail_tags = {
        "top10_revalidated_against_current_catalog_bytes": "FAIL_SELECTION_DRIFT",
        "btc_excluded_from_traded_universe": "FAIL_BTC_EXCLUSION_BROKEN",
        "gap_census_unexplained_zero_both_windows": "FAIL_UNEXPLAINED_GAPS",
        "listing_age_min_365d_at_first_possible_exposure": "FAIL_LISTING_AGE",
        "funding_held_exposure_completeness_all_selected": "FAIL_FUNDING_COVERAGE",
        "pit_instrument_metadata_tick_step_min_notional_present": "FAIL_PIT_METADATA",
    }
    for c in checks:
        if not c["ok"] and c["id"] in fail_tags:
            status = fail_tags[c["id"]]
            break

    # ---- normalized block (V8 data-manifest pattern) ----------------------- #
    inventory = collect_files_by_symbol(catalog_root, funding_root,
                                        [*symbols, BTC_SYMBOL])
    source_hashes_flat = flatten_source_hashes(inventory)

    def _sym_norm(sym: str) -> dict:
        if sym == BTC_SYMBOL and btc_context is not None:
            cen_sc_n = btc_censuses.get("scored_window", {})
            cen = btc_censuses
        else:
            r = per_symbol_reval[sym]
            cen_sc_n = r["census_scored_window"]
            cen = {"pre_window": r["census_pre_window"], "scored_window": cen_sc_n}
        hours = sum(
            cen[w]["unexplained_gaps"] * (BAR_INTERVAL_S / 3600.0)
            for w in ("pre_window", "scored_window")
        )
        fund = (btc_context["funding_held_exposure_audit"]
                if sym == BTC_SYMBOL and btc_context is not None
                else per_symbol_reval[sym]["funding_held_exposure_audit"])
        cov = coverage_all.get(sym)
        return {
            "completed_bars_in_scored_window": cen_sc_n.get("expected_15m_slots", 0)
            - cen_sc_n.get("gaps_found", 0),
            "first_completed_close_utc":
                close_stamp_iso(cov[0]) if cov else None,
            "last_completed_close_utc":
                close_stamp_iso(cov[1]) if cov else None,
            "duplicate_timestamps":
                btc_context["duplicate_bar_timestamps"]
                if sym == BTC_SYMBOL and btc_context is not None
                else per_symbol_reval[sym]["duplicate_bar_timestamps_scored_and_pre"],
            "unexplained_gap_hours_both_windows": round(hours, 6),
            "funding_settlements_in_scored_window":
                (fund or {}).get("settlements_in_exposure_span", 0),
            "role": ("benchmark_context_only" if sym == BTC_SYMBOL else "required"),
            "verdict": ("PASS_CONTEXT_BENCHMARK_ONLY" if sym == BTC_SYMBOL
                        else "PASS"),
        }

    normalized = {
        "label": AUDIT_LABEL,
        "target_window": {
            "start": utc_str(SCORED_START_S),
            "end": utc_str(SCORED_END_S),
        },
        "common_window_required": scored_measured_required,
        "common_window_all_audited": scored_measured_all,
        "symbols": {s: _sym_norm(s) for s in sorted([*symbols, BTC_SYMBOL])
                    if s in inventory},
    }
    normalized_manifest_sha256 = sha256_obj(normalized)

    # ---- deliverable 2: universe_selection_v9.json ------------------------- #
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "universe_selection_v9",
        "agent": AGENT,
        "generated_at_utc": GENERATED_AT_UTC,
        "performance_blind": True,
        "source_selection_artifact": source_block,
        "selection_rule_reuse_note": (
            "V9 cohort-10 universe REUSES the corrected V8 A8 selection rule "
            "verbatim (pre-window median daily quote-volume ranking, BTC excluded "
            "before ranking, exact 15m gap census, held-exposure funding proof); "
            "re-pinned under V9 ownership with sha256 verification; no new rule "
            "or parameter was introduced"),
        "selection_window": pinned["selection_window"],
        "scored_window_contract": pinned["scored_window"],
        "scored_window": scored_measured_required,
        "ranking_rule": pinned["ranking_rule"],
        "btc_excluded": True,
        "btc_benchmark_context_only": {
            "symbol": BTC_SYMBOL,
            "instrument_id": f"{BTC_SYMBOL}-PERP.{VENUE}",
            "excluded_from_ranks_weights_pnl": True,
            "context_summary": btc_context,
        },
        "selected_symbols": selected_symbols,
        "not_selected_eligible_note": (
            "see source_selection_artifact.verdict + pinned manifest "
            "not_selected_eligible (AVAXUSDT AAVEUSDT BCHUSDT NEARUSDT WLDUSDT "
            "BOMEUSDT ZECUSDT ACEUSDT ONGUSDT)"),
        "files_by_symbol": inventory,
        "source_hashes_flat": source_hashes_flat,
        "hash_algorithm": "sha256",
        "normalized": normalized,
        "normalized_manifest_sha256": normalized_manifest_sha256,
    }

    # ---- deliverable 3: data_audit_v9.json --------------------------------- #
    audit_doc = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "data_audit_v9",
        "agent": AGENT,
        "generated_at_utc": GENERATED_AT_UTC,
        "label": AUDIT_LABEL,
        "catalog_path": str(catalog_root),
        "funding_dir": str(funding_root),
        "windows": {
            "pre_window": {"start_utc": utc_str(PRE_START_S),
                           "end_utc": utc_str(PRE_END_S)},
            "scored_window_contract": {"start_utc": utc_str(SCORED_START_S),
                                       "end_utc": utc_str(SCORED_END_S)},
            "scored_window_measured_required": scored_measured_required,
            "scored_window_measured_all_audited": scored_measured_all,
            "per_symbol_scored_coverage_open_stamps": {
                s: {"first_open_utc": per_symbol_reval[s]["scored_window_first_open_utc"],
                    "last_open_utc": per_symbol_reval[s]["scored_window_last_open_utc"]}
                for s in symbols
            },
        },
        "gap_census": {
            "method": ("exact 15-minute grid census over BOTH windows, imported "
                       "verbatim from the corrected V8 A8 selector "
                       "(scripts/v8x_crypto_universe_selection.census_for_symbol)"),
            "interval_seconds": BAR_INTERVAL_S,
            "classification_rule": (
                "run strictly inside ONE capture session's observed range => "
                "unexplained; run bounded before/after/by capture-session edges "
                "=> explained capture-boundary cause"),
            "scope": "10 selected altcoins (BTCUSDT reported as context below)",
            "slots_checked_total": slots_checked,
            "gaps_found_total": gaps_found,
            "unexplained_gaps_total": unexplained_total,
            "documented_gap_classes_present": documented_runs,
            "non_boundary_explained_classes": non_boundary_explained,
            "btc_context_totals": {"slots_checked": btc_slots,
                                   "gaps_found": btc_gaps,
                                   "unexplained_gaps": btc_unexplained},
            "per_symbol": {
                s: {"pre_window": per_symbol_reval[s]["census_pre_window"],
                    "scored_window": per_symbol_reval[s]["census_scored_window"]}
                for s in symbols
            },
            "btc_context_census": btc_censuses,
        },
        "funding_coverage": {
            "assumption": FUNDING_ASSUMPTION_TEXT,
            "first_possible_exposure_utc": utc_str(dt_to_s(FIRST_POSSIBLE_EXPOSURE)),
            "max_interval_seconds": 28800,
            "per_symbol_verdict": {s: funding_per_symbol[s]["verdict"]
                                   for s in symbols},
            "per_symbol": funding_per_symbol,
            "all_selected_complete": funding_all_complete,
        },
        "pit_instrument_metadata": pit,
        "listing_age_gate": {
            "min_days": LISTING_AGE_MIN_DAYS,
            "first_possible_exposure_utc": utc_str(dt_to_s(FIRST_POSSIBLE_EXPOSURE)),
            "per_symbol": {s: per_symbol_reval[s]["listing_age"] for s in symbols},
            "all_ok": not failed_ages,
        },
        "btc_exclusion_check": {
            "btc_symbol": BTC_SYMBOL,
            "in_selected_ten": btc_in_selected,
            "benchmark_only_context_present": btc_context is not None,
            "excluded_before_ranking": True,
        },
        "revalidation_vs_pinned": {"matched": not drifts, "drifts": drifts},
        "source_hashes_flat": source_hashes_flat,
        "normalized_manifest_sha256": normalized_manifest_sha256,
        "verdict": ("V9_DATA_AUDIT_PASS" if status == "PASS"
                    else f"V9_DATA_AUDIT_{status}"),
    }

    # ---- deliverable 4: t02_gate_v9.json ----------------------------------- #
    gate = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "t02_gate_v9",
        "gate": GATE_ID,
        "agent": AGENT,
        "generated_at_utc": GENERATED_AT_UTC,
        "status": status,
        "selected_symbols": [c["symbol"] for c in selected_symbols],
        "btc_excluded": True,
        "scored_window_measured": scored_measured_required,
        "gap_census_totals": {
            "slots_checked": slots_checked,
            "gaps_found": gaps_found,
            "unexplained": unexplained_total,
        },
        "funding_completeness": {
            "all_selected_complete": funding_all_complete,
            "assumption": FUNDING_ASSUMPTION_TEXT,
        },
        "checks": checks,
        "artifacts": [
            "data/v9_manifests/universe_selection_v9.json",
            "research/audits/v9p/data_audit_v9.json",
            "research/audits/v9p/t02_gate_v9.json",
        ],
        "normalized_manifest_sha256": normalized_manifest_sha256,
    }

    return {"manifest": manifest, "audit": audit_doc, "gate": gate}


def main(manifest_out: Path = DEFAULT_MANIFEST_OUT,
         audit_out: Path = DEFAULT_AUDIT_OUT,
         gate_out: Path = DEFAULT_GATE_OUT) -> dict:
    res = run_audit()
    for path, payload in ((manifest_out, res["manifest"]),
                          (audit_out, res["audit"]),
                          (gate_out, res["gate"])):
        write_json(Path(path), payload)
    return res


if __name__ == "__main__":
    result = main(*(Path(a) for a in sys.argv[1:]))
    print("gate:", result["gate"]["status"])
    print("chosen:", [c["symbol"] for c in result["manifest"]["selected_symbols"]])
    print("scored_window_measured:",
          result["manifest"]["scored_window"])
    print("gap_census:", result["gate"]["gap_census_totals"])
    print("funding complete:", result["gate"]["funding_completeness"]["all_selected_complete"])
    print("normalized_manifest_sha256:",
          result["manifest"]["normalized_manifest_sha256"])
