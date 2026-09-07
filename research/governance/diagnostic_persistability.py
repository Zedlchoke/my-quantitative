"""Diagnostic persistability gate — prove BEFORE launch that the terminal
will be able to answer everything, because the runner persisted it.

Why this gate exists (owner amendment 2026-09-07):

- V3R (forex): at terminal, DSR/PBO were NOT_RUN fail-closed — "no
  per-period series in the program ledger". The runner had never
  persisted per-period returns, so the statistic that prices multiple
  testing was unreachable on the exact family that needed it most.
- V15 (crypto, TERMINAL_PENDING at governance intake): the frozen output
  contract carries no per-period-returns fields (measured at the p3
  freeze); owner-reported pending terminal artifacts: gates G6-G9 NOT_RUN
  for absent per-period returns, DSR/PBO NOT_RUN, and a terminal rerun
  producing a metadata TECHABORT.

Gate position: BEFORE A7 launch authorization. A run contract that
reaches A7 without a passing diagnostic contract is BLOCKED_PRELAUNCH —
the A1 must remediate the contract, not the auditor.

Contract format (a `diagnostic_output_contract` block inside the run
contract)::

    {
      "cycle_id": "STOCKS-FREE-V12",
      "asset": "stocks",
      "mechanism_class": "event_conditioned",
      "multiple_testing_accounting": true,
      "outputs": {
        "identity": {"persist": true, "fields": [...], "artifact": "..."},
        ...
      },
      "conditional": {
        "dsr_per_period_series": {
          "applicability": "multiple_testing_accounting == true",
          "persist": true,
          "artifact": "..."
        }
      }
    }

Verdicts:
  DIAGNOSTIC_CONTRACT_PASS   every mandatory category persisted, every
                             conditional either persisted or provably
                             not-applicable under its FROZEN predicate
  BLOCKED_PRELAUNCH          anything missing; findings name the category

A conditional that is absent without a frozen applicability predicate is
a finding — "NOT_RUN for convenience" is exactly what this gate exists
to refuse. Adoption boundary (FAMILY_PIPELINE.md §11): cycles whose
plans preregister this gate (crypto V16+, forex V7+, stocks V12+);
frozen/running cycles are NOT retrofitted.
"""

from __future__ import annotations

from typing import Any

GATE_ID = "DIAGNOSTIC_PERSISTABILITY"

PASS = "DIAGNOSTIC_CONTRACT_PASS"
BLOCKED = "BLOCKED_PRELAUNCH"

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
# The expression is evaluated against the contract's top-level booleans
# ONLY (no arbitrary code). Applicability must be frozen IN the contract
# by the cycle that declares it — never chosen at terminal time.
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

_ALLOWED_CONDITIONAL_KEYS = set(CONDITIONAL_DIAGNOSTICS)


def _category_ok(block: Any) -> bool:
    return isinstance(block, dict) and bool(block.get("persist")) and bool(
        block.get("artifact")
    )


def _eval_applicability(expr: str, contract: dict) -> tuple[bool, str]:
    """Evaluate a frozen boolean expression of the form
    ``flag`` or ``asset == 'x'`` against the contract header."""
    if expr in _asset_flags():
        return bool(contract.get(expr)), f"flag {expr}={bool(contract.get(expr))}"
    if expr.startswith("asset == "):
        want = expr.split("==", 1)[1].strip().strip("'\"")
        got = contract.get("asset")
        return got == want, f"asset {got!r} vs {want!r}"
    return False, f"unparseable frozen expression {expr!r}"


def _asset_flags() -> frozenset[str]:
    return frozenset(
        {"multiple_testing_accounting", "calendar_conditioned", "confirmatory_entry_declared"}
    )


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

    for category, why in MANDATORY_CATEGORIES.items():
        block = outputs.get(category)
        if not _category_ok(block):
            flag(category, "HIGH", f"mandatory diagnostic not persisted ({why})")

    conditional = contract.get("conditional", {})
    if not isinstance(conditional, dict):
        flag("conditional", "HIGH", "conditional block must be an object")
        conditional = {}
    unknown = set(conditional) - _ALLOWED_CONDITIONAL_KEYS
    for name in unknown:
        flag(name, "MEDIUM", f"unknown conditional diagnostic {name!r} (not in spec)")
    for name, (expr, why) in CONDITIONAL_DIAGNOSTICS.items():
        if name not in conditional:
            continue  # declared inapplicable by omission is an A1 choice ONLY
        block = conditional[name]
        if not isinstance(block, dict) or "applicability" not in block:
            flag(name, "HIGH",
                 f"conditional present without a FROZEN applicability predicate — "
                 f"NOT_RUN-for-convenience is refused ({why})")
            continue
        applies, note = _eval_applicability(str(block["applicability"]), contract)
        if applies and not _category_ok(block):
            flag(name, "HIGH",
                 f"conditional APPLIES ({note}) but not persisted ({why})")
        if not applies and _category_ok(block):
            # persisting an inapplicable diagnostic is harmless; record LOW
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


def smoke_check_twin_rerun(
    run_command: list[str],
    expected_artifacts: list[str],
    *,
    cwd=None,
    timeout: int = 600,
) -> tuple[str, list[str]]:
    """Terminal-A7 smoke test: run the twin's driver once on its synthetic
    fixture and assert every declared diagnostic artifact is emitted.

    Returns (verdict, missing_or_error). This is the 'terminal rerun
    smoke-tested on twin' arm of the gate — the V15 metadata-TECHABORT
    class dies here, before launch, instead of at terminal.
    """
    import subprocess

    try:
        proc = subprocess.run(
            run_command, cwd=cwd, timeout=timeout, capture_output=True, text=True
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return BLOCKED, [f"twin smoke run failed to execute: {exc}"]
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-5:]
        return BLOCKED, [f"twin smoke run exit {proc.returncode}: {tail}"]
    missing = [a for a in expected_artifacts if not _path_exists(a, cwd)]
    return (PASS if not missing else BLOCKED), missing


def _path_exists(rel: str, cwd) -> bool:
    from pathlib import Path

    base = Path(cwd) if cwd else Path.cwd()
    return (base / rel).exists()
