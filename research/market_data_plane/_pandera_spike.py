"""Isolated Pandera compatibility spike (freeze pandera_acceptance_criteria).

This module is the ONLY place in the A2 lane where pandas/pandera are
imported, and even here they are imported lazily INSIDE functions — module
import is side-effect free and heavy-import free (freeze ``import_isolation``).

Scope (frozen): batch/DataFrame ingestion boundary only; ``strict=True``; no
implicit column addition; ``coerce=False`` by default.  The differential
runner compares the frozen native validator
(:func:`market_data_plane.models.validate_event`) against equivalent pandera
DataFrame schemas on four fixture sets: crypto trades, forex bid/ask, stocks
quotes, macro series.

This module WRITES NO VERDICT.  It returns measured evidence; the
ADOPTED / PANDERA_EVALUATED_NOT_ADOPTED decision belongs to A1 at P5A.  Where
pandera cannot express a frozen invariant without coercion, that is recorded
as evidence (the criterion fails) — the schema is never loosened to make the
spike pass.
"""

from __future__ import annotations

import copy
import hashlib
import statistics
import time
from decimal import Decimal

from . import models as _models
from . import reason_codes as _rc

# --- frozen acceptance criteria (verbatim from architecture_freeze.json) ----

SPIKE_SCOPE = ("batch/DataFrame ingestion boundary only; strict=True; no implicit "
               "column addition; coerce=False by default")
FIXTURE_NAMES = ("crypto trades", "forex bid/ask", "stocks quotes", "macro series")
ADOPT_REQUIRES_ALL = (
    "identical accepted/rejected row sets and reason attribution vs native frozen schema",
    "no timestamp timezone loss",
    "no Decimal-to-float conversion",
    "deterministic errors independent of row order",
    "no mutation of the input DataFrame",
    "no unexplained runtime or peak-memory regression over 20% vs the native validator "
    "on the same fixtures",
    "optional import isolation: event-stream hot path does not depend on pandas/pandera",
)
FAILURE_VERDICT = "PANDERA_EVALUATED_NOT_ADOPTED"

#: Timing procedure (freeze benchmark_method spirit): 2 warmups + 5 measured
#: repeats per side; medians compared.
TIMING_WARMUPS = 2
TIMING_REPEATS = 5

_HEX64 = "^[0-9a-f]{64}$"
_FIXED_POINT = r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$"


# --- lazy heavy imports -----------------------------------------------------

def _pandas():
    import pandas as pd
    return pd


def _pandera():
    import pandera.pandas as pa
    return pa


# --- deterministic fixtures -------------------------------------------------

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _trade_row(i: int, **overrides):
    fields = dict(
        schema_version=_models.SCHEMA_VERSION,
        raw_id=f"crypto-{i}", source_id="binance-feed", venue="BINANCE",
        instrument_id="BTCUSDT" if i % 2 == 0 else "ETHUSDT",
        asset_class="crypto", event_type="TRADE",
        exchange_time_utc_ns=1_700_000_000_000_000_000 + i * 1_000_000,
        receive_time_utc_ns=1_700_000_000_000_000_000 + i * 1_000_000 + 250_000,
        available_time_utc_ns=1_700_000_000_000_000_000 + i * 1_000_000 + 500_000,
        sequence_number=i,
        price=f"{60000 + (i % 50)}.{(i * 7) % 10**8:08d}",
        quantity=f"0.{(i * 13) % 10**8:08d}",
        side="buy" if i % 3 == 0 else "sell",
        price_precision=8, size_precision=8,
        raw_sha256=_sha(f"crypto-raw-{i}".encode()),
        manifest_sha256=_sha(b"chunk-manifest-1"),
        normalizer_version="mdp-normalizer@1",
    )
    fields.update(overrides)
    return fields


def _quote_row(i: int, **overrides):
    spread = "0.00010"
    fields = dict(
        schema_version=_models.SCHEMA_VERSION,
        raw_id=f"fx-{i}", source_id="lmax-feed", venue="LMAX",
        instrument_id="EURUSD", asset_class="forex", event_type="QUOTE",
        exchange_time_utc_ns=1_700_000_100_000_000_000 + i * 300_000_000,
        receive_time_utc_ns=1_700_000_100_000_000_000 + i * 300_000_000 + 120_000_000,
        available_time_utc_ns=1_700_000_100_000_000_000 + i * 300_000_000 + 240_000_000,
        sequence_number=i,
        bid_price=f"1.{(i % 40):02d}0{50000 + (i * 11) % 40000:05d}",
        ask_price=str(Decimal(f"1.{(i % 40):02d}0{50000 + (i * 11) % 40000:05d}")
                      + Decimal(spread)),
        bid_size=f"{1 + i % 5}.0",
        ask_size=f"{1 + i % 7}.0",
        currency="USD",
        price_precision=8, size_precision=1,
        raw_sha256=_sha(f"fx-raw-{i}".encode()),
        manifest_sha256=_sha(b"chunk-manifest-2"),
        normalizer_version="mdp-normalizer@1",
    )
    fields.update(overrides)
    return fields


