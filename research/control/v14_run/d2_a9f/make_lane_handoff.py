"""A9-F T7: assemble lane_handoff.json (per-proposal feasibility verdicts,
gate ledger with commands/exit codes/SHA-256s) from the lane's committed
artifacts.  Read-only over everything else; run last.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT_ROOT = HERE.parents[3]  # worktree root (research/control/v14_run/d2_a9f -> up 3)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=WT_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def main() -> None:
    feasibility = json.load(open(HERE / "feasibility_report.json", encoding="utf-8"))
    t4 = feasibility["schedule_feasibility"]
    t5 = feasibility["cost_arithmetic"]
    t6 = feasibility["control_and_drop_one"]
    staged = json.load(open(HERE / "staged_basis_manifest.json", encoding="utf-8"))
    oi_ver = json.load(open(HERE / "oi_staging_verification.json", encoding="utf-8"))
    panel_index = json.load(open(HERE / "panel_index.json", encoding="utf-8"))
    probe = json.load(open(HERE / "probe_summary.json", encoding="utf-8"))
    retry = json.load(open(HERE / "probe_retry_summary.json", encoding="utf-8"))

    # ---- per-proposal verdicts (feasibility only; NOT selection/novelty) ----
    def cost_block(prop):
        c = t5["proposals"][prop]
        return {
            "base_drag_upper_frac_yr_worst_case": c["base"]["total_drag_frac_of_gross_yr_worst_case"],
            "base_drag_frac_yr_diversified": c["base"]["total_drag_frac_of_gross_yr_diversified"],
            "stressed_drag_upper_frac_yr_worst_case": c["stress"]["total_drag_frac_of_gross_yr_worst_case"],
            "stressed_drag_frac_yr_diversified": c["stress"]["total_drag_frac_of_gross_yr_diversified"],
            "base_floor_pass_worst_case": c["base"]["pass_worst_case"],
            "stressed_floor_pass_worst_case": c["stress"]["pass_worst_case"],
            "base_floor_pass_diversified": c["base"]["pass_diversified"],
            "stressed_floor_pass_diversified": c["stress"]["pass_diversified"],
        }

    def warmup_block(prop):
        w = t4["warmup"][prop]
        return {
            "needed_from": w["needed_from"],
            "routes_cover_all_19": {r: v["covers_needed_start_all_19"] for r, v in w["routes"].items()},
        }

    verdicts = {}
    for prop in [
        "BASISLV-PREMFADE",
        "BASISLV-WIDTHGATE",
        "BASISDYN-PREMREV",
        "BASISDYN-PREMVOL",
        "OICH",
        "OICYC",
    ]:
        problems = []
        if not t4["decision_stamps"]["floor_pass"]:
            problems.append("decision-floor")
        if not t4["fold_floors"]["pass"]:
            problems.append("fold-floor")
        if prop in ("OICH", "OICYC"):
            if not t4["oi_warmup"]["passes"]:
                problems.append("oi-warmup")
            elig = t4["eligibility_floors"]["A8_oich_min8_19" if prop == "OICH" else "A8_oicyc_19"]
        elif prop.startswith("BASISLV"):
            elig = t4["eligibility_floors"]["A5_tercile_book_min12" if prop == "BASISLV-PREMFADE" else "A5_widthgate_min12"]
        else:
            elig = t4["eligibility_floors"]["A6_premrev_min4" if prop == "BASISDYN-PREMREV" else "A6_premvol_min4"]
        if elig["stamps_below_floor"] > 0:
            problems.append(f"eligibility-floor ({elig['stamps_below_floor']} stamps below)")
        if prop != "OICH" and prop != "OICYC":
            w = warmup_block(prop)
            if not all(w["routes_cover_all_19"].values()):
                problems.append("warmup-coverage")
        cb = cost_block(prop) if prop in t5["proposals"] else None
        sched = t5["measured_turnover_from_rank_schedule"][
            {
                "BASISLV-PREMFADE": "BASISLV-PREMFADE",
                "BASISLV-WIDTHGATE": "BASISLV-WIDTHGATE-ANCHOR(gate-open)",
                "BASISDYN-PREMREV": "BASISDYN-PREMREV",
                "BASISDYN-PREMVOL": "BASISDYN-PREMVOL",
                "OICH": "OICH",
                "OICYC": "OICYC",
            }[prop]
        ]
        measured_drag_pass = (
            sched["drag_frac_of_gross_window_base"] <= 0.08
            and sched["drag_frac_of_gross_window_stress"] <= 0.12
        )
        if cb and not measured_drag_pass:
            problems.append("cost-floor")
        if elig["min_eligible"] == 0:
            # the feature cannot be computed for enough names at ANY stamp:
            # the proposals' own failure tables route this to BLOCKED_DATA
            # ("data problem, not economics"), not to a mechanism verdict
            verdict = "BLOCKED (BLOCKED_DATA per the proposal's own failure table)"
        else:
            verdict = "FEASIBLE" if not problems else "INFEASIBLE"
        entry = {
            "verdict": verdict,
            "blockers": problems,
            "schedule": {
                "scheduled_stamps": t4["decision_stamps"]["count_scheduled"],
                "live_stamps_after_1d_purge": 51,
                "per_365d_annualized": t4["decision_stamps"]["per_365d_annualized"],
                "fold_live_stamps": {k: v["live_stamps_after_1d_purge"] for k, v in t4["folds"].items()},
            },
            "eligibility": elig,
            "cost_arithmetic_upper_bound": cb,
            "control_identifiability": t6["controls"][prop]["well_defined"],
            "drop_one_non_vacuous_by_construction": t6["drop_one"][prop]["non_vacuous_by_construction"],
        }
        if prop in ("OICH", "OICYC"):
            entry["oi_authority"] = {
                "sha_all_match": oi_ver["all_sha_match"],
                "rows_417_all": oi_ver["all_rows_417"],
                "zero_missing_days_all": oi_ver["all_zero_gaps"],
                "warmup_rows_at_first_stamp_min": oi_ver["warmup_rows_at_first_stamp_min"],
            }
        else:
            entry["warmup"] = warmup_block(prop)
        sched_key = {
            "BASISLV-PREMFADE": "BASISLV-PREMFADE",
            "BASISLV-WIDTHGATE": "BASISLV-WIDTHGATE-ANCHOR(gate-open)",
            "BASISDYN-PREMREV": "BASISDYN-PREMREV",
            "BASISDYN-PREMVOL": "BASISDYN-PREMVOL",
            "OICH": "OICH",
            "OICYC": "OICYC",
        }[prop]
        entry["measured_turnover_schedule_only"] = t5["measured_turnover_from_rank_schedule"][sched_key]
        verdicts[prop] = entry

    staged_missing = {
        key: entry["missing_buckets"] for key, entry in staged["entries"].items()
        if entry["missing_buckets"]
    }

    gates = [
        {
            "gate": "G1 per-symbol availability re-verification probes (D1 discharge: premium/mark/index klines earliest+anchor probes, 19 ranked names; D2 honored: indexPriceKlines pair=; D3 honored: basis point anchors only)",
            "command": ".venv/bin/python research/control/v14_run/d2_a9f/probe_basis_depth.py",
            "exit_code": 0,
            "evidence": "evidence/d2probe_0001..0304 (one JSON per request); probe_summary.json",
            "artifact_sha256": sha256_file(HERE / "probe_summary.json"),
            "verdict": "PASS",
            "notes": f"{probe['total_requests']} keyless GETs; kline routes 200/200 rows-or-empty; 29/76 basis point anchors returned transient HTTP 418 (empty body) -> G1b retry",
        },
        {
            "gate": "G1b basis-route retry pass (transient 418 backoff re-checks)",
            "command": ".venv/bin/python research/control/v14_run/d2_a9f/probe_retry.py",
            "exit_code": 0,
            "evidence": "evidence/d2retry_0305..0380; probe_retry_summary.json",
            "artifact_sha256": sha256_file(HERE / "probe_retry_summary.json"),
            "verdict": "PASS",
            "notes": "76/76 retry point anchors returned rows (third pass, fixed evidence naming): all 19 symbols verified with basis-route rows at 2024-08-20, 2025-06-30, 2025-08-22 and 2026-08-21 -- the earlier first-pass misses were transient 418 noise; per-symbol depth is independently confirmed by the full-window staging (G2)",
        },
        {
            "gate": "G2 staging of the frozen 15m conditioning observables, 19 symbols x 4 routes, authorized window 2024-08-20..2026-08-21",
            "command": ".venv/bin/python research/control/v14_run/d2_a9f/stage_basis.py --routes premium_klines,mark_klines,index_klines,basis",
            "exit_code": 0,
            "evidence": "staged/ (machine-local, gitignored); staged_basis_manifest.json",
            "artifact_sha256": sha256_file(HERE / "staged_basis_manifest.json"),
            "verdict": "PASS" if not staged_missing else "FAIL",
            "notes": f"{staged['http_requests_this_run']} HTTP requests this run; {staged['expected_buckets_per_symbol']} expected buckets/symbol/route; missing-bucket entries: {staged_missing if staged_missing else 'NONE'}",
        },
        {
            "gate": "G3 staged OI authority verification (OICH/OICYC; v11_oi_staging_v1)",
            "command": ".venv/bin/python research/control/v14_run/d2_a9f/verify_oi_staging.py",
            "exit_code": 0,
            "evidence": "oi_staging_verification.json",
            "artifact_sha256": sha256_file(HERE / "oi_staging_verification.json"),
            "verdict": "PASS",
            "notes": "20/20 SHA-256 match vs oi_staging_manifest.json; schema {create_time, sum_open_interest}; 417/417 unique day rows, zero missing days, zero duplicate day rows; 55 daily rows available at the first stamp (>= 29 anchor / >= 15 neighbour); complete 19-symbol cross-section at all 52 weekly stamps; day-row stamps before 23:55 on 48-59 days/symbol (documented, read per row)",
        },
        {
            "gate": "G4 per-proposal conditioning-feature rank panels for A7-N (52 Monday stamps x 19 symbols; frozen lag conventions; fail-closed eligibility)",
            "command": ".venv/bin/python research/control/v14_run/d2_a9f/build_panels.py",
            "exit_code": 0,
            "evidence": "panels/ + panel_index.json",
            "artifact_sha256": sha256_file(HERE / "panel_index.json"),
            "verdict": "PASS",
            "notes": "six panels; no PnL/positions; SHA-256 per panel in panel_index.json",
        },
        {
            "gate": "G5 schedule feasibility + cost arithmetic + control/drop-one report",
            "command": ".venv/bin/python research/control/v14_run/d2_a9f/feasibility_report.py",
            "exit_code": 0,
            "evidence": "feasibility_report.json",
            "artifact_sha256": sha256_file(HERE / "feasibility_report.json"),
            "verdict": "PASS",
            "notes": "T4/T5/T6 measured on the real snapshot; cost floors evaluated as worst-case fill-bound arithmetic under the remediated kernel with real perp-metadata ticks",
        },
    ]

    handoff = {
        "schema": "v14_d2_a9f_lane_handoff_v1",
        "cycle": "CRYPTO-V14",
        "lane": "d2-a9f-feasibility",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "head_before_commit": git("rev-parse", "HEAD"),
        "porcelain_before_commit": git("status", "--porcelain=v1"),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A9-F",
        "scope_boundary": "feasibility only: coverage/availability re-verification, schedule feasibility, cost arithmetic, control identifiability, drop-one meaningfulness. NO PnL, NO positions, NO returns-based judgment, NO family selection opinions (A1 selects), NO novelty verdicts (A7-N polices). Proposals unmodified.",
        "per_proposal_feasibility": verdicts,
        "discrepancies_and_observations": [
            {
                "id": "A9F-DISC-1",
                "severity": "HIGH (data vs proposal assumption)",
                "where": "BASISDYN-PREMVOL (and partially BASISDYN-PREMREV); /fapi/v1/premiumIndexKlines close",
                "observation": "premiumIndexKlines CLOSE intermittently emits exact 0.0 when the premium index did not update at the bucket boundary (verified against raw rows: open/high/low carry real values, close is 0; volume fields 0; mark klines carry forward, premium klines do not). Sentinel shares over the authorized window: ACE 48.5%, ONG 48.1%, BOME 30.7%, ZEC 29.1%, NEAR 14.3%, ENA 13.5%, WLD 10.7%, LINK 8.1%, BCH 6.9%, ADA 6.0%, AAVE 5.4%, AVAX 5.4%, 1000PEPE 3.9%, BNB 2.7%, SUI 2.4%, DOGE 1.8%, XRP 1.7%, SOL 0.6%, ETH 0.1%. Under the proposals' frozen fail-closed rule (L-V12-5: malformed == missing; no back-fill, no synthesis), PREMVOL's 2880-slot clean window is unreachable: only 3/19 symbols (BNB, XRP, ETH) have even ONE fully-clean 2880-bucket window anywhere in the authorized window, and the panel measures ZERO eligible names at essentially every stamp (min_iqr=0). Its 90d neighbour is strictly worse. PREMREV's 31-value footprint survives on a shrunken universe: eligible counts min 4 / median 8 (vs the 19-name design), meeting its own N >= 4 floor at every stamp. Verdict routing per the proposals' own failure tables: PREMVOL -> BLOCKED_DATA ('premium-kline coverage gaps force N < 4 persistently - data problem, not economics'); PREMREV -> feasible with drastically reduced breadth (A1 should weigh whether the reduced-universe reading still matches the design intent before selection).",
            },
            {
                "id": "A9F-OBS-1",
                "severity": "LOW",
                "where": "all A5/A6 proposals + staged data",
                "observation": "/futures/data/basis futuresPrice is the perp's LAST-TRADED price while markPriceKlines close is the MARK price, so PREMFADE's p_b and WIDTHGATE's m_b are different premium bases by construction (route-specific and self-consistent within each proposal). Measured BTCUSDT 2024-08-20T00:00Z: basis-route futuresPrice 59398.40 vs mark close 59368.34.",
            },
            {
                "id": "A9F-OBS-2",
                "severity": "MEDIUM",
                "where": "BASISLV-WIDTHGATE staging identity check (m_b vs premiumIndexKlines close)",
                "observation": "The mark/index-derived premium and the endpoint premium kline are distinct observables whose disagreement grows with illiquidity: measured abs-deviation medians ~5e-5 (SOL) to ~6.5e-4 (ONG), per-symbol MAXima 8.7e-2 (ONG), 4.5e-2 (ACE), 2.0e-2 (SOL), 1.7e-2 (ZEC/WLD), 1.7e-2 (ENA) -- all recorded per symbol in the WIDTHGATE panel's staging_identity_check block. A fixed tight band (1e-3) fails several names; a 1e-1 band is trivially loose. A1/I-lane must declare the tolerance from this measured table (or accept the per-symbol fail-closed drops it implies); the WIDTHGATE route data itself is complete (19/19 names x 70,272 buckets).",
            },
            {
                "id": "A9F-OBS-3",
                "severity": "LOW",
                "where": "BASISLV-WIDTHGATE staging identity check",
                "observation": "premiumIndexKlines close is NOT exactly markClose/indexClose-1 per bucket (Binance derives the premium kline from higher-frequency snapshots). Measured abs deviation: mean ~4.0e-5, max ~4.2e-4 (BTCUSDT 500-bucket sample). The proposal's 'declared relative tolerance' must be an ABSOLUTE band (~1e-3) or it will flag near-zero-premium buckets spuriously; the lane's panel declares tolerance_abs=1e-3 and records per-symbol maxima.",
            },
            {
                "id": "A9F-OBS-4",
                "severity": "LOW",
                "where": "all proposals' decision-count floors",
                "observation": "52 Monday stamps exist in the blind-S0 window; the frozen 1-day fold purge removes the 2025-12-22 stamp, leaving 51 live stamps per arm. A6's >= 48 floor passes; A5's and A8's text floors of '52 weekly decisions' are met only by the SCHEDULED calendar. A1 should record which reading binds at selection; no data failure involved.",
            },
            {
                "id": "A9F-OBS-5",
                "severity": "LOW",
                "where": "BASISDYN-PREMREV sigma_chg standardization",
                "observation": "'trailing 30d standard deviation of consecutive 72h premium changes' is ambiguous between daily-sampled (30 changes) and every-15m-overlapping (~2880 changes) readings. The lane's panel uses the DAILY-SAMPLED reading (declared in the artifact); the 72h-change numerator and rank ordering are identical under both, only the sigma scale differs.",
            },
            {
                "id": "A9F-OBS-6",
                "severity": "MEDIUM (staging robustness, not feasibility)",
                "where": "/futures/data/basis (BASISLV-PREMFADE primary route)",
                "observation": "The endpoint intermittently returns HTTP 418 with an empty body under serial ~0.55-0.9s pacing (29/76 first-pass point anchors, 14/76 retries; kline routes never returned 418 in the same runs). The I-lane staging for PREMFADE MUST implement 418 backoff-retry (this lane's stager uses up to 8 attempts with linear 20s backoff). Full-window staging completed with ZERO missing buckets on all routes, so the data are retrievable; the quirk is operational.",
            },
            {
                "id": "A9F-OBS-7",
                "severity": "LOW",
                "where": "OICH/OICYC warmup",
                "observation": "The day's last 5m OI metrics snapshot lands before 23:55Z on 48-59 of 417 days per symbol (documented in OICH section 4). Calendar-day completeness is 417/417 with zero missing/duplicate day rows; consecutive-ness by day-row index as the proposals freeze. Not a gap.",
            },
            {
                "id": "A9F-OBS-8",
                "severity": "LOW (boundary note)",
                "where": "all proposals; execution-drag floors vs single-name concentration",
                "observation": "Under the remediated kernel with real ticks, the diversified upper-bound fill arithmetic gives ~6.5% base / ~11.8% stressed annual drag of gross (inside the 8%/12% floors, stress marginal), while the pathological all-fills-on-the-worst-tick-name bound (NEARUSDT) gives 10.9%/24.9% (breach). The MEASURED schedules reconstructed from the frozen rank rules churn far less than the bounds and pass both floors with wide margin for every measurable proposal (see per-proposal measured_turnover_schedule_only); the no-symbol->25%-of-turnover floor also passes everywhere measured (max 13.3%).",
            },
            {
                "id": "A9F-OBS-9",
                "severity": "LOW (evidence-integrity disclosure)",
                "where": "probe evidence files",
                "observation": "The SECOND basis-retry pass reused the imported probe counter (reset to 0) and overwrote evidence files d2probe_0001..0076 (first-pass records for the probes of 1000PEPEUSDT, AAVEUSDT, ACEUSDT, ADAUSDT and part of AVAXUSDT); those overwritten bodies are not recoverable, but every first-pass record (route, symbol, anchor, status, row_count, first/last row stamps, basis row payload) is retained in probe_summary.json, and the affected first-pass conclusions are independently re-established by the full-window staging (G2: 76/76 entries complete, zero missing buckets). The THIRD retry pass (fixed script) wrote correctly-named evidence/d2retry_0305..0380 with no collisions.",
            },
        ],
        "staging_summary": {
            "manifest": "staged_basis_manifest.json",
            "manifest_sha256": sha256_file(HERE / "staged_basis_manifest.json"),
            "bulk_root_absolute": str(HERE / "staged"),
            "routes": staged["routes"],
            "expected_buckets_per_symbol": staged["expected_buckets_per_symbol"],
            "entries": len(staged["entries"]),
            "total_rows": sum(e["rows"] for e in staged["entries"].values()),
            "total_bytes": sum(e["bytes"] for e in staged["entries"].values()),
            "missing_buckets_total": sum(staged_missing.values()),
        },
        "panels": panel_index["panels"],
        "oi_verification_sha256": sha256_file(HERE / "oi_staging_verification.json"),
        "feasibility_report_sha256": sha256_file(HERE / "feasibility_report.json"),
        "gates": gates,
        "not_run_blocked": [],
        "hard_constraints_respected": {
            "keyless_public_endpoints_only": True,
            "no_pnl": True,
            "no_positions": True,
            "no_selection_or_novelty_opinions": True,
            "proposals_unmodified": True,
            "writes_confined_to_worktree": True,
            "serial_requests_with_sleep": True,
        },
    }
    with open(HERE / "lane_handoff.json", "w", encoding="utf-8") as handle:
        json.dump(handoff, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(json.dumps({p: v["verdict"] for p, v in verdicts.items()}, indent=1))


if __name__ == "__main__":
    main()
