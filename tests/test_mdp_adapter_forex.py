"""Tests for the forex OHLCV -> mdp.market_bar@2 adapter (lane A6, MDP-V2).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_adapter_forex.py -q   (from the lane worktree root)

Hermetic synthetic fixtures ONLY (no network): all provider-local times are
Europe/London wall times with hand-computed integer UTC-ns expectations,
independent of zoneinfo at test time.

DST facts used (Europe/London):
* spring forward: 2026-03-29 01:00 UTC; local 01:00-01:59 does NOT exist
  (imaginary); local 02:00 is BST (+01:00);
* fall back: 2026-10-25 01:00 UTC; local 01:00-01:59 occurs TWICE
  (ambiguous: BST then GMT); local 02:00 is GMT (+00:00).

Hand-computed UTC opens (ns):
* 2026-03-28T23:00 local (GMT) -> 1_774_738_800_000_000_000 (Sat 23:00Z)
* 2026-03-29T00:00 local (GMT) -> 1_774_742_400_000_000_000 (Sun 00:00Z)
* 2026-03-29T02:00 local (BST) -> 1_774_746_000_000_000_000 (Sun 01:00Z)
* 2026-10-24T23:00 local (BST) -> 1_792_879_200_000_000_000 (Sat 22:00Z)
* 2026-10-25T00:00 local (BST) -> 1_792_882_800_000_000_000 (Sun 00:00Z)
* 2026-10-25T02:00 local (GMT) -> 1_792_893_600_000_000_000 (Sun 02:00Z)

NOTE on the default frozen weekly closure (Fri 21:00Z -> Sun 21:00Z): DST
transitions in Europe/London land INSIDE that closure (Sunday 01:00 UTC), so
the DST-artifact coverage tests use the context session-rule override
(explicitly allowed by the frozen interface) to exercise the artifacts
inside an OPEN session; the default-rule tests use Friday-evening /
Sunday-evening open-session slots.
"""

from __future__ import annotations

import copy
import hashlib
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import bars, models  # noqa: E402
from market_data_plane.adapters.forex import adapter as fx  # noqa: E402
from market_data_plane.adapters.forex import context as fxc  # noqa: E402
from market_data_plane.adapters.forex import coverage as fxcov  # noqa: E402
from market_data_plane.adapters.forex import schedule as fxsch  # noqa: E402

HOUR_NS = 3_600_000_000_000
MANIFEST_SHA = hashlib.sha256(b"upstream-retrieval-manifest").hexdigest()

# hand-computed UTC ns (see module docstring)
SPR_SAT23_NS = 1_774_738_800_000_000_000   # local 2026-03-28T23:00 (GMT)
SPR_SUN00_NS = 1_774_742_400_000_000_000   # local 2026-03-29T00:00 (GMT)
SPR_SUN01_NS = 1_774_746_000_000_000_000   # local 2026-03-29T02:00 (BST)
FALL_SAT22_NS = 1_792_879_200_000_000_000  # local 2026-10-24T23:00 (BST)
FALL_SUN00_NS = 1_792_882_800_000_000_000  # local 2026-10-25T00:00 (BST)
FALL_SUN02_NS = 1_792_893_600_000_000_000  # local 2026-10-25T02:00 (GMT)

FRI18_NS = 1_774_634_400_000_000_000  # 2026-03-27T18:00Z (open session)
FRI19_NS = 1_774_638_000_000_000_000
FRI20_NS = 1_774_641_600_000_000_000
FRI21_NS = 1_774_645_200_000_000_000  # first closed slot (Fri 21:00Z)
SUN21_NS = 1_774_818_000_000_000_000  # 2026-03-29T21:00Z (open session)
SUN22_NS = 1_774_821_600_000_000_000

NEVER_CLOSED_RULE = lambda open_ns: False  # noqa: E731  (session-rule override)


def make_context(**overrides):
    fields = dict(
        venue="SYNTH_FX_VENUE",
        provider_id="SYNTH_FX_PROVIDER",
        source_id="SYNTH_FX_SRC",
        provider_timezone="Europe/London",
        pair_table=fxc.EURUSD_PAIR_TABLE,
        manifest_sha256=MANIFEST_SHA,
    )
    fields.update(overrides)
    return fxc.AdapterContext(**fields)


