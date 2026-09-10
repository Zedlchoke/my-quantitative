#!/usr/bin/env python
"""FOREX-FREE-V5 execution driver (I1 lane): wires the SELECTED V5 family
module (FXFV5-A6-P1) into the inherited, FROZEN V3 kernel and drives the
three-arm SANITIZED dummy dry-run (scored=false; never publishes PnL).

Architecture (mirrors research/assets/forex_free_v4/exec_driver_v4.py; the
V3 kernel files are imported READ-ONLY and are never modified):

    register_family("FXFV5-A6-P1",
                    research.assets.forex_free_v5.family_a6p1)

then every arm runs through the kernel's own
``scored_runner.compute_cell`` -> ``validate_decisions`` -> session gate ->
``accounting.book_dual`` / ``book_stress`` -> ``dry_run_sanitized`` path, so
booking, validation, fold/purge semantics, stress tiers (tier 2.0 primary)
and sanitization are the FROZEN kernel's, byte for byte.

Modes
-----
dummy   The three-arm SANITIZED DRY-RUN (handbook 17.2 discipline, V4
        shape).  Runs ``data_paths`` end-to-end with ``freeze_token=None``
        => ``scored=false``, ``real_pnl=false``, ``published=false`` and
        every booked monetary metric a 0.0/None placeholder (kernel
        ``dry_run_sanitized``).  Records go ONLY into a TEMPORARY ledger
        under ``research/control/forex_free_v5_run/dryrun_tmp/`` (tests
        clean it up; never the canonical ledger, never the scored budget)
        through the kernel's once-only ``AtomicJsonlPublisher``.  Reveals
        no outcome: the driver additionally runs a RECURSIVE PnL-leak scan
        over every written record (full nested structure) and fails closed
        on any leak.  Replay support: re-running the dummy mode appends
        nothing (once-only publication) and produces byte-identical
        records (determinism; the tests pin this).
scored  IMPLEMENTED but REFUSES to run unless ALL FIVE launch gates of the
        V5 run contract hold (see ``evaluate_launch_gates``):
          1. FOREX_FREE_V5_W4 freeze recorded with matching code hashes
             (including this driver's own file hash),
          2. independent S0 artifact ``FOREX_FREE_V5_S0_LAUNCH_AUTHORIZED``
             with zero unresolved HIGH/CRITICAL,
          3. owner FRESH exact-phrase GO artifact (postdating the S0
             authorization),
          4. budget: fewer than 3 scored cells consumed (this family's
             frozen budget: exactly three arms),
          5. S1 seal intact (``SEALED_UNTOUCHED``; the sealed artifact is
             never listed, opened, hashed or copied -- only the recorded
             status flag is read).
        The scored path is NOT exercised by the I1 lane (no scored run, no
        dry-run execution against real data beyond unit fixtures).

P-2 scaffolding: every sanitized record carries ``dryrun_gate_scaffold``
-- every frozen gate reported as {gate, threshold, comparator, observed,
margin} with the SIGNED margin to its fail boundary.  In dummy mode
``observed``/``margin`` are computed on the kernel's zeroed placeholders
and are explicitly not evidence; the scored path would fill them from the
booked book.

Structural visibility: each sanitized record carries ``dryrun_structure``
(counts only -- clock counters, schedule counters, skipped-reason counts,
force-flat decision counts, zero-position publication refusal) and
``dryrun_gate_check`` (kernel Stage-A gates re-evaluated ON the zeroed
placeholder metrics, labelled not-evidence).

Trial identity: ``trial_id`` = FOREX-FREE-V5/FXFV5-A6-P1/<arm> and
``arm_config_digest`` = sha256 over the arm's frozen config (proposal sha
+ module file sha + frozen meta config); pairwise distinctness asserted
programmatically; cash (USD) is never an instrument (kernel rule).

Determinism: no wall clock enters any record; replaying the dry-run
produces byte-identical records and zero denominator delta (the once-only
publisher returns (0, 0) for every already-published digest).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3 import scored_runner as R

CYCLE_ID = "FOREX-FREE-V5"
FAMILY_ID = "FXFV5-A6-P1"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
V5_CTL = os.path.join("research", "control", "forex_free_v5_run")
DRYRUN_TMP_DIRNAME = "dryrun_tmp"

REPORT_SCHEMA = "forex_free_v5_dummy_dryrun_report_v1"

W4_FREEZE_TOKEN = "FOREX_FREE_V5_W4"
S0_VERDICT = "FOREX_FREE_V5_S0_LAUNCH_AUTHORIZED"
OWNER_GO_PHRASE = "GO FOREX V5 SCORED EXECUTION"
PLANNED_SCORED_CELLS = 3            # exactly three arms (selection_freeze)

FAMILY_MODULES = {
    FAMILY_ID: {
        "module": "research.assets.forex_free_v5.family_a6p1",
        "proposal": os.path.join(V5_CTL, "i1_inputs",
                                 "PROPOSAL_FXFV5-A6-P1.json"),
        # sha256 of the packet materialized from git object
        # c82403d8c6f39a9d31c276db4d8510b70313c6cd (verified at registration)
        "proposal_sha256":
            "810f8650414ca578c08510fdb150f84d131f89c5fdbd3ace3f0d09a9a344a8f9",
    },
}

# Files whose sha256 a recorded FOREX_FREE_V5_W4 freeze must pin (matching
# hashes) before the scored path may run.
W4_CODE_HASH_FILES = (
    "research/assets/forex_free_v5/exec_driver_v5.py",
    "research/assets/forex_free_v5/family_a6p1.py",
    "research/assets/forex_free_v3/scored_runner.py",
    "research/assets/forex_free_v3/accounting.py",
)

# Launch-gate artifact paths (relative to ROOT).
GATE_W4_FREEZE = os.path.join(V5_CTL, "w4_freeze.json")
GATE_S0 = os.path.join(V5_CTL, "s0_launch_authorized.json")
GATE_FRESH_GO = os.path.join(V5_CTL, "owner_fresh_go.json")
GATE_STATE = os.path.join(V5_CTL, "state.json")
GATE_RUN_CONTRACT = os.path.join(V5_CTL, "run_contract.json")
SCORED_LEDGER_DEFAULT = os.path.join(V5_CTL, "scored_ledger_published.jsonl")

STAGED_MANIFEST = os.path.join("research", "control", "forex_free_v1_run",
                               "staged_data_manifest.json")
PRICE_SNAPSHOT_DIR = os.path.join("data_raw", "forex_free_v1")
CLOCK_AUTHORITY = os.path.join(V5_CTL, "p3_conditioning_clocks_v5.json")
ANNOUNCEMENT_LEDGER = os.path.join(V5_CTL,
                                   "announcement_ledger_v5_extension.jsonl")
LEDGER_MANIFEST = os.path.join(V5_CTL, "ledger_manifest_v5_extension.json")

# Frozen P-3 conditioning clocks + extension-ledger pins (verified
# fail-closed in verify_staged_data).
CLOCK_AUTHORITY_TOTAL = 246
EXTENSION_LEDGER_SHA256 = \
    "cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d20fd902"
EXTENSION_LEDGER_ROWS = 250

# --- PnL-leak scan rules (recursive; handbook 17.2 discipline) ------------
# Inherited V4 allowlist plus the V5 structural keys (counts, frozen
# constants and clock counters only -- never prices, never PnL).
FIELD_ALLOWLIST = frozenset({
    # kernel record columns (accounting.build_scored_record)
    "schema", "record_id", "cost_tier", "n_trades",
    "gross_price_pnl_usd", "price_only_pnl_usd",
    "financing_adjustment_usd", "financing_adjusted_pnl_usd",
    "dry_run", "real_pnl", "published",
    # kernel cell metadata (scored_runner.compute_cell extra)
    "cell_id", "family_id", "arm", "proposal_id", "decision_clock",
    "financing_formula", "scored", "n_decisions", "n_trades_kept",
    "weekend_gate_dropped", "purged_trades", "folds_declared", "purge_days",
    "base", "base_price_only", "folds", "mdd_usd", "fold_positive_share",
    "pair_concentration", "drop_one_expectancy", "dropout_scenarios",
    "break_even_cost_bps", "usd_drift_diag", "usd_index_source",
    "usd_index_pairs", "stress", "delay_stress", "incremental_alpha",
    "incremental_alpha_definition", "benchmark_treatment",
    # book_metrics keys (zeroed placeholders in a sanitized record)
    "trades", "total_pnl", "expectancy", "pf", "gross_positive",
    # fold metrics
    "fold", "populated",
    # stress metrics
    "cost_component_delta_vs_base_usd", "stress_rows_distinct_certified",
    # dropout scenarios
    "scenario", "survived",
    # usd_drift_diag
    "corr", "n_days", "evaluated",
    # delay_stress
    "carried_unblended", "n_delayed_trades",
    # driver-attached trial identity (cycle/family/arm + config digest)
    "trial_id", "arm_config_digest",
    # driver-attached structural block (counts only; no prices, no PnL)
    "dryrun_structure", "cycle_id_in_record", "structure_family",
    "structure_arm", "n_decisions_returned", "n_financing_events",
    "n_force_flat_decisions", "schedule_counters", "skipped_reason_counts",
    "ledger_events", "eligibility_counts", "no_refresh_ignored",
    "schedule_totals", "zero_positions", "would_refuse_publication",
    "refusal_code",
    # per-pair schedule counters (all ints)
    "candidates", "missing_next_fill_bar", "fill_lag_exceeds_4_days",
    "fold_boundary_no_entry", "end_of_data_no_exit",
    "earliest_scheduled_exit_data_end", "round_trips", "decision_bars",
    # ledger-basis + eligibility counters (all ints)
    "raw_rows", "deduped_rate_change_rows", "events_used",
    "zero_delta_rows", "n_unavailable_never_read", "no_eval_before_cutoff",
    "no_decision_bar_available",
    # driver-attached placeholder gate check (labelled not-evidence)
    "dryrun_gate_check", "evaluated_on", "gate_pass", "gate_reasons",
    # driver-attached P-2 margin-to-fail scaffold (thresholds are frozen
    # constants; observed/margin are computed on zeroed placeholders in
    # dummy mode and labelled not-evidence)
    "dryrun_gate_scaffold", "gates", "gate", "threshold", "comparator",
    "observed", "margin",
    # V5 family structural counters (all ints)
    "clock_counters", "published_clocks", "arm_candidates",
    "skipped_no_predecessor", "sham_dropped", "s0_cap_excluded",
    "warmup_void", "exact_zero_direction", "fold_window_voided",
    "missing_decision_bar", "missing_f", "missing_x",
    "f_missing_void", "x_missing_void",
    "fill_lag_refused", "governor_blocked_open", "governor_blocked_same_day",
    "economy_clock_counts",
    # V5 family frozen-constant projection (strings/numbers, no outcomes)
    "frozen_constants", "trailing_return_sum_ny_days",
    "sham_shift_calendar_days", "staleness_mode", "s0_cap_entry_utc",
    "notional_usd_unit", "clocks_pair_map",
})
# Parents whose child keys may be authorized-universe pair names.
PAIR_KEY_PARENTS = frozenset({"drop_one_expectancy", "schedule_totals"})
PAIR_NAMES = frozenset({"EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD",
                        "USD/JPY", "USD/CHF", "USD/CAD"})
# The kernel's frozen cost-tier labels under "stress".
TIER_KEY_PARENTS = frozenset({"stress"})
TIER_KEYS = frozenset({"tier1.0", "tier1.5", "tier2.0"})
# Parents whose child keys may be frozen skip-reason identifiers (the values
# are occurrence counts).
REASON_KEY_PARENTS = frozenset({"skipped_reason_counts"})
# Parents whose child keys may be evidenced-economy identifiers (counts).
ECONOMY_KEY_PARENTS = frozenset({"economy_clock_counts"})
ECONOMY_KEYS = frozenset({"GB", "CA", "AU", "NZ"})
# Parents whose child keys are the frozen clocks->pair map (economy -> pair).
CLOCK_PAIR_PARENTS = frozenset({"clocks_pair_map"})
# Outcome-suspect keys whose value is a frozen identifier LABEL, not a
# number (the kernel sanitizer leaves these strings untouched).
OUTCOME_LABEL_KEYS = frozenset({"incremental_alpha_definition",
                                "staleness_mode", "s0_cap_entry_utc"})
# Any key matching this pattern must hold a ZERO/None/empty placeholder in a
# sanitized record (the kernel zeroes them; the scan proves it recursively).
OUTCOME_VALUE_RE = re.compile(
    r"(pnl|profit|expectancy|pf|mdd|break_even|alpha|concentration|"
    r"survived|gross|share|corr)")
ZERO_PLACES = (0, 0.0, None, False)
LEAK_SCAN_NOTE = (
    "recursive scan over every dict/list leaf of every sanitized record; "
    "key allowlist (FIELD_ALLOWLIST; pair names under drop_one_expectancy/"
    "schedule_totals; frozen skip-reason identifiers under "
    "skipped_reason_counts; frozen cost-tier labels under stress; evidenced-"
    "economy counts under economy_clock_counts; the frozen clocks->pair map "
    "under clocks_pair_map) + forced-placeholder rule for every key matching "
    "pnl|profit|expectancy|pf|mdd|break_even|alpha|concentration|survived|"
    "gross|share|corr (exceptions: incremental_alpha_definition, "
    "staleness_mode, s0_cap_entry_utc are frozen identifier labels) + flags "
    "scored=false real_pnl=false published=false dry_run=true")

LIMITATIONS = [
    "dummy dry-run only: every booked monetary metric is the kernel's 0.0/None "
    "placeholder; the records carry schedule/count evidence, never outcomes",
    "dry-run gates and the P-2 margin-to-fail scaffold in dryrun_gate_check/"
    "dryrun_gate_scaffold are evaluated ON zeroed placeholder metrics and are "
    "explicitly not evidence (thresholds are frozen constants)",
    "scored mode is implemented but not exercised; it refuses without all "
    "five launch gates (W4 freeze + S0 authorized + fresh owner GO + budget "
    "< 3 + S1 seal intact)",
    "dry-run records live in the temporary dryrun_tmp/ ledger; they never "
    "enter the canonical ledger or the scored denominator",
    "code freeze sha is a placeholder (PENDING_V5_W4_FREEZE) until the W4 "
    "freeze records the pinned code hashes",
]


def _utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def git_head(root=ROOT):
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:  # pragma: no cover - record-only
        return None


CODE_FREEZE_SHA_PLACEHOLDER = "PENDING_V5_W4_FREEZE"

# frozen per-arm config projection (feeds arm_config_digest; everything
# here is a frozen constant or a deterministic string -- never an outcome)
FAMILY_CONFIG_KEYS = (
    "trailing_return_sum_ny_days", "sham_shift_calendar_days",
    "staleness_mode", "s0_cap_entry_utc", "warmup_daily_bars",
    "notional_usd_unit", "clocks_pair_map", "economy_order",
    "financing_formula_id", "alpha_definition", "decision_clock",
)


# -------------------------------------------------------------------------- #
# data_paths + staged-data verification (fail closed)                        #
# -------------------------------------------------------------------------- #
def build_default_data_paths(root=ROOT):
    """The staged, hash-verified V5 data authority: the byte-verified
    inherited price snapshot, the P-3 conditioning clocks (the ONLY
    conditioning authority) and the pinned V5-extension announcement
    ledger (financing kernel input, accounting only)."""
    return {
        "price_h1_dir": os.path.join(root, PRICE_SNAPSHOT_DIR),
        "conditioning_clocks": os.path.join(root, CLOCK_AUTHORITY),
        "announcement_ledger": os.path.join(root, ANNOUNCEMENT_LEDGER),
    }


def verify_staged_data(root=ROOT):
    """Verify the staged data authority against its pinned manifests; fail
    closed on any mismatch.  Returns the evidence dict."""
    from research.assets.forex_free_v5 import family_a6p1 as F
    # 1) price snapshot: sha256 vs staged_data_manifest digests_exec2
    manifest_path = os.path.join(root, STAGED_MANIFEST)
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    digests = manifest["digests_exec2"]
    snap_ok, snap_bad = 0, []
    for rel, expected in sorted(digests.items()):
        path = os.path.join(root, rel)
        if not os.path.exists(path) or sha256_file(path) != expected:
            snap_bad.append(rel)
        else:
            snap_ok += 1
    if snap_bad:
        raise RuntimeError(f"STAGED_SNAPSHOT_MISMATCH: {snap_bad[:5]} "
                           f"({len(snap_bad)} bad of {len(digests)})")
    # 2) conditioning clocks: full fail-closed parse (row shape, sha hex,
    #    S0 window, per-economy + total counts vs header AND frozen counts)
    clocks_path = os.path.join(root, CLOCK_AUTHORITY)
    clocks = F.load_clocks(clocks_path)
    if len(clocks) != CLOCK_AUTHORITY_TOTAL:
        raise RuntimeError("CLOCK_AUTHORITY_COUNT_MISMATCH: "
                           f"{len(clocks)} != {CLOCK_AUTHORITY_TOTAL}")
    # 3) pinned V5-extension announcement ledger (financing input)
    ledger_manifest = json.load(open(os.path.join(root, LEDGER_MANIFEST),
                                     encoding="utf-8"))
    pinned = ledger_manifest["extended_ledger"]["sha256"]
    ledger_path = os.path.join(root, ANNOUNCEMENT_LEDGER)
    ledger_sha = sha256_file(ledger_path)
    if ledger_sha != pinned:
        raise RuntimeError("ANNOUNCEMENT_LEDGER_PIN_MISMATCH: "
                           f"{ledger_sha} != {pinned}")
    n_rows = sum(1 for line in open(ledger_path, encoding="utf-8")
                 if line.strip())
    if n_rows != EXTENSION_LEDGER_ROWS:
        raise RuntimeError("EXTENSION_LEDGER_ROW_COUNT_MISMATCH: "
                           f"{n_rows} != {EXTENSION_LEDGER_ROWS}")
    return {
        "price_snapshot": {
            "manifest": STAGED_MANIFEST,
            "manifest_sha256": sha256_file(manifest_path),
            "digests_exec2_entries": len(digests),
            "verified": snap_ok,
            "mismatches": 0,
        },
        "conditioning_clocks": {
            "path": CLOCK_AUTHORITY,
            "sha256": sha256_file(clocks_path),
            "total": len(clocks),
            "per_economy": {e: sum(1 for c in clocks
                                   if c["economy"] == e)
                            for e in ("GB", "CA", "AU", "NZ")},
        },
        "announcement_ledger": {
            "manifest": LEDGER_MANIFEST,
            "pin": pinned,
            "sha256": ledger_sha,
            "rows": n_rows,
            "match": True,
        },
    }


# -------------------------------------------------------------------------- #
# structural recorder (counts only; wraps the family module at registration) #
# -------------------------------------------------------------------------- #
class StructuralRecorder:
    """Delegates ``run_arm`` to the wrapped family module and records a
    compact STRUCTURAL summary of the result (counts and reason tallies
    only -- never prices, never PnL) so the sanitized record can show
    force-flat and zero-position mechanics without leaking outcomes."""

    def __init__(self, family_id, module):
        self.family_id = family_id
        self._module = module
        self.summaries = {}

    @property
    def wrapped(self):
        return self._module

    def run_arm(self, arm, data_paths, macro_reader, freeze_token=None):
        result = self._module.run_arm(arm, data_paths, macro_reader, freeze_token)
        self.summaries[arm] = structural_summary(result)
        return result


def structural_summary(result):
    """Counts-only projection of one family run_arm result."""
    meta = result.get("meta") or {}
    decisions = result.get("decisions") or []
    summary = {
        "n_decisions_returned": len(decisions),
        "n_financing_events": len(result.get("financing_events") or []),
        "n_force_flat_decisions": sum(1 for d in decisions
                                      if d.get("force_flat")),
    }
    if isinstance(meta.get("clock_counters"), dict):
        summary["clock_counters"] = dict(meta["clock_counters"])
    if isinstance(meta.get("economy_clock_counts"), dict):
        summary["economy_clock_counts"] = dict(meta["economy_clock_counts"])
    if isinstance(meta.get("skipped_counts"), dict):
        summary["skipped_reason_counts"] = meta["skipped_counts"]
    if isinstance(meta.get("schedule_totals"), dict):
        summary["schedule_totals"] = meta["schedule_totals"]
    if isinstance(meta.get("frozen_constants"), dict):
        summary["frozen_constants"] = meta["frozen_constants"]
    return summary


# -------------------------------------------------------------------------- #
# recursive PnL-leak scan                                                    #
# -------------------------------------------------------------------------- #
def recursive_leak_scan(record):
    """Walk EVERY dict/list leaf of ``record`` and return
    ``(findings, fields_scanned)``.  A finding is any of:
      * a dict key outside FIELD_ALLOWLIST (pair names under
        PAIR_KEY_PARENTS; economies under ECONOMY_KEY_PARENTS; the frozen
        clocks->pair map under CLOCK_PAIR_PARENTS; reason ids under
        REASON_KEY_PARENTS; tier labels under TIER_KEY_PARENTS),
      * a value under an outcome-suspect key name that is not a
        zero/None/empty placeholder,
      * a broken dry-run flag (scored/real_pnl/published not false,
        dry_run not true)."""
    findings = []
    scanned = 0

    def _zero_ok(value):
        if isinstance(value, dict):
            return all(_zero_ok(v) for v in value.values())
        if isinstance(value, list):
            return all(_zero_ok(v) for v in value)
        if isinstance(value, bool):
            return value is False
        if isinstance(value, (int, float)):
            return value == 0
        return value is None

    def _walk(node, path, parent_key):
        nonlocal scanned
        if isinstance(node, dict):
            for key, value in node.items():
                scanned += 1
                if not isinstance(key, str):
                    findings.append(f"{path}: non-string key {key!r}")
                    continue
                if parent_key in PAIR_KEY_PARENTS:
                    if key not in PAIR_NAMES:
                        findings.append(f"{path}.{key}: key not a pair name")
                elif parent_key in REASON_KEY_PARENTS:
                    if not key:
                        findings.append(f"{path}.{key}: key not a reason id")
                elif parent_key in TIER_KEY_PARENTS:
                    if key not in TIER_KEYS:
                        findings.append(f"{path}.{key}: key not a tier label")
                elif parent_key in ECONOMY_KEY_PARENTS:
                    if key not in ECONOMY_KEYS:
                        findings.append(
                            f"{path}.{key}: key not an evidenced economy")
                elif parent_key in CLOCK_PAIR_PARENTS:
                    if key not in ECONOMY_KEYS:
                        findings.append(
                            f"{path}.{key}: key not an evidenced economy")
                elif key not in FIELD_ALLOWLIST:
                    findings.append(f"{path}.{key}: key outside allowlist")
                if isinstance(key, str) and OUTCOME_VALUE_RE.search(key):
                    if key in OUTCOME_LABEL_KEYS:
                        if not isinstance(value, (str, type(None))):
                            findings.append(
                                f"{path}.{key}: label key carries "
                                f"non-string value {value!r}")
                    elif not _zero_ok(value):
                        findings.append(
                            f"{path}.{key}: outcome-suspect key carries "
                            f"non-placeholder value {value!r}")
                _walk(value, f"{path}.{key}", key)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                scanned += 1
                _walk(value, f"{path}[{i}]", parent_key)

    _walk(record, "$", None)
    for flag, expected in (("scored", False), ("real_pnl", False),
                           ("published", False), ("dry_run", True)):
        if record.get(flag) is not expected:
            findings.append(f"$.{flag}: expected {expected}, "
                            f"got {record.get(flag)!r}")
    return findings, scanned


# -------------------------------------------------------------------------- #
# P-2 margin-to-fail scaffold (every gate: threshold + observed + margin)    #
# -------------------------------------------------------------------------- #
# Frozen gate definitions (inherited Stage-A constants; threshold and
# comparator frozen, observed read from the record, margin = the SIGNED
# distance to the fail boundary in the pass direction: margin > 0 passes,
# margin <= 0 fails; None when the observed value is None/not evaluated).
def gate_scaffold(rec):
    """Build the P-2 margin-to-fail scaffold for one cell record.

    Returns a list of {gate, threshold, comparator, observed, margin}
    where margin is signed in the PASS direction (margin = observed -
    threshold for '>' gates, threshold - observed for '<' gates; None when
    the observed value is None i.e. the gate is not evaluable on this
    record).  In dummy mode this runs on the kernel's sanitized
    placeholders (observed 0.0/None) -- explicitly not evidence; the
    scored path runs the identical scaffold on the booked book."""
    base = rec.get("base") or {}
    pop = [f for f in rec.get("folds", []) if f.get("populated")]
    pos_folds = [f for f in pop if f.get("expectancy", 0.0) > 0]

    def _margin(gate, threshold, comparator, observed):
        if observed is None:
            margin = None
        elif comparator in (">", ">="):
            margin = round(observed - threshold, 10)
        else:
            margin = round(threshold - observed, 10)
        return {"gate": gate, "threshold": threshold,
                "comparator": comparator, "observed": observed,
                "margin": margin}

    rows = [
        _margin("financing_adjusted_expectancy_gt_0", 0.0, ">",
                base.get("expectancy")),
        _margin("pf_ge_1.10", R.MIN_PF, ">=", base.get("pf")),
        _margin("decisions_floor_40", R.MIN_DECISIONS_PER_ARM, ">=",
                float(rec.get("n_decisions", 0))),
        _margin("positive_populated_folds_ge_2", float(R.MIN_POSITIVE_FOLDS),
                ">=", float(len(pos_folds))),
        _margin("mdd_within_2500_usd", R.MDD_CEILING_USD, "<=",
                rec.get("mdd_usd")),
        _margin("positive_fold_share_le_0.50", R.MAX_POS_FOLD_SHARE, "<=",
                rec.get("fold_positive_share")),
        _margin("pair_concentration_le_0.40", R.MAX_PAIR_POS_SHARE, "<=",
                (max(rec["pair_concentration"].values())
                 if rec.get("pair_concentration") else None)),
    ]
    stress = rec.get("stress") or {}
    tier2 = stress.get("tier2.0") or {}
    rows.append(_margin("stress_tier2.0_primary_total_pnl_gt_0", 0.0, ">",
                        tier2.get("total_pnl")))
    rows.append(_margin("stress_tier2.0_primary_pf_ge_1.00", R.STRESS_MIN_PF,
                        ">=", tier2.get("pf")))
    scenarios = rec.get("dropout_scenarios") or []
    surv = sum(1 for s in scenarios if s.get("survived"))
    rows.append(_margin("dropout_survival_ge_6_of_8", float(R.DROPOUT_MIN_SURVIVAL),
                        ">=", float(surv) if scenarios else None))
    rows.append(_margin("incremental_alpha_gt_0", 0.0, ">",
                        rec.get("incremental_alpha")))
    diag = rec.get("usd_drift_diag") or {}
    rows.append(_margin("usd_drift_corr_abs_le_0.30", R.USD_CORR_CEILING,
                        "<=", (abs(diag["corr"])
                               if diag.get("evaluated") and
                               diag.get("corr") is not None else None)))
    return rows


# -------------------------------------------------------------------------- #
# launch gates (scored path; fail closed)                                    #
# -------------------------------------------------------------------------- #
def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_launch_gates(root=ROOT, scored_ledger_path=None):
    """The five frozen launch gates of the V5 run contract (all must hold
    before the scored path computes anything; the I1 lane never runs it)."""
    gates = {}

    def _check(name, ok, detail):
        gates[name] = {"ok": bool(ok), "detail": str(detail)}

    # 1) W4 freeze with matching code hashes
    freeze_path = os.path.join(root, GATE_W4_FREEZE)
    if not os.path.exists(freeze_path):
        _check("w4_freeze", False, f"missing {GATE_W4_FREEZE}")
    else:
        freeze = _load_json(freeze_path)
        if freeze.get("freeze_token") != W4_FREEZE_TOKEN:
            _check("w4_freeze", False, "freeze_token mismatch")
        else:
            bad = []
            for rel in W4_CODE_HASH_FILES:
                expected = (freeze.get("code_hashes") or {}).get(rel)
                actual = sha256_file(os.path.join(root, rel)) \
                    if os.path.exists(os.path.join(root, rel)) else None
                if expected is None or actual is None or expected != actual:
                    bad.append(rel)
            _check("w4_freeze", not bad,
                   "all pinned code hashes match" if not bad else
                   f"code hash mismatches: {bad}")

    # 2) independent S0 authorization
    s0_path = os.path.join(root, GATE_S0)
    if not os.path.exists(s0_path):
        _check("s0_launch_authorized", False,
               f"missing {GATE_S0} (independent S0 artifact)")
    else:
        s0 = _load_json(s0_path)
        unresolved = [f for f in (s0.get("findings") or [])
                      if isinstance(f, dict)
                      and f.get("severity") in ("HIGH", "CRITICAL")
                      and not f.get("resolved")]
        _check("s0_launch_authorized",
               s0.get("verdict") == S0_VERDICT and not unresolved,
               f"verdict={s0.get('verdict')!r} "
               f"unresolved_high_critical={len(unresolved)}")

    # 3) owner FRESH exact-phrase GO postdating the S0 artifact
    go_path = os.path.join(root, GATE_FRESH_GO)
    if not os.path.exists(go_path):
        _check("owner_fresh_go", False,
               f"missing {GATE_FRESH_GO} (fresh exact-phrase owner GO)")
    else:
        go = _load_json(go_path)
        phrase_ok = go.get("phrase") == OWNER_GO_PHRASE
        fresh = (os.path.getmtime(go_path) > os.path.getmtime(s0_path)
                 if os.path.exists(s0_path) else False)
        _check("owner_fresh_go", phrase_ok and fresh,
               f"phrase_ok={phrase_ok} postdates_s0={fresh}")

    # 4) budget: fewer than PLANNED_SCORED_CELLS cells consumed, recorded
    #    in the V5 run contract (missing contract: fail closed)
    contract_path = os.path.join(root, GATE_RUN_CONTRACT)
    if not os.path.exists(contract_path):
        _check("budget", False, "RUN_CONTRACT_MISSING")
    else:
        contract = _load_json(contract_path)
        planned = (contract.get("budget") or {}).get(
            "planned_scored_cells", PLANNED_SCORED_CELLS)
        recorded_used = (contract.get("budget") or {}).get("used", 0)
        consumed = int(recorded_used)
        ledger = scored_ledger_path or os.path.join(root,
                                                    SCORED_LEDGER_DEFAULT)
        if os.path.exists(ledger):
            with open(ledger, "r", encoding="utf-8") as handle:
                consumed = max(consumed,
                               sum(1 for line in handle if line.strip()))
        _check("budget", consumed < planned,
               f"{consumed}/{planned} scored cells consumed")

    # 5) S1 seal intact (status flag read; sealed artifact never touched)
    state_path = os.path.join(root, GATE_STATE)
    if not os.path.exists(state_path):
        _check("s1_seal", False, "STATE_MISSING: cannot confirm the S1 seal")
    else:
        state = _load_json(state_path)
        seal = state.get("s1")
        _check("s1_seal", seal == "SEALED_UNTOUCHED", f"s1={seal!r}")

    return all(g["ok"] for g in gates.values()), gates


# -------------------------------------------------------------------------- #
# the three-arm driver                                                       #
# -------------------------------------------------------------------------- #
def _register_families(root=ROOT):
    recorders = {}
    for family_id, spec in FAMILY_MODULES.items():
        module = importlib.import_module(spec["module"])
        proposal_path = os.path.join(root, spec["proposal"])
        if not os.path.exists(proposal_path):
            raise RuntimeError(
                f"PROPOSAL_PACKET_MISSING: {proposal_path} (materialize it "
                "from git object c82403d8c6f39a9d31c276db4d8510b70313c6cd)")
        actual = sha256_file(proposal_path)
        if actual != spec["proposal_sha256"]:
            raise RuntimeError(
                f"PROPOSAL_SHA_MISMATCH: {spec['proposal']} {actual}")
        recorder = StructuralRecorder(family_id, module)
        R.register_family(family_id, recorder)
        recorders[family_id] = recorder
    return recorders


def _ledger_reader(data_paths):
    """The pinned-ledger vintage reader (financing kernel input).  Built
    here so the kernel's compute_cell never needs a macro_vintages mapping:
    the family's financing authority is the pinned V5-extension ledger,
    accounting only."""
    from research.assets.forex_free_v5 import family_a6p1 as F
    return F.LedgerVintageReader(
        F.dedupe_ledger_rows(F.load_ledger_rows(
            data_paths["announcement_ledger"])))


def _arm_config(rec, family_id, arm, recorder, spec, root=ROOT):
    module_path = FAMILY_MODULES[family_id]["module"]
    module = importlib.import_module(module_path)
    config = {
        "cycle_id": CYCLE_ID,
        "family_id": family_id,
        "arm": arm,
        "arm_id": module.ARM_IDS[arm],
        "record_id": rec["record_id"],
        "proposal_sha256": spec["proposal_sha256"],
        "module_sha256": sha256_file(
            os.path.join(root, module_path.replace(".", "/") + ".py")),
        "frozen_config": {
            "trailing_return_sum_ny_days": module.TRAILING_RETURN_SUM_NY_DAYS,
            "sham_shift_calendar_days": module.SHAM_SHIFT_CALENDAR_DAYS,
            "staleness_mode": (module.STALENESS_MODE if arm in
                               ("control", "benchmark_treatment") else None),
            "s0_cap_entry_utc": module.S0_CAP_ENTRY_UTC,
            "warmup_daily_bars": module.WARMUP_NY_CLOSES,
            "notional_usd_unit": module.NOTIONAL_USD,
            "clocks_pair_map": dict(module.ECONOMY_PAIR),
            "economy_order": list(module.ECONOMY_ORDER),
            "financing_formula_id": module.FINANCING_FORMULA_ID,
            "alpha_definition": module.ALPHA_DEFINITION,
            "decision_clock": "daily",
        },
    }
    return config


def _attach_and_check(rec, family_id, arm, recorder, spec, root=ROOT):
    """Attach trial identity + structural block + placeholder gate check +
    the P-2 margin scaffold to a sanitized record, run the recursive leak
    scan (fail closed)."""
    config = _arm_config(rec, family_id, arm, recorder, spec, root)
    digest = accounting.sha256_hex(accounting.canonical_json_bytes(config))

    rec["trial_id"] = f"{CYCLE_ID}/{family_id}/{arm}"
    rec["arm_config_digest"] = digest
    structure = dict(recorder.summaries.get(arm) or {})
    structure["cycle_id_in_record"] = CYCLE_ID
    structure["structure_family"] = family_id
    structure["structure_arm"] = arm
    n_trades = int(rec.get("n_trades_kept", 0))
    structure["zero_positions"] = {
        "n_trades_kept": n_trades,
        "would_refuse_publication": n_trades == 0,
        "refusal_code": "STRESS_EMPTY_TRADE_SET" if n_trades == 0 else None,
    }
    rec["dryrun_structure"] = structure
    gates, reasons = R.stage_a_gates(rec)
    rec["dryrun_gate_check"] = {
        "evaluated_on": "sanitized_placeholders_not_evidence",
        "gate_pass": bool(gates),
        "gate_reasons": list(reasons),
    }
    rec["dryrun_gate_scaffold"] = {
        "evaluated_on": "sanitized_placeholders_not_evidence",
        "gates": gate_scaffold(rec),
    }
    findings, scanned = recursive_leak_scan(rec)
    if findings:
        raise RuntimeError(
            f"PNL_LEAK_SCAN_FAILED {family_id}:{arm}: {findings[:10]}")
    return digest, scanned


def _schedule_invariant(summary, rec):
    """Programmatic check of the frozen schedule invariant "every scheduled
    round trip becomes exactly one emitted decision" (runner contract: one
    decision per scheduled round trip)."""
    totals = summary.get("schedule_totals")
    if isinstance(totals, dict) and totals:
        scheduled = sum(int(v.get("round_trips", 0)) for v in totals.values())
        return scheduled == int(rec.get("n_decisions", 0)), {
            "n_round_trips_scheduled": scheduled,
            "n_decisions_recorded": rec.get("n_decisions")}
    return True, {}


def run_dummy(data_paths, ledger_path, report_path, root=ROOT,
              macro_reader=None, timeout_minutes=None):
    """The three-arm SANITIZED dummy dry-run.  Records go ONLY to a
    temporary ledger under dryrun_tmp/; nothing is scored, published or
    budgeted.  Replay-safe: a second run appends nothing (once-only
    publication) and produces byte-identical records."""
    tmp_dir = os.path.join(root, V5_CTL, DRYRUN_TMP_DIRNAME)
    abs_ledger = os.path.abspath(ledger_path)
    abs_tmp = os.path.abspath(tmp_dir)
    if os.path.commonpath([abs_ledger, abs_tmp]) != abs_tmp:
        raise SystemExit(
            f"DUMMY_LEDGER_MUST_BE_TEMPORARY: {abs_ledger} is not under "
            f"{abs_tmp} (dummy records never enter any canonical ledger)")
    os.makedirs(abs_tmp, exist_ok=True)

    t0 = time.time()
    data_verification = verify_staged_data(root)
    recorders = _register_families(root)
    if macro_reader is None:
        macro_reader = _ledger_reader(data_paths)
    freeze_token = None  # dummy: the kernel sanitizes every monetary metric

    arms_out = []
    family_cells = {}
    leak_fields_total = 0
    for family_id in FAMILY_MODULES:
        recorder = recorders[family_id]
        spec = FAMILY_MODULES[family_id]
        for arm in R.ARMS:  # anchor -> neighbour -> control, serial
            rec = R.compute_cell(family_id, arm, data_paths,
                                 freeze_token=freeze_token,
                                 macro_reader=macro_reader,
                                 timeout_minutes=timeout_minutes)
            digest, scanned = _attach_and_check(rec, family_id, arm,
                                                recorder, spec, root)
            leak_fields_total += scanned
            inv_ok, inv_counts = _schedule_invariant(
                recorder.summaries.get(arm) or {}, rec)
            payload = accounting.canonical_json_bytes(rec)
            observed_delta, published_now = accounting.AtomicJsonlPublisher(
                abs_ledger).publish_once(rec)
            family_module = importlib.import_module(spec["module"])
            arms_out.append({
                "family": family_id, "arm": arm,
                "arm_id": family_module.ARM_IDS[arm],
                "record_id": rec["record_id"],
                "trial_id": rec["trial_id"],
                "arm_config_digest": digest,
                "record_sha256": accounting.sha256_hex(payload),
                "n_decisions": rec["n_decisions"],
                "n_trades_kept": rec["n_trades_kept"],
                "purged_trades": rec["purged_trades"],
                "weekend_gate_dropped": rec["weekend_gate_dropped"],
                "n_force_flat_decisions":
                    rec["dryrun_structure"]["n_force_flat_decisions"],
                "zero_positions": rec["dryrun_structure"]["zero_positions"],
                "schedule_invariant": {"ok": bool(inv_ok),
                                       "counts": inv_counts},
                "dry_run": rec["dry_run"], "scored": rec["scored"],
                "real_pnl": rec["real_pnl"], "published": rec["published"],
                "observed_delta": observed_delta,
                "published_now": published_now,
                "placeholder_gate_check": rec["dryrun_gate_check"],
                "gate_scaffold": rec["dryrun_gate_scaffold"],
            })
            family_cells.setdefault(family_id, {})[arm] = rec
            print(json.dumps({"arm": rec["record_id"],
                              "n_decisions": rec["n_decisions"],
                              "n_trades_kept": rec["n_trades_kept"],
                              "leak_scan": "clean",
                              "observed_delta": observed_delta,
                              "published_now": published_now}), flush=True)

    pairwise_ids = len({a["record_id"] for a in arms_out}) == len(arms_out) \
        and len({a["trial_id"] for a in arms_out}) == len(arms_out) \
        and len({a["arm_config_digest"] for a in arms_out}) == len(arms_out)
    if not pairwise_ids:
        raise RuntimeError("PAIRWISE_ID_VIOLATION: record/trial/digest ids "
                           "collide across arms")

    invariant_violations = [
        {"record_id": a["record_id"], "counts": a["schedule_invariant"]["counts"]}
        for a in arms_out if not a["schedule_invariant"]["ok"]]

    sanity = {}
    for family_id, cells in family_cells.items():
        ok, reasons = R.mechanism_sanity(cells)
        sanity[family_id] = {
            "evaluated_on": "sanitized_placeholders_not_evidence",
            "pass": bool(ok), "reasons": list(reasons)}

    report = {
        "schema": REPORT_SCHEMA,
        "mode": "dummy",
        "cycle_id": CYCLE_ID,
        "family_id": FAMILY_ID,
        "scored": False, "real_pnl": False, "published": False,
        "dry_run_utc": _utc_now_iso(), "stamp_source": "machine_date_u",
        "base_head": git_head(root),
        "code_freeze_sha": CODE_FREEZE_SHA_PLACEHOLDER,
        "data_verification": data_verification,
        "arms": arms_out,
        "arm_record_counts": {a["record_id"]: a["n_decisions"]
                              for a in arms_out},
        "pairwise_distinct_ids": pairwise_ids,
        "structural_invariant_violations": invariant_violations,
        "recursive_leak_scan": {
            "records_scanned": len(arms_out),
            "fields_scanned": leak_fields_total,
            "leaks_found": [],
            "rule": LEAK_SCAN_NOTE,
        },
        "mechanism_sanity": sanity,
        "temporary_ledger": os.path.relpath(abs_ledger, root),
        "denominator_note": "dummy cells never enter the scored budget; the "
                            "observed counter above counts temp-ledger lines "
                            "only",
        "elapsed_s": round(time.time() - t0, 1),
        "limitations": LIMITATIONS,
        "note": "SANITIZED DUMMY DRY-RUN: scored=false, real_pnl=false, "
                "published=false; book values are the kernel's zero/None "
                "placeholders and carry no outcome information.",
    }
    os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print(json.dumps({"mode": "dummy", "arms": len(arms_out),
                      "pairwise_distinct_ids": pairwise_ids,
                      "leaks": 0, "report": report_path}), flush=True)
    return report


def run_scored(data_paths, ledger_path, authorization_path, report_path,
               root=ROOT, freeze_token=W4_FREEZE_TOKEN, macro_reader=None,
               timeout_minutes=None):
    """The SCORED path.  Refuses (SystemExit 2, refusal report written)
    unless ALL FIVE launch gates hold; never invoked by the I1 lane."""
    ok, gates = evaluate_launch_gates(root)
    if not (os.path.exists(ledger_path) and os.path.exists(authorization_path)):
        ok = False
        gates["publication_inputs"] = {
            "ok": False,
            "detail": "scored mode requires --ledger and --authorization"}
    auth = None
    if os.path.exists(authorization_path):
        auth = _load_json(authorization_path)
        if (auth or {}).get("freeze_token") != freeze_token:
            ok = False
            gates["freeze_token"] = {
                "ok": False,
                "detail": f"authorization freeze_token != {freeze_token!r}"}
    if not ok:
        refusal = {
            "schema": "forex_free_v5_scored_refusal_v1",
            "mode": "scored", "cycle_id": CYCLE_ID,
            "refused_utc": _utc_now_iso(), "stamp_source": "machine_date_u",
            "refused": True,
            "gates": gates,
            "note": "LAUNCH GATES NOT SATISFIED: no cell computed, nothing "
                    "booked, nothing published. Two-key protocol: independent "
                    f"S0 artifact {S0_VERDICT}, then a FRESH exact-phrase "
                    f"'{OWNER_GO_PHRASE}' owner GO.",
        }
        os.makedirs(os.path.dirname(os.path.abspath(report_path)),
                    exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(refusal, handle, indent=1, sort_keys=True)
        print(json.dumps({"mode": "scored", "refused": True,
                          "failed_gates": [k for k, v in gates.items()
                                           if not v["ok"]],
                          "report": report_path}), flush=True)
        raise SystemExit(2)

    # Gates satisfied: the frozen kernel path (mirrors the V4 driver).
    R.FAMILIES.clear()
    _register_families(root)
    if macro_reader is None:
        macro_reader = _ledger_reader(data_paths)
    cells = []
    family_cells = {}
    for arm in R.ARMS:
        rec = R.compute_cell(FAMILY_ID, arm, data_paths,
                             freeze_token=freeze_token,
                             macro_reader=macro_reader,
                             timeout_minutes=timeout_minutes)
        rec["trial_id"] = f"{CYCLE_ID}/{FAMILY_ID}/{arm}"
        gates_pass, reasons = R.stage_a_gates(rec)
        rec["dryrun_gate_scaffold"] = {
            "evaluated_on": "booked_scored_book",
            "gates": gate_scaffold(rec),
        }
        rec["observed_delta"], published_now = R.publish_cell(
            ledger_path, rec, authorization_path, freeze_token)
        rec["published"] = published_now == 1
        family_cells[arm] = rec
        cells.append({"cell_id": rec["record_id"],
                      "gate_scaffold": rec["dryrun_gate_scaffold"],
                      "gates_pass": gates_pass, "gate_reasons": reasons,
                      "published": rec["published"],
                      "observed_delta": rec["observed_delta"]})
    sanity, sanity_reasons = R.mechanism_sanity(family_cells)
    cells.append({"cell_id": f"{FAMILY_ID}:MECHANISM_SANITY",
                  "gates_pass": sanity, "gate_reasons": sanity_reasons})
    report = {"schema": "forex_free_v5_scored_report_v1", "mode": "scored",
              "cycle_id": CYCLE_ID, "family_id": FAMILY_ID,
              "dry_run_utc": _utc_now_iso(),
              "stamp_source": "machine_date_u", "cells": cells}
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("dummy", "scored"), required=True)
    ap.add_argument("--data-paths", default=None,
                    help="JSON file with the data_paths dict; default: the "
                         "staged V5 data authority (verified fail-closed)")
    ap.add_argument("--report", required=True)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--authorization", default=None)
    args = ap.parse_args(argv)

    data_paths = build_default_data_paths()
    if args.data_paths:
        data_paths = json.load(open(args.data_paths, encoding="utf-8"))

    if args.mode == "dummy":
        ledger = args.ledger or os.path.join(
            ROOT, V5_CTL, DRYRUN_TMP_DIRNAME, "dummy_ledger.jsonl")
        return run_dummy(data_paths, ledger, args.report)
    if args.mode == "scored":
        if not (args.ledger and args.authorization):
            ap.error("scored mode requires --ledger and --authorization")
        return run_scored(data_paths, args.ledger, args.authorization,
                          args.report)
    ap.error(f"unknown mode {args.mode!r}")  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    main()