def _stock_quote_row(i: int, **overrides):
    fields = dict(
        schema_version=_models.SCHEMA_VERSION,
        raw_id=f"eq-{i}", source_id="nyse-feed", venue="NYSE",
        instrument_id=f"SY{i % 3}", asset_class="stocks", event_type="QUOTE",
        exchange_time_utc_ns=1_700_000_200_000_000_000 + i * 500_000_000,
        receive_time_utc_ns=1_700_000_200_000_000_000 + i * 500_000_000 + 100_000_000,
        available_time_utc_ns=1_700_000_200_000_000_000 + i * 500_000_000 + 200_000_000,
        sequence_number=i,
        bid_price=f"{100 + i % 10}.{(i * 25) % 10000:04d}",
        ask_price=f"{100 + i % 10}.{((i * 25) % 10000) + 1:04d}",
        bid_size=f"{100 + i}.0", ask_size=f"{200 + i}.0",
        currency="USD", price_precision=4, size_precision=1,
        raw_sha256=_sha(f"eq-raw-{i}".encode()),
        manifest_sha256=_sha(b"chunk-manifest-3"),
        normalizer_version="mdp-normalizer@1",
    )
    fields.update(overrides)
    return fields


def _macro_row(i: int):
    """Macro observation dicts: a different record shape entirely."""
    return {
        "series_id": "CPI_USA",
        "observation_time_utc_ns": 1_700_000_000_000_000_000 + i * 10**12,
        "value": f"{3 + (i % 10)}.{i % 10}",
        "units": "index",
        "vintage": f"2026-0{1 + i % 8}",
    }


def build_fixtures(rows_per_fixture: int = 60):
    """Deterministic mixed-validity fixtures (valid + invalid rows, by design).

    Each of the four frozen fixture sets deliberately mixes valid rows with
    invalid shapes so the differential measures *classification* agreement,
    not just happy-path ingestion.  Invalid rows carry a ``_expect_code``
    metadata key with the frozen native reason code; it is stripped before
    validation.
    """
    trades = []
    for i in range(rows_per_fixture):
        if i % 10 == 1:  # negative quantity
            trades.append((_trade_row(i, quantity="-1.0"), "NEGATIVE_SIZE"))
        elif i % 10 == 2:  # float timestamp poisons int column
            trades.append((_trade_row(i, receive_time_utc_ns=float(
                1_700_000_000_000_000_000 + i)), "MALFORMED_SHAPE"))
        elif i % 10 == 3:  # precision violation (9 fractional digits at prec 8)
            trades.append((_trade_row(i, price="60000.123456789"), "PRECISION_LOSS"))
        elif i % 10 == 4:  # reserved event type
            trades.append((_trade_row(i, event_type="DEPTH_SNAPSHOT"),
                           "UNKNOWN_EVENT_TYPE"))
        elif i % 10 == 5:  # forbidden non-null on TRADE
            trades.append((_trade_row(i, bid_price="1.0"), "MALFORMED_SHAPE"))
        elif i % 10 == 6:  # missing required
            row = _trade_row(i)
            row.pop("quantity")
            trades.append((row, "MISSING_REQUIRED_FIELD"))
        else:
            trades.append((_trade_row(i), None))
    # duplicate raw records -> identical canonical identity -> DUPLICATE_EVENT
    dup = (_trade_row(0), "DUPLICATE_EVENT")
    trades.append(dup)

    forex = []
    for i in range(rows_per_fixture):
        if i % 10 == 3:  # crossed quote (bid >= ask)
            forex.append((_quote_row(i, bid_price="1.08100000", ask_price="1.08000000"),
                           "CROSSED_QUOTE"))
        elif i % 10 == 7:  # negative price
            forex.append((_quote_row(i, bid_price="-1.0"), "NEGATIVE_PRICE"))
        elif i % 10 == 8:  # naive datetime input
            from datetime import datetime
            forex.append((_quote_row(i, exchange_time_utc_ns=datetime(2023, 11, 14)),
                           "TIMEZONE_NAIVE_REJECTED"))
        else:
            forex.append((_quote_row(i), None))

    stocks = []
    for i in range(rows_per_fixture):
        if i % 10 == 2:  # event_id disagreement
            stocks.append((_stock_quote_row(i, event_id="0" * 64), "HASH_DISAGREEMENT"))
        elif i % 10 == 6:  # impossible time order
            stocks.append((_stock_quote_row(
                i, exchange_time_utc_ns=1_700_000_200_000_000_003 + i * 500_000_000,
                receive_time_utc_ns=1_700_000_200_000_000_000 + i * 500_000_000,
                available_time_utc_ns=1_700_000_200_000_000_000 + i * 500_000_000),
                "IMPOSSIBLE_TIME_ORDER"))
        else:
            stocks.append((_stock_quote_row(i), None))

    macro = [(_macro_row(i), "MALFORMED_SHAPE") for i in range(12)]
    return {
        "crypto trades": trades,
        "forex bid/ask": forex,
        "stocks quotes": stocks,
        "macro series": macro,
    }