def record(ts, symbol="EUR_USD", **overrides):
    rec = {
        "ts": ts, "tz": "Europe/London", "symbol": symbol,
        "open": "1.08120", "high": "1.08150", "low": "1.08100",
        "close": "1.08140", "volume": "1000.5",
    }
    rec.update(overrides)
    return rec


# --- happy path: hand-computed UTC ns across a DST boundary ---------------------


def test_spring_forward_happy_path_hand_computed_utc_ns():
    context = make_context()
    records = [
        record("2026-03-28T23:00:00"),  # GMT -> Sat 23:00Z
        record("2026-03-29T00:00:00"),  # GMT -> Sun 00:00Z
        record("2026-03-29T02:00:00"),  # BST -> Sun 01:00Z (local hour skipped)
    ]
    result = fx.normalize_stream(records, context)
    assert result.quarantined_count == 0
    assert [b["open_time_utc_ns"] for b in result.bars] == [
        SPR_SAT23_NS, SPR_SUN00_NS, SPR_SUN01_NS]
    for bar in result.bars:
        assert bar["close_time_utc_ns"] == bar["open_time_utc_ns"] + HOUR_NS - 1
        assert bar["available_time_utc_ns"] == bar["close_time_utc_ns"]  # default lag 0
        assert bar["instrument_id"] == "EUR/USD"
        assert bar["asset_class"] == fx.FOREX_ASSET_CLASS == "forex_spot"
        assert bar["bar_type"] == "1h-OHLC"
        assert bar["interval_ns"] == HOUR_NS
    # UTC clock is contiguous across the vanishing local hour (DST handled)
    assert SPR_SUN01_NS - SPR_SUN00_NS == HOUR_NS
    # weekend-closure slots stay SUSPECT evidence, never deleted; the forex
    # volume-class fields the provider does not supply stay null NOT_EVALUABLE
    assert all(b["quality_status"] == "SUSPECT" for b in result.bars)
    assert all(b["completeness_status"] == "NOT_EVALUABLE" for b in result.bars)
    assert all(set(b["reason_codes"]) ==
               {"BAR_OUTSIDE_CALENDAR", "BAR_VOLUME_NOT_EVALUABLE"}
               for b in result.bars)


def test_fall_back_happy_path_hand_computed_utc_ns():
    context = make_context()
    records = [
        record("2026-10-24T23:00:00"),  # BST -> Sat 22:00Z
        record("2026-10-25T00:00:00"),  # BST -> Sun 00:00Z
        record("2026-10-25T02:00:00"),  # GMT -> Sun 02:00Z
    ]
    result = fx.normalize_stream(records, context)
    assert result.quarantined_count == 0
    assert [b["open_time_utc_ns"] for b in result.bars] == [
        FALL_SAT22_NS, FALL_SUN00_NS, FALL_SUN02_NS]


# --- DST: ambiguous / imaginary local times rejected fail-closed -----------------


def test_ambiguous_local_time_rejected_fail_closed():
    context = make_context()
    with pytest.raises(bars.BarError) as excinfo:
        fx.normalize_bar(record("2026-10-25T01:30:00"), context)
    assert excinfo.value.reason_code == "FOREX_AMBIGUOUS_LOCAL_TIME"
    result = fx.normalize_stream(
        [record("2026-10-24T23:00:00"), record("2026-10-25T01:30:00"),
         record("2026-10-25T02:00:00")], context)
    assert result.accepted_count == 2 and result.quarantined_count == 1
    entry = result.quarantined[0]
    assert entry["reason_code"] == "FOREX_AMBIGUOUS_LOCAL_TIME"
    assert entry["raw_record"]["ts"] == "2026-10-25T01:30:00"


def test_imaginary_local_time_rejected_fail_closed():
    context = make_context()
    with pytest.raises(bars.BarError) as excinfo:
        fx.normalize_bar(record("2026-03-29T01:30:00"), context)
    assert excinfo.value.reason_code == "FOREX_IMAGINARY_LOCAL_TIME"
    # an offset-bearing ts breaks the local-wall-time contract outright
    with pytest.raises(bars.BarError, match="MALFORMED_SHAPE"):
        fx.normalize_bar(record("2026-10-25T01:30:00+01:00"), context)
    # a record tz that disagrees with the context clock is refused
    with pytest.raises(bars.BarError) as excinfo:
        fx.normalize_bar(record("2026-03-30T00:00:00", tz="America/New_York"),
                         context)
    assert excinfo.value.reason_code == "FOREX_PROVIDER_TZ_MISMATCH"


