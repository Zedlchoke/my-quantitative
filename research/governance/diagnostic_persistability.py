"""Diagnostic persistability gate — prove BEFORE launch that the terminal
will be able to answer everything, because the runner persisted it.

Why this gate exists (owner amendment 2026-09-07):

- V3R (forex): at terminal, DSR/PBO were NOT_RUN fail-closed — "no
  per-period series in the program ledger". The runner had never
  persisted per-period returns, so the statistic that prices multiple
  testing was unreachable on the exact family that needed it most.
- V15 (crypto): the frozen output contract carried no per-period-returns
  fields (measured at the p3 freeze); at terminal: gates G6-G9 NOT_RUN
  for absent per-symbol diagnostics, DSR/PBO NOT_RUN, and a terminal
  rerun producing a metadata TECHABORT (A7 terminal APPROVED_0_FAIL).

Gate position: BEFORE A7 launch authorization. A run contract that
reaches A7 without a passing diagnostic contract is BLOCKED_PRELAUNCH —
the A1 must remediate the contract, not the auditor.

Round-2 hardening (owner remediation 2026-09-07):

1. **Canonical schemas.** ``CATEGORY_REQUIRED_FIELDS`` fixes the required
   fields per diagnostic category; a contract CANNOT pick an arbitrary
   field list — its declared ``required_fields`` must EQUAL the canon
   (set-equality). ``schema_id`` must be the REGISTERED id for that
   category (``diag/<category>@1``); unregistered ids are rejected.
2. **Fresh-emission proof.** Artifact paths must be RELATIVE, contain no
   ``..`` and no absolute components; the smoke test always runs the
   driver inside a NEW, EMPTY sandbox directory it creates itself (under
   ``sandbox_root`` when given), so artifacts that existed before the
   driver ran can never satisfy the gate — a no-op driver cannot PASS on
   stale outputs.
3. The smoke test parses every emitted artifact and verifies content:
   required fields per record, identity match against the contract's
   ``cycle_id``, and non-empty / non-all-null series.

Contract format (a ``diagnostic_output_contract`` block inside the run
contract)::

    {
      "cycle_id": "STOCKS-FREE-V12",
      "asset": "stocks",
      "multiple_testing_accounting": true,
      "calendar_conditioned": false,
      "confirmatory_entry_declared": false,
      "outputs": {
        "per_period_series": {
          "persist": true,
          "artifact": "artifacts/per_period_series.jsonl",
          "schema_id": "diag/per_period_series@1",
          "format": "jsonl"
        },
        ...
      },
      "conditional": {
        "dsr_per_period_series": {
          "applicability": "multiple_testing_accounting",
          "persist": true,
          "artifact": "artifacts/dsr_per_period_series.jsonl",
          "schema_id": "diag/dsr_per_period_series@1",
          "format": "jsonl"
        }
      }
    }

Verdicts:
  DIAGNOSTIC_CONTRACT_PASS   every mandatory category persisted with a
                             complete, canon-conforming block; every
                             conditional either persisted or provably
                             not-applicable under its FROZEN predicate
  BLOCKED_PRELAUNCH          anything missing, malformed, unsafe, or an
                             empty derived artifact list; findings name
                             the gap

A conditional that is absent without a frozen applicability predicate is
a finding — "NOT_RUN for convenience" is exactly what this gate exists
to refuse. Adoption boundary (FAMILY_PIPELINE.md §11): cycles whose
plans preregister this gate (crypto V16+, forex V7+, stocks V12+);
frozen/running cycles are NOT retrofitted.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Optional

GATE_ID = "DIAGNOSTIC_PERSISTABILITY"

PASS = "DIAGNOSTIC_CONTRACT_PASS"
BLOCKED = "BLOCKED_PRELAUNCH"

FORMATS = {"json", "jsonl"}

# Canonical required fields per diagnostic category (owner remediation
# round 2): contracts conform, they do not choose.
CATEGORY_REQUIRED_FIELDS: dict[str, list[str]] = {
    "identity": [
        "cycle_id", "family_id", "arm_id", "arm_config_digest",
        "data_snapshot_digest", "code_freeze_sha", "cost_tier",
    ],
    "per_period_series": ["cycle_id", "arm_id", "period", "returns"],
    "per_symbol_breakdown": ["cycle_id", "symbol", "contribution_pnl"],
    "per_fold_breakdown": ["cycle_id", "fold_id", "pnl", "population"],
    "stress_tiers": ["cycle_id", "tier", "pnl"],
    "drop_one_inputs": ["cycle_id", "omitted_symbol", "pnl"],
    "benchmark_context": ["cycle_id", "fold_id", "benchmark", "excess_return"],
    "margins_to_fail": ["cycle_id", "gate_id", "value", "threshold", "margin"],
    "counters": ["observed_delta", "published_delta", "budget_used", "reruns_not_trials"],
    "reproduction_inputs": ["code_freeze_sha", "data_manifest_sha", "sanitized"],
}

CONDITIONAL_REQUIRED_FIELDS: dict[str, list[str]] = {
    "dsr_per_period_series": ["cycle_id", "period", "returns"],
    "sham_control_calendar": ["cycle_id", "arm_id", "calendar"],
    "financing_dual_books": ["cycle_id", "book", "pnl"],
    "confirmatory_status_binding": ["cycle_id", "arm_id", "status"],
}

# Every category/conditional registers exactly one schema id; contracts
# must cite it — schema_id resolves to a REGISTERED schema or the block
# is rejected.
REGISTERED_SCHEMAS: dict[str, str] = {
    **{cat: f"diag/{cat}@1" for cat in CATEGORY_REQUIRED_FIELDS},
    **{name: f"diag/{name}@1" for name in CONDITIONAL_REQUIRED_FIELDS},
}

# Terminal questions every scored cycle must be able to answer from
# persisted bytes (why-text per category).
MANDATORY_CATEGORIES: dict[str, str] = {
    "identity": "trial identity on every record (handbook §13.1)",
    "per_period_series": "DSR, PBO and every per-period statistic die "
    "without it (V3R)",
    "per_symbol_breakdown": "concentration, drop-one, symbol-attribution "
    "gates (V15 gap)",
    "per_fold_breakdown": "per-fold PnL, population and populated-fold flags",
    "stress_tiers": "stress books per tier applied to booked PnL",
    "drop_one_inputs": "inputs sufficient to rerun drop-one-symbol/instrument",
    "benchmark_context": "SPY/sector benchmark excess per fold",
    "margins_to_fail": "distance to failure threshold for EVERY frozen gate (P-2)",
    "counters": "observed/published deltas, budget, reruns-not-trials accounting",
    "reproduction_inputs": "freeze sha + data manifest + sanitized flags the "
    "twin needs to re-emit the same diagnostics",
}

# Conditionals: name -> (frozen applicability expression, why)
CONDITIONAL_DIAGNOSTICS: dict[str, tuple[str, str]] = {
    "dsr_per_period_series": (
        "multiple_testing_accounting",
        "DSR over the cumulative trial count needs per-period returns "
        "(V3R: NOT_RUN fail-closed without them)",
    ),
    "sham_control_calendar": (
        "calendar_conditioned",
        "calendar-conditioned mechanisms carry a mandatory sham-calendar/"
        "sham-event placebo (V5 lesson)",
    ),
    "financing_dual_books": (
        "asset == 'forex'",
        "price-only AND financing-adjusted books, frozen formula",
    ),
    "confirmatory_status_binding": (
        "confirmatory_entry_declared",
        "confirmatory cells bind their status in every record (V14 OICYC)",
    ),
}


def _artifact_path_ok(path: Any) -> bool:
    if not isinstance(path, str) or not path:
        return False
    p = PurePosixPathSafe(path)
    return not p.is_absolute and ".." not in p.parts and "" not in p.parts


class PurePosixPathSafe:
    """Minimal path-shape check without filesystem access."""

    def __init__(self, raw: str):
        self.raw = raw
        self.is_absolute = raw.startswith("/") or (len(raw) > 1 and raw[1] == ":")
        self.parts = [seg for seg in raw.replace("\\", "/").split("/") if seg != ""]


def _canon_for(category: str) -> Optional[list[str]]:
    if category in CATEGORY_REQUIRED_FIELDS:
        return CATEGORY_REQUIRED_FIELDS[category]
    return CONDITIONAL_REQUIRED_FIELDS.get(category)


def _block_problems(category: str, block: Any) -> list[str]:
    """Complete, canon-conforming, path-safe block or a list of problems."""
    problems: list[str] = []
    if not isinstance(block, dict):
        return [f"{category}: block must be an object"]
    if not block.get("persist"):
        problems.append(f"{category}: not persisted")
    artifact = block.get("artifact")
    if not _artifact_path_ok(artifact):
        problems.append(
            f"{category}: unsafe artifact path {artifact!r} — must be relative, "
            f"no '..', no absolute components"
        )
    schema_id = block.get("schema_id")
    registered = REGISTERED_SCHEMAS.get(category)
    if not isinstance(schema_id, str) or not schema_id:
        problems.append(f"{category}: schema_id missing")
    elif schema_id != registered:
        problems.append(
            f"{category}: schema_id {schema_id!r} does not resolve to the "
            f"registered schema {registered!r}"
        )
    fmt = block.get("format")
    if fmt not in FORMATS:
        problems.append(f"{category}: format must be one of {sorted(FORMATS)}")
    declared = block.get("required_fields")
    canon = _canon_for(category)
    if canon is None:
        problems.append(f"{category}: unknown category (no canonical schema)")
    elif declared is not None and sorted(declared) != sorted(canon):
        # Round 2: the canon IS the contract — a declared list that
        # differs from the canonical set is rejected, a missing list
        # simply means the canon applies (verification always uses canon).
        problems.append(
            f"{category}: required_fields are not the canonical set "
            f"{sorted(canon)} (got {sorted(declared)})"
        )
    return problems


def _asset_flags() -> frozenset[str]:
    return frozenset(
        {"multiple_testing_accounting", "calendar_conditioned", "confirmatory_entry_declared"}
    )


def _eval_applicability(expr: str, contract: dict) -> tuple[bool, str]:
    """Evaluate a frozen boolean expression of the form ``flag`` or
    ``asset == 'x'`` against the contract header."""
    if expr in _asset_flags():
        return bool(contract.get(expr)), f"flag {expr}={bool(contract.get(expr))}"
    if expr.startswith("asset == "):
        want = expr.split("==", 1)[1].strip().strip("'\"")
        got = contract.get("asset")
        return got == want, f"asset {got!r} vs {want!r}"
    return False, f"unparseable frozen expression {expr!r}"


def validate_contract(contract: dict) -> tuple[str, list[dict]]:
    """Return (verdict, findings). findings carry gate/category/severity."""
    findings: list[dict] = []

    def flag(category: str, severity: str, detail: str):
        findings.append(
            {"gate": GATE_ID, "category": category, "severity": severity, "detail": detail}
        )

    if not isinstance(contract, dict):
        return BLOCKED, [{"gate": GATE_ID, "category": "contract", "severity": "HIGH",
                          "detail": "contract must be an object"}]
    outputs = contract.get("outputs")
    if not isinstance(outputs, dict):
        flag("outputs", "HIGH", "missing outputs block entirely")
        return BLOCKED, findings
    if not outputs:
        flag("outputs", "HIGH", "EMPTY artifact contract — nothing would be persisted")

    for category, why in MANDATORY_CATEGORIES.items():
        block = outputs.get(category)
        for problem in _block_problems(category, block):
            flag(category, "HIGH", f"{problem} ({why})")

    conditional = contract.get("conditional", {})
    if not isinstance(conditional, dict):
        flag("conditional", "HIGH", "conditional block must be an object")
        conditional = {}
    for name in set(conditional) - set(CONDITIONAL_DIAGNOSTICS):
        flag(name, "MEDIUM", f"unknown conditional diagnostic {name!r} (not in spec)")
    for name, (expr, why) in CONDITIONAL_DIAGNOSTICS.items():
        if name not in conditional:
            continue
        block = conditional[name]
        if not isinstance(block, dict) or "applicability" not in block:
            flag(name, "HIGH",
                 f"conditional present without a FROZEN applicability predicate — "
                 f"NOT_RUN-for-convenience is refused ({why})")
            continue
        applies, note = _eval_applicability(str(block["applicability"]), contract)
        for problem in _block_problems(name, block):
            flag(name, "HIGH" if applies else "LOW", problem)
        if not applies and block.get("persist"):
            flag(name, "LOW", f"conditional persisted though frozen predicate says "
                              f"not applicable ({note})")

    # A conditional that is NOT declared and whose frozen predicate would
    # apply is a gap: the cycle must declare it.
    for name, (expr, why) in CONDITIONAL_DIAGNOSTICS.items():
        if name in conditional:
            continue
        applies, note = _eval_applicability(expr, contract)
        if applies:
            flag(name, "HIGH",
                 f"conditional applies ({note}) but is not declared in the "
                 f"contract ({why})")

    verdict = PASS if not any(f["severity"] == "HIGH" for f in findings) else BLOCKED
    return verdict, findings


def expected_artifacts_from_contract(contract: dict) -> tuple[list[dict], list[str]]:
    """Derive the artifact list from the contract itself (mandatory +
    persisted-and-applicable conditionals). An empty derivation is a
    problem, not a pass. Each spec carries the CANONICAL required fields
    and registered schema id — never the contract's own guess."""
    artifacts: list[dict] = []
    problems: list[str] = []
    for category, block in (contract.get("outputs") or {}).items():
        if isinstance(block, dict) and block.get("persist") and _artifact_path_ok(block.get("artifact")):
            canon = _canon_for(category)
            artifacts.append({
                "category": category,
                "artifact": block["artifact"],
                "format": block.get("format", "jsonl"),
                "required_fields": list(canon) if canon else [],
                "schema_id": REGISTERED_SCHEMAS.get(category),
            })
    for name, block in (contract.get("conditional") or {}).items():
        if not isinstance(block, dict) or "applicability" not in block:
            continue
        applies, _ = _eval_applicability(str(block["applicability"]), contract)
        if applies and block.get("persist") and _artifact_path_ok(block.get("artifact")):
            canon = _canon_for(name)
            artifacts.append({
                "category": name,
                "artifact": block["artifact"],
                "format": block.get("format", "jsonl"),
                "required_fields": list(canon) if canon else [],
                "schema_id": REGISTERED_SCHEMAS.get(name),
            })
    if not artifacts:
        problems.append("derived artifact list is EMPTY — nothing to verify")
    return artifacts, problems


