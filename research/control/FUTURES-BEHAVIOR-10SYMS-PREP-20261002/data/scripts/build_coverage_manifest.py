#!/usr/bin/env python3
"""build_coverage_manifest.py — DATA-PIT-ACQUISITION-PREP

Builds data/COVERAGE_MANIFEST.json from data/coverage_measured.json (OBSERVED)
plus the NEEDS side derived from owner_framework/00_MASTER_FRAMEWORK.md §5-§10
(hypothesis classes). Pure local transformation; no network.

Every HAVE number below is OBSERVED (script + window recorded in
coverage_measured.json). Every NEED is tied to a hypothesis class (HC1-HC4),
which are classes of HYPOTHESES from the owner framework, not facts.
"""

import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
MEASURED = os.path.join(HERE, "..", "coverage_measured.json")
OUT = os.path.join(HERE, "..", "COVERAGE_MANIFEST.json")

SYMS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]
VENUE = {"NQ": "CME", "ES": "CME", "CL": "NYMEX", "NG": "NYMEX", "GC": "COMEX",
         "SI": "COMEX", "6E": "CME", "6J": "CME", "6B": "CME", "6A": "CME"}

HC = {
    "HC1_daily_signal_deep_history": {
        "description": "Daily per-contract signal research over multi-year history "
                       "(driver tables, regime splits, term structure, year-by-year stability).",
        "framework_refs": ["00_MASTER §6 (required tests: year-by-year, regime split, alternative roll)",
                           "00_MASTER §8 (store raw individual contracts, explicit roll tables)",
                           "per-symbol §9 backtest protocol: individual expiry contracts, walk-forward OOS"],
        "needs": {
            "daily_trades_per_contract": "real-volume daily OHLCV per individual expiry, >= 5y continuous, all listed expiries",
            "definitions_reference": "full listing/activation + expiry calendar per root (PIT, no lookahead)",
            "open_interest": "daily OI per contract (liquidity migration, PIT contract selection)",
            "settlement": "official settlement per contract-day (exchange-event truth, separable from trade close)",
        },
    },
    "HC2_intraday_execution": {
        "description": "Intraday execution realism: session statistics, entry-delay tests, spread/depth response, fill realism.",
        "framework_refs": ["00_MASTER §5.7 (entering 1-5 minutes later destroys the edge?)",
                           "per-symbol §10 data checklist (bbo-1m/bbo-1s selective; mbp-1 execution/microstructure validation)",
                           "per-symbol §17.3 (baseline 1-minute return/volatility/session statistics)"],
        "needs": {
            "minute_trades_m1": "continuous M1 per-contract multi-year (session stats, delayed-entry)",
            "bid_ask_intraday": "synchronous BBO at <=1m (executable spread, not asynchronous EOD quotes)",
            "statistics_settlement_oi": "official OHLC/volume/OI to reconcile bars vs exchange truth",
        },
    },
    "HC3_roll_critical_windows": {
        "description": "Roll windows and term structure: calendar vs volume vs OI roll, roll cost, back-adjustment sensitivity, vendor-stitch jump audit.",
        "framework_refs": ["00_MASTER §8 (roll tables: old/new, decision ts, reason, volume/OI, gap, adjustment)",
                           "per-symbol §6 (compare calendar roll vs volume roll vs OI roll; verify no vendor-stitch jump is alpha)"],
        "needs": {
            "daily_trades_per_contract": "ADJACENT contracts' simultaneous real-volume daily bars across full history (roll cost = adjacent close gap)",
            "open_interest": "daily OI of old + new contract at roll decision time (PIT roll rule)",
            "definitions_reference": "exact listing/expiration timestamps (roll decision uses only pre-known info)",
        },
    },
    "HC4_event_study_windows": {
        "description": "Event studies around scheduled releases (FOMC/CPI/NFP for NQ/ES/6*, EIA storage for NG/CL, CoT for positioning).",
        "framework_refs": ["00_MASTER §5 (returns at 1m/5m/15m/1h/1d; spread+volume response; event timestamp in exchange tz + UTC)",
                           "00_MASTER §7 (PIT: release timestamp, tz, vintage, earliest observable ts)"],
        "needs": {
            "minute_trades_m1": "M1 (or tick) around event timestamps, multi-year = many event repetitions",
            "bid_ask_intraday": "spread response around events",
            "external_pit": "release timestamps + as-known-then values (ALFRED vintages, CFTC CoT release times, EIA/BLS schedules) — NOT_SOLVED_BY_VENDOR, see DATA_ACQUISITION_SPEC.md",
        },
    },
}

