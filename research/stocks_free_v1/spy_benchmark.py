"""SPY total-return benchmark reconstruction from official SSGA files.

(owner: A3)

PLAN_stocks_free.md 3.3: "SPY total return is the primary benchmark when
its inputs pass."  PLAN 4.1 item 10 requires SPY price/distribution/
total-return reconciliation.  This module:

1. reads the OFFICIAL State Street (SSGA) SPY files downloaded from the
   issuer pages (URLs + access dates + sha256 are recorded as evidence in
   ``research/audits/stocks_free_v1/z1_a3/``; raw files live OUTSIDE Git
   under the staging area, never in the tree):
     - NAV history:   https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-spy.xlsx
     - distributions: https://www.ssga.com/library-content/products/fund-data/etfs/us/spdr-etf-historical-distributions.xlsx
   (page https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy
   and its "ETF Historical Distributions" resource page; both fetched
   without any account or credential);

2. reconstructs the SPY total-return index from NAV + per-share
   distributions with the DECLARED reinvestment convention
   ``TR_GROWTH_CONVENTION`` (distribution reinvested at the ex-date NAV):

       growth_t = (nav_t + dist_t) / nav_{t-1}   (dist_t on ex-date t)

3. reconciles the reconstruction against (a) the price-only NAV growth
   and (b) any independently supplied adjusted/total-return series, with
   DECLARED tolerances; every mismatch is recorded as a Conflict and
   surfaced in the report status — conflicts are NEVER silently resolved
   (PLAN 4.1: "Conflicts are recorded and block affected instruments").

XLSX parsing uses only the standard library (zipfile + xml.etree): no new
dependency is installed into the shared venv.
"""

from __future__ import annotations

import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Mapping, Sequence

try:  # normal package import (available after A2/integration merge)
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_END,
        CALENDAR_TABLE_START,
        USEquityRegularCalendar,
        US_EQUITY_REGULAR_V1,
    )
except ImportError:  # direct file-path import in the A3 lane worktree
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from research.assets.stocks.calendar import (
        CALENDAR_TABLE_END,
        CALENDAR_TABLE_START,
        USEquityRegularCalendar,
        US_EQUITY_REGULAR_V1,
    )

SPY_BENCHMARK_ID = "STOCKS_FREE_V1_SPY_TR_BENCHMARK_V1"

SSGA_SPY_PAGE_URL = (
    "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy"
)
SSGA_NAV_HISTORY_URL = (
    "https://www.ssga.com/library-content/products/fund-data/etfs/us/"
    "navhist-us-en-spy.xlsx"
)
SSGA_DISTRIBUTIONS_URL = (
    "https://www.ssga.com/library-content/products/fund-data/etfs/us/"
    "spdr-etf-historical-distributions.xlsx"
)
SSGA_DISTRIBUTIONS_RESOURCE_URL = (
    "https://www.ssga.com/us/en/intermediary/resources/documents/"
    "etf-dividend-distributions"
)

# Declared reinvestment convention (frozen): a per-share distribution with
# ex-date t is reinvested at the ex-date NAV, i.e. it contributes dist_t to
# the numerator of growth_t.
TR_GROWTH_CONVENTION = "DISTRIBUTION_REINVESTED_AT_EX_DATE_NAV"

# Declared tolerances (frozen; changing them after scoring starts is a
# scientific-threshold change).
#  - cumulative TR vs an independent adjusted/TR series: 0.5% relative on
#    the cumulative growth factor, 5e-3 on any daily log-growth point;
#  - TR cumulative growth must not fall below price-only growth by more
#    than TR_GE_PRICE_MIN_SLACK (distributions can only add return under
#    the declared convention).
TR_VS_ADJUSTED_CUMULATIVE_TOLERANCE = 5e-3
TR_VS_ADJUSTED_DAILY_LOG_TOLERANCE = 5e-3
TR_GE_PRICE_MIN_SLACK = -1e-9

STATUS_RECONCILED = "RECONCILED"
STATUS_CONFLICTS_RECORDED = "CONFLICTS_RECORDED"
STATUS_FAIL = "FAIL"


class SpyBenchmarkError(ValueError):
    """Fail-closed error for unusable SSGA inputs."""


# --- stdlib xlsx reading ---------------------------------------------------- #

_SSML_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_M_TAG = "{%s}" % _SSML_MAIN
_COL_RE = re.compile(r"[A-Z]+")


def _column_of(ref: str) -> str:
    match = _COL_RE.match(ref or "")
    return match.group(0) if match else ""