# --- session / weekend gap classification ----------------------------------------


def _weekend_records():
    return [
        record("2026-03-27T18:00:00"),  # Fri 18:00Z open session
        record("2026-03-27T19:00:00"),
        record("2026-03-27T20:00:00"),
        record("2026-03-29T22:00:00"),  # BST -> Sun 21:00Z open session
        record("2026-03-29T23:00:00"),  # BST -> Sun 22:00Z open session
    ]


def test_weekend_closure_gaps_expected_interior_hole_unexplained():
    context = make_context()
    result = fx.normalize_stream(_weekend_records(), context)
    assert result.accepted_count == 5
    # raw bar_stream gap accounting counts every missing slot as a sequence gap
    assert result.completeness_status == "GAPS_PRESENT"
    assert result.gap_reasons == ("SEQUENCE_GAP",)

    report = fxcov.check_coverage(result, context)
    assert report.completeness_status == "COMPLETE"  # closure gaps are the calendar
    assert report.expected_slot_count == 53
    assert report.observed_slot_count == 5
    assert report.missing_slot_count == 48
    assert report.expected_closed_market_count == 48
    assert report.unexplained_count == 0
    assert report.dst_shift_artifact_count == 0
    assert report.coverage_reasons == ("EXPECTED_CLOSED_MARKET",)
    closed_opens = sorted(g.open_time_utc_ns for g in report.gaps
                          if g.classification == "EXPECTED_CLOSED_MARKET")
    assert closed_opens[0] == FRI21_NS and closed_opens[-1] == SUN21_NS - HOUR_NS

    # interior hole: drop a MIDDLE open-session bar (Fri 19:00Z) -> UNEXPLAINED
    # (dropping the last bar would only shrink the coverage window)
    holed = fx.normalize_stream(
        [r for i, r in enumerate(_weekend_records()) if i != 1], context)
    hole_report = fxcov.check_coverage(holed, context)
    assert hole_report.completeness_status == "GAPS_PRESENT"
    assert hole_report.unexplained_count == 1
    assert hole_report.expected_closed_market_count == 48
    unexplained = [g for g in hole_report.gaps if g.classification == "UNEXPLAINED"]
    assert [g.open_time_utc_ns for g in unexplained] == [FRI19_NS]


def test_dst_shift_artifacts_classified_never_silent():
    # vanishing local hour (spring forward), session override -> open session
    context = make_context(session_rule=NEVER_CLOSED_RULE)
    vanished = fx.normalize_stream(
        [record("2026-03-28T23:00:00"), record("2026-03-29T00:00:00"),
         record("2026-03-29T01:30:00"),          # imaginary -> quarantined
         record("2026-03-29T03:00:00")], context)  # BST -> Sun 02:00Z (post-hole)
    assert vanished.quarantined[0]["reason_code"] == "FOREX_IMAGINARY_LOCAL_TIME"
    assert vanished.accepted_count == 3
    report = fxcov.check_coverage(vanished, context)
    assert report.dst_shift_artifact_count == 1
    assert report.unexplained_count == 0
    assert report.completeness_status == "GAPS_PRESENT"  # classified, never accepted
    artifacts = [g for g in report.gaps if g.classification == "DST_SHIFT_ARTIFACT"]
    assert [g.open_time_utc_ns for g in artifacts] == [SPR_SUN01_NS]

    # local hour appearing twice (fall back): both ambiguous copies quarantined
    doubled = fx.normalize_stream(
        [record("2026-10-24T23:00:00"), record("2026-10-25T00:00:00"),
         record("2026-10-25T01:30:00"), record("2026-10-25T01:30:00"),
         record("2026-10-25T02:00:00")], context)
    assert doubled.quarantined_count == 2
    assert {e["reason_code"] for e in doubled.quarantined} == \
        {"FOREX_AMBIGUOUS_LOCAL_TIME"}
    report2 = fxcov.check_coverage(doubled, context)
    assert report2.dst_shift_artifact_count == 2  # Sun 00:00Z + Sun 01:00Z
    assert report2.unexplained_count == 0
    artifacts2 = sorted(g.open_time_utc_ns for g in report2.gaps
                        if g.classification == "DST_SHIFT_ARTIFACT")
    assert artifacts2 == [1_792_886_400_000_000_000, 1_792_890_000_000_000_000]


