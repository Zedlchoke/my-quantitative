#!/usr/bin/env python
"""V8X / A8 -- CORRECTED deterministic crypto top-10 universe selection.

Scientific correction of the ad-hoc selection committed at 4f1d704, which
violated the frozen selection contract in four ways:

  V1  ranked by volume over the SCORED window      -> must rank ONLY over the
      pre-window [2025-07-22T00:00Z, 2025-08-21T00:00Z);
  V2  BTCUSDT was included in the traded top-10    -> BTC is benchmark
      measurement-only and is EXCLUDED before ranking;
  V3  gap screen was daily-granularity ("gap_day") -> replaced by an EXACT
      15-minute grid census over BOTH the pre-window and the scored window,
      every gap given a machine-readable cause; unexplained => fail;
  V4  funding gate was `rows >= 1`                 -> replaced by a
      held-exposure completeness proof: settlements verified contiguous
      (no interval above the exchange maximum), boundary-covered from the
      first possible weekly entry (pre-window end / scored-window start,
      conservative Monday-rebalance assumption) through the scored-window end,
      with cross-symbol-corroborated exchange interval steps explained.

Performance-blind: reads only catalog parquets + local funding JSON.
Touches nothing under results/**. Fully offline and byte-deterministic:
re-running produces an identical manifest file (fixed generated_at).
"""

from __future__ import annotations

import collections
import glob
import hashlib
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

# --------------------------------------------------------------------------- #
# Frozen constants (do NOT edit without a new prereg)
# --------------------------------------------------------------------------- #
SCHEMA_VERSION = "2.0.0"
AGENT = "A8-crypto-breadth"
GENERATED_AT_UTC = "2026-08-26T00:00:00Z"  # frozen for byte-reproducibility

CATALOG_ROOT = os.environ.get(
    "V8X_CATALOG_ROOT", "/Users/hoangminhlong/my-quantitative/catalog_live_crypto"
)
FUNDING_ROOT = os.environ.get(
    "V8X_FUNDING_ROOT", "/Users/hoangminhlong/my-quantitative/funding_data/scan_2026"
)

VENUE = "BINANCE"
QUOTE_REQUIRED = "USDT"
CONTRACT_TYPE_REQUIRED = "PERPETUAL"
BAR_SUFFIX = "-15-MINUTE-LAST-EXTERNAL"

PRE_START = datetime(2025, 7, 22, tzinfo=timezone.utc)   # pre-window start
PRE_END = datetime(2025, 8, 21, tzinfo=timezone.utc)     # pre-window end
SCORED_START = PRE_END                                    # scored window start
SCORED_END = datetime(2026, 8, 21, tzinfo=timezone.utc)   # scored window end

# Weekly (Monday) rebalance schedule assumption: a strategy could first hold a
# symbol at the earliest moment the scored window opens; conservatively we take
# FIRST_POSSIBLE_EXPOSURE = pre-window end = scored-window start and require
# funding coverage through the scored-window end inclusive.
FIRST_POSSIBLE_EXPOSURE = SCORED_START

BAR_INTERVAL_S = 900          # exact 15-minute grid
LISTING_AGE_MIN_DAYS = 365    # consistent with prior artifact preference
TOP_N = 10
BTC_SYMBOL = "BTCUSDT"        # PERP.BINANCE.BTC-USDT equivalent local id

MAX_FUNDING_INTERVAL_S = 28800            # Binance USDm maximum funding step
LEGAL_FUNDING_INTERVALS_S = (3600, 7200, 14400, 28800)
FUNDING_JITTER_MS = 60_000                # timestamps carry <= tens-of-ms jitter

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def dt_to_s(dt: datetime) -> int:
    return int((dt - EPOCH).total_seconds())


PRE_START_S, PRE_END_S = dt_to_s(PRE_START), dt_to_s(PRE_END)
SCORED_START_S, SCORED_END_S = dt_to_s(SCORED_START), dt_to_s(SCORED_END)