def _verify_artifact(spec: dict, contract: dict, sandbox: Path) -> list[str]:
    """Parse the artifact INSIDE the sandbox and verify content: canon
    fields per record, identity match, non-empty series."""
    problems: list[str] = []
    category = spec["category"]
    rel = spec["artifact"]
    path = sandbox / rel
    if not path.exists():
        return [f"{category}: artifact {rel} not emitted"]

    required = spec.get("required_fields") or []
    fmt = spec.get("format", "jsonl")

    if fmt == "jsonl":
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            return [f"{category}: artifact {rel} is EMPTY (zero records)"]
        records = []
        for i, ln in enumerate(lines, 1):
            try:
                records.append(json.loads(ln))
            except json.JSONDecodeError as exc:
                problems.append(f"{category}: line {i} is not valid JSON ({exc})")
        for i, rec in enumerate(records, 1):
            for field in required:
                if field not in rec:
                    problems.append(f"{category}: record {i} missing field {field!r}")
        if "cycle_id" in required:
            for i, rec in enumerate(records, 1):
                if rec.get("cycle_id") != contract.get("cycle_id"):
                    problems.append(
                        f"{category}: record {i} identity mismatch "
                        f"{rec.get('cycle_id')!r} != {contract.get('cycle_id')!r}"
                    )
        if category.endswith("_series") and records:
            for field in required:
                if all(rec.get(field) is None for rec in records):
                    problems.append(
                        f"{category}: required column {field!r} is all-null "
                        f"across {len(records)} records"
                    )
    else:  # json
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return [f"{category}: artifact {rel} is not valid JSON ({exc})"]
        if not isinstance(data, dict):
            return [f"{category}: artifact {rel} must be a JSON object"]
        for field in required:
            if field not in data:
                problems.append(f"{category}: missing field {field!r}")
        if "cycle_id" in required and data.get("cycle_id") != contract.get("cycle_id"):
            problems.append(
                f"{category}: identity mismatch {data.get('cycle_id')!r} != "
                f"{contract.get('cycle_id')!r}"
            )
        if category.endswith("_series") and not data:
            problems.append(f"{category}: artifact {rel} is EMPTY")
    return problems