def test_session_rule_override_changes_expected_classification():
    context = make_context(session_rule=NEVER_CLOSED_RULE)
    result = fx.normalize_stream(_weekend_records(), context)
    report = fxcov.check_coverage(result, context)
    assert report.expected_closed_market_count == 0
    assert report.unexplained_count == 48  # with no closure rule the holes are real
    assert report.completeness_status == "GAPS_PRESENT"


# --- macro boundary ---------------------------------------------------------------


def test_macro_date_only_record_is_not_a_bar():
    context = make_context()
    macro = {"date": "2026-03-04", "rate": "4.25"}
    with pytest.raises(bars.BarError) as excinfo:
        fx.normalize_bar(macro, context)
    assert excinfo.value.reason_code == "FOREX_MACRO_DATE_ONLY_ROW"
    result = fx.normalize_stream(
        [macro, record("2026-03-30T00:00:00")], context)
    assert result.quarantined_count == 1
    assert result.quarantined[0]["reason_code"] == "FOREX_MACRO_DATE_ONLY_ROW"
    assert result.accepted_count == 1
    assert all(b["instrument_id"] == "EUR/USD" for b in result.bars)


# --- pair identity: declared table, never string surgery --------------------------


def test_pair_identity_declared_mapping_eur_usd_and_eurusd():
    context = make_context()
    us = fx.normalize_bar(record("2026-03-30T00:00:00", symbol="EUR_USD"), context)
    nosym = fx.normalize_bar(record("2026-03-30T00:00:00", symbol="EURUSD"), context)
    assert us["instrument_id"] == nosym["instrument_id"] == "EUR/USD"
    identity = context.pair_identity("EUR_USD")
    assert (identity.base, identity.quote) == ("EUR", "USD")
    assert context.pair_identity("EURUSD") == identity
    # a HUMAN-parseable but undeclared spelling is rejected, never salvaged
    with pytest.raises(bars.BarError) as excinfo:
        fx.normalize_bar(record("2026-03-30T00:00:00", symbol="EUR-USD"), context)
    assert excinfo.value.reason_code == "UNKNOWN_INSTRUMENT"
    with pytest.raises(bars.BarError, match="UNKNOWN_INSTRUMENT"):
        context.pair_identity("eur_usd")  # case-sensitive declared table
    # identity is frozen to the canonical BASE/QUOTE form
    with pytest.raises(ValueError, match="BASE/QUOTE"):
        fxc.PairIdentity(base="EUR", quote="USD", instrument_id="EURUSD")


# --- disjointness: duplicate / overlap fail closed (never quarantine) -------------


def test_duplicate_and_overlap_intervals_fail_closed():
    context = make_context(session_rule=NEVER_CLOSED_RULE)
    with pytest.raises(bars.BarIntervalError) as excinfo:
        fx.normalize_stream(
            [record("2026-03-30T00:00:00"), record("2026-03-30T00:00:00")], context)
    assert excinfo.value.reason_code == "BAR_INTERVAL_DUPLICATE"
    with pytest.raises(bars.BarIntervalError) as excinfo:
        fx.normalize_stream(
            [record("2026-03-30T00:00:00"), record("2026-03-30T00:30:00")], context)
    assert excinfo.value.reason_code == "BAR_INTERVAL_OVERLAP"
    with pytest.raises(bars.BarIntervalError) as excinfo:
        fx.normalize_stream(
            [record("2026-03-30T01:00:00"), record("2026-03-30T00:00:00")], context)
    assert excinfo.value.reason_code == "BAR_INTERVAL_OVERLAP"


# --- microstructure rule: OHLCV never creates bid/ask/spread/swap ------------------


def test_ohlcv_never_creates_microstructure_evidence():
    context = make_context(session_rule=NEVER_CLOSED_RULE)
    bar = fx.normalize_bar(record("2026-03-30T00:00:00"), context)
    assert set(bar.keys()) == set(bars.BAR_FIELDS)
    forbidden = ("bid", "ask", "spread", "swap", "rollover")
    for key in bar:
        lowered = str(key).lower()
        assert not any(token in lowered for token in forbidden)
    # attempting to sneak microstructure fields in via the adapter fails closed
    for key in ("bid", "ask_price", "spread", "swap", "rollover_rate"):
        with pytest.raises(bars.BarError) as excinfo:
            fx.normalize_bar(record("2026-03-30T00:00:00", **{key: "1"}), context)
        assert excinfo.value.reason_code == "FOREX_FORBIDDEN_MICROSTRUCTURE_FIELD"
    # and post-hoc mutation of a validated bar fails bar validation
    mutated = dict(bar)
    mutated["bid_price"] = "1.0811"
    with pytest.raises(bars.BarError, match="unknown bar field"):
        bars.validate_bar(mutated)


