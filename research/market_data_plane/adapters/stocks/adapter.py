"""Stocks daily OHLCV -> mdp.market_bar@2 adapter (lane A8, MDP-V2).

Freeze authority: research/control/market_data_plane_v2_run/
architecture_freeze_v2.json, sections ``adapters`` -> ``stocks`` (identity,
calendar, adjustment, delisting, total_return, legacy_parity_target) and
``adapters`` -> ``frozen_interface``:

* :func:`normalize_bar` — one raw provider record -> one validated canonical
  ``mdp.market_bar@2`` dict (built through :func:`market_data_plane.bars.build_bar`,
  so every frozen bar rule — decimal-string discipline, strict time order,
  NOT_EVALUABLE nulls, bar_id identity — is inherited, never reimplemented).
* :func:`normalize_stream` — ordered normalization + interval disjointness
  enforced THROUGH ``bar_stream.normalize_bar_stream`` (the frozen bar-stream
  semantics), quarantine with reason codes for recoverable row defects, and
  FAIL-CLOSED (raise, never quarantine-and-continue) for a record dated after
  its entity's delist date — forward-filled price after delisting is
  forbidden; the abort carries a dedicated census count.
* :func:`check_coverage` — calendar-aware coverage: expected sessions are the
  frozen calendar's sessions inside each entity's observed life (weekends and
  holidays are EXPECTED gaps; a missing weekday session inside a listed
  entity's life is UNEXPLAINED); dead-name census for delisted entities.
* :func:`project_decision_schedule` — the legacy daily decision schedule:
  schedule-only rows, one per completed session (per entity per declared
  adjustment mode), with exactly one session availability lag; NO PnL, no
  returns numerics, no positions, no rankings (denylist-guarded in code).

Frozen semantic rules honoured here (each test-enforced in
tests/test_mdp_adapter_stocks.py):

* permanent entity identity distinct from ticker: the bar ``instrument_id``
  IS the permanent entity_id resolved through the frozen context table; a
  ticker change keeps the same bar identity series (identity is never
  derived from the ticker string at runtime).
* raw vs adjusted separation: the same session as RAW and
  CORP_ACTION_ADJUSTED yields two distinct bar_ids (adjustment_mode is in
  the frozen bar_id identity tuple); adjusted bars require a non-null
  ``corporate_action_ref`` (rendered losslessly into the bar's
  ``corporate_action_ref`` identifier string — evidence referenced, never
  erased); RAW records carrying one fail closed.
* NO microstructure: input records carrying bid/ask/spread-family fields are
  rejected outright; the produced bar carries none (asserted absent) —
  OHLCV never synthesizes microstructure.
* split/dividend factors carry exact availability: a factor is available at
  its ex-date session OPEN (frozen rule on the context); an adjusted bar
  whose availability (its session close — the frozen default) precedes that
  instant is a LOOKAHEAD and fails closed.
* no forward fill after delisting: strictly post-delist records raise
  :class:`PostDelistRecordError` (abort; never quarantine-and-continue).
* no bar outside the exchange calendar: weekend/holiday trade dates raise
  ``BAR_OUTSIDE_CALENDAR`` (fail closed), as does a corporate-action ex-date
  that is not a session (its availability instant would be undefined).

Time mapping (frozen synthetic calendar): ``trade_date`` -> exchange-time ns
with ``open_time`` = session open, ``close_time`` = session close
(early-close-aware, 18:00 UTC on early-close dates), ``available_time`` =
session close (the frozen default availability rule, so
``close_time <= available_time`` holds with equality).

Quarantine reason codes are drawn from ``bars.ALL_BAR_REASON_CODES``
(reason_codes@1 + the frozen mdp.bar_reason_codes@2 extension) only.
Interval duplicate/overlap and no-lookahead violations are NOT quarantined —
they propagate from ``bar_stream`` as :class:`BarIntervalError` /
``BarError`` (fail closed, per the frozen bar_contract interval rule).

stdlib + sibling market_data_plane modules only; no network; never mutates
its inputs.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Mapping

from ... import bar_stream as _bar_stream
from ... import bars as _bars
from ... import models as _models
from .context import AdapterContext, parse_iso_date

__all__ = [
    "MICROSTRUCTURE_FIELDS",
    "SCHEDULE_SCHEMA",
    "SCHEDULE_DENYLIST_RE",
    "AdapterResult",
    "CoverageReport",
    "EntityCoverage",
    "PostDelistRecordError",
    "StocksAdapterError",
    "StreamCensus",
    "check_coverage",
    "normalize_bar",
    "normalize_stream",
    "project_decision_schedule",
]


# --- adapter error family -----------------------------------------------------

class StocksAdapterError(ValueError):
    """Adapter-level fail-closed violation (aborts; never silent)."""


class PostDelistRecordError(StocksAdapterError):
    """A record dated strictly after its entity's delist date.

    Forward-filled price after delisting is forbidden: this is fail-closed
    at BOTH the record API (:func:`normalize_bar` raises) and the stream API
    (:func:`normalize_stream` raises — never quarantine-and-continue for
    this specific defect).  The exception carries ``census``, a
    :class:`StreamCensus` snapshot whose dedicated ``post_delist_records``
    field counts the defect.
    """

    code = "POST_DELIST_RECORD"

    def __init__(self, message: str, *, census: "StreamCensus | None" = None):
        super().__init__(message)
        self.census = census if census is not None else StreamCensus()


# --- microstructure denylist (frozen) ------------------------------------------

#: Input fields that describe microstructure.  A daily OHLCV record carrying
#: any of these is rejected outright: bars never synthesize bid/ask/spread
#: evidence, and the adapter will not launder it away either.
MICROSTRUCTURE_FIELDS: frozenset[str] = frozenset({
    "bid", "ask", "bid_price", "ask_price", "bid_size", "ask_size",
    "bid_volume", "ask_volume", "best_bid", "best_ask", "spread", "mid",
    "mid_price",
})

#: Keys a normalized bar must NEVER contain (no-microstructure guarantee,
#: asserted on output as well as enforced on input).
_BAR_MICROSTRUCTURE_SCAN = ("bid", "ask", "spread", "mid")


def _assert_no_microstructure(record: Mapping) -> None:
    present = sorted(set(map(str, record.keys())) & MICROSTRUCTURE_FIELDS)
    if present:
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"microstructure field(s) {present} forbidden in a daily OHLCV "
            "record: bars never synthesize bid/ask/spread evidence (fail closed)")


def _assert_bar_has_no_microstructure(bar: Mapping) -> None:
    for key in bar.keys():
        lowered = str(key).lower()
        for token in _BAR_MICROSTRUCTURE_SCAN:
            assert token not in lowered, (
                f"no-microstructure violated: bar carries key {key!r}")


# --- record parsing helpers -----------------------------------------------------

_RAW_RECORD_FIELDS: frozenset[str] = frozenset({
    "trade_date", "ticker", "open", "high", "low", "close", "volume",
    "quote_volume", "trade_count", "taker_buy_base", "taker_buy_quote",
    "adjustment_mode", "corporate_action_ref", "manifest_sha256",
})

_CORP_REF_FIELDS: frozenset[str] = frozenset(
    {"ex_date", "split_factor", "dividend_amount"})


def _raw_sha256(record: Mapping) -> str:
    """sha256 over the exact raw provider record bytes (canonical form)."""
    try:
        payload = _models.canonical_json(dict(record)).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"raw record is not canonically serializable: {exc}") from exc
    return hashlib.sha256(payload).hexdigest()


def _required(raw: Mapping, key: str):
    value = raw.get(key)
    if value is None:
        raise _bars.BarError("MISSING_REQUIRED_FIELD", f"{key} is required")
    return value


def _corp_ref_string(ref: Mapping) -> str:
    """Lossless canonical rendering of the corporate-action evidence.

    The bar's ``corporate_action_ref`` field is a non-empty string
    identifier; the evidence dict is canonical_json-encoded inside it so the
    reference is exact, deterministic and never erased.
    """
    return "corp-action:" + _models.canonical_json(dict(ref))


def _normalize_corp_ref(raw_ref, context: AdapterContext, trade_date: dt.date) -> str:
    """Validate the corporate-action evidence and enforce the frozen
    availability rule; return the lossless reference string for the bar.

    Fail closed when:

    * the ref is missing / not a mapping / carries unknown keys
      (evidence shape is frozen: ex_date + optional split_factor /
      dividend_amount);
    * ``ex_date`` is not an exchange session (the factor's availability
      instant would be undefined);
    * the bar's availability (its session close — frozen default rule)
      precedes the factor's availability at the ex-date session OPEN — a
      lookahead is forbidden (IMPOSSIBLE_TIME_ORDER);
    * split_factor / dividend_amount are not exact decimal scalars.
    """
    if raw_ref is None:
        raise _bars.BarError(
            "MISSING_REQUIRED_FIELD",
            "CORP_ACTION_ADJUSTED requires a non-null corporate_action_ref "
            "{ex_date, split_factor?, dividend_amount?}")
    if not isinstance(raw_ref, Mapping):
        raise _bars.BarError(
            "MALFORMED_SHAPE", "corporate_action_ref must be a mapping")
    unknown = sorted(set(map(str, raw_ref.keys())) - _CORP_REF_FIELDS)
    if unknown:
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"corporate_action_ref carries unknown key(s) {unknown}; frozen "
            "evidence shape is {ex_date, split_factor?, dividend_amount?}")

    ex_date = parse_iso_date(_required(raw_ref, "ex_date"), "corporate_action_ref.ex_date")
    if not context.is_session(ex_date):
        raise _bars.BarError(
            "BAR_OUTSIDE_CALENDAR",
            f"corporate_action_ref.ex_date {ex_date.isoformat()} is not an "
            "exchange session; the factor's availability instant would be "
            "undefined (fail closed)")

    canonical_ref: dict[str, str] = {"ex_date": ex_date.isoformat()}
    for key in ("split_factor", "dividend_amount"):
        if key not in raw_ref or raw_ref[key] is None:
            continue
        value = raw_ref[key]
        if isinstance(value, bool) or isinstance(value, float):
            raise _bars.BarError(
                "MALFORMED_SHAPE",
                f"corporate_action_ref.{key}: float/bool rejected; supply an "
                "exact decimal string")
        try:
            if isinstance(value, str):
                d = _models.decimal_string_to_decimal(value)
            elif isinstance(value, int):
                d = Decimal(value)
            else:
                raise _bars.BarError(
                    "MALFORMED_SHAPE",
                    f"corporate_action_ref.{key}: unsupported type "
                    f"{type(value).__name__}")
        except _models.MarketDataPlaneError as exc:
            raise _bars.BarError(exc.reason_code, f"corporate_action_ref.{key}: {exc}") from exc
        if not d.is_finite() or d <= 0:
            raise _bars.BarError(
                "NON_FINITE_PRICE" if not d.is_finite() else "BAR_NONPOSITIVE_PRICE",
                f"corporate_action_ref.{key} must be a finite positive decimal")
        canonical_ref[key] = _models.to_fixed_point_string(d)

    # Frozen availability rule: factor available at ex-date session OPEN;
    # the adjusted bar's availability is its own session close.  Applying
    # the factor to a session that CLOSES before the factor is AVAILABLE is
    # a lookahead — fail closed, never rewritten availability.
    available_ns = context.session_available_ns(trade_date)
    factor_ns = context.factor_available_ns(ex_date)
    if available_ns < factor_ns:
        raise _bars.BarError(
            "IMPOSSIBLE_TIME_ORDER",
            f"corporate-action lookahead: bar session {trade_date.isoformat()} "
            f"becomes available at ns {available_ns}, before its referenced "
            f"factor is available at the ex-date {ex_date.isoformat()} session "
            f"open (ns {factor_ns}); a factor applied before its ex-date "
            "availability fails closed (no lookahead)")
    return _corp_ref_string(canonical_ref)


# --- normalize_bar ----------------------------------------------------------------

def normalize_bar(raw_record: Mapping, context: AdapterContext) -> dict:
    """One raw daily OHLCV row -> one canonical ``mdp.market_bar@2`` dict.

    Fail closed on any violation (raises; nothing is dropped or repaired):

    * record shape: Mapping, no microstructure fields, canonically
      serializable, required keys present (``trade_date``, ``ticker``,
      OHLC, ``adjustment_mode``);
    * identity: ``ticker`` must resolve through the frozen entity table
      (UNKNOWN_INSTRUMENT otherwise); the bar's ``instrument_id`` is the
      PERMANENT entity_id — never the ticker string;
    * calendar: ``trade_date`` must be an exchange session
      (BAR_OUTSIDE_CALENDAR for weekends/holidays);
    * delisting: a record dated strictly after the entity's delist date
      raises :class:`PostDelistRecordError` (no forward fill after delisting);
    * adjustment: mode in {RAW, CORP_ACTION_ADJUSTED}; adjusted records
      require the corporate-action evidence and pass the frozen ex-date
      availability (no-lookahead) rule; RAW records must not carry one.
    """
    if not isinstance(raw_record, Mapping):
        raise _bars.BarError("MALFORMED_SHAPE", "raw record must be a mapping")
    _assert_no_microstructure(raw_record)
    raw_sha = _raw_sha256(raw_record)
    unknown = sorted(set(map(str, raw_record.keys())) - _RAW_RECORD_FIELDS)
    if unknown:
        raise _bars.BarError(
            "MALFORMED_SHAPE", f"raw record carries unknown field(s) {unknown}")

    trade_date = parse_iso_date(
        _required(raw_record, "trade_date"), "trade_date")
    ticker = _required(raw_record, "ticker")
    try:
        entity_id = context.entity_for_ticker(ticker)
    except KeyError:
        raise _bars.BarError(
            "UNKNOWN_INSTRUMENT",
            f"ticker {ticker!r} is not in the frozen entity table; identity "
            "is never derived from the ticker string at runtime (fail closed)")

    # Calendar membership: no bar outside the exchange calendar (weekends
    # and holidays fail closed — they are EXPECTED gaps, never bars).
    if not context.is_session(trade_date):
        raise _bars.BarError(
            "BAR_OUTSIDE_CALENDAR",
            f"trade_date {trade_date.isoformat()} is not an exchange session "
            "(weekend or holiday); no bar outside the exchange calendar")

    # Delisting discipline: the delist date is the terminal session; a
    # record strictly after it is a forward-filled price — forbidden, and
    # NEVER quarantined-and-continued.
    delist = context.delist_date(entity_id)
    if delist is not None and trade_date > delist:
        raise PostDelistRecordError(
            f"record for entity {entity_id} (ticker {ticker!r}) dated "
            f"{trade_date.isoformat()} is AFTER its delist date "
            f"{delist.isoformat()}: forward-filled price after delisting is "
            "forbidden (fail closed, not quarantine)",
            census=StreamCensus(post_delist_records=1))

    mode = _required(raw_record, "adjustment_mode")
    if mode not in _bars.ADJUSTMENT_MODES:
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"adjustment_mode {mode!r} outside {_bars.ADJUSTMENT_MODES}")

    corp_ref = raw_record.get("corporate_action_ref")
    if mode == "RAW":
        if corp_ref is not None:
            raise _bars.BarError(
                "MALFORMED_SHAPE",
                "RAW records must not carry a corporate_action_ref; adjusted "
                "bars are a different identity "
                "(adjustment_mode=CORP_ACTION_ADJUSTED)")
        corp_ref_string = None
    else:  # CORP_ACTION_ADJUSTED
        corp_ref_string = _normalize_corp_ref(corp_ref, context, trade_date)

    open_ns = context.session_open_ns(trade_date)
    close_ns = context.session_close_ns(trade_date)
    available_ns = context.session_available_ns(trade_date)

    manifest_sha = raw_record.get("manifest_sha256") or context.manifest_sha256
    if not manifest_sha:
        raise _bars.BarError(
            "MISSING_REQUIRED_FIELD",
            "manifest_sha256 is required (record override or adapter context "
            "default); the upstream retrieval manifest id cannot be invented")

    bar = _bars.build_bar({
        "source_id": context.source_id,
        "provider_id": context.provider_id,
        "venue": context.venue,
        "instrument_id": entity_id,          # PERMANENT identity, not the ticker
        "asset_class": context.asset_class,
        "bar_type": context.bar_type,
        "interval_ns": context.interval_ns,
        "open_time_utc_ns": open_ns,
        "close_time_utc_ns": close_ns,
        "available_time_utc_ns": available_ns,
        "open": _required(raw_record, "open"),
        "high": _required(raw_record, "high"),
        "low": _required(raw_record, "low"),
        "close": _required(raw_record, "close"),
        "volume": raw_record.get("volume"),
        "quote_volume": raw_record.get("quote_volume"),
        "trade_count": raw_record.get("trade_count"),
        "taker_buy_base": raw_record.get("taker_buy_base"),
        "taker_buy_quote": raw_record.get("taker_buy_quote"),
        "price_precision": context.price_precision,
        "size_precision": context.size_precision,
        "adjustment_mode": mode,
        "corporate_action_ref": corp_ref_string,
        # quality_status deliberately left unset: no bar is VALID merely
        # because parsing succeeded (the bar model defaults QUARANTINED);
        # promotion is a downstream quality decision, never the adapter's.
        "raw_sha256": raw_sha,
        "manifest_sha256": manifest_sha,
        "normalizer_version": context.normalizer_version,
    })
    _assert_bar_has_no_microstructure(bar)
    return bar


# --- stream census / result ---------------------------------------------------------

@dataclass(frozen=True)
class StreamCensus:
    """Dedicated stream census counts (declared diagnostics, no PnL)."""

    #: records dated after their entity's delist date (post-delist
    #: forward-fill attempts).  A stream containing one ABORTS fail-closed;
    #: the count rides on :attr:`PostDelistRecordError.census`.
    post_delist_records: int = 0


@dataclass(frozen=True)
class AdapterResult:
    """Result of :func:`normalize_stream` (normalized + quarantined + census).

    ``nothing silently dropped`` invariant: ``bar_count + len(quarantined)``
    equals the number of input records for every completed (non-aborted)
    stream.
    """

    #: canonical bars, INPUT ORDER preserved (via bar_stream validation)
    bars: tuple[dict, ...]
    bar_count: int
    #: rows quarantined with reason codes: {stream_index, reason_code,
    #: message, raw_sha256}.  Recoverable row defects only.
    quarantined: tuple[dict, ...]
    quarantine_counts: Mapping[str, int]
    census: StreamCensus
    stream_digest: str
    stream_byte_length: int
    #: bar_stream completeness (contiguity of daily slots per identity;
    #: weekend/holiday session breaks legitimately report GAPS_PRESENT —
    #: the CALENDAR-aware classification lives in check_coverage).
    completeness_status: str | None
    gap_reasons: tuple[str, ...]
    gaps: tuple[dict, ...]


def normalize_stream(raw_records: Iterable[Mapping], context: AdapterContext) -> AdapterResult:
    """Normalize an ordered record stream; quarantine rows, fail closed on
    delisting violations, enforce disjointness via bar_stream semantics.

    Per record: :func:`normalize_bar`; a recoverable defect (any
    ``BarError``) is QUARANTINED with its frozen reason code and never
    silently dropped; a post-delist record ABORTS the whole stream by
    raising :class:`PostDelistRecordError` carrying the census count (never
    quarantine-and-continue for that defect).

    Across the normalized bars: ``bar_stream.normalize_bar_stream`` enforces
    structural validation, per-identity ordering, interval disjointness
    (BAR_INTERVAL_DUPLICATE / BAR_INTERVAL_OVERLAP propagate — fail closed,
    never quarantine) and the availability no-lookahead gate.
    """
    if raw_records is None:
        raise StocksAdapterError("raw_records must be an iterable of mappings")
    bars: list[dict] = []
    quarantined: list[dict] = []
    census = StreamCensus(post_delist_records=0)
    for index, raw in enumerate(raw_records):
        try:
            if not isinstance(raw, Mapping):
                raise _bars.BarError(
                    "MALFORMED_SHAPE",
                    f"stream record {index} must be a mapping, got "
                    f"{type(raw).__name__}")
            bars.append(normalize_bar(raw, context))
        except PostDelistRecordError:
            # fail closed: dedicated census field + abort (never quarantine)
            census = StreamCensus(post_delist_records=census.post_delist_records + 1)
            raise PostDelistRecordError(
                f"stream aborted at record index {index}: post-delist record "
                "(forward-filled price after delisting is forbidden)",
                census=census,
            )
        except _bars.BarError as exc:
            try:
                raw_sha = _raw_sha256(raw) if isinstance(raw, Mapping) else None
            except _bars.BarError:
                raw_sha = None
            quarantined.append({
                "stream_index": index,
                "reason_code": exc.reason_code,
                "message": str(exc),
                "raw_sha256": raw_sha,
            })

    counts: dict[str, int] = {}
    for entry in quarantined:
        counts[entry["reason_code"]] = counts.get(entry["reason_code"], 0) + 1

    # Disjointness / ordering / no-lookahead via the frozen bar-stream
    # semantics — duplicates and overlaps FAIL CLOSED here (BarIntervalError).
    stream = _bar_stream.normalize_bar_stream(bars)
    return AdapterResult(
        bars=tuple(stream["bars"]),
        bar_count=stream["bar_count"],
        quarantined=tuple(quarantined),
        quarantine_counts=counts,
        census=census,
        stream_digest=stream["stream_digest"],
        stream_byte_length=stream["stream_byte_length"],
        completeness_status=stream["completeness_status"],
        gap_reasons=tuple(stream["gap_reasons"]),
        gaps=tuple(stream["gaps"]) if stream["gaps"] is not None else (),
    )


# --- coverage -------------------------------------------------------------------------

@dataclass(frozen=True)
class EntityCoverage:
    """Per-entity coverage over the entity's observed life (declared diagnostic)."""

    entity_id: str
    first_session: str
    last_session: str
    expected_sessions: int
    observed_sessions: int
    #: expected calendar sessions inside the life with no bar (UNEXPLAINED)
    unexplained_missing_sessions: tuple[str, ...]
    #: weekend/holiday days inside the life — EXPECTED gaps, never unexplained
    expected_calendar_gap_days: int
    # --- dead-name census (entities with delist dates only; else None) ---
    delist_date: str | None
    #: distinct observed sessions up to and including the terminal
    #: (delist-date) session
    bars_before_delist: int | None
    expected_sessions_before_delist: int | None
    #: defensive: always 0 (a post-delist bar can never normalize)
    observed_after_delist: int | None


