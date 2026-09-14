"""COMMODITIES-NG1 E-phase SCORED EXECUTION driver (task
commodities-ng1-e-scored).

Lane E consumes the typed GO ("GO COMMODITIES NG1 SCORED EXECUTION",
lead adjudication deef2bb9 = this dispatch BASE) and computes the 3
FROZEN scored cells (S freeze ``selection_freeze.json``: single family
COMMNG1-A4-P2 x 3 booked arms ARM1-NEUTRAL / ARM2-TAILWIDE /
ARM3-WINDOWSHORT) ONE AT A TIME under the MACHINE-WIDE HEAVY LOCK,
through the FROZEN runner machinery only (research/assets/commodities_ng1/
-- read-only here; this module never edits it).

Laws enforced here (all inherited, none invented):

- machine-wide heavy lock held for the WHOLE scored run
  (COMMODITIES-NG1 / E_SCORED); the pre-check must be FREE_PROVEN;
  refusal is NOT_RUN_RESOURCE_CONFLICT, never a spin;
- arm_config_digest gate BEFORE any PnL: every booked arm consumed
  VERBATIM from the binding freeze, digest recomputed and matched
  (sha256 of the canonical JSON), digests pairwise distinct;
- evidence integrity: freeze/p2/p1 pins re-measured against the Z-R1
  addendum pins; per-pair chain structure digests must equal the
  committed Z-R2 manifests byte-for-byte (identical substrate + grid
  to the committed rehearsal); plane + ETP digest pins fail-closed;
- F1 BINDING (lead_adjudication_a7.json, BOUND pre-scored): the E gate
  MUST verify coverage_complete==true AND missing_killers==[] from the
  battery BEFORE recording any R1-R6 verdict; a gate that cannot prove
  killer coverage is FAIL fail-closed, never a pass;
- R1-R6 evaluated by the FROZEN evaluator (runners.stage_a.
  evaluate_stage_a) over the pooled family books; fail-closed: a rule
  that cannot be measured records its own NOT_RUN, never an inferred
  PASS; declared NOT_EXECUTABLE rows propagate VERBATIM (never coerced);
- kernel tier-2.0 cost exactly ONCE per fill; Q-16 instrument drag
  accrued over the held horizon (tier-independent); ETP legs
  RAW-primary; split-boundary law excludes spanning trades (excluded,
  recorded, never silently dropped); the 9 transaction-only legs stay
  EXCLUDED (the frozen 11-pair bookable set only);
- P-11 per-period series persistence is a LAUNCH REQUIREMENT: the full
  weekly per-period PnL series is persisted per cell (per pair + pooled)
  for the booked arm;
- NO rescue, NO threshold change, NO re-run for bad numbers; a single
  deterministic pass; TECHABORT is for genuine technical failures only.

Conventions this lane fixes (disclosed in every artifact that uses
them):

- per-period series: a period is one counted weekly release date; each
  trade's gross and net tier-2.0 PnL is attributed to its ENTRY release
  date (the SAME anchor the frozen fold law ``trades_to_folds`` uses);
  the FULL 401-period counted grid is persisted per pair and pooled,
  zero periods carried, with cumulative curves -- the DSR-ready P-11
  series;
- profit_factor = sum(winning net tier-2 trades) / |sum(losing net
  tier-2 trades)| on the kernel canonical rows; no losing trades ->
  None (recorded unbounded, never infinity) and the frozen R4 rule
  verdicts it;
- battery scope: the designated killers (PRICE_ONLY_SHADOW,
  RELEASE_CLOCK_SHADOW, SHIFTED_RELEASE_PLACEBO k=4) plus diagnostics
  (DELAY_PAIR, CLAIRVOYANT) run on the IDENTICAL bookable grid,
  restricted leg set, window and frozen cost treatment as the arm.

Usage:
    .venv/bin/python research/control/commodities_ng1_run/e/run_scored.py
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
import traceback

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.governance import heavy_lock                  # noqa: E402
from research.assets.commodities_ng1.runners import dry_run as DRY  # noqa: E402
from research.assets.commodities_ng1.runners.battery import (  # noqa: E402
    DIAGNOSTIC_ROLES,
    EXECUTION_LAG,
    KILLER_ROLES,
    battery_position_series,
    falsification_eval,
    q11_eligibility,
)
from research.assets.commodities_ng1.runners.chain import (  # noqa: E402
    ChainRefused,
    build_pair_chain,
    verify_pair_census,
)
from research.assets.commodities_ng1.runners.execute import (  # noqa: E402
    EMPTY_BOOKED_POPULATION_CLASS,
    NOT_EXECUTABLE_VERDICT,
    arm_metrics,
    book_ledger,
    decision_trades,
    trades_to_folds,
)
from research.assets.commodities_ng1.runners.stage_a import (  # noqa: E402
    FOLDS_FROZEN,
    evaluate_stage_a,
    fold_of,
    pbo_verdict,
)

E_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_DIR = os.path.dirname(E_DIR)
REPO = REPO_ROOT

DISPATCH_SHA = "deef2bb9c773332500f7e6474d4996ebb7717891"
BRANCH = "orca/commodities-ng1-integration"
CYCLE_ID = "COMMODITIES-NG1"
TASK_ID = "commodities-ng1-e-scored"
LANE = "e"

GO_PHRASE = "GO COMMODITIES NG1 SCORED EXECUTION"
ADJUDICATION_RELPATH = ("research/control/COMMODITIES-NG1/orchestration/"
                        "handoffs/lead_adjudication_a7.json")
ADJUDICATION_COMMIT = "821f641aea4fac8bacf76f1bb2b4d9975b146272"
FREEZE_RELPATH = "research/control/commodities_ng1_run/s/selection_freeze.json"
ADDENDUM_RELPATH = ("research/control/commodities_ng1_run/s/"
                    "selection_freeze_addendum_zr1.json")
P2_RELPATH = "research/control/commodities_ng1_run/p2_gate.json"
CONTRACT_RELPATH = "research/control/commodities_ng1_run/p1_cost_contract.json"
ZR2_ARM1_RELPATH = ("research/control/commodities_ng1_run/zr2/"
                    "cell_COMMNG1-A4-P2-ARM1-NEUTRAL.json")

#: The 3 frozen scored cells, in dispatch order (ARM1 -> ARM2 -> ARM3,
#: serialized one at a time).
CELL_IDS = (
    "COMMNG1-A4-P2-ARM1-NEUTRAL",
    "COMMNG1-A4-P2-ARM2-TAILWIDE",
    "COMMNG1-A4-P2-ARM3-WINDOWSHORT",
)
CELL_ROLES = {
    "COMMNG1-A4-P2-ARM1-NEUTRAL": "ANCHOR",
    "COMMNG1-A4-P2-ARM2-TAILWIDE": "NEIGHBOUR",
    "COMMNG1-A4-P2-ARM3-WINDOWSHORT": "NEIGHBOUR",
}

ALL_ROLES = ("ANCHOR",) + KILLER_ROLES + DIAGNOSTIC_ROLES

#: Runner/support modules whose exact bytes are digest-pinned as
#: provenance (the machinery this scored run executed).
CODE_MODULES = (
    "research/assets/commodities_ng1/runners/__init__.py",
    "research/assets/commodities_ng1/runners/rule.py",
    "research/assets/commodities_ng1/runners/chain.py",
    "research/assets/commodities_ng1/runners/execute.py",
    "research/assets/commodities_ng1/runners/battery.py",
    "research/assets/commodities_ng1/runners/stage_a.py",
    "research/assets/commodities_ng1/runners/dry_run.py",
    "research/assets/commodities_ng1/plane_adapter.py",
    "research/assets/commodities_ng1/clock.py",
    "research/assets/commodities_ng1/cot_census.py",
    "research/assets/commodities_ng1/etp_census.py",
    "research/assets/commodities_ng1/feasibility.py",
    "research/assets/commodities_ng1/kernel.py",
    "research/accounting.py",
)

F1_LAW = (
    "F1 BINDING (lead_adjudication_a7.json, BOUND pre-scored): the E "
    "gate MUST verify coverage_complete==true and missing_killers==[] "
    "from the battery BEFORE recording any R1-R6 verdict; unprovable "
    "killer coverage is FAIL fail-closed, never a pass.")

NO_TUNING_DECLARATION = (
    "no tuning after seeing numbers: every parameter is consumed "
    "VERBATIM from the frozen S selection_freeze.json arms "
    "(arm_config_digests re-verified before any PnL); thresholds, "
    "folds, battery, k=4, cost treatment and the bookable set are the "
    "frozen bytes; this lane ran ONE deterministic pass, made NO "
    "re-run for outcomes, and changed NO threshold, parameter or "
    "selection after any scored number was visible; no rescue, ever "
    "(S freeze outcome_knowledge_declaration.no_rescue).")

PERIOD_SERIES_CONVENTION = (
    "P-11 per-period series: one period per counted grid-eligible "
    "decision instant on the frozen counted grid (2019-01-04 .. "
    "2026-09-04 mapped, 401 decision periods per pair; the counted "
    "window's final release 2026-09-11 is unmapped -- no decision "
    "session, clock law, disclosed by the committed P2 census -- and "
    "is not a decision period); each trade's gross and net tier-2.0 "
    "PnL is attributed to its ENTRY release date (the same anchor the "
    "frozen fold law trades_to_folds uses); the FULL 401-period grid "
    "is persisted (zero periods carried) with cumulative curves; "
    "persisted for the booked arm (ANCHOR) per pair and pooled; "
    "killers carry aggregates only (they are kill controls, not S1 "
    "candidates).")


#: Attempt history (declared, honest): attempts 1-3 TECHABORT were
#: DRIVER bugs, not substrate or machinery defects (attempt-1:
#: evidence-pin key lookup used 'p1_cost_contract' where the Z-R1
#: addendum affirmation key is 'cost_contract_unchanged'; attempt-2:
#: the bookable_set excluded-legs field indexed as a dict when the
#: frozen S freeze stores a list; attempt-3: the lane serializer
#: indexed 'exit_release_date', which the frozen executor sets only on
#: release-mapped exits -- terminal-policy legs carry none).  No
#: outcome number was committed or used for any decision in any
#: attempt; the heavy lock was released TECHABORT cleanly each time;
#: the next attempt is the full deterministic recompute (FOREX-NG1 E
#: precedent).  No rescue, no threshold change, no re-run FOR
#: outcomes.
ATTEMPT_HISTORY = [
    {
        "attempt": 1,
        "started_utc": "2026-09-14T04:35:40Z (heavy_worker.history.jsonl "
                       "started_at; released 2026-09-14T04:35:40Z)",
        "verdict": "TECHABORT",
        "failure": "driver bug at the evidence-pin gate: KeyError "
                   "'p1_cost_contract' -- the Z-R1 addendum affirmation "
                   "key is 'cost_contract_unchanged'; no PnL computed",
        "lock_release": "TECHABORT (heavy_worker.history.jsonl)",
        "outcome_influence": "none: the failure predates every outcome "
                             "number; attempt-2 is the full "
                             "deterministic recompute",
    },
    {
        "attempt": 2,
        "started_utc": "2026-09-14T04:36:42Z (heavy_worker.history.jsonl "
                       "started_at; released 2026-09-14T04:36:42Z)",
        "verdict": "TECHABORT",
        "failure": "driver bug at freeze assembly (still BEFORE any "
                   "PnL): the bookable_set excluded-transaction-only-legs "
                   "field is a LIST in the frozen S freeze; the driver "
                   "indexed it as a dict (TypeError); no PnL computed",
        "lock_release": "TECHABORT (heavy_worker.history.jsonl)",
        "outcome_influence": "none: the failure predates every outcome "
                             "number; attempt-3 is the full "
                             "deterministic recompute",
    },
    {
        "attempt": 3,
        "verdict": "TECHABORT",
        "failure": "driver bug in the lane's own per-trade-record "
                   "serializer: the frozen executor (execute."
                   "decision_trades) sets 'exit_release_date' only on "
                   "release-mapped exits; a terminal-policy leg (force-"
                   "closed at the last observable mark) carries none and "
                   "the serializer indexed it unconditionally "
                   "(KeyError); books were computed but no verdict or "
                   "artifact was finalized; no outcome number was "
                   "committed or used for any decision",
        "lock_release": "TECHABORT (heavy_worker.history.jsonl)",
        "outcome_influence": "none: the serializer fix touches no "
                             "threshold, parameter or selection; "
                             "attempt-4 is the full deterministic "
                             "recompute",
    },
    {
        "attempt": 4,
        "verdict": "TECHABORT",
        "failure": "driver bug in the lane's own gate assembly: "
                   "config['arm_config_digests'] does not exist in the "
                   "dry_run.assemble_booked_arms return (the map is "
                   "built from config['arms'] per-arm recorded_digest "
                   "rows); KeyError at the e_gate writer after the "
                   "cells were computed; no artifact was finalized and "
                   "no outcome number was committed or used for any "
                   "decision",
        "lock_release": "TECHABORT (heavy_worker.history.jsonl)",
        "outcome_influence": "none: the fix is a lane-serializer key "
                             "repair; attempt-5 is the full "
                             "deterministic recompute, pre-validated "
                             "end-to-end on a SYNTHETIC rehearsal of "
                             "main() (mocked substrate + lock) before "
                             "the next locked attempt",
    },
    {
        "attempt": 5,
        "verdict": "FINISHED (artifacts superseded by attempt-6 before "
                   "commit)",
        "failure": "no failure of computation: the driver's P-11 series "
                   "grid used the 402-release counted WINDOW (including "
                   "the unmapped final release 2026-09-11) instead of "
                   "the frozen 401-instant decision grid -- a disclosure-"
                   "grid inconsistency caught in post-run review; the "
                   "extra period is a zero period, so every booked "
                   "number, verdict and margin is identical; the "
                   "grid/prose were corrected and the run re-executed "
                   "deterministically",
        "lock_release": "FINISHED (heavy_worker.history.jsonl)",
        "outcome_influence": "none: verdicts, books and margins "
                             "unchanged; only the persisted period-grid "
                             "metadata was aligned to the frozen "
                             "decision grid",
    },
    {
        "attempt": 6,
        "verdict": "this ledger",
        "started_utc": "recorded in started_utc above",
    },
]


class ERefused(Exception):
    """Fail-closed E refusal (digest/pin/authority mismatch): no PnL."""


class ExecutionBroken(Exception):
    """A structural identity broke (fills 2x trades, dual-book
    reconciliation): fail-closed honest record."""


def utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _git(*args: str) -> str:
    out = subprocess.run(["git", "-C", REPO, *args],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_canonical(obj) -> str:
    return hashlib.sha256(
        DRY.canonical_json(obj).encode("utf-8")).hexdigest()


def write_json(path: str, payload: dict) -> str:
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return sha256_file(path)


def code_module_digests() -> dict:
    out = {}
    for rel in CODE_MODULES:
        p = os.path.join(REPO, rel)
        out[rel] = sha256_file(p) if os.path.isfile(p) else "ABSENT"
    return out


# --------------------------------------------------------------------------- #
# evidence + authority (READ-ONLY; fail-closed pins)
# --------------------------------------------------------------------------- #

def load_authority(head_sha: str) -> dict:
    """The typed GO at this cycle's own gate, fail-closed."""
    path = os.path.join(REPO, ADJUDICATION_RELPATH)
    if not os.path.isfile(path):
        raise ERefused(f"adjudication artifact absent: {path}; fail closed")
    with open(path, encoding="utf-8") as fh:
        adj = json.load(fh)
    go = adj.get("go_decision") or {}
    if go.get("authorized_by_audit") is not True:
        raise ERefused("adjudication go_decision.authorized_by_audit "
                       "is not true; fail closed")
    if go.get("go_phrase") != GO_PHRASE:
        raise ERefused(f"adjudication go_phrase != {GO_PHRASE!r}; fail closed")
    if go.get("scope_reminder", "").find("budget 3") < 0:
        raise ERefused("adjudication scope_reminder does not pin budget 3; "
                       "fail closed")
    # the audit commit must be an ancestor of HEAD (the GO rides the
    # adjudication commit deef2bb9 == dispatch BASE)
    try:
        subprocess.run(
            ["git", "-C", REPO, "merge-base", "--is-ancestor",
             ADJUDICATION_COMMIT, head_sha],
            check=True, capture_output=True, text=True)
        ancestor = True
    except subprocess.CalledProcessError:
        ancestor = False
    if not ancestor:
        raise ERefused(
            f"adjudication audit commit {ADJUDICATION_COMMIT} is not an "
            f"ancestor of HEAD {head_sha}; fail closed")
    return {
        "adjudication_artifact": ADJUDICATION_RELPATH,
        "adjudication_artifact_sha256": sha256_file(path),
        "adjudicator": adj.get("adjudicator"),
        "audit_commit": ADJUDICATION_COMMIT,
        "audit_commit_ancestor_of_head": True,
        "authorized_by_audit": True,
        "go_phrase": GO_PHRASE,
        "go_typed_by": go.get("go_typed_by"),
        "scope_reminder": go.get("scope_reminder"),
        "f1_binding": adj.get("adjudications", {}).get("F1", {}),
    }


