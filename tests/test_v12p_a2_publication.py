"""V12P lane A2 tests -- publication guard + ledger hardening.

Coverage required by PLAN section 7-A2 (V12) deliverables:

* D1 -- zero-position publication guard: publication REFUSES when
  ``n_positions == 0`` or when no valid decision/fill record exists
  (``REFUSED_ZERO_POSITIONS`` / ``REFUSED_NO_VALID_DECISION_FILL``,
  repairing the L-V11-4 launch-1 incident); missing evidence fails closed.
* D2 -- refused computations are accounting events: each refusal increments
  the OBSERVED denominator exactly once (one OBSERVATION row, unique
  ``trial_key``, per ``research/control/v12_run/ledger_package/schema.json``)
  and can never publish.
* D3 -- exact replay of the same trial (same ``trial_key`` incl.
  ``arm_config_digest``) increments NEITHER counter and adds NO row.
* D4 -- family-contract cell guard: any computed cell outside the frozen
  per-family cell list (generic superset, L-V11-1) is refused with a stable
  reason code and never published.
* D5 -- portable ledger transfer: manifest verification passes on identical
  bytes and fails closed on tamper/missing/schema/path-escape; a manifest
  can be regenerated for host migration.
* D6 -- concurrency (serialized appends never corrupt) and migration.

All ledgers live under ``tmp_path``; tracked files are opened READ-ONLY
(schema.json / transfer_manifest.json pins).  No historical ledger byte is
rewritten anywhere.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
from pathlib import Path

import pytest

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity, StressSpec
from research.adapter_v10.publish import (
    PRESCORE_BLOCKED,
    evaluate_pre_score_gate,
    publish_trial,
)
from research.global_ledger import snapshot as global_snapshot
from research.v11.publication_identity import arm_config_digest
from research.v12.accounting import (
    CELL_RESULT_REQUIRED_FIELDS,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    OBSERVATION_FROZEN_NOTE,
    OBSERVATION_REQUIRED_FIELDS,
    REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT,
    REFUSED_NO_VALID_DECISION_FILL,
    REFUSED_POSITION_COUNT_ABSENT,
    REFUSED_ZERO_POSITIONS,
    ROW_TYPE_CELL_RESULT,
    ROW_TYPE_OBSERVATION,
    append_v12_row,
    canonical_cell_key,
    enforce_family_contract_cells,
    freeze_family_cell_contract,
    publish_v12_cell,
    validate_position_evidence,
    v12_denominator_view,
    v12_trial_key,
)
from research.v12.ledger_transfer import (
    MANIFEST_REASON_FILE_MISSING,
    MANIFEST_REASON_PATH_ESCAPE,
    MANIFEST_REASON_ROWS_MISMATCH,
    MANIFEST_REASON_SHA256_MISMATCH,
    regenerate_transfer_manifest,
    sha256_bytes,
    verify_or_refuse,
    verify_transfer_manifest,
    write_transfer_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "research/control/v12_run/ledger_package/schema.json"
TRACKED_MANIFEST_PATH = (
    REPO_ROOT / "research/control/v12_run/ledger_package/transfer_manifest.json"
)

BASELINE_CELL = StressSpec(name="baseline")
FEE_X2_CELL = StressSpec(name="fee_x2")
UNSUPPORTED_CELL = StressSpec(name="drop_one_fold", dropped_fold_index=0)

#: The launch-1 incident shape (L-V11-4): score_valid=true over all-zero
#: finite metrics for a book that held NO positions.
ZERO_POSITION_METRICS = {
    "score_valid": True,
    "net_return_sum": 0.0,
    "expectancy_per_day": 0.0,
    "max_drawdown": 0.0,
    "n_positions": 0,
    "n_decisions": 0,
    "n_fills": 0,
}
VALID_METRICS = {
    "score_valid": True,
    "net_return_sum": 0.0123,
    "expectancy_per_day": 0.0004,
    "max_drawdown": 0.0031,
    "n_positions": 12,
    "n_decisions": 34,
    "n_fills": 30,
}
HEAD = "f" * 40


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def make_identity(role: str = "anchor") -> StrategyIdentity:
    return StrategyIdentity(
        strategy_id="strat-v12",
        family_id="family-v12",
        arm_config_id="control_mode:anchor",
        direction="net_long_short",
        window_start_iso="2025-08-22T00:00:00Z",
        window_end_iso="2026-08-21T00:00:00Z",
        config={"arm_role": role},
    )


def arm_digest(role: str = "anchor") -> str:
    return arm_config_digest(make_identity(role), arm_id=role)


def cell_kwargs(
    tmp_path,
    ledger_name: str = "experiments_v12.jsonl",
    arm_id: str = "anchor",
    cell=BASELINE_CELL,
    **overrides,
) -> dict:
    kwargs = dict(
        strategy_id="strat-v12",
        family="family-v12",
        arm_id=arm_id,
        arm_config_digest=arm_digest(arm_id),
        stress_signature=cell,
        window_start_iso="2025-08-22T00:00:00Z",
        window_end_iso="2026-08-21T00:00:00Z",
        scored_metrics=dict(VALID_METRICS),
        result_sha256="c" * 64,
        ledger_path=tmp_path / ledger_name,
        producer_head_sha=HEAD,
    )
    kwargs.update(overrides)
    return kwargs


def read_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# --------------------------------------------------------------------------- #
# D1 -- zero-position publication guard (L-V11-4)
# --------------------------------------------------------------------------- #
def test_zero_position_baseline_is_refused_and_cannot_publish(tmp_path):
    result = publish_v12_cell(
        **cell_kwargs(tmp_path, scored_metrics=dict(ZERO_POSITION_METRICS))
    )
    assert result["published"] is False
    assert result["stage"] == STAGE_REFUSED
    assert result["reasons"][0] == REFUSED_ZERO_POSITIONS
    # The refusal is an accounting event, never a publication: the ledger
    # carries ONLY an OBSERVATION row (no CELL_RESULT, no result fields).
    rows = read_rows(tmp_path / "experiments_v12.jsonl")
    assert len(rows) == 1
    assert rows[0]["row_type"] == ROW_TYPE_OBSERVATION
    assert "result_sha256" not in rows[0] and "published_utc" not in rows[0]
    assert v12_denominator_view(tmp_path / "experiments_v12.jsonl") == {
        "published": 0,
        "observed": 1,
        "observed_total": 1,
        "rows": 1,
    }


def test_missing_or_invalid_position_evidence_fails_closed(tmp_path):
    # Absent n_positions is a refusal, never a silent pass.
    absent = {k: v for k, v in VALID_METRICS.items() if k != "n_positions"}
    result = publish_v12_cell(**cell_kwargs(tmp_path, scored_metrics=absent))
    assert result["reasons"][0] == REFUSED_POSITION_COUNT_ABSENT
    assert validate_position_evidence(absent)[0] is False

    # n_positions > 0 but NO valid decision/fill record: refused.
    no_evidence = {
        **{k: v for k, v in VALID_METRICS.items() if k not in ("n_decisions", "n_fills")},
        "n_positions": 12,
    }
    result2 = publish_v12_cell(
        **cell_kwargs(tmp_path, scored_metrics=no_evidence, arm_id="neighbour"),
    )
    assert result2["reasons"][0] == REFUSED_NO_VALID_DECISION_FILL

    # A valid record needs an instrument AND a timestamp; symbol alone or a
    # bare string is NOT valid evidence.
    for bad in ("BTCUSDT", {"symbol": "BTCUSDT"}, {"ts": 1, "symbol": ""}, 7):
        evidence = {**no_evidence, "decisions": [bad]}
        ok, reasons = validate_position_evidence(evidence)
        assert ok is False and REFUSED_NO_VALID_DECISION_FILL in reasons

    # n_positions as float/bool/str is invalid, not zero.
    for bogus in (1.0, True, "12", None):
        ok, _ = validate_position_evidence({**VALID_METRICS, "n_positions": bogus})
        assert ok is False


def test_legacy_global_ledger_path_gets_the_guard_only_when_opted_in(tmp_path):
    # The launch-1 incident on the legacy path: all-zero finite metrics with
    # score_valid=true passed the historical gate.  The historical behavior
    # is preserved for existing callers (V11 readability; semantics only get
    # STRONGER, never weaker), and the guard is opt-in via the flag...
    legacy_metrics = {
        "score_valid": True,
        "net_return_sum": 0.0,
        "expectancy_per_day": 0.0,
        "max_drawdown": 0.0,
    }
    ok, reasons = evaluate_pre_score_gate(legacy_metrics)
    assert ok is True and reasons == []

    ok2, reasons2 = evaluate_pre_score_gate(
        {**ZERO_POSITION_METRICS, **legacy_metrics}, position_evidence=True
    )
    assert ok2 is False
    assert REFUSED_ZERO_POSITIONS in reasons2

    # ...or via publish_trial(require_position_evidence=True), which refuses
    # BEFORE any append and leaves the ledger byte-identical.
    from research.adapter_v10.protocol import StressSpec as _SS
    from research.adapter_v10.stress import BASELINE_NAME

    ledger = tmp_path / "legacy.jsonl"
    refused = publish_trial(
        identity=make_identity(),
        stress_signature=_SS(name=BASELINE_NAME).signature(),
        scored_metrics={**ZERO_POSITION_METRICS, **legacy_metrics},
        payload_digests={"result_sha256": "d" * 64},
        experiment_digest="e" * 64,
        matrix_id="v12p-a2-legacy",
        ledger_path=str(ledger),
        arm_id="anchor",
        require_position_evidence=True,
    )
    assert refused["published"] is False
    assert refused["stage"] == PRESCORE_BLOCKED
    assert REFUSED_ZERO_POSITIONS in refused["pre_score_reasons"]
    assert not ledger.exists() or global_snapshot(str(ledger))["count"] == 0

    # The guarded V12 entry point refuses the same payload by default.
    v12 = publish_v12_cell(
        **cell_kwargs(
            tmp_path,
            ledger_name="v12_guarded.jsonl",
            scored_metrics={**ZERO_POSITION_METRICS, **legacy_metrics},
        )
    )
    assert v12["reasons"][0] == REFUSED_ZERO_POSITIONS


# --------------------------------------------------------------------------- #
# D2 -- refusal increments observed EXACTLY ONCE and can never publish
# --------------------------------------------------------------------------- #
def test_refusal_observed_exactly_once_and_replay_adds_no_row(tmp_path):
    ledger = tmp_path / "once.jsonl"
    first = publish_v12_cell(
        **cell_kwargs(tmp_path, ledger_name="once.jsonl",
                      scored_metrics=dict(ZERO_POSITION_METRICS))
    )
    assert first["stage"] == STAGE_REFUSED
    assert first["observed_delta"] == 1
    assert first["published_delta"] == 0

    # EXACT replay of the same refused trial (same trial_key incl.
    # arm_config_digest): no new row, no counter movement.
    replay = publish_v12_cell(
        **cell_kwargs(tmp_path, ledger_name="once.jsonl",
                      scored_metrics=dict(ZERO_POSITION_METRICS))
    )
    assert replay["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert replay["trial_key"] == first["trial_key"]
    assert replay["observed_delta"] == 0
    assert v12_denominator_view(ledger) == {
        "published": 0, "observed": 1, "observed_total": 1, "rows": 1,
    }

    # The observed trial can NEVER publish later under the same key: the
    # OBSERVATION row owns the trial_key forever (no rewrite, no second row).
    resurrect = publish_v12_cell(
        **cell_kwargs(tmp_path, ledger_name="once.jsonl")  # valid metrics now
    )
    assert resurrect["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert resurrect["published"] is False
    assert len(read_rows(ledger)) == 1
    assert v12_denominator_view(ledger)["published"] == 0


def test_observation_row_matches_frozen_schema_json():
    """Every row type written by this lane matches the frozen row_schemas."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    declared = schema["row_schemas"]
    frozen_cell = [
        f.split(" (")[0] for f in declared[ROW_TYPE_CELL_RESULT]
    ]
    frozen_obs = [f.split(" (")[0] for f in declared[ROW_TYPE_OBSERVATION]]
    assert list(CELL_RESULT_REQUIRED_FIELDS) == frozen_cell
    assert list(OBSERVATION_REQUIRED_FIELDS) == frozen_obs
    assert "(compute-once observation; never publishable)" in (
        declared[ROW_TYPE_OBSERVATION][-1]
    )
    assert OBSERVATION_FROZEN_NOTE == "compute-once observation; never publishable"
    assert schema["invariants"] == [
        "append-only JSONL",
        "trial_key unique across all rows",
        "every computed scored base result appears exactly once "
        "(published as CELL_RESULT or refused as OBSERVATION)",
        "exact replay adds no row",
        "no row is ever rewritten or deleted",
    ]


