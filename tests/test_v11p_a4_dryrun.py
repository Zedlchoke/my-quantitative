"""V11 P1 lane A4 tests -- exact-arm dry-run and platform-safe QA.

Coverage required by the frozen lane brief (PLAN section 7, A4):

* the dry-run happy path traverses load -> identity distinctness -> signal
  shape -> schedule -> fills -> costs/funding shape -> dummy finite metrics
  -> temporary-ledger publication, all through the REAL adapter path on
  SYNTHETIC data, with zero scored metrics and zero real-PnL exposure;
* the three arm identities (anchor, neighbour, causal control) are pairwise
  distinct and replay-stable BEFORE any freeze, through an injectable
  ``identity_provider`` whose default is the adapter's CURRENT trial-key
  function (no new identity scheme is implemented in this lane);
* explicit fail-closed detection: missing tick sizes, missing benchmark
  declaration, missing terminal valuation bar, missing funding bundle,
  stale manifest, non-finite payload -- any blocking finding refuses
  publication of the affected arm;
* temporary-ledger semantics: first publish +1, one replay per arm +0,
  colliding content under the same key refused with ledger bytes unchanged;
* the real global registry path (and any results/registry tree) is refused
  fail-closed for dry-run publication;
* tests write ONLY to ``tmp_path``: no tracked golden report, no results
  artifact, no ledger under the repo is ever touched, and running this
  suite leaves ``git status --porcelain`` unchanged.

No catalog parquet is read, no network is used, no scored window is opened.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import pytest

from research.adapter_v10.dummy_strategy import DummyDeterministicStrategy
from research.adapter_v10.hashes import payload_sha256
from research.adapter_v10.publish import (
    canonical_scored_payload,
    trial_key,
)
from research.adapter_v10.protocol import ContractViolation, CostModel
from research.global_ledger import DEFAULT_REGISTRY_PATH, snapshot
from research.v11.exact_arm_dryrun import (
    ANCHOR,
    ARM_NAMES,
    BLOCKING_FINDING_CODES,
    CAUSAL_CONTROL,
    DRYRUN_BENCHMARK,
    DRYRUN_DRIFTS,
    DRYRUN_DUMMY_METRICS_KIND,
    DRYRUN_INSTANTS_NS,
    DRYRUN_MATRIX_ID,
    DRYRUN_RATES,
    DRYRUN_SYMBOLS,
    DRYRUN_WINDOW_END_ISO,
    DRYRUN_WINDOW_START_ISO,
    FINDING_MISSING_BENCHMARK_DECLARATION,
    FINDING_MISSING_FUNDING_BUNDLE,
    FINDING_MISSING_TERMINAL_VALUATION_BAR,
    FINDING_MISSING_TICK_SIZE,
    FINDING_NON_FINITE_PAYLOAD,
    FINDING_STALE_MANIFEST,
    NEIGHBOUR,
    STAGE_NAMES,
    build_dummy_metrics,
    build_dry_run_arms,
    build_preflight_bundle,
    default_identity_provider,
    detect_fail_closed_findings,
    exercise_temporary_ledger_semantics,
    publish_arm_to_temporary_ledger,
    prove_arm_identity_distinctness,
    require_temporary_ledger,
    run_exact_arm_dryrun,
    scan_non_finite,
)

REPO = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def make_ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "dryrun_ledger.jsonl"


def good_bundle():
    """A fully-declared bundle assembled from the real adapter path."""
    arms = build_dry_run_arms()
    from research.adapter_v10.runner import run_strategy

    result = run_strategy(arms[ANCHOR], write_artifact_file=False)
    return build_preflight_bundle(arms[ANCHOR], runner_result=result)


def codes(findings) -> set:
    return {finding["code"] for finding in findings}


# --------------------------------------------------------------------------- #
# 1) Happy path: full traversal, no scored metric, everything finite
# --------------------------------------------------------------------------- #
def test_dry_run_happy_path_all_stages_pass_with_no_scored_metric(tmp_path):
    ledger = make_ledger_path(tmp_path)
    result = run_exact_arm_dryrun(ledger_path=ledger)

    assert result["ok"] is True
    assert result["scored"] is False and result["real_pnl"] is False
    assert result["findings"] == []
    assert result["stage_checklist"] == {name: True for name in STAGE_NAMES}
    assert list(result["arms"]) == sorted(ARM_NAMES)
    for arm, info in result["arms"].items():
        assert info["publish_stage"] == "PUBLISHED"
        assert info["publish_delta"] == 1
        assert info["replay_stage"] == "IDEMPOTENT_REPLAY_SKIPPED"
        assert info["replay_delta"] == 0
        dummy = build_dummy_metrics(arm)
        assert dummy["kind"] == DRYRUN_DUMMY_METRICS_KIND
        assert dummy["dry_run"] is True and dummy["scored"] is False

    # the temporary ledger holds EXACTLY one dry-run-namespaced row per arm
    state = snapshot(ledger)
    assert state["count"] == len(ARM_NAMES)
    for row in state["rows"]:
        assert row["kind"] == "CELL_RESULT"
        assert row["matrix_id"] == DRYRUN_MATRIX_ID
        assert row["experiment_id"].startswith(DRYRUN_MATRIX_ID)

    # the whole result is finite JSON (nothing non-serialisable leaks)
    payload = json.loads(json.dumps(result))
    assert scan_non_finite(payload) == []


def test_dry_run_is_deterministic_across_runs(tmp_path):
    first = run_exact_arm_dryrun(ledger_path=make_ledger_path(tmp_path / "a"))
    (tmp_path / "b").mkdir()
    second = run_exact_arm_dryrun(ledger_path=make_ledger_path(tmp_path / "b"))
    assert first["ok"] and second["ok"]
    assert (
        first["identity_distinctness"]["keys_sha256"]
        == second["identity_distinctness"]["keys_sha256"]
    )
    assert first["arms"] == second["arms"]


# --------------------------------------------------------------------------- #
# 2) Identity distinctness before freeze (injectable provider)
# --------------------------------------------------------------------------- #
def test_three_arm_identities_distinct_and_replay_stable_before_freeze():
    arms = build_dry_run_arms()
    signatures = {name: arms[name].baseline_stress().signature() for name in arms}
    proof = prove_arm_identity_distinctness(arms, stress_signatures=signatures)

    assert proof["distinct"] is True
    assert proof["pairwise_collisions"] == []
    keys = proof["keys_sha256"]
    assert len(set(keys.values())) == len(ARM_NAMES) == 3
    assert all(proof["replay_stable"].values())
    # anchor vs causal control differ ONLY in declared arm identity fields,
    # so the key distinctness is carried by the identity itself
    assert proof["control_vs_anchor_differing_identity_fields"] == [
        "arm_config_id",
        "strategy_id",
    ]


def test_identity_provider_is_injectable_and_distinctness_still_enforced():
    arms = build_dry_run_arms()
    signatures = {name: arms[name].baseline_stress().signature() for name in arms}

    def prefixed_provider(payload):
        return "PREFIX::" + default_identity_provider(payload)

    proof = prove_arm_identity_distinctness(
        arms, stress_signatures=signatures, identity_provider=prefixed_provider
    )
    assert proof["distinct"] is True
    assert all(key.startswith("PREFIX::") for key in proof["keys_sha256"].values())
    assert proof["provider"] == "prefixed_provider"


def test_colliding_identity_provider_fails_closed_before_freeze():
    arms = build_dry_run_arms()
    signatures = {name: arms[name].baseline_stress().signature() for name in arms}

    with pytest.raises(ContractViolation, match="arm identity collision"):
        prove_arm_identity_distinctness(
            arms, stress_signatures=signatures, identity_provider=lambda payload: "same"
        )
    with pytest.raises(ContractViolation, match="identity_provider must be callable"):
        prove_arm_identity_distinctness(
            arms, stress_signatures=signatures, identity_provider="not-callable"
        )


def test_default_identity_provider_is_the_adapter_trial_key_function():
    arms = build_dry_run_arms()
    signature = arms[ANCHOR].baseline_stress().signature()
    payload = {
        "identity": arms[ANCHOR].identity().public_payload(),
        "stress_signature": dict(signature),
    }
    expected = trial_key(
        canonical_scored_payload(
            identity=arms[ANCHOR].identity(), stress_signature=dict(signature)
        )
    )
    assert default_identity_provider(payload) == expected
    # the neighbour arm (different declared arm + config) keys differently
    neighbour_payload = {
        "identity": arms[NEIGHBOUR].identity().public_payload(),
        "stress_signature": dict(arms[NEIGHBOUR].baseline_stress().signature()),
    }
    assert default_identity_provider(neighbour_payload) != default_identity_provider(payload)


# --------------------------------------------------------------------------- #
# 3) Fail-closed detection over explicit bundles
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "mutate,expected_code",
    [
        # missing tick size
        (
            lambda bundle: bundle["tick_sizes"].pop(sorted(bundle["tick_sizes"])[0]),
            FINDING_MISSING_TICK_SIZE,
        ),
        (
            lambda bundle: bundle["tick_sizes"].__setitem__(
                sorted(bundle["tick_sizes"])[0], 0.0
            ),
            FINDING_MISSING_TICK_SIZE,
        ),
        # missing benchmark declaration
        (
            lambda bundle: bundle.__setitem__("benchmark_declaration", {}),
            FINDING_MISSING_BENCHMARK_DECLARATION,
        ),
        (
            lambda bundle: bundle.pop("benchmark_declaration"),
            FINDING_MISSING_BENCHMARK_DECLARATION,
        ),
        # missing terminal valuation bar
        (
            lambda bundle: bundle["terminal_valuation"]["marks"].__setitem__(
                sorted(bundle["terminal_valuation"]["marks"])[0], None
            ),
            FINDING_MISSING_TERMINAL_VALUATION_BAR,
        ),
        (
            lambda bundle: bundle.pop("terminal_valuation"),
            FINDING_MISSING_TERMINAL_VALUATION_BAR,
        ),
        # missing funding bundle
        (
            lambda bundle: bundle["funding_bundle"]["settlements"].pop(
                sorted(bundle["funding_bundle"]["settlements"])[0]
            ),
            FINDING_MISSING_FUNDING_BUNDLE,
        ),
        (
            lambda bundle: bundle.pop("funding_bundle"),
            FINDING_MISSING_FUNDING_BUNDLE,
        ),
        # stale manifest
        (
            lambda bundle: bundle["manifest"].__setitem__(
                "payload_sha256", "0" * 64
            ),
            FINDING_STALE_MANIFEST,
        ),
        (
            lambda bundle: bundle["manifest"].pop("payload_sha256"),
            FINDING_STALE_MANIFEST,
        ),
        (
            lambda bundle: bundle.pop("manifest"),
            FINDING_STALE_MANIFEST,
        ),
    ],
)
def test_detection_fails_closed_on_each_declared_hole(mutate, expected_code):
    bundle = good_bundle()
    mutate(bundle)
    findings = detect_fail_closed_findings(bundle)
    assert expected_code in codes(findings)
    assert codes(findings) <= BLOCKING_FINDING_CODES
    assert all(finding["blocking"] is True for finding in findings)


def test_detection_flags_non_finite_payload():
    bundle = good_bundle()
    first_row = bundle["payload"]["daily_returns"][0]
    first_row["net_return_per_unit"] = float("nan")
    # a payload containing NaN cannot even be canonically hashed, so the
    # detector must flag non-finiteness WITHOUT attempting a digest compare
    findings = detect_fail_closed_findings(bundle)
    assert FINDING_NON_FINITE_PAYLOAD in codes(findings)
    assert any("daily_returns" in finding["detail"] for finding in findings)
    assert all(finding["blocking"] for finding in findings)


def test_undeclared_happy_bundle_has_zero_findings():
    assert detect_fail_closed_findings(good_bundle()) == []


def test_scan_non_finite_reports_json_paths():
    payload = {"a": [1.0, {"b": float("inf")}], "c": 2}
    assert scan_non_finite(payload) == ["$.a[1].b"]


# --------------------------------------------------------------------------- #
# 4) Temporary-ledger semantics: first / replay / collision
# --------------------------------------------------------------------------- #
def test_temporary_ledger_first_publish_replay_and_collision(tmp_path):
    ledger = make_ledger_path(tmp_path)
    arms = build_dry_run_arms()
    signatures = {name: arms[name].baseline_stress().signature() for name in arms}

    record = exercise_temporary_ledger_semantics(
        arms, stress_signatures=signatures, ledger_path=ledger
    )
    assert record["denominator_final"] == len(ARM_NAMES)
    assert record["rows_total"] == len(ARM_NAMES)
    for name, per_arm in record["per_arm"].items():
        assert per_arm["first_stage"] == "PUBLISHED"
        assert per_arm["first_delta"] == 1
        assert per_arm["replay_stage"] == "IDEMPOTENT_REPLAY_SKIPPED"
        assert per_arm["replay_delta"] == 0
        assert per_arm["collision_published"] is False
        assert per_arm["collision_stage"] == "IDEMPOTENT_REPLAY_SKIPPED"
        assert per_arm["collision_delta"] == 0

    # ledger bytes are unchanged by the replays and collisions: the digest
    # recorded at the end equals a digest over exactly the 3 first publishes
    state = snapshot(ledger)
    assert state["count"] == 3
    assert record["ledger_sha256_after"] == state["sha256"]
    keys = {row["trial_key_sha256"] for row in state["rows"]}
    assert len(keys) == 3  # three DISTINCT arm keys, no collision ever landed


def test_collision_with_different_content_never_appends(tmp_path):
    ledger = make_ledger_path(tmp_path)
    arms = build_dry_run_arms()
    signatures = {name: arms[name].baseline_stress().signature() for name in arms}
    dummy = build_dummy_metrics(ANCHOR)
    first = publish_arm_to_temporary_ledger(
        arm=ANCHOR,
        strategy=arms[ANCHOR],
        stress_signature=signatures[ANCHOR],
        ledger_path=ledger,
        dummy_metrics=dummy,
    )
    assert first["stage"] == "PUBLISHED" and first["denominator_delta"] == 1
    sha_before = snapshot(ledger)["sha256"]

    mutated = dict(dummy)
    mutated["net_return_sum"] = round(dummy["net_return_sum"] + 123.0, 12)
    collision = publish_arm_to_temporary_ledger(
        arm=ANCHOR,
        strategy=arms[ANCHOR],
        stress_signature=signatures[ANCHOR],
        ledger_path=ledger,
        dummy_metrics=mutated,
    )
    assert collision["published"] is False
    assert collision["denominator_delta"] == 0
    assert snapshot(ledger)["sha256"] == sha_before  # bytes unchanged


# --------------------------------------------------------------------------- #
# 5) The real registry is unreachable from the dry-run (fail closed)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "bad_path",
    [
        None,
        DEFAULT_REGISTRY_PATH,
        "dryrun_wrong_suffix.json",
        "not_namespaced_ledger.jsonl",
    ],
)
def test_require_temporary_ledger_refuses_real_or_unnamespaced_paths(
    tmp_path, bad_path
):
    with pytest.raises(ContractViolation):
        require_temporary_ledger(bad_path)


def test_require_temporary_ledger_refuses_results_registry_tree(tmp_path):
    nested = tmp_path / "results" / "registry" / "dryrun_nested.jsonl"
    nested.parent.mkdir(parents=True)
    nested.touch()
    with pytest.raises(ContractViolation, match="results/registry"):
        require_temporary_ledger(nested)


def test_require_temporary_ledger_refuses_non_temp_directories(tmp_path):
    inside_repo = REPO / "dryrun_should_be_refused.jsonl"  # repo is not temp
    with pytest.raises(ContractViolation, match="system temp tree"):
        require_temporary_ledger(inside_repo)


# --------------------------------------------------------------------------- #
# 6) End-to-end fail-closed dry-runs on defective arms
# --------------------------------------------------------------------------- #
def _arms_with_undeclared_benchmark_control():
    arms = build_dry_run_arms()
    broken = build_dry_run_arms(exclude_benchmark=False)
    arms[CAUSAL_CONTROL] = broken[CAUSAL_CONTROL]
    return arms


def test_dry_run_refuses_publication_when_benchmark_declaration_missing(tmp_path):
    ledger = make_ledger_path(tmp_path)
    result = run_exact_arm_dryrun(
        ledger_path=ledger, arms=_arms_with_undeclared_benchmark_control()
    )
    assert result["ok"] is False
    matching = [
        finding
        for finding in result["findings"]
        if finding.get("arm") == CAUSAL_CONTROL
        and finding["code"] == FINDING_MISSING_BENCHMARK_DECLARATION
    ]
    assert matching, result["findings"]
    # the defective arm is refused fail closed; nothing is published for it
    assert result["arms"][CAUSAL_CONTROL]["published"] is False
    state = snapshot(ledger)
    published_arms = {
        json.loads(line)["experiment_id"]
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert all(exp.startswith(DRYRUN_MATRIX_ID) for exp in published_arms)
    assert state["count"] == 2  # anchor + neighbour only


class _BrokenTickSizeStrategy(DummyDeterministicStrategy):
    """Anchor clone whose cost model drops one symbol's tick size."""

    def cost_model(self) -> CostModel:
        model = super().cost_model()
        broken = dict(model.default_tick_sizes)
        broken.pop(sorted(broken)[0])
        return CostModel(
            taker_fee_bps=float(model.taker_fee_bps),
            adverse_tick_slip_floor=int(model.adverse_tick_slip_floor),
            default_tick_sizes=broken,
        )


