"""A5 reproduction-harness tests (PLAN.md section 6.6, V7 contract).

Synthetic mini experiment dirs only -- no real runs, no network:

* identical source/rerun dirs -> every surface matches, ``all_match`` true;
* a single byte flip in the rerun funding cashflow artifact breaks its
  digest AND the cashflow-sum tolerance with an explicit reason;
* metric drift beyond the frozen tolerance breaks its surface (and
  sub-tolerance drift does NOT);
* the V6 family plan names exactly the four scored trials with
  ``VERIFY-V6FULL-<short>`` verify ids;
* frozen tolerance doc is deterministic and carries the contractual values;
* strict row-count / equity-digest surfaces fail closed on dropped rows;
* ``run_reproduction`` orchestrates the runner subprocess, locates the rerun
  artifacts, compares and writes ``reproduction_report.json`` (subprocess is
  faked; nothing external executes);
* the required signal family is derived from the source
  ``exact_backtest_argv`` and forwarded as ``PORTFOLIO_SIGNAL_FAMILY`` to the
  spawned runner (recorded as ``resolved_env_family``);
* ``rerun_manifest.yaml`` (verify-dir level) is accepted as the rerun-side
  launch-manifest alias;
* ``worker_returncode`` is the raw passthrough exit status of the spawned
  process -- no re-derivation from runner comparison fields.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import research.reproduction_harness as harness
from research.reproduction_harness import (
    FROZEN_TOLERANCES,
    EXIT_REPRO_MISMATCH,
    compare_trials,
    freeze_tolerances,
    run_reproduction,
    v6_family_plan,
    verify_id_for_trial,
)

GIT_COMMIT = "f" * 40
START_EQUITY = 100_000.0
TOTAL_PNL = 1_234.5
FOLD_PNLS = {"F1": 2_000.0, "F2": -765.5}


# --------------------------------------------------------------------------- #
# synthetic mini experiment dir builder
# --------------------------------------------------------------------------- #
def _ledger_rows(n: int = 4) -> list[dict]:
    return [
        {"ts": 1_700_000_000_000_000_000 + i * 86_400_000_000_000_000,
         "equity": START_EQUITY + TOTAL_PNL * i / (n - 1),
         "cash": START_EQUITY, "cash_identity_ok": True}
        for i in range(n)
    ]


def _build_exp_dir(root: Path) -> Path:
    """Deterministic full-mirror experiment dir (all compared surfaces)."""
    exp = Path(root)
    (exp / "frozen").mkdir(parents=True)

    config_text = "run:\n  initial_capital: 100000\n"
    candidate_text = "hypothesis_id: H-XSECT-FUND-CARRY-v1\nfamily: funding_carry\n"
    data_manifest = json.dumps({"schema_version": 1, "rows": 42}, sort_keys=True)
    universe_doc = json.dumps({"schema_version": 2, "symbols": ["AAAUSDT"]},
                              sort_keys=True)
    (exp / "frozen" / "config.yaml").write_text(config_text, encoding="utf-8")
    (exp / "frozen" / "candidate.yaml").write_text(candidate_text, encoding="utf-8")
    (exp / "frozen" / "data_manifest.json").write_text(data_manifest, encoding="utf-8")
    (exp / "frozen" / "universe.json").write_text(universe_doc, encoding="utf-8")

    orders = [{"ts": 1, "symbol": "AAAUSDT", "side": "BUY", "qty": 1.0}]
    positions = [{"ts": 2, "symbol": "AAAUSDT", "canonical_pnl": 10.0}]
    funding = [{"ts": 3, "symbol": "AAAUSDT", "cashflow": 0.25},
               {"ts": 4, "symbol": "BBBUSDT", "cashflow": -0.05}]
    terminal = [{"ts": 5, "symbol": "AAAUSDT", "is_terminal": True}]

    for name, rows in (("orders.jsonl", orders), ("positions.jsonl", positions),
                       ("portfolio_ledger.jsonl", _ledger_rows()),
                       ("funding_cashflows.jsonl", funding),
                       ("terminal_positions.jsonl", terminal)):
        (exp / name).write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
            encoding="utf-8")

    metrics = {
        "schema_version": 4,
        "experiment_id": "XSECT-FUND-CARRY-1D",
        "total_pnl": TOTAL_PNL,
        "starting_equity": START_EQUITY,
        "ending_equity": START_EQUITY + TOTAL_PNL,
        "pf_position_level": 1.234567890123,
        "max_drawdown_fraction": 0.0884,
        "beta": 0.0123456789,
        "turnover_total": 55.5,
        "fold_pnls": copy.deepcopy(FOLD_PNLS),
        "orders_digest": harness.hashlib.sha256(
            json.dumps({"rows": orders}, sort_keys=True).encode()).hexdigest(),
        "positions_digest": harness.hashlib.sha256(
            json.dumps({"rows": positions}, sort_keys=True).encode()).hexdigest(),
    }
    (exp / "canonical_metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")

    launch = {
        "schema_version": 2,
        "experiment_id": "XSECT-FUND-CARRY-1D",
        "git_commit_at_launch": GIT_COMMIT,
        "dirty_worktree_at_launch": False,
        "exact_backtest_argv": [
            sys.executable, "-m", "research.portfolio_runner",
            "--experiment-id", "XSECT-FUND-CARRY-1D",
            "--signal-family", "funding_carry",
        ],
        "runtime_config_sha256": harness.sha256_file(exp / "frozen/config.yaml"),
        "candidate_spec_sha256": harness.sha256_file(exp / "frozen/candidate.yaml"),
        "data_manifest_sha256": harness.sha256_file(exp / "frozen/data_manifest.json"),
        "universe_sha256": harness.sha256_file(exp / "frozen/universe.json"),
    }
    (exp / "launch_manifest.yaml").write_text(
        yaml.safe_dump(launch, sort_keys=False), encoding="utf-8")

    hashes = {}
    for path in sorted(exp.rglob("*")):
        if path.is_file() and path.name != "artifact_hashes.json":
            rel = path.relative_to(exp).as_posix()
            hashes[rel] = harness.sha256_file(path)
    (exp / "artifact_hashes.json").write_text(
        json.dumps({"schema_version": 4, "hashes": hashes}, indent=2,
                   sort_keys=True), encoding="utf-8")
    return exp


@pytest.fixture()
def twin_dirs(tmp_path: Path) -> tuple[Path, Path]:
    source = _build_exp_dir(tmp_path / "source")
    rerun = _build_exp_dir(tmp_path / "rerun")
    return source, rerun


def _read_metrics(exp: Path) -> dict:
    return json.loads((exp / "canonical_metrics.json").read_text(encoding="utf-8"))


def _rewrite_metrics(exp: Path, mutate) -> None:
    metrics = _read_metrics(exp)
    mutate(metrics)
    (exp / "canonical_metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")


# --------------------------------------------------------------------------- #
# 1. identical twins -> full match
# --------------------------------------------------------------------------- #
def test_identical_dirs_all_match(twin_dirs):
    source, rerun = twin_dirs
    report = compare_trials(source, rerun)
    assert report["all_match"] is True, json.dumps(report["surfaces"], indent=2)
    assert all(report["checks"].values())
    assert set(report["checks"]) == set(harness._ALL_SURFACE_NAMES)


# --------------------------------------------------------------------------- #
# 2. byte-flip in funding cashflows -> false + reason
# --------------------------------------------------------------------------- #
def test_funding_byte_flip_breaks_match_with_reason(twin_dirs):
    source, rerun = twin_dirs
    funding_path = rerun / "funding_cashflows.jsonl"
    lines = funding_path.read_text(encoding="utf-8").splitlines()
    flipped = json.loads(lines[0])
    flipped["cashflow"] = 1.25  # was 0.25 -> digest AND sum both break
    lines[0] = json.dumps(flipped, sort_keys=True)
    funding_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = compare_trials(source, rerun)
    assert report["checks"]["funding_digest_match"] is False
    assert report["surfaces"]["funding_digest_match"]["reason"] == (
        "digest_mismatch:funding_cashflows.jsonl")
    assert report["checks"]["funding_sum_match"] is False
    assert report["surfaces"]["funding_sum_match"]["reason"] == (
        "funding_cashflow_sum:beyond_tolerance")
    # the two manifests remain mutually equal (both record the pre-flip
    # digest); the flip is caught by the funding digest surface above
    assert report["checks"]["artifact_manifest_match"] is True
    assert report["all_match"] is False


# --------------------------------------------------------------------------- #
# 3. canonical metric drift beyond frozen tolerance
# --------------------------------------------------------------------------- #
def test_metric_drift_beyond_tolerance_fails(twin_dirs):
    source, rerun = twin_dirs

    def bump_beta(metrics):
        metrics["beta"] = metrics["beta"] + 0.01

    _rewrite_metrics(rerun, bump_beta)
    report = compare_trials(source, rerun)
    assert report["checks"]["beta_match"] is False
    assert report["surfaces"]["beta_match"]["reason"] == "beta:beyond_tolerance"
    assert report["all_match"] is False

    # pnl drift beyond the equity-scaled bound too
    source2, rerun2 = twin_dirs
    _rewrite_metrics(rerun2, lambda m: m.update(total_pnl=m["total_pnl"] + 1.0))
    report2 = compare_trials(source2, rerun2)
    assert report2["checks"]["pnl_match"] is False
    assert report2["surfaces"]["pnl_match"]["reason"] == (
        "total_pnl:beyond_tolerance")


def test_subtolerance_drift_still_matches_surface(twin_dirs):
    source, rerun = twin_dirs
    _rewrite_metrics(rerun, lambda m: m.update(beta=m["beta"] + 5e-7))
    report = compare_trials(source, rerun)
    assert report["checks"]["beta_match"] is True
    # only the (deliberately strict) byte/manifest surfaces may complain here
    assert report["checks"]["fold_pnls_exact_match"] is True
    assert report["checks"]["funding_sum_match"] is True


def test_nested_pf_payload_shape_is_supported(twin_dirs):
    """Real canonical_metrics.json stores PF as the merged position payload."""
    source, rerun = twin_dirs
    for exp in (source, rerun):
        _rewrite_metrics(exp, lambda m: m.update(
            pf_position_level={"profit_factor": m["pf_position_level"],
                               "trades": 1037, "gross_profit": 1.0,
                               "gross_loss": -1.0, "pf_reason": None}))
    report = compare_trials(source, rerun)
    assert report["checks"]["pf_match"] is True

    _rewrite_metrics(rerun, lambda m: m["pf_position_level"].update(
        profit_factor=m["pf_position_level"]["profit_factor"] + 0.01))
    report2 = compare_trials(source, rerun)
    assert report2["checks"]["pf_match"] is False
    assert report2["surfaces"]["pf_match"]["reason"] == "pf_position_level:beyond_tolerance"


def test_fold_pnls_map_must_be_exact(twin_dirs):
    source, rerun = twin_dirs
    _rewrite_metrics(rerun, lambda m: m.update(
        fold_pnls={**m["fold_pnls"], "F2": m["fold_pnls"]["F2"] + 1e-12}))
    report = compare_trials(source, rerun)
    assert report["checks"]["fold_pnls_exact_match"] is False
    assert report["surfaces"]["fold_pnls_exact_match"]["reason"] == (
        "fold_pnls:map_mismatch")
    assert report["all_match"] is False


# --------------------------------------------------------------------------- #
# 4. strict surfaces: row counts and equity digests
# --------------------------------------------------------------------------- #
def test_dropped_ledger_row_breaks_counts_and_equity_digest(twin_dirs):
    source, rerun = twin_dirs
    ledger = rerun / "portfolio_ledger.jsonl"
    lines = ledger.read_text(encoding="utf-8").splitlines()
    ledger.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    report = compare_trials(source, rerun)
    assert report["checks"]["row_counts_match"] is False
    assert "row_count_mismatch:portfolio_ledger.jsonl:" in (
        report["surfaces"]["row_counts_match"]["reason"])
    assert report["checks"]["equity_curve_shape_match"] is False
    assert report["checks"]["equity_curve_digest_match"] is False
    assert report["checks"]["ledger_file_digest_match"] is False
    assert report["all_match"] is False


# --------------------------------------------------------------------------- #
# 5. frozen tolerances contract
# --------------------------------------------------------------------------- #
def test_freeze_tolerances_deterministic_and_contractual(tmp_path):
    doc_a = freeze_tolerances()
    doc_b = freeze_tolerances()
    assert doc_a == doc_b
    assert doc_a["schema_version"] == harness.REPRODUCTION_SCHEMA_VERSION
    assert doc_a["generated_at_utc"]
    tol = doc_a["tolerances"]
    assert tol["pnl_abs_scale_tol"] == 1e-9
    assert tol["fee_abs_tol"] == 1e-6
    assert tol["slippage_abs_tol"] == 1e-6
    for key in ("pf_rel_tol", "mdd_rel_tol", "beta_rel_tol", "turnover_rel_tol",
                "funding_abs_tol"):
        assert tol[key] == 1e-6
    assert tol["row_count_strict"] is True
    assert tol["ledger_equity_digest_strict"] is True
    assert tol["artifact_manifest_strict"] is True
    assert FROZEN_TOLERANCES == tol
    # optional file write is idempotent and refuses divergence
    out = tmp_path / "reproduction_tolerances.json"
    assert freeze_tolerances(out)["artifact"] == "reproduction_tolerances"
    first = out.read_text(encoding="utf-8")
    assert freeze_tolerances(out) == doc_a
    assert out.read_text(encoding="utf-8") == first


def test_missing_directory_fails_closed(tmp_path):
    source = _build_exp_dir(tmp_path / "source")
    report = compare_trials(source, tmp_path / "does_not_exist")
    assert report["all_match"] is False
    assert report["error"] == "rerun_experiment_dir_missing"
    assert all(value is False for value in report["checks"].values())


# --------------------------------------------------------------------------- #
# 6. V6 family plan naming
# --------------------------------------------------------------------------- #
def test_v6_family_plan_names_four_trials():
    plan = v6_family_plan()
    assert [trial_id for trial_id, _ in plan] == [
        "XSECT-FUND-CARRY-1D",
        "XSECT-FUND-CARRY-3D",
        "XSECT-FUND-CARRY-7D",
        "XSECT-FUND-REVERSE-3D-CONTROL",
    ]
    assert [rel for _, rel in plan] == [
        "results/portfolio_v6/XSECT-FUND-CARRY-1D",
        "results/portfolio_v6/XSECT-FUND-CARRY-3D",
        "results/portfolio_v6/XSECT-FUND-CARRY-7D",
        "results/portfolio_v6/XSECT-FUND-REVERSE-3D-CONTROL",
    ]
    assert [verify_id_for_trial(trial_id) for trial_id, _ in plan] == [
        "VERIFY-V6FULL-1D",
        "VERIFY-V6FULL-3D",
        "VERIFY-V6FULL-7D",
        "VERIFY-V6FULL-REV3D",
    ]


# --------------------------------------------------------------------------- #
# 7. run_reproduction orchestration (subprocess faked; no real runs)
# --------------------------------------------------------------------------- #
class _FakeCompleted:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.stdout = "ok"
        self.stderr = ""


def _install_fake_runner(monkeypatch, source: Path, captured: dict,
                         returncode: int = 0, create_artifacts: bool = True) -> None:
    """Replace harness.subprocess.run; mirror source into rerun_artifacts."""

    def fake_run(command, cwd=None, env=None, capture_output=None,
                 text=None, timeout=None, check=False):
        captured["command"] = list(command)
        captured["cwd"] = cwd
        captured["env"] = dict(env or {})
        if create_artifacts:
            root = Path(command[command.index("--reproduction-root") + 1])
            verify_id = command[command.index("--verify-id") + 1]
            rerun_artifacts = root / verify_id / "rerun_artifacts"
            rerun_artifacts.mkdir(parents=True, exist_ok=True)
            for path in source.iterdir():
                target = rerun_artifacts / path.name
                if path.is_dir():
                    shutil.copytree(path, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(path, target)
        return _FakeCompleted(returncode)

    monkeypatch.setattr(harness.subprocess, "run", fake_run)


def test_run_reproduction_end_to_end_with_fake_runner(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    source = _build_exp_dir(repo / source_rel)

    captured: dict = {}
    _install_fake_runner(monkeypatch, source, captured)
    monkeypatch.delenv("PORTFOLIO_SIGNAL_FAMILY", raising=False)

    report = run_reproduction(
        repo, source_rel, "VERIFY-V6FULL-1D",
        extra_env={"ORCA_TEST_MARKER": "1"},
    )

    command = captured["command"]
    assert command[1:4] == ["-m", "research.portfolio_runner", "--reproduce"]
    assert Path(command[0]).exists()
    assert Path(command[4]).is_absolute() and Path(command[4]).is_dir()
    assert command[5:7] == ["--verify-id", "VERIFY-V6FULL-1D"]
    assert command[7] == "--reproduction-root"
    assert Path(command[8]).is_absolute()
    assert captured["cwd"] == str(repo)
    assert captured["env"]["ORCA_TEST_MARKER"] == "1"

    assert report["all_match"] is True, json.dumps(report.get("surfaces"), indent=2)
    assert report["returncode"] == 0
    assert report["worker_returncode"] == 0
    assert "worker_returncode_nonzero" not in report
    expected_report = (repo / "results/reproduction_v7/VERIFY-V6FULL-1D/"
                             "reproduction_report.json")
    assert expected_report.is_file()
    persisted = json.loads(expected_report.read_text(encoding="utf-8"))
    assert persisted["all_match"] is True
    assert report["report_path"] == str(expected_report)


def test_run_reproduction_forwards_derived_signal_family(tmp_path, monkeypatch):
    """Family derived from source exact_backtest_argv reaches the child env."""
    repo = tmp_path / "repo"
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    source = _build_exp_dir(repo / source_rel)
    monkeypatch.delenv("PORTFOLIO_SIGNAL_FAMILY", raising=False)

    # direct derivation from the frozen argv
    assert harness.expected_signal_family_from_source(source) == "funding_carry"

    captured: dict = {}
    _install_fake_runner(monkeypatch, source, captured)

    report = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")
    assert captured["env"]["PORTFOLIO_SIGNAL_FAMILY"] == "funding_carry"
    assert report["resolved_env_family"] == "funding_carry"

    # explicit pin overrides derivation (and lands in the child env)
    captured.clear()
    report = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D",
                              expected_signal_family="none",
                              extra_env={"ORCA_X": "1"})
    assert captured["env"]["PORTFOLIO_SIGNAL_FAMILY"] == "none"
    assert captured["env"]["ORCA_X"] == "1"
    assert report["resolved_env_family"] == "none"

    # extra_env merges LAST so a caller override still wins in the env
    captured.clear()
    report = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D",
                              extra_env={"PORTFOLIO_SIGNAL_FAMILY": "none"})
    assert captured["env"]["PORTFOLIO_SIGNAL_FAMILY"] == "none"
    assert report["resolved_env_family"] == "funding_carry"


def test_run_reproduction_without_family_flags_leaves_env_clean(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    source_rel = "results/portfolio_v6/XSECT-MOM-PLAIN-1D"
    source = _build_exp_dir(repo / source_rel)
    launch_path = source / "launch_manifest.yaml"
    launch_doc = yaml.safe_load(launch_path.read_text(encoding="utf-8"))
    launch_doc.pop("exact_backtest_argv")
    launch_path.write_text(yaml.safe_dump(launch_doc, sort_keys=False),
                           encoding="utf-8")

    assert harness.expected_signal_family_from_source(source) is None

    captured: dict = {}
    _install_fake_runner(monkeypatch, source, captured)
    monkeypatch.delenv("PORTFOLIO_SIGNAL_FAMILY", raising=False)

    report = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")
    assert "PORTFOLIO_SIGNAL_FAMILY" not in captured["env"]
    assert report["resolved_env_family"] is None


def test_worker_returncode_is_raw_passthrough_from_spawned_process(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    source = _build_exp_dir(repo / source_rel)
    monkeypatch.delenv("PORTFOLIO_SIGNAL_FAMILY", raising=False)

    captured: dict = {}
    _install_fake_runner(monkeypatch, source, captured, returncode=7)
    report = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")
    assert report["worker_returncode"] == 7
    assert report["returncode"] == 7
    assert "worker_returncode_nonzero" not in report

    # early-return path (no rerun artifacts) records the same raw code
    captured.clear()
    _install_fake_runner(monkeypatch, source, captured, returncode=7,
                         create_artifacts=False)
    report_missing = run_reproduction(repo, source_rel, "VERIFY-V6FULL-NONE")
    assert report_missing["error"] == "rerun_artifacts_not_found"
    assert report_missing["worker_returncode"] == 7
    assert "worker_returncode_nonzero" not in report_missing


def test_rerun_manifest_alias_resolves_code_config_data_hashes(twin_dirs):
    """Runner layout: rerun_manifest.yaml sits at <verify>/ level beside
    rerun_artifacts/ -- compare_trials must resolve it via the alias."""
    source, rerun = twin_dirs
    verify_dir = rerun.parent
    artifacts = verify_dir / "rerun_artifacts"
    rerun.rename(artifacts)
    (artifacts / "launch_manifest.yaml").rename(verify_dir / "rerun_manifest.yaml")

    report = compare_trials(source, artifacts)
    assert report["surfaces"]["code_hash_match"]["match"] is True
    assert report["checks"]["config_hashes_match"] is True
    assert report["checks"]["data_hashes_match"] is True
    assert report["all_match"] is True, json.dumps(report["surfaces"], indent=2)

    # with NO manifest at all the surface fails closed, honestly
    (verify_dir / "rerun_manifest.yaml").unlink()
    report_missing = compare_trials(source, artifacts)
    assert report_missing["checks"]["code_hash_match"] is False
    assert report_missing["surfaces"]["code_hash_match"]["reason"] == (
        "launch_manifest.yaml:missing")


def test_run_reproduction_reports_missing_rerun_fail_closed(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    _build_exp_dir(repo / source_rel)

    monkeypatch.setattr(
        harness.subprocess, "run",
        lambda *a, **k: _FakeCompleted())

    report = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")
    assert report["all_match"] is False
    assert report["error"] == "rerun_artifacts_not_found"
    assert all(value is False for value in report["checks"].values())
    persisted = (repo / "results/reproduction_v7/VERIFY-V6FULL-1D/"
                        "reproduction_report.json")
    assert persisted.is_file()


# --------------------------------------------------------------------------- #
# 8. CLI surface (compare exit codes; plan output)
# --------------------------------------------------------------------------- #
def test_cli_compare_exit_codes_and_plan(capsys, twin_dirs):
    source, rerun = twin_dirs
    assert harness.main(["compare", "--source", str(source), "--rerun",
                         str(rerun)]) == 0
    compare_out = capsys.readouterr()
    assert json.loads(compare_out.out)["all_match"] is True

    assert harness.main(["plan"]) == 0
    plan_out = capsys.readouterr().out.strip().splitlines()
    assert len(plan_out) == 4
    assert plan_out[0].split("\t") == [
        "XSECT-FUND-CARRY-1D",
        "results/portfolio_v6/XSECT-FUND-CARRY-1D",
        "VERIFY-V6FULL-1D",
    ]

    _rewrite_metrics(rerun, lambda m: m.update(beta=m["beta"] + 0.5))
    code = harness.main(["compare", "--source", str(source), "--rerun", str(rerun)])
    assert code == EXIT_REPRO_MISMATCH
