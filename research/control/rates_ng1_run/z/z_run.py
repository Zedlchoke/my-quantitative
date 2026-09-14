"""RATES-NG1 Z-phase SANITIZED DRY-RUN driver (prelaunch pipeline
rehearsal on the REAL frozen substrate).

Cycle RATES-NG1, task rates-ng1-z-dryrun (dispatch packet invocation
lead-bg-rates-z).  Runs the EXACT 3 frozen cells (arm_config_digests
33b78baa / 54ef5def / cfdad940, digest-verified against the committed S
selection freeze) plus the FULL control battery (level-vs-shape
decomposition control = declared executioner, clock-only shadow, k=5
misaligned placebo, D1 falsification rule) on the REAL frozen substrate
-- plane-verified curve + ETP bytes, the P2 bookable-instant grid, the
frozen tier-2.0 cost contract -- end-to-end through the I-phase runners
(``research/assets/rates_ng1/runners/``, READ-ONLY: defects are
reported, never fixed here).

SANITIZATION LAW (the Z contract): committed artifacts record
STRUCTURAL facts only -- decision counts, fill/mark/cost-event row
counts, control-EXECUTABLE PASS/FAIL, fold-partition counts, digest
chains, provenance.  NO PnL, NO expectancy, NO per-trade or aggregate
outcome number is emitted anywhere.  Outcome internals (the kernel
book views, the per-decision after-cost edge series, the battery
verdicts) ARE computed in memory -- this is a full pipeline rehearsal,
including the E-phase signed arithmetic surface
``round_trip_leg_signed_pnl`` -- but they leave the process ONLY as
sha256 digests (one-way determinism pins for the scored run), recorded
under explicit ``*_sha256`` keys.

Fail-closed semantics:
- any committed-artifact digest drift (freeze pins vs measured files,
  arm digest vs the freeze, plane verify-on-read vs the substrate
  manifest) => integrity FAIL;
- any plumbing failure on real data (blocked/missing substrate,
  runner-law refusal) => ``BLOCKED_PRELAUNCH_CANDIDATE`` reported
  HONESTLY in the stage ledger -- never repaired, never retried with
  substituted data;
- any sanitizer leak in the assembled payload => the report writer
  REFUSES to write (no partial/contaminated emission can be committed).

The payload is a pure function of (substrate bytes, committed
artifacts, runner code): no wall-clock values, so the committed report
bytes are exactly reproducible byte-for-byte.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from typing import Any, Mapping

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.rates_ng1 import plane_adapter as pa  # noqa: E402
from research.assets.rates_ng1.runners import rules as rl  # noqa: E402
from research.assets.rates_ng1.runners.battery import (  # noqa: E402
    KILLER_ROLES,
    battery_verdict,
)
from research.assets.rates_ng1.runners.runner import (  # noqa: E402
    FOLD_WINDOWS,
    RunnerLawError,
    assemble_cell_configs,
    book_round_trips,
    clock_only_state,
    curve_coordinates,
    fold_bounds,
    level_control_state,
    load_representation,
    misaligned_state,
    positions_from_states,
    round_trip_leg_signed_pnl,
    run_arm,
)

SCHEMA = "rates_ng1_run/z_dry_run@1"
REPORT_SCHEMA = "rates_ng1_run/z_report@1"

CYCLE_ID = "RATES-NG1"
TASK_ID = "rates-ng1-z-dryrun"
ROLE = "quant-implementer"
LANE = "z"

BASE_SHA = "5672d9ed980feccc500fd75c565c5cd7c789d1f0"
BRANCH = "orca/rates-ng1-integration"
WORKTREE = ("/Users/hoangminhlong/my-quantitative"
            "/.worktrees/rates-ng1/integration")

#: The packet's exact test command (recorded verbatim in the report).
TEST_COMMAND = (
    "cd /Users/hoangminhlong/my-quantitative"
    "/.worktrees/rates-ng1/integration && "
    "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
    "-m pytest tests/test_rates_ng1_z.py -q")

Z_DIR = os.path.join(REPO_ROOT, "research", "control", "rates_ng1_run",
                     "z")
REPORT_PATH = os.path.join(Z_DIR, "z_report.json")
FREEZE_PATH = os.path.join(REPO_ROOT, "research", "control",
                           "rates_ng1_run", "s", "selection_freeze.json")
CENSUS_PATH = os.path.join(REPO_ROOT, "research", "control",
                           "rates_ng1_run", "p2_grid_census.json")
CONTRACT_PATH = os.path.join(REPO_ROOT, "research", "control",
                             "rates_ng1_run", "p1_cost_contract.json")
MANIFEST_PATH = os.path.join(REPO_ROOT, "research", "control",
                             "rates_ng1_run", "substrate_manifest.json")

#: The dispatch packet's frozen arm-digest prefixes (integrity law:
#: the assembled cells must be EXACTLY these 3 cells).
PACKET_DIGEST_PREFIXES = {
    "RATESNG1-A5-P1-ARM-NEUTRAL": "33b78baa",
    "RATESNG1-A5-P1-ARM-CONSERVATIVE": "54ef5def",
    "RATESNG1-A5-P1-ARM-AGGRESSIVE": "cfdad940",
}

CONTROL_ARM_SUFFIXES = {
    "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL": "LEVEL-CTL",
    "CLOCK_ONLY_SHADOW": "CLOCK-CTL",
    "PLACEBO": "PLACEBO-CTL",
}

#: Z-extended forbidden KEY patterns (additive to the I-phase scanner
#: in rules.EMISSION_FORBIDDEN_PATTERNS).  Any key match at any depth
#: is a sanitizer LEAK -- the report writer refuses to emit.
Z_EXTRA_FORBIDDEN_PATTERNS = (
    "mean", "kill", "margin", "gross", "equity", "sortino", "calmar",
    "hit_?rate", "payoff", "^delta", "delta_", "money_?made",
    "^edge$", "_edge$", "^edge_",
)

VERDICTS = ("PASS", "FAIL", "BLOCKED_PRELAUNCH_CANDIDATE")

PLUMBING_EXCEPTIONS = (
    pa.PlaneDataBlocked,
    pa.PlaneConsumptionRefused,
    RunnerLawError,
    OSError,
    KeyError,
    ValueError,
)


class ZSanitizationError(Exception):
    """A sanitizer leak: the emission is REFUSED (fail-closed)."""


# ------------------------------------------------------------------ #
# Sanitizers (the Z emission law, mechanically enforced).              #
# ------------------------------------------------------------------ #

def _norm_key(k: str) -> str:
    return re.sub(r"[-_\s]+", "_", str(k)).strip("_").lower()


def sanitize_payload(payload: Any) -> dict:
    """The Z sanitization scan over an assembled payload:

    1. KEY law -- the I-phase forbidden outcome-field patterns
       (rules.scan_emission_for_outcome_tokens) PLUS the Z-extended
       patterns, at every depth (dicts + lists);
    2. VALUE law -- NO float value anywhere (counts are ints, digests
       are hex strings, facts are strings/bools; an outcome number can
       only enter as a float, so ``no floats`` is a complete guard);
    3. DIGEST law -- every ``*_sha256`` key carries a 64-hex digest.

    Returns {clean, leaks, value_law_leaks, digest_law_leaks, patterns}.
    """
    patterns = [re.compile(p, re.IGNORECASE)
                for p in rl.EMISSION_FORBIDDEN_PATTERNS]
    z_patterns = [re.compile(p, re.IGNORECASE)
                  for p in Z_EXTRA_FORBIDDEN_PATTERNS]
    hex_re = re.compile(r"[0-9a-f]{64}")
    leaks: list[dict] = []
    value_leaks: list[dict] = []
    digest_leaks: list[dict] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                nk = _norm_key(k)
                for pat in patterns:
                    if pat.search(nk):
                        leaks.append({"path": f"{path}.{k}",
                                      "pattern": pat.pattern,
                                      "scanner": "i_phase"})
                        break
                else:
                    for pat in z_patterns:
                        if pat.search(nk):
                            leaks.append({"path": f"{path}.{k}",
                                          "pattern": pat.pattern,
                                          "scanner": "z_extended"})
                            break
                if nk.endswith("sha256"):
                    if isinstance(v, dict):
                        for dk, dv in v.items():
                            if not (isinstance(dv, str)
                                    and hex_re.fullmatch(dv)):
                                digest_leaks.append(
                                    {"path": f"{path}.{k}.{dk}",
                                     "law": "64-hex digest"})
                    elif not (isinstance(v, str)
                              and hex_re.fullmatch(v)):
                        digest_leaks.append({"path": f"{path}.{k}",
                                             "law": "64-hex digest"})
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        else:
            if isinstance(node, float) and not isinstance(node, bool):
                value_leaks.append({"path": path,
                                    "law": "no-float value law"})

    walk(payload, "$")
    return {
        "schema": SCHEMA + ":sanitization_scan",
        "patterns": list(rl.EMISSION_FORBIDDEN_PATTERNS),
        "extended_patterns": list(Z_EXTRA_FORBIDDEN_PATTERNS),
        "leaks": leaks,
        "value_law_leaks": value_leaks,
        "digest_law_leaks": digest_leaks,
        "clean": not (leaks or value_leaks or digest_leaks),
    }


def build_report_bytes(payload: Mapping[str, Any]) -> bytes:
    """Deterministic report bytes (sort_keys, indent 1, trailing NL)."""
    return (json.dumps(payload, indent=1, sort_keys=True,
                       ensure_ascii=True) + "\n").encode("utf-8")


def emit_report(payload: Mapping[str, Any],
                path: str = REPORT_PATH) -> dict:
    """Fail-closed emission: refuse ANY payload the sanitizer flags;
    otherwise write deterministic bytes and return the artifact
    digest."""
    scan = sanitize_payload(payload)
    if not scan["clean"]:
        raise ZSanitizationError(
            f"report emission REFUSED: sanitizer leaks "
            f"{scan['leaks'][:5]} value_law {scan['value_law_leaks'][:5]} "
            f"digest_law {scan['digest_law_leaks'][:5]}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = build_report_bytes(payload)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)
    return {
        "wrote": path,
        "bytes": len(data),
        "artifact_sha256": hashlib.sha256(data).hexdigest(),
        "sanitization": "CLEAN_REFUSED_NOTHING",
    }


# ------------------------------------------------------------------ #
# Small structural helpers.                                            #
# ------------------------------------------------------------------ #

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_digest(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def _digest_of(obj: Any) -> str:
    return canonical_digest(obj)


def _counts_view(meta: Mapping[str, Any]) -> dict:
    return {k: meta[k] for k in
            ("decisions_total", "states_defined", "states_undefined",
             "state_events_nonzero", "round_trips",
             "decision_ids_pairwise_distinct")}


def _fills_view(books) -> dict:
    struct = books.structural_view()
    return {
        "ledgers": struct,
        "fills_total": sum(v["fills"] for v in struct.values()),
        "marks_total": sum(v["marks"] for v in struct.values()),
        "cost_events_total": sum(v["cost_events"]
                                 for v in struct.values()),
        "all_ledgers_dual_book_equality_ok": all(
            v["dual_book_equality_ok"] for v in struct.values()),
        "kernel_ledger_sha256": {name: led.sha256()
                                 for name, led in
                                 sorted(books.ledgers.items())},
    }


def _fold_partition_view(meta: Mapping[str, Any]) -> dict:
    return {
        "fold_windows": [list(w) for w in fold_bounds()],
        "folds_decisions": dict(meta["folds_decisions"]),
        "folds_state_events": dict(meta["folds_state_events"]),
        "exit_reasons": dict(meta["exit_reasons"]),
        "fold_force_flat_same_day": meta["fold_force_flat_same_day"],
    }


def _fold_partition_law() -> dict:
    """Structural equal-thirds law facts (day counts, no curve
    content).  The freeze's '2804 days' is the EXCLUSIVE day-difference
    convention (last minus first); inclusive spans sum to 2805."""
    lo = dt.date.fromisoformat(FOLD_WINDOWS[0][0])
    hi = dt.date.fromisoformat(FOLD_WINDOWS[-1][1])
    spans = [(dt.date.fromisoformat(w[1]) - dt.date.fromisoformat(w[0])
              ).days + 1 for w in FOLD_WINDOWS]
    contiguous = all(
        dt.date.fromisoformat(FOLD_WINDOWS[i][1])
        + dt.timedelta(days=1)
        == dt.date.fromisoformat(FOLD_WINDOWS[i + 1][0])
        for i in range(len(FOLD_WINDOWS) - 1))
    return {
        "fold_windows": [list(w) for w in FOLD_WINDOWS],
        "window_day_span_exclusive": (hi - lo).days,
        "window_days_inclusive": (hi - lo).days + 1,
        "fold_day_spans_inclusive": spans,
        "folds_contiguous": contiguous,
        "window_matches_freeze_law": (hi - lo).days == 2804,
    }


# ------------------------------------------------------------------ #
# Per-decision after-cost edge series (in-memory ONLY; emitted solely  #
# as a sha256 digest).  The mirror-long leg arithmetic is tied back to  #
# the kernel's own book views by a reconciliation gate (structural      #
# boolean only).                                                        #
# ------------------------------------------------------------------ #

def _leg_mirror_long_pnl(leg_info: Mapping[str, Any],
                         er_daily: Mapping[str, float],
                         leg: str) -> float:
    return ((leg_info["exit_price"] - leg_info["entry_price"])
            * leg_info["qty"]
            - leg_info["spread_cost_entry"]
            - leg_info["spread_cost_exit"]
            - leg_info["drag_notional"] * float(er_daily[leg])
            * leg_info["drag_days"])


def round_trip_edges(instants: list[Mapping[str, Any]],
                     round_trips: list[dict],
                     books,
                     er_daily: Mapping[str, float]) -> list[float | None]:
    """Per-decision after-cost edge series: each round trip's BOTH-leg
    signed after-cost figure (E-phase signed surface) attributed to its
    ENTRY instant.  In-memory only -- never emitted numerically."""
    pos_of_idx = {int(inst["session_index"]): i
                  for i, inst in enumerate(instants)}
    edges: list[float | None] = [None] * len(instants)
    for rt in round_trips:
        total = 0.0
        for leg, info in rt["legs"].items():
            mirror = _leg_mirror_long_pnl(info, er_daily, leg)
            total += round_trip_leg_signed_pnl(info["orientation"], mirror)
        edges[pos_of_idx[int(rt["entry_session_index"])]] = total
    return edges


def signed_surface_reconciled(round_trips: list[dict],
                              books,
                              er_daily: Mapping[str, float]) -> bool:
    """Tie the per-leg mirror arithmetic to the kernel ledger's OWN
    recorded ROWS (never a re-derivation): per ledger, the summed
    mirror-long figures must equal the ledger fills' cash flow
    (SELL proceeds minus BUY cost) minus the ledger's own spread costs
    and drag amounts.  Every round trip closes flat, so the ledger's
    open-position equity view is 0 by construction and is NOT the
    realized surface.  Structural boolean only -- no amount is
    emitted."""
    sums: dict[str, float] = {}
    for rt in round_trips:
        for leg, info in rt["legs"].items():
            name = f"{rt['arm_id']}|{leg}|{info['orientation']}"
            sums[name] = sums.get(name, 0.0) + _leg_mirror_long_pnl(
                info, er_daily, leg)
    if set(sums) != set(books.ledgers):
        return False
    for name, led in books.ledgers.items():
        cash = 0.0
        for f in led.fills:
            sign = -1.0 if f["side"] == "BUY" else 1.0
            cash += sign * f["price"] * f["qty"]
        spreads = sum((f["spread_cost"] or 0.0) for f in led.fills)
        drag = sum(e["amount"] for e in led.cost_events)
        expected = cash - spreads - drag
        if abs(sums[name] - expected) > 1e-6 * max(1.0, abs(expected)):
            return False
    return True


def _outcome_internals(round_trips: list[dict],
                       edges: list[float | None]) -> dict:
    """Outcome internals compressed to one-way determinism pins."""
    structure = {
        "round_trips": [
            {"rt_id": rt["rt_id"],
             "entry_session": rt["entry_session"],
             "exit_session": rt["exit_session"],
             "exit_reason": rt["exit_reason"],
             "direction": rt["direction"],
             "legs": {leg: {
                 "orientation": info["orientation"],
                 "qty": info["qty"],
                 "entry_price": info["entry_price"],
                 "exit_price": info["exit_price"],
                 "spread_cost_entry": info["spread_cost_entry"],
                 "spread_cost_exit": info["spread_cost_exit"],
                 "drag_notional": info["drag_notional"],
                 "signed_leg_figure": _cached_signed(info),
             } for leg, info in sorted(rt["legs"].items())}}
            for rt in round_trips],
        "per_decision_series": edges,
    }
    return {
        "suppression_law": (
            "outcome internals hashed/suppressed only: one-way sha256 "
            "determinism pins; no amount, ratio or series value is "
            "emitted"),
        "round_trip_outcome_sha256": _digest_of(structure),
        "per_decision_edges_sha256": _digest_of(edges),
    }


def _cached_signed(info: Mapping[str, Any]) -> float:
    """Signed per-leg figure (mirror arithmetic pre-sign); the caller
    hashes it, never emits it."""
    return (info["exit_price"] - info["entry_price"]) * info["qty"]


# ------------------------------------------------------------------ #
# One cell: arm run + the three battery control runs + comparators.    #
# ------------------------------------------------------------------ #

def _booked_run(arm_id: str,
                states: list[float | None],
                instants: list[Mapping[str, Any]],
                leg_closes_by_date: Mapping[str, Mapping[str, float]],
                tiers_bps: Mapping[str, float],
                er_daily: Mapping[str, float]) -> dict:
    decisions, round_trips, meta = positions_from_states(
        states, instants, arm_id=arm_id)
    books = book_round_trips(arm_id, round_trips, leg_closes_by_date,
                             tiers_bps, er_daily)
    edges = round_trip_edges(instants, round_trips, books, er_daily)
    return {
        "decisions": decisions,
        "round_trips": round_trips,
        "meta": meta,
        "books": books,
        "edges": edges,
        "reconciled": signed_surface_reconciled(round_trips, books,
                                                er_daily),
    }


def run_cell(cell: Mapping[str, Any],
             rep: Mapping[str, Any],
             cost: Mapping[str, Any]) -> dict:
    """One frozen cell end-to-end on the real substrate: arm run +
    level / clock / placebo control runs + in-memory battery verdicts
    (suppressed to digests) + the sanitized structural manifest."""
    instants = rep["instants"]
    tiers = {leg: cost["per_etp"][leg]["stress_tier_bps"]
             for leg in ("SHY", "TLT")}
    er_daily = {leg: cost["per_etp"][leg]["expense_drag"][
        "drag_per_day_fraction"] for leg in ("SHY", "TLT")}
    common = dict(instants=instants,
                  leg_closes_by_date=rep["leg_closes"],
                  tiers_bps=tiers,
                  er_daily=er_daily)

    arm = run_arm(arm_id=cell["arm_id"],
                  arm_role=cell["role"],
                  config=cell["config"],
                  curve_by_date=rep["curve_by_date"],
                  **common)
    arm_run = {
        "decisions": arm["decision_series"],
        "round_trips": arm["round_trips"],
        "meta": arm["meta"],
        "books": arm["books"],
        "state_series": arm["state_series"],
    }
    arm_run["edges"] = round_trip_edges(instants, arm["round_trips"],
                                        arm["books"], er_daily)
    arm_run["reconciled"] = signed_surface_reconciled(
        arm["round_trips"], arm["books"], er_daily)

    level_series = curve_coordinates(rep["curve_by_date"],
                                     instants)["level"]
    control_states = {
        "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL":
            level_control_state(level_series),
        "CLOCK_ONLY_SHADOW": clock_only_state(instants),
        "PLACEBO": misaligned_state(arm["state_series"]),
    }

    control_runs: dict[str, dict] = {}
    for role, states in control_states.items():
        control_runs[role] = _booked_run(
            f"{cell['arm_id']}|{CONTROL_ARM_SUFFIXES[role]}",
            states, **common)

    anchor_edges = arm_run["edges"]
    verdict = battery_verdict(
        anchor_edges,
        {role: control_runs[role]["edges"] for role in KILLER_ROLES})

    controls_out: dict[str, dict] = {}
    for row in verdict["comparisons"]:
        role = row["control_role"]
        run = control_runs[role]
        executable = (int(row["n_pairs_used"]) >= 1
                      and run["reconciled"]
                      and _fills_view(run["books"])[
                          "all_ledgers_dual_book_equality_ok"])
        controls_out[role] = {
            "status": "PASS" if executable else "FAIL",
            "executable": bool(executable),
            "n_instants": row["n_instants"],
            "n_pairs_used": row["n_pairs_used"],
            "dropped_undefined_anchor": row["dropped_undefined_anchor"],
            "dropped_undefined_control": row["dropped_undefined_control"],
            "control_state_counts": _counts_view(run["meta"]),
            "control_fills_total": _fills_view(run["books"])[
                "fills_total"],
            "control_edges_sha256": _digest_of(run["edges"]),
            "suppressed_fields": ("anchor/control comparator figures "
                                  "and verdict: hashed under "
                                  "verdict_internals_sha256"),
        }

    fills = _fills_view(arm["books"])
    manifest = {
        "cell_id": cell["cell_id"],
        "arm_id": cell["arm_id"],
        "role": cell["role"],
        "arm_config_digest": cell["arm_config_digest"],
        "digest_prefix": cell["arm_config_digest"][:8],
        "packet_digest_prefix_match":
            cell["arm_config_digest"][:8]
            == PACKET_DIGEST_PREFIXES[cell["arm_id"]],
        "cost_treatment": {
            "contract": "research/control/rates_ng1_run/"
                        "p1_cost_contract.json",
            "cost_ladder_tier_label": "tier_2_0_primary",
            "cost_frequency_label": "once_per_fill",
            "both_legs_charged_label": "true",
            "legs_tier_pinned": {leg: True for leg in sorted(tiers)},
        },
        "state_counts": _counts_view(arm["meta"]),
        "fold_partition": _fold_partition_view(arm["meta"]),
        "fills": fills,
        "signed_surface_reconciliation_ok": bool(arm_run["reconciled"]),
        "outcome_internals": _outcome_internals(arm["round_trips"],
                                                anchor_edges),
        "battery": {
            "anchor_arm": cell["arm_id"],
            "roles": list(KILLER_ROLES),
            "declared_executioner": "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL",
            "k_misalign_sessions": int(verdict["k_misalign_sessions"]),
            "falsification_rule": (
                "selection_freeze.json#"
                "section_6_control_battery_binding.falsification_rule "
                "(declared at D1, outcome-blind, sha-pinned)"),
            "controls": controls_out,
            "battery_executed": all(
                c["status"] == "PASS" for c in controls_out.values()),
            "verdict_internals_sha256": _digest_of(verdict),
        },
        "end_to_end_ok": bool(
            arm_run["reconciled"]
            and fills["all_ledgers_dual_book_equality_ok"]),
    }
    return manifest


# ------------------------------------------------------------------ #
# The driver.                                                          #
# ------------------------------------------------------------------ #

def _stage(stage: str, fn, stages: list) -> Any:
    """Run one pipeline stage, recording PASS / FAIL / BLOCKED
    honestly; plumbing failures become BLOCKED (never repaired)."""
    try:
        result = fn()
        stages.append({"stage": stage, "status": "PASS",
                       "detail": "ok"})
        return result
    except PLUMBING_EXCEPTIONS as exc:
        stages.append({"stage": stage, "status": "BLOCKED",
                       "detail": f"{type(exc).__name__}: {exc}"})
        raise ZBlockedStage(stage, type(exc).__name__, str(exc)) from exc


class ZBlockedStage(Exception):
    def __init__(self, stage: str, exc_type: str, detail: str):
        super().__init__(f"stage {stage} blocked: {exc_type}: {detail}")
        self.stage = stage
        self.exc_type = exc_type
        self.detail = detail


def _fail_stage(stage: str, detail: str, stages: list) -> None:
    stages.append({"stage": stage, "status": "FAIL", "detail": detail})


def run_z_dry_run(plane_kwargs: Mapping[str, Any] | None = None
                  ) -> dict:
    """Full sanitized dry-run.  Returns the report payload (structural
    only, sanitizer-clean or carrying the honest failure state)."""
    stages: list[dict] = []
    blocked: dict | None = None
    integrity_fails: list[str] = []
    payload: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "mode": "Z_SANITIZED_DRY_RUN_REAL_SUBSTRATE",
        "base_sha": BASE_SHA,
        "branch": BRANCH,
        "worktree": WORKTREE,
        "scope_law": (
            "Z phase: end-to-end prelaunch pipeline rehearsal of the 3 "
            "frozen cells + the full control battery on the REAL "
            "frozen substrate through the I-phase runners; committed "
            "artifacts carry STRUCTURAL facts only (decision counts, "
            "fill counts, control-executable PASS/FAIL, fold "
            "partitions, digest chains, provenance); outcome internals "
            "are hashed/suppressed only; S1 SEALED_UNTOUCHED; defects "
            "in the I-phase machinery are REPORTED, never fixed here"),
        "sanitization_law": (
            "NO PnL, NO expectancy, NO per-trade or aggregate outcome "
            "number anywhere committed; float-value law: zero floats; "
            "key law: I-phase patterns + Z-extended patterns; digest "
            "law: *_sha256 keys carry 64-hex one-way pins"),
        "s1": "SEALED_UNTOUCHED",
    }

    freeze: dict | None = None
    cells: list[dict] = []
    rep: dict | None = None
    cost: dict | None = None
    cell_manifests: list[dict] = []

    def s_freeze():
        nonlocal freeze
        freeze = json.load(open(FREEZE_PATH, "r", encoding="utf-8"))
        return freeze

    def s_cells():
        nonlocal cells
        cells = assemble_cell_configs(freeze)
        for cell in cells:
            if cell["arm_config_digest"][:8] != \
                    PACKET_DIGEST_PREFIXES[cell["arm_id"]]:
                integrity_fails.append(
                    f"packet digest prefix drift: {cell['arm_id']}")
        return cells

    def s_pins():
        nonlocal cost
        pins = freeze["citation_pins"]
        chain = {"selection_freeze_sha256": _sha256_file(FREEZE_PATH)}
        for label, path, pin_key in (
                ("p2_grid_census", CENSUS_PATH,
                 "research/control/rates_ng1_run/p2_grid_census.json"),
                ("p1_cost_contract", CONTRACT_PATH,
                 "research/control/rates_ng1_run/"
                 "p1_cost_contract.json"),
                ("substrate_manifest", MANIFEST_PATH,
                 "research/control/rates_ng1_run/"
                 "substrate_manifest.json")):
            measured = _sha256_file(path)
            pinned = pins[pin_key]
            chain[f"{label}_sha256"] = measured
            chain[f"{label}_pin_match"] = measured == pinned
            if measured != pinned:
                integrity_fails.append(
                    f"{label} drift: measured {measured} != freeze pin "
                    f"{pinned}")
        # the cost contract is ALSO pinned inside the freeze body
        contract = json.load(open(CONTRACT_PATH, "r", encoding="utf-8"))
        body_pin = freeze["section_4_cost_contract_binding"][
            "contract"]["sha256"]
        chain["contract_body_pin_match"] = (
            chain["p1_cost_contract_sha256"] == body_pin)
        if chain["p1_cost_contract_sha256"] != body_pin:
            integrity_fails.append("cost contract body-pin drift")
        # census counts vs freeze feasibility floors
        census = json.load(open(CENSUS_PATH, "r", encoding="utf-8"))
        feas = freeze["section_1_selected_family"][
            "feasibility_evidence"]
        chain["freeze_cited_bookable_instants"] = feas[
            "bookable_instants"]
        chain["freeze_cited_grid_sessions"] = feas["grid_sessions"]
        chain["census_bookable_instants"] = len(
            census["census"]["bookable_instants"])
        chain["census_grid_sessions"] = len(census["census"]["grid_dates"])
        chain["census_counts_match_freeze"] = (
            chain["census_bookable_instants"]
            == feas["bookable_instants"]
            and chain["census_grid_sessions"] == feas["grid_sessions"])
        if not chain["census_counts_match_freeze"]:
            integrity_fails.append("census counts vs freeze drift")
        cost = contract
        payload["digest_chain"] = chain
        return chain

    def s_plane():
        plane = pa.RatesNG1Plane(**dict(plane_kwargs or {}))
        census = json.load(open(CENSUS_PATH, "r", encoding="utf-8"))
        years = sorted({int(d[:4])
                        for d in census["census"]["grid_dates"]})
        entries = [f"treasury_curve/par_yields_{y}.csv" for y in years]
        entries += ["etp_eod/SHY.US.json", "etp_eod/TLT.US.json"]
        records = []
        for entry in entries:
            res = plane.consume_via_plane(entry)
            records.append({
                "entry": entry,
                "series": res["series"],
                "authority": res["authority"],
                "sha256_pinned": res["sha256_pinned"],
                "sha256_measured": res["sha256_measured"],
                "bytes": int(res["bytes"] or 0),
                "digest_verified": (res["sha256_pinned"]
                                    == res["sha256_measured"]),
            })
        all_ok = all(r["digest_verified"] for r in records)
        payload["plane"] = {
            "adapter": "research/assets/rates_ng1/plane_adapter.py",
            "verify_on_read": "every consumption re-hashes the raw "
                              "bytes against the substrate manifest pin",
            "entries_consumed": len(records),
            "all_digest_verified": all_ok,
            "entries": records,
        }
        if not all_ok:
            integrity_fails.append("plane entry digest drift")
        return plane

    def s_repr():
        nonlocal rep
        plane = pa.RatesNG1Plane(**dict(plane_kwargs or {}))
        census = json.load(open(CENSUS_PATH, "r", encoding="utf-8"))
        rep = load_representation(plane, census)
        payload["representation"] = {
            "loader": "runners.runner.load_representation "
                      "(I-phase machinery, unmodified)",
            "grid_dates_len": len(rep["grid_dates"]),
            "bookable_instants_len": len(rep["instants"]),
            "curve_dates_loaded": len(rep["curve_by_date"]),
            "leg_close_rows": {leg: len(rep["leg_closes"][leg])
                               for leg in sorted(rep["leg_closes"])},
        }
        return rep

    def s_cells_run():
        for cell in cells:
            cell_manifests.append(run_cell(cell, rep, cost))
        return cell_manifests

    try:
        _stage("freeze_load", s_freeze, stages)
        _stage("cell_config_assembly", s_cells, stages)
        _stage("freeze_artifact_pins", s_pins, stages)
        _stage("plane_provenance", s_plane, stages)
        _stage("representation_load", s_repr, stages)
        _stage("cell_runs_battery", s_cells_run, stages)
    except ZBlockedStage as exc:
        blocked = {"stage": exc.stage, "exc_type": exc.exc_type,
                   "detail": exc.detail,
                   "disposition": "reported honestly; never repaired, "
                                  "never re-run with substituted data"}

    # -- assemble the sanitized aggregate ----------------------------- #
    payload["identity"] = {
        "cell_count": len(cells),
        "booked_cells_expected": 3,
        "arm_config_digests": {c["arm_id"]: c["arm_config_digest"]
                               for c in cells},
        "digests_pairwise_distinct":
            len({c["arm_config_digest"] for c in cells}) == len(cells),
        "packet_digest_prefixes_match": all(
            c["arm_config_digest"][:8]
            == PACKET_DIGEST_PREFIXES[c["arm_id"]] for c in cells)
        if cells else False,
        "fold_partition_law": _fold_partition_law(),
    }
    payload["cells"] = cell_manifests
    payload["battery_law"] = {
        "roles": list(KILLER_ROLES),
        "declared_executioner": "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL",
        "k_misalign_sessions": 5,
        "comparator": "strictly greater after-cost per-decision "
                      "edge over Q-11-aligned pairs (a tie is not a "
                      "verdict); comparator figures and verdicts are "
                      "hashed/suppressed per cell",
        "q11_note": "UNDEFINED instants dropped from aligned "
                    "denominators and counted per side, never "
                    "inferred as zero",
    }
    payload["pbo"] = rl.pbo_record(max(len(cells), 0))
    payload["stages"] = stages
    if blocked is not None:
        payload["blocked"] = blocked

    # -- sanitization stage (scan of the payload minus this section) -- #
    pre_scan = sanitize_payload(payload)
    payload["sanitization"] = {
        "clean": pre_scan["clean"],
        "leaks": pre_scan["leaks"],
        "value_law_leaks": pre_scan["value_law_leaks"],
        "digest_law_leaks": pre_scan["digest_law_leaks"],
        "value_law": "no float value anywhere in the committed "
                     "artifact (counts are ints; internals are hex "
                     "digests)",
        "scope_note": "scan covers the payload minus this section; "
                      "re-running sanitize_payload on the committed "
                      "artifact is the enforcement (tests pin it)",
    }
    stages.append({"stage": "sanitization",
                   "status": "PASS" if pre_scan["clean"] else "FAIL",
                   "detail": "structural-only emission verified"
                   if pre_scan["clean"] else
                   f"leaks {len(pre_scan['leaks'])} "
                   f"value {len(pre_scan['value_law_leaks'])} "
                   f"digest {len(pre_scan['digest_law_leaks'])}"})

    # -- overall verdict (fail-closed; integrity/leak FAIL takes       #
    #    precedence over a BLOCKED plumbing state) -------------------- #
    if integrity_fails or not pre_scan["clean"] or any(
            s["status"] == "FAIL" for s in stages):
        verdict = "FAIL"
    elif blocked is not None:
        verdict = "BLOCKED_PRELAUNCH_CANDIDATE"
    else:
        verdict = "PASS"
    basis = [f"stage {s['stage']}={s['status']}" for s in stages]
    basis += [f"integrity: {f}" for f in integrity_fails]
    non_executable = sorted(
        f"{c['arm_id']}:{role}"
        for c in cell_manifests
        for role, ctl in c["battery"]["controls"].items()
        if ctl["status"] != "PASS")
    if verdict == "PASS":
        basis.append("all stages PASS; integrity clean; sanitizer "
                     "clean; structural-only emission verified")
        if non_executable:
            basis.append("recorded honestly, NOT a verdict input (Z "
                         "judges plumbing, not outcomes): battery "
                         "controls without >=1 aligned pair: "
                         + ", ".join(non_executable))
        else:
            basis.append("every battery control executable on >=1 "
                         "aligned pair in every cell")
    else:
        basis.append("fail-closed: see stages/integrity/blocked")
    payload["overall_verdict"] = verdict
    payload["verdict_basis"] = basis

    post_scan = sanitize_payload(payload)
    if not post_scan["clean"]:
        # the failure record itself must stay structural too
        raise ZSanitizationError(
            f"post-insertion sanitizer leak: "
            f"{post_scan['leaks'][:5]}")
    return payload


_CACHE: dict[tuple, dict] = {}


def cached_payload(plane_kwargs: Mapping[str, Any] | None = None
                   ) -> dict:
    """Session cache so the test-suite runs the real-substrate pipeline
    exactly once per configuration."""
    key = tuple(sorted((plane_kwargs or {}).items()))
    if key not in _CACHE:
        _CACHE[key] = run_z_dry_run(plane_kwargs)
    return _CACHE[key]


def main() -> int:
    payload = run_z_dry_run()
    emitted = emit_report(payload)
    print(json.dumps({
        "overall_verdict": payload["overall_verdict"],
        "report": emitted["wrote"],
        "artifact_sha256": emitted["artifact_sha256"],
        "cells": [c["arm_id"] for c in payload["cells"]],
        "sanitization": "CLEAN",
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
