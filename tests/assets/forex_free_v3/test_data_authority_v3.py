"""FOREX-FREE-V3 P2 data-authority pins (offline: adopted Data Fusion code + fixtures).

Pins the V3 data-authority dispositions (research/control/forex_free_v3_run/
data_authority_v3.json) against the adopted data_fusion code:

* ECB SDMX and BIS WS_CBPOL are registered KEYLESS in the source registry and
  carry an AUTHORIZED-or-higher V3 disposition for their declared scope
  (policy rates / macro series), with availability-stamp semantics proven on
  the offline fixtures (effective != available, never invented);
* FRED/ALFRED is key-gated and fails closed (CREDENTIAL_REQUIRED) without a
  key; it stays UNAUTHORIZED for V3 (no owner key decision, no signup);
* TrueFX stays CANDIDATE_NOT_AUTHORIZED (owner license decision required);
* the authorized V1 price-series dispositions are carried unchanged, with the
  P2 156-file snapshot digest replay recorded as evidence.

No network, no keys, no raw data, no wall clock: everything runs on the
hand-written offline fixtures from tests/data_fusion/adapters/fixtures/.
"""

import json
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.data_fusion import source_registry as SR  # noqa: E402
from research.data_fusion.adapters.base import (  # noqa: E402
    AdapterError,
    RawResponse,
    RequestSpec,
    date_only_evidence,
)
from research.data_fusion.adapters.bis import BisAdapter  # noqa: E402
from research.data_fusion.adapters.ecb import EcbAdapter  # noqa: E402
from research.data_fusion.adapters.fred import FredAdapter  # noqa: E402

UTC = timezone.utc
FIXTURES = ROOT / "tests" / "data_fusion" / "adapters" / "fixtures"
AUTHORITY_V3_PATH = ROOT / "research" / "control" / "forex_free_v3_run" / "data_authority_v3.json"

AUTHORIZED_FOR_V3_RESEARCH = "AUTHORIZED_FOR_V3_RESEARCH"
UNAUTHORIZED_FOR_V3 = "UNAUTHORIZED_FOR_V3"
CANDIDATE_NOT_AUTHORIZED = "CANDIDATE_NOT_AUTHORIZED"
UNAVAILABLE_FAIL_CLOSED = "UNAVAILABLE_FAIL_CLOSED"

# V3 rank ladder: AUTHORIZED_FOR_V3_RESEARCH is the only scored-research tier;
# DOCUMENTED_CANDIDATE is the adopted discovery posture that the V3 disposition
# file may lift per series; everything below candidate is fail-closed.
V3_RANK = {
    "REJECTED_LICENSE": -2,
    "UNAVAILABLE_FAIL_CLOSED": -1,
    "CANDIDATE_NOT_AUTHORIZED": 0,
    "DOCUMENTED_CANDIDATE": 1,
    AUTHORIZED_FOR_V3_RESEARCH: 2,
    "AUTHORIZED_INTERNAL_RESEARCH": 2,
}
AUTHORIZED_RANK = V3_RANK[AUTHORIZED_FOR_V3_RESEARCH]

# Fixed retrieval instant keeps every adapter output deterministic (no wall clock).
RETRIEVED_TIME = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def response_for(request: RequestSpec, body: bytes, *, content_type: str) -> RawResponse:
    return RawResponse(
        request_id=request.request_id(),
        url=request.full_url(),
        status=200,
        reason="OK",
        headers=(("content-type", content_type),),
        body=body,
        retrieved_time_utc=RETRIEVED_TIME,
    )


def load_authority_v3() -> dict:
    with open(AUTHORITY_V3_PATH) as fh:
        return json.load(fh)


class TestMacroSeriesRegisteredKeylessAndAuthorized(unittest.TestCase):
    """ECB SDMX and BIS WS_CBPOL: keyless registry entries + V3 authorization."""

    def test_registry_entries_are_keyless_with_declared_scope(self):
        for source_id, capabilities in (
            ("ECB_SDMX", ("macro_series",)),
            ("BIS_CBPOL", ("policy_rates",)),
        ):
            spec = SR.by_id(source_id)
            self.assertFalse(spec.account_or_key_required, source_id)
            self.assertIn("macro", spec.asset_classes, source_id)
            for capability in capabilities:
                self.assertIn(capability, spec.capabilities, source_id)

    def test_adapter_classes_declare_anonymous_no_key_entitlement(self):
        self.assertEqual(EcbAdapter.entitlement_id, "anonymous-no-key")
        self.assertEqual(BisAdapter.entitlement_id, "anonymous-no-key")

    def test_v3_disposition_authorized_or_higher_for_declared_scope(self):
        authority = load_authority_v3()
        for source_id in ("ECB_SDMX", "BIS_CBPOL"):
            entry = authority["macro_series"][source_id]
            self.assertIn(entry["v3_disposition"], V3_RANK, source_id)
            self.assertGreaterEqual(
                V3_RANK[entry["v3_disposition"]], AUTHORIZED_RANK, source_id
            )
            self.assertTrue(entry["access"]["keyless"], source_id)

    def test_bis_fixture_effective_date_semantics_no_backdated_eligibility(self):
        """Offline proof of the availability-stamp semantics the authorization relies on."""
        adapter = BisAdapter()
        request = adapter.build_policy_rate_request("US.P")
        output = adapter.parse_policy_rates(
            response_for(
                request,
                fixture_bytes("bis_cbpol.json"),
                content_type="application/vnd.sdmx.data+json",
            ),
            release_evidence=date_only_evidence("BIS CBPOL capture", date(2024, 5, 1)),
        )
        self.assertEqual(len(output.records), 2)
        for record in output.records:
            # CBPOL observation dates are policy-rate effective dates
            self.assertEqual(record.effective_time_utc, record.event_time_utc)
            # effectiveness is not availability: a record is never eligible on
            # its own effective date (no backdated carry signal)
            self.assertGreater(record.available_time_utc, record.effective_time_utc)
            self.assertFalse(record.eligible_at(record.effective_time_utc))
            self.assertTrue(record.eligible_at(record.available_time_utc))

    def test_ecb_fixture_availability_is_end_of_utc_day_upper_bound(self):
        adapter = EcbAdapter()
        request = adapter.build_series_request("EXR", "D.USD.EUR.SP00.A")
        output = adapter.parse_series(
            response_for(
                request,
                fixture_bytes("ecb_sdmx_exr.json"),
                content_type="application/vnd.sdmx.data+json",
            ),
            dataflow="EXR",
            release_evidence=date_only_evidence("ECB publication calendar", date(2024, 1, 3)),
            unit="USD_PER_EUR",
        )
        self.assertEqual(len(output.records), 2)
        # fixture observation dates: 2024-01-02 and 2024-01-03
        self.assertEqual(
            [r.effective_time_utc for r in output.records],
            [datetime(2024, 1, 2, 0, 0, tzinfo=UTC), datetime(2024, 1, 3, 0, 0, tzinfo=UTC)],
        )
        for record in output.records:
            # date-only evidence may only produce the end-of-UTC-day upper bound
            self.assertEqual(record.available_time_utc, datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC))


