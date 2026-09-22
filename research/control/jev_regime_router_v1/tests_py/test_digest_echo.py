"""A7-1 F1 regression: producer-digest echo law (amendment_1).

input_digest has a SINGLE canonicalization authority: the Python producer
(``jrv1.freezes.canonical_json`` = json.dumps sort_keys, no spaces). The
request line carries the producer-computed digest; the TS adapter echoes it
verbatim and never recomputes; Python ingest recomputes from its own state
(authoritative) and compares to the echo.

The golden vectors below are the cross-language contract: the exact canonical
strings and sha256 digests were produced by the producer authority and are
pinned as literals in BOTH suites (here and adapter/test/digest_golden.test.ts).
Values 1e-05 / 1.234e-07 / 5e-06 / 34.0 sit in the measured divergence window
(Python json.dumps vs JS JSON.stringify), which produced 10/25 (40%) digest
mismatches on real request lines at the A7-1 audit.
"""

from __future__ import annotations

import hashlib
import json

from jrv1.decisions import compute_input_digest, validate_response_line
from jrv1.features import RegimeFeatures
from jrv1.freezes import canonical_json
from jrv1.mock_adapter import MOCK_MODEL, mock_decide

from conftest import make_bars

import numpy as np

GOLDEN_VECTORS = [
    {
        "id": "G1_1e_05",
        "state": {
            "feature_vector": [1e-05, 0.02, 0.05, 0.11, 0.28, 0.004, 0.0025, 1.2, 34.0, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62],
            "prior_regime": None,
        },
        "requested_model": "mock-pin-1",
        "python_canonical_json": '{"feature_vector":[1e-05,0.02,0.05,0.11,0.28,0.004,0.0025,1.2,34.0,0.008,0.62,-0.03,0.3,0.42,0.35,0.62],"prior_regime":null}',
        "python_input_digest": "6c8c858c93301d154db1a982f8f82e8a5ac488ab1a30ebf2f53c76fbb4fda7b7",
    },
    {
        "id": "G2_1_234e_07",
        "state": {
            "feature_vector": [0.01, 1.234e-07, 0.05, 0.11, 0.28, 0.004, 0.0025, 1.2, 34.0, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62],
            "prior_regime": "UPTREND",
        },
        "requested_model": "mock-pin-1",
        "python_canonical_json": '{"feature_vector":[0.01,1.234e-07,0.05,0.11,0.28,0.004,0.0025,1.2,34.0,0.008,0.62,-0.03,0.3,0.42,0.35,0.62],"prior_regime":"UPTREND"}',
        "python_input_digest": "9442cc80180fdf6ff0fd6167537f5b17af93c0425fafbf19c162fff192c85b59",
    },
    {
        "id": "G3_5e_06_neg",
        "state": {
            "feature_vector": [0.01, 0.02, 0.05, 0.11, 0.28, 5e-06, -1.234e-07, 1.2, 34.0, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62],
            "prior_regime": None,
        },
        "requested_model": "mock-pin-1",
        "python_canonical_json": '{"feature_vector":[0.01,0.02,0.05,0.11,0.28,5e-06,-1.234e-07,1.2,34.0,0.008,0.62,-0.03,0.3,0.42,0.35,0.62],"prior_regime":null}',
        "python_input_digest": "53e07db17238e95fbf74e58b879608a14c75aa1d40b24d49864496c5aabc9974",
    },
]


def test_golden_canonical_json_producer_strings():
    """The producer's canonicalization renders the divergence window exactly."""
    for v in GOLDEN_VECTORS:
        assert canonical_json(v["state"]) == v["python_canonical_json"], v["id"]


def test_golden_input_digest_literals():
    """sha256(canonical_json(state)||model) equals the pinned producer digest.

    Protects against silent Python json.dumps behavior drift: any change in
    float formatting would change the digest and break the cross-language
    contract pinned in adapter/test/digest_golden.test.ts.
    """
    for v in GOLDEN_VECTORS:
        d = hashlib.sha256(
            (canonical_json(v["state"]) + v["requested_model"]).encode("utf-8")
        ).hexdigest()
        assert d == v["python_input_digest"], v["id"]
        assert compute_input_digest(v["state"], v["requested_model"]) == v["python_input_digest"]


def test_divergence_window_is_real():
    """Documents exactly why the adapter must not recompute (A7-1 F1)."""
    for x, py in ((1e-05, "1e-05"), (1.234e-07, "1.234e-07"), (5e-06, "5e-06"), (34.0, "34.0")):
        assert json.dumps(x) == py  # producer rendering (exponent forms kept)
        # JS JSON.stringify renders 1e-05 -> "0.00001", 1.234e-07 -> "1.234e-7",
        # 5e-06 -> "0.000005", 34.0 -> "34": different bytes, different digest.


def test_request_lines_carry_producer_digest(fz):
    """Every emitted request line carries the producer-computed input_digest."""
    close = np.linspace(100, 120, 220)
    vol = np.linspace(1.0, 2.0, 220)  # non-constant volume so vol_z is finite
    bars = make_bars(close, close * 1.002, close * 0.998, close, vol)
    feats = RegimeFeatures(bars)
    from jrv1.decisions import CacheProvider, DecisionStore, sequential_timeline

    sink: list = []
    sequential_timeline(
        "btcusdt", fz, bars, feats, CacheProvider(DecisionStore()),
        requested_model="m1", strict=False, request_sink=sink,
    )
    assert sink
    for line in sink:
        assert line["schema"] == "jrv1_decision_io@1"
        assert set(line) == {"schema", "state_id", "state", "requested_model", "input_digest"}
        assert line["input_digest"] == compute_input_digest(line["state"], line["requested_model"])
        assert len(line["input_digest"]) == 64


def test_ingest_recompute_is_authoritative_over_echo(fz):
    """Ingest compares the echoed digest to the local recompute; any mismatch
    (e.g. a tampered or wrongly-formatted echo) fail-closes to SCHEMA_ERROR."""
    payload = {"feature_vector": GOLDEN_VECTORS[0]["state"]["feature_vector"], "prior_regime": None}
    expected = compute_input_digest(payload, MOCK_MODEL)
    line = mock_decide("a" * 16, payload)
    assert line["input_digest"] == expected
    ok, violation = validate_response_line(line, "a" * 16, expected)
    assert violation is None and ok["status"] == "OK"
    # echoed digest differs from the authoritative recompute -> incident class
    line["input_digest"] = "f" * 64
    bad, violation = validate_response_line(line, "a" * 16, expected)
    assert violation == "input_digest_mismatch" and bad["status"] == "SCHEMA_ERROR"
