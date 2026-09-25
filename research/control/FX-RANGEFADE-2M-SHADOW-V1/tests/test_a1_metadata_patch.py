"""A1 metadata patch fixtures (owner-approved preparation 2026-09-25).

Owner spec, verbatim intent: keep T_ctrl from the activation artifact
(authority); the journal cost_book row at boot is CROSS-CHECK only and is
never silently substituted; fix state-layer + wording to
SHORT_BETA_SEPARATION_ACCRUING; no signal/fill/cost/ledger/history
change; fail-closed on missing/contradictory artifact; fixtures for (i)
the one-second boundary, (ii) restart/idempotence, (iii) fail-closed
cases.
"""

import json
from pathlib import Path

import pytest

import fx_shadow_core as C

HERE = Path(__file__).resolve().parent        # tests/
CYCLE = HERE.parent                            # FX-RANGEFADE-2M-SHADOW-V1/
ART = json.loads((CYCLE / "A1_ACTIVATION.json").read_text())
T_CTRL = "2026-09-25T05:35:03Z"        # artifact authority (owner law)
CB_TS = "2026-09-25T05:35:04+00:00"    # journal cost_book row (evidence)


# ------------------------------------------------ (i) one-second boundary
def test_i_production_case_one_second_skew_consistent():
    d = C.derive_a1_activation(ART, CB_TS)
    assert d["phase"] == "ACTIVATED"
    assert d["cross_check"]["skew_s"] == 1.0
    assert d["cross_check"]["verdict"] == "CONSISTENT"


def test_i_t_ctrl_is_artifact_value_never_substituted():
    d = C.derive_a1_activation(ART, CB_TS)
    assert d["T_ctrl"] == T_CTRL  # NOT the journal ts (05:35:04)
    assert d["T_ctrl"] != CB_TS


def test_i_boundary_minus_one_second_fail_closed():
    # journal row BEFORE the artifact's T_ctrl: ordering contradiction
    d = C.derive_a1_activation(ART, "2026-09-25T05:35:02+00:00")
    assert d["phase"] == "ACTIVATION_UNVERIFIED_FAIL_CLOSED"
    assert d["T_ctrl"] is None
    assert d["cross_check"]["reason"] == "JOURNAL_ROW_PRECEDES_ARTIFACT_T_CTRL"


def test_i_boundary_at_exact_t_ctrl_consistent():
    d = C.derive_a1_activation(ART, "2026-09-25T05:35:03+00:00")
    assert d["phase"] == "ACTIVATED"
    assert d["cross_check"]["skew_s"] == 0.0


def test_i_skew_over_tolerance_fail_closed():
    d = C.derive_a1_activation(ART, "2026-09-25T05:45:04+00:00")  # +601s
    assert d["phase"] == "ACTIVATION_UNVERIFIED_FAIL_CLOSED"
    assert d["cross_check"]["reason"] == "SKEW_EXCEEDS_TOLERANCE"


# ------------------------------------------------ (ii) restart / idempotence
def test_ii_derivation_pure_and_idempotent():
    a = C.derive_a1_activation(ART, CB_TS)
    b = C.derive_a1_activation(ART, CB_TS)
    assert a == b  # identical inputs -> identical block (restart-safe)


def test_ii_label_law_all_branches():
    accr = C.short_beta_label_for(True, C.derive_a1_activation(ART, CB_TS),
                                  "2026-09-25T06:00:06+00:00")
    assert accr.startswith("SHORT_BETA_SEPARATION_ACCRUING")
    assert "no FX-vs-control conclusion" in accr
    # fail-closed activation keeps the UNSEPARATED label even with records
    fc = C.derive_a1_activation(None, CB_TS)
    assert C.short_beta_label_for(True, fc, None) == C.SHORT_BETA_LABEL
    # no control records yet -> UNSEPARATED regardless
    assert C.short_beta_label_for(False, C.derive_a1_activation(ART, CB_TS),
                                  None) == C.SHORT_BETA_LABEL


def test_ii_state_writer_uses_derived_block(monkeypatch):
    # source-level: the daemon state block carries derived phase/T_ctrl +
    # cross-check + first_ctrl_record_ts; no static placeholder remains.
    src = (CYCLE / "daemon" / "shadow_daemon.py").read_text()
    assert '"phase": a1_activation["phase"]' in src
    assert '"T_ctrl": a1_activation["T_ctrl"]' in src
    assert "PHASE_I_code_only_NOT_ACTIVATED" not in src  # placeholder gone
    assert 'HERE.parent / "A1_ACTIVATION.json"' in src