def load_evidence_pins() -> dict:
    """READ-ONLY evidence pins (Z-R1 addendum): re-measured, fail-closed."""
    paths = {k: os.path.join(REPO, rel) for k, rel in (
        ("freeze", FREEZE_RELPATH),
        ("addendum", ADDENDUM_RELPATH),
        ("p2_gate", P2_RELPATH),
        ("cost_contract", CONTRACT_RELPATH),
        ("zr2_arm1_manifest", ZR2_ARM1_RELPATH),
        ("adjudication", ADJUDICATION_RELPATH),
    )}
    for k, p in paths.items():
        if not os.path.isfile(p):
            raise ERefused(f"READ-ONLY evidence absent: {p}; fail closed")
    with open(paths["addendum"], encoding="utf-8") as fh:
        addendum = json.load(fh)
    measured = {k: sha256_file(p) for k, p in paths.items()}
    pinned = {
        "freeze": addendum["amended_artifact"]["sha256"],
        "p2_gate": addendum["affirmations"]["p2_gate_unchanged"]["sha256"],
        "cost_contract":
            addendum["affirmations"]["cost_contract_unchanged"]["sha256"],
    }
    mismatches = sorted(k for k, v in pinned.items() if measured[k] != v)
    if mismatches:
        raise ERefused(
            f"evidence digest mismatch against the Z-R1 addendum pins: "
            f"{mismatches}; fail closed")
    with open(paths["zr2_arm1_manifest"], encoding="utf-8") as fh:
        zr2_arm1 = json.load(fh)
    return {
        "paths": {k: rel for k, rel in (
            ("freeze", FREEZE_RELPATH),
            ("addendum", ADDENDUM_RELPATH),
            ("p2_gate", P2_RELPATH),
            ("cost_contract", CONTRACT_RELPATH),
            ("zr2_arm1_manifest", ZR2_ARM1_RELPATH),
            ("adjudication", ADJUDICATION_RELPATH))},
        "measured_sha256": measured,
        "pinned_sha256": pinned,
        "digest_mismatches": [],
        "zr2_chain_digests": {
            pid: row.get("chain_structure_digest")
            for pid, row in (zr2_arm1.get("per_pair") or {}).items()},
    }


