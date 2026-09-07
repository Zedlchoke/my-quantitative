"""Tests for the diagnostic persistability gate (hardened).

Regression anchors (owner amendment 2 + remediation item 5, 2026-09-07):
- V3R: a contract without per-period series must be BLOCKED_PRELAUNCH —
  DSR/PBO were NOT_RUN fail-closed at terminal for exactly this gap.
- V15: a contract without per-symbol breakdown must be BLOCKED_PRELAUNCH
  (gates G6-G9 class); the frozen p3 output contract carried none.
- Remediation false-PASS classes now blocked: output blocks without
  schema_id/required_fields; smoke with EMPTY artifacts; smoke that
  checks existence only (must parse + verify identity + non-empty
  series); hand-picked artifact lists (the list is DERIVED from the
  contract).
"""

from __future__ import annotations

import json
from pathlib import Path

from research.governance.diagnostic_persistability import (
    BLOCKED,
    PASS,
    MANDATORY_CATEGORIES,
    expected_artifacts_from_contract,
    smoke_check_twin_rerun,
    validate_contract,
)


def _full_outputs():
    return {
        category: {
            "persist": True,
            "artifact": f"artifacts/{category}.jsonl",
            "schema_id": f"diag/{category}@1",
            "format": "jsonl",
            "required_fields": ["cycle_id", "value"],
        }
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
                "artifact": "artifacts/dsr_per_period_series.jsonl",
                "schema_id": "diag/dsr_per_period_series@1",
                "format": "jsonl",
                "required_fields": ["cycle_id", "period", "returns"],
            }
        },
    }
    contract.update(over)
    return contract


# ---------------------------------------------------------------- validate

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


def test_rem_cells_block_incomplete_output_block():
    # FALSE-PASS class 1 (old code passed on persist+artifact alone):
    # a block without schema_id / required_fields / format.
    outputs = _full_outputs()
    outputs["stress_tiers"] = {"persist": True, "artifact": "x.jsonl"}
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any(f["category"] == "stress_tiers" for f in findings)


def test_empty_outputs_block_is_high():
    # FALSE-PASS class 2: an outputs block with nothing in it.
    verdict, findings = validate_contract(_contract(outputs={}))
    assert verdict == BLOCKED
    assert any("EMPTY" in f["detail"] for f in findings)


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
            "schema_id": "diag/books@1",
            "format": "jsonl",
            "required_fields": ["cycle_id", "book"],
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
    outputs["stress_tiers"] = {"persist": False, "artifact": "x", "schema_id": "s@1",
                               "format": "jsonl", "required_fields": ["a"]}
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any(f["category"] == "stress_tiers" for f in findings)


# ------------------------------------------------- artifact-list derivation

def test_artifact_list_is_derived_from_contract():
    artifacts, problems = expected_artifacts_from_contract(_contract())
    assert not problems
    cats = {a["category"] for a in artifacts}
    assert set(MANDATORY_CATEGORIES) <= cats
    assert "dsr_per_period_series" in cats  # applicable conditional included


def test_empty_derivation_is_a_problem():
    artifacts, problems = expected_artifacts_from_contract(
        _contract(multiple_testing_accounting=False, outputs={}, conditional={})
    )
    assert not artifacts
    assert any("EMPTY" in p for p in problems)


def test_inapplicable_conditional_not_in_derived_list():
    artifacts, _ = expected_artifacts_from_contract(
        _contract(multiple_testing_accounting=False)
    )
    cats = {a["category"] for a in artifacts}
    assert "dsr_per_period_series" not in cats


# -------------------------------------------------------- twin smoke tests

DRIVER_OK = (
    "import json, sys, pathlib\n"
    "out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)\n"
    "rows = [json.dumps({'cycle_id': 'STOCKS-FREE-V12', 'period': i,\n"
    "                    'returns': 0.5, 'value': 0.5})\n"
    "        for i in range(3)]\n"
    "for cat in ['identity','per_period_series','per_symbol_breakdown',\n"
    "            'per_fold_breakdown','stress_tiers','drop_one_inputs',\n"
    "            'benchmark_context','margins_to_fail','counters',\n"
    "            'reproduction_inputs']:\n"
    "    (out / (cat + '.jsonl')).write_text('\\n'.join(rows) + '\\n')\n"
    "(out / 'dsr_per_period_series.jsonl').write_text('\\n'.join(rows) + '\\n')\n"
)