GAP_TYPES = {
    "DEPTH_WALL_EXPIRED_RESOLUTION": "IBKR expired-contract secdef resolves only ~1y back (FUTURES-DATA-10SYMS-V1 finding 1): per-contract REAL-VOLUME daily chain is only ~14-17 months (measured front-chain run); older expiries unresolvable => cannot extend via IBKR retrospective fetch.",
    "INTRADAY_VINTAGE_WALL": "IBKR intraday (M1/H1) availability ~10 recent months for these entitlements (NG ~2.2y; FUTURES-DATA-10SYMS-V1 finding 4 / S7_DEPTH_ACTIVE.json probes at 2024/2022 ends returned n=0). On-disk corpus is a snapshot: 2 trading days of M1 and ~30 days of H1 per contract, not continuous history.",
    "SETTLEMENT_ONLY_DEEP_BARS": "65-88% of on-disk daily bars are close-only O=H=L=C with volume=0 (settlement-derived; measured per symbol below): usable as reference/signal price, NOT as fill price or volume evidence (FUTURES-DATA-10SYMS-V1 finding 3).",
    "CLASS_ABSENT_OPEN_INTEREST": "IBKR bar files carry no open-interest field: OI class NOT_AVAILABLE in current corpus.",
    "CLASS_ABSENT_STATISTICS": "No exchange statistics schema (official OHLCV/OI/settlement publications) in IBKR corpus; settlement only inferable from close-only bars.",
    "CLASS_PARTIAL_DEFINITIONS": "Definitions only as embedded file headers (expiry_month=lastTradeDate raw, timeZoneId) for the 10-28 fetched contracts + S1_IDENTITY.json for the ~1y resolvable window. No listing/activation dates, no full expiry universe, no PIT add/modify/delete history.",
    "BID_ASK_NONSYNCHRONOUS_1Y": "Daily BID and ASK are separate non-synchronous series (~1y): spread computed from them is NOT an executable spread (FUTURES-DATA-10SYMS-V1 S6).",
}


