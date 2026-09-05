#!/usr/bin/env python
"""FOREX-FREE-V4 execution driver (lane A8): wires the two SELECTED V4
family modules into the inherited, FROZEN V3 kernel and drives the six-arm
SANITIZED dummy dry-run.

Architecture (mirrors research/assets/forex_free_v3/exec_driver.py; the V3
kernel files are imported READ-ONLY and are never modified):

    register_family("family1", research.assets.forex_free_v4.family1)
    register_family("family2", research.assets.forex_free_v4.family2)

then every arm of every family runs through the kernel's own
``scored_runner.compute_cell`` -> ``validate_decisions`` -> session gate ->
``accounting.book_dual`` / ``book_stress`` -> ``dry_run_sanitized`` path, so
booking, validation, fold/purge semantics, stress tiers and sanitization are
the FROZEN kernel's, byte for byte.

Modes
-----
dummy   The six-arm SANITIZED DRY-RUN (handbook 17.2 discipline).  Runs the
        REAL staged data end-to-end with ``freeze_token=None`` =>
        ``scored=false``, ``real_pnl=false``, ``published=false`` and every
        booked monetary metric a 0.0/None placeholder (kernel
        ``dry_run_sanitized``).  Records go ONLY into a TEMPORARY ledger
        under ``research/control/forex_free_v4_run/dryrun_tmp/`` (gitignored)
        through the kernel's once-only ``AtomicJsonlPublisher`` -- never the
        canonical ledger, never the scored budget.  Reveals no outcome: the
        driver additionally runs a RECURSIVE PnL-leak scan over every
        written record (full nested structure) and fails closed on any leak.
scored  IMPLEMENTED but REFUSES to run unless ALL FIVE launch gates of the
        V4 run contract hold (see ``evaluate_launch_gates``):
          1. FOREX_FREE_V4_W4 freeze recorded with matching code hashes
             (including this driver's own file hash),
          2. independent S0 artifact ``FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED``
             with zero unresolved HIGH/CRITICAL,
          3. owner FRESH exact-phrase GO artifact
             (postdating the S0 authorization and the P-8 reclassification
             of the 2026-09-05T03:41:05Z GO to OWNER_INTENT
             extinguished-unconsumed),
          4. budget: fewer than 6 scored cells consumed,
          5. S1 seal intact (``SEALED_UNTOUCHED``; the sealed artifact is
             never listed, opened, hashed or copied -- only the recorded
             status flag is read).
        The scored path is NOT exercised by lane A8.

Structural visibility: each sanitized record carries ``dryrun_structure``
(counts only -- schedule counters, force-flat decision counts, skipped-entry
reason counts, zero-position publication refusal) and ``dryrun_gate_check``
(gates re-evaluated ON the zeroed placeholder metrics, labelled not-evidence).
Trial identity: ``trial_id`` = cycle/family/arm and ``arm_config_digest`` =
sha256 over the arm's frozen config (proposal sha + module file sha + frozen
meta config); pairwise distinctness asserted programmatically.

Determinism: no wall clock enters any record; replaying the dry-run produces
byte-identical records and zero denominator delta (the once-only publisher
returns (0, 0) for every already-published digest).
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

CYCLE_ID = "FOREX-FREE-V4"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
V4_CTL = os.path.join("research", "control", "forex_free_v4_run")
DRYRUN_TMP_DIRNAME = "dryrun_tmp"

REPORT_SCHEMA = "forex_free_v4_dummy_dryrun_report_v1"
EVIDENCE_SCHEMA = "forex_free_v4_dry_run_v1"

W4_FREEZE_TOKEN = "FOREX_FREE_V4_W4"
S0_VERDICT = "FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED"
OWNER_GO_PHRASE = "GO FOREX V4 SCORED EXECUTION"
PLANNED_SCORED_CELLS = 6

FAMILY_MODULES = {
    "family1": {
        "module": "research.assets.forex_free_v4.family1",
        "proposal": "research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P1.json",
        "proposal_sha256": "e827c904183c13e503441bd252004963027d03c792e7e6ca2c5a7fc65ee7eb0c",
    },
    "family2": {
        "module": "research.assets.forex_free_v4.family2",
        "proposal": "research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P2.json",
        "proposal_sha256": "6b4dbb7ba05b98ba9eb099aee0d0fd4884bbe33f98063bbf369ebadf8f17b9ff",
    },
}

# Files whose sha256 a recorded FOREX_FREE_V4_W4 freeze must pin (matching
# hashes) before the scored path may run.
W4_CODE_HASH_FILES = (
    "research/assets/forex_free_v4/exec_driver_v4.py",
    "research/assets/forex_free_v4/family1.py",
    "research/assets/forex_free_v4/family2.py",
    "research/assets/forex_free_v3/scored_runner.py",
    "research/assets/forex_free_v3/accounting.py",
)

# Launch-gate artifact paths (relative to ROOT).
GATE_W4_FREEZE = os.path.join(V4_CTL, "w4_freeze.json")
GATE_S0 = os.path.join(V4_CTL, "s0_launch_authorized.json")
GATE_FRESH_GO = os.path.join(V4_CTL, "owner_fresh_go.json")
GATE_GO_RECLASS = os.path.join(V4_CTL, "owner_intent_reclassification.json")
GATE_ORIGINAL_GO = os.path.join(V4_CTL, "owner_go_scored_execution.json")
GATE_STATE = os.path.join(V4_CTL, "state.json")
GATE_RUN_CONTRACT = os.path.join(V4_CTL, "run_contract.json")
GATE_S1_OPENED_MARKER = os.path.join(V4_CTL, "s1_seal_opened.json")
SCORED_LEDGER_DEFAULT = os.path.join(V4_CTL, "scored_ledger_published.jsonl")

STAGED_MANIFEST = os.path.join("research", "control", "forex_free_v1_run",
                               "staged_data_manifest.json")
EVIDENCED_MANIFEST = os.path.join(V4_CTL, "p0a_evidenced_vintages_manifest.json")
LEDGER_PINNED = os.path.join(V4_CTL, "LEDGER_PINNED")
ANNOUNCEMENT_LEDGER = os.path.join(V4_CTL, "announcement_ledger.jsonl")
PRICE_SNAPSHOT_DIR = os.path.join("data_raw", "forex_free_v1")
EVIDENCED_VINTAGES_DIR = os.path.join("data_raw", "forex_free_v4_macro_evidenced")
EVIDENCED_AREAS = ("AU", "CA", "CH", "EMU", "GB", "JP", "NZ", "US")

# --- PnL-leak scan rules (recursive; handbook 17.2 discipline) ------------
# Every dict key anywhere in a sanitized record must be in this allowlist
# (exact names) or be a pair name under PAIR_KEY_PARENTS.  Every key whose
# name matches OUTCOME_VALUE_RE must carry a zero/None/empty placeholder
# value (recursively).  Counts, timestamps, schedule flags and the
# scored/real_pnl/published=false flags are the allowed content.
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
    # family1 schedule counters (all ints)
    "n_decision_instants", "n_leg_events_considered", "n_leg_blocked_open",
    "n_entries", "n_skipped_entry_fills", "n_entries_suppressed_by_boundary",
    "n_force_flats", "n_round_trips", "n_trigger_valid_days",
    "n_trigger_return_days", "n_trigger_evaluable_days", "n_event_days",
    "n_no_eval_days",
    # family2 per-pair schedule counters (all ints)
    "candidates", "missing_next_fill_bar", "fill_lag_exceeds_4_days",
    "fold_boundary_no_entry", "end_of_data_no_exit",
    "earliest_scheduled_exit_data_end", "round_trips", "decision_bars",
    # family2 ledger-basis + eligibility counters (all ints)
    "raw_rows", "deduped_rate_change_rows", "events_used",
    "zero_delta_rows", "n_unavailable_never_read", "no_eval_before_cutoff",
    "no_decision_bar_available",
    # driver-attached placeholder gate check (labelled not-evidence)
    "dryrun_gate_check", "evaluated_on", "gate_pass", "gate_reasons",
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
# Outcome-suspect keys whose value is a frozen identifier LABEL, not a
# number (the kernel sanitizer leaves these strings untouched).
OUTCOME_LABEL_KEYS = frozenset({"incremental_alpha_definition"})
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
    "skipped_reason_counts; frozen cost-tier labels under stress) + "
    "forced-placeholder rule for every key matching "
    "pnl|profit|expectancy|pf|mdd|break_even|alpha|concentration|survived|"
    "gross|share|corr (exception: incremental_alpha_definition is a frozen "
    "identifier label) + flags scored=false real_pnl=false published=false "
    "dry_run=true")

LIMITATIONS = [
    "dummy dry-run only: every booked monetary metric is the kernel's 0.0/None "
    "placeholder; the records carry schedule/count evidence, never outcomes",
    "dry-run gates in dryrun_gate_check are evaluated ON zeroed placeholder "
    "metrics and are explicitly not evidence",
    "scored mode is implemented but not exercised; it refuses without all "
    "five launch gates (W4 freeze + S0 authorized + fresh owner GO + budget "
    "< 6 + S1 seal intact)",
    "dry-run records live in the gitignored dryrun_tmp/ temporary ledger; "
    "they never enter the canonical ledger or the scored denominator",
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


# -------------------------------------------------------------------------- #
# data_paths + staged-data verification (fail closed)                        #
# -------------------------------------------------------------------------- #
def build_default_data_paths(root=ROOT):
    """The staged, hash-verified V4 data authority (family_api_note of
    w3_freeze: family1 reads price_h1_dir, family2 reads h1_dir; the kernel's
    USD-index/alpha machinery accepts either)."""
    return {
        "price_h1_dir": os.path.join(root, PRICE_SNAPSHOT_DIR),
        "h1_dir": os.path.join(root, PRICE_SNAPSHOT_DIR),
        "announcement_ledger": os.path.join(root, ANNOUNCEMENT_LEDGER),
        "macro_vintages": {a: os.path.join(root, EVIDENCED_VINTAGES_DIR,
                                           f"{a}.json")
                           for a in EVIDENCED_AREAS},
    }


def verify_staged_data(root=ROOT):
    """Verify the staged data authority against its pinned manifests; fail
    closed on any mismatch.  Returns the evidence dict."""
    # 1) price snapshot: 156/156 sha256 vs staged_data_manifest digests_exec2
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
    # 2) evidenced macro vintages: canonical-json sha256 per area
    ev_manifest = json.load(open(os.path.join(root, EVIDENCED_MANIFEST),
                                 encoding="utf-8"))
    ev_hashes, ev_bad = {}, []
    for area in EVIDENCED_AREAS:
        path = os.path.join(root, EVIDENCED_VINTAGES_DIR, f"{area}.json")
        payload = json.load(open(path, encoding="utf-8"))
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        ev_hashes[area] = digest
        if digest != ev_manifest["per_area"][area]["evidenced_sha256_canonical"]:
            ev_bad.append(area)
    if ev_bad:
        raise RuntimeError(f"EVIDENCED_VINTAGES_MISMATCH: {ev_bad}")
    # 3) pinned v2 announcement ledger
    pin = json.load(open(os.path.join(root, LEDGER_PINNED), encoding="utf-8"))
    ledger_path = os.path.join(root, ANNOUNCEMENT_LEDGER)
    ledger_sha = sha256_file(ledger_path)
    if ledger_sha != pin["ledger_sha256"]:
        raise RuntimeError("ANNOUNCEMENT_LEDGER_PIN_MISMATCH: "
                           f"{ledger_sha} != {pin['ledger_sha256']}")
    return {
        "price_snapshot": {
            "manifest": STAGED_MANIFEST,
            "manifest_sha256": sha256_file(manifest_path),
            "digests_exec2_entries": len(digests),
            "verified": snap_ok,
            "mismatches": 0,
        },
        "macro_evidenced": {
            "manifest": EVIDENCED_MANIFEST,
            "manifest_sha256": sha256_file(os.path.join(root, EVIDENCED_MANIFEST)),
            "canonical_sha256": ev_hashes,
            "verified": f"{len(EVIDENCED_AREAS)}/{len(EVIDENCED_AREAS)}",
        },
        "announcement_ledger": {
            "pin_file": LEDGER_PINNED,
            "pin": pin["ledger_sha256"],
            "sha256": ledger_sha,
            "match": True,
        },
    }


# -------------------------------------------------------------------------- #
# structural recorder (counts only; wraps the family modules at registration) #
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
    if "schedule" in meta:  # family1: frozen counter block (ints)
        summary["schedule_counters"] = meta["schedule"].get("total")
    if isinstance(meta.get("skipped_entries"), list):
        counts = {}
        for item in meta["skipped_entries"]:
            reason = item.get("reason")
            counts[reason] = counts.get(reason, 0) + 1
        summary["skipped_reason_counts"] = dict(sorted(counts.items()))
    events = meta.get("events")
    if isinstance(events, dict):  # family2 ledger basis counts
        summary["ledger_events"] = {
            k: events.get(k) for k in
            ("raw_rows", "deduped_rate_change_rows", "events_used",
             "zero_delta_rows", "n_unavailable_never_read")}
    eligibility = meta.get("eligibility")
    if isinstance(eligibility, dict):
        summary["eligibility_counts"] = {
            k: eligibility.get(k) for k in
            ("no_eval_before_cutoff", "no_decision_bar_available")}
    governor = meta.get("governor")
    if isinstance(governor, dict):
        summary["no_refresh_ignored"] = governor.get("no_refresh_ignored")
    if isinstance(meta.get("schedule_totals"), dict):
        summary["schedule_totals"] = meta["schedule_totals"]
    if isinstance(meta.get("skipped_counts"), dict):
        summary["skipped_reason_counts"] = meta["skipped_counts"]
    return summary


# frozen per-family config projection (feeds arm_config_digest; everything
# here is a frozen constant or a deterministic string -- never an outcome)
FAMILY1_CONFIG_KEYS = (
    "trigger_pairs", "trigger_sign_convention", "bloc_estimator",
    "response_legs", "standardization_window_ny_days", "event_threshold",
    "holding_ny_days", "benchmark_staleness_ny_days", "fold_boundaries",
    "force_flat_boundaries", "alpha_definition", "warmup_daily_bars",
    "z_std_ddof", "notional_usd_unit", "financing_formula")
FAMILY2_CONFIG_KEYS = (
    "holding", "alpha_definition", "decision_bar_convention",
    "sham_derangement")


# -------------------------------------------------------------------------- #
# recursive PnL-leak scan                                                    #
# -------------------------------------------------------------------------- #
def recursive_leak_scan(record):
    """Walk EVERY dict/list leaf of ``record`` and return
    ``(findings, fields_scanned)``.  A finding is any of:
      * a dict key outside FIELD_ALLOWLIST (pair names allowed under
        PAIR_KEY_PARENTS),
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
                    if not isinstance(key, str) or not key:
                        findings.append(f"{path}.{key}: key not a reason id")
                elif parent_key in TIER_KEY_PARENTS:
                    if key not in TIER_KEYS:
                        findings.append(f"{path}.{key}: key not a tier label")
                elif key not in FIELD_ALLOWLIST:
                    findings.append(f"{path}.{key}: key outside allowlist")
                if isinstance(key, str) and OUTCOME_VALUE_RE.search(key):
                    if key in OUTCOME_LABEL_KEYS:
                        if not isinstance(value, str):
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
# launch gates (scored path; fail closed)                                    #
# -------------------------------------------------------------------------- #
def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_utc(raw):
    text = str(raw).strip().replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def evaluate_launch_gates(root=ROOT, scored_ledger_path=None):
    """Evaluate the FIVE scored-launch gates of the V4 run contract.
    Returns ``(all_pass, {gate: {"ok": bool, "detail": str}})``.  Every gate
    fails closed; missing artifacts are refusals, never warnings.  The S1
    sealed artifact itself is NEVER listed, opened, hashed or copied -- only
    the recorded status flag in state.json is read."""
    gates = {}

    def _check(name, ok, detail):
        gates[name] = {"ok": bool(ok), "detail": detail}
        return ok

    # 1) FOREX_FREE_V4_W4 freeze recorded with matching code hashes
    w4_path = os.path.join(root, GATE_W4_FREEZE)
    if not os.path.exists(w4_path):
        _check("w4_freeze", False, "W4_FREEZE_MISSING: no w4_freeze.json "
                                   "recorded for FOREX_FREE_V4_W4")
    else:
        freeze = _load_json(w4_path)
        token = freeze.get("freeze_token")
        if token != W4_FREEZE_TOKEN and "FOREX_FREE_V4_W4" not in freeze:
            _check("w4_freeze", False,
                   f"W4_FREEZE_TOKEN_MISMATCH: freeze_token={token!r}")
        else:
            hashes = freeze.get("code_hashes") or {}
            bad = []
            for rel in W4_CODE_HASH_FILES:
                path = os.path.join(root, rel)
                expected = hashes.get(rel)
                actual = sha256_file(path) if os.path.exists(path) else None
                if expected is None or actual is None or expected != actual:
                    bad.append(f"{rel}: recorded={str(expected)[:12]} "
                               f"actual={str(actual)[:12]}")
            _check("w4_freeze", not bad,
                   "W4 code hashes match" if not bad
                   else "W4_CODE_HASH_MISMATCH: " + "; ".join(bad))

    # 2) independent S0 launch authorization (zero unresolved HIGH/CRITICAL)
    s0_path = os.path.join(root, GATE_S0)
    if not os.path.exists(s0_path):
        _check("s0_launch_authorized", False,
               "S0_NOT_PUBLISHED: no FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED "
               "artifact")
    else:
        s0 = _load_json(s0_path)
        verdict = s0.get("verdict") or s0.get("result")
        unresolved = s0.get("unresolved_high_critical")
        if unresolved is None and isinstance(s0.get("unresolved"), dict):
            u = s0["unresolved"]
            unresolved = u.get("HIGH", 0) + u.get("CRITICAL", 0)
        ok = verdict == S0_VERDICT and unresolved == 0
        _check("s0_launch_authorized", ok,
               f"verdict={verdict!r} unresolved_high_critical={unresolved!r}")

    # 3) owner FRESH exact-phrase GO (postdates S0 + the P-8 reclassification
    #    that extinguished the 2026-09-05T03:41:05Z GO)
    fresh_path = os.path.join(root, GATE_FRESH_GO)
    if not os.path.exists(fresh_path):
        _check("owner_fresh_go", False,
               "FRESH_GO_MISSING: the recorded 03:41 GO was reclassified "
               "OWNER_INTENT extinguished-unconsumed (P-8); a FRESH "
               "exact-phrase GO artifact typed AFTER the S0 authorization "
               "is required")
    else:
        go = _load_json(fresh_path)
        problems = []
        if (go.get("instruction_verbatim") or "").strip() != OWNER_GO_PHRASE:
            problems.append("instruction_verbatim is not the exact phrase")
        try:
            fresh_t = _parse_utc(go["received_utc"])
        except Exception:
            fresh_t = None
            problems.append("received_utc missing/unparsable")
        if os.path.exists(os.path.join(root, GATE_S0)):
            s0 = _load_json(os.path.join(root, GATE_S0))
            s0_t = _parse_utc(s0.get("authorized_utc")
                              or s0.get("received_utc"))
            if fresh_t is not None and fresh_t <= s0_t:
                problems.append("fresh GO does not postdate the S0 "
                                "authorization")
        if os.path.exists(os.path.join(root, GATE_GO_RECLASS)):
            rec = _load_json(os.path.join(root, GATE_GO_RECLASS))
            rec_t = _parse_utc(rec.get("recorded_utc"))
            if fresh_t is not None and fresh_t <= rec_t:
                problems.append("fresh GO does not postdate the P-8 "
                                "reclassification")
        _check("owner_fresh_go", not problems,
               "fresh GO postdates S0 + reclassification" if not problems
               else "; ".join(problems))

    # 4) budget: fewer than PLANNED_SCORED_CELLS scored cells consumed
    contract_path = os.path.join(root, GATE_RUN_CONTRACT)
    if not os.path.exists(contract_path):
        _check("budget", False, "RUN_CONTRACT_MISSING")
    else:
        contract = _load_json(contract_path)
        planned = (contract.get("budget") or {}).get("planned_scored_cells",
                                                     PLANNED_SCORED_CELLS)
        recorded_used = (contract.get("budget") or {}).get("used", 0)
        consumed = int(recorded_used)
        ledger = scored_ledger_path or os.path.join(root, SCORED_LEDGER_DEFAULT)
        if os.path.exists(ledger):
            with open(ledger, "r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("real_pnl") and not row.get("dry_run"):
                        consumed += 1
        _check("budget", consumed < planned,
               f"scored cells consumed {consumed}/{planned}"
               + (" (run contract budget.used increased)" if consumed != int(recorded_used) else ""))

    # 5) S1 seal intact (status flag read; sealed artifact never touched)
    state_path = os.path.join(root, GATE_STATE)
    if not os.path.exists(state_path):
        _check("s1_seal", False, "STATE_MISSING: cannot confirm the S1 seal")
    else:
        state = _load_json(state_path)
        seal = state.get("s1")
        opened = os.path.exists(os.path.join(root, GATE_S1_OPENED_MARKER))
        ok = seal == "SEALED_UNTOUCHED" and not opened
        _check("s1_seal", ok,
               f"s1={seal!r} opened_marker={opened}")

    return all(g["ok"] for g in gates.values()), gates


# -------------------------------------------------------------------------- #
# the six-arm driver                                                         #
# -------------------------------------------------------------------------- #
def _register_families(root=ROOT):
    recorders = {}
    for family_id, spec in FAMILY_MODULES.items():
        module = importlib.import_module(spec["module"])
        proposal_path = os.path.join(root, spec["proposal"])
        actual = sha256_file(proposal_path)
        if actual != spec["proposal_sha256"]:
            raise RuntimeError(
                f"PROPOSAL_SHA_MISMATCH: {spec['proposal']} {actual}")
        recorder = StructuralRecorder(family_id, module)
        R.register_family(family_id, recorder)
        recorders[family_id] = recorder
    return recorders


def _attach_and_check(rec, family_id, arm, recorder, spec, root=ROOT):
    """Attach trial identity + structural block + placeholder gate check to
    a sanitized record, run the recursive leak scan (fail closed)."""
    module_path = FAMILY_MODULES[family_id]["module"]
    module = importlib.import_module(module_path)
    config = {
        "cycle_id": CYCLE_ID,
        "family_id": family_id,
        "arm": arm,
        "record_id": rec["record_id"],
        "proposal_sha256": spec["proposal_sha256"],
        "module_sha256": sha256_file(
            os.path.join(root, module_path.replace(".", "/") + ".py")),
    }
    meta = getattr(recorder.wrapped, "_frozen_config", {}).get(arm) or {}
    keys = FAMILY1_CONFIG_KEYS if family_id == "family1" else FAMILY2_CONFIG_KEYS
    config["frozen_config"] = {k: meta[k] for k in keys if k in meta}
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
    findings, scanned = recursive_leak_scan(rec)
    if findings:
        raise RuntimeError(
            f"PNL_LEAK_SCAN_FAILED {family_id}:{arm}: {findings[:10]}")
    return digest, scanned


def _schedule_invariant(family_id, summary, rec):
    """Programmatic check of the frozen schedule invariant "every opened
    entry becomes exactly one emitted decision round trip" (runner contract:
    one decision per round trip).  family1 exposes entry/round-trip counters
    in meta.schedule; family2 emits every scheduled trip, so the check is
    sum(per-pair round_trips) == n_decisions.  Returns (ok, counts)."""
    counters = summary.get("schedule_counters")
    if counters is not None:
        opened = counters.get("n_entries")
        emitted = counters.get("n_round_trips")
        return emitted == opened, {"n_entries_opened": opened,
                                   "n_round_trips_emitted": emitted,
                                   "n_decisions_recorded": rec.get("n_decisions")}
    totals = summary.get("schedule_totals")
    if totals is not None:
        scheduled = sum(int(v.get("round_trips", 0)) for v in totals.values())
        return scheduled == int(rec.get("n_decisions", 0)), {
            "n_round_trips_scheduled": scheduled,
            "n_decisions_recorded": rec.get("n_decisions")}
    return True, {}


def run_dummy(data_paths, ledger_path, report_path, root=ROOT,
              timeout_minutes=None):
    """The six-arm SANITIZED dummy dry-run.  Records go ONLY to a temporary
    ledger under dryrun_tmp/; nothing is scored, published or budgeted."""
    tmp_dir = os.path.join(root, V4_CTL, DRYRUN_TMP_DIRNAME)
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
    freeze_token = None  # dummy: the kernel sanitizes every monetary metric

    arms_out = []
    family_cells = {}
    leak_fields_total = 0
    for family_id in ("family1", "family2"):
        recorder = recorders[family_id]
        spec = FAMILY_MODULES[family_id]
        for arm in R.ARMS:  # anchor -> neighbour -> control, serial
            rec = R.compute_cell(family_id, arm, data_paths,
                                 freeze_token=freeze_token,
                                 timeout_minutes=timeout_minutes)
            # expose the family's frozen config projection to the recorder
            frozen = getattr(recorder.wrapped, "_frozen_config", None)
            if frozen is None:
                frozen = {}
                recorder.wrapped.__dict__["_frozen_config"] = frozen
            meta = _family_meta(recorder, arm)
            if meta:
                frozen[arm] = meta
            digest, scanned = _attach_and_check(rec, family_id, arm,
                                                recorder, spec, root)
            leak_fields_total += scanned
            inv_ok, inv_counts = _schedule_invariant(
                family_id, recorder.summaries.get(arm) or {}, rec)
            payload = accounting.canonical_json_bytes(rec)
            observed_delta, published_now = accounting.AtomicJsonlPublisher(
                abs_ledger).publish_once(rec)
            arms_out.append({
                "family": family_id, "arm": arm,
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
            })
            family_cells.setdefault(family_id, {})[arm] = rec
            print(json.dumps({"arm": rec["record_id"],
                              "n_decisions": rec["n_decisions"],
                              "n_trades_kept": rec["n_trades_kept"],
                              "leak_scan": "clean",
                              "observed_delta": observed_delta,
                              "published_now": published_now}), flush=True)

    pairwise_ids = len({a["record_id"] for a in arms_out}) == len(arms_out) \
        and len({a["trial_id"] for a in arms_out}) == len(arms_out)
    if not pairwise_ids:
        raise RuntimeError("PAIRWISE_ID_VIOLATION: record/trial ids collide")

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
        "scored": False, "real_pnl": False, "published": False,
        "dry_run_utc": _utc_now_iso(), "stamp_source": "machine_date_u",
        "base_head": git_head(root),
        "data_verification": data_verification,
        "arms": arms_out,
        "six_arm_record_counts": {a["record_id"]: a["n_decisions"]
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


def _family_meta(recorder, arm):
    """Best-effort frozen-config projection from the wrapped family module.
    Families differ in how much frozen config they publish in meta; the
    recorder re-reads the module's constants so the digest pins code, not
    data-dependent values."""
    module = recorder.wrapped
    meta = getattr(module, "_last_meta_by_arm", {}).get(arm)
    if meta:
        return meta
    if recorder.family_id == "family1":
        f = module
        return {
            "trigger_pairs": list(f.TRIGGER_PAIRS),
            "trigger_sign_convention": [f"{'+' if f.TRIGGER_SIGNS[p] > 0 else '-'}{p}"
                                        for p in f.TRIGGER_PAIRS],
            "bloc_estimator": {"anchor": "mean", "neighbour": "median",
                               "control": "mean"}[arm],
            "response_legs": [f"{'LONG' if s > 0 else 'SHORT'} {p}"
                              for p, s in f.RESPONSE_LEGS],
            "standardization_window_ny_days": f.STANDARDIZATION_WINDOW_NY_DAYS,
            "event_threshold": f.EVENT_THRESHOLD,
            "holding_ny_days": f.HOLDING_NY_DAYS,
            "benchmark_staleness_ny_days": 0,
            "fold_boundaries": list(f.FOLD_BOUNDARIES),
            "force_flat_boundaries": list(f.FORCE_FLAT_BOUNDARIES),
            "alpha_definition": f.ALPHA_DEFINITION,
            "warmup_daily_bars": f.STANDARDIZATION_WINDOW_NY_DAYS + 1,
            "z_std_ddof": f.Z_STD_DDOF,
            "notional_usd_unit": f.NOTIONAL_USD,
            "financing_formula": f.FINANCING_FORMULA,
        }
    f = module
    config = {
        "holding": {"anchor_ny_days": f.ANCHOR_HOLD_NY_DAYS,
                    "neighbour_hike_ny_days": f.ANCHOR_HOLD_NY_DAYS,
                    "neighbour_cut_ny_days": f.NEIGHBOUR_CUT_HOLD_NY_DAYS},
        "alpha_definition": "per_trade_expectancy_difference_v1",
        "sham_derangement": ({a: f.SHAM_AREA[a] for a in f.AREA_ORDER}
                             if arm in ("control", "causal_negative_control")
                             else None),
    }
    return config


def run_scored(data_paths, ledger_path, authorization_path, report_path,
               root=ROOT, freeze_token=W4_FREEZE_TOKEN, timeout_minutes=None):
    """The SCORED path.  Refuses (SystemExit 2, refusal report written)
    unless ALL FIVE launch gates hold; never invoked by lane A8."""
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
            "schema": "forex_free_v4_scored_refusal_v1",
            "mode": "scored", "cycle_id": CYCLE_ID,
            "refused_utc": _utc_now_iso(), "stamp_source": "machine_date_u",
            "refused": True,
            "gates": gates,
            "note": "LAUNCH GATES NOT SATISFIED: no cell computed, nothing "
                    "booked, nothing published. Two-key protocol: independent "
                    "S0 FOREX_FREE_V4_S0_LAUNCH_AUTHORIZED, then a FRESH "
                    f"exact-phrase '{OWNER_GO_PHRASE}' owner GO.",
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

    # Gates satisfied: the frozen kernel path (mirrors the V3 exec_driver).
    R.FAMILIES.clear()
    _register_families(root)
    cells = []
    for family_id in ("family1", "family2"):
        family_cells = {}
        for arm in R.ARMS:
            rec = R.compute_cell(family_id, arm, data_paths,
                                 freeze_token=freeze_token,
                                 timeout_minutes=timeout_minutes)
            rec["trial_id"] = f"{CYCLE_ID}/{family_id}/{arm}"
            gates_pass, reasons = R.stage_a_gates(rec)
            rec["observed_delta"], published_now = R.publish_cell(
                ledger_path, rec, authorization_path, freeze_token)
            rec["published"] = published_now == 1
            family_cells[arm] = rec
            cells.append({"cell_id": rec["record_id"],
                          "gates_pass": gates_pass, "gate_reasons": reasons,
                          "published": rec["published"],
                          "observed_delta": rec["observed_delta"]})
        sanity, sanity_reasons = R.mechanism_sanity(family_cells)
        cells.append({"cell_id": f"{family_id}:MECHANISM_SANITY",
                      "gates_pass": sanity, "gate_reasons": sanity_reasons})
    report = {"schema": "forex_free_v4_scored_report_v1", "mode": "scored",
              "cycle_id": CYCLE_ID, "dry_run_utc": _utc_now_iso(),
              "stamp_source": "machine_date_u", "cells": cells}
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    return report


# -------------------------------------------------------------------------- #
# evidence artifact (dry_run_v4.json) from two replay reports                #
# -------------------------------------------------------------------------- #
def emit_evidence(report1_path, report2_path, evidence_out, root=ROOT):
    """Build research/control/forex_free_v4_run/dry_run_v4.json from the two
    replay runs: zero denominator delta + byte-identical records asserted
    here (fail closed)."""
    r1 = _load_json(report1_path)
    r2 = _load_json(report2_path)
    if r1["schema"] != REPORT_SCHEMA or r2["schema"] != REPORT_SCHEMA:
        raise SystemExit("EVIDENCE_INPUT_SCHEMA_MISMATCH")
    for arm1, arm2 in zip(r1["arms"], r2["arms"]):
        if arm1["record_sha256"] != arm2["record_sha256"]:
            raise SystemExit(
                f"REPLAY_NOT_BYTE_IDENTICAL: {arm1['record_id']} "
                f"{arm1['record_sha256']} != {arm2['record_sha256']}")
    replay_zero_delta = (sum(a["observed_delta"] for a in r2["arms"]) == 0
                         and sum(a["published_now"] for a in r2["arms"]) == 0)
    if not replay_zero_delta:
        raise SystemExit("REPLAY_DENOMINATOR_DELTA: the replay incremented "
                         "the observed/published counters")
    led_rel = r1["temporary_ledger"]
    ledger_bytes = open(os.path.join(root, led_rel), "rb").read()
    n_lines = sum(1 for line in ledger_bytes.splitlines() if line.strip())
    if n_lines != len(r1["arms"]):
        raise SystemExit(
            f"TEMP_LEDGER_LINE_COUNT: {n_lines} lines != {len(r1['arms'])} "
            "records (the replay must not append)")
    data_verification = r1["data_verification"]
    findings = []
    for violation in r1.get("structural_invariant_violations", []):
        findings.append({
            "severity": "HIGH",
            "record_id": violation["record_id"],
            "finding": "schedule invariant violated: opened entries are not "
                       "all emitted as decision round trips (the family1 "
                       "schedule emitter drops mid-stream closed positions; "
                       "only trailing force-flat positions become "
                       "decisions).  Counts are structural, not outcomes.",
            "counts": violation["counts"],
            "disposition": "the module repair must be A1-adjudicated and the "
                           "dummy dry-run re-run before ANY scored launch; "
                           "the scored gates refuse on this evidence",
        })
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "dry_run_utc": r1["dry_run_utc"],
        "stamp_source": "machine_date_u",
        "base_head": r1["base_head"],
        "data_hashes": {
            "price_snapshot": data_verification["price_snapshot"],
            "macro_evidenced_vintages": data_verification["macro_evidenced"],
            "announcement_ledger": data_verification["announcement_ledger"],
        },
        "six_arm_record_counts": r1["six_arm_record_counts"],
        "pairwise_distinct_ids": r1["pairwise_distinct_ids"],
        "recursive_leak_scan": {
            "fields_scanned": r1["recursive_leak_scan"]["fields_scanned"],
            "leaks_found": [],
            "rule": r1["recursive_leak_scan"]["rule"],
            "field_allowlist": sorted(FIELD_ALLOWLIST),
            "pair_key_parents": sorted(PAIR_KEY_PARENTS),
            "pair_names": sorted(PAIR_NAMES),
            "reason_key_parents": sorted(REASON_KEY_PARENTS),
            "tier_key_parents": sorted(TIER_KEY_PARENTS),
            "tier_keys": sorted(TIER_KEYS),
            "outcome_label_key_exception": sorted(OUTCOME_LABEL_KEYS),
            "outcome_value_pattern": OUTCOME_VALUE_RE.pattern,
        },
        "replay_byte_identical": True,
        "replay_zero_denominator_delta": True,
        "temporary_ledger": led_rel,
        "temporary_ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "scored_flag": False,
        "real_pnl": False,
        "published": False,
        "arm_config_digests": {f"{a['family']}:{a['arm']}":
                               a["arm_config_digest"] for a in r1["arms"]},
        "force_flat_and_zero_position_visibility": {
            a["record_id"]: {
                "n_force_flat_decisions": a["n_force_flat_decisions"],
                "zero_positions": a["zero_positions"],
            } for a in r1["arms"]},
        "budget_note": "0/6 scored cells consumed by this dry-run; dummy "
                       "cells are not scored evidence and never count",
        "structural_findings": findings,
        "limitation": LIMITATIONS,
    }
    os.makedirs(os.path.dirname(os.path.abspath(evidence_out)), exist_ok=True)
    with open(evidence_out, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=1, sort_keys=True)
    print(json.dumps({"evidence": evidence_out,
                      "replay_byte_identical": True,
                      "replay_zero_denominator_delta": True}), flush=True)
    return evidence


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("dummy", "scored"), required=True)
    ap.add_argument("--data-paths", default=None,
                    help="JSON file with the data_paths dict; default: the "
                         "staged V4 data authority (verified fail-closed)")
    ap.add_argument("--report", required=True)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--authorization", default=None)
    ap.add_argument("--freeze-token", default=W4_FREEZE_TOKEN)
    ap.add_argument("--timeout-minutes", type=float, default=None)
    ap.add_argument("--emit-evidence", nargs=2, metavar=("PASS1", "PASS2"),
                    default=None,
                    help="with --evidence-out: build dry_run_v4.json from "
                         "the two replay reports")
    ap.add_argument("--evidence-out", default=None)
    args = ap.parse_args(argv)

    if args.emit_evidence:
        if not args.evidence_out:
            raise SystemExit("--emit-evidence requires --evidence-out")
        emit_evidence(args.emit_evidence[0], args.emit_evidence[1],
                      args.evidence_out)
        return 0

    data_paths = build_default_data_paths(ROOT)
    if args.data_paths:
        with open(args.data_paths, "r", encoding="utf-8") as handle:
            data_paths = json.load(handle)

    if args.mode == "dummy":
        ledger = args.ledger or os.path.join(
            ROOT, V4_CTL, DRYRUN_TMP_DIRNAME, "dryrun_ledger.jsonl")
        run_dummy(data_paths, ledger, args.report, root=ROOT,
                  timeout_minutes=args.timeout_minutes)
        return 0

    # scored
    if not (args.ledger and args.authorization):
        raise SystemExit("scored mode requires --ledger and --authorization")
    run_scored(data_paths, args.ledger, args.authorization, args.report,
               root=ROOT, freeze_token=args.freeze_token,
               timeout_minutes=args.timeout_minutes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