# --- native reference -------------------------------------------------------

def run_native(rows_with_expect):
    """Frozen-schema validation per row; returns (results, canonical_rows).

    ``results`` maps row index -> {"accepted": bool, "codes": sorted list}.

    The native reference applies the frozen envelope schema
    (``models.validate_event``) plus the ONE semantic invariant the pandera
    schemas express beyond the envelope (CROSSED_QUOTE inside one
    venue+instrument, the same rule quality.evaluate applies) so both sides
    compare the same semantic scope.  Acceptance follows the frozen
    final-status rule: only rejection-class codes make a row unaccepted
    (DUPLICATE_EVENT is bookkeeping and stays accepted with its code
    recorded); duplicates come from a DedupeIndex over the fixture stream.
    """
    from .quality import DedupeIndex
    from . import quality as _quality
    dedupe = DedupeIndex()
    results = {}
    canonical_rows = []
    for index, (row, _expected) in enumerate(rows_with_expect):
        payload = {k: v for k, v in row.items() if not k.startswith("_")}
        try:
            canonical = _models.validate_event(payload)
            codes = []
            if canonical["event_type"] == "QUOTE":
                params = _quality.QualityParams(
                    evaluation_time_ns=canonical["exchange_time_utc_ns"],
                    staleness_threshold_ns=0,
                    instrument_registry=None,
                )
                _status, quality_codes = _quality.evaluate(canonical, {}, params)
                if "CROSSED_QUOTE" in quality_codes:
                    codes.append("CROSSED_QUOTE")
            if dedupe.seen(canonical["event_id"]):
                codes.append("DUPLICATE_EVENT")
            else:
                dedupe.add(canonical["event_id"])
            accepted = not any(_rc.is_rejection(c) for c in codes)
            results[index] = {"accepted": accepted, "codes": sorted(set(codes))}
            canonical_rows.append(canonical)
        except _models.MarketDataPlaneError as exc:
            results[index] = {"accepted": False, "codes": [exc.reason_code]}
            canonical_rows.append(None)
    return results, canonical_rows


# --- pandera schemas --------------------------------------------------------

def _decimal_precision_check(field_names, precision_map):
    """DataFrame-level row-wise check: declared precision honoured exactly."""
    def _check(df):
        ok = []
        for _, row in df.iterrows():
            good = True
            for name in field_names:
                value = row[name]
                if value is None or (isinstance(value, float) and value != value):
                    continue
                try:
                    d = Decimal(str(value))
                except Exception:
                    ok.append(False)
                    break
                digits = max(0, -d.as_tuple().exponent)
                if digits > int(row[precision_map[name]]):
                    good = False
                    break
            ok.append(good)
        import pandas as pd
        return pd.Series(ok, index=df.index)
    return _check


def _matrix_check(event_type: str):
    """Row-wise enforcement of the frozen event-type matrix."""
    matrix = _models.EVENT_TYPE_MATRIX[event_type]

    def _check(df):
        import pandas as pd
        ok = []
        for _, row in df.iterrows():
            good = True
            for name in matrix["required"]:
                value = row[name]
                if value is None or (isinstance(value, float) and value != value):
                    good = False
                    break
            if good:
                for name in matrix["forbidden_non_null"]:
                    value = row[name]
                    if value is not None and not (isinstance(value, float) and value != value):
                        good = False
                        break
            ok.append(good)
        return pd.Series(ok, index=df.index)
    return _check


def _time_order_check(df):
    import pandas as pd
    ex = df["exchange_time_utc_ns"]
    rec = df["receive_time_utc_ns"]
    av = df["available_time_utc_ns"]
    return pd.Series((ex <= rec) & (rec <= av), index=df.index)


