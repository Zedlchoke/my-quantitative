"""RATES-NG1 Z-phase sanitized dry-run tests.

Cycle RATES-NG1, task rates-ng1-z-dryrun (dispatch packet invocation
lead-bg-rates-z).

SCOPE LAW: these tests enforce the Z SANITIZATION LAW on the committed
artifact set (research/control/rates_ng1_run/z/z_report.json) and on
the live driver:

1.  the committed z_report records STRUCTURAL facts only -- key law
    (I-phase forbidden outcome patterns + Z-extended patterns at every
    depth), no-float value law, 64-hex digest law;
2.  battery comparator figures/verdicts appear ONLY as sha256
    suppression pins;
3.  the digest chain ties the report to the frozen substrate artifacts
    (selection freeze, P2 grid census, P1 cost contract, substrate
    manifest) by measured sha256;
4.  the live driver run on the REAL frozen substrate (plane-verified,
    end-to-end through the unmodified I-phase runners) reproduces the
    committed report BYTE-FOR-BYTE and verdicts PASS;
5.  negative controls: planted outcome keys/values/digests are caught,
    contaminated emissions are REFUSED, digest drift is REFUSED, and a
    plumbing failure on real data reports BLOCKED_PRELAUNCH_CANDIDATE
    honestly (never repaired).

NO outcome number is asserted, printed or stored anywhere here: the
sanitization law is that committed artifacts cannot carry them, so the
tests assert their ABSENCE.
"""

from __future__ import annotations

import copy
import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.rates_ng1.runners import rules as rl  # noqa: E402
from research.assets.rates_ng1.runners.battery import (  # noqa: E402
    KILLER_ROLES,
)
from research.assets.rates_ng1.runners.runner import (  # noqa: E402
    EXIT_REASONS,
    RunnerLawError,
    assemble_cell_configs,
    canonical_digest,
    fold_of_session,
)
from research.control.rates_ng1_run.z import z_run  # noqa: E402

FREEZE_PATH = z_run.FREEZE_PATH
CENSUS_PATH = z_run.CENSUS_PATH
CONTRACT_PATH = z_run.CONTRACT_PATH
MANIFEST_PATH = z_run.MANIFEST_PATH

