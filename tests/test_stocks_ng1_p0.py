"""STOCKS-NG1 P0 tests: fail-closed adapter + 10b5-1 flag detector.

Two law-groups (dispatch packet):

  1. plane adapter fail-closed when a pinned CADS object's digest
     changes by one byte (tmp copy of a store -- the REAL store and the
     inherited substrate pin are never touched);
  2. flag-detector fixtures hand-computed on three XML samples written
     under /tmp: one WITH the declared-plan flag, one WITHOUT, one
     malformed (must fail closed).

No network, no substrate dependency: everything runs on tmp fixtures.
"""

from __future__ import annotations

import os
import sys
import tempfile

import pytest

_REPO = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir))
sys.path.insert(0, _REPO)

from research.assets.stocks_ng1.plane_adapter import (  # noqa: E402
    ConsumptionRefused, FLAG_TAG_10B5_1, MalformedForm4Error,
    StocksNG1Plane, detect_10b5_1_flag,
)
from research.platform_v3.authority import AuthorityRegistry  # noqa: E402
from research.platform_v3.cads import CADS, CADSIntegrityError  # noqa: E402

PAYLOAD = b'{"hello": "form4-stream"}'


# --------------------------------------------------------------------- #
# fixture builders
# --------------------------------------------------------------------- #
def _build_granted_store(tmpdir: str) -> tuple[str, str]:
    """tmp CADS store + authority journal with ONE granted series
    (S1:form4-stream) pinning one bytes object."""
    store_root = os.path.join(tmpdir, "cads_store")
    store = CADS(store_root)
    address = store.register(PAYLOAD)
    store.pin(address, {"series": "S1:form4-stream"})

    journal = os.path.join(tmpdir, "authority_journal.jsonl")
    reg = AuthorityRegistry(journal)
    reg.register("S1:form4-stream", source="sec-edgar", channel="edgar")
    reg.transition("S1:form4-stream", "INGESTED")
    reg.transition("S1:form4-stream", "VERIFIED")
    reg.evidence("S1:form4-stream", pit_verdict="PASS_PIT_EVIDENCED",
                 license_status="AUTHORIZED",
                 entitlement_status="AUTHORIZED",
                 canary_probe={"edgar": "PASS"}, cads_pins=[address])
    outcome = reg.adjudicate("S1:form4-stream", granted_by="test",
                             granted_at="2026-09-11T00:00:00+00:00")
    assert outcome == "GRANTED"
    return store_root, journal


def _object_path(store_root: str, address: str) -> str:
    return os.path.join(store_root, "objects", address[:2], address)


# --------------------------------------------------------------------- #
# 1. fail-closed on a one-byte digest change
# --------------------------------------------------------------------- #
def test_adapter_fail_closed_on_one_byte_flip() -> None:
    tmp = tempfile.mkdtemp(prefix="ng1_p0_test_")
    store_root, journal = _build_granted_store(tmp)
    plane = StocksNG1Plane(store_root=store_root, substrate_root=tmp,
                           authority_journal=journal)

    # baseline: consumption succeeds through the plane (verify-on-read)
    out = plane.consume_via_plane("S1:form4-stream")
    assert out["bytes"] == len(PAYLOAD)
    address = out["resolved_address"]
    assert address == plane.pins_for_series("S1:form4-stream")[0]["address"]

    # tamper exactly ONE byte of the pinned object
    opath = _object_path(store_root, address)
    with open(opath, "rb") as fh:
        data = fh.read()
    tampered = bytearray(data)
    tampered[0] ^= 0x01
    assert len(tampered) == len(data) and tampered != data
    with open(opath, "wb") as fh:
        fh.write(bytes(tampered))

    with pytest.raises(CADSIntegrityError):
        plane.consume_via_plane("S1:form4-stream")   # fail-closed


def test_adapter_refuses_ungranted_series() -> None:
    tmp = tempfile.mkdtemp(prefix="ng1_p0_test_")
    store_root, journal = _build_granted_store(tmp)
    plane = StocksNG1Plane(store_root=store_root, substrate_root=tmp,
                           authority_journal=journal)
    with pytest.raises(ConsumptionRefused):
        plane.consume_via_plane("S1:form4-xml-substrate")  # not granted
    with pytest.raises(ConsumptionRefused):
        plane.consume_via_plane("X:unplanned-series")      # outside S1-S4


# --------------------------------------------------------------------- #
# 2. flag-detector fixtures (hand-computed, under /tmp)
# --------------------------------------------------------------------- #
FLAGGED_XML = """<?xml version="1.0"?>
<ownershipDocument>
    <documentType>4</documentType>
    <periodOfReport>2023-06-15</periodOfReport>
    <issuer><issuerCik>0000001800</issuerCik></issuer>
    <reportingOwner>
        <reportingOwnerId><rptOwnerCik>0001204554</rptOwnerCik></reportingOwnerId>
    </reportingOwner>
    <aff10b5One>1</aff10b5One>
    <derivativeTable></derivativeTable>
</ownershipDocument>
"""

NOT_FLAGGED_XML = """<?xml version="1.0"?>
<ownershipDocument>
    <documentType>4</documentType>
    <periodOfReport>2023-06-15</periodOfReport>
    <issuer><issuerCik>0000001800</issuerCik></issuer>
    <reportingOwner>
        <reportingOwnerId><rptOwnerCik>0001204554</rptOwnerCik></reportingOwnerId>
    </reportingOwner>
    <aff10b5One>0</aff10b5One>
    <derivativeTable></derivativeTable>
</ownershipDocument>
"""

MALFORMED_XML = """<?xml version="1.0"?>
<ownershipDocument>
    <documentType>4</documentType>
    <periodOfReport>2023-06-15</periodOfReport>
    <aff10b5One>1</aff10b5One>
<!-- unclosed root element: malformed on purpose -->
"""


def test_flag_detector_hand_computed_fixtures() -> None:
    tmp = tempfile.mkdtemp(prefix="ng1_p0_fixture_")

    # fixture 1 (WITH plan flag): hand-computed expectation
    p1 = os.path.join(tmp, "with_plan_flag.xml")
    with open(p1, "w") as fh:
        fh.write(FLAGGED_XML)
    r1 = detect_10b5_1_flag(open(p1, "rb").read())
    assert r1 == {"declared": True, "value": "1", "tag": FLAG_TAG_10B5_1,
                  "occurrences": 1}

    # fixture 2 (WITHOUT plan flag): value "0" -> not declared
    p2 = os.path.join(tmp, "no_plan_flag.xml")
    with open(p2, "w") as fh:
        fh.write(NOT_FLAGGED_XML)
    r2 = detect_10b5_1_flag(open(p2, "rb").read())
    assert r2 == {"declared": False, "value": "0", "tag": FLAG_TAG_10B5_1,
                  "occurrences": 1}

    # fixture 3 (malformed): fail closed -- raises, never guesses, and
    # the doc is never counted as flagged
    p3 = os.path.join(tmp, "malformed.xml")
    with open(p3, "w") as fh:
        fh.write(MALFORMED_XML)
    with pytest.raises(MalformedForm4Error):
        detect_10b5_1_flag(open(p3, "rb").read())


def test_flag_detector_absent_tag_is_none() -> None:
    body = ("<?xml version=\"1.0\"?>\n"
            "<ownershipDocument><documentType>4</documentType>"
            "<periodOfReport>2019-07-24</periodOfReport>"
            "</ownershipDocument>\n")
    r = detect_10b5_1_flag(body.encode())
    assert r == {"declared": None, "value": None, "tag": FLAG_TAG_10B5_1,
                 "occurrences": 0}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