def build():
    meas = json.load(open(MEASURED))
    symbols = {}
    for sym in SYMS:
        s = meas["symbols"][sym]
        cl = s["classes"]
        t = cl.get("daily_trades_per_contract", {})
        rv = s["daily_real_volume"]
        bid = cl.get("daily_bid", {})
        ask = cl.get("daily_ask", {})
        h1 = cl.get("hourly_trades", {})
        m1 = cl.get("minute_trades", {})

        have = {
            "daily_trades_per_contract": {
                "status": "HAVE_PARTIAL",
                "contracts_fetched": t.get("contracts"),
                "contract_list": t.get("contract_list"),
                "bars_total": t.get("bars_total"),
                "bars_close_only_settlement_derived": t.get("bars_close_only"),
                "close_only_fraction": round((t.get("bars_close_only") or 0) / max(t.get("bars_total") or 1, 1), 4),
                "bar_date_span": t.get("bar_date_span"),
                "real_volume_any_contract_window": rv["continuous_recent_run_any_contract"],
                "front_chain_real_volume_run_months": rv["front_chain"]["continuous_recent_run_front"]["n_months"],
                "front_chain_real_volume_run": f"{rv['front_chain']['continuous_recent_run_front']['from']}..{rv['front_chain']['continuous_recent_run_front']['to']}",
            },
            "daily_bid_ask": {
                "status": "HAVE_PARTIAL",
                "bid": {"contracts": bid.get("contracts"), "bars": bid.get("bars_total"), "span": bid.get("bar_date_span")},
                "ask": {"contracts": ask.get("contracts"), "bars": ask.get("bars_total"), "span": ask.get("bar_date_span")},
                "caveat": "non-synchronous separate series; ~1y; not executable spread",
            },
            "minute_trades_m1": {
                "status": "HAVE_SNAPSHOT_ONLY",
                "contracts": m1.get("contracts"),
                "bars_total": m1.get("bars_total"),
                "per_contract_depth": "durationStr='2 D' (RTH) per contract snapshot",
                "span_union": m1.get("bar_date_span"),
            },
            "hourly_trades_h1": {
                "status": "HAVE_SNAPSHOT_ONLY",
                "contracts": h1.get("contracts"),
                "bars_total": h1.get("bars_total"),
                "per_contract_depth": "durationStr='30 D' per contract snapshot",
                "span_union": h1.get("bar_date_span"),
            },
            "definitions_reference": {
                "status": "HAVE_MINIMAL",
                "detail": "embedded headers (expiry_month=raw lastTradeDate, timeZoneId) + S1_IDENTITY.json (multiplier/minTick/tz) for fetched contracts only; no listing/activation, no PIT universe",
            },
            "statistics_settlement_oi": {
                "status": "NOT_AVAILABLE",
                "detail": "no statistics schema in IBKR corpus; settlement only via close-only bars (typed SETTLEMENT_ONLY_DEEP_BARS)",
            },
            "open_interest": {"status": "NOT_AVAILABLE", "detail": "no OI field in IBKR bars"},
            "settlement": {
                "status": "HAVE_DERIVED_ONLY",
                "detail": "separable as close-only v=0 bars (identified, not an official settlement field)",
            },
        }

        need = {
            "daily_trades_per_contract": "real-volume per-contract daily, >= 5y continuous, all listed expiries (incl. adjacent contracts simultaneously) [HC1,HC3]",
            "daily_bid_ask": "synchronous quotes or cross-check basis, deep [HC2]",
            "minute_trades_m1": "continuous multi-year M1 [HC2,HC4]",
            "hourly_trades_h1": "multi-year H1 (cheap coarse intraday) [HC2]",
            "definitions_reference": "full PIT definitions (listing/activation/expiry, add/modify/delete) [HC1,HC3]",
            "statistics_settlement_oi": "official statistics incl. OI (stat_type 9) + settlement (stat_type 3) [HC1,HC2,HC3]",
            "open_interest": "daily OI per contract [HC1,HC3]",
            "settlement": "official settlement series [HC1]",
            "external_pit": "see DATA_ACQUISITION_SPEC.md NOT_SOLVED_BY_VENDOR [HC4]",
        }

        gaps = ["DEPTH_WALL_EXPIRED_RESOLUTION", "INTRADAY_VINTAGE_WALL", "SETTLEMENT_ONLY_DEEP_BARS",
                "CLASS_ABSENT_OPEN_INTEREST", "CLASS_ABSENT_STATISTICS", "CLASS_PARTIAL_DEFINITIONS",
                "BID_ASK_NONSYNCHRONOUS_1Y"]

        symbols[sym] = {
            "venue_ibkr": s.get("exchange") or VENUE[sym],
            "databento_dataset": "GLBX.MDP3 (CME+CBOT+NYMEX+COMEX)",
            "have": have,
            "need": need,
            "gap_types": gaps,
        }

    manifest = {
        "schema": "futures_behavior_10syms_coverage_manifest@1",
        "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
        "lane": "DATA-PIT-ACQUISITION-PREP",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claims_basis": {
            "HAVE": "OBSERVED: data/scripts/measure_coverage.py over ~/.my-quantitative-data/futures-10syms-v1/raw/ (read-only; 1160 files, 0 parse errors; window = full corpus fetched 2026-10-02); per-file detail in data/coverage_measured.json",
            "NEED": "POSTULATED-from-framework: owner_framework/00_MASTER_FRAMEWORK.md + per-symbol files. Framework content = HYPOTHESES, never facts/PASS. Needs are tied to hypothesis classes HC1-HC4, not to accepted strategies.",
            "no_inference_rule": "anything unmeasured is NOT_RUN/NOT_AVAILABLE, never inferred PASS",
        },
        "hypothesis_classes": HC,
        "gap_types": GAP_TYPES,
        "symbols": symbols,
        "cross_symbol_observations": {
            "front_chain_real_volume_run_months": {sym: symbols[sym]["have"]["daily_trades_per_contract"]["front_chain_real_volume_run_months"] for sym in SYMS},
            "close_only_fraction": {sym: symbols[sym]["have"]["daily_trades_per_contract"]["close_only_fraction"] for sym in SYMS},
            "contracts_fetched": {sym: symbols[sym]["have"]["daily_trades_per_contract"]["contracts_fetched"] for sym in SYMS},
        },
    }
    with open(OUT, "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"wrote {os.path.abspath(OUT)}")


if __name__ == "__main__":
    build()
