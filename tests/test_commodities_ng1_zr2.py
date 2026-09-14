"""COMMODITIES-NG1 Z-R2 STRUCTURAL RE-PASS tests (task
commodities-ng1-zr2-repass).

Laws under test
---------------
1. SANITIZATION LAW of every committed Z-R2 artifact (the
   ``zr2_report.json`` and the per-cell manifests under
   ``research/control/commodities_ng1_run/zr2/``): STRUCTURAL facts
   only -- no outcome-vocabulary key, no float value, no float literal
   inside any string; enforced twice (the driver's fail-closed scanner
   and an independent implementation) over the parsed objects AND as a
   raw-text scan of the committed bytes.  The scanner itself is tested
   against violating fixtures (negative controls).
2. DECLARED-NOT_EXECUTABLE LAW (the Z-R1 remediation consumed here):
   an empty booked population is a DECLARED outcome with reason +
   excluded-trades disclosure and NO kernel book and NO root
   reconciliation invoked -- never a crash, never a silent pass, never
   an inferred number.  ``validate_declared_row`` refuses any row
   missing the declaration, the disclosure, or carrying a book.
3. CLEARANCE LAW: the 6 original Z incidents clear iff the declared
   ``NOT_EXECUTABLE`` coordinates EQUAL the original incident
   coordinates (``clearance_of``; mismatches are listed, never
   silently absorbed).
4. EVIDENCE-INTEGRITY LAW: ``load_evidence`` refuses (fail-closed)
   when any pinned evidence byte (original Z report, Z-R1 addendum,
   freeze, p2 gate, p1 cost contract) is tampered.
5. End-to-end driver law on SYNTHETIC substrates: a healthy substrate
   books every cell x pair x role PASS (no declared rows); a
   boundary-swallowing substrate (a committed share-base boundary
   inside every holding window) yields DECLARED NOT_EXECUTABLE rows --
   exactly the Z-incident mechanism -- without a crash, and the cell
   pipeline still verdicts PASS (a declared outcome is not a failure).
6. Committed REAL-substrate artifacts (skipped when absent): the
   acceptance battery -- overall PASS with ZERO incidents, the 6
   declared rows at exactly the original WEAT/IAU release-clock
   coordinates, census identity 11 pairs x 401 instants, 3 arm digests
   matching the Z-R1 addendum pins, fills == 2x trades and kernel
   reconciliation on every PASS row, fold partitions, PASS-row parity
   against the READ-ONLY original Z report, and the evidence digest
   chains.

No outcome number exists in any committed artifact; these tests
enforce exactly that.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKTREE))
ZR2_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run" / "zr2"
sys.path.insert(0, str(ZR2_DIR))

import zr2_run as Z2  # noqa: E402

from research.assets.commodities_ng1.runners.chain import (  # noqa: E402
    build_pair_chain,
)
from research.assets.commodities_ng1.runners.dry_run import (  # noqa: E402
    arm_config_digest,
)
from research.assets.commodities_ng1.runners.stage_a import (  # noqa: E402
    FOLDS_FROZEN,
)

RUN_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run"
ZR2_OUT = RUN_DIR / "zr2"
REPORT_PATH = ZR2_OUT / "zr2_report.json"
CELL_PATHS = sorted(ZR2_OUT.glob("cell_*.json"))
ORIGINAL_Z_REPORT = RUN_DIR / "z" / "z_report.json"
ADDENDUM = RUN_DIR / "s" / "selection_freeze_addendum_zr1.json"

SCHEMA_REPORT = "commodities_ng1_run/zr2_report@1"
SCHEMA_CELL = "commodities_ng1_run/zr2_cell_manifest@1"

ALL_ROLES = Z2.ALL_ROLES
NOT_EXECUTABLE = "NOT_EXECUTABLE"
FOLD_IDS = tuple(f["fold_id"] for f in FOLDS_FROZEN)

#: The 6 original Z-report incident coordinates (READ-ONLY evidence).
ORIGINAL_COORDINATES = sorted(
    (arm, pair, "RELEASE_CLOCK_SHADOW")
    for arm in ("COMMNG1-A4-P2-ARM1-NEUTRAL",
                "COMMNG1-A4-P2-ARM2-TAILWIDE",
                "COMMNG1-A4-P2-ARM3-WINDOWSHORT")
    for pair in ("001602/WEAT", "088691/IAU"))

# Independent scanner (NOT zr2_run's): same law, separate implementation.
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


def assert_sanitized_raw_bytes(path: Path) -> None:
    """Raw-text scan of the committed bytes: no float literal can hide
    outside JSON string semantics."""
    text = path.read_text(encoding="utf-8")
    assert not _FLOAT_TEXT.search(text), \
        f"{path.name}: float literal in the raw committed bytes"


# ----------------------------------------------------------------------- #
# 1. Sanitizer negative + benign controls
# ----------------------------------------------------------------------- #

def test_sanitizer_refuses_contaminated_artifacts():
    with pytest.raises(Z2.ZSanitizationRefused):
        Z2.sanitize_artifact({"per_trade_edge": 1})          # outcome key
    with pytest.raises(Z2.ZSanitizationRefused):
        Z2.sanitize_artifact({"profit_factor_x": {"a": 1}})  # outcome key
    with pytest.raises(Z2.ZSanitizationRefused):
        Z2.sanitize_artifact({"count": 0.5})                 # float value
    with pytest.raises(Z2.ZSanitizationRefused):
        Z2.sanitize_artifact({"note": "pf was 1.2345 here"})  # hidden float
    with pytest.raises(Z2.ZSanitizationRefused):
        Z2.sanitize_artifact({"note": "value 1e-9 leak"})    # sci notation
    with pytest.raises(Z2.ZSanitizationRefused):
        Z2.sanitize_artifact({"when": object()})             # non-JSON type


def test_sanitizer_accepts_structural_facts():
    clean = {"counts": [1, 2, 3], "verdict": "PASS", "when": "2019-01-04",
             "digest": "6c12044f88e5284297f50560587e041ccac3012454e965934"
                       "0b348eb5d6e67d8",
             "declared_row": {"verdict": NOT_EXECUTABLE, "declared": True,
                              "excluded_trades": 1, "why": None,
                              "book": None, "recon": None},
             "nested": {"ok": True, "pair": "001602/DBA",
                        "schema": SCHEMA_CELL}}
    Z2.sanitize_artifact(clean)                     # must not raise
    suppressed, flag = Z2.suppress_float_text("edge was 0.0123 per trade")
    assert flag and "0.0123" not in suppressed \
        and suppressed.startswith("<suppressed-by-sanitizer sha256=")
    kept, flag = Z2.suppress_float_text("census verified on 11 pairs")
    assert not flag and kept == "census verified on 11 pairs"


def test_writer_refuses_dirty_and_writes_clean(tmp_path):
    dirty = tmp_path / "dirty.json"
    with pytest.raises(Z2.ZSanitizationRefused):
        Z2.write_sanitized_json(str(dirty), {"expectancy": 3})
    assert not dirty.exists()                       # nothing written
    ok = tmp_path / "clean.json"
    digest = Z2.write_sanitized_json(str(ok), {"verdicts": ["PASS"],
                                               "n": 7})
    assert json.loads(ok.read_text()) == {"verdicts": ["PASS"], "n": 7}
    assert digest == hashlib.sha256(ok.read_bytes()).hexdigest()


# ----------------------------------------------------------------------- #
# 2. Declared-NOT_EXECUTABLE row law + clearance law
# ----------------------------------------------------------------------- #

def _declared_row_ok() -> dict:
    return {"schema": "commodities_ng1/runners/execute@1",
            "item": "book_ledger", "verdict": NOT_EXECUTABLE,
            "declared": True,
            "outcome_class": "EMPTY_BOOKED_POPULATION",
            "booked_trades": 0, "excluded_trades": 1,
            "reason": "every booked trade was excluded by the "
                      "split-boundary law",
            "disclosure": "empty booked population: declared "
                          "NOT_EXECUTABLE with disclosure",
            "kernel_book": None, "reconciliation": None}


def test_validate_declared_row_accepts_the_declared_shape():
    Z2.validate_declared_row(_declared_row_ok(), "fixture")  # must not raise


def test_validate_declared_row_refuses_degenerate_rows():
    base = _declared_row_ok()
    for mutate, why in (
        ({"verdict": "PASS"}, "not declared verdict"),
        ({"declared": False}, "not declared"),
        ({"outcome_class": "SOMETHING_ELSE"}, "wrong outcome class"),
        ({"reason": ""}, "no reason"),
        ({"reason": None}, "null reason"),
        ({"disclosure": ""}, "no disclosure"),
        ({"kernel_book": {"trades": 1}}, "carries a book"),
        ({"reconciliation": {"identity_ok": True}}, "carries a recon"),
        ({"booked_trades": 3}, "nonzero booked trades"),
    ):
        row = dict(base, **mutate)
        with pytest.raises(Z2.ZRefused):
            Z2.validate_declared_row(row, why)


def test_clearance_of_matches_and_mismatches():
    ok = Z2.clearance_of(ORIGINAL_COORDINATES, ORIGINAL_COORDINATES)
    assert ok["coordinate_match"] is True
    assert ok["missing_declarations"] == []
    assert ok["new_declarations"] == []
    assert ok["declared_count"] == 6
    bad = Z2.clearance_of(
        ORIGINAL_COORDINATES[:5]
        + [("COMMNG1-A4-P2-ARM1-NEUTRAL", "084691/SLV",
            "RELEASE_CLOCK_SHADOW")],
        ORIGINAL_COORDINATES)
    assert bad["coordinate_match"] is False
    assert bad["missing_declarations"] == [list(
        ("COMMNG1-A4-P2-ARM3-WINDOWSHORT", "088691/IAU",
         "RELEASE_CLOCK_SHADOW"))]
    assert bad["new_declarations"] == [list(
        ("COMMNG1-A4-P2-ARM1-NEUTRAL", "084691/SLV",
         "RELEASE_CLOCK_SHADOW"))]


# ----------------------------------------------------------------------- #
# 3. Synthetic substrates: healthy PASS + declared-row mechanism
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
        "schema": "synthetic_freeze_for_zr2_tests@1",
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


def _synthetic_contract(boundary: date | None = None) -> dict:
    events = [] if boundary is None else \
        [{"boundary_date": boundary.isoformat(),
          "law": "synthetic committed share-base boundary"}]
    return {"per_leg": {"TESTLEG": {
        "half_spread_frac_p90_per_fill": 0.002,
        "expense_fact": {"expense_ratio_annual": 0.05},
        "tracking_proxy": None,
        "spread": {"share_base_events": events}}}}


def _synthetic_bundle(boundary: date | None = None) -> dict:
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
                           "etp_pin_match": True}}
    plane_rows = [{"entry": "synthetic/cot", "digest_match": True,
                   "bytes": 1234}]
    etp_rows = [{"leg": "TESTLEG", "digest_match": True,
                 "etp_pin_match": True, "sessions": len(sessions)}]
    return {"freeze": _synthetic_freeze(), "p2": p2,
            "contract": _synthetic_contract(boundary),
            "substrate": {"cot_by_code": cot, "leg_ctx": leg_ctx,
                          "plane_digest_rows": plane_rows,
                          "etp_digest_rows": etp_rows}}


def _run_synthetic(fx: dict, out: str) -> dict:
    return Z2.run_zr2(fx["freeze"], fx["p2"], fx["contract"],
                      fx["substrate"], out, str(WORKTREE),
                      freeze_sha256="0" * 64, p2_sha256="1" * 64,
                      contract_sha256="2" * 64,
                      evidence=None)            # synthetic: no evidence


@pytest.fixture(scope="module")
def healthy_run(tmp_path_factory):
    fx = _synthetic_bundle()
    out = str(tmp_path_factory.mktemp("zr2_healthy"))
    result = _run_synthetic(fx, out)
    report = Z2.finish_report(out, result)
    return result, report, out


def test_synthetic_healthy_end_to_end_all_pass(healthy_run):
    result, report, out = healthy_run
    assert report["overall_verdict"] == "PASS"
    assert report["blocked_prelaunch_candidate"] is False
    assert report["incident_count"] == 0
    assert report["provenance"]["branch"] == Z2.head_and_branch(
        str(WORKTREE))["branch"]
    assert report["grid"]["bookable_pair_count"] == N_PAIRS
    assert report["q11_eligibility"]["eligible_overall"] is True
    assert report["grid"]["census_identity_all_verified"] is True
    assert report["config_assembly"]["all_digests_match"] is True
    assert report["config_assembly"]["digests_pairwise_distinct"] is True
    # synthetic rehearsal mode: the real-evidence parity sections are
    # out of scope and recorded as not evaluated (never inferred)
    assert report["original_incident_clearance"]["evaluated"] is False
    assert report["pass_row_parity"]["evaluated"] is False
    for arm_id, mf in result["cells"].items():
        assert mf["cell_pipeline_executable_verdict"] == "PASS"
        assert mf["cell_failures"] == []
        assert mf["declared_not_executable_rows"] == []
        for pid, prow in mf["per_pair"].items():
            assert len(prow["roles"]) == len(ALL_ROLES)
            for role, v in prow["roles"].items():
                assert v["control_executable_verdict"] == "PASS", \
                    (arm_id, pid, role, v)
                assert v["fills"] == 2 * v["trades_booked"]
                assert v["reconciliation_identity_ok"] is True
                assert v["kernel_book_invoked"] is True
                assert sum(v["fold_partition_counts"].values()) \
                    == v["trades_booked"]
                assert len(v["outcome_payload_sha256"]) == 64


def test_synthetic_healthy_artifacts_sanitized(healthy_run):
    result, report, out = healthy_run
    written = sorted(Path(out).glob("*.json"))
    assert len(written) == 4                       # 3 cells + zr2_report
    for p in written:
        obj = json.loads(p.read_text())
        assert_sanitized(obj, p.name)
        assert_sanitized_raw_bytes(p)
    for arm_id, cell in report["cells"].items():
        path = Path(out) / f"cell_{arm_id}.json"
        assert cell["manifest_sha256"] == \
            hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def declared_run(tmp_path_factory):
    """The Z-incident mechanism, reproduced synthetically: ONE
    committed share-base boundary inside every holding window of the
    leg.  The bare release clock books exactly ONE lifetime trade per
    pair; the split-boundary law excludes it; the booked population is
    EMPTY -> DECLARED NOT_EXECUTABLE (never a crash)."""
    fx = _synthetic_bundle(boundary=_sessions(date(2017, 12, 1),
                                              2200)[1100])
    out = str(tmp_path_factory.mktemp("zr2_declared"))
    result = _run_synthetic(fx, out)
    report = Z2.finish_report(out, result)
    return result, report, out


def test_synthetic_boundary_swallow_yields_declared_rows_no_crash(
        declared_run):
    result, report, out = declared_run
    # NO crash and NO silent failure: the pipeline completes with the
    # declared outcome rows and the cells still verdict PASS.
    assert report["overall_verdict"] == "PASS"
    assert report["incident_count"] == 0
    for arm_id, mf in result["cells"].items():
        assert mf["cell_pipeline_executable_verdict"] == "PASS"
        assert mf["cell_failures"] == []
        for pid, prow in mf["per_pair"].items():
            v = prow["roles"]["RELEASE_CLOCK_SHADOW"]
            assert v["control_executable_verdict"] == NOT_EXECUTABLE
            assert v["declared"] is True
            assert v["declared_outcome_class"] == "EMPTY_BOOKED_POPULATION"
            assert v["trades_booked"] == 0 and v["fills"] == 0
            assert v["excluded_trades"] == 1 \
                and v["split_boundary_excluded_trades"] == 1
            assert v["kernel_book_invoked"] is False
            assert v["root_reconciliation_invoked"] is False
            assert v["reconciliation_identity_ok"] is None
            assert v["declared_reason"] and v["declared_disclosure"]
            assert v["held_decision_count"] == prow["counted_instants"]
            # every OTHER role still books non-empty and reconciles
            for role, w in prow["roles"].items():
                if role == "RELEASE_CLOCK_SHADOW":
                    continue
                assert w["control_executable_verdict"] == "PASS", \
                    (arm_id, pid, role)
                assert w["reconciliation_identity_ok"] is True
        # pooled release-clock book is ALSO empty on this synthetic
        # substrate: declared, never crashed
        pooled = mf["pooled_roles"]["RELEASE_CLOCK_SHADOW"]
        assert pooled["control_executable_verdict"] == NOT_EXECUTABLE
        assert pooled["kernel_book_invoked"] is False
    # declared coordinates = RELEASE_CLOCK_SHADOW x 11 pairs x 3 arms
    coords = Z2.declared_coordinates(result["cells"])
    assert len(coords) == 3 * N_PAIRS
    assert {c[2] for c in coords} == {"RELEASE_CLOCK_SHADOW"}


def test_synthetic_declared_run_artifacts_sanitized(declared_run):
    result, report, out = declared_run
    for p in sorted(Path(out).glob("*.json")):
        obj = json.loads(p.read_text())
        Z2.sanitize_artifact(obj, p.name)          # driver's scanner
        assert_sanitized(obj, p.name)              # independent scanner
        assert_sanitized_raw_bytes(p)


def test_synthetic_etp_pin_mismatch_refused(tmp_path):
    fx = _synthetic_bundle()
    fx["p2"]["substrate_pins"]["etp_eod_sha256"] = {"TESTLEG": "pin"}
    fx["substrate"]["leg_ctx"]["TESTLEG"]["etp_pin_match"] = False
    with pytest.raises(Z2.ZRefused):
        _run_synthetic(fx, str(tmp_path))


def test_synthetic_tampered_arm_digest_refused(tmp_path):
    fx = _synthetic_bundle()
    fx["freeze"]["section2_arm_plan"]["arms"][0]["arm_config_digest"] = \
        "9" * 64
    with pytest.raises(Z2.ZRefused):
        _run_synthetic(fx, str(tmp_path))


# ----------------------------------------------------------------------- #
# 4. Evidence integrity (READ-ONLY pins; tamper detected fail-closed)
# ----------------------------------------------------------------------- #

def test_load_evidence_on_the_real_worktree_pins_match():
    ev = Z2.load_evidence(str(WORKTREE))
    assert ev["measured_sha256"]["z_report"] \
        == ev["pinned_sha256"]["z_report"]
    assert ev["measured_sha256"]["freeze"] \
        == ev["pinned_sha256"]["freeze"]
    assert len(ev["original_incident_coordinates"]) == 6
    assert sorted(map(tuple, ev["original_incident_coordinates"])) \
        == ORIGINAL_COORDINATES


def _evidence_scaffold(tmp_path: Path) -> Path:
    """A fake worktree with byte-identical copies of the pinned
    evidence artifacts (copying READ-ONLY evidence is reading)."""
    fake = tmp_path / "wt"
    for rel in (Z2.ORIGINAL_Z_REPORT_RELPATH, Z2.ADDENDUM_RELPATH,
                Z2.FREEZE_RELPATH, Z2.P2_RELPATH, Z2.CONTRACT_RELPATH,
                Z2.ORIGINAL_CELL_ARM1_RELPATH):
        src = WORKTREE / rel
        dst = fake / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return fake


def test_load_evidence_refuses_tampered_z_report(tmp_path):
    fake = _evidence_scaffold(tmp_path)
    victim = fake / Z2.ORIGINAL_Z_REPORT_RELPATH
    text = victim.read_text()
    victim.write_text(text.replace('"incident_count": 6',
                                   '"incident_count": 7'))
    with pytest.raises(Z2.ZRefused):
        Z2.load_evidence(str(fake))


def test_load_evidence_refuses_tampered_freeze(tmp_path):
    fake = _evidence_scaffold(tmp_path)
    victim = fake / Z2.FREEZE_RELPATH
    victim.write_bytes(victim.read_bytes() + b" ")
    with pytest.raises(Z2.ZRefused):
        Z2.load_evidence(str(fake))


def test_load_evidence_refuses_absent_evidence(tmp_path):
    with pytest.raises(Z2.ZRefused):
        Z2.load_evidence(str(tmp_path))


# ----------------------------------------------------------------------- #
# 5. Committed REAL-substrate artifacts (skipped when absent)
# ----------------------------------------------------------------------- #

requires_artifacts = pytest.mark.skipif(
    not REPORT_PATH.is_file() or len(CELL_PATHS) < 3,
    reason="committed zr2 artifacts absent (run zr2_run.py --run first)")


class TestCommittedArtifacts:

    @requires_artifacts
    def test_every_committed_artifact_is_sanitized(self):
        for p in [REPORT_PATH] + CELL_PATHS:
            obj = json.loads(p.read_text(encoding="utf-8"))
            Z2.sanitize_artifact(obj, p.name)       # driver's scanner
            assert_sanitized(obj, p.name)           # independent scanner
            assert_sanitized_raw_bytes(p)

    @requires_artifacts
    def test_report_schemas_verdict_and_provenance(self):
        r = json.loads(REPORT_PATH.read_text())
        assert r["schema"] == SCHEMA_REPORT
        assert r["cycle_id"] == "COMMODITIES-NG1"
        assert r["task_id"] == "commodities-ng1-zr2-repass"
        assert r["overall_verdict"] == "PASS"
        assert r["fail_closed"] is True
        assert r["blocked_prelaunch_candidate"] is False
        assert r["blocked_data_or_selection_candidate"] is False
        assert r["incident_count"] == 0 and r["incidents"] == []
        proven = r["provenance"]
        assert proven["head_sha"] == Z2.PACKET_BASE_SHA
        assert proven["head_sha"] == \
            "52a5e2ec5be5cef0f98145f79d8fbb2e4b9168cd"
        assert proven["branch"] == "orca/commodities-ng1-integration"
        assert proven["head_matches_packet_base"] is True

    @requires_artifacts
    def test_acceptance_six_incidents_cleared_as_declared_rows(self):
        r = json.loads(REPORT_PATH.read_text())
        cl = r["original_incident_clearance"]
        assert cl["coordinate_match"] is True
        assert cl["original_incident_count"] == 6
        assert cl["declared_count"] == 6
        assert cl["missing_declarations"] == []
        assert cl["new_declarations"] == []
        assert sorted(map(tuple, cl["declared_coordinates"])) \
            == ORIGINAL_COORDINATES
        assert sorted(map(tuple, cl["original_incident_coordinates"])) \
            == ORIGINAL_COORDINATES
        # every declared row carries the full declared disclosure shape
        rows = r["declared_not_executable_rows"]
        assert len(rows) == 6
        for d in rows:
            assert (d["arm_id"], d["pair"], d["role"]) \
                in ORIGINAL_COORDINATES
            assert d["outcome_class"] == "EMPTY_BOOKED_POPULATION"
            assert d["booked_trades"] == 0
            assert d["excluded_trades"] >= 1
            assert d["kernel_book_invoked"] is False
            assert d["root_reconciliation_invoked"] is False
            assert d["reason"] and d["disclosure"]

    @requires_artifacts
    def test_acceptance_remediation_basis_and_evidence_pins(self):
        r = json.loads(REPORT_PATH.read_text())
        rb = r["remediation_basis"]
        assert rb["evidence_digests_all_match"] is True
        assert rb["original_incident_count"] == 6
        assert rb["original_defect_class"] == "TypeError"
        assert rb["original_defect_stage"] == "booking"
        assert rb["original_localized_role"] == "RELEASE_CLOCK_SHADOW"
        assert rb["original_z_report_sha256_measured"] \
            == rb["original_z_report_sha256_pinned_by_addendum"]
        add = json.loads(ADDENDUM.read_text())
        assert rb["original_z_report_sha256_pinned_by_addendum"] \
            == add["citations"]["z_report"]["sha256"]
        assert rb["freeze_sha256_pinned_match"] is True
        assert rb["p2_gate_sha256_pinned_match"] is True
        assert rb["p1_cost_contract_sha256_pinned_match"] is True
        assert rb["addendum_sha256_measured"] \
            == hashlib.sha256(ADDENDUM.read_bytes()).hexdigest()

    @requires_artifacts
    def test_acceptance_previously_green_invariants_hold(self):
        r = json.loads(REPORT_PATH.read_text())
        g = r["grid"]
        assert g["bookable_pair_count"] == 11
        assert set(g["counted_instants_per_pair"].values()) == {401}
        assert g["pooled_counted_instants"] == 4411
        assert g["census_identity_all_verified"] is True
        assert g["rule_source_counts_pooled"] == {
            "p0_release_instant": 11 * 552,
            "week_anchor_holiday_shift": 11 * 6}
        assert g["unmapped_counted_release_dates_union"] == ["2026-09-11"]
        q = r["q11_eligibility"]
        assert q["pooled"] == {"eligible_instants": 4411, "minimum": 3300,
                               "verdict": "ELIGIBLE"}
        assert q["eligible_overall"] is True
        ca = r["config_assembly"]
        assert ca["booked_cells"] == 3 and ca["unbooked_cells"] == 3
        assert ca["trial_budget_cells"] == 6
        assert ca["all_digests_match"] is True
        assert ca["digests_pairwise_distinct"] is True
        # the 3 arm digests equal the Z-R1 addendum's UNCHANGED pins
        add = json.loads(ADDENDUM.read_text())
        pinned = add["affirmations"]["booked_arm_config_digests"]
        assert ca["arm_config_digests"] == pinned
        d = r["substrate_digest_chains"]
        assert d["plane_entries_all_digest_ok"] is True
        assert d["etp_legs_all_pin_ok"] is True
        assert len(d["plane_digest_rows"]) == 11       # deacot2016..2026
        assert len(d["etp_digest_rows"]) == 9          # bookable legs

    @requires_artifacts
    def test_acceptance_pass_row_parity_with_original_z_report(self):
        r = json.loads(REPORT_PATH.read_text())
        parity = r["pass_row_parity"]
        assert parity["all_match"] is True
        z = json.loads(ORIGINAL_Z_REPORT.read_text())   # READ-ONLY
        for arm_id, per in parity["per_cell"].items():
            z_totals = z["cells"][arm_id]["totals"]
            for key, v in per.items():
                assert v["match"] is True
                assert v["original"] == z_totals[key]
                assert v["zr2"] == z_totals[key]

    @requires_artifacts
    def test_acceptance_chain_digest_parity(self):
        r = json.loads(REPORT_PATH.read_text())
        cp = r["chain_structure_digest_parity"]
        assert cp["all_match"] is True
        assert all(v["match"] for v in cp["per_pair"].values())
        assert len(cp["per_pair"]) == 11

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
            assert m["cell_failures"] == []
            assert m["cell_pipeline_executable_verdict"] == "PASS"
            arm_ids.add(m["arm_id"])
            assert len(m["per_pair"]) == 11
            n_declared = 0
            for pid, prow in m["per_pair"].items():
                assert prow["census_identity_verified"] is True
                assert prow["counted_instants"] == 401
                for role, v in prow["roles"].items():
                    assert role in ALL_ROLES
                    if v["control_executable_verdict"] == "PASS":
                        assert v["fills"] == 2 * v["trades_booked"]
                        assert v["reconciliation_identity_ok"] is True
                        assert v["kernel_book_invoked"] is True
                        assert v["root_reconciliation_invoked"] is True
                        assert v["fold_partition_total_matches_trades"] \
                            is True
                        assert sum(
                            v["fold_partition_counts"].values()) \
                            == v["trades_booked"]
                        assert set(v["fold_partition_counts"]) \
                            == set(FOLD_IDS)
                        assert len(v["outcome_payload_sha256"]) == 64
                    else:
                        assert v["control_executable_verdict"] \
                            == NOT_EXECUTABLE
                        n_declared += 1
                        assert v["declared"] is True
                        assert v["trades_booked"] == 0 and v["fills"] == 0
                        assert v["excluded_trades"] >= 1
                        assert v["kernel_book_invoked"] is False
                        assert v["root_reconciliation_invoked"] is False
                        assert v["reconciliation_identity_ok"] is None
                        assert v["declared_reason"]
                        assert v["declared_disclosure"]
                        assert v["held_decision_count"] \
                            == prow["counted_instants"]
                        assert set(v["fold_partition_counts"]) \
                            == set(FOLD_IDS)
                        assert sum(v["fold_partition_counts"].values()) == 0
            assert n_declared == 2                  # WEAT + IAU per cell
            assert m["totals"]["declared_not_executable_row_count"] == 2
            assert \
                m["totals"]["excluded_trades_disclosed_on_declared_rows"] \
                == 2
            assert len(m["declared_not_executable_rows"]) == 2
            for role, v in m["pooled_roles"].items():
                assert v["control_executable_verdict"] == "PASS"
                assert v["fills"] == 2 * v["trades_booked"]
                assert v["reconciliation_identity_ok"] is True
        assert arm_ids == set(json.loads(
            REPORT_PATH.read_text())["freeze"]["booked_arm_ids"])

    @requires_artifacts
    def test_declared_rows_are_exactly_the_release_clock_coordinates(self):
        m = json.loads(
            (ZR2_OUT / "cell_COMMNG1-A4-P2-ARM1-NEUTRAL.json").read_text())
        for pid, role in (("001602/WEAT", "RELEASE_CLOCK_SHADOW"),
                          ("088691/IAU", "RELEASE_CLOCK_SHADOW")):
            v = m["per_pair"][pid]["roles"][role]
            assert v["control_executable_verdict"] == NOT_EXECUTABLE
            assert v["excluded_trades"] == 1
        # every other (pair, role) of the cell executed PASS
        n_pass = sum(
            1 for prow in m["per_pair"].values()
            for v in prow["roles"].values()
            if v["control_executable_verdict"] == "PASS")
        assert n_pass == 11 * len(ALL_ROLES) - 2

    @requires_artifacts
    def test_pass_rows_release_clock_shape_on_clean_legs(self):
        """Structural sanity of the re-pass on a boundary-free leg: the
        bare release clock holds every counted instant and books exactly
        one lifetime trade per pair (entry at the first counted release,
        terminal close at the last observable mark) -- IDENTICAL to the
        original Z committed shape."""
        m = json.loads(
            (ZR2_OUT / "cell_COMMNG1-A4-P2-ARM1-NEUTRAL.json").read_text())
        prow = m["per_pair"]["001602/DBA"]["roles"]["RELEASE_CLOCK_SHADOW"]
        assert prow["control_executable_verdict"] == "PASS"
        assert prow["held_decision_count"] == 401
        assert prow["flat_decision_count"] == 0
        assert prow["trades_booked"] == 1 and prow["fills"] == 2

    @requires_artifacts
    def test_manifest_digests_recorded_in_report_match_bytes(self):
        r = json.loads(REPORT_PATH.read_text())
        for arm_id, cell in r["cells"].items():
            path = ZR2_OUT / f"cell_{arm_id}.json"
            assert path.is_file()
            assert cell["manifest_sha256"] == \
                hashlib.sha256(path.read_bytes()).hexdigest()
            assert cell["cell_failure_count"] == 0
            assert cell["declared_not_executable_row_count"] == 2
            assert cell["cell_pipeline_executable_verdict"] == "PASS"