def _event_id_check(df):
    import pandas as pd
    expected = []
    for _, row in df.iterrows():
        try:
            expected.append(_models.compute_event_id({
                "source_id": row["source_id"], "venue": row["venue"],
                "instrument_id": row["instrument_id"],
                "event_type": row["event_type"],
                "exchange_time_utc_ns": row["exchange_time_utc_ns"],
                "receive_time_utc_ns": row["receive_time_utc_ns"],
                "available_time_utc_ns": row["available_time_utc_ns"],
                "sequence_number": None if row["sequence_number"] != row["sequence_number"]
                else row["sequence_number"],
                "raw_sha256": row["raw_sha256"],
            }))
        except Exception:
            expected.append(None)
    actual = [None if (v is None or (isinstance(v, float) and v != v)) else v
              for v in df["event_id"]]
    return pd.Series([a == b for a, b in zip(actual, expected)], index=df.index)


def _event_schema(event_type: str):
    """Build a strict, coerce-free pandera schema for one event type."""
    pd = _pandas()
    pa = _pandera()
    from pandera import Check, Column

    common = {
        "schema_version": Column(str, Check.eq(_models.SCHEMA_VERSION), nullable=False),
        "event_id": Column(str, Check.str_matches(_HEX64), nullable=False),
        "raw_id": Column(str, nullable=False),
        "source_id": Column(str, nullable=False),
        "venue": Column(str, nullable=False),
        "instrument_id": Column(str, nullable=False),
        "asset_class": Column(str, nullable=False),
        "event_type": Column(str, Check.eq(event_type), nullable=False),
        "exchange_time_utc_ns": Column("Int64", Check.ge(0), nullable=False),
        "receive_time_utc_ns": Column("Int64", Check.ge(0), nullable=False),
        "available_time_utc_ns": Column("Int64", Check.ge(0), nullable=False),
        "sequence_number": Column("Int64", Check.ge(0), nullable=True),
        "side": Column(str, Check.isin(["buy", "sell"]), nullable=True),
        "currency": Column(str, nullable=True),
        "price_precision": Column("Int64", Check.ge(0), nullable=False),
        "size_precision": Column("Int64", Check.ge(0), nullable=False),
        "quality_status": Column(str, Check.isin(list(_models.QUALITY_STATUSES)),
                                 nullable=False),
        "reason_codes": Column(object, nullable=False),
        "raw_sha256": Column(str, Check.str_matches(_HEX64), nullable=False),
        "manifest_sha256": Column(str, Check.str_matches(_HEX64), nullable=True),
        "normalizer_version": Column(str, nullable=False),
    }
    if event_type == "TRADE":
        common["price"] = Column(str, Check.str_matches(_FIXED_POINT), nullable=False)
        common["quantity"] = Column(str, Check.str_matches(_FIXED_POINT), nullable=False)
        common["bid_price"] = Column(str, nullable=True)
        common["ask_price"] = Column(str, nullable=True)
        common["bid_size"] = Column(str, nullable=True)
        common["ask_size"] = Column(str, nullable=True)
        price_cols, size_cols = ("price",), ("quantity",)
    else:
        common["price"] = Column(str, nullable=True)
        common["quantity"] = Column(str, nullable=True)
        common["bid_price"] = Column(str, Check.str_matches(_FIXED_POINT), nullable=False)
        common["ask_price"] = Column(str, Check.str_matches(_FIXED_POINT), nullable=False)
        common["bid_size"] = Column(str, Check.str_matches(_FIXED_POINT), nullable=False)
        common["ask_size"] = Column(str, Check.str_matches(_FIXED_POINT), nullable=False)
        price_cols = ("bid_price", "ask_price")
        size_cols = ("bid_size", "ask_size")

    df_checks = [
        Check(_time_order_check, error="mdp_time_order"),
        Check(_event_id_check, error="mdp_event_id"),
        Check(_matrix_check(event_type), error=f"mdp_matrix_{event_type}"),
        Check(_decimal_precision_check(price_cols,
                                       {"price": "price_precision",
                                        "bid_price": "price_precision",
                                        "ask_price": "price_precision"}),
              error="mdp_price_precision"),
        Check(_decimal_precision_check(size_cols,
                                       {"quantity": "size_precision",
                                        "bid_size": "size_precision",
                                        "ask_size": "size_precision"}),
              error="mdp_size_precision"),
    ]
    if event_type == "QUOTE":
        def _no_cross(df):
            import pandas as pd
            bid = df["bid_price"].map(lambda v: Decimal(str(v)) if isinstance(v, str) else None)
            ask = df["ask_price"].map(lambda v: Decimal(str(v)) if isinstance(v, str) else None)
            ok = [b is None or a is None or b < a for b, a in zip(bid, ask)]
            return pd.Series(ok, index=df.index)
        df_checks.append(Check(_no_cross, error="mdp_no_crossed_quote"))

    return pa.DataFrameSchema(common, checks=df_checks, strict=True, coerce=False)


def trade_schema():
    return _event_schema("TRADE")


def quote_schema():
    return _event_schema("QUOTE")


