"""COMMODITIES-NG1 Z sanitized dry-run tests (task commodities-ng1-z-dryrun).

Laws under test
---------------
1. SANITIZATION LAW of every committed Z artifact (the z_report.json and
   the per-cell manifests under research/control/commodities_ng1_run/z/):
   STRUCTURAL facts only -- no outcome-vocabulary key, no float value,
   no float literal inside any string; independent raw-text scan of the
   committed bytes.  The scanner itself is tested against violating
   fixtures (negative controls) and against benign strings (sha256 hex
   digests, ISO dates) it must NOT false-positive.
2. Digest + pin law: the driver refuses (fail-closed, ZRefused) on a
   tampered arm_config_digest, on an ETP leg whose measured bytes do not
   match the committed p2 substrate pin.
3. Census law: a chain whose reconstructed grid disagrees with the
   committed P2 census is RECORDED (verdict FAIL,
   blocked_data_or_selection_candidate) -- never repaired, never
   silently passed.
4. End-to-end driver law on a healthy SYNTHETIC substrate: the 3 frozen
   cell configs assemble digest-verified, every cell x pair x battery
   role books end-to-end (PASS), fold partitions sum to booked trades,
   fills == 2x booked trades (once-per-fill audit trail), Q-11 floors
   evaluate on the counted grid, and every emitted artifact passes the
   sanitizer.
5. Committed artifacts (skipped when absent): structural invariants of
   the REAL-substrate run -- grid 11 pairs x 401 counted instants,
   pooled 4411, Q-11 ELIGIBLE, census all verified, digest chains all
   green, PASS-row structural identities, and the honest incident set
   (the empty-population book_ledger reconciliation crash on
   RELEASE_CLOCK_SHADOW x WEAT/IAU: reported, not repaired => overall
   FAIL + BLOCKED_PRELAUNCH candidate).

No outcome number exists in any committed artifact; these tests enforce
exactly that.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKTREE))
Z_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run" / "z"
sys.path.insert(0, str(Z_DIR))

import z_run as ZR  # noqa: E402

from research.assets.commodities_ng1.runners.chain import (  # noqa: E402
    build_pair_chain,
)
from research.assets.commodities_ng1.runners.dry_run import (  # noqa: E402
    arm_config_digest,
)

RUN_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run"
Z_OUT = RUN_DIR / "z"
REPORT_PATH = Z_OUT / "z_report.json"
CELL_PATHS = sorted(Z_OUT.glob("cell_*.json"))

SCHEMA_REPORT = "commodities_ng1_run/z_report@1"
SCHEMA_CELL = "commodities_ng1_run/z_cell_manifest@1"

ALL_ROLES = ZR.ALL_ROLES
FOLD_IDS = ("fold-1", "fold-2", "fold-3")

# Independent scanner (NOT z_run's): same law, separate implementation.
_OUTCOME_VOCAB = ("pnl", "expectancy", "edge", "profit_factor", "sharpe",
                  "drawdown", "win_rate", "payoff", "gross", "net_",
                  "_net", "return_", "_return")
_FLOAT_TEXT = re.compile(
    r"(?<![\w.])-?\d+\.\d+(?![\w.])"
    r"|(?<![\w.])-?\d+[eE][-+]?\d+(?![\w.])")


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


def _walk_values(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield v
            yield from _walk_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield v
            yield from _walk_values(v)


def assert_sanitized(obj, name: str) -> None:
    """Independent enforcement of the sanitization law."""
    for k in _walk_keys(obj):
        kl = k.lower()
        for bad in _OUTCOME_VOCAB:
            assert bad not in kl, f"{name}: outcome-vocabulary key {k!r}"
    for v in _walk_values(obj):
        if isinstance(v, float):
            pytest.fail(f"{name}: float value in committed artifact")
        if isinstance(v, str):
            assert not _FLOAT_TEXT.search(v), \
                f"{name}: float literal in string {v!r}"


# ----------------------------------------------------------------------- #
# 1. Sanitizer negative + benign controls
# ----------------------------------------------------------------------- #

def test_sanitizer_refuses_contaminated_artifacts():
    with pytest.raises(ZR.ZSanitizationRefused):
        ZR.sanitize_artifact({"per_trade_edge": 1})          # outcome key
    with pytest.raises(ZR.ZSanitizationRefused):
        ZR.sanitize_artifact({"profit_factor_x": {"a": 1}})  # outcome key
    with pytest.raises(ZR.ZSanitizationRefused):
        ZR.sanitize_artifact({"count": 0.5})                 # float value
    with pytest.raises(ZR.ZSanitizationRefused):
        ZR.sanitize_artifact({"note": "pf was 1.2345 here"})  # hidden float
    with pytest.raises(ZR.ZSanitizationRefused):
        ZR.sanitize_artifact({"note": "value 1e-9 leak"})    # sci notation
    with pytest.raises(ZR.ZSanitizationRefused):
        ZR.sanitize_artifact({"when": object()})             # non-JSON type


def test_sanitizer_accepts_structural_facts_and_writer_refuses_dirty():
    clean = {"counts": [1, 2, 3], "verdict": "PASS", "when": "2019-01-04",
             "digest": "6c12044f88e5284297f50560587e041ccac3012454e965934"
                       "0b348eb5d6e67d8",
             "nested": {"ok": True, "none": None,
                        "pair": "001602/DBA", "schema": SCHEMA_CELL}}
    ZR.sanitize_artifact(clean)                     # must not raise
    suppressed, flag = ZR.suppress_float_text("edge was 0.0123 per trade")
    assert flag and "0.0123" not in suppressed \
        and suppressed.startswith("<suppressed-by-sanitizer sha256=")
    kept, flag = ZR.suppress_float_text("census verified on 11 pairs")
    assert not flag and kept == "census verified on 11 pairs"

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        dirty = os_path(td, "dirty.json")
        with pytest.raises(ZR.ZSanitizationRefused):
            ZR.write_sanitized_json(dirty, {"expectancy": 3})
        assert not Path(dirty).exists()             # nothing written
        ok = os_path(td, "clean.json")
        ZR.write_sanitized_json(ok, clean)
        assert json.loads(Path(ok).read_text()) == clean


def os_path(td: str, name: str) -> str:
    return str(Path(td) / name)


# ----------------------------------------------------------------------- #
# 2. Synthetic healthy substrate: full end-to-end PASS
# ----------------------------------------------------------------------- #

N_PAIRS = 11
N_REPORTS = 365                      # counted = 365 - 52 warmup = 313 >= 300
BOOKABLE = [f"{1000 + i:06d}/TESTLEG" for i in range(N_PAIRS)]
ARMS = (
    {"arm_id": "COMMNG1-A4-P2-ARM1-NEUTRAL", "role": "ANCHOR",
     "params": {"percentile_window_weeks_w": 104, "tail_q_lo": 0.1,
                "tail_q_hi": 0.9, "trigger_tau_geometry": 0.02,
                "carry_bound_weeks_h_max": 13}},
    {"arm_id": "COMMNG1-A4-P2-ARM2-TAILWIDE", "role": "NEIGHBOUR",
     "params": {"percentile_window_weeks_w": 104, "tail_q_lo": 0.2,
                "tail_q_hi": 0.8, "trigger_tau_geometry": 0.02,
                "carry_bound_weeks_h_max": 13}},
    {"arm_id": "COMMNG1-A4-P2-ARM3-WINDOWSHORT", "role": "NEIGHBOUR",
     "params": {"percentile_window_weeks_w": 52, "tail_q_lo": 0.1,
                "tail_q_hi": 0.9, "trigger_tau_geometry": 0.02,
                "carry_bound_weeks_h_max": 13}},
)


def _sessions(d0: date, n: int) -> list:
    out, d = [], d0
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _tuesdays(d0: date, n: int) -> list:
    out, d = [], d0
    while len(out) < n:
        if d.weekday() == 1:
            out.append(d)
        d += timedelta(days=1)
    return out


def _reports(reps: list, salt: int) -> list:
    return [{"report_date": d, "open_interest": 1000,
             "noncomm_long": (i * 37 + salt) % 900, "noncomm_short": 100,
             "noncomm_spreading": 0, "comm_long": 50,
             "comm_short": ((i * 11) + salt) % 400}
            for i, d in enumerate(reps)]


def _synthetic_freeze() -> dict:
    arms = []
    for a in ARMS:
        cfg = {"family": "COMMNG1-A4-P2",
               "parameters": a["params"],
               "bookable_pairs": list(BOOKABLE),
               "cost_treatment": {"primary_tier": 2.0}}
        arms.append({"arm_id": a["arm_id"], "role": a["role"],
                     "family": "COMMNG1-A4-P2", "arm_config": cfg,
                     "arm_config_digest": arm_config_digest(cfg),
                     "selection_status": "BOOKED"})
    return {
        "schema": "synthetic_freeze_for_z_tests@1",
        "frozen_at_utc": "2026-09-14T00:00:00Z",
        "section2_arm_plan": {
            "single_family": "COMMNG1-A4-P2",
            "trial_budget_cells": 6,
            "booked_cells": 3,
            "unbooked_cells": 3,
            "arms": arms,
            "bookable_set": {"pairs": list(BOOKABLE)},
        },
        "trial_accounting": {
            "trial_budget_cells": 6, "booked_cells": 3, "unbooked_cells": 3,
            "booked_arm_ids": [a["arm_id"] for a in arms],
        },
    }


def _synthetic_census(chain: dict, pid: str) -> dict:
    """The committed P2 floor-evaluation echo, computed from the SAME
    synthetic chain (the census identity must hold for healthy runs)."""
    from research.assets.commodities_ng1.feasibility import (
        WARMUP_WEEKS, WINDOW_START,
    )
    rows = chain["rows"]
    window_rows = [i for i, r in enumerate(rows)
                   if r["release_date"] >= WINDOW_START]
    counted_window = window_rows[WARMUP_WEEKS:]
    mapped = [i for i in counted_window
              if rows[i]["decision_session"] is not None]
    return {"counted_expected_releases": len(counted_window),
            "grid_eligible_instants": len(mapped),
            "counted_first_release":
                rows[mapped[0]]["release_date"].isoformat(),
            "counted_last_release":
                rows[counted_window[-1]]["release_date"].isoformat(),
            "unmapped_release_dates_counted": []}


def _synthetic_contract() -> dict:
    return {"per_leg": {"TESTLEG": {
        "half_spread_frac_p90_per_fill": 0.002,
        "expense_fact": {"expense_ratio_annual": 0.05},
        "tracking_proxy": None,
        "spread": {"share_base_events": []}}}}


def _synthetic_substrate(pin_ok: bool = True) -> dict:
    sessions = _sessions(date(2017, 12, 1), 2200)
    closes = {s: 100.0 + ((i * 7) % 23) * 0.5 for i, s in
              enumerate(sessions)}
    reps = _tuesdays(date(2018, 1, 2), N_REPORTS)
    cot = {}
    for i, pid in enumerate(BOOKABLE):
        code = pid.split("/")[0]
        cot[code] = _reports(reps, salt=i * 13)
    chains = {pid: build_pair_chain(
        cot[pid.split("/")[0]], sessions, closes) for pid in BOOKABLE}
    p2 = {"per_pair_census": {
        pid: {"floor_evaluation": _synthetic_census(chains[pid], pid)}
        for pid in BOOKABLE},
        "substrate_pins": {"etp_eod_sha256": {}}}
    leg_ctx = {"TESTLEG": {"session_dates": sessions,
                           "session_closes": closes,
                           "etp_pin_match": pin_ok}}
    plane_rows = [{"entry": "synthetic/cot", "digest_match": True,
                   "bytes": 1234}]
    etp_rows = [{"leg": "TESTLEG", "digest_match": True,
                 "etp_pin_match": pin_ok, "sessions": len(sessions)}]
    return {"freeze": _synthetic_freeze(), "p2": p2,
            "contract": _synthetic_contract(),
            "substrate": {"cot_by_code": cot, "leg_ctx": leg_ctx,
                          "plane_digest_rows": plane_rows,
                          "etp_digest_rows": etp_rows}}


@pytest.fixture(scope="module")
def healthy_run(tmp_path_factory):
    fx = _synthetic_substrate()
    out = str(tmp_path_factory.mktemp("z_healthy"))
    result = ZR.run_zdryun(fx["freeze"], fx["p2"], fx["contract"],
                           fx["substrate"], out, str(WORKTREE),
                           freeze_sha256="0" * 64, p2_sha256="1" * 64,
                           contract_sha256="2" * 64)
    report = ZR.finish_report(out, result)
    return result, report, out


def test_synthetic_end_to_end_all_cells_pass(healthy_run):
    result, report, out = healthy_run
    assert report["overall_verdict"] == "PASS"
    assert report["blocked_prelaunch_candidate"] is False
    assert report["provenance"]["branch"] == ZR.head_and_branch(
        str(WORKTREE))["branch"]
    # grid + Q-11 on the synthetic counted grid (fail-closed floors met)
    assert report["grid"]["bookable_pair_count"] == N_PAIRS
    assert report["grid"]["counted_instants_per_pair"][BOOKABLE[0]] \
        == N_REPORTS - 52
    assert report["q11_eligibility"]["eligible_overall"] is True
    assert report["grid"]["census_identity_all_verified"] is True
    assert report["config_assembly"]["all_digests_match"] is True
    assert report["config_assembly"]["digests_pairwise_distinct"] is True
    assert len(report["config_assembly"]["arm_config_digests"]) == 3
    # every cell x pair x role executed end-to-end
    for arm_id, mf in result["cells"].items():
        assert mf["cell_pipeline_executable_verdict"] == "PASS"
        assert mf["cell_failures"] == []
        for pid, prow in mf["per_pair"].items():
            assert len(prow["roles"]) == len(ALL_ROLES)
            for role, v in prow["roles"].items():
                assert v["control_executable_verdict"] == "PASS", \
                    (arm_id, pid, role, v)
                assert v["fills"] == 2 * v["trades_booked"]
                assert v["fold_partition_total_matches_trades"] is True
                assert sum(v["fold_partition_counts"].values()) \
                    == v["trades_booked"]
                assert set(v["fold_partition_counts"]) == set(FOLD_IDS)
                assert len(v["outcome_payload_sha256"]) == 64
        for role, v in mf["pooled_roles"].items():
            assert v["control_executable_verdict"] == "PASS"
            assert v["eligible_instants"] == N_PAIRS * (N_REPORTS - 52)


def test_synthetic_artifacts_written_and_sanitized(healthy_run):
    result, report, out = healthy_run
    written = sorted(Path(out).glob("*.json"))
    assert len(written) == 4                       # 3 cells + z_report
    for p in written:
        obj = json.loads(p.read_text())
        assert_sanitized(obj, p.name)
    # manifest digests recorded in the report match the committed bytes
    for arm_id, cell in report["cells"].items():
        path = Path(out) / f"cell_{arm_id}.json"
        assert cell["manifest_sha256"] == \
            hashlib.sha256(path.read_bytes()).hexdigest()
    assert report["z_report_sha256"] == \
        hashlib.sha256((Path(out) / "z_report.json").read_bytes()) \
        .hexdigest()


# ----------------------------------------------------------------------- #
# 3. Fail-closed refusals (digest / pin / census)
# ----------------------------------------------------------------------- #

def test_tampered_arm_digest_refused(tmp_path):
    fx = _synthetic_substrate()
    fx["freeze"]["section2_arm_plan"]["arms"][0]["arm_config_digest"] = \
        "9" * 64
    with pytest.raises(ZR.ZRefused):
        ZR.run_zdryun(fx["freeze"], fx["p2"], fx["contract"],
                      fx["substrate"], str(tmp_path), str(WORKTREE))


def test_etp_pin_mismatch_refused(tmp_path):
    fx = _synthetic_substrate()
    fx["p2"]["substrate_pins"]["etp_eod_sha256"] = {"TESTLEG": "pin"}
    fx["substrate"]["leg_ctx"]["TESTLEG"]["etp_pin_match"] = False
    with pytest.raises(ZR.ZRefused):
        ZR.run_zdryun(fx["freeze"], fx["p2"], fx["contract"],
                      fx["substrate"], str(tmp_path), str(WORKTREE))


def test_census_mismatch_recorded_not_repaired(tmp_path):
    fx = _synthetic_substrate()
    pid = fx["p2"]["per_pair_census"][BOOKABLE[0]]
    pid["floor_evaluation"]["grid_eligible_instants"] += 1   # tampered
    result = ZR.run_zdryun(fx["freeze"], fx["p2"], fx["contract"],
                           fx["substrate"], str(tmp_path), str(WORKTREE))
    report = ZR.finish_report(str(tmp_path), result)
    assert report["overall_verdict"] == "FAIL"
    assert report["blocked_prelaunch_candidate"] is False
    assert report["blocked_data_or_selection_candidate"] is True
    prow = result["pair_rows"][BOOKABLE[0]]
    assert prow["chain_built"] is True
    assert prow["census_identity_verified"] is False
    assert prow["failure_class"] == "ChainRefused"
    roles = result["cells"][ARMS[0]["arm_id"]][
        "per_pair"][BOOKABLE[0]]["roles"]
    assert all(v["control_executable_verdict"] == "FAIL"
               and v["failure_class"] == "PAIR_CENSUS_UNVERIFIED"
               for v in roles.values())


# ----------------------------------------------------------------------- #
# 4. Committed REAL-substrate artifacts (skipped when absent)
# ----------------------------------------------------------------------- #

requires_artifacts = pytest.mark.skipif(
    not REPORT_PATH.is_file() or len(CELL_PATHS) < 3,
    reason="committed z artifacts absent (run z_run.py --run first)")


class TestCommittedArtifacts:

    @requires_artifacts
    def test_every_committed_artifact_is_sanitized(self):
        for p in [REPORT_PATH] + CELL_PATHS:
            obj = json.loads(p.read_text(encoding="utf-8"))
            ZR.sanitize_artifact(obj, p.name)       # z_run's scanner
            assert_sanitized(obj, p.name)           # independent scanner

    @requires_artifacts
    def test_report_schemas_verdict_and_provenance(self):
        r = json.loads(REPORT_PATH.read_text())
        assert r["schema"] == SCHEMA_REPORT
        assert r["cycle_id"] == "COMMODITIES-NG1"
        assert r["task_id"] == "commodities-ng1-z-dryrun"
        assert r["overall_verdict"] in {"PASS", "FAIL"}
        assert r["fail_closed"] is True
        assert isinstance(r["blocked_prelaunch_candidate"], bool)
        assert r["overall_verdict"] == "FAIL" or (
            r["blocked_prelaunch_candidate"] is False
            and r["incident_count"] == 0)
        proven = r["provenance"]
        assert proven["head_sha"] == ZR.PACKET_BASE_SHA
        assert proven["branch"] == "orca/commodities-ng1-integration"
        assert proven["head_matches_packet_base"] is True

    @requires_artifacts
    def test_report_structural_invariants(self):
        r = json.loads(REPORT_PATH.read_text())
        g = r["grid"]
        assert g["bookable_pair_count"] == 11
        assert set(g["counted_instants_per_pair"].values()) == {401}
        assert g["pooled_counted_instants"] == 4411
        assert g["census_identity_all_verified"] is True
        # holiday-shifted Mondays: the measured 6 per market x 11 pairs
        assert g["rule_source_counts_pooled"] == {
            "p0_release_instant": 11 * 552,
            "week_anchor_holiday_shift": 11 * 6}
        assert g["unmapped_counted_release_dates_union"] == ["2026-09-11"]
        q = r["q11_eligibility"]
        assert q["pooled"] == {"eligible_instants": 4411, "minimum": 3300,
                               "verdict": "ELIGIBLE"}
        assert q["eligible_overall"] is True
        d = r["substrate_digest_chains"]
        assert d["plane_entries_all_digest_ok"] is True
        assert d["etp_legs_all_pin_ok"] is True
        assert len(d["plane_digest_rows"]) == 11       # deacot2016..2026
        assert len(d["etp_digest_rows"]) == 9          # bookable legs
        ca = r["config_assembly"]
        assert ca["booked_cells"] == 3 and ca["unbooked_cells"] == 3
        assert ca["trial_budget_cells"] == 6
        assert ca["all_digests_match"] is True
        assert ca["digests_pairwise_distinct"] is True

    @requires_artifacts
    def test_cell_manifests_structure_and_pass_row_identities(self):
        arm_ids = set()
        for p in CELL_PATHS:
            m = json.loads(p.read_text())
            assert m["schema"] == SCHEMA_CELL
            assert m["arm_config_digest_match"] is True
            assert m["falsification_rehearsed"] is True
            assert len(m["cell_falsification_outcome_payload_sha256"]) == 64
            assert set(m["parameters_integer_echo"]) == {
                "percentile_window_weeks_w", "carry_bound_weeks_h_max"}
            arm_ids.add(m["arm_id"])
            assert len(m["per_pair"]) == 11
            for pid, prow in m["per_pair"].items():
                assert prow["census_identity_verified"] is True
                assert prow["counted_instants"] == 401
                for role, v in prow["roles"].items():
                    assert role in ALL_ROLES
                    if v["control_executable_verdict"] == "PASS":
                        assert v["fills"] == 2 * v["trades_booked"]
                        assert v["fold_partition_total_matches_trades"] \
                            is True
                        assert sum(
                            v["fold_partition_counts"].values()) \
                            == v["trades_booked"]
                        assert len(v["outcome_payload_sha256"]) == 64
                    else:
                        assert v["failure_class"]
        assert arm_ids == set(json.loads(
            REPORT_PATH.read_text())["freeze"]["booked_arm_ids"])

    @requires_artifacts
    def test_report_incidents_match_cell_failures_and_verdict(self):
        r = json.loads(REPORT_PATH.read_text())
        incidents = r["incidents"]
        assert r["incident_count"] == len(incidents)
        n_cell_failures = sum(c["cell_failure_count"]
                              for c in r["cells"].values())
        assert len(incidents) == n_cell_failures
        if r["overall_verdict"] == "PASS":
            assert incidents == []
            return
        # honest BLOCKED_PRELAUNCH reporting of the localized defect set
        assert r["blocked_prelaunch_candidate"] is True
        for i in incidents:
            assert i["arm_id"] in r["cells"]
            assert i["failure_class"] and i["failure_stage"]

    @requires_artifacts
    def test_committed_incidents_are_the_localized_defect_set(self):
        r = json.loads(REPORT_PATH.read_text())
        expected = {
            ("COMMNG1-A4-P2-ARM1-NEUTRAL", "001602/WEAT",
             "RELEASE_CLOCK_SHADOW"),
            ("COMMNG1-A4-P2-ARM1-NEUTRAL", "088691/IAU",
             "RELEASE_CLOCK_SHADOW"),
            ("COMMNG1-A4-P2-ARM2-TAILWIDE", "001602/WEAT",
             "RELEASE_CLOCK_SHADOW"),
            ("COMMNG1-A4-P2-ARM2-TAILWIDE", "088691/IAU",
             "RELEASE_CLOCK_SHADOW"),
            ("COMMNG1-A4-P2-ARM3-WINDOWSHORT", "001602/WEAT",
             "RELEASE_CLOCK_SHADOW"),
            ("COMMNG1-A4-P2-ARM3-WINDOWSHORT", "088691/IAU",
             "RELEASE_CLOCK_SHADOW"),
        }
        got = {(i["arm_id"], i["pair"], i["role"]) for i in r["incidents"]}
        assert got == expected
        assert all(i["failure_class"] == "TypeError"
                   and i["failure_stage"] == "booking"
                   for i in r["incidents"])

    @requires_artifacts
    def test_manifest_digests_recorded_in_report_match_bytes(self):
        r = json.loads(REPORT_PATH.read_text())
        for arm_id, cell in r["cells"].items():
            path = Z_OUT / f"cell_{arm_id}.json"
            assert path.is_file()
            assert cell["manifest_sha256"] == \
                hashlib.sha256(path.read_bytes()).hexdigest()

    @requires_artifacts
    def test_pass_rows_release_clock_shape_on_clean_legs(self):
        """Structural sanity of the rehearsal on a boundary-free leg:
        the bare release clock holds every counted instant and books
        exactly one lifetime trade per pair (entry at the first counted
        release, terminal close at the last observable mark)."""
        m = json.loads(
            (Z_OUT / "cell_COMMNG1-A4-P2-ARM1-NEUTRAL.json").read_text())
        prow = m["per_pair"]["001602/DBA"]["roles"]["RELEASE_CLOCK_SHADOW"]
        assert prow["control_executable_verdict"] == "PASS"
        assert prow["held_decision_count"] == 401
        assert prow["flat_decision_count"] == 0
        assert prow["trades_booked"] == 1 and prow["fills"] == 2
