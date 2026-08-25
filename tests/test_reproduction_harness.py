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
  process -- no re-derivation from runner comparison fields;
* provenance surfaces are anchored to AUTHORITATIVE sources only: source
  ``git_commit_at_launch`` must be an ANCESTOR of the primary repo HEAD
  (real ``git merge-base --is-ancestor`` exercised against a synthetic repo;
  a descendant integration head passes, diverged history fails) plus
  SOURCE-side frozen-file hash self-consistency; the rerun side carries no
  provenance fields and none are expected from it;
* ``artifact_manifest_match`` replays every entry of the SOURCE
  ``artifact_hashes.json`` against the rerun artifacts -- a tampered entry
  fails naming that rel, a missing/unreadable rerun file fails closed, extra
  unlisted rerun files are ignored, SKIP_RERUN rels
  (``launch_manifest.yaml``/``run.log``, which A3's worker excludes from
  ``rerun_artifacts`` BY DESIGN) are skipped, and the rerun side needs NO
  ``artifact_hashes.json`` of its own (--reproduce emits none by design);
* ``rerun_emission_completeness`` re-states the replay's existence half as an
  explicit boolean: every SOURCE key minus SKIP_RERUN must exist on the
  rerun side; a tampered frozen/candidate.yaml byte-copy still fails naming
  that rel;
* pre-run hygiene: an existing verify dir whose report is ``all_match: true``
  short-circuits untouched, otherwise the whole directory is RENAMED aside
  to ``<verify_id>.FAILED-<UTCcompact>-n`` (bytes preserved, never deleted,
  collisions disambiguated) before a fresh run records ``renamed_from``.