# --- DataFrame ingestion at the boundary -----------------------------------

_INT_COLUMNS = ("exchange_time_utc_ns", "receive_time_utc_ns", "available_time_utc_ns",
                "sequence_number", "price_precision", "size_precision")
_STR_COLUMNS = ("schema_version", "event_id", "raw_id", "source_id", "venue",
                "instrument_id", "asset_class", "event_type", "price", "quantity",
                "side", "bid_price", "ask_price", "bid_size", "ask_size", "currency",
                "quality_status", "raw_sha256", "manifest_sha256", "normalizer_version")


def events_to_dataframe(rows):
    """Ingest raw event dicts at the batch boundary, minimally typed.

    Envelope defaults are filled the same way the native validator fills them
    (schema_version, quality_status=QUARANTINED, reason_codes=[]) so the
    pandera boundary sees the same normalised envelope — this is ingestion
    normalisation, not validation coercion.  Nullable int columns are typed
    ``Int64`` ONLY when every non-null value is a true int (bools excluded);
    nullable str columns are typed ``str`` only when every non-null value is a
    str.  When a poisoned row prevents typing, the column keeps the
    pandas-inferred dtype so pandera's strict dtype check (never silent
    coercion) records the mismatch.  No validated value is ever coerced.
    """
    pd = _pandas()
    normalised = []
    for row in rows:
        record = dict(row)
        if record.get("schema_version") is None:
            record["schema_version"] = _models.SCHEMA_VERSION
        if record.get("quality_status") is None:
            record["quality_status"] = "QUARANTINED"
        if record.get("reason_codes") is None:
            record["reason_codes"] = []
        normalised.append(record)
    frame = pd.DataFrame(normalised, columns=list(_models.ENVELOPE_FIELDS))
    typed = {}
    for column in frame.columns:
        series = frame[column]
        values = list(series.tolist())
        # a value is "typeable null" if it is None or NaN; typeable ints are
        # true ints (bool excluded); typeable strings are true strs
        def _is_null(v):
            return v is None or (isinstance(v, float) and v != v)
        if column in _INT_COLUMNS and all(
                _is_null(v) or type(v) is int for v in values):
            typed[column] = series.astype("Int64")
        elif column in _STR_COLUMNS and all(
                _is_null(v) or isinstance(v, str) for v in values):
            typed[column] = series.astype("str")
        else:
            typed[column] = series
    return pd.DataFrame(typed, columns=list(_models.ENVELOPE_FIELDS))


# --- pandera failure -> MDP reason attribution ------------------------------
#
# NOTE on unique=: pandera's schema-level `unique=` was deliberately NOT used.
# The frozen plane treats DUPLICATE_EVENT as bookkeeping (final status stays
# VALID unless a rejection code is present), so a hard pandera duplicate
# rejection would contradict frozen semantics; duplicates are detected by
# quality.DedupeIndex on the native side and recorded as an attribution note.

_CHECK_TO_CODE = (
    ("mdp_event_id", "HASH_DISAGREEMENT"),
    ("mdp_matrix_TRADE", "MALFORMED_SHAPE"),
    ("mdp_matrix_QUOTE", "MALFORMED_SHAPE"),
    ("mdp_price_precision", "PRECISION_LOSS"),
    ("mdp_size_precision", "PRECISION_LOSS"),
    ("mdp_no_crossed_quote", "CROSSED_QUOTE"),
    ("mdp_time_order", "IMPOSSIBLE_TIME_ORDER"),
)


def attribute_code(failure_case_row) -> str:
    """Map one pandera failure case to the closest frozen reason code.

    Context-aware: DataFrame-level check failures are reported once per
    column with the row's values, so their ``column`` field is incidental —
    only ``Column``-context failures map by column.  Anything unmapped is
    recorded as UNMAPPED (evidence of an attribution gap, never silently
    accepted).
    """
    context = str(failure_case_row.get("schema_context"))
    column = str(failure_case_row.get("column"))
    check = str(failure_case_row.get("check"))

    for needle, code in _CHECK_TO_CODE:  # custom mdp_* checks first
        if needle in check:
            return code
    if context == "Column":
        if column == "event_type":
            return "UNKNOWN_EVENT_TYPE"
        if check == "not_nullable":
            return "MISSING_REQUIRED_FIELD"
        if check.startswith("dtype("):
            return "MALFORMED_SHAPE"
        if "str_matches" in check:
            return "MALFORMED_SHAPE"
        if "greater_than_or_equal_to" in check:
            return "MALFORMED_SHAPE"
        if "equal_to" in check:
            return "MALFORMED_SHAPE"
        if "isin(" in check:
            return "MALFORMED_SHAPE"
    return "UNMAPPED"


