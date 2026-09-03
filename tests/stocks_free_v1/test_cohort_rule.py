"""Synthetic goldens for the pre-return cohort eligibility rule (A3).

Imports the A3 lane modules directly by file path (this lane owns no
``__init__.py``; A2 owns the package init).
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Mapping, Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MODULE_PATH = REPO_ROOT / "research" / "stocks_free_v1" / "cohort.py"
_SPEC = importlib.util.spec_from_file_location("z1_a3_cohort", _MODULE_PATH)
cohort = importlib.util.module_from_spec(_SPEC)
sys.modules["z1_a3_cohort"] = cohort
_SPEC.loader.exec_module(cohort)

from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1 as CAL

# --- frozen synthetic window (calendar-table dates, ~1 quarter of sessions) -- #
WINDOW_START = date(2016, 1, 4)   # Monday, first US session of 2016
WINDOW_END = date(2016, 3, 31)
S0_START = date(2016, 1, 4)
WARMUP = 2                        # small synthetic warmup for inception checks
FLOOR = 10_000_000.0


def _window_sessions() -> list[date]:
    return [
        s.start_utc.astimezone(cohort.ET_ZONE).date()
        for s in CAL.sessions_in_range(WINDOW_START, WINDOW_END)
    ]


SESSIONS = _window_sessions()


class FixtureSource:
    """Synthetic CohortDataSource with per-candidate override hooks."""

    def __init__(
        self,
        *,
        identifiers: Mapping[str, Mapping[str, object] | None] | None = None,
        inceptions: Mapping[str, date | None] | None = None,
        bars: Mapping[str, Sequence[cohort.RawBar]] | None = None,
        tr: Mapping[str, Sequence[cohort.TrPoint]] | None = None,
        unresolved: Mapping[str, Sequence[cohort.UnresolvedEvent]] | None = None,
    ) -> None:
        self._identifiers = identifiers or {}
        self._inceptions = inceptions or {}
        self._bars = bars or {}
        self._tr = tr or {}
        self._unresolved = unresolved or {}

    def identifier_evidence(self, symbol: str):
        return self._identifiers.get(
            symbol,
            {"ticker": symbol, "exchange": "NYSE_ARCA", "issuer": "SYNTH_ISSUER"},
        )

    def inception_date(self, symbol: str):
        return self._inceptions.get(symbol, date(2000, 1, 1))

    def raw_bars(self, symbol: str):
        return self._bars.get(symbol, _default_bars())

    def tr_index(self, symbol: str):
        return self._tr.get(symbol, _default_tr())

    def unresolved_events(self, symbol: str):
        return self._unresolved.get(symbol, [])


def _default_bars() -> list[cohort.RawBar]:
    # price 50, volume 400k -> $20M daily, above the $10M floor
    return [
        cohort.RawBar(session_date=day, open=50.0, high=51.0, low=49.0, close=50.0, volume=400_000.0)
        for day in SESSIONS
    ]


def _default_tr() -> list[cohort.TrPoint]:
    return [cohort.TrPoint(session_date=day, tr_level=100.0) for day in SESSIONS]


def _evaluate(symbol: str, source) -> cohort.CensusRow:
    return cohort.evaluate_candidate(
        symbol,
        source=source,
        calendar=CAL,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        s0_start=S0_START,
        warmup_sessions=WARMUP,
        dollar_volume_floor=FLOOR,
    )


# --- acceptance golden -------------------------------------------------------- #


def test_accept_clean_candidate_with_all_checks_and_reason() -> None:
    row = _evaluate("SPY", FixtureSource(inceptions={"SPY": date(1993, 1, 22)}))
    assert row.accepted is True
    assert row.decision == cohort.ACCEPTED
    assert row.reasons == (cohort.ALL_CHECKS_PASSED,)
    assert all(check.passed for check in row.checks)
    assert len(row.checks) == 7  # C1..C7, mandatory and complete


def test_role_from_seed_list_documentation_only() -> None:
    row = _evaluate("SPY", FixtureSource())
    assert row.role == "BROAD_US_EQUITY_BENCHMARK"
    # roles play no part in acceptance decisions
    census = cohort.build_census(
        [("SYN", "FANCY_ROLE")],
        source=FixtureSource(),
        calendar=CAL,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        s0_start=S0_START,
        warmup_sessions=WARMUP,
    )
    assert census.rows[0].role == "FANCY_ROLE"


# --- rejection goldens (one per rule check) ----------------------------------- #


def test_reject_missing_identifier_evidence() -> None:
    source = FixtureSource(identifiers={"FAKE": None})
    row = _evaluate("FAKE", source)
    assert not row.accepted
    assert cohort.REJECT_IDENTIFIER_EVIDENCE in row.reasons
    check = next(c for c in row.checks if c.code == "IDENTIFIER_EVIDENCE")
    assert "no stable identifier evidence" in check.detail


def test_reject_ticker_mismatch_in_evidence() -> None:
    source = FixtureSource(
        identifiers={"SWP": {"ticker": "OTHER", "exchange": "NYSE_ARCA", "issuer": "X"}}
    )
    row = _evaluate("SWP", source)
    assert not row.accepted
    assert cohort.REJECT_IDENTIFIER_EVIDENCE in row.reasons


def test_reject_inception_on_or_after_warmed_s0_start() -> None:
    # inception exactly at the warmed start -> NOT strictly before -> reject
    warmed = cohort._warmed_s0_start(CAL, S0_START, WARMUP)
    at_start = FixtureSource(inceptions={"NEW": warmed})
    row = _evaluate("NEW", at_start)
    assert not row.accepted
    assert cohort.REJECT_INCEPTION_TOO_LATE in row.reasons
    # one session after -> also reject
    late = FixtureSource(inceptions={"NEW": warmed + timedelta(days=7)})
    assert cohort.REJECT_INCEPTION_TOO_LATE in _evaluate("NEW", late).reasons
    # strictly before -> accept
    early = FixtureSource(inceptions={"NEW": warmed - timedelta(days=1)})
    assert _evaluate("NEW", early).accepted


def test_reject_inception_inside_calendar_table_returns_fail_closed_detail() -> None:
    # warmed start before the frozen table (S0 near 2010-03) -> fail closed
    source = FixtureSource(inceptions={"OLD": date(1995, 1, 3)})
    row = cohort.evaluate_candidate(
        "OLD",
        source=source,
        calendar=CAL,
        window_start=date(2010, 3, 1),
        window_end=date(2010, 4, 30),
        s0_start=date(2010, 3, 1),
        warmup_sessions=63,
    )
    assert not row.accepted
    assert cohort.REJECT_INCEPTION_TOO_LATE in row.reasons
    check = next(c for c in row.checks if c.code == "INCEPTION_BEFORE_WARMED_S0_START")
    assert "fail closed" in check.detail


def test_reject_missing_raw_bar_for_a_session() -> None:
    bars = _default_bars()
    del bars[5]  # one session silently missing -> must be caught
    source = FixtureSource(bars={"GAP": bars})
    row = _evaluate("GAP", source)
    assert not row.accepted
    assert cohort.REJECT_INCOMPLETE_RAW_BARS in row.reasons
    check = next(c for c in row.checks if c.code == "RAW_BARS_INCOMPLETE")
    assert "without a raw bar" in check.detail


def test_reject_raw_bar_on_non_session_date() -> None:
    bars = _default_bars() + [
        cohort.RawBar(session_date=date(2016, 2, 6), open=50, high=51, low=49, close=50, volume=1)
    ]  # 2016-02-06 is a Saturday
    row = _evaluate("WKND", FixtureSource(bars={"WKND": bars}))
    assert not row.accepted
    assert cohort.REJECT_INCOMPLETE_RAW_BARS in row.reasons
    check = next(c for c in row.checks if c.code == "RAW_BARS_INCOMPLETE")
    assert "non-session dates" in check.detail


def test_reject_insane_raw_bar() -> None:
    bars = list(_default_bars())
    bars[3] = cohort.RawBar(
        session_date=bars[3].session_date, open=50, high=40, low=49, close=50, volume=10
    )  # high < low/close
    row = _evaluate("INSANE", FixtureSource(bars={"INSANE": bars}))
    assert not row.accepted
    assert cohort.REJECT_INVALID_RAW_BARS in row.reasons


def test_reject_missing_tr_point() -> None:
    tr = _default_tr()
    del tr[2]
    row = _evaluate("NOTR", FixtureSource(tr={"NOTR": tr}))
    assert not row.accepted
    assert cohort.REJECT_INCOMPLETE_TR_INPUTS in row.reasons


def test_reject_nonpositive_tr_point() -> None:
    tr = list(_default_tr())
    tr[7] = cohort.TrPoint(session_date=tr[7].session_date, tr_level=0.0)
    row = _evaluate("ZTR", FixtureSource(tr={"ZTR": tr}))
    assert not row.accepted
    assert cohort.REJECT_INCOMPLETE_TR_INPUTS in row.reasons


def test_reject_below_dollar_volume_floor() -> None:
    # price 50 x 100k shares = $5M < $10M floor
    bars = [
        cohort.RawBar(session_date=day, open=50, high=51, low=49, close=50, volume=100_000)
        for day in SESSIONS
    ]
    row = _evaluate("ILLQ", FixtureSource(bars={"ILLQ": bars}))
    assert not row.accepted
    assert cohort.REJECT_VOLUME_FLOOR in row.reasons
    check = next(c for c in row.checks if c.code == "DOLLAR_VOLUME_FLOOR")
    assert "predeclared" in check.detail


def test_reject_unresolved_split_event() -> None:
    source = FixtureSource(
        unresolved={
            "SPL": [
                cohort.UnresolvedEvent(
                    symbol="SPL",
                    kind="SPLIT",
                    event_date=date(2016, 2, 10),
                    description="2:1 split reported by one source only",
                )
            ]
        }
    )
    row = _evaluate("SPL", source)
    assert not row.accepted
    assert cohort.REJECT_UNRESOLVED_EVENTS in row.reasons


def test_reject_when_next_session_price_missing() -> None:
    bars = _default_bars()
    # remove the bar right after session[4]; the executable next-session
    # close for session[4] disappears (the FINAL session keeps only the
    # calendar-resolution requirement)
    victim = cohort._session_dates(CAL, WINDOW_START, WINDOW_END)[5]
    bars = [b for b in bars if b.session_date != victim]
    row = _evaluate("NOFILL", FixtureSource(bars={"NOFILL": bars}))
    assert not row.accepted
    assert cohort.REJECT_NEXT_SESSION_NOT_EXECUTABLE in row.reasons
    check = next(c for c in row.checks if c.code == "NEXT_SESSION_EXECUTABLE")
    assert "no raw bar on next session" in check.detail


def test_rejected_row_reasons_never_empty() -> None:
    row = _evaluate("VOID", FixtureSource(identifiers={"VOID": None}))
    assert row.reasons and all(reason for reason in row.reasons)


# --- census builder + digest goldens ------------------------------------------ #


def test_census_builder_rows_and_mandatory_reasons() -> None:
    source = FixtureSource(
        identifiers={"BAD": None},
        bars={"ILLQ": [
            cohort.RawBar(session_date=day, open=50, high=51, low=49, close=50, volume=1)
            for day in SESSIONS
        ]},
    )
    census = cohort.build_census(
        [("SPY", "BROAD_US_EQUITY_BENCHMARK"), ("BAD", "X"), ("ILLQ", "Y")],
        source=source,
        calendar=CAL,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        s0_start=S0_START,
        warmup_sessions=WARMUP,
    )
    by_symbol = {row.symbol: row for row in census.rows}
    assert by_symbol["SPY"].accepted
    assert not by_symbol["BAD"].accepted and by_symbol["BAD"].reasons
    assert not by_symbol["ILLQ"].accepted and cohort.REJECT_VOLUME_FLOOR in by_symbol["ILLQ"].reasons
    assert census.limitation == cohort.CURRENT_SURVIVOR_LIMITATION


def test_cohort_digest_stable_and_canonical() -> None:
    def build(order):
        return cohort.build_census(
            order,
            source=FixtureSource(),
            calendar=CAL,
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            s0_start=S0_START,
            warmup_sessions=WARMUP,
        )

    census_a = build([("SPY", "BROAD_US_EQUITY_BENCHMARK")])
    census_b = build([("SPY", "BROAD_US_EQUITY_BENCHMARK")])
    assert census_a.cohort_digest == census_b.cohort_digest
    assert len(census_a.cohort_digest) == 64

    # a REJECTED-only candidate list yields the empty-cohort digest, stable too
    empty = cohort.build_census(
        [("BAD", "X")],
        source=FixtureSource(identifiers={"BAD": None}),
        calendar=CAL,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        s0_start=S0_START,
        warmup_sessions=WARMUP,
    )
    assert empty.accepted_symbols == ()
    assert len(empty.cohort_digest) == 64

    # a different accepted cohort (an extra accepted member) alters the
    # digest: the digest is cohort identity, never silently stable
    different = cohort.build_census(
        [("SPY", "BROAD_US_EQUITY_BENCHMARK"), ("SECOND", "SYNTHETIC")],
        source=FixtureSource(),
        calendar=CAL,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        s0_start=S0_START,
        warmup_sessions=WARMUP,
    )
    assert different.accepted_symbols == ("SPY", "SECOND")
    assert different.cohort_digest != census_a.cohort_digest


def test_protocol_shape_satisfied_by_fixture() -> None:
    assert isinstance(FixtureSource(), cohort.CohortDataSource)


def test_window_reversed_raises() -> None:
    with pytest.raises(ValueError):
        cohort.evaluate_candidate(
            "SPY",
            source=FixtureSource(),
            calendar=CAL,
            window_start=WINDOW_END,
            window_end=WINDOW_START,
            s0_start=S0_START,
        )