# --------------------------------------------------------------------------- #
# D3 -- replay idempotence (published side)
# --------------------------------------------------------------------------- #
def test_exact_replay_of_published_trial_is_fully_idempotent(tmp_path):
    ledger = tmp_path / "replay.jsonl"
    first = publish_v12_cell(**cell_kwargs(tmp_path, ledger_name="replay.jsonl"))
    assert first["stage"] == STAGE_PUBLISHED
    assert first["published_delta"] == 1
    before = v12_denominator_view(ledger)
    before_bytes = ledger.read_bytes()

    replay = publish_v12_cell(**cell_kwargs(tmp_path, ledger_name="replay.jsonl"))
    assert replay["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert replay["published"] is False
    assert replay["trial_key"] == first["trial_key"]
    assert replay["published_delta"] == 0 and replay["observed_delta"] == 0

    assert v12_denominator_view(ledger) == before
    assert ledger.read_bytes() == before_bytes  # no row added, bytes pinned

    # A DIFFERENT arm_config_digest is a DIFFERENT trial: it publishes under
    # its own key (the digest is inside the key material).
    other = publish_v12_cell(
        **cell_kwargs(tmp_path, ledger_name="replay.jsonl", arm_id="neighbour")
    )
    assert other["stage"] == STAGE_PUBLISHED
    assert other["trial_key"] != first["trial_key"]
    assert v12_denominator_view(ledger)["published"] == 2


def test_trial_key_moves_with_arm_config_digest_and_cell(tmp_path):
    key_anchor = v12_trial_key(
        strategy_id="s", family="f", arm_id="anchor",
        arm_config_digest=arm_digest("anchor"),
        stress_signature=BASELINE_CELL,
        window_start_iso="w1", window_end_iso="w2",
    )
    key_neighbour = v12_trial_key(
        strategy_id="s", family="f", arm_id="neighbour",
        arm_config_digest=arm_digest("neighbour"),
        stress_signature=BASELINE_CELL,
        window_start_iso="w1", window_end_iso="w2",
    )
    assert key_anchor != key_neighbour
    # Same inputs reproduce the same key (replay determinism).
    assert key_anchor == v12_trial_key(
        strategy_id="s", family="f", arm_id="anchor",
        arm_config_digest=arm_digest("anchor"),
        stress_signature=BASELINE_CELL,
        window_start_iso="w1", window_end_iso="w2",
    )
    # Cell drift is also key material.
    assert key_anchor != v12_trial_key(
        strategy_id="s", family="f", arm_id="anchor",
        arm_config_digest=arm_digest("anchor"),
        stress_signature=FEE_X2_CELL,
        window_start_iso="w1", window_end_iso="w2",
    )
    assert canonical_cell_key(BASELINE_CELL) == canonical_cell_key(
        BASELINE_CELL.signature()
    )


# --------------------------------------------------------------------------- #
# D4 -- family-contract cell guard (L-V11-1 generic superset)
# --------------------------------------------------------------------------- #
def test_family_contract_superset_refusal(tmp_path):
    contract = freeze_family_cell_contract(
        "family-v12", [BASELINE_CELL, FEE_X2_CELL]
    )
    ledger = tmp_path / "contract.jsonl"

    # The generic 6-cell matrix contains drop_one_fold; the frozen family
    # contract does NOT.  A computed superset cell must be refused...
    result = publish_v12_cell(
        **cell_kwargs(
            tmp_path,
            ledger_name="contract.jsonl",
            cell=UNSUPPORTED_CELL,
            family_contract_cells=contract,
        )
    )
    assert result["published"] is False
    assert result["stage"] == STAGE_REFUSED
    assert result["reasons"][0].startswith(REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT)
    assert result["observed_delta"] == 1  # computed => observed exactly once
    assert v12_denominator_view(ledger) == {
        "published": 0, "observed": 1, "observed_total": 1, "rows": 1,
    }
    rows = read_rows(ledger)
    assert rows[0]["row_type"] == ROW_TYPE_OBSERVATION

    # ...and a replay of the same unsupported cell adds nothing.
    again = publish_v12_cell(
        **cell_kwargs(
            tmp_path, ledger_name="contract.jsonl",
            cell=UNSUPPORTED_CELL, family_contract_cells=contract,
        )
    )
    assert again["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert len(read_rows(ledger)) == 1

    # Contract-subset cells still publish normally under the same guard.
    ok = publish_v12_cell(
        **cell_kwargs(
            tmp_path, ledger_name="contract.jsonl",
            cell=BASELINE_CELL, family_contract_cells=contract,
        )
    )
    assert ok["stage"] == STAGE_PUBLISHED
    view = v12_denominator_view(ledger)
    assert view["published"] == 1 and view["observed"] == 1


def test_family_contract_enforcer_raises_with_reason_code(tmp_path):
    contract = freeze_family_cell_contract("family-v12", [BASELINE_CELL])
    # Subset passes; superset raises with the stable reason code.
    enforce_family_contract_cells(contract, [BASELINE_CELL], family="family-v12")
    with pytest.raises(ContractViolation) as excinfo:
        enforce_family_contract_cells(
            contract, [BASELINE_CELL, UNSUPPORTED_CELL], family="family-v12"
        )
    assert REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT in str(excinfo.value)
    # Deterministic freezing: duplicate cells are refused, signatures and
    # StressSpec instances freeze to the same key.
    assert freeze_family_cell_contract("f", [BASELINE_CELL.signature()]) == (
        freeze_family_cell_contract("f", [BASELINE_CELL])
    )
    with pytest.raises(ContractViolation):
        freeze_family_cell_contract("f", [BASELINE_CELL, BASELINE_CELL])


# --------------------------------------------------------------------------- #
# D5 -- portable ledger transfer manifest (L-V11-5)
# --------------------------------------------------------------------------- #
def _make_ledger(tmp_path, root: Path, name="results/registry/experiments_v12.jsonl"):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    publish_v12_cell(**cell_kwargs(tmp_path, ledger_name=str(target)))
    publish_v12_cell(
        **cell_kwargs(tmp_path, ledger_name=str(target), arm_id="neighbour",
                      scored_metrics=dict(ZERO_POSITION_METRICS))
    )
    return target


def test_transfer_manifest_verification_pass_and_fail(tmp_path):
    host_a = tmp_path / "host_a"
    ledger = _make_ledger(tmp_path, host_a)
    manifest = regenerate_transfer_manifest(
        ledger, root=host_a, producer_role="A2", generated_utc="2026-09-03T00:00:00Z",
        note="test package",
    )
    assert manifest["schema"] == "v12_ledger_transfer_manifest_v1"
    assert manifest["files"][0]["rows"] == 2
    assert manifest["empty_ledger_sha256"] == sha256_bytes(b"")

    package = host_a / "pkg" / "transfer_manifest.json"
    write_transfer_manifest(manifest, package)
    # Verification PASSES against identical bytes.
    ok = verify_transfer_manifest(package, root=host_a)
    assert ok["ok"] is True and ok["files_verified"] == 1
    # ...and against an in-memory manifest (same semantics).
    assert verify_transfer_manifest(manifest, root=host_a)["ok"] is True

    # TAMPER: flip one byte in the ledger -> sha256 mismatch, fail closed.
    host_b = tmp_path / "host_b"
    shutil.copytree(host_a, host_b)
    tampered = host_b / "results/registry/experiments_v12.jsonl"
    data = tampered.read_bytes().replace(b'"anchor"', b'"anch0r"', 1)
    tampered.write_bytes(data)
    with pytest.raises(ContractViolation) as excinfo:
        verify_transfer_manifest(package, root=host_b)
    assert MANIFEST_REASON_SHA256_MISMATCH in str(excinfo.value)

    # MISSING file: fail closed.
    tampered.unlink()
    with pytest.raises(ContractViolation) as excinfo:
        verify_transfer_manifest(package, root=host_b)
    assert MANIFEST_REASON_FILE_MISSING in str(excinfo.value)

    # ROW-COUNT drift with intact bytes: fail closed (append outside the
    # package without regenerating the manifest is not adoptable).
    manifest_bad = dict(manifest)
    manifest_bad["files"] = [dict(manifest["files"][0], rows=99)]
    refusal = verify_or_refuse(manifest_bad, root=host_a)
    assert refusal["ok"] is False
    assert refusal["reason"] == MANIFEST_REASON_ROWS_MISMATCH

    # PATH ESCAPE: an absolute or .. path is refused before any read.
    for bad_path in ("/etc/passwd", "../outside.jsonl"):
        evil = dict(manifest)
        evil["files"] = [dict(manifest["files"][0], path=bad_path)]
        refusal = verify_or_refuse(evil, root=host_a)
        assert refusal["ok"] is False
        assert refusal["reason"] == MANIFEST_REASON_PATH_ESCAPE

    # SCHEMA token mismatch: refused.
    evil_schema = dict(manifest, schema="v12_ledger_transfer_manifest_v0")
    assert verify_or_refuse(evil_schema, root=host_a)["ok"] is False

    # The TRACKED frozen package pins the empty-ledger seed (read-only pin;
    # the ledger itself is gitignored and absent here, so verification
    # against an empty root must FAIL CLOSED, never fabricate a pass).
    tracked = json.loads(TRACKED_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert tracked["schema"] == "v12_ledger_transfer_manifest_v1"
    assert tracked["empty_ledger_sha256"] == sha256_bytes(b"")
    assert tracked["files"][0]["sha256"] == sha256_bytes(b"")
    assert tracked["files"][0]["rows"] == 0
    empty_root = tmp_path / "virgin_host"
    empty_root.mkdir()
    refusal = verify_or_refuse(TRACKED_MANIFEST_PATH, root=empty_root)
    assert refusal["ok"] is False
    assert refusal["reason"] == MANIFEST_REASON_FILE_MISSING


# --------------------------------------------------------------------------- #
# D6 -- concurrent append safety
# --------------------------------------------------------------------------- #
def test_concurrent_writers_append_serialized_rows_without_corruption(tmp_path):
    ledger = tmp_path / "race.jsonl"
    roles = [f"arm-{i}" for i in range(6)]
    results: list[dict | None] = [None] * len(roles)
    start = threading.Barrier(len(roles))

    def attempt(index: int) -> None:
        role = roles[index]
        start.wait(timeout=30)
        # Half the writers publish a valid cell, half a refused (zero
        # position) compute -- both are accounting events on one file.
        metrics = dict(VALID_METRICS) if index % 2 == 0 else dict(ZERO_POSITION_METRICS)
        results[index] = publish_v12_cell(
            **cell_kwargs(
                tmp_path, ledger_name="race.jsonl", arm_id=role,
                scored_metrics=metrics,
            )
        )

    threads = [
        threading.Thread(target=attempt, args=(i,), daemon=True)
        for i in range(len(roles))
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert all(r is not None for r in results)
    # Exactly 6 rows land: 3 published + 3 observed; every line parses and
    # every trial_key is unique (serialized appends, no corruption).
    rows = read_rows(ledger)
    assert len(rows) == len(roles)
    keys = [r["trial_key"] for r in rows]
    assert len(set(keys)) == len(roles)
    types = sorted(r["row_type"] for r in rows)
    assert types == [ROW_TYPE_CELL_RESULT] * 3 + [ROW_TYPE_OBSERVATION] * 3
    view = v12_denominator_view(ledger)
    assert view == {
        "published": 3, "observed": 3, "observed_total": 6, "rows": 6,
    }
    # Racing the SAME trial from many threads still appends exactly once.
    same: list[dict | None] = [None] * 8
    start2 = threading.Barrier(len(same))

    def attempt_same(index: int) -> None:
        start2.wait(timeout=30)
        same[index] = publish_v12_cell(
            **cell_kwargs(tmp_path, ledger_name="race.jsonl", arm_id="solo")
        )

    threads2 = [
        threading.Thread(target=attempt_same, args=(i,), daemon=True)
        for i in range(len(same))
    ]
    for t in threads2:
        t.start()
    for t in threads2:
        t.join(timeout=60)
    published_same = [r for r in same if r["published"] is True]
    replayed_same = [r for r in same if r["stage"] == STAGE_IDEMPOTENT_REPLAY]
    assert len(published_same) == 1
    assert len(replayed_same) == len(same) - 1
    assert v12_denominator_view(ledger)["rows"] == 7


# --------------------------------------------------------------------------- #
# D6 -- host migration (manifest regenerated + verified)
# --------------------------------------------------------------------------- #
def test_host_migration_manifest_regenerated_and_verified(tmp_path):
    host_a = tmp_path / "migrate_a"
    ledger_a = _make_ledger(tmp_path, host_a)
    manifest_a = regenerate_transfer_manifest(
        ledger_a, root=host_a, producer_role="A2",
        generated_utc="2026-09-03T00:00:00Z",
    )
    package_a = host_a / "pkg" / "transfer_manifest.json"
    written_sha = write_transfer_manifest(manifest_a, package_a)
    assert written_sha == sha256_bytes(
        (json.dumps(manifest_a, indent=1, sort_keys=True) + "\n").encode("utf-8")
    )
    # Refuses to silently overwrite an existing manifest.
    with pytest.raises(ContractViolation):
        write_transfer_manifest(manifest_a, package_a)

    # --- move to the new host: copy ledger bytes + package verbatim -------
    host_b = tmp_path / "migrate_b"
    ledger_relative = ledger_a.relative_to(host_a)  # manifest declares it
    ledger_b = host_b / ledger_relative
    ledger_b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ledger_a, ledger_b)
    package_b = host_b / "pkg" / "transfer_manifest.json"
    package_b.parent.mkdir()
    shutil.copyfile(package_a, package_b)

    # Adoption REQUIRES verification first; it passes on identical bytes.
    verified = verify_transfer_manifest(package_b, root=host_b)
    assert verified["ok"] is True

    # Regenerating on the new host reproduces the same manifest content
    # (deterministic; only the generation stamp may differ).
    manifest_b = regenerate_transfer_manifest(
        ledger_b, root=host_b, producer_role="A2",
        generated_utc=manifest_a["generated_utc"],
    )
    assert manifest_b == manifest_a

    # Unverified adoption (stale manifest / appended row) fails closed.
    extra_row = {
        "row_type": "CELL_RESULT",
        "trial_key": "a" * 64,
        "arm_id": "late",
        "arm_config_digest": arm_digest("late"),
        "family": "family-v12",
        "cell": BASELINE_CELL.signature(),
        "result_sha256": "b" * 64,
        "published_utc": "2026-09-03T00:00:00Z",
        "producer_head_sha": HEAD,
    }
    with open(ledger_b, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(extra_row, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(ContractViolation) as excinfo:
        verify_transfer_manifest(package_b, root=host_b)
    assert MANIFEST_REASON_SHA256_MISMATCH in str(excinfo.value)
    # Regenerated manifest reflects the appended row; a fresh verify passes.
    manifest_b2 = regenerate_transfer_manifest(
        ledger_b, root=host_b, producer_role="A2",
        generated_utc=manifest_a["generated_utc"],
    )
    assert manifest_b2["files"][0]["rows"] == manifest_a["files"][0]["rows"] + 1
    package_c = host_b / "pkg2" / "transfer_manifest.json"
    write_transfer_manifest(manifest_b2, package_c)
    assert verify_transfer_manifest(package_c, root=host_b)["ok"] is True


# --------------------------------------------------------------------------- #
# Preservation -- historical V10/V11 ledger keys stay readable
# --------------------------------------------------------------------------- #
def test_historical_v11_publication_path_is_untouched(tmp_path):
    """Old global-ledger keys remain readable; this lane never rewrites them."""
    from research.adapter_v10.stress import BASELINE_NAME
    from research.v11.publication_identity import legacy_v1_key

    legacy = StrategyIdentity(
        strategy_id="strat-x",
        family_id="family-x",
        arm_config_id="control_mode:anchor",
        direction="net_long_short",
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-01-08T00:00:00Z",
        config={"arm_role": "anchor"},
    )
    ledger = tmp_path / "history.jsonl"
    result = publish_trial(
        identity=legacy,
        stress_signature=StressSpec(name=BASELINE_NAME).signature(),
        scored_metrics={
            "score_valid": True,
            "net_return_sum": 1.0,
            "expectancy_per_day": 0.1,
            "max_drawdown": 0.5,
        },
        payload_digests={"result_sha256": "a" * 64},
        experiment_digest="b" * 64,
        matrix_id="v12p-a2-history",
        ledger_path=str(ledger),
    )
    assert result["published"] is True
    assert result["identity_version"] == "v1"
    assert result["trial_key_sha256"] == legacy_v1_key(
        identity=legacy,
        stress_signature=StressSpec(name=BASELINE_NAME).signature(),
    )
    frozen = ledger.read_bytes()
    # The V12 machinery writes to a SEPARATE ledger file; the historical one
    # is byte-identical after V12 activity beside it.
    publish_v12_cell(
        **cell_kwargs(tmp_path, ledger_name="experiments_v12.jsonl")
    )
    assert ledger.read_bytes() == frozen
    assert hashlib.sha256(frozen).hexdigest() == hashlib.sha256(
        ledger.read_bytes()
    ).hexdigest()