def run_pandera(rows_with_expect):
    """Validate the fixture through the pandera boundary.

    Returns {"ingested": bool, "ingest_error": str|None, "results": {...},
    "unmapped_checks": [...]} where results maps row index -> accepted bool.
    Failure cases carrying a row index reject that row; failure cases without
    a row index (column dtype mismatches, strict column-set errors) fail the
    batch at the boundary and therefore reject EVERY row — recorded as such.
    """
    pa = _pandera()
    rows = [{k: v for k, v in row.items() if not k.startswith("_")}
            for row, _ in rows_with_expect]
    if not rows:
        return {"ingested": True, "ingest_error": None, "results": {},
                "unmapped_checks": []}
    try:
        events_to_dataframe(rows)
    except Exception as exc:  # ingest failure is itself recorded evidence
        return {"ingested": False, "ingest_error": f"{type(exc).__name__}: {exc}",
                "results": None, "unmapped_checks": []}

    schemas = {"TRADE": trade_schema, "QUOTE": quote_schema}
    results = {i: {"accepted": True, "codes": [], "pandera": []}
               for i in range(len(rows))}
    unmapped = []

    by_type = {}
    for index, row in enumerate(rows):
        event_type = row.get("event_type")
        key = event_type if event_type in ("TRADE", "QUOTE") else "unknown"
        by_type.setdefault(key, []).append(index)

    for key, indices in by_type.items():
        if key == "unknown":
            for index in indices:
                results[index] = {"accepted": False,
                                  "codes": ["UNKNOWN_EVENT_TYPE"],
                                  "pandera": ["schema-selection"]}
            continue
        sub_rows = [rows[i] for i in indices]
        try:
            schemas[key]().validate(events_to_dataframe(sub_rows), lazy=True)
        except pa.errors.SchemaErrors as exc:
            for _, case in exc.failure_cases.iterrows():
                code = attribute_code(case)
                if code == "UNMAPPED":
                    unmapped.append({k: str(v) for k, v in case.items()})
                    continue
                index = case.get("index")
                if isinstance(index, (int,)) and not isinstance(index, bool) \
                        and 0 <= int(index) < len(indices):
                    hit = indices[int(index)]
                    entry = results[hit]
                    entry["accepted"] = False
                    if code not in entry["codes"]:
                        entry["codes"].append(code)
                    entry["pandera"].append(str(case.get("check")))
                else:
                    # frame/column-level failure: the boundary rejects the batch
                    for hit in indices:
                        entry = results[hit]
                        entry["accepted"] = False
                        if code not in entry["codes"]:
                            entry["codes"].append(code)
                        entry["pandera"].append(str(case.get("check")))
        except Exception as exc:  # non-lazy failure mode: batch rejected
            for hit in indices:
                results[hit] = {"accepted": False, "codes": ["MALFORMED_SHAPE"],
                                "pandera": [f"{type(exc).__name__}: {exc}"]}

    return {"ingested": True, "ingest_error": None, "results": results,
            "unmapped_checks": unmapped}


# --- differential + timing --------------------------------------------------

def _compare_mode(rows_with_expect):
    """One accepted/rejected comparison pass over a given row list."""
    native, _ = run_native(rows_with_expect)
    pandera = run_pandera(rows_with_expect)
    row_count = len(rows_with_expect)

    if not pandera.get("ingested"):
        return {
            "rows": row_count,
            "native_rejected": sorted(i for i, r in native.items()
                                      if not r["accepted"]),
            "pandera_rejected": None,
            "same_row_sets": False,
            "same_reason_attribution": False,
            "attribution_gaps": [],
            "ingest_error": pandera.get("ingest_error"),
            "unmapped_checks": [],
        }

    native_rejected = sorted(i for i, r in native.items() if not r["accepted"])
    pandera_rejected = sorted(i for i, r in pandera["results"].items()
                              if not r["accepted"])
    same_sets = native_rejected == pandera_rejected

    attribution_gaps = []
    for index in range(row_count):
        native_rejection_codes = {c for c in native[index]["codes"]
                                  if _rc.is_rejection(c)}
        pandera_codes = set(pandera["results"][index]["codes"])
        if native_rejection_codes != pandera_codes:
            attribution_gaps.append({
                "index": index,
                "native": sorted(native_rejection_codes),
                "pandera": sorted(pandera_codes),
            })
    return {
        "rows": row_count,
        "native_rejected": native_rejected,
        "pandera_rejected": pandera_rejected,
        "same_row_sets": same_sets,
        "same_reason_attribution": not attribution_gaps,
        "attribution_gaps": attribution_gaps[:20],
        "ingest_error": None,
        "unmapped_checks": pandera["unmapped_checks"][:20],
    }