def _broken_neighbour() -> DummyDeterministicStrategy:
    return _BrokenTickSizeStrategy(
        symbols=DRYRUN_SYMBOLS,
        instants_ns=DRYRUN_INSTANTS_NS,
        n_select=5,
        daily_drift_by_symbol=DRYRUN_DRIFTS,
        settle_rate_by_day_index=DRYRUN_RATES,
        excluded_benchmark_symbol=DRYRUN_BENCHMARK,
        window_start_iso=DRYRUN_WINDOW_START_ISO,
        window_end_iso=DRYRUN_WINDOW_END_ISO,
        strategy_id="v11_dryrun_neighbour",
        family_id="V11_DRYRUN_EXACT_ARMS",
        arm_config_id="v11-dryrun-arm-neighbour",
        fold_count=2,
        purge_days=1,
    )


def test_dry_run_stage_failure_blocks_publication_fail_closed(tmp_path):
    ledger = make_ledger_path(tmp_path)
    arms = build_dry_run_arms()
    arms[NEIGHBOUR] = _broken_neighbour()
    result = run_exact_arm_dryrun(ledger_path=ledger, arms=arms)
    assert result["ok"] is False
    tick_stage = [
        stage
        for stage in result["stages"]
        if stage["name"] == "fills" and stage["ok"] is False
    ]
    assert tick_stage and "tick_size" in tick_stage[0]["error"]
    assert result["arms"][NEIGHBOUR]["published"] is False
    assert snapshot(ledger)["count"] == 2  # only healthy arms published