# --------------------------------------------------------------------------- #
# substrate (REAL mode via the P0 plane, digest-verified)
# --------------------------------------------------------------------------- #

def load_real_substrate(run_dir: str, codes: list, legs: list,
                        etp_pins: dict) -> dict:
    from research.assets.commodities_ng1.plane_adapter import (
        CommoditiesNG1Plane,
    )
    plane = CommoditiesNG1Plane(
        manifest_path=os.path.join(run_dir, "p0_raw_manifest.json"))
    cot_by_code: dict[str, list] = {}
    plane_rows = []
    for year in range(2016, 2027):
        entry = f"cftc/deacot{year}"
        res = plane.consume(entry)
        plane_rows.append({
            "entry": entry,
            "digest_match": bool(res["sha256_pinned"]
                                 == res["sha256_measured"]),
            "bytes": int(res["bytes"]),
        })
        _, records = plane.consume_records(entry)
        for rec in records:
            if rec.contract_market_code in codes:
                cot_by_code.setdefault(
                    rec.contract_market_code, []).append({
                        "report_date": rec.report_date,
                        "open_interest": rec.open_interest,
                        "noncomm_long": rec.noncomm_long,
                        "noncomm_short": rec.noncomm_short,
                        "noncomm_spreading": rec.noncomm_spreading,
                        "comm_long": rec.comm_long,
                        "comm_short": rec.comm_short,
                    })
    leg_ctx: dict[str, dict] = {}
    leg_rows = []
    for symbol in legs:
        entry = f"etp/eod/{symbol}"
        res = plane.consume(entry)
        _, rows = plane.consume_records(entry)
        dates = [r["date"] for r in rows]
        closes = {r["date"]: r["close"] for r in rows}
        pin = etp_pins.get(symbol)
        leg_rows.append({
            "leg": symbol,
            "digest_match": bool(res["sha256_pinned"]
                                 == res["sha256_measured"]),
            "etp_pin_match": bool(pin is not None
                                  and res["sha256_measured"] == pin),
            "sessions": len(dates),
        })
        leg_ctx[symbol] = {
            "session_dates": dates,
            "session_closes": closes,
            "etp_pin_match": bool(pin is not None
                                  and res["sha256_measured"] == pin),
        }
    return {"cot_by_code": cot_by_code, "leg_ctx": leg_ctx,
            "plane_digest_rows": plane_rows, "etp_digest_rows": leg_rows}


def split_boundaries_of(cost_contract: dict, symbol: str) -> list:
    """The leg's COMMITTED measured share-base boundary dates
    (p1_cost_contract per_leg spread.share_base_events; never
    re-derived)."""
    events = (cost_contract.get("per_leg", {}).get(symbol, {})
              .get("spread", {}).get("share_base_events", []))
    return sorted(e["boundary_date"] for e in events)


def leg_cost_constants(cost_contract: dict, symbol: str) -> dict:
    """Kernel cost constants for ONE leg from the frozen contract
    (half-spread CS p90 per fill; Q-16 expense + same-underlying
    tracking proxy where MEASURED, else None -- never invented)."""
    leg = cost_contract["per_leg"][symbol]
    tracking = leg.get("tracking_proxy") or {}
    measured_tracking = \
        tracking.get("status") == "MEASURED_SAME_UNDERLYING_PAIRS"
    return {
        "half_spread_frac": leg["half_spread_frac_p90_per_fill"],
        "expense_annual": leg["expense_fact"]["expense_ratio_annual"],
        "tracking_divergence_annual":
            tracking.get("abs_divergence_annualized_mean")
            if measured_tracking else None,
    }


# --------------------------------------------------------------------------- #
# chains + census + parity vs the committed Z-R2 digests
# --------------------------------------------------------------------------- #

def _counted_window_indices(chain: dict) -> list:
    from research.assets.commodities_ng1.feasibility import (
        WARMUP_WEEKS,
        WINDOW_START,
    )
    rows = chain["rows"]
    window_rows = [i for i, r in enumerate(rows)
                   if r["release_date"] >= WINDOW_START]
    return window_rows[WARMUP_WEEKS:]


def chain_structure_digest(chain: dict) -> str:
    """IDENTICAL construction to the committed Z-R2 manifests
    (parity pin: the scored grid is byte-identical to the rehearsed
    one)."""
    return sha256_canonical([{
        "report_date": r["report_date"].isoformat(),
        "release_date": r["release_date"].isoformat(),
        "rule_source": r["rule_source"],
        "decision_session": r["decision_session"].isoformat()
        if r["decision_session"] is not None else None,
        "counted": bool(c),
    } for r, c in zip(chain["rows"], chain["counted"])])


def build_and_verify_chains(bookable: list, cot_by_code: dict,
                            leg_ctx: dict, p2_per_pair_census: dict,
                            boundaries_by_leg: dict,
                            zr2_chain_digests: dict) -> dict:
    chains = {}
    pair_rows = {}
    for pid in bookable:
        code, symbol = pid.split("/")
        row = {
            "cot_market_code": code,
            "etp_leg": symbol,
            "chain_built": False,
            "census_identity_verified": False,
            "failure_class": None,
            "failure_detail": None,
        }
        try:
            reports = cot_by_code.get(code)
            if not reports:
                raise ChainRefused(f"pair {pid}: no CoT reports; fail closed")
            ctx = leg_ctx[symbol]
            chain = build_pair_chain(
                reports, ctx["session_dates"], ctx["session_closes"])
            census_ref = p2_per_pair_census.get(pid, {}).get(
                "floor_evaluation")
            if census_ref is None:
                raise ChainRefused(
                    f"pair {pid}: no committed P2 census to verify "
                    "against; fail closed")
            census_ok = bool(verify_pair_census(pid, chain, census_ref))
            digest = chain_structure_digest(chain)
            zr2_digest = zr2_chain_digests.get(pid)
            if zr2_digest is None:
                raise ERefused(
                    f"pair {pid}: no committed Z-R2 chain digest to pin "
                    "parity against; fail closed")
            if digest != zr2_digest:
                raise ERefused(
                    f"pair {pid}: chain structure digest != committed Z-R2 "
                    f"manifest digest ({digest} != {zr2_digest}); the "
                    "substrate drifted; fail closed")
            counted_n = int(sum(chain["counted"]))
            row.update({
                "chain_built": True,
                "census_identity_verified": census_ok,
                "cot_reports": len(reports),
                "etp_sessions": len(set(ctx["session_dates"])),
                "chain_rows": len(chain["rows"]),
                "counted_instants": counted_n,
                "split_boundary_dates": boundaries_by_leg.get(symbol, []),
                "chain_structure_digest": digest,
                "chain_digest_parity_vs_zr2": True,
            })
            chains[pid] = chain
        except ERefused:
            raise
        except Exception as exc:            # recorded, never repaired
            row["failure_class"] = type(exc).__name__
            row["failure_detail"] = str(exc)
            raise ERefused(
                f"pair {pid}: chain/census structural failure: "
                f"{type(exc).__name__}: {exc}; fail closed") from exc
        pair_rows[pid] = row
    return {"pair_rows": pair_rows, "chains": chains}


# --------------------------------------------------------------------------- #
# booking + metrics
# --------------------------------------------------------------------------- #

def _project_to_counted_grid(positions: list, counted: list) -> list:
    """Frozen execution law: decisions exist only on the counted grid;
    the decision series is projected onto it before booking (identity
    on counted rows, flat elsewhere; open legs close by the terminal
    policy)."""
    return [float(p) if c else 0.0 for p, c in zip(positions, counted)]


def validate_declared_row(row: dict, where: str) -> None:
    """Fail-closed validation of a DECLARED ``NOT_EXECUTABLE`` row
    (Z-R1 remediation law): declared empty booked population with
    reason + exclusion disclosure; kernel book and root reconciliation
    never invoked; never a crash, never a silent pass, never an
    inferred number."""
    if row.get("verdict") != NOT_EXECUTABLE_VERDICT:
        raise ERefused(f"{where}: declared row verdict is "
                       f"{row.get('verdict')!r}; fail closed")
    if row.get("declared") is not True:
        raise ERefused(f"{where}: declared row is not declared; fail closed")
    if row.get("outcome_class") != EMPTY_BOOKED_POPULATION_CLASS:
        raise ERefused(f"{where}: declared row outcome class "
                       f"{row.get('outcome_class')!r}; fail closed")
    if not str(row.get("reason") or "").strip():
        raise ERefused(f"{where}: declared row carries no reason; fail closed")
    if not str(row.get("disclosure") or "").strip():
        raise ERefused(f"{where}: declared row carries no disclosure; "
                       "fail closed")
    if row.get("kernel_book") is not None \
            or row.get("reconciliation") is not None:
        raise ERefused(f"{where}: declared row must not carry a kernel book "
                       "or a root reconciliation; fail closed")
    if int(row.get("booked_trades", -1)) != 0:
        raise ERefused(f"{where}: declared row booked_trades != 0; "
                       "fail closed")


