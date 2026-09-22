#!/usr/bin/env python3
"""JRV1 freeze builder — generates every freeze contract from measured data
identity. Run once before any feature/outcome computation. Committed for
reproducibility; outputs under freezes/ are the frozen authority.

Deterministic: same inputs -> byte-identical JSON (sort_keys, indent=1).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import pathlib
from datetime import datetime, timezone

import numpy as np
import pyarrow.parquet as pq

ROOT = pathlib.Path("/Users/hoangminhlong/my-quantitative")
CYCLE = ROOT / ".worktrees/jev-regime-router-v1/integration/research/control/jev_regime_router_v1"
FREEZES = CYCLE / "freezes"

BTC_PARQUET = ROOT / "catalog/data/binance_bar/BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/2025-08-20T02-34-14-475394000Z_2026-08-20T02-34-14-475394000Z.parquet"
BTC_PARQUET_OVERLAP = ROOT / "catalog/data/binance_bar/BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/2026-07-20T04-54-14-416942000Z_2026-08-19T04-54-14-416942000Z.parquet"
SPY_LOCAL = CYCLE / "data_local/SPY.json.gz"
SPY_SOURCE = ROOT / ".worktrees/stocks-search-v1/integration/research/control/stocks_search_v1_run/p0/raw/eod_cache/SPY.json.gz"
SPY_MANIFEST_PIN = "0b6c4963f832d55a67d45c817fc7f1b17d7fe04fc856c037d06b72c0c6b9a8fd"

WARMUP_REGIME_BARS = 192
N_FOLDS = 4
BTC_FOLD_MIN_DECISIONS = 1000
SPY_FOLD_MIN_DECISIONS = 300
STABILITY_SEED = 20260922
STABILITY_N_BTC, STABILITY_N_SPY = 20, 10

BUILD_TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(name: str, obj: dict) -> str:
    path = FREEZES / name
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return name


def ns_to_iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------- data identity ----------------
def btc_15m_grid() -> dict:
    t = pq.read_table(BTC_PARQUET)
    d = t.to_pydict()
    ts = np.asarray(d["ts_event"], dtype=np.int64)  # bar CLOSE stamps (ns)
    # ts_event convention (measured): close stamped ~1ms BEFORE the clean
    # boundary (e.g. boundary-999936ns; offset varies slightly per bar).
    # Snap: close_norm = ceil(ts / 15m) * 15m (offset <=1ms, safe upward snap).
    # open = close_norm - 15m. H1 bucket = wall hour of OPEN time.
    M15 = 900_000_000_000
    snapped = np.where(ts % M15 == 0, ts, (ts // M15 + 1) * M15)
    opens = snapped - M15
    hour_buckets = (opens // 3_600_000_000_000) * 3_600_000_000_000  # hour START
    uniq, counts = np.unique(hour_buckets, return_counts=True)
    complete = uniq[counts == 4]
    partial = uniq[counts != 4]
    # verify alignment of minutes inside complete hours
    ok = True
    for h in complete:
        mask = hour_buckets == h
        mins = sorted(int((o - h) // 60_000_000_000) for o in opens[mask])
        if mins != [0, 15, 30, 45]:
            ok = False
    h1_close = complete + 3_600_000_000_000  # clean boundary ns
    return {
        "ts_event_convention": "bar close stamped 1us BEFORE clean boundary; normalize close snapped UP to next 15m boundary (offset <=1ms); open=close-15m; H1 bucket = floor(open/1h)",
        "rows": int(t.num_rows),
        "first_close": ns_to_iso(int(ts[0])),
        "last_close": ns_to_iso(int(ts[-1])),
        "h1_total_hours_spanned": int(len(uniq)),
        "h1_complete_hours": int(len(complete)),
        "h1_partial_hours": [
            {"hour_start": ns_to_iso(int(h)), "bars": int(c)}
            for h, c in zip(uniq[counts != 4], counts[counts != 4])
        ],
        "h1_alignment_all_ok": ok,
        "h1_first_complete_close": ns_to_iso(int(complete[0] + 3_600_000_000_000)),
        "h1_last_complete_close": ns_to_iso(int(complete[-1] + 3_600_000_000_000)),
        "h1_complete_closes": [int(x) for x in h1_close],
        "gap_15m_interior": int(len(complete) * 4 + sum(c for c in counts[counts != 4]) - t.num_rows),
    }


def spy_sessions() -> list[str]:
    data = json.loads(gzip.decompress(SPY_LOCAL.read_bytes()).decode())
    return [r["date"] for r in data]


def main() -> None:
    FREEZES.mkdir(parents=True, exist_ok=True)
    btc_grid = btc_15m_grid()
    spy_dates = spy_sessions()

    btc_file_sha = sha256_file(BTC_PARQUET)
    spy_sha = sha256_file(SPY_LOCAL)
    assert spy_sha == sha256_file(SPY_SOURCE), "local SPY copy drifted from source"

    # ---------------- folds ----------------
    h1 = btc_grid["h1_complete_closes"]
    btc_eval = h1[WARMUP_REGIME_BARS:]
    btc_folds = np.array_split(np.asarray(btc_eval), N_FOLDS)
    spy_eval = spy_dates[WARMUP_REGIME_BARS:]
    spy_folds = np.array_split(np.asarray(spy_eval), N_FOLDS)

    def fold_rec(arr, iso=True):
        return {
            "n_decisions": int(len(arr)),
            "start": ns_to_iso(int(arr[0])) if iso else str(arr[0]),
            "end": ns_to_iso(int(arr[-1])) if iso else str(arr[-1]),
        }

    # ---------------- stability sample (preregistered before ANY call) ----
    rng = np.random.default_rng(STABILITY_SEED)
    btc_idx = np.sort(rng.choice(len(btc_eval), size=STABILITY_N_BTC, replace=False))
    spy_idx = np.sort(rng.choice(len(spy_eval), size=STABILITY_N_SPY, replace=False))
    stability = {
        "seed": STABILITY_SEED,
        "sample_rule": "numpy default_rng(seed).choice(n, replace=False), sorted; "
                       "state_ids derived as sha256(asset_salt||bar_ts)[:16] with "
                       "asset_salt = sha256('JRV1'||asset||data_sha256)[:16]",
        "btcusdt": [
            {"i": int(i), "regime_bar_close": ns_to_iso(int(btc_eval[i]))} for i in btc_idx
        ],
        "spy": [{"i": int(i), "session_close_date": str(spy_eval[i])} for i in spy_idx],
        "n_repeat_calls": 2,
        "metric": "top1 agreement rate + probability L1 distance distribution",
    }

    # ---------------- freezes ----------------
    written = []
    written.append(dump("data_identity_freeze.json", {
        "schema": "jrv1_data_identity_freeze@1",
        "built_at_utc": BUILD_TS,
        "BTCUSDT": {
            "status": "ELIGIBLE",
            "source": "Binance USD-M perp 15m LAST-EXTERNAL bars (nautilus catalog capture)",
            "file": str(BTC_PARQUET),
            "file_sha256": btc_file_sha,
            "rows": btc_grid["rows"],
            "first_bar_close_utc": btc_grid["first_close"],
            "last_bar_close_utc": btc_grid["last_close"],
            "v8x_manifest_reference": "data/v8x_manifests/crypto_universe_selection.json bars_dir_digest_sha256=ac967c853c6658c620f27874f285daeeac65057c0e8816ccc007af4e464a3ccc (dir-level pin; file-level sha256 above is THIS cycle's binding pin)",
            "h1_resample_law": "hour h complete iff exactly 4 bars aligned :00/:15/:30/:45 close into h; open=first open, close=last close, high/low=extremes, volume=sum; partial hour -> INVALID, fail-closed",
            "h1_census": {
                "ts_event_convention": btc_grid["ts_event_convention"],
                "complete_hours": btc_grid["h1_complete_hours"],
                "partial_hours": btc_grid["h1_partial_hours"],
                "alignment_all_ok": btc_grid["h1_alignment_all_ok"],
                "first_complete_close": btc_grid["h1_first_complete_close"],
                "last_complete_close": btc_grid["h1_last_complete_close"],
                "gap_15m_interior": btc_grid["gap_15m_interior"],
            },
            "overlap_file_not_used": {
                "file": str(BTC_PARQUET_OVERLAP),
                "sha256": sha256_file(BTC_PARQUET_OVERLAP),
                "reason": "overlapping re-capture; primary file only",
            },
        },
        "SPY": {
            "status": "ELIGIBLE_DAILY_ONLY",
            "source": "EODHD EOD daily cache (entitlement EODHD_API_KEY), read-only copy from STOCKS-SEARCH-V1 p0 (BLOCKED cycle; source worktree untouched)",
            "file": str(SPY_LOCAL),
            "source_file": str(SPY_SOURCE),
            "file_sha256": spy_sha,
            "records": len(spy_dates),
            "first_session": spy_dates[0],
            "last_session": spy_dates[-1],
            "identity_findings": [
                {
                    "id": "SPY-SHA-MISMATCH-DISCLOSED",
                    "detail": "STOCKS-SEARCH-V1 retrieval_manifest double_pull pin "
                              f"{SPY_MANIFEST_PIN} does not byte-match the on-disk cache "
                              f"(gz sha {spy_sha}; decompressed sha differs too). File mtime "
                              "2026-09-17T17:40:58Z predates the manifest write "
                              "(2026-09-18T01:24:26Z): the pin most plausibly refers to the "
                              "fresh double-pull HTTP body (through session 2026-09-17) while "
                              "the cache holds through 2026-09-16.",
                    "resolution": "SNAPSHOT SEMANTICS: this cycle freezes the on-disk bytes as "
                                  "a point-in-time snapshot (retrieved <=2026-09-18). No re-pull: "
                                  "the EODHD adjusted channel is revision-prone (future dividends "
                                  "rewrite historical adjusted_close), so byte-stability requires "
                                  "freezing, not re-fetching. All arms run on the identical frozen "
                                  "vehicle (Q-14), so arm comparisons are unaffected. Disclosed, "
                                  "not silently resolved (P-1).",
                }
            ],
            "series_convention": "entire leg computed on back-adjusted series (total-return "
                                 "convention; adjusted_open = open*adjfactor inferred as "
                                 "adjusted_close/close*open per session); disclosed limitation: "
                                 "adjusted factors embed dividends recorded after past sessions "
                                 "(scale information, not direction); decisions use only "
                                 "relative structure of one consistent frozen series",
            "clock_law": "decision at completed session close t; fills at next session open; "
                         "no synthetic bars over closures; long-only (F6 no-borrow law)",
        },
        "EURUSD": {
            "status": "NOT_RUN",
            "reasons": [
                "no intraday EURUSD OHLCV anywhere in repo/worktrees",
                "daily TD archive digest-pinned but off-disk (file absent)",
                "forex broker cost authority BLOCKED_BROKER_COST_AUTHORITY (DEU lane-f dossier; only 1.5bps/fill floor + stress 2.0 exist)",
                "owner law: khong dung du lieu khong ro nguon de ep du ba asset",
            ],
        },
    }))

    written.append(dump("feature_contract.json", {
        "schema": "jrv1_feature_contract@1",
        "regime_clock": {"BTCUSDT": "H1 (resampled from 15m per data identity law)",
                         "SPY": "D1 session bars"},
        "warmup_regime_bars": WARMUP_REGIME_BARS,
        "causality_law": "completed bars only; strictly trailing windows; no centered window; no future normalization; no whole-sample statistics",
        "features": [
            {"id": "f01", "name": "r1", "def": "log(close_t/close_{t-1})"},
            {"id": "f02", "name": "r4", "def": "log(close_t/close_{t-4})"},
            {"id": "f03", "name": "r12", "def": "log(close_t/close_{t-12})"},
            {"id": "f04", "name": "r24", "def": "log(close_t/close_{t-24})"},
            {"id": "f05", "name": "r72", "def": "log(close_t/close_{t-72})"},
            {"id": "f06", "name": "ema_slope_fast", "def": "(EMA12_t/EMA12_{t-12}-1)/12"},
            {"id": "f07", "name": "ema_slope_slow", "def": "(EMA48_t/EMA48_{t-48}-1)/48"},
            {"id": "f08", "name": "dist_ema", "def": "(close/EMA50-1)/(ATR14/close)"},
            {"id": "f09", "name": "adx14", "def": "Wilder ADX(14)"},
            {"id": "f10", "name": "atr_pct", "def": "ATR14/close"},
            {"id": "f11", "name": "rv_pctile", "def": "rank of rv24_t among its trailing 168 PAST values (exclusive) /168; rv24 = std of last 24 log returns"},
            {"id": "f12", "name": "dd_168", "def": "close/max(close,168)-1"},
            {"id": "f13", "name": "dist_low", "def": "close/min(close,168)-1"},
            {"id": "f14", "name": "range_pos", "def": "(close-min24)/(max24-min24)-0.5; 0.0 if max24==min24"},
            {"id": "f15", "name": "vol_z", "def": "(v/mean168-1)/(std168/mean168)"},
            {"id": "f16", "name": "clv_24", "def": "mean over last 24 bars of (close-low)/(high-low), zero-range bars dropped; fail-closed if all 24 zero-range"},
            {"id": "f17", "name": "prior_regime", "def": "one-hot(5) of persisted regime in force at t-1; all-zero before first persisted state"},
        ],
        "state_payload_law": {
            "state_object": {"feature_vector": "f01..f16 plain numbers", "prior_regime": "label string or null"},
            "forbidden_anywhere": ["symbol", "absolute dates", "absolute prices/volumes", "calendar features", "session/day-of-week (NOT preregistered)", "strategy PnL / future returns / fold verdicts", "event names"],
            "state_id": "sha256(asset_salt||bar_ts)[:16]; asset_salt=sha256('JRV1'||asset||data_sha256)[:16]; opaque",
            "non_finite_features": "state NOT sent; decision locally TRANSITION_UNKNOWN (status LOCAL_INVALID)",
        },
    }))

    written.append(dump("regime_label_contract.json", {
        "schema": "jrv1_regime_label_contract@1",
        "labels": ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND", "TRANSITION_UNKNOWN"],
        "definitions_outcome_blind": {
            "ACCUMULATION": "a downtrend occurred previously; price now ranges/compresses; downside pressure is weakening (defined ONLY by past structure, never by future price direction)",
            "UPTREND": "a positive causal trend exists now: higher-price structure and measurable trend strength",
            "DISTRIBUTION": "an uptrend occurred previously; price now ranges/compresses; upside pressure is weakening",
            "DOWNTREND": "a negative causal trend exists now: lower-price structure and measurable downside pressure",
            "TRANSITION_UNKNOWN": "evidence conflicts, confidence is low, data is insufficient, or the state is changing",
        },
        "response_fields_required": ["regime", "probabilities(all5,sum=1+/-0.01)", "confidence", "model", "request_id", "input_digest", "latency_ms", "status"],
        "free_text_regime": "REJECTED -> SCHEMA_ERROR -> TRANSITION_UNKNOWN",
    }))

    written.append(dump("persistence_contract.json", {
        "schema": "jrv1_persistence_contract@1",
        "params": {"min_confidence": 0.50, "min_margin": 0.20, "confirm_bars": 2,
                   "min_dwell": 6, "cooldown": 3},
        "rationale_outcome_blind": "chosen from regime semantics + synthetic fixtures: a 5-class "
                                   "probability vector needs a majority belief (0.50) separated "
                                   "from the runner-up (0.20 margin); 2-bar confirmation kills "
                                   "single-bar flapping; 6-bar dwell (BTC 6h / SPY 6 sessions) "
                                   "prevents whipsaw regime changes; 3-bar cooldown bars a "
                                   "rejected candidate from immediate re-candidacy. NO PnL was "
                                   "computed when choosing these numbers.",
        "algorithm": [
            "state := UNKNOWN initially (and after warmup)",
            "each regime bar: raw = top1 label if (confidence>=min_confidence and p1-p2>=min_margin and status==OK) else UNKNOWN-candidate",
            "if raw != current regime: candidate(raw) counter++ ; if counter>=confirm_bars and bars_in_current>=min_dwell: switch (candidate must equal raw on each of the confirm bars, else reset)",
            "on switch: bars_in_current=0; failed candidates enter cooldown (label barred from candidacy for cooldown bars)",
            "any error/LOCAL_INVALID -> treated as UNKNOWN-candidate (never auto-switch on errors)",
            "output regime label per bar = persisted state",
        ],
        "applies_to": ["JEV classifier (arm E)", "deterministic router (arm D)"],
    }))

    written.append(dump("regime_strategy_mapping_freeze.json", {
        "schema": "jrv1_regime_strategy_mapping_freeze@1",
        "mapping": {
            "ACCUMULATION": {"BTCUSDT": "MR_LONG", "SPY": "MR_LONG"},
            "UPTREND": {"BTCUSDT": "TREND_LONG", "SPY": "TREND_LONG"},
            "DISTRIBUTION": {"BTCUSDT": "FLAT", "SPY": "FLAT"},
            "DOWNTREND": {"BTCUSDT": "TREND_SHORT", "SPY": "FLAT"},
            "TRANSITION_UNKNOWN": {"BTCUSDT": "FLAT", "SPY": "FLAT"},
        },
        "mapping_rationale": "code-owned, frozen before any outcome; DISTRIBUTION flat everywhere "
                             "(short-side MR lacks frozen authority for SPY by F6 long-only law; "
                             "one uniform mapping, no asset-specific post-hoc additions); SPY "
                             "DOWNTREND flat by the same long-only law; BTC DOWNTREND short is "
                             "supported by its symmetric cost contract",
        "strategies": {
            "TREND_LONG": {
                "entry": "close>EMA20 and EMA20>EMA50 (execution clock), flat",
                "exit": "close<EMA20 | intrabar stop entry-3*ATR14 | regime turns this strategy off | fold force-flat",
                "ancestry": "strategy.py ema_atr / strategy_trend_pullback.py lineage",
            },
            "TREND_SHORT": {
                "instrument": "BTCUSDT only",
                "entry": "close<EMA20 and EMA20<EMA50, flat",
                "exit": "close>EMA20 | intrabar stop entry+3*ATR14 | regime off | fold force-flat",
                "funding": "signed, charged per 8h boundary on open notional",
            },
            "MR_LONG": {
                "entry": "RSI14<30 and close<BOLL(20,2.0) lower, flat",
                "exit": "close>=BOLL mid | RSI14>55 | 96 execution bars max hold | intrabar stop entry-2*ATR14 | regime off | fold force-flat",
                "ancestry": "strategy_mean_reversion.py (RSI 30/55, BOLL 20/2, 2*ATR stop; wide-stop doctrine NOTES 4.2)",
            },
            "FLAT": "no position; open position exits at next execution bar open when the active regime maps away",
        },
        "position_sizing": "notional fraction 1.0 of current equity per position; one position at a time; no leverage anywhere",
        "regime_change_rule": "on persisted regime change, position reconciles to the new regime's strategy target at next execution bar open",
        "remapping_law": "this file's sha256 is asserted by the runner at start; changing it after ANY outcome is a cycle violation",
    }))

    written.append(dump("fold_contract.json", {
        "schema": "jrv1_fold_contract@1",
        "law": "chronological walk-forward; boundaries frozen before any outcome; no train/test split (nothing is fitted: Jev model fixed, strategies frozen, persistence frozen); positions force-liquidated at fold end (cost debited); features roll continuously across boundaries (causal); next fold decisions start with prior-regime state carried over",
        "BTCUSDT": {
            "n_folds": N_FOLDS, "warmup_regime_bars": WARMUP_REGIME_BARS,
            "total_h1_complete": btc_grid["h1_complete_hours"],
            "evaluable_decisions": int(len(btc_eval)),
            "floor_per_fold": BTC_FOLD_MIN_DECISIONS,
            "folds": [fold_rec(f) for f in btc_folds],
            "clock": "regime decision at H1 close t (features from 15m bars <= t); execution on 15m bars strictly after t; first possible fill = first 15m bar open after t",
        },
        "SPY": {
            "n_folds": N_FOLDS, "warmup_regime_bars": WARMUP_REGIME_BARS,
            "total_sessions": len(spy_dates),
            "evaluable_decisions": int(len(spy_eval)),
            "floor_per_fold": SPY_FOLD_MIN_DECISIONS,
            "folds": [fold_rec(f, iso=False) for f in spy_folds],
            "clock": "decision at session close t; fill at next session open",
        },
    }))

    written.append(dump("cost_contract.json", {
        "schema": "jrv1_cost_contract@1",
        "BTCUSDT": {
            "status": "DECLARED_CONSERVATIVE_BOUND",
            "taker_fee_bps_per_side": 5.0,
            "slippage_bps_per_side": 1.0,
            "round_trip_bps": 12.0,
            "funding": {"rate_per_8h_on_signed_notional": 1.377e-5,
                        "source": "CRYPTO-NG4 plan sec7 frozen constant (measured from FDF census bytes)",
                        "charge_rule": "every 8h UTC boundary the position is open, on signed notional"},
            "stress_multiplier": 2.0,
            "disclosure_q8": "fee/slip are exchange-schedule-derived conservative bounds, not broker-measured; every arm runs on the identical bound and a 1.0x/1.5x/2.0x cost sweep is reported so no verdict hinges on the bound",
        },
        "SPY": {
            "status": "FROZEN_BAND_MODEL_F6",
            "band": "A (ADV>>$50M)",
            "cost_bps_per_fill": 10.0,
            "stress_multiplier": 2.0,
            "ceiling_round_trip_bps": 40.0,
            "source": "plans/PLAN_stocks_search_v1.md F6 (kernel_band_cost_v9 lineage); cost once per fill; long-only",
        },
        "cost_debit_law": "debited exactly once per fill at fill price; stop fills cost too; fold force-flat costs; no silent zero anywhere",
    }))

    written.append(dump("evaluation_contract.json", {
        "schema": "jrv1_evaluation_contract@1",
        "metrics_per_arm": ["gross_pnl", "costs_fee", "costs_slip", "costs_funding", "net_pnl",
                            "total_return", "cagr", "sharpe", "sortino", "max_drawdown",
                            "profit_factor", "expectancy_per_trade", "trades", "win_rate",
                            "turnover", "time_in_market", "regime_switches", "regime_occupancy",
                            "avg_dwell", "unknown_share", "fold_by_fold", "concentration_top_fold_profit_share",
                            "skipped_trade_pnl", "margin_to_fail_vs_each_arm", "cost_sweep_1x_1p5x_2x"],
        "per_fold_series_persisted": "mandatory (P-11): per-fold per-period returns + per-regime classification logs persisted as launch-contract outputs; DSR/PBO computed at terminal when series suffice",
        "gates": {
            "fold_concentration_kill": "top-fold profit share > 0.50 kills a positive claim (V14 precedent)",
            "fold_floor": "decisions/fold >= fold_contract floor, fail-closed",
            "single_asset_dependency_kill": "JEV_INCREMENTAL_VALUE_SUPPORTED requires net-positive + beats B,C,D,F(median) on BOTH instruments",
            "reproduction": "byte-level decisions+ledger ALL_MATCH required",
            "a7_terminal": "zero unresolved HIGH/CRITICAL",
        },
        "seven_questions": [
            "1 Jev vs always-on (B,C) after costs?",
            "2 Jev vs deterministic router (D)?",
            "3 Jev vs random matched (F median)?",
            "4 PnL of trades Jev blocked (skipped-trade by regime)?",
            "5 regime intelligence vs trading less (invested-fraction normalization + turnover)?",
            "6 stable across folds AND instruments?",
            "7 switching-cost attrition (cost share on switch days, stress tier)?",
        ],
        "terminal_vocabulary": ["JEV_INCREMENTAL_VALUE_SUPPORTED", "JEV_NO_INCREMENTAL_VALUE",
                                "JEV_INCONSISTENT_ACROSS_FOLDS_OR_ASSETS",
                                "BLOCKED_CREDENTIAL_OR_COST", "BLOCKED_DATA",
                                "BLOCKED_CONTROL_STATE", "TECHABORT"],
        "reports": ["REGIME_CLASSIFICATION_REPORT.md", "REGIME_BACKTEST_REPORT.md"],
        "matrix_law": "strategy x Jev-regime matrix is DIAGNOSTIC ONLY; remapping strategies after seeing it inside this cycle is forbidden",
    }))

    written.append(dump("controls_contract.json", {
        "schema": "jrv1_controls_contract@1",
        "controls": {
            "delayed_feature_control": "Jev decisions recomputed with features shifted +1 regime bar (bulk phase; measures pipeline sensitivity to staleness)",
            "shuffled_regime_control": "Jev realized regime path segments permuted in time (seeded x21); measures whether timing carries information",
            "random_matched_router_arm_F": "segment permutation null preserving segment lengths; matching targets occupancy +-2pp, switches +-10%, mean dwell +-10%, invested fraction +-2pp; fail-closed NOT_RUN_CONTROL_MATCHING with measured deltas; headline = median of 21 seeds; Q-11 live-null verification: lag-1 label autocorrelation and regime->forward-return association must MOVE vs Jev path (else null invalid, disclosed)",
            "deterministic_router_arm_D": "trend x vol classifier (EMA12/48 structure, ADX14>=22, trailing-168 return +-10% for range-after-trend labels) + SAME persistence layer",
            "no_persistence_diagnostic": "raw Jev labels without persistence: switch-count inflation + what persistence bought",
            "unknown_always_flat_control": "mapping replaced by {UNKNOWN->FLAT, else TREND_LONG}: isolates the value of UNKNOWN gating",
            "repeated_decision_stability": "preregistered sample below; 2 calls per state; top1 agreement + probability L1 distance",
        },
        "stability_sample_preregistered": stability,
    }))

    fixtures = {
        "schema": "jrv1_synthetic_canary_fixtures@1",
        "law": "expected labels frozen BEFORE any live call; mock canaries validate plumbing (smoke namespace, kill-only per P-15); live canaries (<=100 budget) validate provider",
        "feature_order": ["r1", "r4", "r12", "r24", "r72", "ema_slope_fast", "ema_slope_slow",
                          "dist_ema", "adx14", "atr_pct", "rv_pctile", "dd_168", "dist_low",
                          "range_pos", "vol_z", "clv_24"],
        "fixtures": [
            {"id": "FIX1_CLEAR_UPTREND", "prior_regime": None,
             "vector": [0.004, 0.020, 0.050, 0.110, 0.280, 0.0040, 0.0025, 1.2, 34.0, 0.008, 0.62, -0.03, 0.30, 0.42, 0.35, 0.62],
             "expected_acceptable": ["UPTREND"]},
            {"id": "FIX2_CLEAR_DOWNTREND", "prior_regime": None,
             "vector": [-0.005, -0.025, -0.060, -0.130, -0.300, -0.0040, -0.0028, -1.4, 31.0, 0.011, 0.78, -0.26, -0.002, -0.38, 0.50, 0.35],
             "expected_acceptable": ["DOWNTREND"]},
            {"id": "FIX3_RANGE_AFTER_DOWNTREND", "prior_regime": "DOWNTREND",
             "vector": [0.001, 0.004, -0.003, -0.010, -0.180, 0.0004, -0.0015, -0.2, 14.0, 0.006, 0.30, -0.19, 0.04, 0.10, -0.30, 0.47],
             "expected_acceptable": ["ACCUMULATION", "TRANSITION_UNKNOWN"]},
            {"id": "FIX4_RANGE_AFTER_UPTREND", "prior_regime": "UPTREND",
             "vector": [-0.001, -0.004, 0.003, 0.012, 0.220, -0.0004, 0.0018, 0.25, 15.0, 0.007, 0.35, -0.05, 0.24, 0.25, -0.20, 0.50],
             "expected_acceptable": ["DISTRIBUTION", "TRANSITION_UNKNOWN"]},
            {"id": "FIX5_CONTRADICTORY_NOISY", "prior_regime": "UPTREND",
             "vector": [0.006, -0.020, 0.030, -0.050, 0.070, 0.0020, -0.0010, 0.6, 19.0, 0.013, 0.92, -0.11, 0.09, 0.45, 1.80, 0.52],
             "expected_acceptable": ["TRANSITION_UNKNOWN"]},
            {"id": "FIX6_MISSING_STALE", "prior_regime": None,
             "vector": None,
             "expected_acceptable": ["TRANSITION_UNKNOWN"],
             "handling": "NOT SENT to provider; locally forced TRANSITION_UNKNOWN (status LOCAL_INVALID)"},
        ],
        "pass_criteria": ["valid schema", "no unsupported label", "missing/stale => UNKNOWN",
                          "directional fixtures (FIX1/FIX2) not inverted",
                          "raw request/response hashed and stored", "zero credential leakage"],
    }
    written.append(dump("synthetic_canary_fixtures.json", fixtures))

    written.append(dump("adapter_contract.json", {
        "schema": "jrv1_adapter_contract@1",
        "sdk": {"package": "@typesafe-ai/sdk", "pinned_version": "0.6.0",
                "pin_method": "package-lock exact version (no range); measured latest 2026-09-22",
                "runtime": "node>=20 (host 24.5.0)"},
        "auth": {"env": "TYPESAFE_API_KEY", "law": "environment only; never in prompts/logs/git/handoff/manifests; no browser execution (dangerouslyAllowBrowser stays false)"},
        "model_pin": {
            "procedure": "client.models.list() at canary time -> freeze exact model name (highest non-alias version)",
            "jev_latest": "FORBIDDEN in frozen replay (owner law + SDK default fallback trap)",
            "status_without_key": "CANDIDATE_UNVERIFIED -> all live calls BLOCKED_CREDENTIAL",
            "response_model_must_equal_pin": True,
        },
        "call_discipline": {"maxRetries": 0, "timeout_ms": 10000,
                            "error_law": "APIError/APIConnectionError/APITimeoutError/schema violation -> TRANSITION_UNKNOWN with status; NO re-asking for a nicer answer",
                            "one_call_per_state_id": True, "cache": "append-only JSONL, replay reads cache never re-calls"},
        "io_schema": "jrv1_decision_io@1",
        "request_line": {"schema": "jrv1_decision_io@1", "state_id": "str16hex", "state": "object(feature_vector[16], prior_regime)", "requested_model": "str"},
        "response_line": {"schema": "jrv1_decision_io@1", "state_id": "str", "status": "OK|TIMEOUT|PROVIDER_ERROR|SCHEMA_ERROR|LOCAL_INVALID",
                          "regime": "label?", "probabilities": "{label:float}?", "confidence": "float?",
                          "model": "str?", "request_id": "str?", "input_digest": "sha256(canonical_json(state)||requested_model)",
                          "latency_ms": "float", "error_class": "str?"},
        "boundary": "TypeScript = SDK adapter + schema validation + capture only; Python = data/features/folds/backtest/accounting",
    }))

    written.append(dump("model_pin.json", {
        "schema": "jrv1_model_pin@1",
        "status": "CANDIDATE_UNVERIFIED",
        "pinned_model": None,
        "pinned_at_utc": None,
        "models_list_evidence": None,
        "note": "filled at G0 canary only when TYPESAFE_API_KEY is present; until then every live call is BLOCKED_CREDENTIAL",
    }))

    manifest = {
        "schema": "jrv1_freeze_manifest@1",
        "built_at_utc": BUILD_TS,
        "builder": "research/control/jev_regime_router_v1/tools/build_freezes.py",
        "files": {},
    }
    for name in written:
        manifest["files"][name] = hashlib.sha256((FREEZES / name).read_bytes()).hexdigest()
    dump("freeze_manifest.json", manifest)
    print(json.dumps({"written": written,
                      "btc_evaluable": int(len(btc_eval)),
                      "spy_evaluable": int(len(spy_eval)),
                      "btc_folds": [fold_rec(f) for f in btc_folds],
                      "spy_folds": [fold_rec(f, iso=False) for f in spy_folds]}, indent=1))


if __name__ == "__main__":
    main()