# --- schedule: exactly one completed-bar availability lag + PnL denylist ----------


def test_decision_schedule_lag_exact_and_pnl_family_denylist():
    for lag_ns in (0, 300_000_000_000):
        context = make_context(session_rule=NEVER_CLOSED_RULE,
                               publication_lag_ns=lag_ns)
        result = fx.normalize_stream(_weekend_records(), context)
        rows = fxsch.project_decision_schedule(result, context)
        assert len(rows) == result.accepted_count == 5
        for row, bar in zip(rows, result.bars):
            assert tuple(row) == tuple(fxsch.SCHEDULE_ROW_FIELDS)
            assert row["decision_time_utc_ns"] == row["available_time_utc_ns"]
            assert row["available_time_utc_ns"] == \
                bar["close_time_utc_ns"] + lag_ns
            assert row["bar_open_time_utc_ns"] == bar["open_time_utc_ns"]
            assert row["bar_id"] == bar["bar_id"]
            assert row["row_kind"] == "FOREX_HOURLY_DECISION_ROW"
            assert row["publication_lag_ns"] == lag_ns
        # PnL-family denylist over every key of every row (independent regex)
        deny = re.compile(r"pnl|profit|return|sharpe|drawdown|cost|fee", re.I)
        for row in rows:
            for key in row:
                assert not deny.search(key), f"leaked schedule key {key!r}"
        # rows carry timestamps/ids/constants only
        allowed = {int, str}
        for row in rows:
            assert all(type(value) in allowed for value in row.values())
    # the internal leak guard itself fails closed
    with pytest.raises(AssertionError, match="leak guard"):
        fxsch._assert_no_pnl_keys({"pnl": 1})
    with pytest.raises(AssertionError, match="leak guard"):
        fxsch._assert_no_pnl_keys({"total_fees_bps": 1})
    with pytest.raises(bars.BarError, match="MALFORMED_SHAPE"):
        fxsch.project_decision_schedule({"bars": []}, make_context())


# --- availability clock, volume nullability, session flagging ----------------------