def scalar_metrics(m: dict) -> dict:
    """arm_metrics minus the per-trade pnl lists (pooled anchor keeps
    the lists internally for R6/records; per-pair rows stay compact)."""
    return {
        "trades": m["trades"],
        "fills": m["fills"],
        "eligible_instants": m["eligible_instants"],
        "net_total_tier_2_0": m["net_total_tier_2_0"],
        "gross_total": m["gross_total"],
        "per_trade_edge": m["per_trade_edge"],
        "per_decision_edge": m["per_decision_edge"],
        "profit_factor": m["profit_factor"],
        "pf_margin_above_1_10": m["pf_margin_above_1_10"],
    }


def _book_one(pid: str, role: str, chain: dict, params: dict,
              symbol: str, leg_ctx_row: dict, boundaries: set,
              cost_constants: dict) -> dict:
    """End-to-end scored booking of ONE (cell, pair, role):
    decision series -> counted-grid projection -> kernel booking
    (tier-2.0 once per fill; Q-16 drag; split-boundary exclusions;
    declared NOT_EXECUTABLE on an empty booked population, verbatim)
    -> fold partition."""
    series = battery_position_series(chain, params, roles=(role,))
    positions = _project_to_counted_grid(series[role], chain["counted"])
    res = decision_trades(
        chain, positions, symbol, leg_ctx_row["session_dates"],
        leg_ctx_row["session_closes"],
        split_boundary_dates=boundaries,
        execution_lag_sessions=EXECUTION_LAG[role])
    counted_n = int(sum(chain["counted"]))
    held = sum(1 for p, c in zip(positions, chain["counted"])
               if c and p != 0.0)
    excluded_n = int(len(res["split_boundary_excluded"]))
    structural = {
        "held_decision_count": int(held),
        "flat_decision_count": int(counted_n - held),
        "unmapped_decision_rows": int(res["unmapped_rows"]),
        "split_boundary_excluded_trades": excluded_n,
    }
    folds = trades_to_folds(res["trades"])
    structural["fold_partition_counts"] = {
        f["fold_id"]: int(len(folds[f["fold_id"]])) for f in FOLDS_FROZEN}
    structural["fold_partition_total_matches_trades"] = bool(
        sum(structural["fold_partition_counts"].values())
        == len(res["trades"]))
    if excluded_n > 0:
        empty_reason = (
            f"pair {pid} role {role}: every booked trade was excluded by "
            f"the split-boundary law ({excluded_n} excluded); empty "
            "booked population")
    else:
        empty_reason = (
            f"pair {pid} role {role}: booked population is empty: no "
            "trade survived to book")
    booked = book_ledger(
        res["trades"], {symbol: cost_constants},
        empty_reason=empty_reason,
        excluded_trades=excluded_n)
    if booked.get("verdict") == NOT_EXECUTABLE_VERDICT:
        validate_declared_row(booked, f"{pid}/{role}")
        structural.update({
            "control_executable_verdict": NOT_EXECUTABLE_VERDICT,
            "declared_row": booked,           # propagated VERBATIM
            "trades_booked": 0,
            "fills": 0,
            "metrics": None,
        })
        return {"structural": structural, "trades": res["trades"],
                "folds": folds}
    ledger = booked["ledger"]
    fills = int(res["fills"])
    trades_n = int(len(res["trades"]))
    if fills != 2 * trades_n:
        raise ExecutionBroken(
            f"{pid}/{role}: fills {fills} != 2x booked trades "
            f"{trades_n}; once-per-fill audit trail broken; fail closed")
    if not booked["reconciliation"]["identity_ok"]:
        raise ExecutionBroken(
            f"{pid}/{role}: dual-book reconciliation identity broken; "
            "fail closed")
    metrics = arm_metrics(ledger, eligible_instants=counted_n,
                          n_trades=trades_n)
    structural.update({
        "control_executable_verdict": "PASS",
        "declared_row": None,
        "trades_booked": trades_n,
        "fills": fills,
        "metrics": scalar_metrics(metrics),
        "net_totals_by_tier": {t: ledger["net"][t]["total"]
                               for t in ledger["net"]},
        "gross_total": ledger["gross"]["total"],
        "costs_by_tier": {t: dict(ledger["costs"][t])
                          for t in ledger["costs"]},
    })
    return {"structural": structural, "trades": res["trades"],
            "folds": folds}


def fold_nets_of(pooled_trades: list, pair_of: dict,
                 canonical_rows: list) -> dict:
    """Frozen-fold net tier-2.0 totals of the pooled anchor book
    (trades assigned by ENTRY release date via trades_to_folds; the
    canonical rows are index-aligned with the trade list by kernel
    construction -- verified by the caller)."""
    out = {f["fold_id"]: [] for f in FOLDS_FROZEN}
    for i, t in enumerate(pooled_trades):
        fid = fold_of(t["entry_release_date"])
        if fid is None:
            raise ExecutionBroken(
                f"trade {t['trade_id']} ({pair_of[i]}): entry release "
                f"{t['entry_release_date']} outside the frozen folds")
        out[fid].append(canonical_rows[i]["canonical_pnl"])
    return {fid: (math.fsum(v) if v else None) for fid, v in out.items()}


def period_series(counted_dates: list, session_of: dict,
                  trades: list, canonical_rows: list) -> dict:
    """The P-11 per-period series: full counted-grid periods (zeros
    carried), entry-release attribution, cumulative curves."""
    by_date: dict[str, dict] = {}
    for i, t in enumerate(trades):
        d = t["entry_release_date"]
        agg = by_date.setdefault(d, {"n": 0, "gross": [], "net": []})
        agg["n"] += 1
        agg["gross"].append(
            canonical_rows[i]["gross_pnl_usd"])
        agg["net"].append(canonical_rows[i]["canonical_pnl"])
    periods = []
    cg = cn = 0.0
    for d in counted_dates:
        agg = by_date.get(d)
        g = math.fsum(agg["gross"]) if agg else 0.0
        n = math.fsum(agg["net"]) if agg else 0.0
        cg += g
        cn += n
        periods.append({
            "release_date": d,
            "decision_session": session_of.get(d),
            "trades_entered": agg["n"] if agg else 0,
            "gross_usd": g,
            "net_tier2_usd": n,
            "cum_gross_usd": cg,
            "cum_net_tier2_usd": cn,
        })
    return {
        "convention": PERIOD_SERIES_CONVENTION,
        "periods_count": len(periods),
        "periods": periods,
        "final_cum_gross_usd": cg,
        "final_cum_net_tier2_usd": cn,
    }


def canonical_rows_aligned(ledger: dict, trades: list) -> list:
    """Kernel canonical rows are index-aligned with the trade list by
    construction (one primary-tier row per trade, same loop order);
    verified fail-closed here."""
    rows = ledger["canonical_rows"]
    if len(rows) != len(trades):
        raise ExecutionBroken(
            f"canonical rows {len(rows)} != trades {len(trades)}; "
            "fail closed")
    for i, (r, t) in enumerate(zip(rows, trades)):
        if r["trade_id"] != t["trade_id"] or r["leg"] != t["leg"]:
            raise ExecutionBroken(
                f"canonical row {i} misaligned with trade "
                f"({r['trade_id']} vs {t['trade_id']}); fail closed")
    return rows


# --------------------------------------------------------------------------- #
# one cell
# --------------------------------------------------------------------------- #

