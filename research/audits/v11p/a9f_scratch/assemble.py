"""Assemble the D2-A9-F feasibility audit artifact from raw scratch outputs."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/v11/d2-a9-feasibility")
SCRATCH = ROOT / "research/audits/v11p/a9f_scratch"
BOOTSTRAP_SHA = "903ed49529de5ee56ece7dc9fe896da32804a4f8"

cov = json.load(open(SCRATCH / "coverage_raw.json"))
sch = json.load(open(SCRATCH / "schedules_raw.json"))
comp = json.load(open(SCRATCH / "compute_raw.json"))

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


CASE_BY_LABEL = {c["label"]: c for c in sch["cases"]}

# ---------------------------------------------------------------- verdicts
FAMILY_FIELDS = {
    "V11-SEED-DEFENSIVE-RESIDUAL-RISK": {
        "required": ["15m completed bars (close)", "BTC bars", "funding settlements (cost line)", "instrument defs / tick size"],
        "data_verdict": "PASS",
    },
    "V11-SEED-LOTTERY-MAX-SKEW": {
        "required": ["15m completed bars (close)", "BTC bars", "funding settlements (cost line)", "instrument defs / tick size"],
        "data_verdict": "PASS",
    },
    "V11-A5-ILLIQ-PREMIUM": {
        "required": ["15m completed bars (close, volume, quote_volume)", "BTC bars", "funding settlements", "mark price context", "instrument defs / tick size"],
        "data_verdict": "PASS",
    },
    "V11-A5-OI-HEDGEPRESSURE": {
        "required": ["15m completed bars", "OI snapshot series >=1/day per universe symbol", "mark price", "funding settlements", "instrument defs / tick size"],
        "data_verdict": "UNAVAILABLE",
    },
    "V11-A6-ILLIQUIDITY-PREMIUM": {
        "required": ["15m completed bars (close, quote volume)", "BTC bars", "funding settlements", "instrument defs / tick size"],
        "data_verdict": "PASS",
    },
    "V11-A6-POSITIONING-SATURATION": {
        "required": ["15m completed bars", "OI snapshot series (>=60d coverage at declared cadence per symbol)", "funding settlements", "instrument defs / tick size"],
        "data_verdict": "UNAVAILABLE",
    },
    "A8-V11-ILLIQ-AMIHUD": {
        "required": ["15m completed bars (close, quote volume) per USD-M symbol", "BTC bars", "funding settlements"],
        "data_verdict": "PASS",
    },
    "A8-V11-OILEVER-DELEV": {
        "required": ["15m completed bars", "per-symbol OI snapshots", "funding settlements (cost only)", "BTC bars"],
        "data_verdict": "UNAVAILABLE",
    },
}

SCHEDULE_CASE = {
    "V11-SEED-DEFENSIVE-RESIDUAL-RISK": ["seed_defensive_residual_risk"],
    "V11-SEED-LOTTERY-MAX-SKEW": ["seed_lottery_max_skew"],
    "V11-A5-ILLIQ-PREMIUM": ["a5_prop1_V11-A5-ILLIQ-PREMIUM"],
    "V11-A5-OI-HEDGEPRESSURE": ["a5_prop2_V11-A5-OI-HEDGEPRESSURE", "a5_prop2_scheduleonly"],
    "V11-A6-ILLIQUIDITY-PREMIUM": ["a6_prop1_V11-A6-ILLIQUIDITY-PREMIUM", "a6_prop1_breadth_relaxed_min1"],
    "V11-A6-POSITIONING-SATURATION": ["a6_prop2_V11-A6-POSITIONING-SATURATION", "a6_prop2_scheduleonly", "a6_prop2_breadth_relaxed_min1"],
    "A8-V11-ILLIQ-AMIHUD": ["a8_prop1_A8-V11-ILLIQ-AMIHUD"],
    "A8-V11-OILEVER-DELEV": ["a8_prop2_A8-V11-OILEVER-DELEV", "a8_prop2_scheduleonly"],
}

FINAL = {
    "V11-SEED-DEFENSIVE-RESIDUAL-RISK": (
        "PASS",
        "Data fields all present PIT-correct; frozen A3 schedule gate PASS on all five floors. "
        "Breadth caveat HIGH (9 eligible symbols -> 1 name/leg in a quintile proxy) but the seed "
        "declares no min-names-per-leg rule; concentration is a D3/Stage-A concern, not a floor fail.",
    ),
    "V11-SEED-LOTTERY-MAX-SKEW": (
        "PASS",
        "Data fields all present PIT-correct (7d residual MAX and 30d residual skew computable from "
        "daily residual dailies); frozen A3 schedule gate PASS on all five floors. Same HIGH breadth caveat.",
    ),
    "V11-A5-ILLIQ-PREMIUM": (
        "PASS",
        "All required bar/volume/funding/tick fields present; gate PASS (base 2.48%/yr, stressed "
        "4.18%/yr, medhold 21d, max symbol share 16.7%, 52 decisions/365d).",
    ),
    "V11-A5-OI-HEDGEPRESSURE": (
        "UNAVAILABLE",
        "Fail-closed: no OI snapshot series exists in the staged snapshot (0 files, 0 rows, no cadence "
        "to quantify). Its own predeclared gate (>=1 OI snapshot/day per universe symbol) cannot be "
        "evaluated. Schedule-only counterfactual passes all cost floors, so data is the only blocker.",
    ),
    "V11-A6-ILLIQUIDITY-PREMIUM": (
        "FAIL",
        "Data PASS but its own fail-closed risk rule (minimum 6 names per leg) is unsatisfiable at "
        "every decision: PIT eligible universe is 9 symbols, tercile legs max 3. Schedule floors pass "
        "only under a breadth-relaxed counterfactual (min 1/leg) which is NOT a waiver.",
    ),
    "V11-A6-POSITIONING-SATURATION": (
        "UNAVAILABLE",
        "Double-blocked: (1) no OI snapshot series exists (fail-closed, cannot evaluate its own "
        "declared OI coverage diagnostic); (2) min-6-names-per-leg rule unsatisfiable on a 9-symbol "
        "eligible universe.",
    ),
    "A8-V11-ILLIQ-AMIHUD": (
        "PASS",
        "Required fields present (15m bars + quote volume only; OI/mark not used); gate PASS (identical "
        "weekly schedule to A5-PROP1: base 2.48%/yr, stressed 4.18%/yr, medhold 21d, share 16.7%).",
    ),
    "A8-V11-OILEVER-DELEV": (
        "UNAVAILABLE",
        "Fail-closed on its own P9 OI data-quality gate: there is no OI snapshot series to evaluate "
        "non-negativity / gap / jump checks. Schedule-only counterfactual passes all cost floors.",
    ),
}

GROUPS = {
    "ILLIQUIDITY_PREMIUM": {
        "members": ["V11-A5-ILLIQ-PREMIUM", "V11-A6-ILLIQUIDITY-PREMIUM", "A8-V11-ILLIQ-AMIHUD"],
        "verdict": "PASS (2 of 3 proposals; a6 monthly variant FAIL on breadth)",
    },
    "OI_POSITIONING": {
        "members": ["V11-A5-OI-HEDGEPRESSURE", "V11-A6-POSITIONING-SATURATION", "A8-V11-OILEVER-DELEV"],
        "verdict": "UNAVAILABLE (all three proposals fail closed on absent OI snapshot data)",
    },
    "SEEDS": {
        "members": ["V11-SEED-DEFENSIVE-RESIDUAL-RISK", "V11-SEED-LOTTERY-MAX-SKEW"],
        "verdict": "PASS (both; HIGH breadth caveat)",
    },
}

CANONICAL = {
    "ILLIQUIDITY_PREMIUM": {
        "recommendation": "A8-V11-ILLIQ-AMIHUD (a8_prop1)",
        "criteria_applied": "Data readiness equal (bars-only). Schedule simplicity equal in cadence "
        "(52 weekly Monday 00:00Z decisions); a8_prop1 is the simpler spec: single Amihud estimator "
        "for anchor+neighbour (28d/56d), plain quintile book, no winsorisation step and no Roll "
        "estimator dependency (a5_prop1). a5_prop1 is equally feasible and remains fully eligible; "
        "PLAN D3 lexicographic tie-break applies if A1 needs it.",
        "runner_up": "V11-A5-ILLIQ-PREMIUM (a5_prop1) - equal data readiness, equal floor margins, "
        "adds Roll-spread estimator-consistency neighbour and reversal-orthogonality diagnostic.",
    },
    "OI_POSITIONING": {
        "recommendation": "NONE - group is data-blocked; no canonical variant selectable",
        "criteria_applied": "Data readiness first: zero OI coverage for every symbol, so no variant "
        "can be evaluated. If the owner later stages PIT OI snapshots, the weekly lane (a8_prop2 "
        "OILEV-FLOW-28D-W, or a5_prop2 OI-HP-28D-W) already demonstrates floor-passing schedule "
        "counterfactuals; a8_prop2 carries the most predeclared OI data-quality gates and would be "
        "the natural conditional candidate. a6 monthly variants remain breadth-blocked regardless.",
    },
}

# ---------------------------------------------------------------- assemble
per_symbol_bars = {}
for s, b in cov["bars"].items():
    per_symbol_bars[s] = {
        "rows": b["rows"],
        "first_bar_close_utc": datetime.fromtimestamp(b["first_ts_ns"] / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_bar_close_utc": datetime.fromtimestamp(b["last_ts_ns"] / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "missing_bars_internal": b["missing_bars_internal"],
        "gap_events": b["gap_count"],
        "gaps_over_1h": [
            {"from_utc": datetime.fromtimestamp(g["from"] / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "to_utc": datetime.fromtimestamp(g["to"] / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "missing_bars": g["missing_bars"]}
            for g in b["gaps_over_1h"]
        ],
        "zero_volume_bars": b["zero_volume_bars"],
        "zero_dollar_volume_days": b["zero_dollar_volume_days"],
        "rows_through_2026_08_21T00Z": b["rows_through_2026_08_21"],
        "stale_bars_at_window_end": b["stale_bars_at_cut"],
    }

per_symbol_funding = {}
for s, f in cov["funding"]["scan_2026"].items():
    per_symbol_funding[s] = {
        "rows": f["rows"],
        "first_utc": datetime.fromtimestamp(f["first_funding_ms"] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "last_utc": datetime.fromtimestamp(f["last_funding_ms"] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "median_interval_h": f["median_interval_h"],
        "max_gap_h": f["max_gap_h"],
        "gaps_over_12h": f["gaps_over_12h"],
        "mark_price_present_rows": f["mark_price_present_rows"],
    }
per_symbol_funding_2024dir = {
    s: {"rows": f["rows"], "median_interval_h": f["median_interval_h"], "max_gap_h": f["max_gap_h"]}
    for s, f in cov["funding"]["20240820_20260821"].items()
}

schedule_cases = {}
for c in sch["cases"]:
    schedule_cases[c["label"]] = {
        "cadence": c["cadence"],
        "buckets": c["buckets"],
        "history_days": c["history_days"],
        "gate_verdict": c["verdict"],
        "discretionary_decisions": c["n_discretionary"],
        "decisions_per_365d": c["decisions_per_365d"],
        "median_intended_holding_days": c["median_holding_d"],
        "annualised_base_cost_drag_frac_of_gross": c["base_drag"],
        "annualised_stressed_cost_drag_frac_of_gross": c["stressed_drag"],
        "max_symbol_turnover_share": c["max_sym_share"],
        "max_symbol_turnover_share_symbol": c.get("max_sym_share_symbol"),
        "floors": c["floors"],
        "unavailable_metrics": c["unavailable_metrics"],
        "metric_reasons": c.get("metric_reasons", {}),
        "eligibility_above_median_min_median_max": [
            c["eligibility_min_above_median"], c["eligibility_median_above_median"], c["eligibility_max_above_median"]
        ],
        "schedule_sha256": c["schedule_sha256"],
        "note": c.get("note", "primary schedule-proxy run"),
    }

verdict_matrix = {}
for fam, (verdict, reason) in FINAL.items():
    labels = SCHEDULE_CASE[fam]
    primary = CASE_BY_LABEL[labels[0]]
    verdict_matrix[fam] = {
        "family_id": fam,
        "verdict": verdict,
        "reason": reason,
        "field_existence_verdict": FAMILY_FIELDS[fam]["data_verdict"],
        "required_observables": FAMILY_FIELDS[fam]["required"],
        "schedule_gate_verdict_primary": primary["verdict"],
        "schedule_gate_labels": labels,
        "min_eligible_symbols_per_decision": primary["eligibility_min_above_median"],
    }

audit = {
    "schema": "v11_a9f_feasibility_audit_v1",
    "producer_role": "D2-A9-F",
    "generated_utc": now,
    "bootstrap_sha": BOOTSTRAP_SHA,
    "branch": "orca/v11d-a9-feasibility",
    "worktree": str(ROOT),
    "head_sha_at_audit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
    "mandate": "PLAN.md section 9 A9-F: data, turnover and implementation feasibility audit. "
    "Schedule-only: NO scored return/PnL was computed, exposed or persisted; budget remains 0/12; "
    "denominators 119 published / 120 observed untouched.",
    "data_provenance": {
        "staged_snapshot_path": "/Users/hoangminhlong/my-quantitative/catalog_live_crypto",
        "staged_snapshot_read_only": True,
        "read_only_assertion": "Auditor wrote NOTHING under catalog_live_crypto or funding_data; all "
        "writes confined to research/audits/v11p/a9f_scratch and research/audits/v11p artifacts. "
        "No downloads performed; downloading is forbidden by mandate.",
        "funding_data_paths": [
            "/Users/hoangminhlong/my-quantitative/funding_data/scan_2026 (20/20 symbols, used)",
            "/Users/hoangminhlong/my-quantitative/funding_data/20240820_20260821 (7 symbols, earlier partial capture, audited not used for gates)",
        ],
        "python": "/Users/hoangminhlong/my-quantitative/.venv/bin/python",
        "candidate_frozen_window": {
            "scored_window_candidate": "2025-08-22T00:00:00Z .. 2026-08-21T00:00:00Z (365d; end anchored to the task's 'data through 2026-08-21'; no run_contract window declared yet)",
            "prewindow": "2024-08-21/23 .. 2025-08-21 (snapshot start .. scored-window start; >=90d warmup available for every symbol)",
        },
        "snapshot_fingerprint": {
            "catalog_files": len(cov["catalog_files"]),
            "bar_symbols": len(cov["bars"]),
            "instrument_def_symbols": len(cov["instrument_defs"]),
            "funding_symbols_scan_2026": len(cov["funding"]["scan_2026"]),
        },
    },
    "field_existence": {
        "timestamp_semantics": "Bar ts_event is the exchange CLOSE stamp of each completed 15m bar "
        "(research/panel.py convention); last bar before every candidate decision covers the boundary "
        "with staleness 0 at the 2026-08-21T00:00Z window end for all 20 symbols. Funding rows are "
        "settlement events (fundingTime ms, rate, markPrice). Instrument defs are a SINGLE static "
        "snapshot (ts 2026-08-23), not a PIT series - PIT caveat: tick size / fees are end-of-window "
        "values; V10 contract floor taker 5bps equals the staged taker_fee so no floor depends on "
        "fee drift. Mark price exists ONLY at funding settlement stamps, not as a continuous series; "
        "no proposal requires a continuous mark series for scheduling (a5_prop2 lists mark price as "
        "context - not present as a series, flagged LOW because HP features use OI and bars only).",
        "bars_per_symbol": per_symbol_bars,
        "instrument_defs_per_symbol": cov["instrument_defs"],
        "funding_per_symbol_scan_2026": per_symbol_funding,
        "funding_per_symbol_20240820_20260821": per_symbol_funding_2024dir,
        "summary": {
            "bars": "20/20 symbols: 70045-70079 rows each, 2024-08-21..23 -> 2026-08-23; zero volume "
            "gaps except ETHUSDT (63 missing bars across 3 events: 57-bar gap 2025-08-20T23:59->"
            "2025-08-21T14:29 UTC, 4-bar gap 2026-08-21T14:15, 2 single-bar); daily-close construction "
            "survives all events (fail-closed panel rule untriggered through 2026-08-21T00:00Z); "
            "zero zero-volume bars and zero zero-dollar-volume days.",
            "instrument_defs": "20/20 symbols present, price_increment (tick size), min_notional, "
            "taker_fee 0.0005 all present; onboardDate <= 2023-12 for every symbol so all 20 are "
            "listed >= 240d before the scored-window start (no mid-window listings).",
            "funding": "scan_2026: 20/20 symbols, 2190-4636 settlements, 2024-08-23T08:00Z -> "
            "2026-08-23T00:00/04:00Z, median cadence 8h (4h for ACE/BOME/ENA/ONG), max gap 8h, zero "
            "gaps >12h, markPrice present in 100% of rows.",
            "oi_snapshots": "0/20 symbols - NO open-interest series exists anywhere in the staged "
            "catalog (full parquet schema census below).",
            "mark_price_series": "ABSENT as a continuous series; present only inside funding settlements.",
        },
        "oi_schema_census": {
            "ohlcv_bar_parquets": 23,
            "instrument_def_static_parquets": 20,
            "open_interest_parquets": 0,
            "note": "20 bar dirs + 3 additional bar parquet parts; crypto_perpetual holds static "
            "CryptoPerpetual instrument definitions only (one row per symbol).",
        },
    },
    "oi_coverage_decisive_answer": {
        "question": "OI snapshot coverage per symbol (count, cadence, gaps)",
        "answer": "COVERAGE IS ZERO. For every one of the 20 staged symbols the open-interest "
        "snapshot count is 0 and cadence/gap statistics are UNDEFINED. The staged snapshot contains "
        "only 15m OHLCV bars and static instrument definitions; no OI parquet, table or field exists "
        "(census over all 43 catalog files). Per the fail-closed rule, missing = UNAVAILABLE for the "
        "OI_POSITIONING family - never an inferred PASS. All three OI-lane proposals (a5_prop2, "
        "a6_prop2, a8_prop2) are therefore UNAVAILABLE on data readiness, by their own predeclared "
        "gates (>=1 snapshot/day per symbol; a8_prop2 P9 plausibility gate; a6_prop2 >=60d OI coverage).",
        "coverage_per_symbol": {s: {"oi_snapshot_count": 0, "cadence": "UNDEFINED", "gaps": "UNDEFINED"}
                                for s in sorted(cov["bars"].keys())},
    },
    "schedule_feasibility": {
        "method": "Schedules constructed from each spec (weekly Monday 00:00Z for A5/A8 lanes and "
        "seeds; 28d cycle at 00:05Z for A6 lane) over the candidate scored window, plus a terminal "
        "FORCED_FLAT at 2026-08-21T00:05Z. Target books are REPRESENTATIVE SCHEDULE PROXIES: bucket "
        "membership from a deterministic, price-independent pseudo-characteristic (slow sinusoids), "
        "gross 1.0 dollar-neutral, weights 0.5/q (= the 1/(2*N_bucket) cap). NO scored return, PnL, "
        "factor or ranking exists anywhere in this audit. Fill prices are REAL staged 15m closes "
        "(first completed bar strictly after each decision) used as cost inputs only. Cost model "
        "declared at the frozen floors: taker_fee_bps=5.0 (= staged taker fee and V10 contract floor), "
        "adverse_tick_slip_floor=1, per-symbol tick sizes from staged instrument defs; stressed cell "
        "= frozen fee x1.5 / +2 ticks. All arithmetic reused verbatim from research.v11."
        "cost_feasibility.evaluate_schedule_cost_feasibility and research.adapter_v10 - nothing forked.",
        "cases": schedule_cases,
        "weekly_lane_result": "a5_prop1 / a8_prop1 / both seeds: gate PASS on all five floors "
        "(52 discretionary decisions, 52.58/365d <= 60; median intended holding 21d >= 3; base drag "
        "2.48%/yr <= 8%; stressed 4.18%/yr <= 12%; max symbol turnover share 16.7% <= 25%).",
        "oi_weekly_counterfactuals": "With availability supplied (data-absence neutralised) the "
        "schedule+cost floors alone PASS for a5_prop2 (base 1.49%, stressed 2.53%) and a8_prop2 "
        "(base 2.48%, stressed 4.18%): the ONLY blocker for the OI weekly lane is the absent OI data.",
        "monthly_lane_result": "a6 lane: 14 cycle starts fall in the 365d window under the frozen "
        "per-365d normalisation (13.0 under an exclusive-end convention; both << 60). Books EMPTY at "
        "every decision because the A6 fail-closed min-6-names-per-leg rule cannot be met (eligible "
        "universe 9), so gate = UNAVAILABLE_FAIL_CLOSED. Breadth-relaxed counterfactual (min 1/leg, "
        "NOT a waiver) shows the floors themselves pass: base 1.22%, stressed 2.05%, medhold 29d.",
        "proxy_caveat": "Holding/turnover metrics depend on proxy membership persistence (slow "
        "pseudo-characteristic). The observed medhold 21-29d and share 11.7-16.7% are therefore "
        "schedule-structure evidence, not scored outcomes; even the proposals' own full-swap "
        "worst-case (~6.2%/yr) sits inside both drag floors, so the PASS is robust to persistence "
        "assumptions for the drag floors.",
    },
    "min_eligible_symbols_per_decision": {
        "rule": "PIT eligibility = exchange-listed (instrument onboardDate, all 20 listed long "
        "before window) AND required history (60d A5/A8-weekly, 90d A6/seeds from bar firsts) AND "
        "active (a bar within 48h before decision) AND trailing-28d median daily dollar volume "
        "strictly above the cross-sectional PIT median of active symbols (declared tradability floor).",
        "result": "active = 20/20 at every decision date; above-median = 9 at every decision "
        "(min 9 / median 9 / max 9 across 52 weekly and 14 monthly dates). The DV-median floor "
        "structurally caps the universe near half the active names.",
        "breadth_assessment": "VIABLE BREADTH THRESHOLD STATED: quintile books (A5/A8/seeds) run "
        "with 1 name per leg (floor(9/5)); tercile books run with 3 per leg. A6's declared fail-closed "
        "minimum of 6 names per leg requires >= 18 eligible symbols - UNSATISFIABLE on this snapshot "
        "(9 eligible < 18) and likely unsatisfiable on any ~20-symbol universe. Flag: weekly quintile "
        "families operate at extreme breadth (2 scored names per side); single-symbol concentration "
        "gates at Stage-A are the binding risk, HIGH severity, but not a pre-score floor failure.",
        "pit_listing_caveat": "Staged bar firsts (2024-08-21..23 for all symbols) are snapshot-"
        "coverage starts, NOT exchange listing dates; PIT listing was therefore taken from the "
        "instrument-info onboardDate field (all <= 2023-12-31).",
    },
    "compute_estimates": {
        "host": {**comp["host"], "ram_gib": round(comp["host"]["ram_bytes"] / 2**30, 1)},
        "representative_workloads_prewindow": {
            "window": comp["features"]["prewindow"],
            "bar_load_all_20_symbols_15m_wall_s": comp["features"]["bar_load_wall_s"],
            "amihud_28d_across_symbols_wall_s": comp["features"]["f1_amihud_28d_wall_s"],
            "amihud_28d_status": comp["features"]["f1_status"],
            "residual_90d_beta_plus_28d_vol_7d_max_30d_skew_wall_s": comp["features"]["f2_residual_moments_wall_s"],
            "residual_moments_status": comp["features"]["f2_status"],
            "oi_growth_wall_s": comp["features"]["f3_oi_growth_wall_s"],
            "oi_growth_status": comp["features"]["f3_status"],
            "oi_growth_reason": comp["features"]["f3_reason"],
            "peak_rss_mb": comp["features"]["peak_rss_mb"],
        },
        "verdict": "No stronger machine needed for D2/P1 feature generation at this 20-symbol "
        "universe: total representative wall-clock ~2.2s and peak RSS ~137MB of 8GiB. Full 2-year "
        "history is < 2.5x this workload. (Owner directive already moves Phase E scored execution "
        "to a stronger owner machine - unrelated to this estimate.)",
    },
    "new_external_data_needs": [
        {
            "need": "Per-symbol OI snapshot history for all 20 staged USD-M perps",
            "needed_by": ["V11-A5-OI-HEDGEPRESSURE", "V11-A6-POSITIONING-SATURATION", "A8-V11-OILEVER-DELEV"],
            "spec": "PIT snapshots at published timestamps, >=1/day per symbol, >=90d history before "
            "each formation (28d/56d/90d features + a6 >=60d rule), through 2026-08-21",
            "status": "FLAGGED ONLY - not fetched (forbidden by mandate). Requires owner decision "
            "and a new staged snapshot revision before Phase I for any OI_POSITIONING family.",
        }
    ],
    "verdict_matrix": verdict_matrix,
    "mechanism_groups": GROUPS,
    "canonical_recommendation": CANONICAL,
    "blockers": [
        "OI_POSITIONING group (a5_prop2, a6_prop2, a8_prop2): UNAVAILABLE - zero OI snapshot "
        "coverage in the staged snapshot; new data staging requires owner scope.",
        "V11-A6-ILLIQUIDITY-PREMIUM: FAIL - its own min-6-names-per-leg fail-closed rule is "
        "unsatisfiable (9 eligible symbols) at every decision date.",
        "Breadth HIGH flag (not a floor fail): weekly quintile families trade 1 name per leg on this "
        "universe; Stage-A concentration gates are the binding downstream risk.",
        "LOW flag: instrument defs are a single end-of-window static snapshot (no PIT tick/fee "
        "series); acceptable because the declared cost floors equal the staged values.",
    ],
    "assumptions": [
        "Candidate frozen scored window assumed 2025-08-22..2026-08-21 (365d, end anchored to the "
        "task statement; no window declared yet in research/control/v11_run/run_contract.json).",
        "Weekly decision instant Monday 00:00Z (A5/A8/seeds); monthly = 28d cycle at 00:05Z (A6 "
        "declared convention). Terminal force-flat appended at 2026-08-21T00:05Z per V10 schedule "
        "convention; excluded from the discretionary decision count by the frozen gate.",
        "Books are schedule proxies from a deterministic price-independent pseudo-characteristic; "
        "they quantify schedule structure only and are NOT scored results.",
        "Trailing-28d median daily dollar volume implemented from 15m quote_volume sums per UTC day; "
        "cross-sectional median over active listed symbols (strictly-above rule, hence 9 of 20).",
        "Funding cadence for the gate taken from funding_data/scan_2026 (full 20-symbol coverage); "
        "the 20240820_20260821 directory (7 symbols) is an earlier partial capture.",
        "ETHUSDT 57-bar gap (2025-08-20/21) does not break daily-close PIT construction; any "
        "intraday-resampling feature would need a declared gap rule at implementation.",
    ],
    "outcome_blind_attestation": {
        "no_scored_return_pnl_computed": True,
        "budget_consumed": 0,
        "budget_max": 12,
        "gate_arithmetic_reused": "research/v11/cost_feasibility.py + research/adapter_v10/base.py (not forked)",
    },
    "raw_scratch_outputs": [
        "research/audits/v11p/a9f_scratch/coverage_raw.json",
        "research/audits/v11p/a9f_scratch/schedules_raw.json",
        "research/audits/v11p/a9f_scratch/compute_raw.json",
        "research/audits/v11p/a9f_scratch/run_coverage.py",
        "research/audits/v11p/a9f_scratch/run_schedules.py",
        "research/audits/v11p/a9f_scratch/run_compute.py",
    ],
}

out = ROOT / "research/audits/v11p/a9f_feasibility_audit.json"
json.dump(audit, open(out, "w"), indent=1, default=str, sort_keys=False)
print("wrote", out)