# --------------------------------------------------------------------------- #
# 7) Platform safety: nothing tracked is ever written by this suite
# --------------------------------------------------------------------------- #
def _tracked_side_effects() -> tuple[frozenset, str]:
    results_root = REPO / "results"
    if results_root.exists():
        files = frozenset(str(p) for p in results_root.rglob("*") if p.is_file())
    else:
        files = frozenset()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return files, status


def test_dry_run_writes_nothing_under_the_repo(tmp_path):
    before_files, before_status = _tracked_side_effects()
    result = run_exact_arm_dryrun(ledger_path=make_ledger_path(tmp_path))
    after_files, after_status = _tracked_side_effects()

    assert result["ok"] is True
    assert after_files == before_files  # no results/ artifact, no ledger row
    assert after_status == before_status  # no tracked file rewritten
    ledger_under_repo = REPO / "results" / "registry"
    assert not any(
        str(ledger_under_repo) in str(p) for p in [Path(result["ledger"]["path"])]
    )


def test_detection_bundle_carries_every_declared_hole_key():
    bundle = good_bundle()
    for key in (
        "universe",
        "tick_sizes",
        "benchmark_declaration",
        "terminal_valuation",
        "funding_bundle",
        "manifest",
        "payload",
    ):
        assert key in bundle, key


@pytest.mark.parametrize("arm", sorted(ARM_NAMES))
def test_dummy_metrics_are_finite_deterministic_and_explicitly_not_scored(arm):
    first = build_dummy_metrics(arm)
    second = build_dummy_metrics(arm)
    assert first == second  # fixed constants, no randomness
    assert first["kind"] == DRYRUN_DUMMY_METRICS_KIND
    assert first["scored"] is False and first["dry_run"] is True
    for field in ("net_return_sum", "expectancy_per_day", "max_drawdown"):
        value = first[field]
        assert isinstance(value, float) and math.isfinite(value)
    # magnitudes stay in dummy territory: nowhere near a scored PnL claim
    assert abs(first["net_return_sum"]) < 1.0