class TestFredKeyGatedUnauthorized(unittest.TestCase):
    """FRED/ALFRED fails closed without a key and is UNAUTHORIZED for V3."""

    def test_adapter_requires_key_and_fails_closed_without_one(self):
        adapter = FredAdapter()
        for build in (adapter.build_vintagedates_request, adapter.build_alfred_observations_request):
            for blank in ("", "   "):
                with self.assertRaises(AdapterError) as ctx:
                    build("CPIAUCSL", api_key=blank)
                self.assertEqual(ctx.exception.code, "CREDENTIAL_REQUIRED")

    def test_registry_entry_is_key_gated_candidate(self):
        spec = SR.by_id("FRED_ALFRED")
        self.assertTrue(spec.account_or_key_required)
        self.assertEqual(spec.status.value, "CANDIDATE_NOT_AUTHORIZED")
        self.assertIn("analyst_consensus", spec.forbidden_inference)
        self.assertIn("exact_wire_release_timestamp", spec.forbidden_inference)

    def test_v3_disposition_unauthorized(self):
        entry = load_authority_v3()["macro_key_gated"]["FRED_ALFRED"]
        self.assertEqual(entry["v3_disposition"], UNAUTHORIZED_FOR_V3)
        self.assertTrue(entry["key_gated"])
        self.assertIn("no owner key decision exists", entry["rationale"])


class TestTruefxCandidateNotAuthorized(unittest.TestCase):
    """TrueFX stays CANDIDATE_NOT_AUTHORIZED until an owner license decision."""

    def test_registry_entry_candidate_not_authorized(self):
        spec = SR.by_id("TRUEFX")
        self.assertEqual(spec.status.value, "CANDIDATE_NOT_AUTHORIZED")
        self.assertIn("forex", spec.asset_classes)

    def test_v3_disposition_candidate_not_authorized(self):
        entry = load_authority_v3()["forex_candidates"]["TRUEFX"]
        self.assertEqual(entry["v3_disposition"], CANDIDATE_NOT_AUTHORIZED)
        self.assertTrue(entry["owner_license_decision_required"])


class TestPriceSeriesCarriedFromV1(unittest.TestCase):
    """Authorized V1 price dispositions carried unchanged, with P2 replay evidence."""

    def test_price_dispositions_unchanged(self):
        prices = load_authority_v3()["price_series"]
        self.assertEqual(prices["H1_twelve_data"]["disposition"], "RESEARCH_AUTHORIZED")
        self.assertEqual(prices["D1_twelve_data"]["disposition"], "CONTEXT_ONLY")
        self.assertEqual(prices["H4_twelve_data"]["disposition"], UNAVAILABLE_FAIL_CLOSED)
        self.assertEqual(prices["HISTORICAL_BID_ASK"]["disposition"], UNAVAILABLE_FAIL_CLOSED)
        self.assertEqual(prices["HISTORICAL_ROLLOVER_FINANCING"]["disposition"], UNAVAILABLE_FAIL_CLOSED)

    def test_snapshot_replay_evidence_recorded(self):
        evidence = load_authority_v3()["price_series"]["snapshot_replay_evidence"]
        self.assertEqual(evidence["schema"], "forex_free_v1_staged_data_manifest_v2")
        for tree in ("e-exec-1", "r-reproduce"):
            self.assertEqual(evidence["trees"][tree]["matched"], 156)
            self.assertEqual(evidence["trees"][tree]["missing"], 0)
            self.assertEqual(evidence["trees"][tree]["mismatch"], 0)

    def test_financing_disposition_policy_rate_differentials_only(self):
        financing = load_authority_v3()["financing_disposition"]
        self.assertEqual(
            financing["carry_adjacent_financing_model"],
            "POLICY_RATE_DIFFERENTIALS_ONLY",
        )
        self.assertEqual(
            financing["historical_rollover_financing"],
            UNAVAILABLE_FAIL_CLOSED,
        )
        self.assertIn("INELIGIBLE", financing["beyond_differentials_verdict"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
