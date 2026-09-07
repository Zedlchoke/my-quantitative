"""Diagnostic persistability gate — prove BEFORE launch that the terminal
will be able to answer everything, because the runner persisted it.

Why this gate exists (owner amendment 2026-09-07):

- V3R (forex): at terminal, DSR/PBO were NOT_RUN fail-closed — "no
  per-period series in the program ledger". The runner had never
  persisted per-period returns, so the statistic that prices multiple
  testing was unreachable on the exact family that needed it most.
- V15 (crypto): the frozen output contract carried no per-period-returns
  fields (measured at the p3 freeze); at terminal: gates G6-G9 NOT_RUN
  for absent per-period returns, DSR/PBO NOT_RUN, and a terminal rerun
  producing a metadata TECHABORT.

Gate position: BEFORE A7 launch authorization. A run contract that
reaches A7 without a passing diagnostic contract is BLOCKED_PRELAUNCH —
the A1 must remediate the contract, not the auditor.

Contract format (a ``diagnostic_output_contract`` block inside the run
contract). Hardened per owner remediation 2026-09-07: every persisted
output declares its ``schema_id``, ``format`` (json|jsonl) and
``required_fields``; the smoke test's artifact list is DERIVED from the
validated contract (never hand-picked), and the smoke test parses and
verifies artifact CONTENT — identity match and non-empty series — not
mere existence::

    {
      "cycle_id": "STOCKS-FREE-V12",
      "asset": "stocks",
      "mechanism_class": "event_conditioned",
      "multiple_testing_accounting": true,
      "outputs": {
        "per_period_series": {
          "persist": true,
          "artifact": "artifacts/per_period_series.jsonl",
          "schema_id": "diag/per_period_series@1",
          "format": "jsonl",
          "required_fields": ["cycle_id", "arm_id", "period", "returns"]
        },
        ...
      },
      "conditional": {
        "dsr_per_period_series": {
          "applicability": "multiple_testing_accounting",
          "persist": true,
          "artifact": "artifacts/dsr_series.jsonl",
          "schema_id": "diag/dsr_series@1",
          "format": "jsonl",
          "required_fields": ["cycle_id", "period", "returns"]
        }
      }
    }

Verdicts:
  DIAGNOSTIC_CONTRACT_PASS   every mandatory category persisted with a
                             complete block; every conditional either
                             persisted or provably not-applicable under
                             its FROZEN predicate
  BLOCKED_PRELAUNCH          anything missing, malformed, or an empty
                             derived artifact list; findings name the gap

A conditional that is absent without a frozen applicability predicate is
a finding — "NOT_RUN for convenience" is exactly what this gate exists
to refuse. Adoption boundary (FAMILY_PIPELINE.md §11): cycles whose
plans preregister this gate (crypto V16+, forex V7+, stocks V12+);
frozen/running cycles are NOT retrofitted.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

GATE_ID = "DIAGNOSTIC_PERSISTABILITY"

PASS = "DIAGNOSTIC_CONTRACT_PASS"
BLOCKED = "BLOCKED_PRELAUNCH"

FORMATS = {"json", "jsonl"}

# Terminal questions every scored cycle must be able to answer from
# persisted bytes. Each entry: (category, why).
MANDATORY_CATEGORIES: dict[str, str] = {
    "identity": "cycle/family/arm/arm_config_digest/data_snapshot_digest/"
    "code_freeze_sha/cost_tier on every record — trial identity (handbook §13.1)",
    "per_period_series": "per-period decision/position/returns series — DSR, PBO "
    "and every per-period statistic die without it (V3R)",
    "per_symbol_breakdown": "per-symbol/per-instrument leg contributions — "
    "concentration, drop-one, symbol-attribution gates (V15 gap)",
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


def _block_ok(block: Any) -> bool:
    """A persisted output block is complete only with schema_id, format
    and required_fields — existence alone is not a contract."""
    if not isinstance(block, dict):
        return False
    if not block.get("persist"):
        return False
    artifact = block.get("artifact")
    schema_id = block.get("schema_id")
    required = block.get("required_fields")
    fmt = block.get("format")
    return (
        isinstance(artifact, str)
        and bool(artifact)
        and isinstance(schema_id, str)
        and bool(schema_id)
        and isinstance(required, list)
        and bool(required)
        and all(isinstance(f, str) and f for f in required)
        and fmt in FORMATS
    )


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
        if not _block_ok(block):
            flag(category, "HIGH",
                 f"mandatory diagnostic not persisted as a complete block "
                 f"(persist/artifact/schema_id/format/required_fields) ({why})")

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
        if applies and not _block_ok(block):
            flag(name, "HIGH",
                 f"conditional APPLIES ({note}) but not persisted as a complete "
                 f"block ({why})")
        if not applies and _block_ok(block):
            flag(name, "LOW", f"conditional persisted though frozen predicate says "
                              f"not applicable ({note})")

    # A conditional that is NOT declared and whose frozen predicate would
    # apply is a gap: the cycle must declare it (persisted or explicitly
    # frozen-off with the predicate visible).
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
    """Derive the artifact list from the contract itself.

    Hardened per owner remediation: the smoke test may not be handed a
    wish-list — the artifacts it verifies are exactly those the validated
    contract declares (mandatory outputs + persisted-and-applicable
    conditionals). An empty derivation is a problem, not a pass.
    """
    artifacts: list[dict] = []
    problems: list[str] = []
    for category, block in (contract.get("outputs") or {}).items():
        if isinstance(block, dict) and block.get("persist") and block.get("artifact"):
            artifacts.append({"category": category, **block})
    for name, block in (contract.get("conditional") or {}).items():
        if not isinstance(block, dict) or "applicability" not in block:
            continue
        applies, _ = _eval_applicability(str(block["applicability"]), contract)
        if applies and block.get("persist") and block.get("artifact"):
            artifacts.append({"category": name, **block})
    if not artifacts:
        problems.append("derived artifact list is EMPTY — nothing to verify")
    return artifacts, problems


def _verify_artifact(spec: dict, contract: dict, cwd: Optional[Path]) -> list[str]:
    """Parse the artifact and verify content: required fields, identity,
    non-empty series. Existence alone is not verification."""
    problems: list[str] = []
    category = spec["category"]
    rel = spec["artifact"]
    base = Path(cwd) if cwd else Path.cwd()
    path = base / rel
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
            # non-empty series: at least one non-null value per required column
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
    cwd=None,
    timeout: int = 600,
) -> tuple[str, list[str]]:
    """Terminal-A7 smoke test on the twin, hardened:

    1. the contract must pass :func:`validate_contract` first (a broken
       contract never runs the driver);
    2. the artifact list is DERIVED from the contract — never supplied;
    3. the twin's driver runs once and every declared artifact is parsed
       and verified for content: required fields, identity match against
       the contract's cycle_id, non-empty series.

    Returns (verdict, problems). This is the 'terminal rerun
    smoke-tested on twin' arm of the gate — the V15 metadata-TECHABORT
    class dies here, before launch, instead of at terminal.
    """
    import subprocess

    verdict, findings = validate_contract(contract)
    if verdict != PASS:
        return BLOCKED, [f"contract invalid before smoke: {f['category']}: {f['detail']}"
                         for f in findings if f["severity"] == "HIGH"] or ["contract invalid"]

    artifacts, problems = expected_artifacts_from_contract(contract)
    if problems:
        return BLOCKED, problems

    try:
        proc = subprocess.run(
            run_command, cwd=cwd, timeout=timeout, capture_output=True, text=True
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return BLOCKED, [f"twin smoke run failed to execute: {exc}"]
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-5:]
        return BLOCKED, [f"twin smoke run exit {proc.returncode}: {tail}"]

    for spec in artifacts:
        problems.extend(_verify_artifact(spec, contract, cwd))
    return (PASS if not problems else BLOCKED), problems