def smoke_check_twin_rerun(
    run_command: list[str],
    contract: dict,
    *,
    sandbox_root: Optional[Path] = None,
    timeout: int = 600,
) -> tuple[str, list[str]]:
    """Terminal-A7 smoke test on the twin, fresh-emission hardened:

    1. the contract must pass :func:`validate_contract` first;
    2. the artifact list is DERIVED from the contract (canon fields,
       registered schemas);
    3. a NEW EMPTY sandbox directory is created (under ``sandbox_root``
       when given) and the driver runs with the sandbox as its cwd —
       artifacts that existed before the run can never satisfy the gate;
    4. every artifact is parsed and verified for content: canon fields,
       identity match, non-empty series.

    Returns (verdict, problems).
    """
    import subprocess

    verdict, findings = validate_contract(contract)
    if verdict != PASS:
        return BLOCKED, [f"contract invalid before smoke: {f['category']}: {f['detail']}"
                         for f in findings if f["severity"] == "HIGH"] or ["contract invalid"]

    artifacts, problems = expected_artifacts_from_contract(contract)
    if problems:
        return BLOCKED, problems

    sandbox = Path(tempfile.mkdtemp(prefix="diag_smoke_", dir=sandbox_root))
    if any(sandbox.iterdir()):
        return BLOCKED, ["sandbox not empty at creation — refusing to run"]

    try:
        proc = subprocess.run(
            run_command, cwd=sandbox, timeout=timeout, capture_output=True, text=True
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return BLOCKED, [f"twin smoke run failed to execute: {exc}"]
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-5:]
        return BLOCKED, [f"twin smoke run exit {proc.returncode}: {tail}"]

    for spec in artifacts:
        problems.extend(_verify_artifact(spec, contract, sandbox))
    return (PASS if not problems else BLOCKED), problems
