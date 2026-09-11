"""Lane A8 tests: stocks daily OHLCV -> mdp.market_bar@2 adapter.

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
tests/test_mdp_adapter_stocks.py -q   (from the lane worktree root)

Hermetic synthetic fixtures only (no network).  Every frozen semantic rule
carries a test:

* happy path hand-computed (weekday, holiday-adjacent, early-close);
* permanent entity identity: ticker change keeps entity_id (and two names
  of one entity on one session are ONE bar identity — duplicate);
* RAW vs CORP_ACTION_ADJUSTED distinct identities + missing
  corporate_action_ref rejection + RAW-with-ref rejection;
* ex-date availability: a factor applied before its ex-date session open
  fails closed (no lookahead); non-session ex-dates fail closed;
* post-delist record fails closed (raise, never quarantine) with a
  dedicated census count;
* weekend/holiday records rejected BAR_OUTSIDE_CALENDAR;
* duplicate/overlap fail closed via bar_stream semantics;
* quarantine with frozen reason codes, nothing silently dropped;
* coverage: expected sessions, weekend/holiday gaps EXPECTED, missing
  weekday session UNEXPLAINED, dead-name census counts, early closes
  count as sessions;
* decision schedule: exactly one session availability lag, mode declared,
  PnL-family denylist leak guard, no numerics beyond ids/times/lag;
* no microstructure: input carrying bid/ask/spend-family rejected, output
  bar asserted absent of bid/ask/spread/mid keys.

Hand-computed instants: the frozen synthetic calendar opens sessions at
14:30 UTC and closes at 20:00 UTC (18:00 UTC on early-close dates).
Midnight 2026-06-01 UTC = 1_780_272_000_000_000_000 ns (days-since-epoch x
86_400e9); every session instant below is midnight + seconds x 1e9.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from market_data_plane import bars as _bars  # noqa: E402
from market_data_plane import models as _models  # noqa: E402
from market_data_plane.adapters.stocks import adapter as stocks  # noqa: E402
from market_data_plane.adapters.stocks import context as stocks_context  # noqa: E402
from market_data_plane.adapters.stocks.context import AdapterContext  # noqa: E402

# --- hand-computed frozen-calendar instants (ns) ---------------------------------

NS = 1_000_000_000
NS_PER_DAY = 86_400_000_000_000        # 86,400 s (one day) in ns
OPEN_SECS = 14 * 3600 + 30 * 60        # 14:30 UTC session open
REG_CLOSE_SECS = 20 * 3600             # 20:00 UTC regular close
EARLY_CLOSE_SECS = 18 * 3600           # 18:00 UTC early close

MIDNIGHT_JUN1 = 1_780_272_000_000_000_000          # 2026-06-01 (Mon)
MIDNIGHT_JUN3 = MIDNIGHT_JUN1 + 2 * NS_PER_DAY     # 2026-06-03 (Wed)
MIDNIGHT_JUN4 = MIDNIGHT_JUN1 + 3 * NS_PER_DAY     # 2026-06-04 (Thu)
MIDNIGHT_JUN9 = MIDNIGHT_JUN1 + 8 * NS_PER_DAY     # 2026-06-09 (Tue)

OPEN_0601 = MIDNIGHT_JUN1 + OPEN_SECS * NS
CLOSE_0601 = MIDNIGHT_JUN1 + REG_CLOSE_SECS * NS
OPEN_0603 = MIDNIGHT_JUN3 + OPEN_SECS * NS
CLOSE_0603 = MIDNIGHT_JUN3 + REG_CLOSE_SECS * NS
OPEN_0604 = MIDNIGHT_JUN4 + OPEN_SECS * NS
EARLY_CLOSE_0604 = MIDNIGHT_JUN4 + EARLY_CLOSE_SECS * NS
EX_OPEN_0609 = MIDNIGHT_JUN9 + OPEN_SECS * NS

MANIFEST_SHA = hashlib.sha256(b"s0-stocks-snapshot-manifest").hexdigest()
ENTITY_ACME = "E::ACME"
ENTITY_ZENITH = "E::ZENITH"
ADJUSTED_REF = {"ex_date": "2026-06-09", "split_factor": "4",
                "dividend_amount": "0.25"}
ADJUSTED_REF_STRING = "corp-action:" + _models.canonical_json(
    {"ex_date": "2026-06-09", "split_factor": "4", "dividend_amount": "0.25"})


def make_context(**overrides) -> AdapterContext:
    fields = dict(
        entity_table={
            "AAA": ENTITY_ACME,
            "AAB": ENTITY_ACME,       # ticker change: SAME permanent entity
            "ZZZ": ENTITY_ZENITH,
        },
        delist_dates={ENTITY_ZENITH: "2026-06-19"},
        holidays=["2026-06-02"],
        early_close_dates=["2026-06-04"],
        manifest_sha256=MANIFEST_SHA,
    )
    fields.update(overrides)
    return AdapterContext(**fields)


def record(trade_date: str, ticker: str = "AAA", mode: str = "RAW",
           **overrides) -> dict:
    rec = {
        "trade_date": trade_date,
        "ticker": ticker,
        "open": "10.00",
        "high": "10.50",
        "low": "9.90",
        "close": "10.25",
        "volume": "1000000",
        "adjustment_mode": mode,
    }
    rec.update(overrides)
    return rec


# --- happy path, hand-computed -----------------------------------------------------


def test_happy_path_weekday_hand_computed():
    context = make_context()
    raw = record("2026-06-01")
    bar = stocks.normalize_bar(raw, context)

    # exact frozen bar field list, nothing added, nothing dropped
    assert list(bar.keys()) == list(_bars.BAR_FIELDS)
    # hand-computed exchange-time mapping: open 14:30 UTC, close 20:00 UTC,
    # available = session close (frozen default availability rule)
    assert bar["open_time_utc_ns"] == OPEN_0601
    assert bar["close_time_utc_ns"] == CLOSE_0601
    assert bar["available_time_utc_ns"] == CLOSE_0601
    # exact decimal-string persistence of the raw values
    assert (bar["open"], bar["high"], bar["low"], bar["close"]) == \
        ("10.00", "10.50", "9.90", "10.25")
    assert bar["volume"] == "1000000"
    # frozen completeness rule: ANY null volume-class field -> NOT_EVALUABLE
    # with the code, never zero.  Stock records carry volume only; the
    # crypto-native volume-class fields stay null (never fabricated).
    assert bar["completeness_status"] == "NOT_EVALUABLE"
    assert bar["reason_codes"] == ["BAR_VOLUME_NOT_EVALUABLE"]
    for field_name in ("quote_volume", "trade_count", "taker_buy_base",
                       "taker_buy_quote"):
        assert bar[field_name] is None
    # identity: PERMANENT entity id from the frozen table, never the ticker
    assert bar["instrument_id"] == ENTITY_ACME
    assert "AAA" not in json.dumps(bar)
    assert bar["asset_class"] == "equity"
    assert bar["bar_type"] == "1d-LAST"
    assert bar["interval_ns"] == NS_PER_DAY
    assert bar["adjustment_mode"] == "RAW"
    assert bar["corporate_action_ref"] is None
    assert bar["price_precision"] == 4
    assert bar["size_precision"] == 8
    assert bar["normalizer_version"] == context.normalizer_version
    # no bar is VALID merely because parsing succeeded (frozen bar rule)
    assert bar["quality_status"] == "QUARANTINED"
    # raw discipline: sha over the exact canonical raw record bytes
    expected_raw_sha = hashlib.sha256(
        _models.canonical_json(dict(raw)).encode("utf-8")).hexdigest()
    assert bar["raw_sha256"] == expected_raw_sha
    assert bar["raw_id"] == expected_raw_sha
    assert bar["manifest_sha256"] == MANIFEST_SHA
    # golden bar_id recomputed BY HAND from the frozen identity tuple
    identity = {
        "schema_version": "mdp.market_bar@2",
        "source_id": "SYNTH-STOCKS-S0",
        "provider_id": "SYNTH",
        "venue": "XSYN",
        "instrument_id": ENTITY_ACME,
        "asset_class": "equity",
        "bar_type": "1d-LAST",
        "interval_ns": NS_PER_DAY,
        "open_time_utc_ns": OPEN_0601,
        "adjustment_mode": "RAW",
    }
    expected_bar_id = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True).encode("utf-8")).hexdigest()
    assert bar["bar_id"] == expected_bar_id
    # the normalized bar re-validates under the frozen bar contract
    assert _bars.validate_bar(bar) == bar


def test_happy_path_holiday_adjacent():
    context = make_context()
    # session immediately AFTER the 2026-06-02 holiday normalizes cleanly
    bar = stocks.normalize_bar(record("2026-06-03"), context)
    assert bar["open_time_utc_ns"] == OPEN_0603
    assert bar["close_time_utc_ns"] == CLOSE_0603
    assert bar["available_time_utc_ns"] == CLOSE_0603
    # the holiday itself is not a session: fail closed
    with pytest.raises(_bars.BarError) as excinfo:
        stocks.normalize_bar(record("2026-06-02"), context)
    assert excinfo.value.reason_code == "BAR_OUTSIDE_CALENDAR"


def test_happy_path_early_close():
    context = make_context()
    bar = stocks.normalize_bar(record("2026-06-04"), context)
    # early close: the session closes (and is available) at 18:00 UTC
    assert bar["open_time_utc_ns"] == OPEN_0604
    assert bar["close_time_utc_ns"] == EARLY_CLOSE_0604
    assert bar["available_time_utc_ns"] == EARLY_CLOSE_0604
    # an early close is still a full session for the calendar
    assert context.is_session(dt.date(2026, 6, 4))


def test_missing_volume_is_not_evaluable_never_zero():
    bar = stocks.normalize_bar(record("2026-06-01", volume=None), make_context())
    assert bar["volume"] is None
    assert bar["completeness_status"] == "NOT_EVALUABLE"
    assert "BAR_VOLUME_NOT_EVALUABLE" in bar["reason_codes"]


def test_missing_manifest_fails_closed():
    context = make_context(manifest_sha256="")
    with pytest.raises(_bars.BarError, match="manifest_sha256"):
        stocks.normalize_bar(record("2026-06-01"), context)


# --- permanent entity identity -------------------------------------------------------


def test_ticker_change_keeps_entity_id():
    context = make_context()
    before = stocks.normalize_bar(record("2026-06-01", ticker="AAA"), context)
    after = stocks.normalize_bar(record("2026-06-03", ticker="AAB"), context)
    # identity never derived from the ticker string: SAME permanent entity
    assert before["instrument_id"] == after["instrument_id"] == ENTITY_ACME
    # the shared-identity series is contiguous in the stream
    result = stocks.normalize_stream(
        [record("2026-06-01", ticker="AAA"), record("2026-06-03", ticker="AAB")],
        context)
    assert result.bar_count == 2
    assert result.quarantined == ()
    # one entity, one session, two names => ONE bar identity => duplicate
    with pytest.raises(_bars.BarIntervalError) as excinfo:
        stocks.normalize_stream(
            [record("2026-06-01", ticker="AAA"), record("2026-06-01", ticker="AAB")],
            context)
    assert excinfo.value.reason_code == "BAR_INTERVAL_DUPLICATE"
    # an unknown ticker fails closed (no identity invented from strings)
    with pytest.raises(_bars.BarError) as excinfo:
        stocks.normalize_bar(record("2026-06-01", ticker="QQQ"), context)
    assert excinfo.value.reason_code == "UNKNOWN_INSTRUMENT"


# --- raw vs adjusted identities --------------------------------------------------------


def test_raw_vs_adjusted_distinct_identities_and_missing_ref_rejected():
    context = make_context()
    raw = stocks.normalize_bar(record("2026-06-09"), context)
    adjusted = stocks.normalize_bar(
        record("2026-06-09", mode="CORP_ACTION_ADJUSTED",
               corporate_action_ref=ADJUSTED_REF), context)
    # same session, DIFFERENT identities (adjustment_mode is in bar_id)
    assert raw["bar_id"] != adjusted["bar_id"]
    assert raw["adjustment_mode"] == "RAW"
    assert adjusted["adjustment_mode"] == "CORP_ACTION_ADJUSTED"
    # corporate-action evidence referenced losslessly, never erased
    assert adjusted["corporate_action_ref"] == ADJUSTED_REF_STRING
    assert "2026-06-09" in adjusted["corporate_action_ref"]
    assert raw["corporate_action_ref"] is None

    # adjusted WITHOUT evidence fails closed
    with pytest.raises(_bars.BarError) as excinfo:
        stocks.normalize_bar(
            record("2026-06-09", mode="CORP_ACTION_ADJUSTED"), context)
    assert excinfo.value.reason_code == "MISSING_REQUIRED_FIELD"
    assert "corporate_action_ref" in str(excinfo.value)
    # RAW with evidence fails closed (identity hygiene)
    with pytest.raises(_bars.BarError, match="RAW records must not carry"):
        stocks.normalize_bar(
            record("2026-06-09", corporate_action_ref=ADJUSTED_REF), context)
    # unknown evidence keys fail closed (frozen evidence shape)
    with pytest.raises(_bars.BarError, match="unknown key"):
        stocks.normalize_bar(
            record("2026-06-09", mode="CORP_ACTION_ADJUSTED",
                   corporate_action_ref={"ex_date": "2026-06-09",
                                         "multiplier": "4"}), context)


# --- ex-date availability (no lookahead) --------------------------------------------------


def test_ex_date_availability_lookahead_rejected():
    context = make_context()
    # factor available at the 2026-06-09 session OPEN; a bar for 2026-06-08
    # becomes available at ITS session close (2026-06-08 20:00 UTC), i.e.
    # BEFORE the factor exists -> lookahead -> fail closed
    with pytest.raises(_bars.BarError) as excinfo:
        stocks.normalize_bar(
            record("2026-06-08", mode="CORP_ACTION_ADJUSTED",
                   corporate_action_ref=ADJUSTED_REF), context)
    assert excinfo.value.reason_code == "IMPOSSIBLE_TIME_ORDER"
    assert "lookahead" in str(excinfo.value)
    # exact availability instants involved (hand-computed)
    assert context.factor_available_ns(dt.date(2026, 6, 9)) == EX_OPEN_0609

    # the ex-date session itself carries the factor: legal
    ok = stocks.normalize_bar(
        record("2026-06-09", mode="CORP_ACTION_ADJUSTED",
               corporate_action_ref=ADJUSTED_REF), context)
    assert ok["available_time_utc_ns"] >= EX_OPEN_0609
    # a LATER session referencing an earlier factor: legal
    later = stocks.normalize_bar(
        record("2026-06-10", mode="CORP_ACTION_ADJUSTED",
               corporate_action_ref={"ex_date": "2026-06-09"}), context)
    assert later["adjustment_mode"] == "CORP_ACTION_ADJUSTED"

    # a factor whose ex-date is not a session has no availability instant
    with pytest.raises(_bars.BarError) as excinfo:
        stocks.normalize_bar(
            record("2026-06-03", mode="CORP_ACTION_ADJUSTED",
                   corporate_action_ref={"ex_date": "2026-06-02"}), context)
    assert excinfo.value.reason_code == "BAR_OUTSIDE_CALENDAR"


# --- delisting discipline -------------------------------------------------------------------


def test_post_delist_record_fails_closed_with_census():
    context = make_context()
    # the delist date itself is the terminal session: legal
    terminal = stocks.normalize_bar(record("2026-06-19", ticker="ZZZ"), context)
    assert terminal["instrument_id"] == ENTITY_ZENITH
    # strictly after the delist date: forward fill -> FAIL CLOSED (record API)
    with pytest.raises(stocks.PostDelistRecordError) as excinfo:
        stocks.normalize_bar(record("2026-06-22", ticker="ZZZ"), context)
    assert excinfo.value.census.post_delist_records == 1
    # stream API: raise, NEVER quarantine-and-continue
    stream_records = [
        record("2026-06-18", ticker="ZZZ"),
        record("2026-06-19", ticker="ZZZ"),
        record("2026-06-22", ticker="ZZZ"),   # post-delist: abort here
        record("2026-06-23", ticker="ZZZ"),   # must never be reached
    ]
    with pytest.raises(stocks.PostDelistRecordError) as excinfo:
        stocks.normalize_stream(stream_records, context)
    assert "forbidden" in str(excinfo.value)
    assert excinfo.value.census.post_delist_records == 1
    # clean streams carry the dedicated census field at zero
    clean = stocks.normalize_stream(
        [record("2026-06-18", ticker="ZZZ"), record("2026-06-19", ticker="ZZZ")],
        context)
    assert clean.census.post_delist_records == 0
    assert clean.bar_count == 2


# --- calendar membership -----------------------------------------------------------------------


def test_weekend_and_holiday_rejected_bar_outside_calendar():
    context = make_context()
    for bad_date in ("2026-06-06",):        # Saturday
        with pytest.raises(_bars.BarError) as excinfo:
            stocks.normalize_bar(record(bad_date), context)
        assert excinfo.value.reason_code == "BAR_OUTSIDE_CALENDAR"
    with pytest.raises(_bars.BarError) as excinfo:
        stocks.normalize_bar(record("2026-06-07"), context)  # Sunday
    assert excinfo.value.reason_code == "BAR_OUTSIDE_CALENDAR"
    with pytest.raises(_bars.BarError) as excinfo:
        stocks.normalize_bar(record("2026-06-02"), context)  # declared holiday
    assert excinfo.value.reason_code == "BAR_OUTSIDE_CALENDAR"


# --- duplicate / overlap fail closed (bar_stream semantics) --------------------------------------


def test_duplicate_and_overlap_fail_closed():
    context = make_context()
    # duplicate: same (entity, mode, session) twice
    with pytest.raises(_bars.BarIntervalError) as excinfo:
        stocks.normalize_stream(
            [record("2026-06-01"), record("2026-06-01")], context)
    assert excinfo.value.reason_code == "BAR_INTERVAL_DUPLICATE"
    # overlap: backwards delivery within one identity
    with pytest.raises(_bars.BarIntervalError) as excinfo:
        stocks.normalize_stream(
            [record("2026-06-03"), record("2026-06-01")], context)
    assert excinfo.value.reason_code == "BAR_INTERVAL_OVERLAP"
    # same session in BOTH modes is NOT a duplicate (distinct identities)
    result = stocks.normalize_stream(
        [record("2026-06-09"),
         record("2026-06-09", mode="CORP_ACTION_ADJUSTED",
                corporate_action_ref=ADJUSTED_REF)], context)
    assert result.bar_count == 2


# --- quarantine semantics --------------------------------------------------------------------------


def test_normalize_stream_quarantines_recoverable_defects_with_reason_codes():
    context = make_context()
    result = stocks.normalize_stream([
        record("2026-06-01"),                                    # ok
        record("2026-06-01", close="-1.0"),                      # BAR_NONPOSITIVE_PRICE
        record("2026-06-01", ticker="QQQ"),                      # UNKNOWN_INSTRUMENT
        record("2026-06-03"),                                    # ok
        record("2026-06-04", bid="9.95", ask="10.05"),           # microstructure rejected
    ], context)
    assert result.bar_count == 2
    assert len(result.quarantined) == 3
    assert result.quarantine_counts == {
        "BAR_NONPOSITIVE_PRICE": 1,
        "UNKNOWN_INSTRUMENT": 1,
        "MALFORMED_SHAPE": 1,
    }
    # nothing silently dropped
    assert result.bar_count + len(result.quarantined) == 5
    # quarantine rows carry stream index + a FROZEN reason code + lineage
    for entry in result.quarantined:
        assert entry["reason_code"] in _bars.ALL_BAR_REASON_CODES
        assert isinstance(entry["stream_index"], int)
        assert entry["message"]
    assert [e["stream_index"] for e in result.quarantined] == [1, 2, 4]
    # a non-mapping record quarantines too (never crashes the stream)
    result2 = stocks.normalize_stream([record("2026-06-01"), "garbage"], context)
    assert result2.bar_count == 1
    assert result2.quarantine_counts == {"MALFORMED_SHAPE": 1}
    # the adapter result is a frozen value object
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.bar_count = 99


# --- coverage ---------------------------------------------------------------------------------------


def test_coverage_expected_gaps_unexplained_gaps_and_early_close_session():
    context = make_context()
    result = stocks.normalize_stream([
        record("2026-06-01"),   # Mon
        # 06-02 Tue is a holiday (EXPECTED gap)
        record("2026-06-03"),   # Wed
        # 06-04 Thu deliberately MISSING: early close still counts as a
        # session -> its absence is UNEXPLAINED
        record("2026-06-05"),   # Fri
        # weekend 06-06/07 (EXPECTED gap)
        record("2026-06-08"),   # Mon
        record("2026-06-09"),   # Tue
    ], context)
    report = stocks.check_coverage(result, context)
    assert isinstance(report, stocks.CoverageReport)
    assert [e.entity_id for e in report.entities] == [ENTITY_ACME]
    entity = report.entities[0]
    assert (entity.first_session, entity.last_session) == \
        ("2026-06-01", "2026-06-09")
    # expected sessions: 06-01,03,04,05,08,09 (holiday 06-02 excluded;
    # early close 06-04 INCLUDED as a session)
    assert entity.expected_sessions == 6
    assert entity.observed_sessions == 5
    assert entity.unexplained_missing_sessions == ("2026-06-04",)
    # expected calendar gap days inside the life: holiday + weekend
    assert entity.expected_calendar_gap_days == 3   # 06-02, 06-06, 06-07
    assert entity.delist_date is None
    assert report.unexplained_gap_count == 1
    assert report.expected_gap_count == 3
    assert report.dead_name_census == ()


def test_dead_name_census_counts_bars_before_delist():
    context = make_context()
    result = stocks.normalize_stream([
        record("2026-06-01"),                    # ACME
        record("2026-06-03"),                    # ACME
        record("2026-06-15", ticker="ZZZ"),      # ZENITH Mon
        record("2026-06-16", ticker="ZZZ"),
        # 06-17 Wed deliberately missing (UNEXPLAINED inside life)
        record("2026-06-18", ticker="ZZZ"),
        record("2026-06-19", ticker="ZZZ"),      # terminal (delist) session
    ], context)
    report = stocks.check_coverage(result, context)
    zenith = next(e for e in report.entities if e.entity_id == ENTITY_ZENITH)
    assert zenith.delist_date == "2026-06-19"
    # dead-name census: bars-before-delist coverage counts (declared
    # diagnostic, no PnL) — 4 distinct observed sessions incl. the terminal
    assert zenith.bars_before_delist == 4
    assert zenith.expected_sessions_before_delist == 5
    assert zenith.observed_after_delist == 0
    assert zenith.unexplained_missing_sessions == ("2026-06-17",)
    assert report.dead_name_census == (zenith,)
    acme = next(e for e in report.entities if e.entity_id == ENTITY_ACME)
    assert acme.delist_date is None
    assert acme.bars_before_delist is None


# --- legacy daily decision schedule -------------------------------------------------------------------


def test_schedule_lag_exact_mode_declared_and_pnl_denylist_leak_guard():
    context = make_context()
    result = stocks.normalize_stream([
        record("2026-06-01"),
        record("2026-06-03"),
        record("2026-06-04"),                                  # early close
        record("2026-06-05"),
        record("2026-06-05", mode="CORP_ACTION_ADJUSTED",
               corporate_action_ref={"ex_date": "2026-06-05"}),
    ], context)
    rows = stocks.project_decision_schedule(result, context)
    # one row per completed session per (entity, declared mode)
    assert len(rows) == 5
    keys = [(r["entity_id"], r["adjustment_mode"], r["evidence_session"])
            for r in rows]
    assert len(set(keys)) == len(keys)
    for row in rows:
        assert row["schema"] == stocks.SCHEDULE_SCHEMA
        assert row["availability_lag_sessions"] == 1        # EXACTLY one lag
        # decision lands on the NEXT exchange session (holiday/weekend aware)
        decision = dt.date.fromisoformat(row["decision_session"])
        evidence = dt.date.fromisoformat(row["evidence_session"])
        assert decision == context.next_session(evidence)
        assert context.is_session(decision)
    # holiday-aware lag: 06-01 -> 06-03 (06-02 skipped)
    by_session = {r["evidence_session"]: r for r in rows
                  if r["adjustment_mode"] == "RAW"}
    assert by_session["2026-06-01"]["decision_session"] == "2026-06-03"
    assert by_session["2026-06-03"]["decision_session"] == "2026-06-04"
    assert by_session["2026-06-04"]["decision_session"] == "2026-06-05"
    # weekend-aware lag: Friday -> Monday
    assert by_session["2026-06-05"]["decision_session"] == "2026-06-08"
    # availability instant rides from the evidence bar (early-close aware)
    assert by_session["2026-06-04"]["evidence_available_time_utc_ns"] == \
        EARLY_CLOSE_0604
    assert by_session["2026-06-01"]["evidence_available_time_utc_ns"] == CLOSE_0601
    # total-return use is DECLARED: the adjusted schedule row carries its mode
    adjusted_rows = [r for r in rows if r["adjustment_mode"] == "CORP_ACTION_ADJUSTED"]
    assert len(adjusted_rows) == 1
    assert adjusted_rows[0]["evidence_session"] == "2026-06-05"
    assert adjusted_rows[0]["availability_lag_sessions"] == 1
    # traceability: row points at its exact evidence bar
    bar_ids = {b["bar_id"] for b in result.bars}
    assert all(r["bar_id"] in bar_ids for r in rows)
    # PnL-family denylist leak guard: no key matches; no numerics beyond
    # ids/times/lag; schedule rows are orderable and deterministic
    denylist = stocks.SCHEDULE_DENYLIST_RE
    for row in rows:
        for key, value in row.items():
            assert not denylist.search(key), key
            assert isinstance(value, (str, int))
            assert not isinstance(value, float)
    assert rows == stocks.project_decision_schedule(result, context)


# --- no microstructure -----------------------------------------------------------------------------------


def test_no_microstructure_input_rejected_output_absent():
    context = make_context()
    # input carrying bid/ask family fields is rejected outright
    for injected in ({"bid": "9.95"}, {"ask": "10.05"}, {"spread": "0.10"},
                     {"bid_size": "100", "mid": "10.00"}):
        with pytest.raises(_bars.BarError) as excinfo:
            stocks.normalize_bar(record("2026-06-01", **injected), context)
        assert excinfo.value.reason_code == "MALFORMED_SHAPE"
        assert "microstructure" in str(excinfo.value)
    # the frozen bar field list itself carries no microstructure field
    for field_name in _bars.BAR_FIELDS:
        lowered = field_name.lower()
        for token in ("bid", "ask", "spread", "mid"):
            assert token not in lowered, field_name
    # and a produced bar carries none (case-insensitive scan, asserted)
    bar = stocks.normalize_bar(record("2026-06-01"), context)
    for key in bar:
        lowered = key.lower()
        for token in ("bid", "ask", "spread", "mid"):
            assert token not in lowered


# --- frozen context ----------------------------------------------------------------------------------------


def test_adapter_context_is_frozen_and_defensively_copied():
    table = {"AAA": ENTITY_ACME}
    context = AdapterContext(entity_table=table)
    table["AAA"] = "E::MUTATED"          # caller-side mutation after freeze
    table["EVIL"] = "E::EVIL"
    # identity resolution is unchanged (snapshot taken at construction)
    assert context.entity_for_ticker("AAA") == ENTITY_ACME
    with pytest.raises(KeyError):
        context.entity_for_ticker("EVIL")
    # the context is a frozen value object
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.price_precision = 99
    # divergent adjustment-availability rules are a different adapter
    with pytest.raises(ValueError, match="frozen"):
        AdapterContext(entity_table={"AAA": ENTITY_ACME},
                       adjustment_availability_rule="SOMETHING_ELSE")
