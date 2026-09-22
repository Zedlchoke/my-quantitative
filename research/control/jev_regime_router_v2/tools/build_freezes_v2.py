#!/usr/bin/env python3
"""JRV2 freeze builder — generates every V2 freeze contract from measured
data identity + domain-standard bins. Deterministic; committed for
reproducibility. No historical outcome is consulted anywhere."""
from __future__ import annotations

import gzip
import hashlib
import json
import pathlib
from datetime import datetime, timezone

import numpy as np
import pyarrow.parquet as pq

ROOT = pathlib.Path("/Users/hoangminhlong/my-quantitative")
CYCLE = ROOT / ".worktrees/jev-regime-router-v2/integration/research/control/jev_regime_router_v2"
FREEZES = CYCLE / "freezes"
BTC_PARQUET = ROOT / "catalog/data/binance_bar/BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/2025-08-20T02-34-14-475394000Z_2026-08-20T02-34-14-475394000Z.parquet"
SPY_LOCAL = ROOT / ".worktrees/jev-regime-router-v1/integration/research/control/jev_regime_router_v1/data_local/SPY.json.gz"

WARMUP = 192
N_FOLDS = 4
PREVIEW_N = 100
PERTURB_N = 8
SEED = 20260923
BUILD_TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(name: str, obj: dict) -> str:
    (FREEZES / name).write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return name


