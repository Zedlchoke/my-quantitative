"""V8 resolved-run-contract tests (PLAN sections 5.2/6/8; owner A6).

Covers :mod:`research.resolved_contract_v8` fail-closed behavior end to
end: strict frozen inventory/universe/costs/limits/schedule, per-fold
7-day purge/embargo enforcement, explicit-real-commit launch_sha gate,
the committed TEMPLATE artifact conformance (launch_sha=None +
``launch_sha_frozen: false``), and the two-stage ``freeze_final()``
writer that A1 calls at integration.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.resolved_contract_v8 import (  # noqa: E402
    BENCHMARK_FROZEN,
    CONTRACT_RELPATH,
    CONTROL_TRIAL_ID,
    COSTS_FROZEN,
    EXECUTION_CONTRACT_FROZEN,
    FROZEN_TRIAL_IDS,
    FROZEN_UNIVERSE,
    LIMITS_FROZEN,
    PROVENANCE_ATTESTATION_PATH_FROZEN,
    PROVENANCE_BASELINE_PATH_FROZEN,
    PROVENANCE_CONTRACT_FROZEN,
    REGISTRY_OUTPUT_CONTRACT_FROZEN,
    SCHEMA_VERSION,
    SIGNAL_FAMILY_FROZEN,
    TEMPLATE_RELPATH,
    WEEKLY_SCHEDULE_FROZEN,
    ResolvedContractErrorV8,
    build_resolved_contract_v8,
    build_template_contract,
    discover_bootstrap_commit,
    freeze_final,
    load_template,
    verify_resolved_contract_v8,
)

# Bootstrap commit of this V8 worktree branch ("V8 BOOTSTRAP:" subject);
# a REAL commit object used as the launch sha in unit happy paths.
REAL_COMMIT_SHA = discover_bootstrap_commit(REPO)[0]
FINAL_LAUNCH_SHA_FOR_TESTS = "f" * 40      # format-valid, NOT a real commit
NOT_HEX_SHA = "g" * 40                     # fails the format gate outright

W0 = datetime(2024, 8, 21, 14, 30, tzinfo=timezone.utc)   # candidate.yaml target_start_utc
W1 = datetime(2026, 8, 21, 0, 0, tzinfo=timezone.utc)     # candidate.yaml target_end_utc


def default_folds(n: int = 3) -> list[dict]:
    span = (W1 - W0) / n
    return [
        {
            "fold_id": f"F{i + 1}",
            "start_utc": (W0 + i * span).isoformat(),
            "end_utc": (W0 + (i + 1) * span if i + 1 < n else W1).isoformat(),
            "purge_days": 7,
            "embargo_days": 7,
        }
        for i in range(n)
    ]


FROZEN_TRIAL_INVENTORY = [
    {"trial_id": "XSECT-WREV-3D", "formation_lookback_days": 3, "kind": "reversal"},
    {"trial_id": "XSECT-WREV-7D", "formation_lookback_days": 7, "kind": "reversal"},
    {"trial_id": "XSECT-WREV-14D", "formation_lookback_days": 14, "kind": "reversal"},
    {
        "trial_id": "XSECT-WMOM-7D-CONTROL",
        "formation_lookback_days": 7,
        "kind": "momentum_control",
    },
]

DATASET_HASHES_OK = {"daily_bars_15m": "a" * 64}


def contract_kwargs(**overrides) -> dict:
    kw = dict(
        window_start=W0.isoformat(),
        window_end=W1.isoformat(),
        folds=default_folds(),
        traded_universe=list(FROZEN_UNIVERSE),
        benchmark=BENCHMARK_FROZEN,
        costs=dict(COSTS_FROZEN),
        limits=dict(LIMITS_FROZEN),
        weekly_schedule=dict(WEEKLY_SCHEDULE_FROZEN),
        dataset_hashes=dict(DATASET_HASHES_OK),
        launch_sha=REAL_COMMIT_SHA,
        trial_inventory=[dict(t) for t in FROZEN_TRIAL_INVENTORY],
        signal_family=SIGNAL_FAMILY_FROZEN,
        registry_output_contract=dict(REGISTRY_OUTPUT_CONTRACT_FROZEN),
        execution_contract={
            "max_concurrent_workers": EXECUTION_CONTRACT_FROZEN[
                "max_concurrent_workers"
            ],
            "stress_surface": list(EXECUTION_CONTRACT_FROZEN["stress_surface"]),
        },
        provenance_contract=dict(PROVENANCE_CONTRACT_FROZEN),
        repo_root=REPO,
        generated_at_utc="2026-08-25T00:00:00Z",
    )
    kw.update(overrides)
    return kw


# --------------------------------------------------------------------------- #
# 1) Happy path: canonical body + self-hash + canonical trial ordering
# --------------------------------------------------------------------------- #
def test_build_resolved_contract_v8_happy_path():
    built_reversed_input = build_resolved_contract_v8(
        **contract_kwargs(trial_inventory=list(reversed(FROZEN_TRIAL_INVENTORY))))
    built = build_resolved_contract_v8(**contract_kwargs())
    verify_resolved_contract_v8(built)
    verify_resolved_contract_v8(built_reversed_input)
    assert built["schema_version"] == SCHEMA_VERSION
    assert built["signal_family"] == SIGNAL_FAMILY_FROZEN
    assert built["weekly_schedule"] == WEEKLY_SCHEDULE_FROZEN
    assert [t["trial_id"] for t in built["trial_inventory"]] == list(FROZEN_TRIAL_IDS)
    assert built["trial_inventory"] == built_reversed_input["trial_inventory"]
    assert built["universe"]["traded_symbols"] == sorted(FROZEN_UNIVERSE)
    assert built["universe"]["n_traded"] == 6
    assert built["universe"]["benchmark"] not in built["universe"]["traded_symbols"]
    assert built["costs"] == COSTS_FROZEN
    assert built["limits"] == LIMITS_FROZEN
    assert built["registry_output_contract"] == REGISTRY_OUTPUT_CONTRACT_FROZEN
    assert built["execution_contract"] == EXECUTION_CONTRACT_FROZEN
    assert built["provenance_contract"] == PROVENANCE_CONTRACT_FROZEN
    assert built["launch_sha"] == REAL_COMMIT_SHA
    assert built["launch_sha_frozen"] is True
    assert len(built["folds"]) == 3
    assert all(f["purge_days"] == 7 and f["embargo_days"] == 7 for f in built["folds"])
    assert built["window"]["days"] == pytest.approx((W1 - W0).total_seconds() / 86_400.0)


def test_unknown_kwargs_never_accepted_silently():
    with pytest.raises(ResolvedContractErrorV8, match="unexpected contract arguments"):
        build_resolved_contract_v8(**contract_kwargs(funding_lookback_days=3))


def test_dataset_hash_values_must_be_hex_digests():
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(
            **contract_kwargs(dataset_hashes={"x": "nope"}))
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(dataset_hashes={}))


# --------------------------------------------------------------------------- #
# 2) Fail-closed on missing/nulled required arguments (mirror sibling style)
# --------------------------------------------------------------------------- #
def test_missing_or_null_required_arguments_fail_closed():
    kwargs = contract_kwargs()
    base = build_resolved_contract_v8(**kwargs)
    verify_resolved_contract_v8(base)

    absent = {k: v for k, v in kwargs.items() if k != "weekly_schedule"}
    with pytest.raises((TypeError, ResolvedContractErrorV8)):
        build_resolved_contract_v8(**absent)

    for field in (
        "window_start", "folds", "traded_universe", "benchmark", "costs",
        "limits", "weekly_schedule", "dataset_hashes", "launch_sha",
        "trial_inventory", "signal_family", "registry_output_contract",
        "execution_contract", "provenance_contract",
    ):
        bad = dict(kwargs)
        bad[field] = None
        with pytest.raises(ResolvedContractErrorV8):
            build_resolved_contract_v8(**bad)


def test_window_and_fold_structure_fail_closed():
    bad = contract_kwargs(window_end=W0.isoformat())
    with pytest.raises(ResolvedContractErrorV8, match="after window_start"):
        build_resolved_contract_v8(**bad)
    bad = contract_kwargs(window_start="not-a-stamp")
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**bad)
    naive = contract_kwargs(window_start="2024-08-21T14:30:00")
    with pytest.raises(ResolvedContractErrorV8, match="timezone-aware"):
        build_resolved_contract_v8(**naive)

    folds = default_folds()
    folds[1]["end_utc"] = folds[0]["end_utc"]
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(folds=folds))

    folds = default_folds()
    folds[2]["start_utc"] = folds[1]["start_utc"]
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(folds=folds))

    folds = default_folds()
    folds[0]["start_utc"] = "2024-01-01T00:00:00+00:00"   # escapes window
    with pytest.raises(ResolvedContractErrorV8, match="escapes"):
        build_resolved_contract_v8(**contract_kwargs(folds=folds))


# --------------------------------------------------------------------------- #
# 3) Frozen blocks: costs / limits / weekly schedule / registry / execution /
#    provenance — any drift, extra key or missing key raises
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "field,broken",
    [
        ("costs", {"fee_taker": 0.0005}),                       # slippage defaulted?
        ("costs", {"fee_taker": 0.0005, "slippage_ticks": 1, "extra": 1}),
        ("costs", {"fee_taker": 0.001, "slippage_ticks": 1}),   # drifted fee
        ("costs", {"fee_taker": 0.0005, "slippage_ticks": 2}),  # drifted ticks
        ("limits", {"gross": 0.80, "net": 0.0, "long_gross": 0.40,
                    "short_gross": 0.40}),                      # symbol_weight gone
        ("limits", {**LIMITS_FROZEN, "gross": 0.90}),
        ("limits", {**LIMITS_FROZEN, "net": 0.10}),
        ("limits", {**LIMITS_FROZEN, "long_gross": 0.50}),
        ("limits", {**LIMITS_FROZEN, "short_gross": 0.30}),
        ("limits", {**LIMITS_FROZEN, "symbol_weight": 0.25}),
        ("weekly_schedule", {k: v for k, v in WEEKLY_SCHEDULE_FROZEN.items()
                             if k != "warmup_days_min"}),
        ("weekly_schedule", {**WEEKLY_SCHEDULE_FROZEN, "weekday": "SUN"}),
        ("weekly_schedule", {**WEEKLY_SCHEDULE_FROZEN, "utc": False}),
        ("weekly_schedule", {**WEEKLY_SCHEDULE_FROZEN, "rebalance_days": 5}),
        ("weekly_schedule", {**WEEKLY_SCHEDULE_FROZEN, "purge_embargo_days": 3}),
        ("weekly_schedule", {**WEEKLY_SCHEDULE_FROZEN, "warmup_days_min": 7}),
        ("registry_output_contract", {**REGISTRY_OUTPUT_CONTRACT_FROZEN,
                                      "output_root": "results/portfolio_v9"}),
        ("registry_output_contract", {**REGISTRY_OUTPUT_CONTRACT_FROZEN,
                                      "matrix_id": "v8_wrong"}),
        ("provenance_contract", {**PROVENANCE_CONTRACT_FROZEN,
                                 "baseline_path": "research/audits/v7p/baseline_root.json"}),
        ("provenance_contract", {**PROVENANCE_CONTRACT_FROZEN,
                                 "attestation_path": "research/audits/v8p/wrong.json"}),
        ("provenance_contract", {**PROVENANCE_CONTRACT_FROZEN,
                                 "enforcement_required": False}),
    ],
)
def test_frozen_block_drift_rejected(field, broken):
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(**{field: broken}))


def test_execution_contract_stress_surface_is_exact_ordered_freeze():
    reordered = {
        "max_concurrent_workers": 2,
        "stress_surface": list(reversed(EXECUTION_CONTRACT_FROZEN["stress_surface"])),
    }
    with pytest.raises(ResolvedContractErrorV8, match="stress_surface"):
        build_resolved_contract_v8(**contract_kwargs(execution_contract=reordered))
    dropped = {
        "max_concurrent_workers": 2,
        "stress_surface": EXECUTION_CONTRACT_FROZEN["stress_surface"][:-1],
    }
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(execution_contract=dropped))
    widened = {
        "max_concurrent_workers": 2,
        "stress_surface": EXECUTION_CONTRACT_FROZEN["stress_surface"] + ["extra"],
    }
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(execution_contract=widened))
    more_workers = {"max_concurrent_workers": 4,
                    "stress_surface": list(EXECUTION_CONTRACT_FROZEN["stress_surface"])}
    with pytest.raises(ResolvedContractErrorV8, match="max_concurrent_workers"):
        build_resolved_contract_v8(**contract_kwargs(execution_contract=more_workers))
    partial = {"max_concurrent_workers": 2}
    with pytest.raises(ResolvedContractErrorV8, match="exactly keys"):
        build_resolved_contract_v8(**contract_kwargs(execution_contract=partial))
    truthy_int = {**PROVENANCE_CONTRACT_FROZEN, "enforcement_required": 1}
    with pytest.raises(ResolvedContractErrorV8, match="enforcement_required"):
        build_resolved_contract_v8(**contract_kwargs(provenance_contract=truthy_int))


# --------------------------------------------------------------------------- #
# 4) Universe: EXACTLY the frozen six alts; benchmark context-only
# --------------------------------------------------------------------------- #
def test_traded_universe_must_be_exact_frozen_six():
    with pytest.raises(ResolvedContractErrorV8, match="EXACTLY"):
        build_resolved_contract_v8(
            **contract_kwargs(traded_universe=list(FROZEN_UNIVERSE) + ["ETHUSDT"]))
    with pytest.raises(ResolvedContractErrorV8, match="EXACTLY"):
        build_resolved_contract_v8(**contract_kwargs(traded_universe=list(FROZEN_UNIVERSE)[:5]))
    swapped = ["BTCUSDT" if s == "ADAUSDT" else s for s in FROZEN_UNIVERSE]
    with pytest.raises(ResolvedContractErrorV8, match="EXACTLY"):
        build_resolved_contract_v8(**contract_kwargs(traded_universe=swapped))
    duped = list(FROZEN_UNIVERSE)
    duped[1] = duped[0]
    with pytest.raises(ResolvedContractErrorV8, match="duplicates"):
        build_resolved_contract_v8(**contract_kwargs(traded_universe=duped))
    with pytest.raises(ResolvedContractErrorV8, match="benchmark"):
        build_resolved_contract_v8(**contract_kwargs(benchmark="SOLUSDT"))


# --------------------------------------------------------------------------- #
# 5) Per-fold purge/embargo fields are mandatory and pinned to 7 days
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mutate", [
    lambda f: f.update(purge_days=3),
    lambda f: f.update(embargo_days=0),
    lambda f: f.pop("purge_days"),
    lambda f: f.update(purge_days="7"),
    lambda f: f.update(extra_field=1),
])
def test_fold_purge_embargo_fields_fail_closed(mutate):
    folds = default_folds()
    mutate(folds[1])
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(folds=folds))


# --------------------------------------------------------------------------- #
# 6) Trial inventory negatives (count/dupes/drift/control constraints)
# --------------------------------------------------------------------------- #
def test_trial_inventory_count_duplicates_unknown_rejected():
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(
            **contract_kwargs(trial_inventory=FROZEN_TRIAL_INVENTORY[:3]))
    duped = FROZEN_TRIAL_INVENTORY[:3] + [dict(FROZEN_TRIAL_INVENTORY[2])]
    with pytest.raises(ResolvedContractErrorV8, match="duplicate"):
        build_resolved_contract_v8(**contract_kwargs(trial_inventory=duped))
    unknown = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    unknown.append({"trial_id": "XSECT-WREV-10D", "formation_lookback_days": 10,
                    "kind": "reversal"})
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(trial_inventory=unknown))
    missing_one = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    missing_one[0] = {"trial_id": "XSECT-WREV-7D", "formation_lookback_days": 7,
                      "kind": "reversal"}
    with pytest.raises(ResolvedContractErrorV8):   # 3D gone, 7D duplicated
        build_resolved_contract_v8(**contract_kwargs(trial_inventory=missing_one))


def test_trial_kind_and_lookback_drift_rejected():
    bad = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    bad[0]["formation_lookback_days"] = 7          # WREV-3D carrying 7D lookback
    with pytest.raises(ResolvedContractErrorV8, match="drifts"):
        build_resolved_contract_v8(**contract_kwargs(trial_inventory=bad))
    bad = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    bad[0]["kind"] = "momentum_control"            # control sign on reversal id
    with pytest.raises(ResolvedContractErrorV8, match="momentum_control"):
        build_resolved_contract_v8(**contract_kwargs(trial_inventory=bad))
    bad = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    idx = [t["trial_id"] for t in bad].index(CONTROL_TRIAL_ID)
    bad[idx] = {"trial_id": CONTROL_TRIAL_ID, "formation_lookback_days": 3,
                "kind": "momentum_control"}
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(trial_inventory=bad))
    bad = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    bad[1]["kind"] = "short_winners"               # unknown kind string
    with pytest.raises(ResolvedContractErrorV8, match="kind"):
        build_resolved_contract_v8(**contract_kwargs(trial_inventory=bad))
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(signal_family="momentum"))


# --------------------------------------------------------------------------- #
# 7) launch_sha gate: placeholders/non-commit/non-hex all fail closed
# --------------------------------------------------------------------------- #
def test_launch_sha_placeholder_semantics_forbidden():
    for forbidden in ("PENDING_FINAL_CODE_SHA", "TO_FREEZE",
                      "PENDING_INTEGRATION_SHA", "", None):
        with pytest.raises(ResolvedContractErrorV8):
            build_resolved_contract_v8(**contract_kwargs(launch_sha=forbidden))
    with pytest.raises(ResolvedContractErrorV8, match="launch_sha_not_a_commit"):
        build_resolved_contract_v8(
            **contract_kwargs(launch_sha=FINAL_LAUNCH_SHA_FOR_TESTS))
    with pytest.raises(ResolvedContractErrorV8):
        build_resolved_contract_v8(**contract_kwargs(launch_sha=NOT_HEX_SHA))


# --------------------------------------------------------------------------- #
# 8) Committed TEMPLATE artifact: unfrozen state, self-hash, frozen blocks
# --------------------------------------------------------------------------- #
def test_committed_template_artifact_conformance():
    artifact_path = REPO / TEMPLATE_RELPATH
    assert artifact_path.is_file(), "template artifact must be committed"
    template = load_template()          # verifies self-hash + unfrozen state
    assert template["schema_version"] == SCHEMA_VERSION
    assert template["artifact_state"] == "TEMPLATE_PENDING_A1_FREEZE"
    assert template["launch_sha"] is None
    assert template["launch_sha_frozen"] is False
    assert template["dataset_hashes"] == {}
    assert template["trial_inventory"] == [
        {"trial_id": tid,
         "formation_lookback_days":
             {"XSECT-WREV-3D": 3, "XSECT-WREV-7D": 7, "XSECT-WREV-14D": 14,
              CONTROL_TRIAL_ID: 7}[tid],
         "kind": ("momentum_control" if tid == CONTROL_TRIAL_ID else "reversal")}
        for tid in FROZEN_TRIAL_IDS
    ]
    assert template["signal_family"] == SIGNAL_FAMILY_FROZEN
    assert template["weekly_schedule"] == WEEKLY_SCHEDULE_FROZEN
    assert template["registry_output_contract"] == REGISTRY_OUTPUT_CONTRACT_FROZEN
    assert template["execution_contract"] == EXECUTION_CONTRACT_FROZEN
    assert template["costs"] == COSTS_FROZEN
    assert template["limits"] == LIMITS_FROZEN
    assert template["provenance_contract"] == PROVENANCE_CONTRACT_FROZEN
    assert template["universe"]["traded_symbols"] == sorted(FROZEN_UNIVERSE)
    assert template["universe"]["benchmark"] == "BTCUSDT"
    assert template["window"]["start_utc"].startswith("2024-08-21T14:30:00")
    assert template["window"]["end_utc"].startswith("2026-08-21T00:00:00")
    assert len(template["folds"]) == 3
    ids = [f["fold_id"] for f in template["folds"]]
    starts = [datetime.fromisoformat(f["start_utc"]) for f in template["folds"]]
    ends = [datetime.fromisoformat(f["end_utc"]) for f in template["folds"]]
    assert ids == ["F1", "F2", "F3"]
    assert all(s < e for s, e in zip(starts, ends))
    assert all(a <= b for a, b in zip(starts, starts[1:]))
    assert all(f["purge_days"] == 7 and f["embargo_days"] == 7
               for f in template["folds"])
    # Final artifact MUST NOT exist yet: only freeze_final() may create it.
    assert not (REPO / CONTRACT_RELPATH).exists()


def test_template_builder_matches_committed_artifact_body():
    fresh = build_template_contract(
        window_start=W0.isoformat(),
        window_end=W1.isoformat(),
        folds=default_folds(),
        dataset_hashes={},
        repo_root=REPO,
        generated_at_utc="2026-08-25T00:00:00Z",
    )
    verify_resolved_contract_v8(fresh)
    committed = load_template()
    strip = lambda d: {k: v for k, v in d.items()
                       if k not in ("generated_at_utc", "contract_sha256")}
    # Body identical modulo generation timestamp (clock anchor, not science);
    # the self-hash differs only because that timestamp is hashed with it.
    assert strip(fresh) == strip(committed)


def test_template_tamper_detected_by_self_hash(tmp_path):
    template = json.loads((REPO / TEMPLATE_RELPATH).read_text(encoding="utf-8"))
    tampered = copy.deepcopy(template)
    tampered["limits"]["gross"] = 0.95
    path = tmp_path / "tampered.template.json"
    path.write_text(json.dumps(tampered, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ResolvedContractErrorV8, match="contract_sha256 mismatch"):
        load_template(template_path=path)


# --------------------------------------------------------------------------- #
# 9) freeze_final(): the ONLY writer of the final artifact
# --------------------------------------------------------------------------- #
def test_freeze_final_happy_path_writes_verified_final(tmp_path):
    out = tmp_path / "resolved_run_contract_v8.json"
    written = freeze_final(
        REAL_COMMIT_SHA,
        dataset_hashes=dict(DATASET_HASHES_OK),
        template_path=REPO / TEMPLATE_RELPATH,
        final_path=out,
        repo_root=REPO,
    )
    assert written == out
    contract = json.loads(out.read_text(encoding="utf-8"))
    verify_resolved_contract_v8(contract)
    assert contract["launch_sha"] == REAL_COMMIT_SHA
    assert contract["launch_sha_frozen"] is True
    assert "artifact_state" not in contract
    assert contract["dataset_hashes"] == DATASET_HASHES_OK
    assert contract["trial_inventory"][0]["trial_id"] == "XSECT-WREV-3D"
    assert contract["execution_contract"]["max_concurrent_workers"] == 2


def test_freeze_final_refuses_placeholders_and_empty_hashes(tmp_path):
    out = tmp_path / "final.json"
    for forbidden in ("PENDING_FINAL_CODE_SHA", "TO_FREEZE", None, "",
                      FINAL_LAUNCH_SHA_FOR_TESTS):
        with pytest.raises(ResolvedContractErrorV8):
            freeze_final(
                forbidden,
                dataset_hashes=dict(DATASET_HASHES_OK),
                template_path=REPO / TEMPLATE_RELPATH,
                final_path=out,
                repo_root=REPO,
            )
    assert not out.exists()
    with pytest.raises(ResolvedContractErrorV8, match="dataset_hashes"):
        freeze_final(REAL_COMMIT_SHA, dataset_hashes=None,
                     template_path=REPO / TEMPLATE_RELPATH,
                     final_path=out, repo_root=REPO)
    assert not out.exists()


def test_freeze_final_refuses_overwrite_of_existing_final(tmp_path):
    out = tmp_path / "final.json"
    kw = dict(dataset_hashes=dict(DATASET_HASHES_OK),
              template_path=REPO / TEMPLATE_RELPATH,
              final_path=out, repo_root=REPO)
    freeze_final(REAL_COMMIT_SHA, **kw)
    with pytest.raises(ResolvedContractErrorV8, match="already frozen"):
        freeze_final(REAL_COMMIT_SHA, **kw)


def test_freeze_final_detects_template_drift_from_constants(tmp_path):
    template = json.loads((REPO / TEMPLATE_RELPATH).read_text(encoding="utf-8"))
    template["weekly_schedule"]["rebalance_days"] = 5   # drift, then fix hash
    payload = {k: v for k, v in template.items() if k != "contract_sha256"}
    template["contract_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path = tmp_path / "drifted.template.json"
    path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ResolvedContractErrorV8, match="drifted"):
        freeze_final(REAL_COMMIT_SHA, dataset_hashes=dict(DATASET_HASHES_OK),
                     template_path=path, final_path=tmp_path / "final.json",
                     repo_root=REPO)


def test_freeze_final_rejects_unfrozen_state_markers(tmp_path):
    template = json.loads((REPO / TEMPLATE_RELPATH).read_text(encoding="utf-8"))
    template["launch_sha_frozen"] = True   # someone pre-froze the template?
    payload = {k: v for k, v in template.items() if k != "contract_sha256"}
    template["contract_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path = tmp_path / "prefrozen.template.json"
    path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ResolvedContractErrorV8, match="launch_sha_frozen"):
        freeze_final(REAL_COMMIT_SHA, dataset_hashes=dict(DATASET_HASHES_OK),
                     template_path=path, final_path=tmp_path / "final.json",
                     repo_root=REPO)
