"""Tests for the diagnostic persistability gate (round-2 hardened).

Round-2 invariants (owner remediation 2026-09-07):
- CATEGORY_REQUIRED_FIELDS is canonical: a contract cannot pick an
  arbitrary field list (mismatched lists are rejected; verification
  always uses the canon);
- schema_id must resolve to the REGISTERED schema for its category;
- artifact paths must be relative with no '..' and no absolute parts;
- the smoke test runs in a NEW EMPTY sandbox — artifacts that existed
  before the driver ran can never satisfy the gate, so a no-op driver
  cannot PASS on stale outputs;
- per_symbol needs symbol + contribution/PnL; per_fold needs fold_id +
  PnL + population; margins needs gate_id/value/threshold/margin;
  counters needs observed/published/budget/rerun accounting; series
  needs period/arm_id/returns, non-empty, non-all-null.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.governance.diagnostic_persistability import (
    BLOCKED,
    CATEGORY_REQUIRED_FIELDS,
    CONDITIONAL_REQUIRED_FIELDS,
    PASS,
    REGISTERED_SCHEMAS,
    expected_artifacts_from_contract,
    smoke_check_twin_rerun,
    validate_contract,
)

CYCLE = "STOCKS-FREE-V12"


def _full_outputs(**overrides):
    outputs = {}
    for category, fields in CATEGORY_REQUIRED_FIELDS.items():
        outputs[category] = {
            "persist": True,
            "artifact": f"artifacts/{category}.jsonl",
            "schema_id": REGISTERED_SCHEMAS[category],
            "format": "jsonl",
        }
    outputs.update(overrides)
    return outputs


def _contract(**over):
    contract = {
        "cycle_id": CYCLE,
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
                "schema_id": REGISTERED_SCHEMAS["dsr_per_period_series"],
                "format": "jsonl",
            }
        },
    }
    contract.update(over)
    return contract


# --------------------------------------------------- canonical schema tests

def test_canonical_fields_match_owner_spec():
    assert CATEGORY_REQUIRED_FIELDS["per_symbol_breakdown"] == [
        "cycle_id", "symbol", "contribution_pnl"
    ]
    assert CATEGORY_REQUIRED_FIELDS["per_fold_breakdown"] == [
        "cycle_id", "fold_id", "pnl", "population"
    ]
    assert CATEGORY_REQUIRED_FIELDS["margins_to_fail"] == [
        "cycle_id", "gate_id", "value", "threshold", "margin"
    ]
    assert CATEGORY_REQUIRED_FIELDS["counters"] == [
        "observed_delta", "published_delta", "budget_used", "reruns_not_trials"
    ]
    assert CATEGORY_REQUIRED_FIELDS["per_period_series"] == [
        "cycle_id", "arm_id", "period", "returns"
    ]


def test_full_contract_passes_without_field_lists():
    # The canon IS the contract — omitting required_fields is fine.
    verdict, findings = validate_contract(_contract())
    assert verdict == PASS, findings


def test_contract_cannot_choose_arbitrary_fields():
    # Round-2 false-PASS class: a custom (too-thin) field list.
    outputs = _full_outputs(
        per_period_series={
            "persist": True, "artifact": "artifacts/per_period_series.jsonl",
            "schema_id": REGISTERED_SCHEMAS["per_period_series"], "format": "jsonl",
            "required_fields": ["cycle_id"],  # NOT the canonical set
        }
    )
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any("not the canonical set" in f["detail"] for f in findings)


def test_schema_id_must_be_registered_for_category():
    outputs = _full_outputs(
        margins_to_fail={
            "persist": True, "artifact": "artifacts/margins.jsonl",
            "schema_id": "diag/some_other_thing@9", "format": "jsonl",
        }
    )
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any("does not resolve" in f["detail"] for f in findings)


def test_missing_schema_id_blocks():
    outputs = _full_outputs(
        counters={"persist": True, "artifact": "artifacts/counters.jsonl", "format": "jsonl"}
    )
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any(f["category"] == "counters" for f in findings)


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


# -------------------------------------------------------- path-safety tests

def test_absolute_artifact_path_blocks():
    outputs = _full_outputs(
        identity={
            "persist": True, "artifact": "/etc/passwd",
            "schema_id": REGISTERED_SCHEMAS["identity"], "format": "jsonl",
        }
    )
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any("unsafe artifact path" in f["detail"] for f in findings)


def test_parent_escape_artifact_path_blocks():
    outputs = _full_outputs(
        stress_tiers={
            "persist": True, "artifact": "../../outside/leak.jsonl",
            "schema_id": REGISTERED_SCHEMAS["stress_tiers"], "format": "jsonl",
        }
    )
    verdict, findings = validate_contract(_contract(outputs=outputs))
    assert verdict == BLOCKED
    assert any("unsafe artifact path" in f["detail"] for f in findings)


# ------------------------------------------------------- conditional tests

def test_conditional_without_frozen_predicate_blocks():
    contract = _contract()
    contract["conditional"] = {
        "dsr_per_period_series": {"persist": True, "artifact": "x.jsonl",
                                  "schema_id": REGISTERED_SCHEMAS["dsr_per_period_series"],
                                  "format": "jsonl"}
    }
    verdict, findings = validate_contract(contract)
    assert verdict == BLOCKED
    assert any("FROZEN applicability" in f["detail"] for f in findings)


def test_applicable_conditional_undeclared_blocks():
    verdict, findings = validate_contract(_contract(conditional={}))
    assert verdict == BLOCKED
    assert any(f["category"] == "dsr_per_period_series" for f in findings)


def test_frozen_off_conditional_passes():
    verdict, findings = validate_contract(
        _contract(multiple_testing_accounting=False, conditional={})
    )
    assert verdict == PASS, findings


def test_forex_requires_financing_books():
    contract = _contract(asset="forex", calendar_conditioned=False,
                         multiple_testing_accounting=False, conditional={})
    verdict, findings = validate_contract(contract)
    assert verdict == BLOCKED
    assert any(f["category"] == "financing_dual_books" for f in findings)

    contract["conditional"] = {
        "financing_dual_books": {
            "applicability": "asset == 'forex'", "persist": True,
            "artifact": "artifacts/books.jsonl",
            "schema_id": REGISTERED_SCHEMAS["financing_dual_books"], "format": "jsonl",
        }
    }
    verdict, findings = validate_contract(contract)
    assert verdict == PASS, findings


def test_empty_outputs_block_is_high():
    verdict, findings = validate_contract(_contract(outputs={}))
    assert verdict == BLOCKED
    assert any("EMPTY" in f["detail"] for f in findings)


# --------------------------------------------------- derivation + smoke

DRIVER_BODY = (
    "import json, os, pathlib\n"
    "out = pathlib.Path('artifacts'); out.mkdir(parents=True, exist_ok=True)\n"
    "sample = {'cycle_id': '%s', 'family_id': 'F1', 'arm_id': 'ANCHOR',\n"
    "          'arm_config_digest': 'd', 'data_snapshot_digest': 'd',\n"
    "          'code_freeze_sha': 'd', 'cost_tier': 'base',\n"
    "          'period': 1, 'returns': 0.5, 'symbol': 'SYM',\n"
    "          'contribution_pnl': 1.0, 'fold_id': 'F0', 'pnl': 1.0,\n"
    "          'population': 10, 'tier': 'x2.0', 'omitted_symbol': 'S2',\n"
    "          'benchmark': 'SPY', 'excess_return': 0.1, 'gate_id': 'G1',\n"
    "          'value': 1.0, 'threshold': 2.0, 'margin': -1.0,\n"
    "          'observed_delta': 1, 'published_delta': 1,\n"
    "          'budget_used': 0, 'reruns_not_trials': 0,\n"
    "          'data_manifest_sha': 'd', 'sanitized': True}\n"
    "for cat in json.loads(os.environ['DIAG_CANON']):\n"
    "    recs = []\n"
    "    for i in range(2):\n"
    "        rec = dict(sample); rec['x'] = i\n"
    "        recs.append(json.dumps(rec))\n"
    "    (out / (cat + '.jsonl')).write_text('\\n'.join(recs) + '\\n')\n"
) % CYCLE


def _driver_env():
    import os
    return {**os.environ, "DIAG_CANON": json.dumps(CATEGORY_REQUIRED_FIELDS)}


def test_smoke_passes_with_fresh_emission(tmp_path, monkeypatch):
    driver = tmp_path / "driver.py"
    driver.write_text(DRIVER_BODY, encoding="utf-8")
    monkeypatch.setenv("DIAG_CANON", json.dumps({**CATEGORY_REQUIRED_FIELDS, **CONDITIONAL_REQUIRED_FIELDS}))
    verdict, problems = smoke_check_twin_rerun(
        ["python3", str(driver)], _contract(), sandbox_root=tmp_path, timeout=120
    )
    assert verdict == PASS, problems


def test_noop_driver_cannot_pass_on_stale_artifacts(tmp_path, monkeypatch):
    """Round-2 adversarial: artifacts pre-exist NEXT TO the sandbox and
    the driver is a no-op — the gate must refuse because emission
    happens in a fresh empty sandbox only."""
    stale = tmp_path / "stale_output"
    stale.mkdir()
    for cat in CATEGORY_REQUIRED_FIELDS:
        (stale / f"{cat}.jsonl").write_text(
            json.dumps({"cycle_id": CYCLE}) + "\n", encoding="utf-8"
        )
    monkeypatch.setenv("DIAG_CANON", json.dumps({**CATEGORY_REQUIRED_FIELDS, **CONDITIONAL_REQUIRED_FIELDS}))
    noop = tmp_path / "noop.py"
    noop.write_text("pass\n", encoding="utf-8")
    verdict, problems = smoke_check_twin_rerun(
        ["python3", str(noop)], _contract(), sandbox_root=tmp_path, timeout=120
    )
    assert verdict == BLOCKED
    assert any("not emitted" in p for p in problems)


def test_preexisting_artifacts_in_sandbox_root_cannot_leak(tmp_path, monkeypatch):
    # The sandbox_root itself is dirty; the gate must still create a FRESH
    # subdirectory, so the leftovers cannot satisfy it.
    for cat in CATEGORY_REQUIRED_FIELDS:
        (tmp_path / f"{cat}.jsonl").write_text(
            json.dumps({"cycle_id": CYCLE}) + "\n", encoding="utf-8"
        )
    monkeypatch.setenv("DIAG_CANON", json.dumps({**CATEGORY_REQUIRED_FIELDS, **CONDITIONAL_REQUIRED_FIELDS}))
    noop = tmp_path / "noop.py"
    noop.write_text("pass\n", encoding="utf-8")
    # Drivers write under artifacts/ relative to cwd; the leftovers sit at
    # the root level and use the wrong shape anyway.
    contract = _contract()
    verdict, problems = smoke_check_twin_rerun(
        ["python3", str(noop)], contract, sandbox_root=tmp_path, timeout=120
    )
    assert verdict == BLOCKED


def test_smoke_blocked_on_nonzero_exit(tmp_path):
    boom = tmp_path / "boom.py"
    boom.write_text("import sys; sys.exit(3)\n", encoding="utf-8")
    verdict, problems = smoke_check_twin_rerun(
        ["python3", str(boom)], _contract(), sandbox_root=tmp_path, timeout=60
    )
    assert verdict == BLOCKED
    assert any("exit 3" in p for p in problems)


def test_smoke_never_runs_driver_when_contract_invalid(tmp_path):
    marker = tmp_path / "ran.marker"
    body = f"import pathlib; pathlib.Path({str(marker)!r}).write_text('ran')\n"
    driver = tmp_path / "driver.py"
    driver.write_text(body, encoding="utf-8")
    verdict, _ = smoke_check_twin_rerun(
        ["python3", str(driver)], _contract(outputs={}), sandbox_root=tmp_path, timeout=60
    )
    assert verdict == BLOCKED
    assert not marker.exists()


def test_smoke_blocked_when_derived_list_empty(tmp_path):
    contract = _contract(multiple_testing_accounting=False, outputs={}, conditional={})
    marker = tmp_path / "ran.marker"
    driver = tmp_path / "driver.py"
    driver.write_text(f"import pathlib; pathlib.Path({str(marker)!r}).write_text('ran')\n",
                      encoding="utf-8")
    verdict, problems = smoke_check_twin_rerun(
        ["python3", str(driver)], contract, sandbox_root=tmp_path, timeout=60
    )
    assert verdict == BLOCKED
    assert any("EMPTY" in p for p in problems)
    assert not marker.exists()


def test_derivation_carries_canon_fields_and_registered_schemas():
    artifacts, problems = expected_artifacts_from_contract(_contract())
    assert not problems
    for spec in artifacts:
        canon = {**{}, **{k: v for k, v in CATEGORY_REQUIRED_FIELDS.items()}}
        if spec["category"] in CATEGORY_REQUIRED_FIELDS:
            assert spec["required_fields"] == CATEGORY_REQUIRED_FIELDS[spec["category"]]
        assert spec["schema_id"] == REGISTERED_SCHEMAS.get(spec["category"])


def test_contract_is_json_serializable_round_trip():
    contract = _contract()
    assert json.loads(json.dumps(contract)) == contract