def read_xlsx_rows(path: str | Path) -> list[dict[str, str]]:
    """Read the FIRST worksheet of an .xlsx into column-keyed row dicts.

    Handles shared strings and inline strings; ignores styles/formatting.
    Rows are returned in worksheet order, keyed by column letters ("A",
    "B", ...).  Pure standard library.
    """
    path = Path(path)
    if not path.is_file():
        raise SpyBenchmarkError(f"file not found: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                for si in root.findall(_M_TAG + "si"):
                    shared.append(
                        "".join(
                            t.text or "" for t in si.iter(_M_TAG + "t")
                        )
                    )
            sheet_names = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)
            ]
            if not sheet_names:
                raise SpyBenchmarkError(f"no worksheet in {path}")
            sheet_names.sort()
            root = ET.fromstring(archive.read(sheet_names[0]))
    except (zipfile.BadZipFile, ET.ParseError) as exc:
        raise SpyBenchmarkError(f"unreadable xlsx {path}: {exc}") from exc

    rows: list[dict[str, str]] = []
    for row in root.iter(_M_TAG + "row"):
        values: dict[str, str] = {}
        for cell in row.iter(_M_TAG + "c"):
            column = _column_of(cell.get("r") or "")
            if not column:
                continue
            text: str | None = None
            inline = cell.find(_M_TAG + "is")
            if inline is not None:
                text = "".join(t.text or "" for t in inline.iter(_M_TAG + "t"))
            else:
                v = cell.find(_M_TAG + "v")
                if v is not None and v.text is not None:
                    text = v.text
                    if cell.get("t") == "s" and text:
                        text = shared[int(text)]
            values[column] = (text or "").strip()
        rows.append(values)
    return rows


# --- official-file parsers --------------------------------------------------- #


@dataclass(frozen=True)
class NavRow:
    """One NAV-history row from the official SSGA NAV workbook."""

    nav_date: date
    nav: float


@dataclass(frozen=True)
class DistributionRow:
    """One per-share distribution record (official SSGA workbook)."""

    ex_date: date
    ordinary: float
    short_term_cap_gain: float = 0.0
    long_term_cap_gain: float = 0.0

    @property
    def total_per_share(self) -> float:
        return self.ordinary + self.short_term_cap_gain + self.long_term_cap_gain


def parse_ssga_nav_history(path: str | Path) -> list[NavRow]:
    """Parse the official SSGA SPY NAV-history workbook.

    Non-date rows (title block, footers) are skipped and counted; the
    header is located by content, never by fixed offset.
    """
    rows = read_xlsx_rows(path)
    header_idx = next(
        (i for i, row in enumerate(rows) if row.get("A") == "Date"), None
    )
    if header_idx is None:
        raise SpyBenchmarkError(
            "SSGA NAV workbook: no 'Date' header row found"
        )
    out: list[NavRow] = []
    skipped = 0
    for row in rows[header_idx + 1 :]:
        raw_date = row.get("A", "")
        nav = _to_float(row.get("B"))
        parsed = _parse_dmy(raw_date)
        if parsed is None or nav is None:
            skipped += 1
            continue
        out.append(NavRow(nav_date=parsed, nav=nav))
    if not out:
        raise SpyBenchmarkError("SSGA NAV workbook: zero parsable data rows")
    out.sort(key=lambda item: item.nav_date)
    return out


def parse_ssga_distributions(
    path: str | Path, ticker: str = "SPY"
) -> list[DistributionRow]:
    """Parse the official SPDR ETF Historical Distributions workbook."""
    rows = read_xlsx_rows(path)
    header_idx = next(
        (i for i, row in enumerate(rows) if row.get("B") == "TICKER"), None
    )
    if header_idx is None:
        raise SpyBenchmarkError(
            "SSGA distributions workbook: no 'TICKER' header row found"
        )
    out: list[DistributionRow] = []
    for row in rows[header_idx + 1 :]:
        if row.get("B", "").strip().upper() != ticker.upper():
            continue
        ex_date = _parse_mdy(row.get("D", ""))
        if ex_date is None:
            continue
        out.append(
            DistributionRow(
                ex_date=ex_date,
                ordinary=_to_float(row.get("G")) or 0.0,
                short_term_cap_gain=_to_float(row.get("H")) or 0.0,
                long_term_cap_gain=_to_float(row.get("I")) or 0.0,
            )
        )
    out.sort(key=lambda item: item.ex_date)
    return out