def _driver(tmp_path, body, name="driver.py"):
    driver = tmp_path / name
    driver.write_text(body, encoding="utf-8")
    return [ "python3", str(driver), str(tmp_path / "artifacts") ]


def test_smoke_passes_with_content_verification(tmp_path):
    cmd = _driver(tmp_path, DRIVER_OK)
    verdict, problems = smoke_check_twin_rerun(cmd, _contract(), cwd=tmp_path, timeout=60)
    assert verdict == PASS, problems


def test_smoke_blocked_on_empty_artifact_file(tmp_path):
    # FALSE-PASS class 3: old code checked existence only; an EMPTY
    # jsonl must now BLOCK.
    body = DRIVER_OK + (
        "pathlib.Path(sys.argv[1]).joinpath('margins_to_fail.jsonl').write_text('')"
    )
    cmd = _driver(tmp_path, body)
    verdict, problems = smoke_check_twin_rerun(cmd, _contract(), cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert any("margins_to_fail" in p and "EMPTY" in p for p in problems)


def test_smoke_blocked_on_missing_required_field(tmp_path):
    body = DRIVER_OK.replace("'period': i,", "")
    cmd = _driver(tmp_path, body)
    verdict, problems = smoke_check_twin_rerun(cmd, _contract(), cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert any("missing field" in p for p in problems)


def test_smoke_blocked_on_identity_mismatch(tmp_path):
    body = DRIVER_OK.replace("STOCKS-FREE-V12", "OTHER-CYCLE-9")
    cmd = _driver(tmp_path, body)
    verdict, problems = smoke_check_twin_rerun(cmd, _contract(), cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert any("identity mismatch" in p for p in problems)


def test_smoke_blocked_on_all_null_series_column(tmp_path):
    body = DRIVER_OK.replace("'returns': 0.5", "'returns': None")
    cmd = _driver(tmp_path, body)
    verdict, problems = smoke_check_twin_rerun(cmd, _contract(), cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert any("all-null" in p for p in problems)


def test_smoke_blocked_on_missing_artifact(tmp_path):
    body = DRIVER_OK.replace(
        "            'benchmark_context','margins_to_fail','counters',\n"
        "            'reproduction_inputs']:", "            'margins_to_fail','counters',\n"
        "            'reproduction_inputs']:")
    cmd = _driver(tmp_path, body)
    verdict, problems = smoke_check_twin_rerun(cmd, _contract(), cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert any("not emitted" in p for p in problems)


def test_smoke_blocked_on_nonzero_exit(tmp_path):
    cmd = _driver(tmp_path, "import sys; sys.exit(3)\n")
    verdict, problems = smoke_check_twin_rerun(cmd, _contract(), cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert any("exit 3" in p for p in problems)


def test_smoke_never_runs_driver_when_contract_invalid(tmp_path):
    # FALSE-PASS class 4: an invalid contract must BLOCK before the
    # driver runs at all (marker file proves the driver did not execute).
    marker = tmp_path / "ran.marker"
    body = f"import pathlib; pathlib.Path({str(marker)!r}).write_text('ran')\n"
    cmd = _driver(tmp_path, body)
    bad = _contract(outputs={})
    verdict, problems = smoke_check_twin_rerun(cmd, bad, cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert not marker.exists()


def test_smoke_blocked_when_derived_list_empty(tmp_path):
    contract = _contract(multiple_testing_accounting=False, outputs={}, conditional={})
    marker = tmp_path / "ran.marker"
    cmd = _driver(tmp_path, f"import pathlib; pathlib.Path({str(marker)!r}).write_text('ran')\n")
    verdict, problems = smoke_check_twin_rerun(cmd, contract, cwd=tmp_path, timeout=60)
    assert verdict == BLOCKED
    assert any("EMPTY" in p for p in problems)
    assert not marker.exists()


def test_contract_is_json_serializable_round_trip():
    contract = _contract()
    assert json.loads(json.dumps(contract)) == contract