# ------------------------------------------------ (iii) fail-closed cases
@pytest.mark.parametrize("artifact,reason", [
    (None, "ARTIFACT_MISSING_OR_UNREADABLE"),
    ({}, "ARTIFACT_MALFORMED_NO_T_CTRL"),
    ({"phase_a": {}}, "ARTIFACT_MALFORMED_NO_T_CTRL"),
    ({"phase_a": {"t_ctrl_utc": 123}}, "ARTIFACT_MALFORMED_NO_T_CTRL"),
])
def test_iii_artifact_missing_or_malformed_fail_closed(artifact, reason):
    d = C.derive_a1_activation(artifact, CB_TS)
    assert d["phase"] == "ACTIVATION_UNVERIFIED_FAIL_CLOSED"
    assert d["T_ctrl"] is None
    assert d["cross_check"]["reason"] == reason
    # fail-closed keeps the NOT PROMOTABLE label law
    assert C.short_beta_label_for(True, d, None) == C.SHORT_BETA_LABEL


def test_iii_journal_cost_book_row_missing_fail_closed():
    d = C.derive_a1_activation(ART, None)
    assert d["phase"] == "ACTIVATION_UNVERIFIED_FAIL_CLOSED"
    assert d["cross_check"]["reason"] == "JOURNAL_COST_BOOK_ROW_MISSING"


def test_iii_unparseable_ts_fail_closed():
    d = C.derive_a1_activation(ART, "not-a-timestamp")
    assert d["phase"] == "ACTIVATION_UNVERIFIED_FAIL_CLOSED"
    assert d["cross_check"]["reason"] == "TIMESTAMP_PARSE_ERROR"


# ------------------------------------------------ scope containment
def test_scope_state_layer_only_frozen_paths_untouched():
    # the patch touches ONLY fx_shadow_core.py + shadow_daemon.py in this
    # change-set; frozen strategy surface byte-identical (git-level).
    import subprocess
    for frozen in ("daemon/v2_lib.py", "daemon/engine.py"):
        proc = subprocess.run(
            ["git", "-C", str(CYCLE.parent), "status", "--porcelain=v1",
             "--", frozen],
            capture_output=True, text=True)
        assert proc.returncode == 0 and proc.stdout.strip() == "", frozen


# ------------------------------------------------ F1 seam (A7 delta)
def test_f1_cross_check_uses_activation_time_row_not_boot_clock():
    # journal replay contains the activation-time cost_book row; a much
    # later boot must still cross-check against THAT row (skew 1s), not
    # the current clock (which would be >300s and fail-closed forever).
    lines = [
        json.dumps({"event": "bar_closed", "ts": "2026-09-25T05:35:03+00:00"}),
        json.dumps({"event": "cost_book", "ts": "2026-09-25T05:35:04+00:00",
                    "digest": "sha256:de02abf16b142a6e"}),
        json.dumps({"event": "ctrl_open", "ts": "2026-09-25T06:00:06+00:00"}),
        json.dumps({"event": "cost_book", "ts": "2026-09-25T07:14:00+00:00"}),
    ]
    late_boot = "2026-09-25T09:00:00+00:00"
    ts = C.boot_cross_check_ts(lines, late_boot)
    assert ts == "2026-09-25T05:35:04+00:00"   # FIRST row, not later ones
    d = C.derive_a1_activation(ART, ts)
    assert d["phase"] == "ACTIVATED" and d["T_ctrl"] == T_CTRL
    assert d["cross_check"]["skew_s"] == 1.0
    # counterfactual: wiring via the boot clock would fail-closed
    d_bad = C.derive_a1_activation(ART, late_boot)
    assert d_bad["phase"] == "ACTIVATION_UNVERIFIED_FAIL_CLOSED"


def test_f1_no_prior_row_falls_back_to_fresh_ts():
    assert C.boot_cross_check_ts([], "2026-09-25T05:35:04+00:00") == \
        "2026-09-25T05:35:04+00:00"


def test_f1_daemon_wiring_source_uses_helper():
    src = (CYCLE / "daemon" / "shadow_daemon.py").read_text()
    assert "C.boot_cross_check_ts(" in src
    assert "_cb_ts = now_utc().isoformat(timespec=\"seconds\")" not in src.replace(
        "a1_lines, now_utc().isoformat(timespec=\"seconds\"))", "")