def _to_float(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_dmy(text: str) -> date | None:
    """'01-Sep-2026' style SSGA NAV dates."""
    try:
        return datetime.strptime(text.strip(), "%d-%b-%Y").date()
    except ValueError:
        return None


def _parse_mdy(text: str) -> date | None:
    """'03/19/1993' style SSGA distribution dates."""
    try:
        return datetime.strptime(text.strip(), "%m/%d/%Y").date()
    except ValueError:
        return None


# --- reconstruction + reconciliation ----------------------------------------- #


@dataclass(frozen=True)
class TrPointSeries:
    """Reconstructed daily total-return index (base 1.0 at first NAV)."""

    base_date: date
    dates: tuple[date, ...]
    tr_levels: tuple[float, ...]

    def growth_over_series(self) -> float:
        return self.tr_levels[-1] / self.tr_levels[0] if self.tr_levels else 1.0


@dataclass(frozen=True)
class Conflict:
    """A recorded, never silently resolved reconciliation conflict."""

    kind: str
    detail: str


@dataclass(frozen=True)
class TrReconstruction:
    """Total-return reconstruction with every anomaly recorded."""

    tr: TrPointSeries
    distribution_count_applied: int
    ex_dates_missing_from_nav: tuple[date, ...]
    nonpositive_nav_rows: int
    conflicts: tuple[Conflict, ...]

    @property
    def status(self) -> str:
        if self.conflicts:
            return STATUS_CONFLICTS_RECORDED
        return STATUS_RECONCILED


@dataclass(frozen=True)
class ReconciliationReport:
    """Declared-tolerance reconciliation record (TR vs price / adjusted)."""

    benchmark_id: str = SPY_BENCHMARK_ID
    convention: str = TR_GROWTH_CONVENTION
    tr_growth: float = 1.0
    other_growth: float = 1.0
    cumulative_relative_difference: float = 0.0
    max_abs_daily_log_difference: float = 0.0
    conflicts: tuple[Conflict, ...] = field(default_factory=tuple)

    @property
    def status(self) -> str:
        if any(c.kind == "FAIL" for c in self.conflicts):
            return STATUS_FAIL
        if self.conflicts:
            return STATUS_CONFLICTS_RECORDED
        return STATUS_RECONCILED


def reconstruct_total_return(
    nav_rows: Sequence[NavRow],
    distributions: Sequence[DistributionRow],
    *,
    calendar: USEquityRegularCalendar = US_EQUITY_REGULAR_V1,
) -> TrReconstruction:
    """Reconstruct the daily TR index under the declared convention.

    Fail-closed inputs: at least two NAV rows, all NAVs positive.  Ex-dates
    absent from the NAV history are recorded as conflicts (never silently
    dropped); NAV dates that are not calendar sessions are recorded too.
    """
    rows = sorted(nav_rows, key=lambda item: item.nav_date)
    if len(rows) < 2:
        raise SpyBenchmarkError(
            "TR reconstruction needs at least two NAV rows; fail closed"
        )
    nonpositive = sum(1 for row in rows if row.nav <= 0)
    if nonpositive:
        raise SpyBenchmarkError(
            f"{nonpositive} non-positive NAV row(s); fail closed"
        )

    by_date = {row.nav_date: row.nav for row in rows}
    # The frozen calendar table covers 2010-2030 and fails closed outside
    # it; NAV dates outside the horizon are recorded, never guessed at.
    in_horizon = [
        row.nav_date
        for row in rows
        if CALENDAR_TABLE_START <= row.nav_date <= CALENDAR_TABLE_END
    ]
    non_session_dates = tuple(
        day for day in in_horizon if not calendar.is_session_day(day)
    )
    out_of_horizon_dates = tuple(
        row.nav_date
        for row in rows
        if row.nav_date < CALENDAR_TABLE_START or row.nav_date > CALENDAR_TABLE_END
    )

    dist_by_ex: dict[date, float] = {}
    missing_ex: list[date] = []
    for dist in distributions:
        total = dist.total_per_share
        if total == 0.0:
            continue
        if dist.ex_date in by_date:
            dist_by_ex[dist.ex_date] = dist_by_ex.get(dist.ex_date, 0.0) + total
        else:
            missing_ex.append(dist.ex_date)

    dates: list[date] = []
    levels: list[float] = []
    level = 1.0
    base = rows[0].nav_date
    dates.append(base)
    levels.append(level)
    applied = 0
    for prev, curr in zip(rows, rows[1:]):
        dist = dist_by_ex.get(curr.nav_date, 0.0)
        growth = (curr.nav + dist) / prev.nav
        if growth <= 0:
            raise SpyBenchmarkError(
                f"non-positive TR growth at {curr.nav_date.isoformat()}; "
                "fail closed"
            )
        level *= growth
        dates.append(curr.nav_date)
        levels.append(level)
        if dist:
            applied += 1

    conflicts: list[Conflict] = []
    if missing_ex:
        shown = ", ".join(d.isoformat() for d in sorted(missing_ex)[:5])
        conflicts.append(
            Conflict(
                "DISTRIBUTION_EX_DATE_NOT_IN_NAV",
                f"{len(missing_ex)} distribution ex-date(s) absent from NAV "
                f"history (first: {shown}); recorded, never silently dropped",
            )
        )
    if non_session_dates:
        shown = ", ".join(d.isoformat() for d in non_session_dates[:5])
        conflicts.append(
            Conflict(
                "NAV_DATE_NOT_CALENDAR_SESSION",
                f"{len(non_session_dates)} NAV date(s) inside the frozen "
                f"table horizon are not regular sessions (first: {shown}); "
                "recorded for A7 review",
            )
        )
    if out_of_horizon_dates:
        conflicts.append(
            Conflict(
                "NAV_DATE_OUTSIDE_CALENDAR_TABLE",
                f"{len(out_of_horizon_dates)} NAV date(s) precede/exceed the "
                f"frozen table horizon "
                f"[{CALENDAR_TABLE_START.isoformat()}, "
                f"{CALENDAR_TABLE_END.isoformat()}] (first: "
                f"{min(out_of_horizon_dates).isoformat()}, last: "
                f"{max(out_of_horizon_dates).isoformat()}); reconstruction "
                "continues on raw NAV math only, calendar session checks do "
                "not apply there",
            )
        )
    return TrReconstruction(
        tr=TrPointSeries(
            base_date=base, dates=tuple(dates), tr_levels=tuple(levels)
        ),
        distribution_count_applied=applied,
        ex_dates_missing_from_nav=tuple(sorted(missing_ex)),
        nonpositive_nav_rows=nonpositive,
        conflicts=tuple(conflicts),
    )


def reconcile_tr_vs_price(
    tr: TrPointSeries,
    price_index: Mapping[date, float],
    *,
    price_series_name: str = "PRICE_ONLY",
) -> ReconciliationReport:
    """Compare cumulative TR growth vs a price-only index.

    Under the declared convention the TR growth must not fall below the
    price-only growth by more than ``TR_GE_PRICE_MIN_SLACK``; a larger
    deficit is recorded as a conflict (blocked, not silently fixed).
    """
    common = [d for d in tr.dates if d in price_index]
    if len(common) < 2:
        return ReconciliationReport(
            conflicts=(
                Conflict(
                    "FAIL",
                    "price index shares fewer than two dates with the TR "
                    "series; reconciliation impossible; fail closed",
                ),
            )
        )
    first = common[0]
    last = common[-1]
    tr_growth = tr.tr_levels[tr.dates.index(last)] / tr.tr_levels[tr.dates.index(first)]
    price_growth = price_index[last] / price_index[first]
    conflicts: list[Conflict] = []
    slack = tr_growth - price_growth
    if slack < TR_GE_PRICE_MIN_SLACK:
        conflicts.append(
            Conflict(
                "TR_BELOW_PRICE_GROWTH",
                f"cumulative TR growth {tr_growth:.10f} < price-only growth "
                f"{price_growth:.10f} ({price_series_name}); distributions "
                "can only add return under the declared convention; "
                "conflict recorded",
            )
        )
    return ReconciliationReport(
        tr_growth=tr_growth,
        other_growth=price_growth,
        cumulative_relative_difference=slack,
        conflicts=tuple(conflicts),
    )


def reconcile_tr_vs_adjusted(
    tr: TrPointSeries,
    adjusted_index: Mapping[date, float],
    *,
    adjusted_series_name: str = "ADJUSTED",
    cumulative_tolerance: float = TR_VS_ADJUSTED_CUMULATIVE_TOLERANCE,
    daily_log_tolerance: float = TR_VS_ADJUSTED_DAILY_LOG_TOLERANCE,
) -> ReconciliationReport:
    """Compare the reconstruction against an independent adjusted/TR series.

    Declared tolerances: cumulative relative difference and max absolute
    daily log-growth difference.  Any exceedance is recorded as a conflict;
    the conflict BLOCKS, it never silently replaces the reconstruction.
    """
    import math

    common = [d for d in tr.dates if d in adjusted_index]
    if len(common) < 2:
        return ReconciliationReport(
            conflicts=(
                Conflict(
                    "FAIL",
                    "adjusted index shares fewer than two dates with the TR "
                    "series; reconciliation impossible; fail closed",
                ),
            )
        )
    tr_level_by_date = dict(zip(tr.dates, tr.tr_levels))
    first = common[0]
    last = common[-1]
    tr_growth = tr_level_by_date[last] / tr_level_by_date[first]
    adj_growth = adjusted_index[last] / adjusted_index[first]
    cumulative_diff = abs(tr_growth - adj_growth) / adj_growth

    max_log_diff = 0.0
    worst_date: date | None = None
    for prev, curr in zip(common, common[1:]):
        tr_g = tr_level_by_date[curr] / tr_level_by_date[prev]
        adj_g = adjusted_index[curr] / adjusted_index[prev]
        if adj_g <= 0 or tr_g <= 0:
            continue
        diff = abs(math.log(tr_g) - math.log(adj_g))
        if diff > max_log_diff:
            max_log_diff = diff
            worst_date = curr

    conflicts: list[Conflict] = []
    if cumulative_diff > cumulative_tolerance:
        conflicts.append(
            Conflict(
                "CUMULATIVE_TOLERANCE_EXCEEDED",
                f"cumulative growth TR {tr_growth:.10f} vs "
                f"{adjusted_series_name} {adj_growth:.10f}: relative "
                f"difference {cumulative_diff:.6f} > tolerance "
                f"{cumulative_tolerance}; conflict recorded, not resolved",
            )
        )
    if max_log_diff > daily_log_tolerance:
        conflicts.append(
            Conflict(
                "DAILY_LOG_TOLERANCE_EXCEEDED",
                f"max absolute daily log-growth difference "
                f"{max_log_diff:.6f} > tolerance {daily_log_tolerance} "
                f"(at {worst_date.isoformat() if worst_date else 'n/a'}); "
                "conflict recorded, not resolved",
            )
        )
    return ReconciliationReport(
        tr_growth=tr_growth,
        other_growth=adj_growth,
        cumulative_relative_difference=cumulative_diff,
        max_abs_daily_log_difference=max_log_diff,
        conflicts=tuple(conflicts),
    )


@dataclass(frozen=True)
class CoverageSummary:
    """Loader-resolved coverage of one official file."""

    first: date
    last: date
    rows: int
    years: float

    def as_dict(self) -> dict[str, object]:
        return {
            "first": self.first.isoformat(),
            "last": self.last.isoformat(),
            "rows": self.rows,
            "years": round(self.years, 3),
        }


def summarize_coverage(rows: Sequence[NavRow] | Sequence[DistributionRow]) -> CoverageSummary:
    """First/last/row-count/years of a parsed official series."""
    if not rows:
        raise SpyBenchmarkError("no rows to summarize; fail closed")
    dates = [
        row.nav_date if isinstance(row, NavRow) else row.ex_date for row in rows
    ]
    first, last = min(dates), max(dates)
    years = (last - first).days / 365.25
    return CoverageSummary(first=first, last=last, rows=len(rows), years=years)


def sha256_file(path: str | Path) -> str:
    """Streaming sha256 of a downloaded file (evidence manifest input)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "Conflict",
    "CoverageSummary",
    "DistributionRow",
    "NavRow",
    "ReconciliationReport",
    "SPY_BENCHMARK_ID",
    "SSGA_DISTRIBUTIONS_RESOURCE_URL",
    "SSGA_DISTRIBUTIONS_URL",
    "SSGA_NAV_HISTORY_URL",
    "SSGA_SPY_PAGE_URL",
    "STATUS_CONFLICTS_RECORDED",
    "STATUS_FAIL",
    "STATUS_RECONCILED",
    "SpyBenchmarkError",
    "TR_GE_PRICE_MIN_SLACK",
    "TR_GROWTH_CONVENTION",
    "TR_VS_ADJUSTED_CUMULATIVE_TOLERANCE",
    "TR_VS_ADJUSTED_DAILY_LOG_TOLERANCE",
    "TrPointSeries",
    "TrReconstruction",
    "parse_ssga_distributions",
    "parse_ssga_nav_history",
    "read_xlsx_rows",
    "reconcile_tr_vs_adjusted",
    "reconcile_tr_vs_price",
    "reconstruct_total_return",
    "sha256_file",
    "summarize_coverage",
]
