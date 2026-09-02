"""V11P lane A2 tests -- publication identity v2 + denominator reconciliation.

Coverage required by the frozen PLAN section 7-A2 deliverables:

* D1/D2 -- trial identity carries an explicit ``arm_id`` and a canonical
  ``arm_config_digest`` covering every score-affecting arm field; anchor,
  neighbour and causal-control arms produce DISTINCT v2 keys while exact
  replay of each reproduces the same key with zero additional publication;
* D3 (regression pin of the documented V10 defect) -- the frozen v1 key
  COLLAPSES arms that differ only inside ``StrategyIdentity.config`` (M01-N
  shared ``control_mode='anchor'`` with M01-A while ``neighbour_mode`` lived
  outside the key), which is exactly why one computed neighbour was never
  published;
* D4 -- compute-once increments the OBSERVED denominator even when
  publication is refused, while a true idempotent replay moves NEITHER
  counter; the M01 neighbour is reconciled append-only from the documented
  terminal artifact provenance (119 published / 120 observed), never
  re-scored;
* D5 -- migration/fault coverage: v1-key collision, missing arm id, digest
  drift, duplicate replay, historical-byte preservation and concurrent
  append.

Synthetic identities only; the real M01 terminal artifact is opened READ-ONLY
for provenance equality.  No historical ledger row is rewritten anywhere.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

import pytest

from research.adapter_v10.protocol import ContractViolation, StrategyIdentity, StressSpec
from research.adapter_v10.publish import (
    IDEMPOTENT_REPLAY,
    LEDGER_APPEND_REFUSED,
    PUBLISHED,
    PUBLISHED_CELL_KIND,
    canonical_scored_payload,
    denominator_view,
    publish_trial,
    record_trial_observation,
    trial_denominator,
    trial_key,
)
from research.adapter_v10.stress import BASELINE_NAME
from research.global_ledger import snapshot, verify_append_only
from research.protocol.registry import validate_entry_kind
from research.v11.publication_identity import (
    ARM_CONFIG_DIGEST_SCHEMA,
    M01_FROZEN_OBSERVED_DENOMINATOR,
    M01_FROZEN_PUBLISHED_DENOMINATOR,
    M01_NEIGHBOUR_ARM_ID,
    M01_NEIGHBOUR_FROZEN_METRICS,
    M01_TERMINAL_ARTIFACT,
    OBSERVATION_VERDICT,
    TRIAL_OBSERVATION_SCHEMA_VERSION,
    canonical_arm_payload,
    arm_config_digest,
    canonical_scored_payload_v2,
    legacy_v1_key,
    legacy_v1_payload,
    load_m01_terminal,
    m01_neighbour_amendment_entry,
    trial_key_v2,
    V1_PAYLOAD_KEYS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
M01_TERMINAL_PATH = REPO_ROOT / M01_TERMINAL_ARTIFACT

SCORED_METRICS = {
    "score_valid": True,
    "net_return_sum": 0.0123,
    "expectancy_per_day": 0.0004,
    "max_drawdown": 0.0031,
}

ARM_ROLES = ("anchor", "neighbour", "causal_control")


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #
def make_identity(role: str = "anchor", **overrides) -> StrategyIdentity:
    """Three-arm identity mirroring the documented M01 defect.

    All arms SHARE ``arm_config_id`` and differ ONLY inside ``config`` --
    exactly the shape the frozen v1 key could not distinguish (M01-N shared
    ``control_mode='anchor'`` with M01-A while ``neighbour_mode`` was outside
    the key).  The explicit ``arm_id`` is the V11P repair.
    """
    kwargs = dict(
        strategy_id="strat-x",
        family_id="family-x",
        arm_config_id="control_mode:anchor",
        direction="net_long_short",
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-01-08T00:00:00Z",
        config={"arm_role": role},
    )
    identity = StrategyIdentity(arm_id=role, **{**kwargs, **overrides})
    return identity


def arm_kwargs(
    tmp_path,
    role: str = "anchor",
    ledger_name: str = "ledger.jsonl",
    **overrides,
) -> dict:
    """publish_trial kwargs for one arm against a temp ledger."""
    kwargs = dict(
        identity=make_identity(role),
        arm_id=role,
        stress_signature=StressSpec(name=BASELINE_NAME).signature(),
        scored_metrics=dict(SCORED_METRICS),
        payload_digests={"result_sha256": "a" * 64},
        experiment_digest="b" * 64,
        matrix_id="v11p-a2-cell",
        ledger_path=str(tmp_path / ledger_name),
    )
    kwargs.update(overrides)
    return kwargs


def stress_only() -> dict:
    return StressSpec(name=BASELINE_NAME).signature()


# --------------------------------------------------------------------------- #
# D3 regression pin -- the V10 v1 key collision (documented M01 defect)
# --------------------------------------------------------------------------- #
def test_v1_keying_collides_arms_v2_keying_distinguishes_them(tmp_path):
    identities = {role: make_identity(role) for role in ARM_ROLES}

    # DEFECT PIN: the frozen v1 payload ignores identity.config entirely, so
    # all three arms collapse onto ONE trial key -- the second computed arm
    # could never be published (duplicate_trial_key_already_published).
    v1_keys = {
        trial_key(
            canonical_scored_payload(
                identity=identities[role], stress_signature=stress_only()
            )
        )
        for role in ARM_ROLES
    }
    assert len(v1_keys) == 1

    # REPAIR: the v2 key carries the explicit arm + arm_config_digest, so the
    # same three identities produce three distinct keys.
    v2_keys = {
        trial_key_v2(identity=identities[role], stress_signature=stress_only(), arm_id=role)
        for role in ARM_ROLES
    }
    assert len(v2_keys) == 3
    # v1 and v2 live in disjoint key spaces (schema_version is in the payload).
    assert v1_keys.isdisjoint(v2_keys)


def test_publishing_all_three_arms_under_v2_is_exactly_once(tmp_path):
    first_keys = {}
    for role in ARM_ROLES:
        result = publish_trial(**arm_kwargs(tmp_path, role, ledger_name="arms.jsonl"))
        assert result["published"] is True
        assert result["stage"] == PUBLISHED
        assert result["identity_version"] == "v2"
        assert result["denominator_delta"] == 1
        first_keys[role] = result["trial_key_sha256"]

    assert len(set(first_keys.values())) == 3
    assert trial_denominator(str(tmp_path / "arms.jsonl")) == 3

    # Exact replay of each arm: same key, zero additional publication.
    for role in ARM_ROLES:
        replay = publish_trial(**arm_kwargs(tmp_path, role, ledger_name="arms.jsonl"))
        assert replay["published"] is False
        assert replay["stage"] == IDEMPOTENT_REPLAY
        assert replay["trial_key_sha256"] == first_keys[role]
        assert replay["denominator_delta"] == 0
    state = snapshot(str(tmp_path / "arms.jsonl"))
    assert state["count"] == 3
    assert trial_denominator(str(tmp_path / "arms.jsonl")) == 3


# --------------------------------------------------------------------------- #
# D1 -- explicit arm_id + canonical arm_config_digest (fail closed)
# --------------------------------------------------------------------------- #
def test_v2_refuses_missing_blank_or_padded_arm_ids(tmp_path):
    bare = StrategyIdentity(
        strategy_id="strat-x",
        family_id="family-x",
        arm_config_id="control_mode:anchor",
        direction="net_long_short",
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-01-08T00:00:00Z",
        config={"arm_role": "anchor"},
    )
    # No declared arm and no arm argument: a v2 key is refused, never guessed.
    with pytest.raises(ContractViolation):
        publish_trial(
            **arm_kwargs(tmp_path, "anchor", identity=bare, arm_id="", identity_version="v2")
        )
    with pytest.raises(ContractViolation):
        publish_trial(**arm_kwargs(tmp_path, "anchor", arm_id="   ", identity_version="v2"))
    with pytest.raises(ContractViolation):
        StrategyIdentity(
            strategy_id="s",
            family_id="f",
            arm_config_id="a",
            direction="d",
            window_start_iso="w1",
            window_end_iso="w2",
            arm_id=" anchor ",
        )
    # The frozen v1 key space refuses arm-aware trials (no silent fallback).
    with pytest.raises(ContractViolation):
        publish_trial(**arm_kwargs(tmp_path, "anchor", identity_version="v1"))
    # Unknown versions are refused, never approximated.
    with pytest.raises(ContractViolation):
        publish_trial(**arm_kwargs(tmp_path, "anchor", identity_version="v9"))
    # An identity WITHOUT a declared arm keeps the historical v1 default.
    legacy = StrategyIdentity(
        strategy_id="strat-x",
        family_id="family-x",
        arm_config_id="control_mode:anchor",
        direction="net_long_short",
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-01-08T00:00:00Z",
        config={"arm_role": "anchor"},
    )
    result = publish_trial(
        **arm_kwargs(tmp_path, "anchor", identity=legacy, arm_id="", ledger_name="legacy.jsonl")
    )
    assert result["identity_version"] == "v1"
    assert result["trial_key_sha256"] == legacy_v1_key(
        identity=legacy, stress_signature=stress_only()
    )


def test_every_score_affecting_arm_field_moves_the_digest():
    base = make_identity("anchor")
    base_digest = arm_config_digest(base, arm_id="anchor")
    mutations = {
        "strategy_id": "strat-y",
        "family_id": "family-y",
        "arm_config_id": "control_mode:other",
        "direction": "net_short",
        "funding_sign_convention": "SHORT_PAYS_POSITIVE_RATE",
        "config": {"arm_role": "anchor", "fee_overlay_bps": 7.0},
    }
    for field, value in mutations.items():
        drifted = make_identity("anchor", **{field: value})
        assert arm_config_digest(drifted, arm_id="anchor") != base_digest, field
    # A different benchmark-exclusion set is score-affecting too.
    benched = make_identity("anchor", benchmark_symbols_excluded=("BENCH00",))
    assert arm_config_digest(benched, arm_id="anchor") != base_digest
    # Window stamps are CELL fields (already inside the full trial key), not
    # arm fields: the digest deliberately stays comparable across cells.
    recelled = make_identity("anchor", window_start_iso="2025-02-01T00:00:00Z")
    assert arm_config_digest(recelled, arm_id="anchor") == base_digest
    # The digest is stable across rebuilds and carries its versioned schema.
    assert arm_config_digest(base, arm_id="anchor") == base_digest
    payload = canonical_arm_payload(base, arm_id="anchor")
    assert payload["schema"] == ARM_CONFIG_DIGEST_SCHEMA
    assert payload["arm_id"] == "anchor"
    assert payload["config"] == base.public_payload()["config"]


def test_digest_drift_yields_distinct_keys_and_separate_publications(tmp_path):
    first = publish_trial(**arm_kwargs(tmp_path, "anchor", ledger_name="drift.jsonl"))
    assert first["published"] is True
    drifted = make_identity(
        "anchor", config={"arm_role": "anchor", "entry_offset_bars": 1}
    )
    second = publish_trial(
        **arm_kwargs(
            tmp_path,
            "anchor",
            ledger_name="drift.jsonl",
            identity=drifted,
        )
    )
    # Digest drift is DETECTED as a different trial (new key, new row), never
    # silently collapsed onto the first publication.
    assert second["published"] is True
    assert second["arm_config_digest"] != first["arm_config_digest"]
    assert second["trial_key_sha256"] != first["trial_key_sha256"]
    assert trial_denominator(str(tmp_path / "drift.jsonl")) == 2


def test_arm_declaration_does_not_alter_the_historical_public_payload():
    """Adding ``arm_id`` to StrategyIdentity must not rewrite legacy views."""
    with_arm = make_identity("anchor")
    bare = StrategyIdentity(
        strategy_id="strat-x",
        family_id="family-x",
        arm_config_id="control_mode:anchor",
        direction="net_long_short",
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-01-08T00:00:00Z",
        config={"arm_role": "anchor"},
    )
    assert with_arm.public_payload() == bare.public_payload()
    # ...and therefore the v1 key of the legacy identity is unchanged.
    assert (
        legacy_v1_key(identity=with_arm, stress_signature=stress_only())
        == legacy_v1_key(identity=bare, stress_signature=stress_only())
    )


def test_legacy_v1_payload_shape_is_pinned():
    payload = legacy_v1_payload(
        identity=make_identity("anchor"), stress_signature=stress_only()
    )
    assert tuple(sorted(payload)) == tuple(sorted(V1_PAYLOAD_KEYS))
    assert "arm_id" not in payload and "arm_config_digest" not in payload
    assert payload["schema_version"] == "v10.adapter.trial_publication.v1"
    # Byte-stable with the historical publisher key.
    assert (
        legacy_v1_key(identity=make_identity("neighbour"), stress_signature=stress_only())
        == trial_key(
            canonical_scored_payload(
                identity=make_identity("neighbour"), stress_signature=stress_only()
            )
        )
    )


# --------------------------------------------------------------------------- #
# D4 -- compute-once accounting: observed vs published denominators
# --------------------------------------------------------------------------- #
def test_compute_once_counts_observed_even_when_publication_refused(tmp_path):
    # verdict=None makes the registry refuse the CELL_RESULT append AFTER the
    # pre-score gate: the trial was scored (compute-once) but not published.
    refused = publish_trial(
        **arm_kwargs(tmp_path, "neighbour", verdict=None, observe_unpublished=True)
    )
    assert refused["pre_score_passed"] is True
    assert refused["published"] is False
    assert refused["stage"] == LEDGER_APPEND_REFUSED
    assert refused["observed"]["attempted"] is True
    assert refused["observed"]["appended"] is True

    view = denominator_view(refused["ledger_path"])
    assert view["published"] == 0
    assert view["observed_unpublished"] == 1
    assert view["observed_total"] == 1

    # The observation row is kind-less: it can never count as a publication.
    rows = snapshot(refused["ledger_path"])["rows"]
    assert len(rows) == 1
    assert "kind" not in rows[0]
    assert validate_entry_kind(rows[0]) == []
    assert rows[0]["schema"] == TRIAL_OBSERVATION_SCHEMA_VERSION
    assert rows[0]["observation"]["status"] == "COMPUTED_UNPUBLISHED"
    assert rows[0]["observation"]["counts_toward_published_denominator"] is False
    assert rows[0]["observation"]["rescore_forbidden"] is True

    # Re-attempting the same refused compute does NOT double count.
    again = publish_trial(
        **arm_kwargs(tmp_path, "neighbour", verdict=None, observe_unpublished=True)
    )
    assert again["observed"]["appended"] is False
    assert again["observed"]["reasons"] == ["duplicate_observation_key_already_recorded"]
    assert denominator_view(refused["ledger_path"])["observed_unpublished"] == 1


def test_true_idempotent_replay_moves_neither_counter(tmp_path):
    published = publish_trial(**arm_kwargs(tmp_path, "anchor", observe_unpublished=True))
    assert published["published"] is True
    before = denominator_view(published["ledger_path"])
    assert before == {"published": 1, "observed_unpublished": 0, "observed_total": 1}

    replay = publish_trial(
        **arm_kwargs(tmp_path, "anchor", observe_unpublished=True)
    )
    assert replay["stage"] == IDEMPOTENT_REPLAY
    assert replay["observed"]["attempted"] is False
    assert replay["observed"]["reasons"] == [
        "true_v2_replay_of_published_trial_not_observable"
    ]
    assert denominator_view(published["ledger_path"]) == before


def test_v1_replay_is_never_observable():
    # A v1 replay cannot be attributed to an arm, so it must not silently
    # inflate the observed denominator either.
    kwargs = dict(
        identity=make_identity("anchor"),
        stress_signature=stress_only(),
    )
    payload = canonical_scored_payload(**kwargs)
    record = {
        "stage": IDEMPOTENT_REPLAY,
        "reasons": ["duplicate_trial_key_already_published"],
    }
    from research.adapter_v10.publish import _observation_outcome

    outcome = _observation_outcome(
        record,
        identity=kwargs["identity"],
        stress_signature=kwargs["stress_signature"],
        effective_arm="",
        identity_version="v1",
        matrix_id="v11p-a2-cell",
        observe_unpublished=True,
        ledger_path=None,
    )
    assert outcome["attempted"] is False
    assert outcome["appended"] is False
    assert outcome["reasons"] == ["observation_requires_explicit_arm_id"]
    # And the v1 key of that identity collides with its sibling arms (D3).
    assert trial_key(payload) == trial_key(
        canonical_scored_payload(
            identity=make_identity("neighbour"), stress_signature=stress_only()
        )
    )


def test_observation_superseded_when_the_trial_later_publishes(tmp_path):
    refused = publish_trial(
        **arm_kwargs(tmp_path, "anchor", verdict=None, observe_unpublished=True)
    )
    assert refused["stage"] == LEDGER_APPEND_REFUSED
    assert denominator_view(refused["ledger_path"])["observed_unpublished"] == 1

    repaired = publish_trial(**arm_kwargs(tmp_path, "anchor"))
    assert repaired["published"] is True
    view = denominator_view(repaired["ledger_path"])
    # The trial moved from observed-unpublished to published: counted once.
    assert view == {"published": 1, "observed_unpublished": 0, "observed_total": 1}


# --------------------------------------------------------------------------- #
# D4 -- M01 neighbour reconciliation (append-only, documented provenance)
# --------------------------------------------------------------------------- #
def test_m01_amendment_matches_documented_provenance():
    assert M01_TERMINAL_PATH.exists()
    doc = load_m01_terminal(M01_TERMINAL_PATH)
    cell = doc["cells"]["neighbour"]
    entry = m01_neighbour_amendment_entry(terminal_path=M01_TERMINAL_PATH)

    assert "kind" not in entry  # registry kind contract accepts it as-is
    assert entry["verdict"] == OBSERVATION_VERDICT
    assert entry["schema"] == TRIAL_OBSERVATION_SCHEMA_VERSION

    observation = entry["observation"]
    assert observation["status"] == cell["status"] == "COMPUTED_UNPUBLISHED_CONTRACT_GAP"
    assert observation["computed_unpublished"] is True
    assert observation["rescore_forbidden"] is True
    assert observation["counts_toward_published_denominator"] is False
    assert observation["counts_toward_observed_denominator"] is True
    assert observation["arm_id"] == M01_NEIGHBOUR_ARM_ID
    assert observation["frozen_metrics"] == {
        "net_return_sum": cell["net_return_sum"],
        "expectancy_per_day": cell["expectancy_per_day"],
        "max_drawdown": cell["max_drawdown"],
    } == dict(sorted(M01_NEIGHBOUR_FROZEN_METRICS.items()))
    assert observation["publish_stage_documented"] == cell["publish_stage"]
    assert observation["root_cause"] == cell["root_cause"]
    assert "neighbour_mode is outside the key" in observation["root_cause"]

    # Provenance is byte-exact with the read-only terminal artifact.
    assert entry["provenance"]["artifact"] == M01_TERMINAL_ARTIFACT
    assert entry["provenance"]["artifact_sha256"] == hashlib.sha256(
        M01_TERMINAL_PATH.read_bytes()
    ).hexdigest()
    assert entry["provenance"]["original_producer_role"] == doc["producer_role"]
    assert entry["provenance"]["verdict"] == doc["verdict"] == "M01_FAMILY_REJECT"

    # A drifted terminal must be refused, never silently re-scored.
    drifted = json.loads(json.dumps(doc))
    drifted["cells"]["neighbour"]["net_return_sum"] = 1.0
    with pytest.raises(ContractViolation):
        m01_neighbour_amendment_entry(terminal=drifted)


def test_m01_reconciliation_is_append_only_119_published_120_observed(tmp_path):
    ledger = tmp_path / "m01_reconciled.jsonl"
    # Seed the frozen M01 published denominator: 117 historical + 2 published
    # CELL_RESULT rows (anchor + C2 placebo), timestamps monotonically newer.
    base_ns = 1_755_733_500  # 2025-08-21-ish; ordering is what matters
    lines = []
    for index in range(M01_FROZEN_PUBLISHED_DENOMINATOR):
        lines.append(
            json.dumps(
                {
                    "experiment_id": f"v10r-m01-family-hist-{index:03d}",
                    "verdict": "CELL_RESULT",
                    "kind": PUBLISHED_CELL_KIND,
                    "schema": "v10.adapter.trial_publication.v1",
                    "matrix_id": "v10r-m01-family",
                    "trial_key_sha256": hashlib.sha256(f"hist-{index}".encode()).hexdigest(),
                    "appended_at": f"2025-08-21T{index // 60:02d}:{index % 60:02d}:00Z",
                },
                sort_keys=True,
            )
        )
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert trial_denominator(str(ledger)) == M01_FROZEN_PUBLISHED_DENOMINATOR == 119

    first_bytes = ledger.read_bytes()
    entry = m01_neighbour_amendment_entry(terminal_path=M01_TERMINAL_PATH)
    recorded = record_trial_observation(entry, str(ledger))
    assert recorded["appended"] is True

    view = denominator_view(str(ledger))
    assert view["published"] == 119  # historical rows untouched, still 2/9 cells
    assert view["observed_unpublished"] == 1
    assert view["observed_total"] == M01_FROZEN_OBSERVED_DENOMINATOR == 120

    # Append-only: every historical byte is exactly where it was.
    assert ledger.read_bytes().startswith(first_bytes)

    # Re-running the reconciliation is a no-op (exactly-once observation).
    repeat = record_trial_observation(
        m01_neighbour_amendment_entry(terminal_path=M01_TERMINAL_PATH), str(ledger)
    )
    assert repeat["appended"] is False
    assert repeat["reasons"] == ["duplicate_observation_key_already_recorded"]
    assert denominator_view(str(ledger)) == view


def test_frozen_m01_constants_match_the_terminal_artifact():
    assert M01_FROZEN_PUBLISHED_DENOMINATOR == 119
    assert M01_FROZEN_OBSERVED_DENOMINATOR == 120
    assert M01_FROZEN_OBSERVED_DENOMINATOR == M01_FROZEN_PUBLISHED_DENOMINATOR + 1
    doc = load_m01_terminal(M01_TERMINAL_PATH)
    cell = doc["cells"]["neighbour"]
    for name, value in M01_NEIGHBOUR_FROZEN_METRICS.items():
        assert cell[name] == value
    assert doc["budget"]["cells_published"] == 2
    assert doc["budget"]["unpublished_documented"] == 1


def test_historical_v1_ledger_bytes_are_never_rewritten(tmp_path):
    ledger = tmp_path / "mixed.jsonl"
    legacy = StrategyIdentity(
        strategy_id="strat-x",
        family_id="family-x",
        arm_config_id="control_mode:anchor",
        direction="net_long_short",
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-01-08T00:00:00Z",
        config={"arm_role": "anchor"},
    )
    historical = publish_trial(
        **arm_kwargs(tmp_path, "anchor", identity=legacy, arm_id="", ledger_name="mixed.jsonl")
    )
    assert historical["identity_version"] == "v1"
    frozen_bytes = (tmp_path / "mixed.jsonl").read_bytes()

    for role in ("anchor", "neighbour", "causal_control"):
        result = publish_trial(
            **arm_kwargs(tmp_path, role, ledger_name="mixed.jsonl")
        )
        assert result["published"] is True
        assert result["identity_version"] == "v2"

    grown = (tmp_path / "mixed.jsonl").read_bytes()
    # The historical v1 row is byte-for-byte untouched, still first.
    assert grown.startswith(frozen_bytes)
    state = snapshot(str(tmp_path / "mixed.jsonl"))
    assert state["count"] == 4
    assert trial_denominator(str(tmp_path / "mixed.jsonl")) == 4
    assert verify_append_only(tmp_path / "mixed.jsonl") is True


# --------------------------------------------------------------------------- #
# D5 -- concurrent append fault coverage
# --------------------------------------------------------------------------- #
def test_concurrent_publish_of_one_trial_appends_exactly_once(tmp_path):
    threads: list[threading.Thread] = []
    results: list[dict | None] = [None] * 8
    start = threading.Barrier(len(results))

    def attempt(index: int) -> None:
        start.wait(timeout=30)
        results[index] = publish_trial(
            **arm_kwargs(tmp_path, "anchor", ledger_name="race.jsonl")
        )

    for index in range(len(results)):
        threads.append(threading.Thread(target=attempt, args=(index,), daemon=True))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)

    published = [r for r in results if r["published"] is True]
    replayed = [r for r in results if r["stage"] == IDEMPOTENT_REPLAY]
    assert len(published) == 1
    assert len(replayed) == len(results) - 1
    keys = {r["trial_key_sha256"] for r in results if r is not None}
    assert len(keys) == 1
    state = snapshot(str(tmp_path / "race.jsonl"))
    assert state["count"] == 1
    assert trial_denominator(str(tmp_path / "race.jsonl")) == 1
    assert verify_append_only(tmp_path / "race.jsonl") is True


def test_concurrent_distinct_arms_append_without_corruption(tmp_path):
    threads: list[threading.Thread] = []
    results: list[dict | None] = [None] * 6
    start = threading.Barrier(len(results))

    def attempt(index: int) -> None:
        role = ARM_ROLES[index % len(ARM_ROLES)] + f"-{index}"
        start.wait(timeout=30)
        results[index] = publish_trial(
            **arm_kwargs(tmp_path, role, ledger_name="parallel.jsonl")
        )

    for index in range(len(results)):
        threads.append(threading.Thread(target=attempt, args=(index,), daemon=True))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)

    assert all(r["published"] is True for r in results)
    keys = [r["trial_key_sha256"] for r in results]
    assert len(set(keys)) == len(results)
    state = snapshot(str(tmp_path / "parallel.jsonl"))
    assert state["count"] == len(results)
    assert len(state["rows"]) == len(results)  # every line parses, none lost
    assert trial_denominator(str(tmp_path / "parallel.jsonl")) == len(results)
    assert verify_append_only(tmp_path / "parallel.jsonl") is True