def differential(rows_with_expect):
    """Compare native vs pandera classification on a fixture.

    Two modes are recorded per fixture:

    * ``raw_boundary`` — the raw provider-shaped rows exactly as ingested.
      A single type-poisoned row (e.g. one float timestamp) makes the whole
      pandera batch fail at the strict dtype boundary, which is the central
      batch-vs-row evidence for the adoption decision.
    * ``canonical_control`` — the native-canonical form of the rows native
      accepted, isolating classification agreement from ingestion typing.
    """
    _, canonical_rows = run_native(rows_with_expect)
    raw = _compare_mode(rows_with_expect)
    control_rows = [(c, None) for c in canonical_rows if c is not None]
    if control_rows:
        control = _compare_mode(control_rows)
    else:
        control = {"rows": 0, "native_rejected": [], "pandera_rejected": None,
                   "same_row_sets": False, "same_reason_attribution": False,
                   "attribution_gaps": [],
                   "ingest_error": "no canonically-valid rows in fixture "
                                   "(control vacuous for this fixture)",
                   "unmapped_checks": []}
    return {
        "raw_boundary": raw,
        "canonical_control": control,
        "duplicate_note": ("DUPLICATE_EVENT is frozen bookkeeping (quality "
                           "DedupeIndex), not a schema rejection; pandera "
                           "unique= intentionally unused"),
    }


def _time_once_native(rows):
    start = time.perf_counter()
    for row, _ in rows:
        payload = {k: v for k, v in row.items() if not k.startswith("_")}
        try:
            _models.validate_event(payload)
        except _models.MarketDataPlaneError:
            pass
    return time.perf_counter() - start


def _time_once_pandera(rows_with_expect):
    rows = [{k: v for k, v in row.items() if not k.startswith("_")}
            for row, _ in rows_with_expect]
    schemas = {"TRADE": trade_schema, "QUOTE": quote_schema}
    start = time.perf_counter()
    frame = events_to_dataframe(rows)
    for event_type, schema_fn in schemas.items():
        mask = frame["event_type"] == event_type
        if mask.any():
            try:
                schema_fn().validate(frame[mask], lazy=True)
            except Exception:
                pass
    return time.perf_counter() - start


def measure_timing(rows_with_expect):
    """2 warmups + 5 measured repeats; returns medians and the ratio."""
    native = []
    pandera = []
    for _ in range(TIMING_WARMUPS):
        _time_once_native(rows_with_expect)
        _time_once_pandera(rows_with_expect)
    for _ in range(TIMING_REPEATS):
        native.append(_time_once_native(rows_with_expect))
        pandera.append(_time_once_pandera(rows_with_expect))
    native_median = statistics.median(native)
    pandera_median = statistics.median(pandera)
    ratio = pandera_median / native_median if native_median > 0 else float("inf")
    return {
        "repeats": TIMING_REPEATS,
        "native_median_s": native_median,
        "pandera_median_s": pandera_median,
        "pandera_over_native_ratio": ratio,
        "over_20pct_regression": ratio > 1.2,
    }


def _row_signature(row):
    payload = {k: v for k, v in row.items() if not k.startswith("_")}
    return repr(sorted(payload.items(), key=lambda kv: kv[0]))


def check_determinism_vs_row_order(rows_with_expect):
    """Failure sets (by row signature) must not depend on row order."""
    native_a, _ = run_native(rows_with_expect)
    shuffled = list(reversed(rows_with_expect))
    native_b, _ = run_native(shuffled)
    pandera_a = run_pandera(rows_with_expect)
    pandera_b = run_pandera(shuffled)

    def failing(results, rows):
        return {(_row_signature(rows[i][0])) for i, r in results.items()
                if not r["accepted"]}

    native_stable = failing(native_a, rows_with_expect) == \
        failing(native_b, shuffled)
    if not pandera_a.get("ingested") or not pandera_b.get("ingested"):
        return {"native_stable": native_stable,
                "pandera_stable": None,
                "deterministic": native_stable}
    pandera_stable = failing(pandera_a["results"], rows_with_expect) == \
        failing(pandera_b["results"], shuffled)
    return {"native_stable": native_stable, "pandera_stable": pandera_stable,
            "deterministic": native_stable and bool(pandera_stable)}


def check_no_mutation(rows_with_expect):
    """Both paths must leave the input dicts untouched."""
    before = copy.deepcopy(rows_with_expect)
    run_native(rows_with_expect)
    run_pandera(rows_with_expect)
    return rows_with_expect == before