@dataclass(frozen=True)
class CoverageReport:
    """Calendar-aware coverage report (declared diagnostics; no PnL)."""

    entities: tuple[EntityCoverage, ...]
    unexplained_gap_count: int
    expected_gap_count: int
    #: subset of entities with delist dates (the dead-name census)
    dead_name_census: tuple[EntityCoverage, ...]


def check_coverage(result: AdapterResult, context: AdapterContext) -> CoverageReport:
    """Expected-vs-observed session coverage per permanent entity.

    Expected sessions come from the frozen calendar (weekdays minus
    holidays; early closes still count as sessions) inside each entity's
    observed life ``[first observed session, last observed session]``
    (capped at the delist date for delisted entities).  Weekend/holiday
    gaps are EXPECTED; a missing weekday session inside a listed entity's
    life is UNEXPLAINED.  Entities with delist dates additionally report
    the dead-name census (bars-before-delist coverage counts).
    """
    observed: dict[str, set[dt.date]] = {}
    for bar in result.bars:
        entity_id = bar["instrument_id"]
        day = _models.ns_to_timestamp(bar["open_time_utc_ns"]).date()
        observed.setdefault(entity_id, set()).add(day)

    entities: list[EntityCoverage] = []
    for entity_id in sorted(observed):
        days = observed[entity_id]
        first, last = min(days), max(days)
        delist = context.delist_date(entity_id)
        life_end = last if delist is None else min(last, delist)

        sessions = context.sessions_between(first, life_end)
        gap_days = context.calendar_gap_days(first, life_end)
        missing = tuple(sorted(
            day.isoformat() for day in sessions if day not in days))

        if delist is None:
            delist_iso = bars_before = expected_before = after = None
        else:
            delist_iso = delist.isoformat()
            bars_before = len([d for d in days if d <= delist])
            expected_before = len(context.sessions_between(first, delist))
            after = len([d for d in days if d > delist])
            assert after == 0, (
                "post-delist bar reached coverage; normalize_bar must have "
                "failed closed first")

        entities.append(EntityCoverage(
            entity_id=entity_id,
            first_session=first.isoformat(),
            last_session=last.isoformat(),
            expected_sessions=len(sessions),
            observed_sessions=len(days),
            unexplained_missing_sessions=missing,
            expected_calendar_gap_days=len(gap_days),
            delist_date=delist_iso,
            bars_before_delist=bars_before,
            expected_sessions_before_delist=expected_before,
            observed_after_delist=after,
        ))

    unexplained = sum(len(e.unexplained_missing_sessions) for e in entities)
    expected_gaps = sum(e.expected_calendar_gap_days for e in entities)
    return CoverageReport(
        entities=tuple(entities),
        unexplained_gap_count=unexplained,
        expected_gap_count=expected_gaps,
        dead_name_census=tuple(e for e in entities if e.delist_date is not None),
    )