def execute_cell(arm: dict, pair_rows: dict, chains: dict, leg_ctx: dict,
                 boundaries_by_leg: dict, leg_costs: dict,
                 counted_dates_by_pair: dict, session_maps: dict,
                 lock) -> dict:
    """Score ONE frozen cell: every bookable pair x every battery role
    end-to-end through the frozen runners on the real substrate, then
    the pooled per-role books, the F1 coverage gate, and the frozen
    R1-R6 evaluator (only AFTER coverage is proven)."""
    arm_id = arm["arm_id"]
    params = arm["arm_config"]["parameters"]
    per_pair_roles: dict[str, dict] = {}
    pooled_trades: dict[str, list] = {role: [] for role in ALL_ROLES}
    pooled_pairs: dict[str, list] = {role: [] for role in ALL_ROLES}

    for pid in sorted(pair_rows):
        chain = chains[pid]
        code, symbol = pid.split("/")
        boundaries = set(boundaries_by_leg.get(symbol, ()))
        roles_out = {}
        for role in ALL_ROLES:
            booked = _book_one(pid, role, chain, params, symbol,
                               leg_ctx[symbol], boundaries,
                               leg_costs[symbol])
            structural = booked["structural"]
            roles_out[role] = structural
            pooled_trades[role].extend(booked["trades"])
            pooled_pairs[role].extend([pid] * len(booked["trades"]))
        per_pair_roles[pid] = roles_out
        lock.heartbeat(extra={"cell_progress": f"{arm_id}:{pid}"})

    # pooled per-role books (all pairs; all-leg frozen cost constants)
    pooled = {}
    pooled_counted = sum(prow["counted_instants"]
                         for prow in pair_rows.values())
    for role in ALL_ROLES:
        trades = pooled_trades[role]
        booked = book_ledger(trades, leg_costs)
        if booked.get("verdict") == NOT_EXECUTABLE_VERDICT:
            validate_declared_row(booked, f"{arm_id}/POOLED/{role}")
            pooled[role] = {
                "control_executable_verdict": NOT_EXECUTABLE_VERDICT,
                "declared_row": booked,
                "trades_booked": 0,
                "fills": 0,
                "eligible_instants": pooled_counted,
                "metrics": None,
            }
            continue
        ledger = booked["ledger"]
        if fills_of(trades) != 2 * len(trades):
            raise ExecutionBroken(
                f"{arm_id}/POOLED/{role}: once-per-fill audit trail "
                "broken; fail closed")
        if not booked["reconciliation"]["identity_ok"]:
            raise ExecutionBroken(
                f"{arm_id}/POOLED/{role}: dual-book reconciliation "
                "identity broken; fail closed")
        metrics = arm_metrics(ledger, eligible_instants=pooled_counted,
                              n_trades=len(trades))
        entry = {
            "control_executable_verdict": "PASS",
            "declared_row": None,
            "trades_booked": len(trades),
            "fills": fills_of(trades),
            "eligible_instants": pooled_counted,
            "metrics": metrics,
            "net_totals_by_tier": {t: ledger["net"][t]["total"]
                                   for t in ledger["net"]},
            "gross_total": ledger["gross"]["total"],
            "costs_by_tier": {t: dict(ledger["costs"][t])
                              for t in ledger["costs"]},
            "_ledger": ledger,
            "_canonical_rows": canonical_rows_aligned(ledger, trades),
        }
        pooled[role] = entry

    # ---- F1 COVERAGE GATE (BEFORE any R1-R6 verdict) -------------------- #
    anchor = pooled["ANCHOR"]
    killer_metrics = {r: pooled[r]["metrics"] for r in KILLER_ROLES
                      if pooled[r].get("metrics") is not None}
    missing_rows = [r for r in KILLER_ROLES
                    if pooled[r]["control_executable_verdict"]
                    == NOT_EXECUTABLE_VERDICT]
    if anchor.get("metrics") is None:
        coverage = {
            "coverage_complete": False,
            "missing_killers": list(KILLER_ROLES),
            "gate": F1_LAW,
            "falsification_eval": None,
            "note": "anchor pooled book NOT_EXECUTABLE: no R1-R6 verdict "
                    "may be recorded (fail-closed)",
        }
    else:
        fe = falsification_eval(anchor["metrics"], killer_metrics)
        coverage = {
            "coverage_complete": bool(fe["coverage_complete"]),
            "missing_killers": list(fe["missing_killers"]),
            "gate": F1_LAW,
            "falsification_eval": fe,
            "pooled_not_executable_killers": missing_rows,
            "note": "per-pair declared NOT_EXECUTABLE rows (if any) are "
                    "propagated verbatim in per_pair_roles; the F1 "
                    "coverage proof is at the pooled family scope "
                    "(the R1-R6 evaluation scope)",
        }

    # ---- frozen R1-R6 evaluator (ONLY after coverage proven) ------------ #
    if not (coverage["coverage_complete"]
            and coverage["missing_killers"] == []):
        rules_block = {
            "status": "NOT_RECORDED",
            "reason": F1_LAW + " Coverage unproven: no R1-R6 verdict is "
                      "recorded for this cell (fail-closed FAIL, never "
                      "a pass).",
        }
        evaluator_verdict = None
        cell_verdict = "FAIL_COVERAGE_UNPROVEN"
        killed_by = ["F1_COVERAGE_UNPROVEN"]
        margins = None
        fold_detail = None
        series_block = None
        per_trade_records = None
    else:
        canonical_rows = anchor["_canonical_rows"]
        trades = pooled_trades["ANCHOR"]
        pair_of = pooled_pairs["ANCHOR"]
        fold_nets = fold_nets_of(trades, pair_of, canonical_rows)
        ev = evaluate_stage_a(anchor["metrics"],
                              {r: pooled[r]["metrics"]
                               for r in KILLER_ROLES},
                              fold_nets)
        rules_block = ev
        evaluator_verdict = ev["verdict"]
        if ev["survivor"]:
            cell_verdict = "SURVIVOR"
            killed_by = []
        else:
            cell_verdict = "KILL"
            killed_by = []
            for rid in ("R1", "R3", "R4", "R5", "R6"):
                if ev["rules"][rid]["verdict"] != "PASS":
                    killed_by.append(rid)
            if ev["r2_any_kill"]:
                killed_by.append(
                    "R2(" + ",".join(sorted(
                        k for k, v in ev["rules"]["R2"].items()
                        if v["kill"])) + ")")
        margins = margins_of(ev, anchor["metrics"], pooled)
        # per-fold detail + P-11 per-period series (booked arm)
        fold_counts = {f["fold_id"]: 0 for f in FOLDS_FROZEN}
        for t in trades:
            fold_counts[fold_of(t["entry_release_date"])] += 1
        fold_detail = {}
        for f in FOLDS_FROZEN:
            fid = f["fold_id"]
            n = fold_counts[fid]
            fold_detail[fid] = {
                "release_date_start": f["release_date_start"],
                "release_date_end": f["release_date_end"],
                "trades": n,
                "net_total_tier2_usd": fold_nets[fid],
                "expectancy_net_tier2_usd":
                    (fold_nets[fid] / n) if n else None,
            }
        counted_union = sorted(
            {d for v in counted_dates_by_pair.values() for d in v})
        session_of = session_maps
        per_pair_series = {}
        for pid in sorted(chains):
            rows = chains[pid]["rows"]
            dates = counted_dates_by_pair[pid]
            idx = _counted_window_indices(chains[pid])
            s_map = {rows[i]["release_date"].isoformat():
                     (rows[i]["decision_session"].isoformat()
                      if rows[i]["decision_session"] is not None else None)
                     for i in idx}
            per_pair_series[pid] = period_series(
                dates, s_map,
                [t for t, p in zip(trades, pair_of) if p == pid],
                [r for r, p in zip(canonical_rows, pair_of) if p == pid])
        pooled_series = period_series(
            counted_union, session_of, trades, canonical_rows)
        recon = {
            "law": "the persisted per-period series must reconcile with "
                   "the pooled kernel book (entry-attribution identity)",
            "ledger_net_total_tier_2_0":
                anchor["metrics"]["net_total_tier_2_0"],
            "series_final_cum_net_tier2_usd":
                pooled_series["final_cum_net_tier2_usd"],
            "match": bool(abs(
                anchor["metrics"]["net_total_tier_2_0"]
                - pooled_series["final_cum_net_tier2_usd"])
                <= 1e-9 * max(1.0, abs(
                    anchor["metrics"]["net_total_tier_2_0"] or 0.0))),
        }
        if not recon["match"]:
            raise ExecutionBroken(
                f"{arm_id}: P-11 per-period series fails to reconcile "
                f"with the pooled kernel book: {recon} (TECHABORT)")
        series_block = {
            "pooled": pooled_series,
            "per_pair": per_pair_series,
            "reconciliation_vs_kernel_book": recon,
            "decision_grid_disclosure": {
                "decision_periods_per_pair": len(counted_union),
                "counted_window_final_release_unmapped":
                    "2026-09-11 (no decision session, clock law; "
                    "disclosed by the committed P2 census; not a "
                    "decision period)",
            },
        }
        per_trade_records = [{
            "trade_id": t["trade_id"],
            "pair": pair_of[i],
            "leg": t["leg"],
            "direction": t["direction"],
            "notional_usd": t["notional_usd"],
            "entry_release_date": t["entry_release_date"],
            # terminal-policy legs carry no exit release date (the exit
            # is the last observable mark, not a release-mapped row):
            # None there is the honest record.
            "exit_release_date": t.get("exit_release_date"),
            "entry_session": t["entry_session"].isoformat(),
            "exit_session": t["exit_session"].isoformat(),
            "entry_price": t["entry_price"],
            "exit_price": t["exit_price"],
            "days_held": t["days_held"],
            "closed": t["closed"],
            "fold": fold_of(t["entry_release_date"]),
            "gross_usd": canonical_rows[i]["gross_pnl_usd"],
            "net_tier2_usd": canonical_rows[i]["canonical_pnl"],
        } for i, t in enumerate(trades)]

    # ---- compact pooled block for the artifact -------------------------- #
    pooled_out = {}
    for role in ALL_ROLES:
        entry = pooled[role]
        row = {
            "control_executable_verdict":
                entry["control_executable_verdict"],
            "declared_row": entry["declared_row"],
            "trades_booked": entry["trades_booked"],
            "fills": entry["fills"],
            "eligible_instants": entry["eligible_instants"],
        }
        if entry.get("metrics") is not None:
            row["metrics"] = scalar_metrics(entry["metrics"])
            row["net_totals_by_tier"] = entry["net_totals_by_tier"]
            row["gross_total"] = entry["gross_total"]
            row["costs_by_tier"] = entry["costs_by_tier"]
        pooled_out[role] = row

    per_pair_out = {}
    declared_rows = []
    for pid in sorted(per_pair_roles):
        per_pair_out[pid] = {}
        for role in ALL_ROLES:
            v = per_pair_roles[pid][role]
            row = dict(v)
            if v["control_executable_verdict"] == NOT_EXECUTABLE_VERDICT:
                declared_rows.append({
                    "pair": pid, "role": role,
                    "declared_row": v["declared_row"]})
            per_pair_out[pid][role] = row

    return {
        "arm_id": arm_id,
        "per_pair_roles": per_pair_out,
        "pooled_roles": pooled_out,
        "declared_rows": declared_rows,
        "coverage": coverage,
        "rules": rules_block,
        "evaluator_verdict": evaluator_verdict,
        "cell_verdict": cell_verdict,
        "killed_by": killed_by,
        "margins": margins,
        "fold_detail": fold_detail,
        "series": series_block,
        "per_trade_records": per_trade_records,
        "pooled_counted_instants": pooled_counted,
    }


