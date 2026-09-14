"""COMMODITIES-NG1 Z SANITIZED DRY-RUN (prelaunch pipeline rehearsal).

Runs the exact 3 frozen cells (S freeze ``selection_freeze.json``, the
ANCHOR arm + 2 convention-neighbour arms) plus the FULL binding control
battery (3 designated killers + 2 diagnostics, S freeze section6) on the
REAL frozen substrate end-to-end through the I-phase runner machinery
(``research/assets/commodities_ng1/runners/``), as a prelaunch pipeline
rehearsal.

SANITIZATION LAW (binding for every committed artifact of this run):
committed artifacts record STRUCTURAL facts only -- decision counts,
fill counts, split-boundary-excluded trade counts, control-executable
PASS/FAIL, fold-partition counts, digest chains, provenance.  NO PnL,
NO expectancy, NO per-trade or aggregate outcome number is committed.
The outcome internals produced by the rehearsal (per-trade/per-decision
edges, ledger books, the falsification payload) are serialized
in-memory, hashed (sha256 of the freeze's canonical JSON) and
suppressed: only the digest is committed.  The strict scanner
(``sanitize_artifact``) refuses outcome-vocabulary keys AND any float
(a float cannot be a structural fact here; every structural fact is a
count, a date, a verdict, a status or a digest), fail-closed;
exception-derived free text is float-literal-scanned and violating
strings are suppressed to their sha256 (suppression recorded).

PLUMBING-FAILURE LAW: a defect of the runner machinery or the substrate
on the real data is REPORTED honestly (incident rows + verdict FAIL +
``blocked_prelaunch_candidate: true``) and NEVER repaired here: the
runners and the freeze are READ-ONLY at BASE.  A plumbing failure makes
the run a BLOCKED_PRELAUNCH candidate for the cycle owner to rule on; a
chain/census structural disagreement is reported as a
BLOCKED_DATA_OR_SELECTION candidate instead.

Counted-grid booking projection (frozen execution law, not a new
convention): decisions exist only on the counted grid
(``execute.decision_trades`` refuses any non-zero position on an
uncounted row), so every battery decision series is projected onto the
counted grid (identity on counted rows, flat elsewhere) before booking;
a still-open leg is closed by the kernel's frozen terminal policy at
the last observable mark.

Run modes:

- ``python research/control/commodities_ng1_run/z/z_run.py --run``:
  the REAL substrate via the P0 plane adapter (digest-verified),
  writing the sanitized per-cell manifests + ``z_report.json``;
- the tests run the same driver on SYNTHETIC loaders (no real
  substrate) and scan the committed artifacts for contamination.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

# .../research/control/commodities_ng1_run/z/z_run.py -> worktree root
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

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
    arm_metrics,
    book_ledger,
    decision_trades,
    trades_to_folds,
)
from research.assets.commodities_ng1.runners.stage_a import (  # noqa: E402
    FOLDS_FROZEN,
)
from research.assets.commodities_ng1.feasibility import (  # noqa: E402
    WARMUP_WEEKS,
    WINDOW_START,
)

SCHEMA_REPORT = "commodities_ng1_run/z_report@1"
SCHEMA_CELL = "commodities_ng1_run/z_cell_manifest@1"

CYCLE_ID = "COMMODITIES-NG1"
TASK_ID = "commodities-ng1-z-dryrun"

#: Base sha this lane is frozen on (dispatch packet BASE).
PACKET_BASE_SHA = "0a6969c9f1c3ba87b523c7c9203147e6a16d2320"

#: All roles the rehearsal must book per cell: the cell's own ANCHOR
#: arm plus the full binding battery (S freeze section6).
ALL_ROLES = ("ANCHOR",) + KILLER_ROLES + DIAGNOSTIC_ROLES

#: Runner/support modules whose exact bytes are digest-pinned as
#: provenance (the machinery this rehearsal executed).
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


class ZRefused(Exception):
    """Fail-closed Z refusal (digest mismatch, sanitizer violation,
    substrate blocked): nothing contaminated is ever emitted."""


class ZSanitizationRefused(ZRefused):
    """A committed artifact failed the sanitization scan; refused."""


# -- sanitization scanner ------------------------------------------------ #

#: Outcome vocabulary forbidden in ANY committed key (the I-phase
#: dry_run scanner's exact list, reused verbatim).
OUTCOME_VOCABULARY = DRY._OUTCOME_VOCABULARY

# Free-standing numeric literals only: word-boundary guards keep sha256
# hex digests and other identifier runs (which contain digit/e runs)
# from false-matching; a genuine number inside prose still matches.
_FLOAT_LITERAL = re.compile(
    r"(?<![\w.])-?\d+\.\d+(?![\w.])"
    r"|(?<![\w.])-?\d+[eE][-+]?\d+(?![\w.])")


def _has_float_literal(text: str) -> bool:
    return bool(_FLOAT_LITERAL.search(text))


def sanitize_artifact(obj, path: str = "$") -> None:
    """Strict fail-closed scan of a COMMITTED artifact.

    - no outcome-vocabulary key anywhere (I-phase no-PnL law, the
      dry_run scanner's list verbatim);
    - value types restricted to bool / int / str / None / list / dict:
      a FLOAT cannot be a structural fact in a Z artifact (every
      outcome number is a float; every structural fact here is a
      count, a date, a verdict, a status or a digest);
    - no float literal inside any string value (outcome numbers cannot
      hide in free text).
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            for bad in OUTCOME_VOCABULARY:
                if bad in kl:
                    raise ZSanitizationRefused(
                        f"committed artifact carries outcome-vocabulary "
                        f"key {path}.{k} (sanitization law)")
            sanitize_artifact(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            sanitize_artifact(v, f"{path}[{i}]")
    elif isinstance(obj, float):
        raise ZSanitizationRefused(
            f"committed artifact carries a float at {path} (sanitization "
            "law: only integer counts, verdicts, dates, digests)")
    elif isinstance(obj, str):
        if _has_float_literal(obj):
            raise ZSanitizationRefused(
                f"committed artifact carries a float literal in a string "
                f"at {path} (sanitization law)")
    elif isinstance(obj, (bool, int)) or obj is None:
        return
    else:
        raise ZSanitizationRefused(
            f"committed artifact carries value of disallowed type "
            f"{type(obj).__name__} at {path}")


def suppress_float_text(text: str) -> tuple[str, bool]:
    """Exception-derived free text: hash-suppress any float literal
    (the text may embed measured numbers; the digest keeps it
    verifiable without disclosure).  Returns (safe_text, suppressed)."""
    if not _has_float_literal(text):
        return text, False
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return (f"<suppressed-by-sanitizer sha256={digest}>", True)


def write_sanitized_json(path: str, obj) -> str:
    """Sanitize, serialize (sort_keys canonical law) and write; re-parse
    and re-scan the written bytes before returning the sha256 of the
    committed bytes."""
    sanitize_artifact(obj, os.path.basename(path))
    text = json.dumps(obj, indent=1, sort_keys=True) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(path, encoding="utf-8") as fh:
        reparsed = json.load(fh)
    sanitize_artifact(reparsed, os.path.basename(path) + ":reparsed")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# -- digests ------------------------------------------------------------- #

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_canonical(obj) -> str:
    return hashlib.sha256(
        DRY.canonical_json(obj).encode("utf-8")).hexdigest()


def code_module_digests(worktree: str) -> dict:
    out = {}
    for rel in CODE_MODULES:
        p = os.path.join(worktree, rel)
        out[rel] = sha256_file(p) if os.path.isfile(p) else "ABSENT"
    return out


def head_and_branch(worktree: str) -> dict:
    try:
        head = subprocess.run(
            ["git", "-C", worktree, "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
        branch = subprocess.run(
            ["git", "-C", worktree, "branch", "--show-current"],
            capture_output=True, text=True, check=True).stdout.strip()
    except Exception:                                   # pragma: no cover
        head, branch = "UNKNOWN", "UNKNOWN"
    return {"head_sha": head, "branch": branch,
            "packet_base_sha": PACKET_BASE_SHA,
            "head_matches_packet_base": bool(head == PACKET_BASE_SHA)}


# -- substrate loading (REAL mode) --------------------------------------- #

def load_real_substrate(run_dir: str, codes: list, legs: list,
                        etp_pins: dict) -> dict:
    """Consume the frozen substrate through the P0 plane adapter
    (authority verdict + sha256 digest verification, fail-closed) and
    return injectable substrate records + structural digest rows."""
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
            "csv_sha256_measured": res["sha256_measured"],
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
    """Kernel cost constants for ONE leg from the frozen contract:
    half-spread CS p90 per fill (once-per-fill charge law), measured
    expense, measured same-underlying tracking proxy where the contract
    declares one (None otherwise -- the kernel's declared-None path,
    disclosed structurally via the status strings)."""
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


# -- chain building + census --------------------------------------------- #

def _counted_window_indices(chain: dict) -> list:
    """Indices of the COUNTED-WINDOW rows (release_date >= WINDOW_START,
    past the warmup carve-out) -- the census scope.  A counted-window row
    whose decision session is unmapped is NOT counted by the chain mask
    (decisions exist only on mapped rows) but stays in this census
    scope, exactly mirroring ``verify_pair_census``."""
    rows = chain["rows"]
    window_rows = [i for i, r in enumerate(rows)
                   if r["release_date"] >= WINDOW_START]
    return window_rows[WARMUP_WEEKS:]


def build_and_verify_chains(bookable: list, cot_by_code: dict,
                            leg_ctx: dict, p2_per_pair_census: dict,
                            boundaries_by_leg: dict) -> dict:
    """Build each bookable pair's weekly chain and assert the fail-closed
    P2 census identity against the committed per-pair floor evaluation.
    Census/chain refusals are RECORDED (never repaired); the pair is
    marked structurally failed."""
    pairs = {}
    chains = {}
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
                raise ChainRefused(
                    f"pair {pid}: no CoT reports; fail closed")
            ctx = leg_ctx[symbol]
            chain = build_pair_chain(
                reports, ctx["session_dates"], ctx["session_closes"])
            row["chain_built"] = True
            chains[pid] = chain
            census_ref = p2_per_pair_census.get(pid, {}).get(
                "floor_evaluation")
            if census_ref is None:
                raise ChainRefused(
                    f"pair {pid}: no committed P2 census to verify "
                    "against; fail closed")
            census_ok = bool(verify_pair_census(pid, chain, census_ref))
            rule_counts: dict[str, int] = {}
            for r in chain["rows"]:
                rule_counts[r["rule_source"]] = \
                    rule_counts.get(r["rule_source"], 0) + 1
            unmapped_counted = sorted(
                chain["rows"][i]["release_date"].isoformat()
                for i in _counted_window_indices(chain)
                if chain["rows"][i]["decision_session"] is None)
            row.update({
                "chain_built": True,
                "census_identity_verified": census_ok,
                "cot_reports": len(reports),
                "etp_sessions": len(set(ctx["session_dates"])),
                "chain_rows": len(chain["rows"]),
                "counted_instants": int(sum(chain["counted"])),
                "rule_source_counts": rule_counts,
                "unmapped_counted_release_dates": unmapped_counted,
                "split_boundary_dates":
                    boundaries_by_leg.get(symbol, []),
                "chain_structure_digest": sha256_canonical([{
                    "report_date": r["report_date"].isoformat(),
                    "release_date": r["release_date"].isoformat(),
                    "rule_source": r["rule_source"],
                    "decision_session": r["decision_session"].isoformat()
                    if r["decision_session"] is not None else None,
                    "counted": bool(c),
                } for r, c in zip(chain["rows"], chain["counted"])]),
            })
        except Exception as exc:                # recorded, never repaired
            row["failure_class"] = type(exc).__name__
            row["failure_detail"] = suppress_float_text(str(exc))[0]
            chains.pop(pid, None)
        pairs[pid] = row
    return {"pair_rows": pairs, "chains": chains}


# -- one cell = one frozen arm over the bookable set ---------------------- #

def _project_to_counted_grid(positions: list, counted: list) -> list:
    """Frozen execution law: decisions exist only on the counted grid;
    the decision series is projected onto it before booking (identity on
    counted rows, flat elsewhere; open legs close by the terminal
    policy)."""
    return [float(p) if c else 0.0 for p, c in zip(positions, counted)]


def _failure_row(exc: Exception, stage: str) -> dict:
    safe, _ = suppress_float_text(str(exc))
    return {"control_executable_verdict": "FAIL",
            "failure_class": type(exc).__name__,
            "failure_stage": stage,
            "failure_detail": safe}


def _book_one(arm_id: str, pid: str, role: str, chain: dict, params: dict,
              symbol: str, leg_ctx_row: dict, boundaries: set,
              cost_constants: dict) -> dict:
    """End-to-end rehearsal of ONE (cell, pair, role): decision series
    -> counted-grid projection -> kernel booking -> fold partition ->
    E-phase metrics.  Returns structural rows + the suppressed outcome
    payload (hashed by the caller, never committed)."""
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
    structural = {
        "held_decision_count": int(held),
        "flat_decision_count": int(counted_n - held),
        "trades_booked": int(len(res["trades"])),
        "fills": int(res["fills"]),
        "split_boundary_excluded_trades":
            int(len(res["split_boundary_excluded"])),
        "unmapped_decision_rows": int(res["unmapped_rows"]),
    }
    booked = book_ledger(res["trades"], {symbol: cost_constants})
    ledger = booked["ledger"]           # the kernel dual-book ledger
    folds = trades_to_folds(res["trades"])
    fold_counts = {f["fold_id"]: int(len(folds[f["fold_id"]]))
                   for f in FOLDS_FROZEN}
    structural["fold_partition_counts"] = fold_counts
    structural["fold_partition_total_matches_trades"] = bool(
        sum(fold_counts.values()) == len(res["trades"]))
    structural["reconciliation_identity_ok"] = bool(
        booked["reconciliation"]["identity_ok"])
    structural["control_executable_verdict"] = "PASS"
    payload = {
        "arm_id": arm_id, "pair": pid, "role": role,
        "trades_booked": structural["trades_booked"],
        "arm_metrics": arm_metrics(ledger, eligible_instants=counted_n),
        "ledger_net_totals_by_tier": {
            t: ledger["net"][t]["total"] for t in ledger["net"]},
    }
    return {"structural": structural,
            "payload": payload,
            "trades": res["trades"]}


def execute_cell(arm: dict, pair_rows: dict, chains: dict, leg_ctx: dict,
                 boundaries_by_leg: dict, leg_costs: dict) -> dict:
    """Rehearse ONE frozen cell: every bookable pair x every battery
    role end-to-end, plus the pooled per-role books and the pooled
    falsification evaluation.  Emits the SANITIZED structural rows +
    the suppressed outcome payloads (hashed by the caller)."""
    arm_id = arm["arm_id"]
    params = arm["arm_config"]["parameters"]
    per_pair_roles: dict[str, dict] = {}
    pooled_trades: dict[str, list] = {role: [] for role in ALL_ROLES}
    for pid, prow in pair_rows.items():
        roles_out = {}
        chain = chains.get(pid)
        for role in ALL_ROLES:
            if not prow.get("chain_built") or chain is None:
                roles_out[role] = {
                    "control_executable_verdict": "FAIL",
                    "failure_class": "PAIR_CHAIN_UNAVAILABLE"
                    if not prow.get("chain_built")
                    else "PAIR_CENSUS_UNVERIFIED",
                    "failure_stage": "chain",
                    "failure_detail":
                        "pair structurally failed (see pair row); "
                        "booking refused fail-closed",
                }
                continue
            code, symbol = pid.split("/")
            boundaries = set(boundaries_by_leg.get(symbol, ()))
            try:
                booked = _book_one(arm_id, pid, role, chain, params,
                                   symbol, leg_ctx[symbol], boundaries,
                                   leg_costs[symbol])
                roles_out[role] = dict(
                    booked["structural"],
                    outcome_payload_sha256=sha256_canonical(
                        booked["payload"]))
                pooled_trades[role].extend(booked["trades"])
            except Exception as exc:            # reported, never repaired
                roles_out[role] = _failure_row(exc, "booking")
        per_pair_roles[pid] = roles_out

    # pooled per-role books (all pairs, all-leg frozen cost constants)
    pooled_rows = {}
    pooled_metrics = {}
    for role in ALL_ROLES:
        try:
            booked = book_ledger(pooled_trades[role], leg_costs)
            ledger = booked["ledger"]
            eligible = sum(prow.get("counted_instants", 0)
                           for prow in pair_rows.values()
                           if prow.get("chain_built"))
            pooled_metrics[role] = arm_metrics(
                ledger, eligible_instants=eligible)
            pooled_rows[role] = {
                "trades_booked": int(len(pooled_trades[role])),
                "fills": int(sum(len(t["fills"])
                                 for t in pooled_trades[role])),
                "eligible_instants": int(eligible),
                "reconciliation_identity_ok": bool(
                    booked["reconciliation"]["identity_ok"]),
                "control_executable_verdict": "PASS",
                "failure_class": None,
                "failure_stage": None,
                "failure_detail": None,
            }
        except Exception as exc:
            pooled_rows[role] = dict(
                _failure_row(exc, "pooled_booking"),
                trades_booked=int(len(pooled_trades[role])))
    if "ANCHOR" in pooled_metrics:
        cell_fals = falsification_eval(
            pooled_metrics["ANCHOR"],
            {r: pooled_metrics[r] for r in KILLER_ROLES
             if r in pooled_metrics})
    else:
        cell_fals = {"coverage_complete": False,
                     "missing_killers": list(KILLER_ROLES)}
    cell_payload = {"arm_id": arm_id, "scope": "POOLED",
                    "role_metrics": pooled_metrics,
                    "falsification_eval": cell_fals}
    pair_ok = all(
        prow.get("chain_built") and prow.get("census_identity_verified")
        for prow in pair_rows.values())
    roles_ok = all(
        v["control_executable_verdict"] == "PASS"
        for roles in per_pair_roles.values() for v in roles.values())
    pooled_ok = all(
        v["control_executable_verdict"] == "PASS"
        for v in pooled_rows.values())
    verdict = "PASS" if (pair_ok and roles_ok and pooled_ok) else "FAIL"
    return {
        "per_pair_roles": per_pair_roles,
        "pooled_rows": pooled_rows,
        "cell_payload": cell_payload,
        "cell_pipeline_executable_verdict": verdict,
    }


def cell_manifest(arm: dict, pair_rows: dict, cell: dict,
                  substrate_meta: dict) -> dict:
    """The SANITIZED per-cell manifest (structural facts only)."""
    params = arm["arm_config"]["parameters"]
    per_pair_out = {}
    totals = {"trades_booked_all_roles": 0, "fills_all_roles": 0,
              "split_boundary_excluded_trades_all_roles": 0,
              "held_decision_count_all_roles": 0}
    for pid, roles in cell["per_pair_roles"].items():
        prow = pair_rows[pid]
        per_pair_out[pid] = {
            "cot_market_code": prow["cot_market_code"],
            "etp_leg": prow["etp_leg"],
            "chain_rows": prow.get("chain_rows", 0),
            "counted_instants": prow.get("counted_instants", 0),
            "census_identity_verified": prow["census_identity_verified"],
            "rule_source_counts": prow.get("rule_source_counts", {}),
            "unmapped_counted_release_dates":
                prow.get("unmapped_counted_release_dates", []),
            "split_boundary_dates": prow.get("split_boundary_dates", []),
            "chain_structure_digest": prow.get("chain_structure_digest"),
            "pair_failure_class": prow["failure_class"],
            "roles": roles,
        }
        for v in roles.values():
            if v["control_executable_verdict"] == "PASS":
                totals["trades_booked_all_roles"] += \
                    v["trades_booked"]
                totals["fills_all_roles"] += v["fills"]
                totals["split_boundary_excluded_trades_all_roles"] += \
                    v["split_boundary_excluded_trades"]
                totals["held_decision_count_all_roles"] += \
                    v["held_decision_count"]
    failures = []
    for pid, roles in cell["per_pair_roles"].items():
        for role, v in roles.items():
            if v["control_executable_verdict"] != "PASS":
                failures.append({
                    "pair": pid, "role": role,
                    "failure_class": v["failure_class"],
                    "failure_stage": v["failure_stage"],
                    "failure_detail": v["failure_detail"],
                })
    for role, v in cell["pooled_rows"].items():
        if v["control_executable_verdict"] != "PASS":
            failures.append({
                "pair": "POOLED", "role": role,
                "failure_class": v["failure_class"],
                "failure_stage": v["failure_stage"],
                "failure_detail": v["failure_detail"],
            })
    manifest = {
        "schema": SCHEMA_CELL,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "item": "z_sanitized_cell_manifest",
        "law": "SANITIZED prelaunch rehearsal artifact: structural facts "
               "only (decision/fill/exclusion counts, control-executable "
               "verdicts, fold-partition counts, digest chains, "
               "provenance); outcome internals are hashed/suppressed",
        "arm_id": arm["arm_id"],
        "arm_role": arm["role"],
        "family": arm["family"],
        "arm_config_digest_recorded": arm["arm_config_digest"],
        "arm_config_digest_recomputed":
            DRY.arm_config_digest(arm["arm_config"]),
        "arm_config_digest_match": bool(
            DRY.arm_config_digest(arm["arm_config"])
            == arm["arm_config_digest"]),
        "parameters_integer_echo": {
            k: int(v) for k, v in params.items()
            if isinstance(v, int) and not isinstance(v, bool)},
        "parameters_fractional_pinned_by":
            "arm_config_digest (sha256 of the canonical JSON of the "
            "frozen arm_config; the fractional convention values "
            "(tails, trigger tau) are carried verbatim by the freeze "
            "and are NOT echoed here: the sanitization law forbids "
            "floats in committed Z artifacts)",
        "bookable_pairs": list(arm["arm_config"]["bookable_pairs"]),
        "bookable_pair_count": len(arm["arm_config"]["bookable_pairs"]),
        "substrate_digest_chains": substrate_meta,
        "per_pair": per_pair_out,
        "pooled_roles": cell["pooled_rows"],
        "totals": totals,
        "cell_failures": failures,
        "falsification_rehearsed": True,
        "cell_falsification_outcome_payload_sha256":
            sha256_canonical(cell["cell_payload"]),
        "cell_pipeline_executable_verdict":
            cell["cell_pipeline_executable_verdict"],
        "sanitization": {
            "scanner": "no outcome-vocabulary keys; no float values; "
                       "no float literals in strings (fail-closed)",
            "scanned": True,
        },
    }
    sanitize_artifact(manifest, arm["arm_id"])
    return manifest


# -- driver ---------------------------------------------------------------- #

def run_zdryun(freeze: dict, p2_gate: dict, cost_contract: dict,
               substrate: dict, out_dir: str, worktree: str,
               freeze_sha256: str | None = None,
               p2_sha256: str | None = None,
               contract_sha256: str | None = None) -> dict:
    """The Z sanitized dry-run over injectable substrate records.

    ``substrate``: {"cot_by_code", "leg_ctx" (session_dates/
    session_closes/etp_pin_match), "plane_digest_rows",
    "etp_digest_rows"}.  Writes the sanitized per-cell manifests into
    ``out_dir`` and returns the full result (the caller writes
    ``z_report.json`` via ``finish_report`` after attaching digests).
    """
    os.makedirs(out_dir, exist_ok=True)
    try:
        config = DRY.assemble_booked_arms(freeze)   # digest-verified
    except ValueError as exc:                       # fail-closed refusal
        raise ZRefused(
            f"config assembly refused against the binding freeze "
            f"(digest/trial-accounting law): {exc}") from exc
    arms = [a for a in freeze["section2_arm_plan"]["arms"]
            if a.get("selection_status") == "BOOKED"]
    bookable = DRY.bookable_pairs_of(freeze)
    legs = sorted({p.split("/")[1] for p in bookable})
    boundaries_by_leg = {s: split_boundaries_of(cost_contract, s)
                         for s in legs}
    leg_costs = {s: leg_cost_constants(cost_contract, s) for s in legs}
    etp_pins = (p2_gate.get("substrate_pins", {})
                .get("etp_eod_sha256", {}))
    for s in legs:
        if etp_pins and not substrate["leg_ctx"][s].get("etp_pin_match"):
            raise ZRefused(
                f"ETP leg {s}: measured bytes do not match the committed "
                "p2_gate substrate pin (BLOCKED_DATA: fail closed)")

    substrate_meta = {
        "freeze_sha256": freeze_sha256 or "NOT_MEASURED",
        "p2_gate_sha256": p2_sha256 or "NOT_MEASURED",
        "p1_cost_contract_sha256": contract_sha256 or "NOT_MEASURED",
        "plane_digest_rows": substrate["plane_digest_rows"],
        "plane_entries_all_digest_ok": bool(
            all(r["digest_match"]
                for r in substrate["plane_digest_rows"])),
        "etp_digest_rows": substrate["etp_digest_rows"],
        "etp_legs_all_pin_ok": bool(
            substrate["etp_digest_rows"]
            and all(r.get("etp_pin_match")
                    for r in substrate["etp_digest_rows"])),
        "code_module_sha256": code_module_digests(worktree),
    }

    built = build_and_verify_chains(bookable, substrate["cot_by_code"],
                                    substrate["leg_ctx"],
                                    p2_gate["per_pair_census"],
                                    boundaries_by_leg)
    pair_rows, chains = built["pair_rows"], built["chains"]

    eligible_per_pair = {pid: int(prow.get("counted_instants", 0))
                         for pid, prow in pair_rows.items()}
    q11 = q11_eligibility(eligible_per_pair)

    manifests = {}
    cells = {}
    for arm in arms:
        cell = execute_cell(arm, pair_rows, chains,
                            substrate["leg_ctx"], boundaries_by_leg,
                            leg_costs)
        mf = cell_manifest(arm, pair_rows, cell, substrate_meta)
        path = os.path.join(out_dir, f"cell_{arm['arm_id']}.json")
        manifests[arm["arm_id"]] = {
            "path": path,
            "sha256": write_sanitized_json(path, mf),
            "verdict": mf["cell_pipeline_executable_verdict"],
            "failures": mf["cell_failures"],
        }
        cells[arm["arm_id"]] = mf

    report = assemble_report(freeze, config, pair_rows, q11, manifests,
                             cells, substrate_meta, worktree)
    return {"report": report, "manifests": manifests, "cells": cells,
            "pair_rows": pair_rows, "q11": q11}


def _classify_incidents(cells: dict, pair_rows: dict) -> list:
    """Incident rows: every structural failure of the rehearsal,
    localized (arm / pair / role / stage / class), honestly reported."""
    incidents = []
    for arm_id, mf in cells.items():
        for f in mf["cell_failures"]:
            incidents.append(dict(f, arm_id=arm_id))
    for pid, prow in pair_rows.items():
        if not prow.get("chain_built"):
            incidents.append({
                "arm_id": "ALL", "pair": pid, "role": "CHAIN_CENSUS",
                "failure_stage": "chain",
                "failure_class": prow["failure_class"]
                or "CHAIN_UNAVAILABLE",
                "failure_detail": prow["failure_detail"],
            })
        elif not prow["census_identity_verified"]:
            incidents.append({
                "arm_id": "ALL", "pair": pid, "role": "CHAIN_CENSUS",
                "failure_stage": "chain",
                "failure_class": "CENSUS_IDENTITY_MISMATCH",
                "failure_detail": "reconstructed grid != committed P2 "
                                  "per-pair floor evaluation",
            })
    return incidents


def assemble_report(freeze, config, pair_rows, q11, manifests, cells,
                    substrate_meta, worktree) -> dict:
    """The SANITIZED aggregate report (the verdict is PLUMBING-only: a
    FAIL here is a fail-closed prelaunch finding, never an outcome
    statement)."""
    incidents = _classify_incidents(cells, pair_rows)
    machinery_failures = [i for i in incidents
                          if i.get("failure_stage") != "chain"]
    chain_failures = [i for i in incidents
                      if i.get("failure_stage") == "chain"]
    plumbing_ok = (
        config["all_digests_match"]
        and config["digests_pairwise_distinct"]
        and substrate_meta["plane_entries_all_digest_ok"]
        and substrate_meta["etp_legs_all_pin_ok"]
        and all(prow["chain_built"] and prow["census_identity_verified"]
                for prow in pair_rows.values())
        and all(m["verdict"] == "PASS" for m in manifests.values())
        and q11["eligible_overall"])
    verdict = "PASS" if plumbing_ok else "FAIL"
    report = {
        "schema": SCHEMA_REPORT,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "phase": "Z sanitized dry-run (prelaunch pipeline rehearsal)",
        "item": "z_report",
        "law": "SANITIZED aggregate: structural facts only; NO PnL, no "
               "expectancy, no per-trade or aggregate outcome numbers; "
               "outcome internals hashed/suppressed; plumbing failures "
               "reported honestly, never repaired (runners READ-ONLY)",
        "provenance": head_and_branch(worktree),
        "freeze": {
            "sha256": substrate_meta["freeze_sha256"],
            "frozen_at_utc": freeze["frozen_at_utc"],
            "single_family": freeze["section2_arm_plan"]["single_family"],
            "booked_arm_ids": freeze["trial_accounting"]["booked_arm_ids"],
        },
        "config_assembly": {
            "trial_budget_cells": config["trial_budget_cells"],
            "booked_cells": config["booked_cells"],
            "unbooked_cells": config["unbooked_cells"],
            "booked_arm_ids": config["booked_arm_ids"],
            "all_digests_match": config["all_digests_match"],
            "digests_pairwise_distinct":
                config["digests_pairwise_distinct"],
            "arm_config_digests": {
                a["arm_id"]: a["recorded_digest"]
                for a in config["arms"]},
        },
        "substrate_digest_chains": {
            k: substrate_meta[k] for k in (
                "freeze_sha256", "p2_gate_sha256",
                "p1_cost_contract_sha256", "plane_digest_rows",
                "plane_entries_all_digest_ok", "etp_digest_rows",
                "etp_legs_all_pin_ok", "code_module_sha256")},
        "grid": {
            "bookable_pairs": sorted(pair_rows),
            "bookable_pair_count": len(pair_rows),
            "counted_instants_per_pair": {
                pid: prow.get("counted_instants", 0)
                for pid, prow in pair_rows.items()},
            "pooled_counted_instants": sum(
                prow.get("counted_instants", 0)
                for prow in pair_rows.values()),
            "census_identity_all_verified": bool(
                all(prow["chain_built"]
                    and prow["census_identity_verified"]
                    for prow in pair_rows.values())),
            "rule_source_counts_pooled":
                _pooled_rule_sources(pair_rows),
            "unmapped_counted_release_dates_union": sorted({
                d for prow in pair_rows.values()
                for d in prow.get("unmapped_counted_release_dates", [])}),
        },
        "q11_eligibility": q11,
        "cells": {arm_id: {
            "manifest_sha256": manifests[arm_id]["sha256"],
            "cell_pipeline_executable_verdict":
                manifests[arm_id]["verdict"],
            "totals": cells[arm_id]["totals"],
            "cell_failure_count":
                len(manifests[arm_id]["failures"]),
        } for arm_id in cells},
        "incidents": incidents,
        "incident_count": len(incidents),
        "sanitization": {
            "law": "structural facts only; outcome internals "
                   "hashed/suppressed (sha256 of the canonical JSON)",
            "scanner": "no outcome-vocabulary keys; no float values; no "
                       "float literals in strings (fail-closed)",
            "committed_artifacts":
                [os.path.relpath(manifests[a]["path"], _REPO_ROOT)
                 for a in sorted(manifests)]
                + [os.path.relpath(
                    os.path.join(os.path.dirname(
                        manifests[sorted(manifests)[0]]["path"]),
                        "z_report.json"), _REPO_ROOT)],
            "scanned": True,
        },
        "overall_verdict": verdict,
        "fail_closed": True,
        "blocked_prelaunch_candidate": bool(verdict == "FAIL"
                                            and machinery_failures),
        "blocked_data_or_selection_candidate": bool(
            verdict == "FAIL" and chain_failures
            and not machinery_failures),
        "blocked_prelaunch_why":
            None if verdict != "FAIL" or not machinery_failures
            else "prelaunch rehearsal plumbing failure(s) of the runner "
                 "machinery on the real substrate: see incidents "
                 "(reported, not repaired; runners + freeze READ-ONLY "
                 "at BASE)",
        "recommended_next_action":
            "PASS: prelaunch rehearsal complete; E phase may proceed "
            "under the cycle's own gates"
            if verdict == "PASS" else
            "cycle owner rules on the BLOCKED_PRELAUNCH candidate: the "
            "incidents localize the machinery defects; repair belongs "
            "to an owner-authorized lane, never to this dry-run",
    }
    sanitize_artifact(report, "z_report")
    return report


def _pooled_rule_sources(pair_rows: dict) -> dict:
    out: dict[str, int] = {}
    for prow in pair_rows.values():
        for k, v in prow.get("rule_source_counts", {}).items():
            out[k] = out.get(k, 0) + int(v)
    return out


def finish_report(out_dir: str, result: dict) -> dict:
    """Write z_report.json sanitized; returns the final report dict."""
    path = os.path.join(out_dir, "z_report.json")
    digest = write_sanitized_json(path, result["report"])
    result["report"]["z_report_sha256"] = digest
    return result["report"]


# -- REAL-mode main -------------------------------------------------------- #

def load_real_context(run_dir: str) -> dict:
    with open(os.path.join(run_dir, "s", "selection_freeze.json"),
              encoding="utf-8") as fh:
        freeze = json.load(fh)
    with open(os.path.join(run_dir, "p2_gate.json"),
              encoding="utf-8") as fh:
        p2 = json.load(fh)
    with open(os.path.join(run_dir, "p1_cost_contract.json"),
              encoding="utf-8") as fh:
        contract = json.load(fh)
    return {"freeze": freeze, "p2": p2, "contract": contract,
            "freeze_sha256": sha256_file(os.path.join(
                run_dir, "s", "selection_freeze.json")),
            "p2_sha256": sha256_file(os.path.join(
                run_dir, "p2_gate.json")),
            "contract_sha256": sha256_file(os.path.join(
                run_dir, "p1_cost_contract.json"))}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--run" not in argv:
        print("usage: z_run.py --run", file=sys.stderr)
        return 2
    run_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(run_dir, "z")
    ctx = load_real_context(run_dir)
    freeze = ctx["freeze"]
    bookable = DRY.bookable_pairs_of(freeze)
    codes = sorted({p.split("/")[0] for p in bookable})
    legs = sorted({p.split("/")[1] for p in bookable})
    etp_pins = ctx["p2"].get("substrate_pins", {}).get("etp_eod_sha256", {})
    try:
        substrate = load_real_substrate(run_dir, codes, legs, etp_pins)
        result = run_zdryun(
            freeze, ctx["p2"], ctx["contract"], substrate, out_dir,
            worktree=_REPO_ROOT,
            freeze_sha256=ctx["freeze_sha256"],
            p2_sha256=ctx["p2_sha256"],
            contract_sha256=ctx["contract_sha256"])
    except ZRefused as exc:
        print(f"Z REFUSED (fail-closed; no artifacts emitted): {exc}",
              file=sys.stderr)
        return 3
    report = finish_report(out_dir, result)
    print(json.dumps({
        "schema": report["schema"],
        "overall_verdict": report["overall_verdict"],
        "blocked_prelaunch_candidate":
            report["blocked_prelaunch_candidate"],
        "incident_count": report["incident_count"],
        "pooled_counted_instants":
            report["grid"]["pooled_counted_instants"],
        "q11_eligible_overall":
            report["q11_eligibility"]["eligible_overall"],
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