def utc_str(ts_s: int) -> str:
    return datetime.fromtimestamp(ts_s, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# 15-minute grid helpers
# --------------------------------------------------------------------------- #
def slot_opens_from_ts_event(ts_ns: np.ndarray) -> np.ndarray:
    """Map raw ns timestamps to unique 15m slot-open epoch seconds.

    Local bars are stamped at slot close minus ~0.1 ms, so each stamp is
    assigned to its own slot via ceil-to-close then minus one interval.
    """
    if ts_ns.size == 0:
        return np.empty(0, dtype=np.int64)
    sec = -(-ts_ns // 1_000_000_000)              # ceil to seconds
    close = -(-sec // BAR_INTERVAL_S) * BAR_INTERVAL_S
    return np.unique(close - BAR_INTERVAL_S)


def gap_runs(observed_opens: np.ndarray, win_a: int, win_b: int):
    """Exact census: expected 15m slots in [win_a, win_b) minus observed.

    Returns (expected_count, missing_runs) where each run is a dict with
    start/end slot-open seconds and the list of missing slots.
    """
    expected = np.arange(win_a, win_b, BAR_INTERVAL_S, dtype=np.int64)
    missing = np.setdiff1d(expected, observed_opens)
    runs = []
    for m in missing:
        if runs and m - runs[-1]["slots"][-1] == BAR_INTERVAL_S:
            runs[-1]["slots"].append(int(m))
        else:
            runs.append({"slots": [int(m)]})
    return len(expected), runs


def classify_run(run_slots, session_ranges):
    """Frozen classification of a missing-slot run.

    interior : the whole run lies strictly inside ONE capture session's
               observed [min_open, max_open] range while that session holds no
               such bars -> no local evidence can explain it -> UNEXPLAINED.
    boundary : the run is bounded by capture sessions (before/at the start of
               local coverage, after/at its end, or in a hole BETWEEN two
               sessions) -> cause = local-capture-session boundary -> EXPLAINED.
    """
    s, e = run_slots[0], run_slots[-1]
    if not session_ranges:
        return {"cause": "no_local_capture_sessions", "explained": False, "evidence": {}}
    for lo, hi, _idx in session_ranges:
        if lo < s and e < hi:
            return {
                "cause": "unexplained_hole_inside_single_capture_session",
                "explained": False,
                "evidence": {"session_range": [utc_str(lo), utc_str(hi)]},
            }
    before = [r for r in session_ranges if r[1] < s]
    after = [r for r in session_ranges if r[0] > e]
    if before and after:
        cause = "local_capture_boundary_between_sessions"
        ev = {"prev_end": utc_str(max(r[1] for r in before)),
              "next_start": utc_str(min(r[0] for r in after))}
    elif not before:
        cause = "local_capture_starts_after_window_start"
        ev = {"first_session_start": utc_str(min(r[0] for r in session_ranges))}
    else:
        cause = "local_capture_ends_before_window_end"
        ev = {"last_session_end": utc_str(max(r[1] for r in session_ranges))}
    return {"cause": cause, "explained": True, "evidence": ev}


def census_for_symbol(bar_files, win_a: int, win_b: int) -> dict:
    """Per-file session ranges + exact gap census over one window."""
    session_ranges, all_opens = [], []
    for idx, f in enumerate(sorted(bar_files)):
        t = pq.read_table(f, columns=["ts_event"])["ts_event"].to_numpy()
        opens = slot_opens_from_ts_event(np.asarray(t, dtype=np.int64))
        if opens.size:
            session_ranges.append((int(opens[0]), int(opens[-1]), idx))
            all_opens.append(opens)
    observed = np.unique(np.concatenate(all_opens)) if all_opens else np.empty(0, np.int64)
    n_expected, runs = gap_runs(observed, win_a, win_b)
    gaps, unexplained = [], 0
    for r in runs:
        cls = classify_run(r["slots"], session_ranges)
        unexplained += 0 if cls["explained"] else len(r["slots"])
        gaps.append({
            "start_utc": utc_str(r["slots"][0]),
            "end_utc": utc_str(r["slots"][-1]),
            "missing_slots": len(r["slots"]),
            "cause": cls["cause"],
            "explained": cls["explained"],
            "evidence": cls["evidence"],
        })
    return {
        "window": [utc_str(win_a), utc_str(win_b)],
        "expected_15m_slots": n_expected,
        "gaps_found": int(sum(g["missing_slots"] for g in gaps)),
        "unexplained_gaps": int(unexplained),
        "gap_runs": gaps,
    }


# --------------------------------------------------------------------------- #
# Volume metric (pre-window only) and ranking
# --------------------------------------------------------------------------- #
def median_daily_quote_volume_pre_window(bar_files) -> dict:
    """Decimal-exact daily quote-volume sums over PRE-WINDOW bar-days only."""
    per_day = collections.defaultdict(Decimal)
    for f in sorted(bar_files):
        tbl = pq.read_table(f, columns=["ts_event", "quote_volume"])
        opens = slot_opens_from_ts_event(
            np.asarray(tbl["ts_event"].to_numpy(), dtype=np.int64))
        qv = tbl["quote_volume"].to_pylist()
        for o, q in zip(opens, qv):
            day = o // 86400
            if PRE_START_S <= o < PRE_END_S:
                per_day[day] += Decimal(q)
    days = sorted(per_day)
    vals = [per_day[d] for d in days]
    med = statistics.median(vals) if vals else Decimal(0)
    return {
        "days_with_bars_pre_window": len(days),
        "median_daily_quote_volume_usdt_exact": str(med),
        "median_daily_quote_volume_usdt": float(round(med, 2)),
    }


def rank_and_select(eligible, top_n=TOP_N):
    """Primary: pre-window median daily quote volume desc; tie-break symbol asc."""
    ordered = sorted(
        eligible,
        key=lambda c: (-Decimal(c["volume"]["median_daily_quote_volume_usdt_exact"]),
                       c["symbol"]),
    )
    return ordered[:top_n], ordered


# --------------------------------------------------------------------------- #
# Funding held-exposure completeness proof
# --------------------------------------------------------------------------- #
def analyze_funding(sym_rows, corroborate_pairs):
    """Prove settlements are complete across the held-exposure span.

    Gates (all must hold):
      f1 sorted & duplicate-free (tolerance FUNDING_JITTER_MS);
      f2 every consecutive gap is a legal Binance interval (<=8h) + jitter;
      f3 boundary coverage: first settlement <= exposure_start + 8h AND
         last settlement >= scored_end - 8h;
      f4 any single 8h step inside a sub-8h cadence regime is flagged and must
         be cross-symbol corroborated at an identical timestamp (exchange-wide
         interval-regime step), otherwise it is unexplained => fail.
    """
    ext_lo = (SCORED_START_S - MAX_FUNDING_INTERVAL_S) * 1000 - FUNDING_JITTER_MS
    ext_hi = (SCORED_END_S * 1000) + FUNDING_JITTER_MS
    ts_all = sorted(r["fundingTime"] for r in sym_rows)
    ts = [t for t in ts_all if ext_lo <= t <= ext_hi]

    dups = sum(1 for a, b in zip(ts, ts[1:]) if b - a < FUNDING_JITTER_MS)
    diffs_ms = [(b - a) for a, b in zip(ts, ts[1:])]
    diffs_s = sorted({round(d / 1000) for d in diffs_ms})
    illegal = [d for d in diffs_s
               if not any(abs(d - leg) <= FUNDING_JITTER_MS / 1000
                          for leg in LEGAL_FUNDING_INTERVALS_S)]
    cadence_mode_s = statistics.mode(round(d / 60000) for d in diffs_ms) if diffs_ms else None

    f1 = dups == 0
    f2 = not illegal
    f3 = bool(ts) and ts[0] <= (SCORED_START_S + MAX_FUNDING_INTERVAL_S) * 1000 \
        and ts[-1] >= (SCORED_END_S - MAX_FUNDING_INTERVAL_S) * 1000

    anomalies = []
    if cadence_mode_s is not None and cadence_mode_s < MAX_FUNDING_INTERVAL_S // 60:
        for a, b in zip(ts, ts[1:]):
            gap_s = round((b - a) / 1000)
            if abs(gap_s - MAX_FUNDING_INTERVAL_S) <= FUNDING_JITTER_MS / 1000:
                pair = (a, b)
                n_corr = corroborate_pairs.get(pair, 0)
                explained = n_corr >= 2
                anomalies.append({
                    "step_start_utc": utc_str(a // 1000),
                    "step_end_utc": utc_str(b // 1000),
                    "gap_minutes": round((b - a) / 60000),
                    "symbols_sharing_identical_step": n_corr,
                    "cause": ("exchange_wide_funding_interval_step"
                              if explained else "unexplained_isolated_interval_step"),
                    "explained": explained,
                })

    unexplained_anomalies = [x for x in anomalies if not x["explained"]]
    in_span = [t for t in ts if SCORED_START_S * 1000 <= t <= SCORED_END_S * 1000]
    return {
        "exposure_span_utc": [utc_str(SCORED_START_S), utc_str(SCORED_END_S)],
        "assumption": ("weekly Monday rebalance; conservative first-possible-exposure "
                       "= pre-window end = scored-window start 2025-08-21T00:00Z; "
                       "coverage required through scored-window end inclusive"),
        "settlements_in_exposure_span": len(in_span),
        "min_expected_settlements_if_max_cadence":
            (SCORED_END_S - SCORED_START_S) // MAX_FUNDING_INTERVAL_S,
        "first_settlement_utc": utc_str(ts[0] // 1000) if ts else None,
        "last_settlement_utc": utc_str(ts[-1] // 1000) if ts else None,
        "duplicate_timestamps": dups,
        "distinct_interval_seconds": diffs_s,
        "cadence_mode_minutes": cadence_mode_s,
        "gate_sorted_unique_f1": f1,
        "gate_legal_intervals_f2": f2,
        "gate_boundary_coverage_f3": f3,
        "flagged_interval_steps": anomalies,
        "complete": bool(f1 and f2 and f3 and not unexplained_anomalies),
    }


def build_corroboration(funding_by_sym):
    """Count, per identical (prev_ms, next_ms) 8h step, how many sub-8h symbols show it."""
    pairs = collections.Counter()
    for sym, rows in funding_by_sym.items():
        ts = sorted(r["fundingTime"] for r in rows)
        diffs = [(a, b) for a, b in zip(ts, ts[1:])
                 if abs((b - a) / 1000 - MAX_FUNDING_INTERVAL_S) <= FUNDING_JITTER_MS / 1000]
        # cadence context: only flag when symbol mostly runs faster than 8h
        all_d = [b - a for a, b in zip(ts, ts[1:])]
        if all_d and statistics.mode(all_d) < MAX_FUNDING_INTERVAL_S * 1000:
            for p in set(diffs):
                pairs[p] += 1
    return pairs


# --------------------------------------------------------------------------- #
# Instrument metadata
# --------------------------------------------------------------------------- #
def load_instrument(symbol):
    pat = os.path.join(CATALOG_ROOT, "data", "crypto_perpetual",
                       f"{symbol}-PERP.{VENUE}", "*.parquet")
    files = sorted(glob.glob(pat))
    if not files:
        return None
    row = pq.read_table(files[0]).to_pandas().iloc[0]
    info = json.loads(bytes(row["info"]))
    return {
        "instrument_id": str(row["id"]),
        "quote_currency": str(info.get("quoteAsset", "")),
        "contract_type": str(info.get("contractType", "")),
        "status": str(info.get("status", "")),
        "onboard_date_utc": datetime.fromtimestamp(
            int(info["onboardDate"]) / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if info.get("onboardDate") else None,
        "onboard_ms": int(info["onboardDate"]) if info.get("onboardDate") else None,
    }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bars_dir_digest(files):
    lines = sorted(f"{os.path.basename(f)}:{sha256_file(f)}" for f in files)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Main pipeline
# --------------------------------------------------------------------------- #
def main(manifest_out):
    bar_dirs = sorted(glob.glob(os.path.join(
        CATALOG_ROOT, "data", "binance_bar", f"*-PERP.{VENUE}{BAR_SUFFIX}")))
    funding_files = {os.path.basename(os.path.dirname(p)): p
                     for p in glob.glob(os.path.join(FUNDING_ROOT, "*", "funding.json"))}
    funding_raw = {sym: json.load(open(p))["rows"]
                   for sym, p in funding_files.items()}
    corroborate = build_corroboration(funding_raw)

    listing_age_cutoff_ms = (dt_to_s(SCORED_START - timedelta(days=LISTING_AGE_MIN_DAYS))) * 1000
    candidates, funding_hashes, dir_digests = [], {}, {}

    for bd in bar_dirs:
        symbol = os.path.basename(bd).split("-")[0]
        files = sorted(glob.glob(os.path.join(bd, "*.parquet")))
        inst = load_instrument(symbol)
        vol = median_daily_quote_volume_pre_window(files)
        cen_pre = census_for_symbol(files, PRE_START_S, PRE_END_S)
        cen_sc = census_for_symbol(files, SCORED_START_S, SCORED_END_S)

        meta_ok = bool(inst and inst["quote_currency"] == QUOTE_REQUIRED
                       and inst["contract_type"] == CONTRACT_TYPE_REQUIRED
                       and inst["status"] == "TRADING")
        age_days = None
        listing_ok = False
        if inst and inst["onboard_ms"]:
            # instrument age (days) at the conservative first possible exposure
            age_days = (dt_to_s(SCORED_START) * 1000 - inst["onboard_ms"]) / 86400000.0
            listing_ok = inst["onboard_ms"] <= listing_age_cutoff_ms

        fund_complete = None
        if symbol in funding_raw:
            fund_complete = analyze_funding(funding_raw[symbol], corroborate)
            funding_hashes[symbol] = sha256_file(funding_files[symbol])
        dir_digests[symbol] = bars_dir_digest(files)

        reasons = []
        if not meta_ok:
            reasons.append("METADATA_SANITY_FAIL")
        if not listing_ok:
            reasons.append("LISTING_AGE_LT_365D_AT_FIRST_EXPOSURE")
        if cen_pre["gaps_found"] > 0 or cen_pre["unexplained_gaps"] > 0:
            reasons.append("PRE_WINDOW_GAPS_PRESENT")
        if cen_sc["unexplained_gaps"] > 0:
            reasons.append("SCORED_WINDOW_UNEXPLAINED_GAPS")
        if fund_complete is None or not fund_complete["complete"]:
            reasons.append("FUNDING_HELD_EXPOSURE_INCOMPLETE")

        btc_rule_hit = symbol == BTC_SYMBOL
        eligible = meta_ok and listing_ok and not reasons
        candidates.append({
            "symbol": symbol,
            "instrument_id": inst["instrument_id"] if inst else f"{symbol}-PERP.{VENUE}",
            "metadata_sanity": {
                "present": inst is not None,
                "venue": VENUE,
                "quote_currency": inst["quote_currency"] if inst else None,
                "contract_type": inst["contract_type"] if inst else None,
                "status": inst["status"] if inst else None,
                "ok": meta_ok,
            },
            "onboard_date_utc": inst["onboard_date_utc"] if inst else None,
            "listing_age_days_at_first_possible_exposure":
                round(age_days, 2) if age_days is not None else None,
            "listing_age_gate_min_days": LISTING_AGE_MIN_DAYS,
            "volume": vol,
            "census_pre_window": cen_pre,
            "census_scored_window": cen_sc,
            "funding_held_exposure_audit": fund_complete,
            "btc_benchmark_measurement_only": btc_rule_hit,
            "eligible": eligible and not btc_rule_hit,
            "reason_if_rejected": (
                ["BTC_BENCHMARK_MEASUREMENT_ONLY_EXCLUDED_BEFORE_RANKING"] + reasons
                if btc_rule_hit else (reasons or None)),
        })

    ranked_pool = [c for c in candidates if c["eligible"]]
    chosen, ranked_all = rank_and_select(ranked_pool)

    for i, c in enumerate(chosen, 1):
        c["rank"] = i
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "agent": AGENT,
        "generated_at_utc": GENERATED_AT_UTC,
        "performance_blind": True,
        "correction_of": {
            "prior_commit": "4f1d704eeaa72713a1cd81455f8b24f1d61f6330",
            "prior_manifest_schema_version": "1.0.0",
            "violations_fixed": [
                "V1 ranking window was scored window -> now pre-window only",
                "V2 BTC included in traded top-10 -> now benchmark measurement-only, excluded before ranking",
                "V3 daily-granularity gap_day screen tolerated intra-day holes -> now exact 15-minute census over pre-window AND scored window with mandatory cause per gap; unexplained fails",
                "V4 funding gate rows>=1 -> now held-exposure completeness proof (contiguous legal intervals, boundary coverage from first possible weekly exposure, corroborated interval steps)",
            ],
        },
        "selection_window": {
            "start_utc": utc_str(PRE_START_S),
            "end_utc": utc_str(PRE_END_S),
            "note": "strictly BEFORE the scored window; ranking uses ONLY this window",
        },
        "scored_window": {"start_utc": utc_str(SCORED_START_S), "end_utc": utc_str(SCORED_END_S)},
        "ranking_rule": "median_daily_quote_volume_pre_window_only",
        "ranking_metric_detail": (
            "median over distinct pre-window UTC bar-days of the daily sum of the 15m "
            "parquet native quote_volume (USDT, Decimal-exact); even-count median = mean "
            "of the two central values"),
        "rank_tiebreak": "symbol asc (carried from prior frozen artifact)",
        "btc_excluded": True,
        "btc_exclusion_note": (
            f"{BTC_SYMBOL}-PERP.{VENUE} (equivalent of PERP.BINANCE.BTC-USDT) is the "
            "benchmark, measurement-only; excluded from the ranked/traded universe before ranking"),
        "listing_age_rule": (
            f"onboard_date <= scored-window start minus {LISTING_AGE_MIN_DAYS}d "
            f"(= {utc_str(dt_to_s(SCORED_START - timedelta(days=LISTING_AGE_MIN_DAYS)))}); "
            "consistent with prior artifact's >=365d preference; no contradicting frozen prereg found"),
        "rule_constants": {
            "catalog_root": CATALOG_ROOT,
            "bar_dir_rel": "data/binance_bar",
            "instrument_dir_rel": "data/crypto_perpetual",
            "funding_root": FUNDING_ROOT,
            "venue": VENUE,
            "quote_currency_required": QUOTE_REQUIRED,
            "contract_type_required": CONTRACT_TYPE_REQUIRED,
            "bar_spec_suffix": BAR_SUFFIX,
            "bar_interval_seconds": BAR_INTERVAL_S,
            "top_n": TOP_N,
            "max_funding_interval_seconds": MAX_FUNDING_INTERVAL_S,
            "legal_funding_intervals_seconds": list(LEGAL_FUNDING_INTERVALS_S),
            "funding_jitter_ms": FUNDING_JITTER_MS,
            "first_possible_exposure_utc": utc_str(dt_to_s(FIRST_POSSIBLE_EXPOSURE)),
        },
        "candidates_evaluated": candidates,
        "chosen_top10": [
            {
                "rank": c["rank"],
                "symbol": c["symbol"],
                "instrument_id": c["instrument_id"],
                "median_daily_quote_volume_pre_window_usdt":
                    c["volume"]["median_daily_quote_volume_usdt"],
                "days_with_bars_pre_window": c["volume"]["days_with_bars_pre_window"],
                "census_pre_window_gaps": c["census_pre_window"]["gaps_found"],
                "census_scored_window_gaps": c["census_scored_window"]["gaps_found"],
                "census_scored_window_unexplained": c["census_scored_window"]["unexplained_gaps"],
                "funding_held_exposure_complete":
                    c["funding_held_exposure_audit"]["complete"],
            }
            for c in chosen
        ],
        "not_selected_eligible": [
            {"symbol": c["symbol"],
             "median_daily_quote_volume_pre_window_usdt":
                 c["volume"]["median_daily_quote_volume_usdt"]}
            for c in ranked_all[TOP_N:]
        ],
        "audits": {
            "gap_census_15m_summary": {
                "scope": "exact 15-minute grid census, pre-window AND scored window, every candidate",
                "total_expected_slots_all_candidates_both_windows":
                    sum(c["census_pre_window"]["expected_15m_slots"]
                        + c["census_scored_window"]["expected_15m_slots"] for c in candidates),
                "total_gaps_found":
                    sum(c["census_pre_window"]["gaps_found"]
                        + c["census_scored_window"]["gaps_found"] for c in candidates),
                "total_unexplained_gaps":
                    sum(c["census_pre_window"]["unexplained_gaps"]
                        + c["census_scored_window"]["unexplained_gaps"] for c in candidates),
                "classification_rule": (
                    "run strictly inside ONE capture session's observed range => unexplained; "
                    "run bounded before/after/by capture-session edges => explained "
                    "capture-boundary cause"),
            },
            "selected_symbols_gap_census": {
                c["symbol"]: {"pre_window": c["census_pre_window"],
                              "scored_window": c["census_scored_window"]}
                for c in chosen
            },
            "metadata_sanity_all_ok": all(
                c["metadata_sanity"]["ok"] for c in candidates),
            "funding_held_exposure_coverage": {
                c["symbol"]: c["funding_held_exposure_audit"] for c in chosen
            },
            "eligibility_counts": {
                "candidates_evaluated": len(candidates),
                "excluded_btc_benchmark_only": sum(
                    1 for c in candidates if c["btc_benchmark_measurement_only"]),
                "altcoin_pool": len(candidates) - sum(
                    1 for c in candidates if c["btc_benchmark_measurement_only"]),
                "eligible_altcoins": len(ranked_pool),
                "rejected_altcoins": [
                    {"symbol": c["symbol"], "reasons": c["reason_if_rejected"]}
                    for c in candidates
                    if not c["btc_benchmark_measurement_only"] and not c["eligible"]],
                "selected": len(chosen),
            },
        },
        "verdict": ("V8X_CRYPTO_TOP10_ELIGIBLE_PREWINDOW_BENCHMARK_EXCLUDED"
                    if len(chosen) == TOP_N
                    and not any(c["census_scored_window"]["unexplained_gaps"]
                                or not c["funding_held_exposure_audit"]["complete"]
                                for c in chosen)
                    else "V8X_AUDIT_FAIL_UNEXPLAINED_GAPS_OR_FUNDING_INCOMPLETE"),
        "hashes": {
            "funding_json_sha256": dict(sorted(funding_hashes.items())),
            "bars_dir_digest_sha256": dict(sorted(dir_digests.items())),
        },
    }

    out = Path(manifest_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return manifest


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        repo_root / "data" / "v8x_manifests" / "crypto_universe_selection.json"
    m = main(out_path)
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print("verdict:", m["verdict"])
    print("eligibility:", m["audits"]["eligibility_counts"])
    print("census:", m["audits"]["gap_census_15m_summary"])
    print("chosen:", [c["symbol"] for c in m["chosen_top10"]])
    print("manifest:", out_path)
    print("manifest_sha256:", digest)
