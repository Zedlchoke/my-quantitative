"""Exact arm identity + observed-vs-published counter contract tests.

Gate M0 (PLAN_stocks.md section 15): asset-class identities cannot collide;
same-class replay digests are equal; compute-once/publish-fail and
idempotent-replay counter semantics hold.
"""

from __future__ import annotations

import hashlib

import pytest

from research.assets.common.contracts import canonical_json
from research.assets.common.trial_identity import (
    ArmIdentity,
    TrialCounterBook,
    TrialCounters,
    assert_cross_asset_class_separation,
    assert_no_collision,
    canonical_identity_payload,
    check_counter_invariants,
    identity_digest,
    record_computation,
    record_idempotent_replay,
    record_publication_failure,
    record_publication_success,
    digest_preimage,
)

HEX_A = hashlib.sha256(b"universe-a").hexdigest()
HEX_B = hashlib.sha256(b"config-b").hexdigest()


def _identity(asset_class="CRYPTO_PERP", **overrides) -> ArmIdentity:
    kwargs = {
        "asset_class": asset_class,
        "venue": "BINANCE",
        "calendar_id": "TEST_ONLY_DUMMY_SOLAR_24X7",
        "cost_model_id": "CRYPTO_COMPAT::taker::two_tick::mark",
        "universe_digest": HEX_A,
        "family_id": "FAM_MR",
        "arm_id": "ARM_1",
        "arm_config_digest": HEX_B,
    }
    kwargs.update(overrides)
    return ArmIdentity(**kwargs)


# --- identity determinism + collision freedom -------------------------------- #
def test_same_class_replay_digests_are_equal():
    first = identity_digest(_identity())
    second = identity_digest(_identity())
    assert first == second
    # Any single field change produces a different digest.
    mutated = identity_digest(_identity(arm_id="ARM_2"))
    assert mutated != first


@pytest.mark.parametrize(
    "other_class",
    ["US_CASH_EQUITY", "FX_SPOT", "CRYPTO_PERP_V2", "B3_TESTCLASS"],
)
def test_identities_differing_only_in_asset_class_never_collide(other_class):
    base = _identity("CRYPTO_PERP")
    other = _identity(other_class)
    # The non-asset-class fields are identical; digests must still differ.
    assert base.non_class_fields == other.non_class_fields
    assert identity_digest(base) != identity_digest(other)
    assert_cross_asset_class_separation(base, other)  # does not raise


def test_namespacing_is_structural_in_the_preimage():
    crypto = _identity("CRYPTO_PERP")
    equities = _identity("US_CASH_EQUITY")
    preimage_crypto = digest_preimage(crypto)
    preimage_equities = digest_preimage(equities)
    # asset_class appears as namespace AND inside the payload.
    assert '"namespace":"CRYPTO_PERP"' in preimage_crypto
    assert '"namespace":"US_CASH_EQUITY"' in preimage_equities
    assert preimage_crypto != preimage_equities
    assert identity_digest(crypto) == hashlib.sha256(
        preimage_crypto.encode("utf-8")
    ).hexdigest()


def test_collision_assert_helpers_raise_on_breakage():
    base = _identity("CRYPTO_PERP")
    impostor = _identity("US_CASH_EQUITY")
    # Force a (contract-breaking) scenario by monkeypatching the payload
    # function to drop the namespace, then expect the assert to fire.
    import research.assets.common.trial_identity as ti

    original = ti.canonical_identity_payload

    def broken_payload(identity):
        payload = dict(original(identity))
        payload.pop("namespace")
        payload.pop("asset_class")
        payload["fields"] = dict(payload["fields"])
        return payload

    ti.canonical_identity_payload = broken_payload
    try:
        with pytest.raises(ValueError, match="COLLISION"):
            assert_cross_asset_class_separation(base, impostor)
        with pytest.raises(ValueError, match="COLLISION"):
            assert_no_collision([base, impostor])
    finally:
        ti.canonical_identity_payload = original
    # Restored: no collision for genuinely different identities.
    assert_no_collision([base, impostor, _identity("CRYPTO_PERP", arm_id="ARM_2")])


def test_identity_validators_fail_closed():
    with pytest.raises(ValueError, match="asset_class"):
        _identity(asset_class="crypto-perp")
    with pytest.raises(ValueError, match="universe_digest"):
        _identity(universe_digest="xyz")
    with pytest.raises(ValueError, match="venue"):
        _identity(venue="")


def test_canonical_identity_payload_is_json_stable():
    identity = _identity()
    once = canonical_json(canonical_identity_payload(identity))
    twice = canonical_json(canonical_identity_payload(identity))
    assert once == twice


# --- observed-vs-published counters (pure logic) ------------------------------ #
def test_compute_once_publish_fail_increments_observed_only():
    book, status = TrialCounterBook().record_computation("digest-1")
    assert status == "OBSERVED"
    assert book.counters == TrialCounters(observed=1, published=0)
    # Publication FAILS: the failure op is a no-op for counters.
    failed = record_publication_failure(book.counters)
    assert failed == TrialCounters(observed=1, published=0)
    assert check_counter_invariants(failed) == []


def test_publication_success_increments_published_once():
    book, _ = TrialCounterBook().record_computation("digest-1")
    published_book = book.record_publication("digest-1")
    assert published_book.counters == TrialCounters(observed=1, published=1)
    with pytest.raises(ValueError, match="double publication"):
        published_book.record_publication("digest-1")
    with pytest.raises(ValueError, match="unobserved"):
        book.record_publication("never-computed")


def test_idempotent_replay_increments_neither_counter():
    book, _ = TrialCounterBook().record_computation("digest-1")
    replayed_book = book.replay("digest-1")
    assert replayed_book.counters == book.counters == TrialCounters(observed=1, published=0)
    # Also via the low-level op with already_observed=True.
    assert record_computation(book.counters, already_observed=True) == book.counters
    assert record_idempotent_replay(book.counters) == book.counters
    _, status = book.record_computation("digest-1")
    assert status == "REPLAYED"
    assert book.counters == TrialCounters(observed=1, published=0)


def test_two_trials_two_publications_and_invariant_checks():
    book = TrialCounterBook()
    for digest in ("d1", "d2", "d1"):  # third is a replay
        book, _ = book.record_computation(digest)
    assert book.counters == TrialCounters(observed=2, published=0)
    book = book.record_publication("d1")
    book = book.record_publication("d2")
    assert book.counters == TrialCounters(observed=2, published=2)
    with pytest.raises(ValueError, match="unpublished_observed"):
        record_publication_success(book.counters)


def test_counter_invariants_and_validation():
    with pytest.raises(ValueError):
        TrialCounters(observed=1, published=2)
    with pytest.raises(ValueError):
        TrialCounters(observed=-1)
    assert check_counter_invariants(TrialCounters(3, 1)) == []
    # Build an out-of-contract state without the constructor guard to prove
    # the checker (not only the constructor) flags it.
    corrupt = TrialCounters.__new__(TrialCounters)
    object.__setattr__(corrupt, "observed", 1)
    object.__setattr__(corrupt, "published", 3)
    assert check_counter_invariants(corrupt) == ["published_exceeds_observed"]