def check_dtype_preservation(rows_with_expect):
    """Timestamps stay int ns; decimal strings never become floats."""
    rows = [{k: v for k, v in row.items() if not k.startswith("_")}
            for row, _ in rows_with_expect]
    frame = events_to_dataframe(rows)
    dtype_map = {c: str(frame[c].dtype) for c in frame.columns}
    tz_loss = any("datetime" in dt for dt in dtype_map.values())
    decimal_to_float = any(
        dtype_map[c] in ("float64", "float32")
        for c in ("price", "quantity", "bid_price", "ask_price",
                  "bid_size", "ask_size"))
    return {"dtype_map": dtype_map, "timestamp_timezone_loss": tz_loss,
            "decimal_to_float": decimal_to_float}


def collect_evidence(rows_per_fixture: int = 60):
    """Full measured evidence bundle; A1 decides adoption at P5A."""
    fixtures = build_fixtures(rows_per_fixture)
    per_fixture = {}
    for name, rows in fixtures.items():
        entry = differential(rows)
        entry["timing"] = measure_timing(rows)
        entry["no_input_mutation"] = check_no_mutation(rows)
        entry["dtype_preservation"] = check_dtype_preservation(rows)
        per_fixture[name] = entry

    determinism = {}
    for name, rows in fixtures.items():
        determinism[name] = check_determinism_vs_row_order(rows)

    controls = []
    for e in per_fixture.values():
        control = e["canonical_control"]
        if control["rows"] == 0:
            continue  # vacuous: fixture had no canonically-valid rows (macro)
        controls.append(control["same_row_sets"]
                        and control["same_reason_attribution"])
    controls_agree = bool(controls) and all(controls)
    raw_agrees = all(
        e["raw_boundary"]["same_row_sets"]
        and e["raw_boundary"]["same_reason_attribution"]
        for e in per_fixture.values())
    criterion_1 = {
        # frozen wording: "identical accepted/rejected row sets and reason
        # attribution vs native frozen schema".  The frozen spike scope is the
        # batch/DataFrame INGESTION boundary, so the criterion is measured on
        # the raw rows; the canonical-control result is recorded as
        # supplementary evidence showing where pandera CAN agree (canonical,
        # uniformly-typed batches).
        "raw_boundary": raw_agrees,
        "canonical_control": controls_agree,
        "met": bool(controls_agree and raw_agrees),
    }
    # supplemental large-batch timing (pure-perf context for the ratio)
    large = [(row, None) for row in (_trade_row(i) for i in range(2000))]
    large_timing = measure_timing(large)
    timing_detail = {
        name: {"over_20pct": e["timing"]["over_20pct_regression"],
               "ratio": e["timing"]["pandera_over_native_ratio"]}
        for name, e in per_fixture.items()}
    timing_detail["large_batch_2000_trades"] = {
        "over_20pct": large_timing["over_20pct_regression"],
        "ratio": large_timing["pandera_over_native_ratio"]}
    criteria = {
        ADOPT_REQUIRES_ALL[0]: criterion_1,
        ADOPT_REQUIRES_ALL[1]: not any(
            e["dtype_preservation"]["timestamp_timezone_loss"]
            for e in per_fixture.values()),
        ADOPT_REQUIRES_ALL[2]: not any(
            e["dtype_preservation"]["decimal_to_float"]
            for e in per_fixture.values()),
        ADOPT_REQUIRES_ALL[3]: all(d["deterministic"] for d in determinism.values()),
        ADOPT_REQUIRES_ALL[4]: all(e["no_input_mutation"] for e in per_fixture.values()),
        # "no UNEXPLAINED regression over 20%": the measured ratios are all
        # far over 20% and are EXPLAINED (per-row python native loop vs batch
        # schema machinery on small fixtures) — A1 judges "unexplained";
        # measured facts recorded, met-flag reflects the raw 20% bound.
        ADOPT_REQUIRES_ALL[5]: {
            "met": not any(d["over_20pct"] for d in timing_detail.values()),
            "detail": timing_detail,
        },
        ADOPT_REQUIRES_ALL[6]: True,  # enforced by tests/test_mdp_models.py subprocess check
    }
    bool_criteria = [v for v in criteria.values() if isinstance(v, bool)]
    failing = [k for k, v in criteria.items()
               if isinstance(v, bool) and not v]
    if not criterion_1["met"]:
        failing.append(ADOPT_REQUIRES_ALL[0])
    if not criteria[ADOPT_REQUIRES_ALL[5]]["met"]:
        failing.append(ADOPT_REQUIRES_ALL[5])
    return {
        "verdict_authority": "A1 at P5A; this module records measured evidence only",
        "candidate_verdict_if_a1_follows_the_frozen_rule": (
            "ADOPTED" if all(bool_criteria) and not failing else FAILURE_VERDICT),
        "failing_criteria": sorted(set(failing)),
        "per_fixture": per_fixture,
        "determinism_vs_row_order": determinism,
        "timing_large_batch_2000_trades": large_timing,
        "criteria_checklist": criteria,
    }
