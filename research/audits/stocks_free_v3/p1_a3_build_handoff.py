"""Build the A3 P1 authority handoff artifact (STOCKS-FREE-V3).

Re-runnable by A7: run from the A3 worktree root with the lane interpreter::

    /Users/hoangminhlong/my-quantitative/.venv/bin/python \
        research/audits/stocks_free_v3/p1_a3_build_handoff.py

Reads ONLY the V2 staged snapshot (byte hashes + S0-truncated payloads
through the sealed reader) and the read-only V2 control artifacts.  Performs
no network I/O, reads no credentials, writes exactly one JSON file next to
this script.  Every check that cannot run is recorded as NOT_RUN or
UNAVAILABLE — never an inferred PASS.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from research.assets.stocks.calendar import USEquityRegularCalendar  # noqa: E402
from research.stocks_free_v3 import authority as A  # noqa: E402
from research.stocks_free_v3.benchmarks import (  # noqa: E402
    BENCHMARK_EW_SECTOR_TOTAL_RETURN,
    BENCHMARK_FLAT_HARD,
    BENCHMARK_RISK_MATCHED_SPY,
    BENCHMARK_SPY_TOTAL_RETURN,
    DEFAULT_VOL_SCALING_RULE,
)
from research.stocks_free_v3.cohort import verify_real_cohort  # noqa: E402
from research.stocks_free_v3.data_policy import ALLOWED_DATA_FIELDS  # noqa: E402
from research.stocks_free_v3.incremental import (  # noqa: E402
    CONTRACT_SCHEMA,
    FALSIFICATION_NOTE,
)
from research.stocks_free_v3.isolation import (  # noqa: E402
    S0WindowPolicy,
    S1Seal,
    SealedSnapshotReader,
)

HANDOFF_PATH = Path(__file__).resolve().parent / "p1_a3_authority_handoff.json"

NOT_RUN: list[dict[str, str]] = []


def not_run(item: str, reason: str) -> dict[str, str]:
    entry = {"item": item, "status": "NOT_RUN", "reason": reason}
    NOT_RUN.append(entry)
    return entry


def main() -> int:
    produced_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    #: Lane provenance: the recorded wave base SHA this branch started from.
    WAVE_BASE_SHA = "a29bc070b72fc72d324fd529224a19152b41711b"

    not_run(
        "live_vendor_entitlement_and_account_standing",
        "revalidation is by READING the frozen V2 control artifacts only; "
        "credential access, account queries and any network fetch are "
        "forbidden in this lane, so current vendor account standing cannot "
        "be confirmed and is NOT claimed",
    )
    not_run(
        "s1_era_total_return_series",
        "S1 (2025-08-01..2026-07-31) is SEALED: TR reconstruction and all "
        "value-level checks are verified over S0 only; the sole post-S0 "
        "values read are the two pinned split-provenance closes per split "
        "symbol (corporate-action provenance, A7-approved in V2)",
    )

    # 1. snapshot pin revalidation -------------------------------------------- #
    staging = Path(A.SNAPSHOT_STAGING_PATH)
    if not staging.is_dir():
        pins_payload: dict[str, object] = {
            "verdict": "NOT_RUN",
            "detail": f"UNAVAILABLE: staging root absent: {staging}",
        }
        cohort_payload: dict[str, object] = pins_payload
    else:
        pins = A.verify_snapshot_pins(staging)
        pins_payload = pins.to_payload()

        # 2. license/terms evidence (read-only control artifacts) -------------- #
        control = Path(A.V2_CONTROL_PATH)
        license_report = A.revalidate_license_evidence(control, staging_root=staging)
        if not (control / "da1_authority.json").is_file():
            not_run(
                "license_terms_revalidation",
                f"UNAVAILABLE: V2 control artifacts absent at {control}",
            )
        license_payload = license_report.to_payload()

        # 3. cohort verification (S0-bounded, split provenance closes only) ---- #
        seal = S1Seal(A.S1_START, A.S1_END)
        reader = SealedSnapshotReader(
            staging, seal=seal, policy=S0WindowPolicy()
        )
        distributions_path = staging / "distributions.json"
        splits_path = staging / "split_factors.json"
        if distributions_path.is_file() and splits_path.is_file():
            distributions = json.loads(distributions_path.read_text(encoding="utf-8"))
            split_factors = json.loads(splits_path.read_text(encoding="utf-8"))
            cohort = verify_real_cohort(
                reader, distributions, split_factors, USEquityRegularCalendar()
            )
            cohort_payload = cohort.to_payload()
        else:
            cohort_payload = {
                "verdict": "NOT_RUN",
                "detail": (
                    "UNAVAILABLE: distributions.json / split_factors.json absent "
                    f"in staging ({staging})"
                ),
            }
            not_run(
                "cohort_verification",
                "UNAVAILABLE: staging corporate-action evidence files absent",
            )

    calendar = USEquityRegularCalendar()
    calendar_digest = calendar.calendar_manifest_digest

    # supplementary digests of unpinned staging evidence files ----------------- #
    supplementary: dict[str, str] = {}
    for name in (
        "distributions.json",
        "split_factors.json",
        "spdr-etf-historical-distributions.xlsx",
        "navhist-us-en-spy.xlsx",
    ):
        path = staging / name
        supplementary[name] = A.sha256_file(path) if path.is_file() else "UNAVAILABLE"

    seal_digest = S1Seal(A.S1_START, A.S1_END).definition_digest()

    # read-only V2 control artifact digests for the audit trail --------------- #
    control_dir = Path(A.V2_CONTROL_PATH)
    control_digests: dict[str, str] = {}
    for name in (
        "w1_freeze.json",
        "snapshot_manifest.json",
        "split_factors.json",
        "cohort_census.json",
        "partition.json",
        "da1_authority.json",
    ):
        path = control_dir / name
        control_digests[name] = A.sha256_file(path) if path.is_file() else "UNAVAILABLE"

    handoff = {
        "schema": "stocks_free_v3/p1_a3_authority_handoff@1",
        "produced_at_utc": produced_at,
        "producer_role": "A3",
        "cycle": "STOCKS_FREE_V3",
        "branch": "orca/stocks-free-v3-p1-a3-data",
        "worktree": str(REPO_ROOT),
        "wave_base_sha": WAVE_BASE_SHA,
        "interpreter": sys.executable,
        "snapshot_revalidation": pins_payload,
        "license_evidence": license_payload if staging.is_dir() else {"verdict": "NOT_RUN"},
        "cohort_verification": cohort_payload,
        "calendar": {
            "calendar_id": calendar.calendar_id,
            "table_version": calendar.table_version,
            "manifest_digest": calendar_digest(),
            "frozen_pin": A.CALENDAR_DIGEST,
            "verdict": (
                "PASS" if calendar_digest() == A.CALENDAR_DIGEST else "FAIL"
            ),
        },
        "s1_seal": {
            "s0_window": [A.S0_START.isoformat(), A.S0_END.isoformat()],
            "s1_window": [A.S1_START.isoformat(), A.S1_END.isoformat()],
            "warmup_window": [A.WARMUP_START.isoformat(), A.WARMUP_END.isoformat()],
            "s1_status": "SEALED_UNTOUCHED",
            "seal_definition_digest": seal_digest,
            "discipline_note": (
                "no S1 return exposed: per-symbol payloads are value-checked only "
                "at or before S0 end; the only post-S0 values read are the two "
                "pinned split-provenance closes (2025-12-04/05) per split symbol, "
                "re-deriving the A7-approved V2 corporate-action ratios"
            ),
        },
        "benchmark_contract": {
            "status": "FROZEN_SEMANTICS_ONLY_NOT_SCORED",
            "benchmarks": [
                {
                    "benchmark_id": BENCHMARK_FLAT_HARD,
                    "semantics": "return 0.0 every session; level 1.0",
                },
                {
                    "benchmark_id": BENCHMARK_SPY_TOTAL_RETURN,
                    "semantics": (
                        "issuer TR of SPY: r(d) = (sadj(d) + dist(d)) / "
                        "sadj(prev(d)) - 1; sadj multiplies raw close by the "
                        "cumulative split factor from each effective date onward "
                        "(2:1 split factor = 2.0)"
                    ),
                },
                {
                    "benchmark_id": BENCHMARK_EW_SECTOR_TOTAL_RETURN,
                    "semantics": (
                        "equal weight (daily rebalanced) across the ten sector "
                        "ETFs (cohort minus SPY): r_ew(d) = mean_i r_i(d)"
                    ),
                    "members": list(A.SECTOR_SYMBOLS),
                },
                {
                    "benchmark_id": BENCHMARK_RISK_MATCHED_SPY,
                    "semantics": (
                        "SPY TR scaled ex ante: s(d) = clip(target_daily_vol / "
                        "realized_vol, min_gross, max_gross); realized_vol is the "
                        "ddof=0 std of the last lookback realized SPY TR returns "
                        "STRICTLY BEFORE d (no look-ahead); insufficient history "
                        "scales by min_gross; zero realized vol scales by max_gross"
                    ),
                    "default_rule": DEFAULT_VOL_SCALING_RULE.to_payload(),
                    "default_rule_digest": DEFAULT_VOL_SCALING_RULE.digest,
                },
            ],
        },
        "incremental_alpha_definition": {
            "contract_schema": CONTRACT_SCHEMA,
            "definition": (
                "per fold: incremental_alpha = R_strategy_after_cost - "
                "R_benchmark, with R_benchmark the RISK_MATCHED_SPY_CONTEXT "
                "total return over the same fold window built with the arm's "
                "frozen ex-ante gross/vol rule"
            ),
            "beta_isolation": "RISK_MATCHED_EX_ANTE",
            "pass_eligibility": (
                "only strictly positive incremental alpha against the "
                "risk-matched benchmark is pass-eligible; diagnostics against "
                "flat/SPY/EW benchmarks are never pass-eligible"
            ),
            "falsification_note": FALSIFICATION_NOTE,
        },
        "unavailable_data_policy": {
            "allowed_fields": sorted(ALLOWED_DATA_FIELDS),
            "enforcement": (
                "config-validation-time rejection (research.stocks_free_v3."
                "data_policy.validate_family_data_requirements); earnings, "
                "borrow, quote-spread, fundamentals and any other field outside "
                "the whitelist are rejected before any data is touched"
            ),
        },
        "supplementary_staging_digests": supplementary,
        "control_artifact_digests": control_digests,
        "not_run_or_unavailable": NOT_RUN,
        "network_fetches": 0,
        "credentials_accessed": False,
        "raw_data_committed": False,
    }

    HANDOFF_PATH.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {HANDOFF_PATH}")
    print(f"pins: {pins_payload.get('verdict')}")
    print(f"license: {license_payload.get('verdict') if staging.is_dir() else 'NOT_RUN'}")
    print(f"cohort: {cohort_payload.get('verdict')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
