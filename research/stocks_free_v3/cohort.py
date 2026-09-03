"""11-ETF cohort verification: schema, corporate actions, TR inputs, calendar.

Owner: lane A3, STOCKS-FREE-V3 P1 (PLAN_stocks.md section 9 A3, deliverable
2: "Verify all 11 ETFs, raw OHLCV schema, corporate actions, issuer
total-return inputs and regular-session calendar").

S1 discipline: structural checks run over the WHOLE file (row shape,
ordering, parseability — no S1 price is exposed or recorded), but every
VALUE-LEVEL check (OHLC sanity, TR reconstruction) is restricted to rows
dated at or before S0 end.  The single deliberate exception is the five
2025-12-05 2:1 split events: their verification reads the closes on
2025-12-04/2025-12-05 only to re-derive the close ratio already recorded in
the V2 control artifact (A7-approved corporate-action provenance); no S1
return series is computed, returned, or recorded.

Checks (PASS/FAIL/NOT_RUN vocabulary, fail-closed):

* ``status_and_meta``        — payload status ok, symbol/interval/exchange identity;
* ``row_schema``             — exactly the six raw OHLCV keys per row, ISO
                               datetimes, strictly descending, unique;
* ``numeric_parse``          — OHLCV fields parse to finite floats;
* ``s0_bar_sanity``          — S0 rows only: high >= max(open, close) >=
                               min(open, close) >= low > 0, volume >= 0;
* ``split_events``           — exactly the five pinned 2:1 events
                               (XLK/XLE/XLY/XLU/XLB, 2025-12-05), and the
                               measured close ratio matches the pinned ratio;
* ``distribution_inputs``    — issuer distribution records present and dated
                               for every cohort member;
* ``tr_inputs_reconstruct``  — issuer-TR daily returns reconstruct finitely
                               over S0-truncated closes for every member;
* ``calendar_regular_v1``    — injected calendar digest matches the frozen
                               pin, partition boundary dates are sessions,
                               and the S0 span contains the expected count
                               of regular sessions.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence

from research.assets.common.contracts import canonical_json
from research.stocks_free_v3.authority import (
    CALENDAR_DIGEST,
    COHORT_SYMBOLS,
    PINNED_CLOSE_RATIOS,
    S0_END,
    S1_START,
    SPLIT_EFFECTIVE_DATE,
    SPLIT_FACTOR,
    SPLIT_PROVENANCE_DATES,
    SPLIT_SYMBOLS,
    WARMUP_START,
)
from research.stocks_free_v3.benchmarks import BenchmarkError, issuer_total_return_daily
from research.stocks_free_v3.isolation import S0WindowPolicy, SealedSnapshotReader

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_NOT_RUN = "NOT_RUN"

#: The Twelve Data raw-bar row schema (exactly these keys, string values).
ROW_KEYS = frozenset({"datetime", "open", "high", "low", "close", "volume"})

RATIO_TOLERANCE = 1e-3

_MAX_FINDINGS_IN_DETAIL = 8


@dataclass(frozen=True)
class CohortCheck:
    """One cohort verification check."""

    name: str
    verdict: str
    detail: str

    def to_payload(self) -> dict[str, Any]:
        return {"name": self.name, "verdict": self.verdict, "detail": self.detail}


@dataclass(frozen=True)
class CohortVerificationReport:
    """Fail-closed report across the 11-ETF cohort."""

    symbol_reports: Mapping[str, tuple[CohortCheck, ...]]
    cross_checks: tuple[CohortCheck, ...]

    @property
    def checks(self) -> tuple[CohortCheck, ...]:
        out: list[CohortCheck] = []
        for symbol in sorted(self.symbol_reports):
            out.extend(self.symbol_reports[symbol])
        out.extend(self.cross_checks)
        return tuple(out)

    @property
    def verdict(self) -> str:
        verdicts = {c.verdict for c in self.checks}
        if VERDICT_FAIL in verdicts:
            return VERDICT_FAIL
        if VERDICT_NOT_RUN in verdicts:
            return VERDICT_NOT_RUN
        return VERDICT_PASS

    def to_payload(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "symbols": {
                s: [c.to_payload() for c in checks]
                for s, checks in sorted(self.symbol_reports.items())
            },
            "cross_checks": [c.to_payload() for c in self.cross_checks],
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_payload())


# --- per-symbol checks ---------------------------------------------------------- #


def _parse_iso(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def verify_symbol_payload(
    payload: Mapping[str, Any],
    symbol: str,
    *,
    s0_end: date = S0_END,
) -> tuple[CohortCheck, ...]:
    """Raw OHLCV schema checks for one symbol's staging payload.

    Structural checks run over all rows; value-level (OHLC sanity) checks
    are restricted to rows dated on or before ``s0_end`` so no S1 price is
    examined.  Digits of prices are never recorded — findings name dates and
    relationships, never levels.
    """
    checks: list[CohortCheck] = []
    status = payload.get("status")
    checks.append(
        CohortCheck(
            name="status_and_meta",
            verdict=VERDICT_PASS if status == "ok" else VERDICT_FAIL,
            detail=f"payload status={status!r}",
        )
    )
    meta = payload.get("meta") or {}
    meta_ok = (
        meta.get("symbol") == symbol
        and meta.get("interval") == "1day"
        and bool(meta.get("exchange"))
        and bool(meta.get("mic_code"))
        and meta.get("currency") == "USD"
    )
    checks.append(
        CohortCheck(
            name="symbol_identity",
            verdict=VERDICT_PASS if meta_ok else VERDICT_FAIL,
            detail=(
                f"symbol={meta.get('symbol')!r} interval={meta.get('interval')!r} "
                f"exchange={meta.get('exchange')!r}/{meta.get('mic_code')!r} "
                f"currency={meta.get('currency')!r}"
            ),
        )
    )
    values = payload.get("values")
    if not isinstance(values, list) or not values:
        return tuple(
            checks
            + [
                CohortCheck(
                    name="row_schema",
                    verdict=VERDICT_FAIL,
                    detail="values is empty or not a list",
                )
            ]
        )
    schema_failures: list[str] = []
    numeric_failures: list[str] = []
    dates: list[date] = []
    for row in values:
        if not isinstance(row, dict) or set(row.keys()) != ROW_KEYS:
            schema_failures.append(f"row keys {sorted(row.keys()) if isinstance(row, dict) else row!r}")
            continue
        parsed = _parse_iso(str(row["datetime"]))
        if parsed is None:
            schema_failures.append(f"unparsable datetime {row['datetime']!r}")
            continue
        dates.append(parsed)
        for field in ("open", "high", "low", "close", "volume"):
            try:
                number = float(row[field])
            except (TypeError, ValueError):
                numeric_failures.append(f"{parsed.isoformat()} {field} unparsable")
                continue
            if not math.isfinite(number):
                numeric_failures.append(f"{parsed.isoformat()} {field} non-finite")
    descending = all(a > b for a, b in zip(dates, dates[1:]))
    if not descending:
        schema_failures.append("datetimes not strictly descending/unique")
    checks.append(
        CohortCheck(
            name="row_schema",
            verdict=VERDICT_PASS if not schema_failures else VERDICT_FAIL,
            detail=(
                f"{len(values)} rows, strictly descending ISO datetimes"
                if not schema_failures
                else "; ".join(schema_failures[:_MAX_FINDINGS_IN_DETAIL])
            ),
        )
    )
    checks.append(
        CohortCheck(
            name="numeric_parse",
            verdict=VERDICT_PASS if not numeric_failures else VERDICT_FAIL,
            detail=(
                "all OHLCV fields parse to finite floats"
                if not numeric_failures
                else "; ".join(numeric_failures[:_MAX_FINDINGS_IN_DETAIL])
            ),
        )
    )

    sanity_failures: list[str] = []
    s0_rows = 0
    first_row = dates[-1] if dates else None
    last_row = dates[0] if dates else None
    for row in values:
        if not isinstance(row, dict) or set(row.keys()) != ROW_KEYS:
            continue
        parsed = _parse_iso(str(row["datetime"]))
        if parsed is None or parsed > s0_end:
            continue  # value-level checks are S0-bounded only
        try:
            o, h, low, c = (float(row[k]) for k in ("open", "high", "low", "close"))
            v = float(row["volume"])
        except (TypeError, ValueError):
            continue  # numeric_parse already records unparsable fields
        s0_rows += 1
        if not (h >= max(o, c) >= min(o, c) >= low > 0.0):
            sanity_failures.append(f"{parsed.isoformat()} OHLC relationship violated")
        if v < 0.0:
            sanity_failures.append(f"{parsed.isoformat()} negative volume")
    checks.append(
        CohortCheck(
            name="s0_bar_sanity",
            verdict=VERDICT_PASS if not sanity_failures else VERDICT_FAIL,
            detail=(
                f"{s0_rows} S0 rows sane (values not recorded; S1 rows "
                "structurally present but deliberately not value-checked)"
                if not sanity_failures
                else "; ".join(sanity_failures[:_MAX_FINDINGS_IN_DETAIL])
            ),
        )
    )
    checks.append(
        CohortCheck(
            name="coverage_span",
            verdict=VERDICT_PASS if s0_rows > 0 else VERDICT_FAIL,
            detail=(
                f"first row {first_row.isoformat()}, last row "
                f"{last_row.isoformat()}, {s0_rows} rows at or before S0 end"
                if first_row and last_row
                else "no parsable rows"
            ),
        )
    )
    return tuple(checks)


# --- cross checks ---------------------------------------------------------------- #


def verify_split_events(
    raw_closes: Mapping[str, Mapping[str, float]],
) -> CohortCheck:
    """The five pinned 2025-12-05 2:1 splits re-derive from raw closes.

    ``raw_closes[s]["2025-12-04"]`` / ``["2025-12-05"]`` must exist for the
    five split symbols and the measured ratio must match the pinned V2
    control ratio.  This reads exactly two closes per affected symbol — the
    dates of the pinned corporate-action provenance — and computes a ratio
    only; no S1 return series is formed.
    """
    problems: list[str] = []
    for symbol, expected_ratio in PINNED_CLOSE_RATIOS.items():
        series = raw_closes.get(symbol) or {}
        pre = series.get("2025-12-04")
        post = series.get("2025-12-05")
        if pre is None or post is None or pre <= 0.0:
            problems.append(f"{symbol}: closes on 2025-12-04/05 unavailable")
            continue
        measured = post / pre
        if abs(measured - expected_ratio) > RATIO_TOLERANCE:
            problems.append(
                f"{symbol}: measured split ratio {measured:.4f} deviates from "
                f"pinned {expected_ratio:.4f}"
            )
    return CohortCheck(
        name="split_events",
        verdict=VERDICT_FAIL if problems else VERDICT_PASS,
        detail=(
            f"five {SPLIT_FACTOR:.0f}:1 splits on {SPLIT_EFFECTIVE_DATE} "
            f"({', '.join(SPLIT_SYMBOLS)}) re-derive within tolerance "
            f"{RATIO_TOLERANCE}; two closes per affected symbol read purely "
            "as corporate-action provenance (dates inside sealed S1), no S1 "
            "return formed"
            if not problems
            else "; ".join(problems)
        ),
    )


def verify_distribution_inputs(
    distributions: Mapping[str, Mapping[str, float]],
    symbols: Sequence[str] = COHORT_SYMBOLS,
) -> CohortCheck:
    """Issuer distribution records exist and are dated for every member."""
    members = tuple(symbols)
    missing: list[str] = []
    empty: list[str] = []
    unparsable: list[str] = []
    for symbol in members:
        records = distributions.get(symbol)
        if records is None:
            missing.append(symbol)
            continue
        if not records:
            empty.append(symbol)
            continue
        for key in records:
            if _parse_iso(str(key)) is None:
                unparsable.append(f"{symbol}:{key}")
    problems = (
        (["missing: " + ",".join(missing)] if missing else [])
        + (["empty: " + ",".join(empty)] if empty else [])
        + (["unparsable: " + ",".join(unparsable[:5])] if unparsable else [])
    )
    return CohortCheck(
        name="distribution_inputs",
        verdict=VERDICT_FAIL if problems else VERDICT_PASS,
        detail=(
            "issuer distribution records present and dated for all "
            f"{len(members)} cohort members"
            if not problems
            else "; ".join(problems)
        ),
    )


def verify_tr_inputs(
    raw_closes: Mapping[str, Mapping[str, float]],
    distributions: Mapping[str, Mapping[str, float]],
    split_factors: Mapping[str, Mapping[str, float]],
    symbols: Sequence[str] = COHORT_SYMBOLS,
    *,
    s0_end: date = S0_END,
) -> CohortCheck:
    """Issuer-TR daily returns reconstruct finitely over S0-truncated closes."""
    problems: list[str] = []
    checked = 0
    for symbol in symbols:
        series = {
            d: c for d, c in (raw_closes.get(symbol) or {}).items() if d <= s0_end.isoformat()
        }
        if len(series) < 2:
            problems.append(f"{symbol}: fewer than two S0 observations")
            continue
        try:
            dates, returns = issuer_total_return_daily(
                series,
                {
                    d: v
                    for d, v in (distributions.get(symbol) or {}).items()
                    if d <= s0_end.isoformat()
                },
                split_factors.get(symbol, {}),
            )
        except BenchmarkError as exc:
            problems.append(f"{symbol}: {exc}")
            continue
        bad = [d for d, r in zip(dates, returns) if not math.isfinite(r)]
        if bad:
            problems.append(f"{symbol}: {len(bad)} non-finite TR returns (first {bad[0]})")
            continue
        checked += len(dates)
    return CohortCheck(
        name="tr_inputs_reconstruct",
        verdict=VERDICT_FAIL if problems else VERDICT_PASS,
        detail=(
            f"issuer-TR reconstruction finite for all members "
            f"({checked} S0 daily returns checked; S1 never reconstructed)"
            if not problems
            else "; ".join(problems)
        ),
    )


def verify_calendar(calendar: Any, *, s0_sessions_expected: int | None = None) -> CohortCheck:
    """Injected calendar digest, boundary sessions and S0 session count.

    ``calendar`` must expose ``calendar_manifest_digest`` and
    ``is_session_day`` (the shared ``USEquityRegularCalendar`` satisfies
    both); it is injected, never reimplemented here.
    """
    try:
        raw_digest = calendar.calendar_manifest_digest
        digest = raw_digest() if callable(raw_digest) else raw_digest
        is_session = calendar.is_session_day
    except AttributeError:
        return CohortCheck(
            name="calendar_regular_v1",
            verdict=VERDICT_NOT_RUN,
            detail="no calendar injected; the official calendar cannot be assumed",
        )
    problems: list[str] = []
    if digest != CALENDAR_DIGEST:
        problems.append(f"calendar digest {digest} != frozen pin {CALENDAR_DIGEST}")
    boundaries = {
        "warmup_start": WARMUP_START,
        "s0_start": S0WindowPolicy().s0_start,
        "s0_end": S0WindowPolicy().s0_end,
        "s1_start": S1_START,
    }
    for label, day in boundaries.items():
        if not is_session(day):
            problems.append(f"{label} ({day.isoformat()}) is not a regular session")
    if s0_sessions_expected is not None:
        policy = S0WindowPolicy()
        count = sum(
            1
            for offset in range((policy.s0_end - policy.s0_start).days + 1)
            if is_session(date.fromordinal(policy.s0_start.toordinal() + offset))
        )
        if count != s0_sessions_expected:
            problems.append(
                f"S0 session count {count} != declared {s0_sessions_expected}"
            )
    return CohortCheck(
        name="calendar_regular_v1",
        verdict=VERDICT_FAIL if problems else VERDICT_PASS,
        detail=(
            f"calendar digest matches the frozen pin; boundary dates "
            f"{sorted(d.isoformat() for d in boundaries.values())} are regular sessions"
            if not problems
            else "; ".join(problems)
        ),
    )


# --- full verification over the real snapshot (S0-bounded) ----------------------- #


def verify_real_cohort(
    reader: SealedSnapshotReader,
    distributions: Mapping[str, Mapping[str, float]],
    split_factors: Mapping[str, Mapping[str, float]],
    calendar: Any,
    *,
    symbols: Sequence[str] = COHORT_SYMBOLS,
) -> CohortVerificationReport:
    """Verify the REAL staged cohort through the sealed S0-only reader.

    Every symbol file is hash-pinned and read through the
    :class:`SealedSnapshotReader`.  Two reads happen per symbol:

    * an S0-truncated close map (value checks, TR reconstruction) — post-S0
      rows are dropped by the reader before anything sees them;
    * a pinned full-text read used ONLY for the structural schema checks
      (row shape, ordering, parseability — findings name dates and
      relationships, never S1 price levels).

    For the five split symbols the reader additionally returns exactly the
    two pinned provenance closes (2025-12-04/05) used by
    :func:`verify_split_events`.
    """
    symbol_reports: dict[str, tuple[CohortCheck, ...]] = {}
    raw_closes: dict[str, dict[str, float]] = {}
    policy = S0WindowPolicy()
    for symbol in symbols:
        relpath = f"{symbol}_none_p1.json"
        s0_closes = reader.load_symbol_closes(
            relpath, start=policy.s0_start, end=policy.s0_end
        )
        if symbol in SPLIT_SYMBOLS:
            s0_closes = {
                **s0_closes,
                **reader.read_provenance_closes(relpath),
            }
        raw_closes[symbol] = s0_closes
        full_payload = json.loads(reader.read_pinned_text(relpath))
        symbol_reports[symbol] = verify_symbol_payload(full_payload, symbol)

    cross = (
        verify_split_events(raw_closes),
        verify_distribution_inputs(distributions),
        verify_tr_inputs(raw_closes, distributions, split_factors),
        verify_calendar(calendar),
    )
    return CohortVerificationReport(symbol_reports=symbol_reports, cross_checks=cross)


__all__ = [
    "PINNED_CLOSE_RATIOS",
    "RATIO_TOLERANCE",
    "ROW_KEYS",
    "SPLIT_EFFECTIVE_DATE",
    "SPLIT_FACTOR",
    "SPLIT_PROVENANCE_DATES",
    "SPLIT_SYMBOLS",
    "VERDICT_FAIL",
    "VERDICT_NOT_RUN",
    "VERDICT_PASS",
    "CohortCheck",
    "CohortVerificationReport",
    "verify_calendar",
    "verify_distribution_inputs",
    "verify_real_cohort",
    "verify_split_events",
    "verify_symbol_payload",
    "verify_tr_inputs",
]
