"""VOL-NG1 Z tests (task vol-ng1-z-dryrun).

Three families, all on the COMMITTED Z artifacts (no real-substrate
execution in tests):

1. SANITIZATION SCAN -- no outcome-worded / money-worded KEY and no
   per-trade or aggregate outcome payload exists anywhere in the
   committed z_report.json / z_cell_*.json (the SANITIZATION LAW:
   structural facts only; outcome-like internal plumbing values are
   committed solely as sha256 digest chains).
2. SCHEMA + FAIL-CLOSED CONSISTENCY -- artifact schemas, cell budget
   law, digest-chain formats, control battery completeness, and the
   fail-closed verdict law (overall PASS only on a clean preflight AND
   all cells PASS; a FAIL is recorded honestly, never repaired).
3. SYNTHETIC NEGATIVES -- contaminated reports are REFUSED by the
   scanner (at object level and at write time).

Run:
    python -m pytest tests/test_vol_ng1_z.py -q
"""

from __future__ import annotations

import json
import os
import re

import pytest

from research.control.vol_ng1_run.z import z_run

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."))
Z_DIR = os.path.join(REPO_ROOT, "research", "control", "vol_ng1_run", "z")
REPORT_PATH = os.path.join(Z_DIR, "z_report.json")

REPORT_SCHEMA = "vol_ng1_run/z_report@1"
CELL_SCHEMA = "vol_ng1_run/z_cell_manifest@1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

CONTROLS = ("index_only_shadow", "calendar_clock_shadow", "placebo",
            "invalid_null_distinction", "cost_path_control")