def test_publication_lag_default_close_time_and_lag_constant():
    context = make_context(session_rule=NEVER_CLOSED_RULE)
    bar = fx.normalize_bar(record("2026-03-30T00:00:00"), context)
    assert bar["available_time_utc_ns"] == bar["close_time_utc_ns"]  # default
    lagged = make_context(session_rule=NEVER_CLOSED_RULE,
                          publication_lag_ns=HOUR_NS // 2)
    bar2 = fx.normalize_bar(record("2026-03-30T00:00:00"), lagged)
    assert bar2["available_time_utc_ns"] == bar2["close_time_utc_ns"] + HOUR_NS // 2
    assert bar2["available_time_utc_ns"] > bar2["close_time_utc_ns"] > \
        bar2["open_time_utc_ns"]


def test_null_volume_is_not_evaluable_never_zero():
    context = make_context(session_rule=NEVER_CLOSED_RULE)
    bar = fx.normalize_bar(
        record("2026-03-30T00:00:00", volume=None), context)
    assert bar["volume"] is None
    assert bar["completeness_status"] == "NOT_EVALUABLE"
    assert "BAR_VOLUME_NOT_EVALUABLE" in bar["reason_codes"]
    assert bar["quality_status"] == "VALID"  # completeness never degrades quality
    with pytest.raises(bars.BarError, match="float input rejected"):
        fx.normalize_bar(record("2026-03-30T00:00:00", volume=1.5), context)


def test_bar_opening_inside_closure_is_suspect_not_deleted():
    context = make_context()  # default weekly closure
    bar = fx.normalize_bar(record("2026-03-29T12:00:00"), context)  # Sun 11:00Z
    assert "BAR_OUTSIDE_CALENDAR" in bar["reason_codes"]
    assert "BAR_VOLUME_NOT_EVALUABLE" in bar["reason_codes"]  # null forex volume class
    assert bar["quality_status"] == "SUSPECT"


# --- record sha / manifest discipline ----------------------------------------------


def test_raw_sha256_and_manifest_discipline():
    context = make_context()
    rec = record("2026-03-30T00:00:00")
    bar = fx.normalize_bar(rec, context)
    assert bar["raw_sha256"] == hashlib.sha256(
        models.canonical_json(dict(rec)).encode("utf-8")).hexdigest()
    assert bar["raw_id"] == bar["raw_sha256"]
    assert bar["manifest_sha256"] == MANIFEST_SHA
    pinned = fx.normalize_bar(
        record("2026-03-30T00:00:00", raw_sha256="ab" * 32), context)
    assert pinned["raw_sha256"] == "ab" * 32
    with pytest.raises(bars.BarError, match="raw_sha256"):
        fx.normalize_bar(record("2026-03-30T00:00:00", raw_sha256="nope"), context)
    no_manifest = make_context(manifest_sha256=None)
    result = fx.normalize_stream([record("2026-03-30T00:00:00")], no_manifest)
    assert result.quarantined[0]["reason_code"] == "MISSING_REQUIRED_FIELD"


# --- adapter hygiene -----------------------------------------------------------------


def test_inputs_never_mutated_and_quarantine_records_verbatim():
    context = make_context(session_rule=NEVER_CLOSED_RULE)
    good = record("2026-03-30T00:00:00")
    bad = {"date": "2026-03-04", "rate": "4.25"}
    good_snapshot = copy.deepcopy(good)
    bad_snapshot = copy.deepcopy(bad)
    result = fx.normalize_stream([good, bad], context)
    assert good == good_snapshot and bad == bad_snapshot
    assert result.quarantined[0]["raw_record"] == bad_snapshot
    assert result.quarantined[0]["stream_index"] == 1
    assert result.quarantine_reason_codes == ("FOREX_MACRO_DATE_ONLY_ROW",)
    assert result.bars[0]["instrument_id"] == "EUR/USD"
    assert result.stream_digest and result.stream_byte_length > 0


def test_forex_codes_live_outside_the_frozen_bar_registry():
    assert frozenset(fxc.FOREX_ADAPTER_REASON_CODES).isdisjoint(
        bars.ALL_BAR_REASON_CODES)
    with pytest.raises(AssertionError):
        fxc.ForexAdapterError("FOREX_NOT_A_REAL_CODE", "nope")
    # and they can never be smuggled into the bar model itself
    with pytest.raises(bars.BarError, match="outside reason_codes@1"):
        bars.build_bar({
            "instrument_id": "EUR/USD", "venue": "V", "source_id": "S",
            "provider_id": "P", "asset_class": "forex_spot",
            "bar_type": "1h-OHLC", "interval_ns": HOUR_NS,
            "open_time_utc_ns": 1, "close_time_utc_ns": 2,
            "available_time_utc_ns": 2, "open": "1", "high": "1",
            "low": "1", "close": "1", "price_precision": 1,
            "size_precision": 1, "adjustment_mode": "RAW",
            "raw_sha256": "ab" * 32, "manifest_sha256": "cd" * 32,
            "normalizer_version": "x", "reason_codes":
                ["FOREX_MACRO_DATE_ONLY_ROW"],
        })


def test_context_validation_fail_closed():
    with pytest.raises(ValueError, match="IANA"):
        make_context(provider_timezone="Not/AZone")
    with pytest.raises(ValueError, match="pair_table"):
        make_context(pair_table={})
    with pytest.raises(ValueError, match="unknown session rule"):
        make_context(session_rule="WEEKENDS_AND_MOST_OF_MONDAY")
    with pytest.raises(ValueError, match="publication_lag_ns"):
        make_context(publication_lag_ns=-1)
    with pytest.raises(ValueError, match="interval_ns"):
        make_context(interval_ns=0)
    # non-mapping records and None streams are rejected fail-closed
    with pytest.raises(bars.BarError, match="MALFORMED_SHAPE"):
        fx.normalize_bar("2026-03-30T00:00:00,1.08,1.09,1.07,1.08", make_context())
    with pytest.raises(bars.BarError, match="MALFORMED_SHAPE"):
        fx.normalize_stream(None, make_context())
    # non-AdapterResult inputs to downstream projections fail closed
    with pytest.raises(bars.BarError, match="AdapterResult"):
        fxcov.check_coverage({"bars": []}, make_context())
    with pytest.raises(bars.BarError, match="AdapterResult"):
        fxsch.project_decision_schedule([], make_context())