def fills_of(trades: list) -> int:
    return sum(len(t["fills"]) for t in trades)


def margins_of(ev: dict, anchor_metrics: dict, pooled: dict) -> dict:
    """Per-rule margins of the verdict (P-2 margin law): every KILL or
    FAIL cites its measured margin."""
    rules = ev["rules"]
    r2 = {}
    for k, v in rules["R2"].items():
        km = pooled[k]["metrics"]
        a_t = anchor_metrics["per_trade_edge"]
        k_t = km["per_trade_edge"] if km else None
        a_d = anchor_metrics["per_decision_edge"]
        k_d = km["per_decision_edge"] if km else None
        r2[k] = {
            "kill": v["kill"],
            "v8_clause_fires": v["v8_clause"]["fires"],
            "falsification_clause_fires":
                v["falsification_clause"]["fires"],
            "v8_threshold_0_5x_anchor_per_trade":
                (0.5 * a_t) if a_t is not None else None,
            "killer_per_trade_edge": k_t,
            "anchor_per_trade_edge": a_t,
            "falsification_delta_per_decision":
                (k_d - a_d) if (k_d is not None and a_d is not None)
                else None,
            "killer_per_decision_edge": k_d,
            "anchor_per_decision_edge": a_d,
        }
    return {
        "R1_per_trade_edge": (rules["R1"].get("per_trade_edge")),
        "R3_positive_folds": rules["R3"]["positive_folds"],
        "R3_required": rules["R3"]["required"],
        "R3_fold_nets": {fid: v["net_total"]
                         for fid, v in rules["R3"]["folds"].items()},
        "R4_profit_factor": rules["R4"].get("profit_factor"),
        "R4_margin_above_1_10": rules["R4"].get("margin_above_1_10"),
        "R4_floor": 1.10,
        "R5_per_trade_edge": rules["R5"].get("per_trade_edge"),
        "R6_max_event_gross_share":
            rules["R6"].get("max_event_gross_share"),
        "R6_concentration_cap": rules["R6"].get("concentration_cap"),
        "R6_drop_one_fold": rules["R6"].get("drop_one_fold"),
        "R2_per_killer": r2,
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    started_utc = utcnow()
    t0 = time.time()
    incidents: list[dict] = []
    cells_written: list[dict] = []
    ledger_path = os.path.join(E_DIR, "execution_ledger.json")
    family_path = os.path.join(E_DIR, "family_verdicts.json")
    gate_path = os.path.join(E_DIR, "e_gate.json")
    lock = None
    status = "TECHABORT"
    note = ""

    head_sha = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    if head_sha != DISPATCH_SHA:
        raise SystemExit(
            f"FROZEN_SHA_MISMATCH: HEAD {head_sha} != dispatch BASE "
            f"{DISPATCH_SHA} (STOP)")
    if branch != BRANCH:
        raise SystemExit(
            f"FROZEN_SHA_MISMATCH: branch {branch!r} != {BRANCH!r} (STOP)")

    try:
        # -- machine-wide heavy lock (whole scored run) ------------------- #
        precheck = heavy_lock.inspect()
        if precheck["verdict"] != heavy_lock.VERDICT_FREE_PROVEN:
            raise heavy_lock.LockBusyError(
                f"pre-check verdict {precheck['verdict']}: "
                f"{precheck['reason']}")
        lock = heavy_lock.acquire(
            cycle_id=CYCLE_ID, role="E_SCORED", worktree=REPO,
            command=sys.argv,
            expected_artifacts=[
                os.path.join(E_DIR, f"cell_{a}.json") for a in CELL_IDS
            ] + [family_path, gate_path, ledger_path])
        lock_started = lock.owner["started_at"]

        # -- authority: the typed GO at this cycle's own gate ------------- #
        authority = load_authority(head_sha)
        lock.heartbeat(extra={"authority": "verified"})

        # -- evidence pins (freeze/p2/p1 vs the Z-R1 addendum) ------------ #
        pins = load_evidence_pins()
        with open(os.path.join(REPO, FREEZE_RELPATH),
                  encoding="utf-8") as fh:
            freeze = json.load(fh)
        with open(os.path.join(REPO, P2_RELPATH), encoding="utf-8") as fh:
            p2 = json.load(fh)
        with open(os.path.join(REPO, CONTRACT_RELPATH),
                  encoding="utf-8") as fh:
            contract = json.load(fh)

        # -- digest gate BEFORE any PnL ----------------------------------- #
        config = DRY.assemble_booked_arms(freeze)   # fail-closed on mismatch
        if not config["all_digests_match"] \
                or not config["digests_pairwise_distinct"]:
            raise ERefused("arm digest gate failed; fail closed")
        arms_by_id = {a["arm_id"]: a for a in
                      freeze["section2_arm_plan"]["arms"]
                      if a.get("selection_status") == "BOOKED"}
        if sorted(arms_by_id) != sorted(CELL_IDS):
            raise ERefused("booked arms != the 3 dispatch cells; fail closed")
        arm_digests_map = {a["arm_id"]: a["recorded_digest"]
                           for a in config["arms"]}

        # -- bookable set + leg constants --------------------------------- #
        bookable = DRY.bookable_pairs_of(freeze)
        codes = sorted({p.split("/")[0] for p in bookable})
        legs = sorted({p.split("/")[1] for p in bookable})
        boundaries_by_leg = {s: split_boundaries_of(contract, s)
                             for s in legs}
        leg_costs = {s: leg_cost_constants(contract, s) for s in legs}
        excluded_legs = list(
            freeze["section2_arm_plan"]["bookable_set"]
            ["excluded_transaction_only_legs"])

        etp_pins = p2.get("substrate_pins", {}).get("etp_eod_sha256", {})
        substrate = load_real_substrate(RUN_DIR, codes, legs, etp_pins)
        if not all(r["digest_match"] for r in substrate["plane_digest_rows"]):
            raise ERefused("plane digest mismatch; fail closed")
        if not all(r["etp_pin_match"] for r in substrate["etp_digest_rows"]):
            raise ERefused("ETP leg pin mismatch vs p2_gate; fail closed")

        # -- chains + census + Z-R2 parity -------------------------------- #
        built = build_and_verify_chains(
            bookable, substrate["cot_by_code"], substrate["leg_ctx"],
            p2["per_pair_census"], boundaries_by_leg,
            pins["zr2_chain_digests"])
        pair_rows, chains = built["pair_rows"], built["chains"]

        # -- Q-11 eligibility (300/pair; 3300 pooled) --------------------- #
        eligible_per_pair = {pid: int(prow["counted_instants"])
                             for pid, prow in pair_rows.items()}
        q11 = q11_eligibility(eligible_per_pair)
        if not q11["eligible_overall"]:
            raise ERefused("Q-11 eligibility failed; fail closed")

        # counted DECISION periods per pair (the 401 counted grid-
        # eligible instants: counted mask = mapped decision sessions)
        # + pooled session map.  The counted WINDOW's final release
        # (2026-09-11) is unmapped (no decision session, clock law;
        # disclosed by the committed P2 census) and is NOT a decision
        # period.
        counted_dates_by_pair = {}
        session_maps: dict[str, str | None] = {}
        for pid, chain in chains.items():
            idx = [i for i, c in enumerate(chain["counted"]) if c]
            counted_dates_by_pair[pid] = [
                chain["rows"][i]["release_date"].isoformat() for i in idx]
            for i in idx:
                d = chain["rows"][i]["release_date"].isoformat()
                s = chain["rows"][i]["decision_session"]
                if d in session_maps and session_maps[d] != (
                        s.isoformat() if s else None):
                    raise ERefused(
                        f"counted grid decision session mismatch at {d} "
                        f"({pid}); the counted release grid is not "
                        "pair-invariant; fail closed")
                session_maps[d] = s.isoformat() if s else None
        grids = {tuple(v) for v in counted_dates_by_pair.values()}
        if len(grids) != 1:
            raise ERefused("counted release grids differ across pairs; "
                           "fail closed")

        # -- the 3 scored cells, ONE AT A TIME (ARM1 -> ARM2 -> ARM3) ----- #
        cells = {}
        for arm_id in CELL_IDS:
            cell_t0 = time.time()
            arm = arms_by_id[arm_id]
            cells[arm_id] = execute_cell(
                arm, pair_rows, chains, substrate["leg_ctx"],
                boundaries_by_leg, leg_costs, counted_dates_by_pair,
                session_maps, lock)
            cells[arm_id]["runtime_seconds"] = \
                round(time.time() - cell_t0, 3)
            lock.heartbeat(extra={"cell_done": arm_id})

        # -- per-cell artifacts ------------------------------------------- #
        substrate_meta = {
            "freeze_sha256": pins["measured_sha256"]["freeze"],
            "addendum_sha256": pins["measured_sha256"]["addendum"],
            "p2_gate_sha256": pins["measured_sha256"]["p2_gate"],
            "p1_cost_contract_sha256":
                pins["measured_sha256"]["cost_contract"],
            "adjudication_sha256":
                pins["measured_sha256"]["adjudication"],
            "plane_digest_rows": substrate["plane_digest_rows"],
            "plane_entries_all_digest_ok": True,
            "etp_digest_rows": substrate["etp_digest_rows"],
            "etp_legs_all_pin_ok": True,
            "code_module_sha256": code_module_digests(),
            "chain_digest_parity_vs_zr2": {
                pid: prow["chain_structure_digest"]
                for pid, prow in pair_rows.items()},
        }
        for arm_id in CELL_IDS:
            cell = cells[arm_id]
            arm = arms_by_id[arm_id]
            payload = {
                "schema": "commodities_ng1_run/e_cell_scored@1",
                "cycle_id": CYCLE_ID,
                "task_id": TASK_ID,
                "lane": LANE,
                "arm_id": arm_id,
                "family": arm["family"],
                "arm_role": arm["role"],
                "parameters": arm["arm_config"]["parameters"],
                "arm_config_digest": {
                    "recorded": arm["arm_config_digest"],
                    "recomputed": DRY.arm_config_digest(arm["arm_config"]),
                    "match": bool(DRY.arm_config_digest(arm["arm_config"])
                                  == arm["arm_config_digest"]),
                },
                "identity": {
                    "dispatch_sha": DISPATCH_SHA,
                    "run_head_sha": head_sha,
                    "run_branch": branch,
                    "code_freeze": "the frozen runner bytes are digest-"
                                   "pinned in substrate_meta."
                                   "code_module_sha256",
                    "bookable_pairs": list(arm["arm_config"]
                                           ["bookable_pairs"]),
                    "bookable_pair_count":
                        len(arm["arm_config"]["bookable_pairs"]),
                    "excluded_transaction_only_legs": excluded_legs,
                    "counted_window": {
                        "first_counted_release": min(counted_dates_by_pair[
                            next(iter(counted_dates_by_pair))]),
                        "last_counted_release": max(counted_dates_by_pair[
                            next(iter(counted_dates_by_pair))]),
                        "decision_periods_per_pair":
                            len(next(iter(counted_dates_by_pair.values()))),
                        "pooled_counted_instants":
                            cell["pooled_counted_instants"],
                        "note": "counted releases 2019-01-04 .. "
                                "2026-09-11 per the committed P2 census; "
                                "the final counted-window release "
                                "2026-09-11 is unmapped (no decision "
                                "session) and is not a decision period; "
                                "the 401 mapped counted instants per "
                                "pair are the decision grid",
                    },
                },
                "execution": {
                    "started_utc": started_utc,
                    "cell_runtime_seconds": cell["runtime_seconds"],
                    "scored": True,
                    "real_pnl": True,
                    "heavy_lock": {
                        "mechanism": "machine-wide heavy lock "
                                     "(research/governance/heavy_lock.py)",
                        "cycle_id": CYCLE_ID, "role": "E_SCORED",
                        "worktree": REPO,
                        "started_at": lock_started,
                        "precheck": precheck["verdict"],
                    },
                },
                "budget_delta": {
                    "observed": 1,
                    "published": 1,
                    "note": "observed +1 at computation; published at "
                            "commit inclusion of this artifact (single "
                            "substance commit of the e/ directory; "
                            "commit sha recorded in the lane handoff)",
                },
                "f1_coverage_gate": cell["coverage"],
                "rules_r1_r6": cell["rules"],
                "evaluator_verdict": cell["evaluator_verdict"],
                "cell_verdict": cell["cell_verdict"],
                "killed_by": cell["killed_by"],
                "margins": cell["margins"],
                "fold_detail": cell["fold_detail"],
                "pooled_roles": cell["pooled_roles"],
                "per_pair_roles": cell["per_pair_roles"],
                "declared_not_executable_rows": [
                    dict(d, arm_id=arm_id) for d in cell["declared_rows"]],
                "per_period_series_p11": cell["series"],
                "per_trade_records_pooled_anchor": cell[
                    "per_trade_records"],
                "substrate_meta": substrate_meta,
                "disclosures": {
                    "f1_binding": F1_LAW,
                    "no_tuning": NO_TUNING_DECLARATION,
                    "period_series_convention": PERIOD_SERIES_CONVENTION,
                    "cost": "tier 2.0 PRIMARY; kernel tier-2.0 cost "
                            "exactly once per fill (2 fills per round "
                            "trip); Q-16 instrument drag accrued over "
                            "the held horizon, tier-independent; the 9 "
                            "transaction-only legs stay EXCLUDED",
                    "split_boundary": "holding windows spanning a "
                                      "committed share-base boundary are "
                                      "EXCLUDED and recorded "
                                      "(split-boundary law)",
                    "q11": "minima 300 eligible instants per bookable "
                           "pair, 3300 pooled (S freeze section2)",
                    "pbo": "PBO fail-closed NOT_RUN_CELLS_LT_8 (3 < 8); "
                           "the frozen alternative overfitting discipline "
                           "is the stage-A rule order R1-R6 per the "
                           "FOREX-NG1 precedent cited in the S freeze "
                           "(evaluated per booked cell in this run)",
                    "unbooked_cells": "3 of the 6 budget cells remain "
                                      "UNBOOKED (single-family cap); "
                                      "never padded; unused slots are "
                                      "never reassigned",
                },
            }
            path = os.path.join(E_DIR, f"cell_{arm_id}.json")
            sha = write_json(path, payload)
            cells_written.append({
                "arm_id": arm_id, "family_id": arm["family"],
                "role": arm["role"],
                "path": os.path.relpath(path, REPO), "sha256": sha,
                "cell_verdict": cell["cell_verdict"],
                "killed_by": cell["killed_by"],
                "evaluator_verdict": cell["evaluator_verdict"],
                "pooled_anchor_trades":
                    cell["pooled_roles"]["ANCHOR"]["trades_booked"],
                "declared_not_executable_rows":
                    len(cell["declared_rows"]),
            })
            lock.heartbeat(extra={"cell_written": arm_id})

        # -- family verdicts (per-cell SURVIVOR/KILL + per-pair detail) --- #
        fam_out = {
            "schema": "commodities_ng1_run/e_family_verdicts@1",
            "cycle_id": CYCLE_ID,
            "task_id": TASK_ID,
            "lane": LANE,
            "survivor_law":
                freeze["section3_stage_a_rules_r1_r6"]
                ["stage_a_rule_order_frozen"][-1],
            "f1_binding": F1_LAW,
            "no_tuning": NO_TUNING_DECLARATION,
            "pbo": pbo_verdict(3),
            "q11_eligibility": q11,
            "cells": {},
        }
        for arm_id in CELL_IDS:
            cell = cells[arm_id]
            per_pair_detail = {}
            for pid, roles in cell["per_pair_roles"].items():
                anchor_row = roles["ANCHOR"]
                per_pair_detail[pid] = {
                    "etp_leg": pair_rows[pid]["etp_leg"],
                    "cot_market_code": pair_rows[pid]["cot_market_code"],
                    "counted_instants":
                        pair_rows[pid]["counted_instants"],
                    "anchor_verdict":
                        anchor_row["control_executable_verdict"],
                    "anchor": anchor_row.get("metrics"),
                    "killers": {
                        r: roles[r].get("metrics")
                        for r in KILLER_ROLES},
                    "declared_not_executable_roles": sorted(
                        r for r in ALL_ROLES
                        if roles[r]["control_executable_verdict"]
                        == NOT_EXECUTABLE_VERDICT),
                }
            fam_out["cells"][arm_id] = {
                "arm_id": arm_id,
                "arm_role": arms_by_id[arm_id]["role"],
                "family": arms_by_id[arm_id]["family"],
                "arm_config_digest":
                    arms_by_id[arm_id]["arm_config_digest"],
                "cell_verdict": cell["cell_verdict"],
                "killed_by": cell["killed_by"],
                "evaluator_verdict": cell["evaluator_verdict"],
                "verdict_basis": (
                    "frozen R1-R6 (stage_a.evaluate_stage_a) on the "
                    "pooled family anchor book; R2 = V8 clause + the D1 "
                    "falsification rule over the 3 designated killers; "
                    "F1 coverage gate enforced BEFORE any verdict; "
                    "survivor := passes ALL rules -> "
                    "PROVISIONAL_STAGE_A_SURVIVOR (S1 SEALED; no rescue)"),
                "f1_coverage": {
                    "coverage_complete":
                        cell["coverage"]["coverage_complete"],
                    "missing_killers": cell["coverage"]["missing_killers"],
                },
                "margins": cell["margins"],
                "pooled_anchor": {
                    k: v for k, v in
                    cell["pooled_roles"]["ANCHOR"].items()
                    if k != "declared_row"},
                "per_pair_detail": per_pair_detail,
                "declared_not_executable_rows": [
                    dict(d, arm_id=arm_id) for d in cell["declared_rows"]],
            }
        fam_sha = write_json(family_path, fam_out)

        # -- e_gate.json --------------------------------------------------- #
        gate = {
            "schema": "commodities_ng1_run/e_gate@1",
            "cycle_id": CYCLE_ID,
            "task_id": TASK_ID,
            "lane": LANE,
            "measured_utc": utcnow(),
            "go": {
                "phrase": GO_PHRASE,
                "typed_at": "this cycle's own gate (adjudication commit "
                            f"{ADJUDICATION_COMMIT}, dispatch BASE "
                            f"{DISPATCH_SHA})",
                "authorized_by_audit": True,
                "adjudication_artifact": ADJUDICATION_RELPATH,
                "adjudication_artifact_sha256":
                    authority["adjudication_artifact_sha256"],
                "scope_reminder": authority["scope_reminder"],
            },
            "f1_coverage_enforcement": {
                "binding": F1_LAW,
                "enforced": True,
                "per_cell": {
                    arm_id: {
                        "coverage_complete":
                            cells[arm_id]["coverage"]["coverage_complete"],
                        "missing_killers":
                            cells[arm_id]["coverage"]["missing_killers"],
                        "gate_order": "coverage verified BEFORE any "
                                      "R1-R6 verdict recorded",
                    } for arm_id in CELL_IDS},
            },
            "lock": {
                "mechanism": "machine-wide heavy lock "
                             "(research/governance/heavy_lock.py)",
                "law": "the WHOLE scored run (3 cells, serialized) under "
                       "ONE lock acquisition; refusal would be "
                       "NOT_RUN_RESOURCE_CONFLICT, never contention",
                "precheck_verdict": precheck["verdict"],
                "precheck_reason": precheck["reason"],
                "cycle_id": CYCLE_ID,
                "role": "E_SCORED",
                "worktree": REPO,
                "started_at": lock_started,
                "release_status": "recorded at release (see "
                                  "execution_ledger.json + "
                                  "heavy_worker.history.jsonl)",
            },
            "budget": {
                "trial_budget_cells":
                    freeze["trial_accounting"]["trial_budget_cells"],
                "booked_cells": freeze["trial_accounting"]["booked_cells"],
                "observed_scored_cells": len(cells_written),
                "unbooked_cells":
                    freeze["trial_accounting"]["unbooked_cells"],
                "booked_arm_ids":
                    freeze["trial_accounting"]["booked_arm_ids"],
                "unbooked_policy":
                    freeze["trial_accounting"]["unbooked_policy"],
                "unused_slots_never_reassigned": True,
                "verdict": "3/6 observed + scored; 3 unbooked stay empty "
                           "(never padded)",
            },
            "no_tuning": {
                "declaration": NO_TUNING_DECLARATION,
                "parameters_source": "S freeze arms consumed VERBATIM "
                                     "(digests re-verified before any "
                                     "PnL; Z-R1 addendum "
                                     "no_parameter_tuning affirmation "
                                     "re-measured)",
                "digests_pairwise_distinct":
                    config["digests_pairwise_distinct"],
                "arm_config_digests": arm_digests_map,
            },
            "pbo": pbo_verdict(3),
            "q11_eligibility": q11,
            "digest_gates": {
                "evidence_pins": {
                    "measured": pins["measured_sha256"],
                    "pinned_by_addendum": pins["pinned_sha256"],
                    "mismatches": pins["digest_mismatches"],
                },
                "arm_digests_all_match": config["all_digests_match"],
                "chain_digest_parity_vs_zr2_all_match": True,
                "plane_entries_all_digest_ok": True,
                "etp_legs_all_pin_ok": True,
            },
            "structural_invariants": {
                "fills_2x_trades_every_pass_row": True,
                "dual_book_reconciliation_identity_every_pass_row": True,
                "declared_not_executable_rows_propagated_verbatim": True,
                "counted_grid_pair_invariant": True,
                "p11_series_reconciles_with_kernel_book": True,
            },
            "s1": "SEALED_UNTOUCHED",
            "cells": {row["arm_id"]: {
                "path": row["path"],
                "sha256": row["sha256"],
                "cell_verdict": row["cell_verdict"],
                "killed_by": row["killed_by"],
            } for row in cells_written},
            "family_verdicts": {
                "path": os.path.relpath(family_path, REPO),
                "sha256": fam_sha,
            },
            "recommended_next_action":
                "controller/owner review of the 3 scored cell verdicts; "
                "terminal phase consumes the verdicts verbatim (zero "
                "survivors = honest COMMODITIES_NG1_REJECT_ALL); S1 "
                "stays SEALED",
        }
        gate_sha = write_json(gate_path, gate)

        # -- execution ledger ---------------------------------------------- #
        elapsed = round(time.time() - t0, 3)
        execution_ledger = {
            "schema": "commodities_ng1_run/e_execution_ledger@1",
            "cycle_id": CYCLE_ID,
            "task_id": TASK_ID,
            "lane": LANE,
            "verdict": "FINISHED",
            "started_utc": started_utc,
            "ended_utc": utcnow(),
            "runtime_seconds": elapsed,
            "dispatch_sha": DISPATCH_SHA,
            "actual_start_sha": head_sha,
            "base_match": head_sha == DISPATCH_SHA,
            "branch": branch,
            "attempts": ATTEMPT_HISTORY,
            "authority": authority,
            "lock": {
                "mechanism": "machine-wide heavy lock "
                             "(research/governance/heavy_lock.py)",
                "cycle_id": CYCLE_ID, "role": "E_SCORED",
                "worktree": REPO,
                "started_at": lock_started,
                "precheck": precheck["verdict"],
                "release_status": "FINISHED (recorded at release)",
            },
            "cells": cells_written,
            "e_gate": {"path": os.path.relpath(gate_path, REPO),
                       "sha256": gate_sha},
            "family_verdicts": {
                "path": os.path.relpath(family_path, REPO),
                "sha256": fam_sha},
            "digest_gate": {
                "arm_digests_all_match": config["all_digests_match"],
                "digests_pairwise_distinct":
                    config["digests_pairwise_distinct"],
                "arm_config_digests": arm_digests_map,
                "evidence_pins_measured": pins["measured_sha256"],
                "evidence_pins_pinned": pins["pinned_sha256"],
                "code_module_sha256": substrate_meta["code_module_sha256"],
            },
            "grid": {
                "bookable_pairs": sorted(pair_rows),
                "bookable_pair_count": len(pair_rows),
                "counted_instants_per_pair": eligible_per_pair,
                "pooled_counted_instants": sum(
                    eligible_per_pair.values()),
                "counted_grid_pair_invariant": True,
            },
            "q11_eligibility": q11,
            "budget": gate["budget"],
            "s1": "SEALED_UNTOUCHED",
            "pnl_anywhere": True,
            "pnl_note": "scored lane: real after-cost PnL computed for "
                        "the 3 frozen cells across the 11 fully-costed "
                        "pairs through the frozen kernel (tier 2.0 once "
                        "per fill; Q-16 drag carried); the only phase "
                        "where outcome numbers are lawful",
            "incidents": incidents,
        }
        write_json(ledger_path, execution_ledger)
        status = "FINISHED"
        note = ("3/3 frozen cells scored under the heavy lock; artifacts "
                "under research/control/commodities_ng1_run/e/")
        print(json.dumps({
            "schema": "commodities_ng1_run/e_execution_ledger@1",
            "verdict": status,
            "cells": {r["arm_id"]: r["cell_verdict"]
                      for r in cells_written},
            "killed_by": {r["arm_id"]: r["killed_by"]
                          for r in cells_written},
            "declared_not_executable_rows_total": sum(
                r["declared_not_executable_rows"]
                for r in cells_written),
            "runtime_seconds": elapsed,
        }, indent=1, sort_keys=True))
        return 0

    except heavy_lock.LockBusyError as exc:
        status = "TECHABORT"
        note = f"NOT_RUN_RESOURCE_CONFLICT: {exc}"
        incidents.append({"id": "E-LOCK-CONFLICT", "detail": str(exc),
                          "verdict": "NOT_RUN_RESOURCE_CONFLICT"})
        print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT",
                          "detail": str(exc)}, indent=1))
        return 3
    except Exception as exc:                        # genuine technical failure
        status = "TECHABORT"
        note = f"{type(exc).__name__}: {exc}"
        incidents.append({
            "id": "E-TECHABORT",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc()[-2000:],
            "exposure": "cells computed before the failure are listed in "
                        "this process's stdout only; no rescue, no re-run "
                        "for outcomes",
        })
        try:
            write_json(ledger_path, {
                "schema": "commodities_ng1_run/e_execution_ledger@1",
                "cycle_id": CYCLE_ID, "task_id": TASK_ID, "lane": LANE,
                "verdict": "TECHABORT",
                "started_utc": started_utc, "ended_utc": utcnow(),
                "dispatch_sha": DISPATCH_SHA,
                "actual_start_sha": head_sha, "branch": branch,
                "cells": cells_written, "incidents": incidents,
                "error": note,
                "exposure": "partial ledger written by the exception "
                            "handler; per-cell verdicts stand as "
                            "computed, no re-run",
            })
        except Exception:
            pass
        print(f"E TECHABORT: {note}", file=sys.stderr)
        return 2
    finally:
        if lock is not None:
            try:
                lock.release(status=status, note=note)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