"""

from __future__ import annotations

import copy
import json
import re
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


def _build_exp_dir(root: Path, git_commit: str = GIT_COMMIT) -> Path:
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
        "git_commit_at_launch": git_commit,
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
    # worker console log: SOURCE-manifest-listed but SKIP_RERUN-excluded from
    # the rerun side by A3's emission contract
    (exp / "run.log").write_text(
        "[launch] XSECT-FUND-CARRY-1D\n[worker] deterministic log\n",
        encoding="utf-8")

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


def _compare(source: Path, rerun: Path, **kwargs):
    """compare_trials with the fixture's launch commit as the vouched
    hermetic HEAD (seam emulates the ancestry rule by equality)."""
    kwargs.setdefault("git_head", GIT_COMMIT)
    return compare_trials(source, rerun, **kwargs)


def _init_git_repo(path: Path) -> str:
    """Real git repo with one empty commit at ``path``; returns HEAD sha."""
    def git(*args: str) -> str:
        proc = subprocess.run(["git", "-C", str(path), *args],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        return proc.stdout
    path.mkdir(parents=True, exist_ok=True)
    git("init", "-q")
    git("config", "user.email", "a5@example.invalid")
    git("config", "user.name", "A5 Test")
    git("commit", "--allow-empty", "-q", "-m", "launch")
    return git("rev-parse", "HEAD").strip()


def _tree_digest(root: Path) -> list[tuple[str, str]]:
    """Byte-identity snapshot: sorted (relpath, sha256) of every file."""
    return [(path.relative_to(root).as_posix(), harness.sha256_file(path))
            for path in sorted(root.rglob("*")) if path.is_file()]


# --------------------------------------------------------------------------- #
# 1. identical twins -> full match
# --------------------------------------------------------------------------- #
def test_identical_dirs_all_match(twin_dirs):
    source, rerun = twin_dirs
    report = _compare(source, rerun)
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

    report = _compare(source, rerun)
    assert report["checks"]["funding_digest_match"] is False
    assert report["surfaces"]["funding_digest_match"]["reason"] == (
        "digest_mismatch:funding_cashflows.jsonl")
    assert report["checks"]["funding_sum_match"] is False
    assert report["surfaces"]["funding_sum_match"]["reason"] == (
        "funding_cashflow_sum:beyond_tolerance")
    # the source manifest replay also catches the flip: the recorded funding
    # digest no longer matches the recomputed rerun bytes (names the rel)
    assert report["checks"]["artifact_manifest_match"] is False
    assert report["surfaces"]["artifact_manifest_match"]["reason"] == (
        "artifact_hash_mismatch:funding_cashflows.jsonl")
    assert report["all_match"] is False


# --------------------------------------------------------------------------- #
# 2b. artifact manifest: SOURCE replay semantics (round-3 contract)
# --------------------------------------------------------------------------- #
def test_artifact_manifest_tampered_entry_fails_naming_rel(twin_dirs):
    source, rerun = twin_dirs
    path = source / "artifact_hashes.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["hashes"]["orders.jsonl"] = "0" * 64  # one tampered entry
    path.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")

    report = _compare(source, rerun)
    assert report["checks"]["artifact_manifest_match"] is False
    assert report["surfaces"]["artifact_manifest_match"]["reason"] == (
        "artifact_hash_mismatch:orders.jsonl")
    assert report["surfaces"]["artifact_manifest_match"]["differing"] == [
        "orders.jsonl"]
    assert report["all_match"] is False


def test_artifact_manifest_missing_rerun_file_fails_closed(twin_dirs):
    source, rerun = twin_dirs
    (rerun / "positions.jsonl").unlink()

    report = _compare(source, rerun)
    assert report["checks"]["artifact_manifest_match"] is False
    assert report["surfaces"]["artifact_manifest_match"]["reason"] == (
        "missing_rerun_artifact:positions.jsonl")
    # the dedicated digest surface flags the same gap independently
    assert report["checks"]["positions_file_digest_match"] is False
    # ...and so does the explicit existence-only boolean (non-skipped rel)
    assert report["checks"]["rerun_emission_completeness"] is False
    assert report["surfaces"]["rerun_emission_completeness"]["reason"] == (
        "missing_rerun_artifact:positions.jsonl")


def test_artifact_manifest_skips_excluded_by_design_rels(twin_dirs):
    """A3 emission contract: rerun_artifacts exclude launch_manifest.yaml and
    run.log BY DESIGN; both are SOURCE-manifest-listed, yet the replay must
    honor SKIP_RERUN and still match fully."""
    source, rerun = twin_dirs
    hashes = json.loads(
        (source / "artifact_hashes.json").read_text(encoding="utf-8"))["hashes"]
    # fixture sanity: the SOURCE manifest carries skipped AND non-skipped keys
    assert set(harness.SKIP_RERUN).issubset(hashes)
    assert set(hashes) - set(harness.SKIP_RERUN)

    for rel in harness.SKIP_RERUN:
        (rerun / rel).unlink()  # A3's worker never emits these

    report = _compare(source, rerun)
    expected_entries = sum(1 for rel in hashes if rel not in harness.SKIP_RERUN)
    manifest_surface = report["surfaces"]["artifact_manifest_match"]
    assert report["checks"]["artifact_manifest_match"] is True, manifest_surface
    assert manifest_surface["skipped"] == ["launch_manifest.yaml", "run.log"]
    assert manifest_surface["entries"] == expected_entries

    emission = report["surfaces"]["rerun_emission_completeness"]
    assert report["checks"]["rerun_emission_completeness"] is True, emission
    assert emission["expected"] == expected_entries
    assert emission["missing"] == []
    assert emission["skipped"] == ["launch_manifest.yaml", "run.log"]
    assert report["all_match"] is True, json.dumps(report["surfaces"], indent=2)


def test_tampered_frozen_candidate_copy_fails_naming_rel(twin_dirs):
    """A byte-tampered frozen/ copy on the rerun side is caught by the
    SOURCE-manifest replay; SOURCE-side self-consistency stays green."""
    source, rerun = twin_dirs
    (rerun / "frozen" / "candidate.yaml").write_text(
        "hypothesis_id: H-TAMPERED\nfamily: funding_carry\n", encoding="utf-8")

    report = _compare(source, rerun)
    assert report["checks"]["artifact_manifest_match"] is False
    assert report["surfaces"]["artifact_manifest_match"]["reason"] == (
        "artifact_hash_mismatch:frozen/candidate.yaml")
    assert report["surfaces"]["artifact_manifest_match"]["differing"] == [
        "frozen/candidate.yaml"]
    # existence is fine -- only the digest diverges
    assert report["checks"]["rerun_emission_completeness"] is True
    # SOURCE-side frozen self-consistency is a separate surface: untouched
    assert report["checks"]["config_hashes_match"] is True
    assert report["all_match"] is False


def test_artifact_manifest_extra_rerun_files_are_ignored(twin_dirs):
    """--reproduce emits no artifact_hashes.json and adds worker-only files
    (core_result.json); neither may break the SOURCE-manifest replay."""
    source, rerun = twin_dirs
    (rerun / "artifact_hashes.json").unlink()  # rerun side carries none
    (rerun / "core_result.json").write_text('{"total_pnl": 1.0}\n',
                                            encoding="utf-8")
    (rerun / "comparison.json").write_text('{"all_match": true}\n',
                                           encoding="utf-8")

    report = _compare(source, rerun)
    assert report["checks"]["artifact_manifest_match"] is True, (
        report["surfaces"]["artifact_manifest_match"])
    assert report["all_match"] is True


def test_artifact_manifest_source_missing_or_empty_fails_closed(twin_dirs):
    source, rerun = twin_dirs
    (source / "artifact_hashes.json").unlink()
    report = _compare(source, rerun)
    assert report["checks"]["artifact_manifest_match"] is False
    assert report["surfaces"]["artifact_manifest_match"]["reason"] == (
        "source_artifact_hashes:missing_or_unreadable")

    source, rerun = twin_dirs
    (source / "artifact_hashes.json").write_text(
        json.dumps({"schema_version": 4, "hashes": {}}), encoding="utf-8")
    report_empty = _compare(source, rerun)
    assert report_empty["checks"]["artifact_manifest_match"] is False
    assert report_empty["surfaces"]["artifact_manifest_match"]["reason"] == (
        "source_artifact_hashes:missing_or_unreadable")


# --------------------------------------------------------------------------- #
# 3. canonical metric drift beyond frozen tolerance
# --------------------------------------------------------------------------- #
def test_metric_drift_beyond_tolerance_fails(twin_dirs):
    source, rerun = twin_dirs

    def bump_beta(metrics):
        metrics["beta"] = metrics["beta"] + 0.01

    _rewrite_metrics(rerun, bump_beta)
    report = _compare(source, rerun)
    assert report["checks"]["beta_match"] is False
    assert report["surfaces"]["beta_match"]["reason"] == "beta:beyond_tolerance"
    assert report["all_match"] is False

    # pnl drift beyond the equity-scaled bound too
    source2, rerun2 = twin_dirs
    _rewrite_metrics(rerun2, lambda m: m.update(total_pnl=m["total_pnl"] + 1.0))
    report2 = _compare(source2, rerun2)
    assert report2["checks"]["pnl_match"] is False
    assert report2["surfaces"]["pnl_match"]["reason"] == (
        "total_pnl:beyond_tolerance")


def test_subtolerance_drift_still_matches_surface(twin_dirs):
    source, rerun = twin_dirs
    _rewrite_metrics(rerun, lambda m: m.update(beta=m["beta"] + 5e-7))
    report = _compare(source, rerun)
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
    report = _compare(source, rerun)
    assert report["checks"]["pf_match"] is True

    _rewrite_metrics(rerun, lambda m: m["pf_position_level"].update(
        profit_factor=m["pf_position_level"]["profit_factor"] + 0.01))
    report2 = _compare(source, rerun)
    assert report2["checks"]["pf_match"] is False
    assert report2["surfaces"]["pf_match"]["reason"] == "pf_position_level:beyond_tolerance"


def test_fold_pnls_map_must_be_exact(twin_dirs):
    source, rerun = twin_dirs
    _rewrite_metrics(rerun, lambda m: m.update(
        fold_pnls={**m["fold_pnls"], "F2": m["fold_pnls"]["F2"] + 1e-12}))
    report = _compare(source, rerun)
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

    report = _compare(source, rerun)
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


_REAL_SUBPROCESS_RUN = subprocess.run


def _install_fake_runner(monkeypatch, source: Path, captured: dict,
                         returncode: int = 0, create_artifacts: bool = True) -> None:
    """Replace harness.subprocess.run for RUNNER invocations only; mirror
    source into rerun_artifacts.  The harness's own ``git rev-parse`` probe
    passes through to the real subprocess untouched."""

    def fake_run(command, cwd=None, env=None, capture_output=None,
                 text=None, timeout=None, check=False):
        if command and command[0] == "git":
            return _REAL_SUBPROCESS_RUN(command, capture_output=True,
                                        text=True, check=False)
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
    head = _init_git_repo(repo)
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    source = _build_exp_dir(repo / source_rel, git_commit=head)

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
    # code hash anchored via a REAL git rev-parse against the primary repo
    assert report["surfaces"]["code_hash_match"]["head"] == head
    assert report["returncode"] == 0
    assert report["worker_returncode"] == 0
    assert "worker_returncode_nonzero" not in report
    assert "renamed_from" not in report  # fresh verify dir: nothing archived
    expected_report = (repo / "results/reproduction_v7/VERIFY-V6FULL-1D/"
                             "reproduction_report.json")
    assert expected_report.is_file()
    persisted = json.loads(expected_report.read_text(encoding="utf-8"))
    assert persisted["all_match"] is True
    assert report["report_path"] == str(expected_report)


# --------------------------------------------------------------------------- #
# 7c. pre-run hygiene: already-verified skip + FAILED archive
# --------------------------------------------------------------------------- #
def test_run_reproduction_skips_untouched_when_already_verified(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    head = _init_git_repo(repo)
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    source = _build_exp_dir(repo / source_rel, git_commit=head)

    captured: dict = {}
    _install_fake_runner(monkeypatch, source, captured)
    first = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")
    assert first["all_match"] is True

    verify_dir = repo / "results/reproduction_v7/VERIFY-V6FULL-1D"
    snapshot = _tree_digest(verify_dir)
    captured.clear()
    second = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")

    assert "command" not in captured  # no subprocess spawned at all
    assert second["all_match"] is True
    assert _tree_digest(verify_dir) == snapshot  # evidence bytes untouched
    assert second["report_path"] == str(verify_dir / "reproduction_report.json")
    assert not any(path.name.startswith("VERIFY-V6FULL-1D.FAILED-")
                   for path in verify_dir.parent.iterdir())


def test_run_reproduction_archives_false_report_then_runs_fresh(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    head = _init_git_repo(repo)
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    source = _build_exp_dir(repo / source_rel, git_commit=head)

    # attempt 1: broken worker leaves a false-report verify dir behind
    captured: dict = {}
    _install_fake_runner(monkeypatch, source, captured, returncode=7,
                         create_artifacts=False)
    broken = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")
    assert broken["all_match"] is False
    verify_dir = repo / "results/reproduction_v7/VERIFY-V6FULL-1D"
    assert verify_dir.is_dir()
    broken_snapshot = _tree_digest(verify_dir)

    # attempt 2: healthy worker -> stale dir archived BYTES-PRESERVED,
    # fresh run proceeds, new report records the rename
    captured.clear()
    _install_fake_runner(monkeypatch, source, captured)
    good = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")

    assert good["all_match"] is True, json.dumps(good.get("surfaces"), indent=2)
    archive = Path(good["archived_to"])
    assert re.fullmatch(r"VERIFY-V6FULL-1D\.FAILED-\d{8}T\d{6}-\d+",
                        archive.name)
    assert archive.is_dir() and archive != verify_dir
    assert _tree_digest(archive) == broken_snapshot  # preserved, never deleted
    assert good["renamed_from"] == str(verify_dir)
    persisted = json.loads((verify_dir / "reproduction_report.json")
                           .read_text(encoding="utf-8"))
    assert persisted["renamed_from"] == str(verify_dir)
    assert persisted["archived_to"] == str(archive)


def test_run_reproduction_archives_unreadable_prior_report(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    head = _init_git_repo(repo)
    source_rel = "results/portfolio_v6/XSECT-FUND-CARRY-1D"
    source = _build_exp_dir(repo / source_rel, git_commit=head)

    verify_dir = repo / "results/reproduction_v7/VERIFY-V6FULL-1D"
    verify_dir.mkdir(parents=True)
    (verify_dir / "reproduction_report.json").write_text(
        "{not valid json", encoding="utf-8")
    snapshot = _tree_digest(verify_dir)

    captured: dict = {}
    _install_fake_runner(monkeypatch, source, captured)
    report = run_reproduction(repo, source_rel, "VERIFY-V6FULL-1D")

    assert report["all_match"] is True
    archive = Path(report["archived_to"])
    assert archive != verify_dir
    assert _tree_digest(archive) == snapshot
    assert (archive / "reproduction_report.json").read_text(
        encoding="utf-8") == "{not valid json"


def test_archive_preserves_bytes_and_disambiguates_collisions(tmp_path):
    stale = tmp_path / "VERIFY-V6FULL-1D"
    stale.mkdir()
    (stale / "reproduction_report.json").write_text('{"all_match": false}\n',
                                                    encoding="utf-8")
    snapshot = _tree_digest(stale)

    renamed_from_a, archived_a = harness._archive_failed_verify_dir(stale)
    assert renamed_from_a == str(stale)
    arch_a = Path(archived_a)
    assert re.fullmatch(r"VERIFY-V6FULL-1D\.FAILED-\d{8}T\d{6}-\d+", arch_a.name)
    assert not stale.exists()
    assert _tree_digest(arch_a) == snapshot  # bytes preserved by rename

    # same-second collision: -n counter disambiguates, never overwrites
    stale.mkdir()
    _renamed_from_b, archived_b = harness._archive_failed_verify_dir(stale)
    arch_b = Path(archived_b)
    assert arch_b != arch_a and arch_b.is_dir()
    assert list(arch_b.iterdir()) == []  # fresh-empty dir archived as-is
    assert sorted(tmp_path.glob("VERIFY-V6FULL-1D.FAILED-*")) == [arch_a, arch_b]


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


def test_rerun_manifest_alias_loader_still_resolves(twin_dirs):
    """Round-1 fix intact: verify-dir-level rerun_manifest.yaml resolves via
    _load_launch_manifest -- while provenance surfaces no longer consult the
    rerun side AT ALL (they never carried those fields)."""
    source, rerun = twin_dirs
    verify_dir = rerun.parent
    artifacts = verify_dir / "rerun_artifacts"
    rerun.rename(artifacts)
    (artifacts / "launch_manifest.yaml").rename(verify_dir / "rerun_manifest.yaml")

    manifest, reason = harness._load_launch_manifest(artifacts)
    assert reason is None
    assert manifest["git_commit_at_launch"] == GIT_COMMIT
    assert harness.expected_signal_family_from_source(artifacts) == "funding_carry"

    # replay contract: every SOURCE-listed rel must exist on the rerun side,
    # so the manifest file is restored before comparing (the verify-dir-level
    # alias resolution was already proven above at loader level).
    shutil.copy(verify_dir / "rerun_manifest.yaml",
                artifacts / "launch_manifest.yaml")
    report = _compare(source, artifacts)
    assert report["all_match"] is True, json.dumps(report["surfaces"], indent=2)

    # ...and provenance still passes with the alias file deleted outright
    (verify_dir / "rerun_manifest.yaml").unlink()
    report_no_alias = _compare(source, artifacts)
    assert report_no_alias["all_match"] is True


# --------------------------------------------------------------------------- #
# 7b. provenance surfaces anchored to authoritative sources only
# --------------------------------------------------------------------------- #
def test_provenance_ignores_rerun_side_provenance_fields(twin_dirs):
    """The rerun side carries NO git_commit/frozen-hash fields and none are
    expected: strip them entirely and provenance still passes.  The removed
    launch_manifest.yaml is SKIP_RERUN-excluded from the SOURCE-manifest
    replay (round-4 contract), so both manifest surfaces stay green."""
    source, rerun = twin_dirs
    (rerun / "launch_manifest.yaml").unlink()
    (rerun.parent / "rerun_manifest.yaml").write_text(
        yaml.safe_dump({"schema_version": 4, "verify_id": "VERIFY-X",
                        "verification_type": "INDEPENDENT_RERUN",
                        "tolerances": {"pnl_abs_scale_tol": 1e-6}}),
        encoding="utf-8")

    report = _compare(source, rerun)
    for surface in ("code_hash_match", "config_hashes_match",
                    "data_hashes_match"):
        assert report["checks"][surface] is True, report["surfaces"][surface]
    # the removed file is SKIP_RERUN-excluded from the replay BY DESIGN:
    # manifest replay + emission completeness stay green, all_match holds
    assert report["checks"]["artifact_manifest_match"] is True
    assert report["surfaces"]["artifact_manifest_match"]["skipped"] == [
        "launch_manifest.yaml", "run.log"]
    assert report["checks"]["rerun_emission_completeness"] is True
    assert report["all_match"] is True


def test_provenance_is_source_frozen_file_self_consistency(twin_dirs):
    """Recomputed sha256 of SOURCE frozen/* must equal its own manifest."""
    source, rerun = twin_dirs
    (source / "frozen" / "config.yaml").write_text("run:\n  tampered: true\n",
                                                   encoding="utf-8")
    (source / "frozen" / "universe.json").write_text('{"schema_version": 9}\n',
                                                     encoding="utf-8")
    report = _compare(source, rerun)
    assert report["checks"]["config_hashes_match"] is False
    assert "runtime_config_sha256:self_hash_mismatch" in (
        report["surfaces"]["config_hashes_match"]["reason"])
    assert report["checks"]["data_hashes_match"] is False
    assert "universe_sha256:self_hash_mismatch" in (
        report["surfaces"]["data_hashes_match"]["reason"])
    # untouched fields stay green; code hash is a separate surface
    assert "candidate_spec_sha256" not in (
        report["surfaces"]["config_hashes_match"]["reason"])
    assert report["checks"]["code_hash_match"] is True


def test_provenance_manifest_field_drift_and_missing_fail_closed(twin_dirs):
    source, rerun = twin_dirs
    launch_path = source / "launch_manifest.yaml"
    doc = yaml.safe_load(launch_path.read_text(encoding="utf-8"))
    doc["candidate_spec_sha256"] = "0" * 64  # recorded != recomputed
    del doc["data_manifest_sha256"]          # field absent from manifest
    launch_path.write_text(yaml.safe_dump(doc, sort_keys=False),
                           encoding="utf-8")

    report = _compare(source, rerun)
    assert report["surfaces"]["config_hashes_match"]["reason"] == (
        "candidate_spec_sha256:self_hash_mismatch")
    assert report["surfaces"]["data_hashes_match"]["reason"] == (
        "data_manifest_sha256:missing_in_source_manifest")


def test_code_hash_requires_launch_commit_ancestor_of_head(tmp_path):
    source, rerun = _build_exp_dir(tmp_path / "s1"), _build_exp_dir(tmp_path / "r1")
    report = compare_trials(source, rerun, git_head="a" * 40)
    assert report["checks"]["code_hash_match"] is False
    assert report["surfaces"]["code_hash_match"]["reason"] == (
        "git_commit_at_launch:not_ancestor_of_head")

    source, rerun = _build_exp_dir(tmp_path / "s2"), _build_exp_dir(tmp_path / "r2")
    launch_path = source / "launch_manifest.yaml"
    doc = yaml.safe_load(launch_path.read_text(encoding="utf-8"))
    doc.pop("git_commit_at_launch")
    launch_path.write_text(yaml.safe_dump(doc, sort_keys=False),
                           encoding="utf-8")
    report_missing = compare_trials(source, rerun, git_head=GIT_COMMIT)
    assert report_missing["surfaces"]["code_hash_match"]["reason"] == (
        "git_commit_at_launch:missing_field")

    # unresolvable HEAD (dir outside any repo) fails closed as well
    source, rerun = _build_exp_dir(tmp_path / "s3"), _build_exp_dir(tmp_path / "r3")
    report_unresolved = compare_trials(source, rerun,
                                       primary_repo=tmp_path / "nowhere")
    assert report_unresolved["checks"]["code_hash_match"] is False
    assert report_unresolved["surfaces"]["code_hash_match"]["reason"].startswith(
        "git_head_unresolved:")


def test_code_hash_resolves_real_head_via_git_rev_parse(tmp_path):
    head = _init_git_repo(tmp_path / "repo")
    source = _build_exp_dir(
        tmp_path / "repo/results/portfolio_v6/XSECT-FUND-CARRY-1D",
        git_commit=head)
    rerun = _build_exp_dir(tmp_path / "rerun", git_commit=head)

    report = compare_trials(source, rerun, primary_repo=tmp_path / "repo")
    assert report["checks"]["code_hash_match"] is True
    assert report["surfaces"]["code_hash_match"]["head"] == head
    assert report["surfaces"]["code_hash_match"]["source"] == head


def test_code_hash_accepts_descendant_head_and_rejects_diverged(tmp_path):
    """Round-3 ancestor rule: the rerun worker runs at integration HEAD,
    which legitimately ADVANCES past the historical launch commit -- the
    surface must PASS while the launch commit remains an ancestor and FAIL
    closed once history diverges from it."""
    repo = tmp_path / "repo"
    head = _init_git_repo(repo)
    source = _build_exp_dir(
        repo / "results/portfolio_v6/XSECT-FUND-CARRY-1D", git_commit=head)
    rerun = _build_exp_dir(tmp_path / "rerun", git_commit=head)

    def git(*args: str) -> str:
        proc = subprocess.run(["git", "-C", str(repo), *args],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        return proc.stdout

    # descendant integration commit: launch commit is an ANCESTOR -> pass
    git("commit", "--allow-empty", "-q", "-m", "integration moves on")
    moved = git("rev-parse", "HEAD").strip()
    assert moved != head
    report_moved = compare_trials(source, rerun, primary_repo=repo)
    assert report_moved["checks"]["code_hash_match"] is True, (
        report_moved["surfaces"]["code_hash_match"])
    assert report_moved["surfaces"]["code_hash_match"]["source"] == head
    assert report_moved["surfaces"]["code_hash_match"]["head"] == moved

    # diverged history: an ORPHAN line shares no ancestry with the launch
    # commit -> fail closed
    git("checkout", "-q", "--orphan", "diverged-line")
    git("commit", "--allow-empty", "-q", "-m", "unrelated history")
    diverged = git("rev-parse", "HEAD").strip()
    assert diverged not in (head, moved)
    report_diverged = compare_trials(source, rerun, primary_repo=repo)
    assert report_diverged["checks"]["code_hash_match"] is False
    assert report_diverged["surfaces"]["code_hash_match"]["reason"] == (
        "git_commit_at_launch:not_ancestor_of_head")


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
def test_cli_compare_exit_codes_and_plan(capsys, tmp_path):
    head = _init_git_repo(tmp_path / "repo")
    source = _build_exp_dir(tmp_path / "source", git_commit=head)
    rerun = _build_exp_dir(tmp_path / "rerun", git_commit=head)
    compare_argv = ["compare", "--source", str(source), "--rerun", str(rerun),
                    "--primary-repo", str(tmp_path / "repo")]

    assert harness.main(compare_argv) == 0
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
    code = harness.main(compare_argv)
    assert code == EXIT_REPRO_MISMATCH
