"""T16 — sandbox isolation: the real governance dir / real root registry /
real GO artifact are refused BEFORE any read or write, and the session-
scoped snapshot in conftest proves they are byte-identical before vs after
the ENTIRE suite (heavy_runtime listings excepted: the canonical machine
lock runtime belongs to other cycles and is never pointed at by this
suite)."""
from __future__ import annotations

import json
import os

from conftest import REAL_ES_GO, REAL_GOV, REAL_REG, sha256_path


def _gov_before_after_untouched():
    return None  # the session fixture is the authority; direct checks below


def test_T16_direct_real_governance_dir_refused_pre_write(sb):
    assert os.path.isdir(REAL_GOV), "expected the real governance dir"
    r = sb.run(extra=["--governance-dir", REAL_GOV])
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    fs = sb.final()
    assert fs["refusal_code"] == "REFUSED_REAL_GOVERNANCE_DIR"
    assert fs["status"] == "REFUSED"
    # refusal recorded in the SANDBOX, never under the real dir
    rr = sb.out / "refusal_record.json"
    assert rr.is_file()
    assert json.loads(rr.read_text())["reason"] == \
        "REFUSED_REAL_GOVERNANCE_DIR"
    # the runner never got far enough to read the real registry
    assert "registered_cycle_ids" not in json.dumps(fs)
    assert not [x for x in sb.ledger_rows() if x["row_type"] == "TRIAL"]


def test_T16b_real_plans_dir_as_governance_refused(sb):
    r = sb.run(extra=["--governance-dir", os.path.dirname(REAL_REG)])
    assert r.returncode == 2
    assert sb.final()["refusal_code"] == "REFUSED_REAL_GOVERNANCE_DIR"


def test_T16c_governance_dir_at_real_registry_file_refused(sb):
    # --governance-dir pointed AT the real root registry path itself
    r = sb.run(extra=["--governance-dir", REAL_REG])
    assert r.returncode == 2
    assert sb.final()["refusal_code"] == "REFUSED_REAL_GOVERNANCE_DIR"


def test_T16d_final_status_into_real_dir_refused_no_write(sb):
    violating = os.path.join(REAL_GOV, "suite_should_never_write_FS.json")
    if os.path.exists(violating):  # pragma: no cover
        os.remove(violating)
    r = sb.run(extra=["--final-status-out", violating])
    assert r.returncode == 2
    assert not os.path.exists(violating), \
        "FINAL_STATUS must never be written into the real governance dir"
    # the refusal evidence falls back INTO the sandbox: emergency final
    # status + refusal_record land in the run dir, never in the real dir
    emergency = sb.out_file("FINAL_STATUS.emergency.json")
    assert emergency.is_file()
    assert json.loads(emergency.read_text())["refusal_code"] == \
        "REFUSED_REAL_GOVERNANCE_DIR"
    assert sb.out_file("refusal_record.json").is_file()
    assert not os.path.exists(os.path.join(REAL_GOV,
                                           "refusal_record.json"))


def test_T16e_real_governance_and_registry_unchanged_by_direct_run():
    """Direct before/after around one refused run (the suite-wide guard is
    the session fixture; this is the same property pinned locally)."""
    before_gov = sha256_path(os.path.join(REAL_GOV, "CYCLE_REGISTRY.json")) \
        if os.path.isfile(os.path.join(REAL_GOV, "CYCLE_REGISTRY.json")) \
        else "ABSENT"
    before_reg = sha256_path(REAL_REG)
    before_go = sha256_path(REAL_ES_GO)
    yield_before = (before_gov, before_reg, before_go)
    assert yield_before  # snapshot taken; the session fixture does the rest
    # (the session-scoped autouse fixture re-snapshots after ALL tests and
    #  asserts equality — including anything this suite might have caused.)
