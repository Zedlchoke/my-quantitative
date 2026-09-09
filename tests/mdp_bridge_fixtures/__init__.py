"""Provider-neutral SYNTHETIC fixtures for the MDP-V1 nautilus bridge (A8).

Freeze authority: research/control/market_data_plane_v1_run/architecture_freeze.json
(sha256 7f7403e67bfb9707b547b6762cc0a3c87f2c96f701b3f1ec3ad2197478736c02),
section "nautilus_bridge_contract.fixtures".

AUTHORITY STATEMENT (frozen): these fixtures prove code semantics only and
confer ZERO data authority — no event here originates from, or may be treated
as evidence about, any real provider, venue or instrument.  All bytes are
deterministic functions of small integer seeds committed in these modules.

Every module exposes:

* ``events()`` — canonical ``mdp.market_event@1`` dicts (exactly the frozen
  27 envelope fields), constructed+validated through
  ``market_data_plane.models.build_event`` and quality-labelled through
  ``models.set_quality`` so they are contract-legal by construction;
* ``instrument_metadata()`` — id/precisions suitable for building the
  matching nautilus_trader 1.230.0 test instrument (see docs/MDP_BRIDGE_NOTES.md);
* ``invalid_event()`` / ``quarantined_variant(event, codes)`` helpers to
  derive quality-gate test cases without ever making the streaming fixture
  set itself unconvertible.
"""

from __future__ import annotations

import hashlib

from market_data_plane import models

__all__ = [
    "FIXTURE_NORMALIZER_VERSION",
    "invalid_variant",
    "make_event",
    "quarantined_variant",
    "synthetic_manifest_sha256",
    "synthetic_raw_sha256",
]

#: Fixtures are synthetic; the normalizer tag must never imitate a real one.
FIXTURE_NORMALIZER_VERSION = "mdp-bridge-fixtures@1"


def synthetic_raw_sha256(scope: str, index: int) -> str:
    """Deterministic sha256 standing in for a raw provider record hash."""
    payload = f"mdp-bridge-fixture|raw|{scope}|{index}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def synthetic_manifest_sha256(scope: str) -> str:
    """Deterministic 64-hex standing in for the upstream manifest reference.

    Only the hex form is contractual here (models validates it as 64-hex);
    the value references no real manifest.
    """
    payload = f"mdp-bridge-fixture|manifest|{scope}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_event(
    *,
    event_type: str,
    source_id: str,
    venue: str,
    instrument_id: str,
    exchange_ns: int,
    receive_ns: int,
    available_ns: int,
    sequence_number: int,
    price_precision: int,
    size_precision: int,
    raw_id: str,
    raw_sha256: str,
    manifest_sha256: str,
    currency: str | None = None,
    **decimals,
) -> dict:
    """Build + validate one canonical event; raises on any contract breach."""
    fields = dict(
        raw_id=raw_id,
        source_id=source_id,
        venue=venue,
        instrument_id=instrument_id,
        event_type=event_type,
        exchange_time_utc_ns=exchange_ns,
        receive_time_utc_ns=receive_ns,
        available_time_utc_ns=available_ns,
        sequence_number=sequence_number,
        currency=currency,
        price_precision=price_precision,
        size_precision=size_precision,
        raw_sha256=raw_sha256,
        manifest_sha256=manifest_sha256,
        normalizer_version=FIXTURE_NORMALIZER_VERSION,
    )
    fields.update(decimals)
    return models.build_event(fields)


def invalid_variant(event: dict, reason_codes) -> dict:
    """Derive an INVALID-labelled copy of a fixture event (fail-gate test input)."""
    return models.set_quality(event, "INVALID", list(reason_codes))


def quarantined_variant(event: dict, reason_codes) -> dict:
    """Derive a QUARANTINED-labelled copy of a fixture event."""
    return models.set_quality(event, "QUARANTINED", list(reason_codes))