# --- legacy daily decision schedule ------------------------------------------------

#: Declared schedule schema (schedule-only rows; NO PnL/returns/positions).
SCHEDULE_SCHEMA = "mdp.stocks_decision_schedule@1"

#: PnL-family denylist: no schedule key may ever match (leak guard, enforced
#: in code as well as tested — the schedule carries schedule semantics only).
SCHEDULE_DENYLIST_RE = re.compile(
    r"pnl|profit|return|sharpe|drawdown|cost|fee", re.IGNORECASE)


def _assert_schedule_row_clean(row: Mapping) -> None:
    for key in row.keys():
        assert not SCHEDULE_DENYLIST_RE.search(str(key)), (
            f"schedule leak guard: key {key!r} matches the PnL-family denylist")
        value = row[key]
        assert isinstance(value, (str, int)) and not isinstance(value, bool) \
            and not isinstance(value, float), (
            f"schedule leak guard: value for {key!r} must be str/int, got "
            f"{type(value).__name__} (no numerics beyond ids/times/lag)")


def project_decision_schedule(result: AdapterResult,
                              context: AdapterContext) -> list[dict]:
    """Legacy daily decision schedule: one row per completed session.

    A completed session T (its bar is in the result, available at T's
    session close) produces exactly one schedule row per
    ``(entity_id, adjustment_mode)`` identity: the decision applies to the
    NEXT exchange session (``availability_lag_sessions == 1``, exactly one
    session lag — never zero, never two).  Total-return use is DECLARED:
    every row carries its evidence bar's ``adjustment_mode`` explicitly, so
    RAW (execution-price) and CORP_ACTION_ADJUSTED (total-return) schedules
    never blur.

    Rows carry schedule semantics ONLY: identifiers, ISO sessions, the
    availability instant, the declared mode and the constant lag.  NO PnL,
    no returns numerics, no positions, no rankings (a code-level denylist
    guard fails closed on any violating key or non-str/int value).
    """
    rows: list[dict] = []
    for bar in result.bars:
        evidence_day = _models.ns_to_timestamp(bar["open_time_utc_ns"]).date()
        decision_day = context.next_session(evidence_day)
        row = {
            "schema": SCHEDULE_SCHEMA,
            "entity_id": bar["instrument_id"],
            "evidence_session": evidence_day.isoformat(),
            "decision_session": decision_day.isoformat(),
            "evidence_available_time_utc_ns": int(bar["available_time_utc_ns"]),
            "availability_lag_sessions": 1,
            "adjustment_mode": bar["adjustment_mode"],
            "bar_id": bar["bar_id"],
        }
        _assert_schedule_row_clean(row)
        rows.append(row)
    rows.sort(key=lambda r: (r["entity_id"], r["adjustment_mode"],
                             r["evidence_session"]))
    return rows