#: The dispatch packet's frozen arm-digest prefixes.
PACKET_PREFIXES = {
    "RATESNG1-A5-P1-ARM-NEUTRAL": "33b78baa",
    "RATESNG1-A5-P1-ARM-CONSERVATIVE": "54ef5def",
    "RATESNG1-A5-P1-ARM-AGGRESSIVE": "cfdad940",
}


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture(scope="module")
def committed_report():
    with open(z_run.REPORT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def committed_bytes():
    with open(z_run.REPORT_PATH, "rb") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def freeze():
    with open(FREEZE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def live_payload():
    """One full real-substrate pipeline run per test session (cached)."""
    return z_run.cached_payload()


# ================================================================== #
# 1. Committed report: schema + sanitization law                       #
# ================================================================== #

class TestCommittedReportSanitization:
    def test_report_exists_with_schema(self, committed_report):
        assert committed_report["schema"] == z_run.REPORT_SCHEMA
        assert committed_report["cycle_id"] == "RATES-NG1"
        assert committed_report["task_id"] == "rates-ng1-z-dryrun"
        assert committed_report["mode"] == \
            "Z_SANITIZED_DRY_RUN_REAL_SUBSTRATE"
        assert committed_report["s1"] == "SEALED_UNTOUCHED"

    def test_overall_verdict_in_allowed_set_and_pass(
            self, committed_report):
        assert committed_report["overall_verdict"] in z_run.VERDICTS
        assert committed_report["overall_verdict"] == "PASS"

    def test_committed_report_sanitizer_clean(self, committed_report):
        scan = z_run.sanitize_payload(committed_report)
        assert scan["clean"] is True, json.dumps(scan)[:2000]

    def test_committed_report_i_phase_scanner_clean(
            self, committed_report):
        scan = rl.scan_emission_for_outcome_tokens(committed_report)
        assert scan["clean"] is True

    def test_no_float_values_anywhere(self, committed_report):
        floats = []

        def walk(node):
            if isinstance(node, dict):
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, float) and not isinstance(
                    node, bool):
                floats.append(node)

        walk(committed_report)
        assert floats == []

    def test_sha256_keys_carry_64hex(self, committed_report):
        import re
        hex_re = re.compile(r"[0-9a-f]{64}")
        bad = []

        def walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    if str(k).lower().endswith("sha256"):
                        if isinstance(v, dict):
                            for dk, dv in v.items():
                                if not (isinstance(dv, str)
                                        and hex_re.fullmatch(dv)):
                                    bad.append(f"{path}.{k}.{dk}")
                        elif not (isinstance(v, str)
                                  and hex_re.fullmatch(v)):
                            bad.append(f"{path}.{k}")
                    walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")

        walk(committed_report, "$")
        assert bad == []

    def test_battery_verdicts_suppressed_to_digests(
            self, committed_report):
        for cell in committed_report["cells"]:
            battery = cell["battery"]
            assert set(battery["controls"]) == set(KILLER_ROLES)
            assert len(battery["verdict_internals_sha256"]) == 64
            for role, ctl in battery["controls"].items():
                # structural keys only; comparator figures/verdicts
                # appear ONLY as the suppression pins
                assert set(ctl) == {
                    "status", "executable", "n_instants",
                    "n_pairs_used", "dropped_undefined_anchor",
                    "dropped_undefined_control", "control_state_counts",
                    "control_fills_total", "control_edges_sha256",
                    "suppressed_fields",
                }
                assert ctl["status"] in ("PASS", "FAIL")
                assert ctl["n_pairs_used"] >= 0
                assert len(ctl["control_edges_sha256"]) == 64

    def test_every_cell_carries_outcome_internals_as_pins_only(
            self, committed_report):
        for cell in committed_report["cells"]:
            internals = cell["outcome_internals"]
            assert set(internals) == {
                "suppression_law", "round_trip_outcome_sha256",
                "per_decision_edges_sha256",
            }
            for key in ("round_trip_outcome_sha256",
                        "per_decision_edges_sha256"):
                assert len(internals[key]) == 64


# ================================================================== #
# 2. Digest chain vs the frozen artifacts (re-measured)                #
# ================================================================== #

class TestDigestChain:
    def test_freeze_digest_measured(self, committed_report):
        import hashlib
        h = hashlib.sha256(open(FREEZE_PATH, "rb").read()).hexdigest()
        assert committed_report["digest_chain"][
            "selection_freeze_sha256"] == h

    def test_artifact_pins_match_freeze_citation_pins(
            self, committed_report, freeze):
        import hashlib
        chain = committed_report["digest_chain"]
        pins = freeze["citation_pins"]
        for label, path, pin_key in (
                ("p2_grid_census", CENSUS_PATH,
                 "research/control/rates_ng1_run/p2_grid_census.json"),
                ("p1_cost_contract", CONTRACT_PATH,
                 "research/control/rates_ng1_run/"
                 "p1_cost_contract.json"),
                ("substrate_manifest", MANIFEST_PATH,
                 "research/control/rates_ng1_run/"
                 "substrate_manifest.json")):
            measured = hashlib.sha256(open(path, "rb").read()).hexdigest()
            assert chain[f"{label}_sha256"] == measured
            assert chain[f"{label}_pin_match"] is True
            assert measured == pins[pin_key]

    def test_census_counts_match_freeze_feasibility(
            self, committed_report, freeze):
        chain = committed_report["digest_chain"]
        feas = freeze["section_1_selected_family"][
            "feasibility_evidence"]
        assert chain["census_bookable_instants"] == \
            feas["bookable_instants"] == 1918
        assert chain["census_grid_sessions"] == \
            feas["grid_sessions"] == 2170
        assert chain["census_counts_match_freeze"] is True

    def test_plane_provenance_all_verified(self, committed_report):
        plane = committed_report["plane"]
        assert plane["all_digest_verified"] is True
        assert plane["entries_consumed"] == len(plane["entries"]) == 11
        kinds = {e["entry"].split("/")[0] for e in plane["entries"]}
        assert kinds == {"treasury_curve", "etp_eod"}
        for entry in plane["entries"]:
            assert entry["digest_verified"] is True
            assert entry["sha256_pinned"] == entry["sha256_measured"]

    def test_representation_through_i_runner_loader(
            self, committed_report):
        rep = committed_report["representation"]
        assert rep["bookable_instants_len"] == 1918
        assert rep["grid_dates_len"] == 2170
        assert "runners.runner.load_representation" in rep["loader"]

    def test_base_sha_and_branch_pinned(self, committed_report):
        assert committed_report["base_sha"] == \
            "5672d9ed980feccc500fd75c565c5cd7c789d1f0"
        assert committed_report["branch"] == "orca/rates-ng1-integration"


# ================================================================== #
# 3. Cells: the exact 3 frozen cells, structural counts                #
# ================================================================== #

class TestCells:
    def test_exactly_three_cells_with_packet_digests(
            self, committed_report):
        cells = committed_report["cells"]
        assert len(cells) == 3
        by_arm = {c["arm_id"]: c for c in cells}
        assert set(by_arm) == set(PACKET_PREFIXES)
        for arm_id, prefix in PACKET_PREFIXES.items():
            assert by_arm[arm_id]["digest_prefix"] == prefix
            assert by_arm[arm_id]["packet_digest_prefix_match"] is True
        digests = [c["arm_config_digest"] for c in cells]
        assert len(set(digests)) == 3

    def test_arm_digests_match_freeze_verbatim(
            self, committed_report, freeze):
        frozen = {a["arm_id"]: a["arm_config_digest"]
                  for a in freeze["section_2_arm_configuration_plan"][
                      "arms"]}
        for cell in committed_report["cells"]:
            assert cell["arm_config_digest"] == \
                frozen[cell["arm_id"]]
            assert cell["arm_config_digest"] == canonical_digest(
                next(a["config"] for a
                     in freeze["section_2_arm_configuration_plan"]["arms"]
                     if a["arm_id"] == cell["arm_id"]))

    def test_state_counts_on_full_grid(self, committed_report):
        for cell in committed_report["cells"]:
            sc = cell["state_counts"]
            assert sc["decisions_total"] == 1918
            assert sc["states_defined"] + sc["states_undefined"] == 1918
            assert sc["decision_ids_pairwise_distinct"] is True
            assert sc["round_trips"] >= 1
            assert sc["state_events_nonzero"] >= 1

    def test_states_undefined_equal_min_past_points(
            self, committed_report, freeze):
        # Q-11: the pre-fit head is UNDEFINED, exactly min_past_points
        # long (the freeze freezes min_past_points = 63 for every arm).
        for cell in committed_report["cells"]:
            cfg = next(a["config"] for a
                       in freeze["section_2_arm_configuration_plan"]["arms"]
                       if a["arm_id"] == cell["arm_id"])
            assert cell["state_counts"]["states_undefined"] == \
                cfg["orthogonalization"]["min_past_points"] == 63

    def test_fold_partitions_sum_to_grid(self, committed_report):
        for cell in committed_report["cells"]:
            fp = cell["fold_partition"]
            assert sum(fp["folds_decisions"].values()) == 1918
            assert sorted(fp["folds_decisions"]) == ["1", "2", "3"]
            assert sum(fp["folds_state_events"].values()) == \
                cell["state_counts"]["state_events_nonzero"]
            assert set(fp["exit_reasons"]) <= set(EXIT_REASONS)
            assert sum(fp["exit_reasons"].values()) == \
                cell["state_counts"]["round_trips"]
            assert fp["fold_windows"] == [list(w) for w in
                                          z_run.FOLD_WINDOWS]

    def test_fill_counts_tie_to_round_trips(self, committed_report):
        for cell in committed_report["cells"]:
            fills = cell["fills"]
            assert fills["fills_total"] == \
                4 * cell["state_counts"]["round_trips"]
            assert fills["cost_events_total"] == \
                2 * cell["state_counts"]["round_trips"]
            assert fills["marks_total"] == \
                4 * cell["state_counts"]["round_trips"]
            assert fills["all_ledgers_dual_book_equality_ok"] is True
            # per ledger: 2 fills + 2 marks + 1 drag cost row per leg
            # round trip (orientation-sparse: only used combos exist)
            allowed = {
                f"{cell['arm_id']}|{leg}|{o}"
                for leg in ("SHY", "TLT") for o in ("LONG", "SHORT")}
            for name, led in fills["ledgers"].items():
                assert name in allowed
                assert led["fills"] % 2 == 0
                assert led["marks"] == led["fills"]
                assert led["cost_events"] == led["fills"] // 2
                assert led["dual_book_equality_ok"] is True
            assert fills["marks_total"] == fills["fills_total"]
            n_rt = cell["state_counts"]["round_trips"]
            assert len(fills["kernel_ledger_sha256"]) >= 2

    def test_fold_partition_law_frozen(self, committed_report):
        law = committed_report["identity"]["fold_partition_law"]
        assert law["window_day_span_exclusive"] == 2804
        assert law["window_matches_freeze_law"] is True
        assert law["folds_contiguous"] is True
        assert sum(law["fold_day_spans_inclusive"]) == \
            law["window_days_inclusive"]

    def test_pbo_fail_closed_below_8(self, committed_report):
        assert committed_report["pbo"]["status"] == \
            "NOT_RUN_FAIL_CLOSED_CELLS_LT_8"
        assert committed_report["pbo"]["n_cells"] == 3

    def test_battery_law_and_stages_recorded(self, committed_report):
        assert committed_report["battery_law"]["roles"] == \
            list(KILLER_ROLES)
        assert committed_report["battery_law"][
            "declared_executioner"] == \
            "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL"
        assert committed_report["battery_law"][
            "k_misalign_sessions"] == 5
        statuses = {s["stage"]: s["status"]
                    for s in committed_report["stages"]}
        assert set(statuses) == {
            "freeze_load", "cell_config_assembly",
            "freeze_artifact_pins", "plane_provenance",
            "representation_load", "cell_runs_battery", "sanitization"}
        assert all(v == "PASS" for v in statuses.values())


# ================================================================== #
# 4. Live real-substrate run: byte-determinism + verdict               #
# ================================================================== #

class TestLiveRealSubstrateRun:
    def test_live_run_reproduces_committed_report_bytes(
            self, live_payload, committed_bytes):
        assert z_run.build_report_bytes(live_payload) == committed_bytes

    def test_live_run_verdict_pass_and_sanitizer_clean(
            self, live_payload):
        assert live_payload["overall_verdict"] == "PASS"
        assert live_payload["sanitization"]["clean"] is True
        assert z_run.sanitize_payload(live_payload)["clean"] is True

    def test_cached_run_is_session_stable(self, live_payload):
        assert z_run.cached_payload() is live_payload

    def test_cells_end_to_end_through_i_machinery(
            self, live_payload):
        for cell in live_payload["cells"]:
            assert cell["end_to_end_ok"] is True
            assert cell["signed_surface_reconciliation_ok"] is True

    def test_battery_executability_recorded_honestly(
            self, live_payload):
        # Z judges PLUMBING, not outcomes: control executability is a
        # Q-11 structural record, never a verdict input.
        by_arm = {c["arm_id"]: c for c in live_payload["cells"]}
        neutral = by_arm["RATESNG1-A5-P1-ARM-NEUTRAL"]["battery"]
        aggressive = by_arm["RATESNG1-A5-P1-ARM-AGGRESSIVE"]["battery"]
        conservative = by_arm[
            "RATESNG1-A5-P1-ARM-CONSERVATIVE"]["battery"]
        assert neutral["battery_executed"] is True
        assert aggressive["battery_executed"] is True
        # the CONSERVATIVE anchor fires only 3 times on the real grid;
        # its k=5-shifted placebo shares NO aligned defined pair with
        # it -- recorded honestly as status FAIL / n_pairs_used 0.
        assert conservative["controls"]["PLACEBO"]["status"] == "FAIL"
        assert conservative["controls"]["PLACEBO"][
            "n_pairs_used"] == 0
        assert conservative["controls"]["PLACEBO"][
            "executable"] is False


# ================================================================== #
# 5. Negative controls: contamination caught, emission refused         #
# ================================================================== #

class TestNegativeContamination:
    @pytest.mark.parametrize("planted", [
        {"total_pnl": 1.0},
        {"expectancy": 0.01},
        {"x": [{"y": {"sharpe_ratio": 1.23}}]},
        {"profit_factor": 1.15},
        {"mean_edge": 0.003},          # Z-extended pattern
        {"family_kill": True},         # Z-extended pattern
        {"margin_vs_bound": 0.2},      # Z-extended pattern
        {"gross_win": 5.0},
    ])
    def test_planted_outcome_keys_caught(self, planted):
        payload = copy.deepcopy(z_run.cached_payload())
        payload.update(planted)
        scan = z_run.sanitize_payload(payload)
        assert scan["clean"] is False
        assert scan["leaks"], planted

    def test_planted_float_value_caught(self):
        payload = copy.deepcopy(z_run.cached_payload())
        payload["structural_note_section"] = {"note": "clean"}
        payload["structural_note_section"]["tuning_const"] = 0.37
        scan = z_run.sanitize_payload(payload)
        assert scan["clean"] is False
        assert scan["value_law_leaks"]
        assert scan["leaks"] == []          # key law NOT triggered

    def test_planted_bad_digest_caught(self):
        payload = copy.deepcopy(z_run.cached_payload())
        payload["digest_chain"]["selection_freeze_sha256"] = "deadbeef"
        scan = z_run.sanitize_payload(payload)
        assert scan["clean"] is False
        assert scan["digest_law_leaks"]

    def test_contaminated_emission_refused(self, tmp_path):
        bad = copy.deepcopy(z_run.cached_payload())
        bad["leak_probe"] = {"after_cost_expectancy": 0.01}
        target = tmp_path / "must_not_exist.json"
        with pytest.raises(z_run.ZSanitizationError):
            z_run.emit_report(bad, str(target))
        assert not target.exists()

    def test_clean_emission_writes_deterministic_bytes(
            self, tmp_path, live_payload):
        target = tmp_path / "ok.json"
        res = z_run.emit_report(live_payload, str(target))
        import hashlib
        assert res["artifact_sha256"] == hashlib.sha256(
            target.read_bytes()).hexdigest()
        assert target.read_bytes() == \
            z_run.build_report_bytes(live_payload)


# ================================================================== #
# 6. Negative controls: law refusals in the frozen machinery           #
# ================================================================== #

class TestLawRefusals:
    def test_tampered_arm_digest_refused(self, freeze):
        import copy as _copy
        tampered = _copy.deepcopy(freeze)
        arms = tampered["section_2_arm_configuration_plan"]["arms"]
        arms[0]["config"]["gate"]["upper_quantile"] = 0.51
        with pytest.raises(RunnerLawError, match="drift"):
            assemble_cell_configs(tampered)

    def test_tampered_arm_digest_string_refused(self, freeze):
        import copy as _copy
        tampered = _copy.deepcopy(freeze)
        arms = tampered["section_2_arm_configuration_plan"]["arms"]
        arms[1]["arm_config_digest"] = "0" * 64
        with pytest.raises(RunnerLawError, match="drift"):
            assemble_cell_configs(tampered)

    def test_cell_count_law_refused(self, freeze):
        import copy as _copy
        tampered = _copy.deepcopy(freeze)
        tampered["section_2_arm_configuration_plan"]["arms"] = \
            tampered["section_2_arm_configuration_plan"]["arms"][:2]
        with pytest.raises(RunnerLawError, match="exactly 3"):
            assemble_cell_configs(tampered)

    def test_fold_of_session_outside_windows_refused(self):
        with pytest.raises(RunnerLawError, match="outside"):
            fold_of_session("2018-12-31")
        with pytest.raises(RunnerLawError, match="outside"):
            fold_of_session("2026-09-14")


# ================================================================== #
# 7. Negative controls: plumbing failure => BLOCKED, honest            #
# ================================================================== #

class TestBlockedPrelaunchPath:
    def test_missing_substrate_reports_blocked_not_repaired(
            self, tmp_path):
        empty_raw_root = tmp_path / "no_substrate"
        empty_raw_root.mkdir()
        payload = z_run.run_z_dry_run(
            plane_kwargs={"raw_root": str(empty_raw_root)})
        assert payload["overall_verdict"] == \
            "BLOCKED_PRELAUNCH_CANDIDATE"
        assert payload["blocked"]["stage"] == "plane_provenance"
        assert payload["blocked"]["exc_type"] == "PlaneDataBlocked"
        statuses = {s["stage"]: s["status"]
                    for s in payload["stages"]}
        assert statuses["plane_provenance"] == "BLOCKED"
        assert statuses["freeze_load"] == "PASS"
        assert statuses["cell_config_assembly"] == "PASS"
        # the honest blocked record is itself structural-clean
        assert z_run.sanitize_payload(payload)["clean"] is True
        # and cells were NOT fabricated
        assert payload["cells"] == []

    def test_blocked_payload_still_emittable(self, tmp_path):
        empty_raw_root = tmp_path / "no_substrate"
        empty_raw_root.mkdir()
        payload = z_run.run_z_dry_run(
            plane_kwargs={"raw_root": str(empty_raw_root)})
        target = tmp_path / "blocked_report.json"
        res = z_run.emit_report(payload, str(target))
        assert res["wrote"] == str(target)
        assert target.exists()


# ================================================================== #
# Standalone execution                                                 #
# ================================================================== #

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
