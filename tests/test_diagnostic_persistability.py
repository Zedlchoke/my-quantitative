"""Tests for the diagnostic persistability gate.

Regression anchors (owner amendment 2, 2026-09-07):
- V3R: a contract without per-period series must be BLOCKED_PRELAUNCH —
  DSR/PBO were NOT_RUN fail-closed at terminal for exactly this gap.
- V15: a contract without per-symbol breakdown must be BLOCKED_PRELAUNCH
  (gates G6-G9 class); the frozen p3 output contract carried none.
- Conditionals may never become NOT_RUN for convenience: absence of a
  frozen applicability predicate is a HIGH finding.
"""

from __future__ import annotations

import json

from research.governance.diagnostic_persistability import (
    BLOCKED,
    PASS,
    MANDATORY_CATEGORIES,
    smoke_check_twin_rerun,
    validate_contract,
)


def _full_outputs():
    return {
        category: {"persist": True, "artifact": f"artifacts/{category}.jsonl"}
        for category in MANDATORY_CATEGORIES
    }


def _contract(**over):
    contract = {
        "cycle_id": "STOCKS-FREE-V12",
        "asset": "stocks",
        "multiple_testing_accounting": True,
        "calendar_conditioned": False,
        "confirmatory_entry_declared": False,
        "outputs": _full_outputs(),
        "conditional": {
            "dsr_per_period_series": {
                "applicability": "multiple_testing_accounting",
                "persist": True,
                "artifact": "artifacts/dsr_series.jsonl",
            }
        },
    }
    contract.update(over)
    return contract


def test_full_contract_passes():
    verdict, findings = validate_contract(_contract())
    assert verdict == PASS, findings


def test_v3r_regression_missing_per_period_series_blocks():
    outputs = _full_outputs()
    del outputs["per_period_series"]
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any(f["category"] == "per_period_series" for f in findings)


def test_v15_regression_missing_per_symbol_blocks():
    outputs = _full_outputs()
    del outputs["per_symbol_breakdown"]
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any(f["category"] == "per_symbol_breakdown" for f in findings)


def test_missing_margins_to_fail_blocks():
    outputs = _full_outputs()
    del outputs["margins_to_fail"]
    verdict, _ = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED


def test_conditional_without_frozen_predicate_blocks():
    contract = _contract()
    contract["conditional"] = {
        "dsr_per_period_series": {"persist": True, "artifact": "x"}  # no applicability
    }
    verdict, findings = validate_contract(contract)
    assert verdict == BLOCKED
    assert any("FROZEN applicability" in f["detail"] for f in findings)


def test_applicable_conditional_undeclared_blocks():
    contract = _contract(conditional={})
    verdict, findings = validate_contract(contract)
    assert verdict == BLOCKED
    assert any(f["category"] == "dsr_per_period_series" for f in findings)


def test_frozen_off_conditional_passes_without_persist():
    contract = _contract(multiple_testing_accounting=False, conditional={})
    verdict, findings = validate_contract(contract)
    assert verdict == PASS, findings


def test_forex_requires_financing_books():
    contract = _contract(
        asset="forex", calendar_conditioned=False, multiple_testing_accounting=False,
        conditional={},
    )
    verdict, findings = validate_contract(contract)
    assert verdict == BLOCKED
    assert any(f["category"] == "financing_dual_books" for f in findings)

    contract["conditional"] = {
        "financing_dual_books": {
            "applicability": "asset == 'forex'",
            "persist": True,
            "artifact": "artifacts/books.jsonl",
        }
    }
    verdict, findings = validate_contract(contract)
    assert verdict == PASS, findings


def test_calendar_conditioned_requires_sham_control():
    contract = _contract(calendar_conditioned=True, conditional={})
    verdict, findings = validate_contract(contract)
    assert verdict == BLOCKED
    assert any(f["category"] == "sham_control_calendar" for f in findings)


def test_persist_false_is_not_persisted():
    outputs = _full_outputs()
    outputs["stress_tiers"] = {"persist": False, "artifact": "x"}
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any(f["category"] == "stress_tiers" for f in findings)


def test_twin_smoke_pass_and_missing_artifact(tmp_path):
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import json, sys, pathlib\n"
        "out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)\n"
        "(out / 'per_fold.jsonl').write_text('{}')\n"
        "(out / 'per_symbol.jsonl').write_text('{}')\n",
        encoding="utf-8",
    )
    outdir = tmp_path / "artifacts"
    verdict, missing = smoke_check_twin_rerun(
        ["python3", str(driver), str(outdir)],
        [f"{outdir.name}/per_fold.jsonl", f"{outdir.name}/per_symbol.jsonl"],
        cwd=tmp_path,
    )
    assert verdict == PASS and not missing

    verdict, missing = smoke_check_twin_rerun(
        ["python3", str(driver), str(outdir)],
        [f"{outdir.name}/per_fold.jsonl", f"{outdir.name}/margins.json"],
        cwd=tmp_path,
    )
    assert verdict == BLOCKED and missing == [f"{outdir.name}/margins.json"]


def test_twin_smoke_nonzero_exit_blocks(tmp_path):
    driver = tmp_path / "boom.py"
    driver.write_text("import sys; sys.exit(3)\n", encoding="utf-8")
    verdict, errors = smoke_check_twin_rerun(
        ["python3", str(driver)], ["whatever.json"], cwd=tmp_path, timeout=30
    )
    assert verdict == BLOCKED
    assert any("exit 3" in e for e in errors)


def test_contract_is_json_serializable_round_trip():
    contract = _contract()
    assert json.loads(json.dumps(contract)) == contract