# --------------------------------------------------------------------------- #
# fixtures: the committed artifacts
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def report():
    assert os.path.isfile(REPORT_PATH), (
        f"committed z_report.json missing at {REPORT_PATH}")
    with open(REPORT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def manifests(report):
    out = {}
    for aid, cell in report["cells"].items():
        p = os.path.join(REPO_ROOT, cell["manifest_file"])
        assert os.path.isfile(p), f"committed cell manifest missing: {p}"
        with open(p, "r", encoding="utf-8") as fh:
            out[aid] = json.load(fh)
    return out


# --------------------------------------------------------------------------- #
# 1. sanitization scan of the committed artifacts
# --------------------------------------------------------------------------- #
def test_report_is_structural_only(report):
    z_run.scan_structural_only(report, "z_report")   # raises on any breach


def test_every_manifest_is_structural_only(manifests):
    assert len(manifests) == 6
    for aid, m in manifests.items():
        z_run.scan_structural_only(m, f"manifest {aid}")


def test_no_outcome_payload_in_committed_bytes(report, manifests):
    """The committed artifacts carry NO per-trade or aggregate outcome
    payload: ledger/books/series content appears ONLY behind digest
    fields (sha256 of internal values), never as data structures.
    Mechanically: no key begins with an entry_/exit_ trade prefix, and
    no list-of-dicts (the shape every per-trade payload would take)
    exists anywhere."""
    for label, art in [("z_report", report)] + list(manifests.items()):
        def walk(o, path_=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    kl = str(k).lower()
                    assert not kl.startswith(("entry_", "exit_")), \
                        f"{label}: trade-key {path_}/{k}"
                    walk(v, f"{path_}/{k}")
            elif isinstance(o, list):
                assert not any(isinstance(v, dict) for v in o), (
                    f"{label}: list-of-dicts payload at {path_} "
                    "(per-trade payload shape)")
                for i, v in enumerate(o):
                    walk(v, f"{path_}[{i}]")
        walk(art)


# --------------------------------------------------------------------------- #
# 2. schema + fail-closed consistency
# --------------------------------------------------------------------------- #
def test_report_schema_and_identity(report):
    assert report["schema"] == REPORT_SCHEMA
    assert report["cycle_id"] == "VOL-NG1"
    assert report["task_id"] == "vol-ng1-z-dryrun"
    assert report["mode"] == "REAL_SUBSTRATE_SANITIZED_DRYRUN"
    assert report["overall"] in ("PASS", "FAIL")
    assert report["git"]["branch"] == "orca/vol-ng1-integration"


def test_report_base_sha_provenance(report):
    st = report["base_sha_status"]
    assert st["base_sha"] == z_run.BASE_SHA
    assert st["ok"] is True
    assert st["relationship"] in ("HEAD == BASE",
                                  "BASE is an ancestor of HEAD")


def test_cell_budget_law(report, manifests):
    assert len(report["cells"]) == 6
    assert sorted(c["budget_cell"]
                  for c in report["cells"].values()) == list(range(1, 7))
    for aid, cell in report["cells"].items():
        m = manifests[aid]
        assert m["schema"] == CELL_SCHEMA
        assert m["arm_id"] == aid
        assert m["budget_cell"] == cell["budget_cell"]
        assert m["plumbing_verdict"] in ("PASS", "FAIL")


def test_digest_chain_formats(report, manifests):
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if (k.endswith("_digest") or k.endswith("_sha256")) \
                        and isinstance(v, str):
                    assert HEX64.match(v), f"bad digest format {k}={v!r}"
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(report)
    for m in manifests.values():
        walk(m)


def test_plumbing_verdict_law_per_cell(manifests):
    """PASS requires every sanitized structural check true; any False or
    a recorded exception forces FAIL (fail-closed, never repaired)."""
    for aid, m in manifests.items():
        checks = m.get("sanitized_checks", {})
        if m["plumbing_verdict"] == "PASS":
            assert checks and all(checks.values()), aid
            assert m["runtime"]["status"] == "COMPLETED", aid
            assert "exception" not in m, aid
        else:
            broken = (not checks) or (not all(checks.values())) \
                or ("exception" in m)
            assert broken, aid


def test_fail_closed_overall_law(report):
    cell_vs = [c["plumbing_verdict"] for c in report["cells"].values()]
    expect = "PASS" if (report["preflight"]["preflight_ok"]
                        and all(v == "PASS" for v in cell_vs)) else "FAIL"
    assert report["overall"] == expect
    assert (report["blocked_prelaunch_candidate"] is None) == \
        (report["overall"] == "PASS")


def test_preflight_representation_law(report):
    pf = report["preflight"]
    rep = pf["substrate"]["representation"]
    assert rep["grid_sessions_total"] == 2167
    assert rep["bookable_instants"] == 1914
    assert rep["first_bookable_instant"] == "2019-01-24"
    assert rep["last_bookable_instant"] == "2026-09-10"
    assert rep["v7_tail_refused_sessions"] == ["2026-09-11"]
    if pf["preflight_ok"]:
        assert all(rep["matches_freeze"].values())
        assert all(pf["preflight_detail"].values())
        assert pf["substrate"]["all_series_granted"] is True
        assert pf["substrate"]["corp_actions"][
            "residual_below_1e4_tol"] is True


def test_control_battery_complete_and_frozen(manifests):
    for aid, m in manifests.items():
        assert set(m["controls"]) == set(CONTROLS), aid
        cal = m["controls"]["calendar_clock_shadow"]
        assert cal["calendar_shift_k_sessions"] == 5
        pl = m["controls"]["placebo"]
        assert pl["placebo_seed"] == 20260912
        assert pl["rng_kind"] == "numpy.random.default_rng"
        cpc = m["controls"]["cost_path_control"]
        assert cpc["tier_ladder"] == [1.0, 1.5, 2.0]
        assert cpc["primary_tier"] == 2.0
        for c in CONTROLS:
            ctl = m["controls"][c]
            verdict = ctl.get("control_verdict", ctl.get("verdict"))
            assert verdict in ("PASS", "FAIL"), (aid, c)
        if m["plumbing_verdict"] == "PASS":
            for c in CONTROLS:
                ctl = m["controls"][c]
                assert ctl.get("control_verdict",
                               ctl.get("verdict")) == "PASS", (aid, c)


def test_structural_count_invariants(manifests):
    for aid, m in manifests.items():
        c = m["structural_counts"]
        assert (c["decisions"] + c["invalid_instants"]
                + c["refused_tail_decisions"]) == c["grid_sessions"], aid
        assert c["fills"] == 2 * c["round_trips"], aid
        assert c["kernel_events"] == c["round_trips"], aid
        assert sum(c["by_fold"].values()) == c["round_trips"], aid
        assert c["refused_tail_decisions"] == 1, aid
        dc = m["digest_chain"]
        for key in ("decision_series_digest", "fills_ledger_digest",
                    "round_trips_ledger_digest", "kernel_books_digest",
                    "mechanism_lines_digest", "cost_control_books_digest"):
            assert HEX64.match(dc[key]), (aid, key)


def test_controls_matrix_matches_manifests(report, manifests):
    for control in CONTROLS:
        col = report["controls_matrix"][control]
        assert set(col) == set(report["cells"])
        for aid in col:
            ctl = manifests[aid]["controls"][control]
            assert col[aid] == ctl.get("control_verdict",
                                       ctl.get("verdict"))


def test_runner_substrate_note_discloses_state_warmup(report):
    note = report["runner_substrate_note"]
    assert "bookable" in note and "invalid" in note.lower()


# --------------------------------------------------------------------------- #
# 3. synthetic negatives: contamination is REFUSED
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("contaminated", [
    {"cells": {"X": {"pnl": 123.45}}},
    {"totals": {"net_stress_usd_total": -51.2}},
    {"r1": {"expectancy_net_tier2": 0.013}},
    {"r4": {"profit_factor_net_tier2": 1.21}},
    {"per_trade": [{"entry_price": 19.5, "exit_price": 20.1}]},
    {"legs": {"VXX": {"notional_usd": 10000.0}}},
    {"fold": {"F1": {"win_rate": 0.58}}},
    {"a": [{"b": [{"sharpe": 1.9}]}]},
    {"books": [{"gross": 88.8}]},
    {"spread_frac_vxx": 0.021},
])
def test_scanner_refuses_contaminated_reports(contaminated):
    with pytest.raises(z_run.ZError):
        z_run.scan_structural_only(contaminated, "contaminated")


def test_scanner_accepts_clean_structural_artifact():
    clean = {
        "schema": CELL_SCHEMA,
        "structural_counts": {"decisions": 10, "fills": 8,
                              "round_trips": 4},
        "controls": {"placebo": {"placebo_seed": 20260912,
                                 "control_verdict": "PASS"}},
        "digest_chain": {"kernel_books_digest": "a" * 64},
        "law_text": "sanitized: no pnl / expectancy committed "
                    "(banned words live in VALUES, never KEYS)",
    }
    z_run.scan_structural_only(clean, "clean")       # must not raise


def test_write_refuses_contaminated_artifact(tmp_path):
    bad = {"cells": {"X": {"q16": {"execution_cost_usd_by_tier":
                                       {"2.0": 41.3}}}}}
    target = str(tmp_path / "bad.json")
    with pytest.raises(z_run.ZError):
        z_run.write_json_sanitized(target, bad, "contaminated write")
    assert not os.path.exists(target)   # scanned FIRST, written SECOND


def test_write_emits_clean_artifact(tmp_path):
    good = {"schema": "x@1", "counts": {"fills": 2}}
    target = str(tmp_path / "good.json")
    sha = z_run.write_json_sanitized(target, good, "clean write")
    assert os.path.exists(target)
    assert HEX64.match(sha)
    with open(target, "r", encoding="utf-8") as fh:
        assert json.load(fh) == good