def ns_to_iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def btc_grid():
    t = pq.read_table(BTC_PARQUET)
    ts = np.asarray(t.to_pydict()["ts_event"], dtype=np.int64)
    M15 = 900_000_000_000
    snapped = np.where(ts % M15 == 0, ts, (ts // M15 + 1) * M15)
    opens = snapped - M15
    out = {}
    for label, span in (("h1", 4), ("h4", 16)):
        bucket = (opens // (span * M15)) * (span * M15)
        uniq, counts = np.unique(bucket, return_counts=True)
        complete = uniq[counts == span]
        align_ok = True
        for h in complete:
            mask = bucket == h
            offs = sorted(int((o - h) // M15) for o in opens[mask])
            if offs != list(range(span)):
                align_ok = False
        out[label] = {
            "complete": [int(x + span * M15) for x in complete],  # close boundary ns
            "partial": [
                {"bucket_start": ns_to_iso(int(h)), "bars": int(c)}
                for h, c in zip(uniq[counts != span], counts[counts != span])
            ],
            "align_ok": align_ok,
            "interior_gaps": int(len(complete) * span + sum(c for c in counts[counts != span]) - t.num_rows),
        }
    return out, sha256_file(BTC_PARQUET), int(t.num_rows)


def spy_sessions():
    data = json.loads(gzip.decompress(SPY_LOCAL.read_bytes()).decode())
    return [r["date"] for r in data], sha256_file(SPY_LOCAL), len(data)


def main() -> None:
    FREEZES.mkdir(parents=True, exist_ok=True)
    grid, btc_sha, btc_rows = btc_grid()
    spy_dates, spy_sha, spy_n = spy_sessions()

    h1 = grid["h1"]["complete"]
    h4 = grid["h4"]["complete"]
    spy_eval = spy_dates[WARMUP:]

    def folds_from(arr, iso=True):
        parts = np.array_split(np.asarray(arr), N_FOLDS)
        return [
            {"n_decisions": int(len(p)),
             "start": ns_to_iso(int(p[0])) if iso else str(p[0]),
             "end": ns_to_iso(int(p[-1])) if iso else str(p[-1])}
            for p in parts
        ]

    h1_eval = h1[WARMUP:]
    h4_eval = h4[WARMUP:]

    # preview sample: preregistered timestamp rule over BTC-H1 evaluable states
    preview_idx = sorted({int(k * len(h1_eval) / PREVIEW_N) for k in range(PREVIEW_N)})

    written = []
    written.append(dump("data_identity_freeze.json", {
        "schema": "jrv2_data_identity_freeze@1",
        "built_at_utc": BUILD_TS,
        "BTCUSDT": {
            "status": "ELIGIBLE",
            "file": str(BTC_PARQUET), "file_sha256": btc_sha, "rows": btc_rows,
            "ts_convention": "closes stamped <=1ms early; snap = ceil to next 15m boundary; open = close-15m; buckets by wall-clock open",
            "h1_census": {"complete": len(h1), "partial": grid["h1"]["partial"],
                          "align_ok": grid["h1"]["align_ok"], "interior_gaps": grid["h1"]["interior_gaps"]},
            "h4_census": {"complete": len(h4), "partial": grid["h4"]["partial"],
                          "align_ok": grid["h4"]["align_ok"], "interior_gaps": grid["h4"]["interior_gaps"],
                          "law": "H4 bucket = floor(open/4h)*4h (UTC 00/04/08/12/16/20); complete iff exactly 16 aligned bars"},
        },
        "SPY": {
            "status": "ELIGIBLE_DAILY_ONLY",
            "file": str(SPY_LOCAL),
            "source_lineage": "read-only reuse of the V1 frozen snapshot (same bytes, same disclosed snapshot semantics SPY-SHA-MISMATCH-DISCLOSED; no re-pull)",
            "file_sha256": spy_sha, "records": spy_n,
            "first_session": spy_dates[0], "last_session": spy_dates[-1],
            "clock_law": "decision at session close; fill next session open; long-only",
        },
        "EURUSD": {"status": "NOT_RUN", "reasons": ["no intraday authority on disk", "cost authority BLOCKED_BROKER_COST_AUTHORITY"]},
        "v2_salt_law": "state_id salts are namespaced JRV2 (sha256('JRV2'||asset||data_sha)) — disjoint from V1 by construction; a collision test is mandatory in tests",
    }))

    written.append(dump("semantic_state_contract.json", {
        "schema": "jrv2_semantic_state_contract@1",
        "warmup_regime_bars": WARMUP,
        "causality_law": "trailing-only windows; no centered/future normalization; same feature math as V1 f01..f16 (identical formulas); every field carries a name and a semantic bin",
        "bins": {
            "fast_trend": {"field": "ema_slope_fast", "thresholds": [-0.002, -0.0003, 0.0003, 0.002],
                            "labels": ["strong_down", "weak_down", "flat", "weak_up", "strong_up"]},
            "slow_trend": {"field": "ema_slope_slow", "thresholds": [-0.0015, -0.0002, 0.0002, 0.0015],
                            "labels": ["strong_down", "weak_down", "flat", "weak_up", "strong_up"]},
            "trend_strength": {"field": "adx14", "thresholds": [20, 30], "labels": ["low", "medium", "high"],
                                "rationale": "Wilder-standard ADX conventions (20 trend / 30 strong trend)"},
            "volatility_regime": {"field": "rv_pctile", "thresholds": [0.25, 0.75, 0.90],
                                   "labels": ["low", "normal", "high", "extreme"],
                                   "rationale": "distribution quartiles of a trailing percentile"},
            "drawdown_state": {"field": "dd_168", "thresholds": [-0.20, -0.05],
                                "labels": ["deep", "mild", "near_high"], "note": "dd_168 <= -0.20 deep; -0.20..-0.05 mild; > -0.05 near_high"},
            "range_location": {"field": "range_pos", "thresholds": [-0.30, 0.30],
                                "labels": ["near_low", "middle", "near_high"]},
            "close_location": {"field": "clv_24", "thresholds": [0.40, 0.60], "labels": ["weak", "neutral", "strong"]},
            "volume_state": {"field": "vol_z", "thresholds": [-1, 1], "labels": ["low", "normal", "high"]},
            "dist_to_ema": {"field": "dist_ema", "thresholds": [-1.5, -0.25, 0.25, 1.5],
                             "labels": ["extended_below", "below", "at", "above", "extended_above"]},
            "prior_structure": {"from": "persisted effective regime",
                                 "map": {"UPTREND": "TREND_UP", "DOWNTREND": "TREND_DOWN",
                                         "ACCUMULATION": "RANGE", "DISTRIBUTION": "RANGE",
                                         "TRANSITION_UNKNOWN": "RANGE", "null": "none"}},
            "prior_direction": {"from": "persisted effective regime",
                                 "map": {"UPTREND": "UP", "DOWNTREND": "DOWN",
                                         "ACCUMULATION": "DOWN", "DISTRIBUTION": "UP",
                                         "TRANSITION_UNKNOWN": "NEUTRAL", "null": "none"}},
        },
        "raw_numerics_with_names": ["short_return(r4)", "medium_return(r24)", "long_return(r72)",
                                     "ema_slope_fast", "ema_slope_slow", "dist_ema", "adx14", "atr_pct",
                                     "rv_pctile", "dd_168", "dist_low", "range_pos", "vol_z", "clv_24"],
        "state_payload_law": {"forbidden": ["symbol", "absolute dates", "price levels", "calendar features", "event names", "PnL/outcomes"],
                               "state_id": "sha256('JRV2'||asset||data_sha||bar_ts)[:16]"},
        "bin_freeze_rationale": "domain-standard indicator conventions + synthetic fixtures, frozen BEFORE any historical call; no PnL consulted (V1 labels used ONLY to name UNKNOWN_COLLAPSE)",
    }))

    written.append(dump("question_contract.json", {
        "schema": "jrv2_question_contract@1",
        "one_call_law": "exactly one systemOne call per state carrying THREE typed questions; two-call designs are forbidden; no silent call-count inflation",
        "questions": {
            "structure": {"type": "choice", "options": ["TREND", "RANGE"]},
            "direction": {"type": "choice", "options": ["UP", "DOWN", "NEUTRAL"]},
            "phase": {"type": "choice", "options": ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"],
                       "law": "FORCED CHOICE — TRANSITION_UNKNOWN is NOT an option; the model may never abstain"},
        },
        "consistency_law": [
            "TREND + UP -> UPTREND", "TREND + DOWN -> DOWNTREND",
            "RANGE + NEUTRAL + prior_direction DOWN -> ACCUMULATION",
            "RANGE + NEUTRAL + prior_direction UP -> DISTRIBUTION",
            "RANGE + NEUTRAL + prior_direction NEUTRAL -> contradiction (UNKNOWN)",
            "TREND + NEUTRAL -> contradiction (UNKNOWN)", "RANGE + UP -> contradiction (UNKNOWN)", "RANGE + DOWN -> contradiction (UNKNOWN)",
            "phase != structure x direction expectation -> contradiction (UNKNOWN)",
            "phase ACCUMULATION requires prior_direction DOWN; phase DISTRIBUTION requires prior_direction UP; else contradiction (UNKNOWN)",
        ],
        "response_required": ["per-question choice", "per-question probabilities", "per-question confidence",
                               "model == pin", "request_id", "usage(input/output tokens) persisted per response"],
        "digest_laws": {"input_digest": "producer-computed sha256(canonical_json(state)||model) (V1 amendment_1 law)",
                         "cache_key": "sha256(model||state_id||input_digest||prompt_digest) (V1 amendment_2 law)"},
        "io_schema": "jrv2_question_io@1",
        "prompt_revision_budget": {"max_revisions_before_historical": 2,
                                    "law": "each revision is an observed design trial, fully disclosed with fixtures evidence; after the FIRST historical preview call the prompt is FROZEN",
                                    "v0": "full named semantic schema (field list + bins + meanings), hierarchy rules verbatim, forced-choice instruction, anonymization note"},
    }))

    written.append(dump("safety_persistence_contract.json", {
        "schema": "jrv2_safety_persistence_contract@1",
        "code_owned_unknown_triggers": [
            "provider/schema failure", "missing or stale state",
            "phase confidence < 0.50", "phase top1-top2 margin < 0.20",
            "hierarchical contradiction (question_contract consistency_law)",
            "persistence confirmation failure",
        ],
        "no_forced_trades_law": "confidence/margin thresholds are NEVER lowered to increase trade count",
        "no_double_abstention_law": "the model never receives an UNKNOWN option (schema-enforced); abstention exists ONLY in code",
        "effective_regime_algorithm": [
            "provider ok AND phase_conf>=0.50 AND phase_margin>=0.20 AND hierarchy consistent -> phase label",
            "else -> TRANSITION_UNKNOWN",
        ],
        "persistence_params": {"min_confidence": 0.50, "min_margin": 0.20, "confirm_bars": 2,
                                "min_dwell": 6, "cooldown": 3,
                                "note": "applied to EFFECTIVE labels; identical machine to V1 frozen law"},
    }))

    written.append(dump("mapping_arms_freeze.json", {
        "schema": "jrv2_mapping_arms_freeze@1",
        "mapping": {
            "ACCUMULATION": {"BTCUSDT": "MR_LONG", "SPY": "MR_LONG"},
            "UPTREND": {"BTCUSDT": "TREND_LONG", "SPY": "TREND_LONG"},
            "DISTRIBUTION": {"BTCUSDT": "FLAT", "SPY": "FLAT"},
            "DOWNTREND": {"BTCUSDT": "TREND_SHORT", "SPY": "FLAT"},
            "TRANSITION_UNKNOWN": {"BTCUSDT": "FLAT", "SPY": "FLAT"},
        },
        "strategies": "identical frozen specs to V1 regime_strategy_mapping_freeze (TREND_LONG/TREND_SHORT BTC-only/MR_LONG/FLAT; next-bar-open fills; fraction 1.0; fold force-flat)",
        "arms": {
            "ALWAYS_ON_TREND": "TREND_LONG always active",
            "ALWAYS_ON_MEAN_REVERSION": "MR_LONG always active",
            "DETERMINISTIC_REGIME_ROUTER": "V1 arm-D classifier (EMA12/48 structure, ADX>=22, +-10% trailing-168) + same persistence",
            "JEV_ONLY_ROUTER": "effective Jev regime drives the mapping",
            "DETERMINISTIC_PLUS_JEV_CONFIRMATION": "deterministic law proposes the regime; trade its strategy IFF Jev effective regime equals the proposal; ANY disagreement -> flat; Jev never selects alone, disagreement never invents a strategy",
            "RANDOM_MATCHED_ROUTER": "21 seeded segment-permutation null matched to the JEV_ONLY path (occupancy +-2pp, switches +-10%, dwell +-10%, invested +-2pp; Q-11 movement checks; fail-closed NOT_RUN_CONTROL_MATCHING)",
        },
        "costs": {
            "BTCUSDT": {"taker_fee_bps_per_side": 5.0, "slippage_bps_per_side": 1.0,
                         "funding_per_8h_signed": 1.377e-5, "stress": 2.0,
                         "status": "DECLARED_CONSERVATIVE_BOUND"},
            "SPY": {"cost_bps_per_fill": 10.0, "stress": 2.0, "status": "FROZEN_BAND_MODEL_F6", "long_only": True},
        },
    }))

    written.append(dump("fold_contract.json", {
        "schema": "jrv2_fold_contract@1",
        "cells": {
            "BTC_H1": {"regime_clock": "H1", "exec_clock": "15m", "warmup": WARMUP,
                        "evaluable_decisions": int(len(h1_eval)), "floor_per_fold": 1000,
                        "folds": folds_from(h1_eval)},
            "BTC_H4": {"regime_clock": "H4", "exec_clock": "15m", "warmup": WARMUP,
                        "evaluable_decisions": int(len(h4_eval)), "floor_per_fold": 300,
                        "folds": folds_from(h4_eval),
                        "law": "INDEPENDENT cell: own folds, own trial accounting; H1-vs-H4 selection by PnL is forbidden"},
            "SPY_D1": {"regime_clock": "D1", "exec_clock": "D1", "warmup": WARMUP,
                        "evaluable_decisions": int(len(spy_eval)), "floor_per_fold": 300,
                        "folds": folds_from(spy_eval, iso=False)},
        },
        "partition_law": "contiguous exec-bar fold partition with reconciliation identity and no-position-span invariants (V1 remediation-r1 law, built in from the start)",
    }))

    rng = np.random.default_rng(SEED)
    canary = {
        "schema": "jrv2_canary_contract@1",
        "seed": SEED,
        "synthetic_fixtures": [
            {"id": "C1_CLEAR_UPTREND",
             "state": {"short_return": 0.020, "medium_return": 0.110, "long_return": 0.280,
                        "fast_trend": "strong_up", "slow_trend": "weak_up", "trend_strength": "high",
                        "volatility_regime": "normal", "drawdown_state": "near_high",
                        "range_location": "near_high", "close_location": "strong", "volume_state": "normal",
                        "dist_to_ema": "above", "prior_structure": "TREND_UP", "prior_direction": "UP"},
             "expected": {"structure": "TREND", "direction": "UP", "phase": "UPTREND", "effective": "UPTREND"},
             "class": "clear"},
            {"id": "C2_CLEAR_DOWNTREND",
             "state": {"short_return": -0.025, "medium_return": -0.130, "long_return": -0.300,
                        "fast_trend": "strong_down", "slow_trend": "weak_down", "trend_strength": "high",
                        "volatility_regime": "high", "drawdown_state": "deep",
                        "range_location": "near_low", "close_location": "weak", "volume_state": "high",
                        "dist_to_ema": "below", "prior_structure": "TREND_DOWN", "prior_direction": "DOWN"},
             "expected": {"structure": "TREND", "direction": "DOWN", "phase": "DOWNTREND", "effective": "DOWNTREND"},
             "class": "clear"},
            {"id": "C3_RANGE_AFTER_DOWNTREND",
             "state": {"short_return": 0.004, "medium_return": -0.010, "long_return": -0.180,
                        "fast_trend": "flat", "slow_trend": "weak_down", "trend_strength": "low",
                        "volatility_regime": "low", "drawdown_state": "mild",
                        "range_location": "middle", "close_location": "neutral", "volume_state": "low",
                        "dist_to_ema": "at", "prior_structure": "RANGE", "prior_direction": "DOWN"},
             "expected": {"structure": "RANGE", "direction": "NEUTRAL", "phase": "ACCUMULATION", "effective": "ACCUMULATION"},
             "class": "clear"},
            {"id": "C4_RANGE_AFTER_UPTREND",
             "state": {"short_return": -0.004, "medium_return": 0.012, "long_return": 0.220,
                        "fast_trend": "flat", "slow_trend": "weak_up", "trend_strength": "low",
                        "volatility_regime": "normal", "drawdown_state": "near_high",
                        "range_location": "middle", "close_location": "neutral", "volume_state": "normal",
                        "dist_to_ema": "at", "prior_structure": "RANGE", "prior_direction": "UP"},
             "expected": {"structure": "RANGE", "direction": "NEUTRAL", "phase": "DISTRIBUTION", "effective": "DISTRIBUTION"},
             "class": "clear"},
            {"id": "C5_HIGH_VOL_CONFLICT",
             "state": {"short_return": 0.030, "medium_return": -0.080, "long_return": 0.050,
                        "fast_trend": "strong_up", "slow_trend": "weak_down", "trend_strength": "medium",
                        "volatility_regime": "extreme", "drawdown_state": "mild",
                        "range_location": "middle", "close_location": "strong", "volume_state": "high",
                        "dist_to_ema": "extended_above", "prior_structure": "RANGE", "prior_direction": "NEUTRAL"},
             "expected": {"effective": "TRANSITION_UNKNOWN"},
             "class": "ambiguous"},
            {"id": "C6_LOW_VOL_RANGE",
             "state": {"short_return": 0.001, "medium_return": 0.002, "long_return": -0.005,
                        "fast_trend": "flat", "slow_trend": "flat", "trend_strength": "low",
                        "volatility_regime": "low", "drawdown_state": "near_high",
                        "range_location": "middle", "close_location": "neutral", "volume_state": "low",
                        "dist_to_ema": "at", "prior_structure": "RANGE", "prior_direction": "NEUTRAL"},
             "expected": {"effective": "TRANSITION_UNKNOWN"},
             "class": "ambiguous"},
            {"id": "C7_NOISY_CONTRADICTORY",
             "state": {"short_return": -0.020, "medium_return": 0.030, "long_return": -0.070,
                        "fast_trend": "weak_down", "slow_trend": "weak_up", "trend_strength": "medium",
                        "volatility_regime": "high", "drawdown_state": "mild",
                        "range_location": "near_low", "close_location": "strong", "volume_state": "high",
                        "dist_to_ema": "extended_below", "prior_structure": "RANGE", "prior_direction": "NEUTRAL"},
             "expected": {"effective": "TRANSITION_UNKNOWN"},
             "class": "ambiguous"},
            {"id": "C8_MISSING_STALE", "state": None,
             "expected": {"effective": "TRANSITION_UNKNOWN", "not_sent": True}, "class": "ambiguous"},
        ],
        "perturbations": {
            "n_per_clear_fixture": PERTURB_N, "jitter": 0.10,
            "rule": "raw numerics jittered +-10% uniform (seeded); semantic bins recomputed from jittered numerics; expected effective label UNCHANGED",
            "stability_threshold": ">= 6/8 perturbed states keep the expected effective label per clear family",
        },
        "acceptance_preregistered": [
            "raw output NEVER contains a non-schema label (no UNKNOWN option exists)",
            "100% schema-valid on fixtures",
            "clear directional fixtures not inverted",
            "no single raw phase label > 70% across the balanced CLEAR fixtures",
            "perturbation stability >= 6/8 per clear family",
            "ambiguous fixtures ARE code-abstained (effective TRANSITION_UNKNOWN)",
            "clear fixtures NOT mass-abstained by code (>= 80% of clear fixtures keep an effective non-UNKNOWN label)",
            "zero credential leakage", "exact model pin", "cost/call/latency measured and recorded",
        ],
        "historical_preview": {
            "max_states": PREVIEW_N, "cell": "BTC_H1",
            "sampling_rule": f"i_k = floor(k*{len(h1_eval)}/{PREVIEW_N}), k=0..{PREVIEW_N - 1}; dedup; preregistered by timestamp, no return-based choice",
            "preview_indices": preview_idx,
            "prior_rule": "prior fields of sampled state k taken from the last SAMPLED predecessor (preview-only approximation; bulk uses strict sequential law)",
            "classification_only": True, "no_pnl": True,
            "collapse_criteria_fail_stop": ["any single effective label > 90%", "effective UNKNOWN > 80%"],
            "stop_law": "on collapse: STOP, no bulk, no prompt rescue beyond the preregistered revision budget",
        },
    }
    written.append(dump("canary_v2_contract.json", canary))

    written.append(dump("adapter_contract.json", {
        "schema": "jrv2_adapter_contract@1",
        "sdk": {"package": "@typesafe-ai/sdk", "pinned_version": "0.6.0"},
        "auth": {"env": "TYPESAFE_API_KEY", "law": "environment only; never printed/logged/committed; no browser"},
        "model_pin": {"procedure": "re-probe models.list at G0; expected jev-1.13.0 (V1 measured direct-addressable); re-freeze before any call; jev-latest FORBIDDEN",
                       "drift_law": "response model != pin -> SCHEMA_ERROR -> code UNKNOWN + incident"},
        "call_discipline": {"maxRetries": 0, "timeout_ms": 10000, "one_call_per_state": True,
                             "three_questions_per_call": True, "no_re_asks": True,
                             "usage_persisted_per_response": True},
        "cache": {"dir": "runtime/cache/ (v2 namespaced)", "append_only": True,
                   "key": "sha256(model||state_id||input_digest||prompt_digest)"},
        "v1_isolation": "no V1 runtime path is readable by v2 code (static + runtime test); salts disjoint",
    }))

    written.append(dump("model_pin.json", {
        "schema": "jrv2_model_pin@1", "status": "CANDIDATE_UNVERIFIED",
        "pinned_model": None, "expected": "jev-1.13.0",
        "note": "re-probed and frozen at G0 before any V2 call",
    }))

    written.append(dump("evaluation_contract.json", {
        "schema": "jrv2_evaluation_contract@1",
        "per_cell_per_arm_metrics": ["gross_pnl", "costs_split", "net_pnl", "total_return", "cagr", "sharpe",
                                      "sortino", "max_drawdown", "profit_factor", "expectancy", "trades", "win_rate",
                                      "turnover", "time_in_market", "regime_switches", "regime_occupancy",
                                      "avg_dwell", "unknown_share_effective", "fold_by_fold", "concentration",
                                      "skipped_trade_pnl", "margin_to_fail", "cost_sweep_1x_1p5x_2x",
                                      "buy_hold_reference (metric, not scored arm)"],
        "gates": {"fold_concentration_kill": "top-fold profit share > 0.50 kills positive claims",
                   "single_cell_dependency_kill": "JEV_INCREMENTAL_VALUE_SUPPORTED requires beating always-on arms, deterministic router, random matched AND non-inferiority of the confirmation arm across cells per preregistered rule",
                   "reproduction": "byte-level ALL_MATCH", "a7_terminal_clean": True},
        "terminal_vocabulary": ["JEV_INCREMENTAL_VALUE_SUPPORTED", "JEV_NO_INCREMENTAL_VALUE",
                                 "JEV_INCONSISTENT_ACROSS_FOLDS_OR_ASSETS", "BLOCKED_CREDENTIAL_OR_COST",
                                 "BLOCKED_DATA", "BLOCKED_CONTROL_STATE", "TECHABORT"],
        "reports": ["REGIME_CLASSIFICATION_REPORT.md", "REGIME_BACKTEST_REPORT.md"],
    }))

    manifest = {"schema": "jrv2_freeze_manifest@1", "built_at_utc": BUILD_TS,
                 "builder": "research/control/jev_regime_router_v2/tools/build_freezes_v2.py",
                 "files": {}}
    for name in written:
        manifest["files"][name] = hashlib.sha256((FREEZES / name).read_bytes()).hexdigest()
    dump("freeze_manifest.json", manifest)
    print(json.dumps({
        "written": written,
        "h1_evaluable": int(len(h1_eval)), "h4_evaluable": int(len(h4_eval)),
        "spy_evaluable": int(len(spy_eval)),
        "h4_census": {"complete": len(h4), "partial": grid["h4"]["partial"], "align": grid["h4"]["align_ok"], "gaps": grid["h4"]["interior_gaps"]},
        "preview_n": len(preview_idx),
    }, indent=1))


if __name__ == "__main__":
    main()
