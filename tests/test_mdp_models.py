"""Unit + golden tests for mdp models (freeze exact_arithmetic_goldens).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_models.py -q   (from the lane worktree root)
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import models, reason_codes  # noqa: E402
from market_data_plane.models import (  # noqa: E402
    ENVELOPE_FIELDS,
    MANIFEST_FIELDS,
    MarketDataPlaneError,
)

PYTHON = sys.executable
RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"


def base_trade(**overrides):
    fields = dict(
        schema_version=models.SCHEMA_VERSION,
        raw_id="raw-1",
        source_id="src-1",
        venue="BINANCE",
        instrument_id="BTCUSDT",
        asset_class="crypto",
        event_type="TRADE",
        exchange_time_utc_ns=1_700_000_000_000_000_000,
        receive_time_utc_ns=1_700_000_000_000_000_001,
        available_time_utc_ns=1_700_000_000_000_000_002,
        sequence_number=7,
        price="60000.00000001",
        quantity="0.00000010",
        side="buy",
        currency=None,
        bid_price=None,
        ask_price=None,
        bid_size=None,
        ask_size=None,
        price_precision=8,
        size_precision=8,
        raw_sha256=hashlib.sha256(b"raw").hexdigest(),
        manifest_sha256=hashlib.sha256(b"manifest").hexdigest(),
        normalizer_version="mdp-normalizer@1",
    )
    fields.update(overrides)
    return fields


def base_quote(**overrides):
    fields = base_trade()
    fields.update(dict(
        event_type="QUOTE",
        price=None,
        quantity=None,
        side=None,
        bid_price="100.0050",
        ask_price="100.0060",
        bid_size="10.0",
        ask_size="12.5",
        price_precision=4,
        size_precision=1,
    ))
    fields.update(overrides)
    return fields


# --- envelope / frozen constants -------------------------------------------


def test_envelope_is_exactly_the_frozen_27_fields():
    assert len(ENVELOPE_FIELDS) == 27
    assert ENVELOPE_FIELDS[0] == "schema_version"
    assert ENVELOPE_FIELDS[-1] == "normalizer_version"
    assert list(models.EVENT_TYPE_MATRIX) == ["TRADE", "QUOTE"]


def test_manifest_fields_match_frozen_list():
    assert len(MANIFEST_FIELDS) == 33
    assert MANIFEST_FIELDS[0] == "schema_version"
    assert MANIFEST_FIELDS[-1] == "created_utc"


def test_reason_codes_registry_is_frozen():
    assert len(reason_codes.CODES) == 21
    assert len(reason_codes.REJECT_TO_QUARANTINE) == 15
    assert len(reason_codes.FLAG_SUSPECT) == 5
    assert reason_codes.BOOKKEEPING == ("DUPLICATE_EVENT",)
    assert reason_codes.is_rejection("CROSSED_QUOTE")
    assert not reason_codes.is_rejection("STALE_QUOTE")
    assert reason_codes.is_suspect("SEQUENCE_GAP")
    assert not reason_codes.is_suspect("DUPLICATE_EVENT")
    assert reason_codes.final_status_for(["DUPLICATE_EVENT"]) == "VALID"
    assert reason_codes.final_status_for(["STALE_QUOTE"]) == "SUSPECT"
    assert reason_codes.final_status_for(["STALE_QUOTE", "NEGATIVE_PRICE"]) == "INVALID"


# --- construction basics ----------------------------------------------------


def test_build_event_produces_canonical_27_field_dict():
    event = models.build_event(base_trade())
    assert set(event) == set(ENVELOPE_FIELDS)
    assert event["quality_status"] == "QUARANTINED"  # never VALID by default
    assert event["reason_codes"] == []
    assert event["price"] == "60000.00000001"


def test_from_dict_to_dict_round_trip():
    event = models.build_event(base_trade())
    assert models.from_dict(models.to_dict(event)) == event


def test_validate_rejects_extra_and_missing_envelope_fields():
    event = models.build_event(base_trade())
    with_extra = dict(event)
    with_extra["oops"] = 1
    with pytest.raises(MarketDataPlaneError) as exc:
        models.validate_event(with_extra)
    assert exc.value.reason_code == "MALFORMED_SHAPE"

    missing = dict(event)
    missing.pop("venue")
    with pytest.raises(MarketDataPlaneError) as exc:
        models.validate_event(missing)
    assert exc.value.reason_code == "MALFORMED_SHAPE"


def test_depth_types_are_reserved_in_v1():
    for event_type in ("DEPTH_SNAPSHOT", "DEPTH_DELTA", "SWAP_PRINT"):
        with pytest.raises(MarketDataPlaneError) as exc:
            models.build_event(base_trade(event_type=event_type))
        assert exc.value.reason_code == "UNKNOWN_EVENT_TYPE"


def test_event_type_matrix_required_forbidden_optional():
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(price=None))
    assert exc.value.reason_code == "MISSING_REQUIRED_FIELD"

    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_quote(side="buy"))  # QUOTE forbids side
    assert exc.value.reason_code == "MALFORMED_SHAPE"

    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(bid_price="1.0"))  # TRADE forbids bid
    assert exc.value.reason_code == "MALFORMED_SHAPE"

    event = models.build_event(base_trade(side=None))  # optional null is fine
    assert event["side"] is None


# --- timestamp field_rules --------------------------------------------------


def test_timestamp_type_rules():
    event = models.build_event(base_trade())  # ints pass
    assert event["exchange_time_utc_ns"] == 1_700_000_000_000_000_000
    for bad in (1.5, "1700000000000000000", True):
        with pytest.raises(MarketDataPlaneError) as exc:
            models.build_event(base_trade(exchange_time_utc_ns=bad))
        assert exc.value.reason_code == "MALFORMED_SHAPE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(
            exchange_time_utc_ns=datetime(2026, 1, 1)))  # naive
    assert exc.value.reason_code == "TIMEZONE_NAIVE_REJECTED"


def test_aware_datetime_converts_exactly_to_ns():
    import calendar
    aware = datetime(2026, 9, 9, 12, 30, 56, 789012, tzinfo=timezone.utc)
    expected = calendar.timegm(aware.utctimetuple()) * 10**9 \
        + aware.microsecond * 1000
    event = models.build_event(base_trade(
        exchange_time_utc_ns=aware,
        receive_time_utc_ns=expected + 1,
        available_time_utc_ns=expected + 2))
    assert event["exchange_time_utc_ns"] == expected


def test_impossible_time_order_rejected_at_construction():
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(
            exchange_time_utc_ns=1_700_000_000_000_000_002,
            receive_time_utc_ns=1_700_000_000_000_000_001))
    assert exc.value.reason_code == "IMPOSSIBLE_TIME_ORDER"
    # equality is allowed at construction (the three times are not aliases)
    equal = 1_700_000_000_000_000_000
    event = models.build_event(base_trade(exchange_time_utc_ns=equal,
                                          receive_time_utc_ns=equal,
                                          available_time_utc_ns=equal))
    assert event["available_time_utc_ns"] == equal


# --- decimal field_rules (goldens 1, 2, 5) ----------------------------------


def test_golden_price_0_1_stored_as_decimal_string_never_binary_artifact():
    event = models.build_event(base_trade(price="0.1"))
    assert event["price"] == "0.1"
    event_float = models.build_event(base_trade(price=0.1))
    assert event_float["price"] == "0.1"
    assert "0.1000000000000000055511151231257827" not in models.canonical_json(
        event_float)


def test_golden_1e_8_price_and_1e9_size_round_trip_as_strings():
    event = models.build_event(base_trade(
        price="0.00000001", quantity="1000000000",
        price_precision=8, size_precision=0))
    assert event["price"] == "0.00000001"
    assert event["quantity"] == "1000000000"
    again = models.from_dict(json.loads(models.canonical_json(event)))
    assert again == event
    # float inputs of the same magnitudes are converted via Decimal(repr(x))
    event_float = models.build_event(base_trade(
        price=1e-8, quantity=1e9, price_precision=8, size_precision=0))
    assert event_float["price"] == "0.00000001"
    assert event_float["quantity"] == "1000000000"


def test_golden_float_0_1_passes_float_one_third_fails_precision_2():
    event = models.build_event(base_trade(price=0.1, price_precision=2,
                                          quantity="3.00"))
    assert event["price"] == "0.1"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(price=1 / 3, price_precision=2))
    assert exc.value.reason_code == "PRECISION_LOSS"


def test_non_finite_and_negative_values_rejected():
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(price=float("nan")))
    assert exc.value.reason_code == "NON_FINITE_PRICE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(price=float("inf")))
    assert exc.value.reason_code == "NON_FINITE_PRICE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(price="-1"))
    assert exc.value.reason_code == "NEGATIVE_PRICE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(quantity="-1"))
    assert exc.value.reason_code == "NEGATIVE_SIZE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_quote(bid_price="NaN"))
    assert exc.value.reason_code == "MALFORMED_SHAPE"  # exponent/non-fixed form


# --- event identity (frozen 0x1F canonical identity string) -----------------


def test_event_id_matches_independent_sha256_computation():
    fields = base_trade()
    identity = "\x1f".join([
        models.SCHEMA_VERSION, fields["source_id"], fields["venue"],
        fields["instrument_id"], fields["event_type"],
        str(fields["exchange_time_utc_ns"]), str(fields["receive_time_utc_ns"]),
        str(fields["available_time_utc_ns"]), str(fields["sequence_number"]),
        fields["raw_sha256"],
    ])
    expected = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    event = models.build_event(fields)
    assert event["event_id"] == expected


def test_supplied_event_id_disagreement_is_hash_disagreement():
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(event_id="0" * 64))
    assert exc.value.reason_code == "HASH_DISAGREEMENT"


# --- quality enum + reason codes -------------------------------------------


def test_quality_status_enum_and_reason_code_canonicalisation():
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(quality_status="GREAT"))
    assert exc.value.reason_code == "MALFORMED_SHAPE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_event(base_trade(reason_codes=["NOT_IN_REGISTRY"]))
    assert exc.value.reason_code == "MALFORMED_SHAPE"
    event = models.build_event(base_trade(
        reason_codes=["STALE_QUOTE", "STALE_QUOTE", "MALFORMED_SHAPE"]))
    # canonicalised to sorted unique
    assert event["reason_codes"] == ["MALFORMED_SHAPE", "STALE_QUOTE"]


def test_set_quality_keeps_identity_and_validates():
    event = models.build_event(base_trade())
    updated = models.set_quality(event, "SUSPECT", ["STALE_QUOTE"])
    assert updated["quality_status"] == "SUSPECT"
    assert updated["event_id"] == event["event_id"]
    with pytest.raises(MarketDataPlaneError):
        models.set_quality(event, "GREAT", [])


# --- canonical json + stream digest (golden 6 support) ----------------------


def test_canonical_json_is_sorted_compact_ascii_no_nan():
    obj = {"b": 1, "a": "x"}
    assert models.canonical_json(obj) == '{"a":"x","b":1}'
    with pytest.raises(MarketDataPlaneError):
        models.canonical_json({"a": float("nan")})


def _digest_script() -> str:
    return (
        "import hashlib, json, sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from market_data_plane import models\n"
        "def trade(i):\n"
        f"    base = json.loads({json.dumps(json.dumps(base_trade()))})\n"
        "    base['sequence_number'] = i\n"
        "    base['raw_id'] = f'raw-{i}'\n"
        "    base['exchange_time_utc_ns'] += i\n"
        "    base['receive_time_utc_ns'] += i\n"
        "    base['available_time_utc_ns'] += i\n"
        "    return models.build_event(base)\n"
        "events = [trade(i) for i in range(50)]\n"
        "print(models.stream_digest(models.sort_events_for_replay(events)))\n"
    )


def test_golden_stream_digest_byte_stable_across_processes_and_cwd():
    script = _digest_script()
    digests = set()
    env_base = dict(os.environ)
    for hashseed, cwd in (("0", str(RESEARCH_DIR.parent)),
                          ("12345", tempfile.gettempdir()),
                          ("random", str(RESEARCH_DIR.parent))):
        env = dict(env_base)
        env["PYTHONHASHSEED"] = hashseed
        env["PYTHONPATH"] = str(RESEARCH_DIR)
        proc = subprocess.run(
            [PYTHON, "-c", script, str(RESEARCH_DIR)],
            capture_output=True, text=True, env=env, cwd=cwd, timeout=120)
        assert proc.returncode == 0, proc.stderr
        digests.add(proc.stdout.strip())
    assert len(digests) == 1, f"digest not byte-stable: {digests}"


# --- raw chunk manifest -----------------------------------------------------

def base_manifest(**overrides):
    fields = dict(
        schema_version=models.MANIFEST_SCHEMA_VERSION,
        manifest_id=None,
        source_id="src-1",
        provider_id="prov-1",
        venue="BINANCE",
        instrument_id="BTCUSDT",
        asset_class="crypto",
        event_class="TRADE",
        request_identity_secrets_removed={"symbol": "BTCUSDT", "limit": "500"},
        entitlement_evidence_ref="entitlements/2026/btc-1",
        allowed_use_classification="RESEARCH_AUTHORIZED",
        retrieval_start_utc_ns=1_700_000_000_000_000_000,
        retrieval_end_utc_ns=1_700_000_060_000_000_000,
        payload_byte_length=128,
        record_count=2,
        payload_sha256=hashlib.sha256(b"payload").hexdigest(),
        media_type="application/x-ndjson",
        encoding="utf-8",
        min_exchange_time_utc_ns=1_700_000_000_000_000_000,
        max_exchange_time_utc_ns=1_700_000_000_000_000_002,
        min_receive_time_utc_ns=1_700_000_000_000_000_000,
        max_receive_time_utc_ns=1_700_000_000_000_000_002,
        min_available_time_utc_ns=1_700_000_000_000_000_000,
        max_available_time_utc_ns=1_700_000_000_000_000_002,
        parser_version="parser-1",
        normalizer_version="mdp-normalizer@1",
        prev_manifest_id=None,
        next_manifest_id=None,
        completeness_status="COMPLETE",
        gap_reasons=[],
        sequence_semantics="CONTIGUOUS",
        ordered_delivery=True,
        created_utc=1_700_000_060_000_000_000,
    )
    fields.update(overrides)
    return fields


def test_manifest_build_validate_round_trip_and_id_rule():
    manifest = models.build_manifest(base_manifest())
    assert set(manifest) == set(MANIFEST_FIELDS)
    minus_id = {k: v for k, v in manifest.items() if k != "manifest_id"}
    assert manifest["manifest_id"] == models.compute_manifest_id(minus_id)
    assert models.validate_manifest(dict(manifest)) == manifest


def test_manifest_id_mismatch_fails_closed():
    manifest = models.build_manifest(base_manifest())
    tampered = dict(manifest)
    tampered["record_count"] = 99
    with pytest.raises(MarketDataPlaneError) as exc:
        models.validate_manifest(tampered)
    assert exc.value.reason_code == "HASH_DISAGREEMENT"


def test_manifest_min_max_and_enum_rules():
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_manifest(base_manifest(min_exchange_time_utc_ns=200,
                                            max_exchange_time_utc_ns=100))
    assert exc.value.reason_code == "MANIFEST_MISMATCH"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_manifest(base_manifest(retrieval_start_utc_ns=200,
                                            retrieval_end_utc_ns=100))
    assert exc.value.reason_code == "MANIFEST_MISMATCH"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_manifest(base_manifest(completeness_status="MOSTLY"))
    assert exc.value.reason_code == "MALFORMED_SHAPE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_manifest(base_manifest(
            allowed_use_classification="SELL_TO_ANYONE"))
    assert exc.value.reason_code == "MALFORMED_SHAPE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_manifest(base_manifest(gap_reasons=["NOT_A_CODE"]))
    assert exc.value.reason_code == "MALFORMED_SHAPE"
    manifest = models.build_manifest(base_manifest(
        completeness_status="GAPS_PRESENT", gap_reasons=["SEQUENCE_GAP",
                                                         "SEQUENCE_GAP"]))
    assert manifest["gap_reasons"] == ["SEQUENCE_GAP"]  # sorted unique
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_manifest(base_manifest(ordered_delivery="yes"))
    assert exc.value.reason_code == "MALFORMED_SHAPE"
    with pytest.raises(MarketDataPlaneError) as exc:
        models.build_manifest(base_manifest(sequence_semantics="ALWAYS"))
    assert exc.value.reason_code == "MALFORMED_SHAPE"


def test_manifest_consistency_checks_against_events():
    events = [
        models.build_event(base_trade(raw_id="a", sequence_number=0)),
        models.build_event(base_trade(raw_id="b", sequence_number=1)),
    ]
    stream = models.stream_bytes(events)
    manifest = models.build_manifest(base_manifest(
        record_count=2,
        payload_byte_length=len(stream),
        payload_sha256=hashlib.sha256(stream).hexdigest(),
        min_exchange_time_utc_ns=min(e["exchange_time_utc_ns"] for e in events),
        max_exchange_time_utc_ns=max(e["exchange_time_utc_ns"] for e in events),
        min_receive_time_utc_ns=min(e["receive_time_utc_ns"] for e in events),
        max_receive_time_utc_ns=max(e["receive_time_utc_ns"] for e in events),
        min_available_time_utc_ns=min(e["available_time_utc_ns"] for e in events),
        max_available_time_utc_ns=max(e["available_time_utc_ns"] for e in events),
    ))
    models.check_manifest_consistency(manifest, events, payload_bytes=stream)

    bad_count = models.build_manifest(base_manifest(
        record_count=3,
        payload_byte_length=len(stream),
        payload_sha256=hashlib.sha256(stream).hexdigest(),
        min_exchange_time_utc_ns=min(e["exchange_time_utc_ns"] for e in events),
        max_exchange_time_utc_ns=max(e["exchange_time_utc_ns"] for e in events),
        min_receive_time_utc_ns=min(e["receive_time_utc_ns"] for e in events),
        max_receive_time_utc_ns=max(e["receive_time_utc_ns"] for e in events),
        min_available_time_utc_ns=min(e["available_time_utc_ns"] for e in events),
        max_available_time_utc_ns=max(e["available_time_utc_ns"] for e in events),
    ))
    with pytest.raises(MarketDataPlaneError) as exc:
        models.check_manifest_consistency(bad_count, events, payload_bytes=stream)
    assert exc.value.reason_code == "MANIFEST_MISMATCH"

    tampered = models.build_manifest(base_manifest(
        record_count=2,
        payload_byte_length=len(stream),
        payload_sha256=hashlib.sha256(b"other").hexdigest(),
        min_exchange_time_utc_ns=min(e["exchange_time_utc_ns"] for e in events),
        max_exchange_time_utc_ns=max(e["exchange_time_utc_ns"] for e in events),
        min_receive_time_utc_ns=min(e["receive_time_utc_ns"] for e in events),
        max_receive_time_utc_ns=max(e["receive_time_utc_ns"] for e in events),
        min_available_time_utc_ns=min(e["available_time_utc_ns"] for e in events),
        max_available_time_utc_ns=max(e["available_time_utc_ns"] for e in events),
    ))
    with pytest.raises(MarketDataPlaneError) as exc:
        models.check_manifest_consistency(tampered, events, payload_bytes=stream)
    assert exc.value.reason_code == "MANIFEST_MISMATCH"


def test_prev_next_linkage_nullable_and_hash_checked():
    manifest = models.build_manifest(base_manifest(
        prev_manifest_id="bead" + "0" * 60,
        next_manifest_id="cafe" + "0" * 60))
    assert manifest["prev_manifest_id"] == "bead" + "0" * 60
    with pytest.raises(MarketDataPlaneError):
        models.build_manifest(base_manifest(prev_manifest_id="nope"))


# --- golden 3 handled in quality tests; exact mid here ----------------------


def test_golden_exact_decimal_mid_of_0_00001_and_0_00002():
    mid = models.quote_mid("0.00001", "0.00002")
    assert mid == Decimal("0.000015")
    assert str(mid) == "0.000015"
    # the binary-float path would give 0.015000000000000001-style artefacts
    assert mid * 2 == Decimal("0.00003")


# --- import isolation (freeze import_isolation) -----------------------------


def test_import_isolation_hot_path_modules_never_import_heavy_libs():
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(RESEARCH_DIR)!r})\n"
        "from market_data_plane import models, quality, reason_codes\n"
        "import market_data_plane._pandera_spike as spike\n"
        "heavy = [m for m in ('pandas', 'pandera', 'dvc', 'nautilus_trader')\n"
        "         if m in sys.modules]\n"
        "print('HEAVY:', heavy)\n"
        "assert not heavy, heavy\n"
        "print('ISOLATION_OK')\n"
    )
    proc = subprocess.run([PYTHON, "-c", script], capture_output=True,
                          text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "ISOLATION_OK" in proc.stdout


def test_manifest_sha256_is_required_never_null_a1_ruling():
    fields = base_trade()
    for bad in (None,):
        ev = dict(fields, manifest_sha256=bad)
        with pytest.raises(models.MarketDataPlaneError):
            models.build_event(ev)
    # 64-hex required form still accepted
    assert models.build_event(dict(fields))["manifest_sha256"] == fields["manifest_sha256"]
