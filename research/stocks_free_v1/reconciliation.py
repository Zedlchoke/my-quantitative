"""Raw/adjusted/distribution reconciliation for stocks-free-v1 (A2, Z1).

Implements PLAN_stocks_free.md section 4.1 items 7, 10, 14, 15:

- parse issuer-official SSGA workbooks with the STDLIB ONLY (zipfile +
  ElementTree): the owner virtualenv deliberately lacks openpyxl and the lane
  must not mutate it;
- reconstruct a total-return series from raw NAV + cash-distribution records
  under a declared reinvestment convention;
- compare a reconstructed/adjusted series against an independent provider
  series on common dates with a DECLARED tolerance, recording every conflict
  per date instead of silently averaging or dropping it;
- check distribution coverage against the price-series session dates.

Conflicts never override a provider silently (PLAN 4.1: conflicts are recorded
and block affected instruments).
"""

from __future__ import annotations

import datetime as dt
import zipfile
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence
import xml.etree.ElementTree as ET

XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


# ------------------------------------------------------------------ parsers
def _col_index(ref: str) -> int:
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - ord("A") + 1)
    return n - 1


def xlsx_grid(path, sheet: Optional[str] = None) -> List[List[str]]:
    """Read a single-sheet simple xlsx into a positional string grid.

    Handles inline strings and the shared-strings table; columns are derived
    from each cell's ref so blank cells yield empty strings. Sufficient for
    the single-worksheet SSGA fund-data fixtures used by this lane.
    """
    with zipfile.ZipFile(path) as zf:
        shared: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sroot = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sroot.findall(f"{{{XLSX_MAIN_NS}}}si"):
                shared.append(
                    "".join(t.text or "" for t in si.iter(f"{{{XLSX_MAIN_NS}}}t"))
                )
        wroot = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
    rows: List[List[str]] = []
    for row in wroot.iter(f"{{{XLSX_MAIN_NS}}}row"):
        vals: Dict[int, str] = {}
        for c in row:
            idx = _col_index(c.get("r") or "A1")
            ctype = c.get("t")
            v = c.find(f"{{{XLSX_MAIN_NS}}}v")
            if v is not None and ctype == "s":
                vals[idx] = shared[int(v.text)]
            elif v is not None:
                vals[idx] = v.text or ""
            else:
                inline = c.find(f"{{{XLSX_MAIN_NS}}}is/{{{XLSX_MAIN_NS}}}t")
                vals[idx] = inline.text if inline is not None and inline.text else ""
        if vals:
            width = max(vals) + 1
            rows.append([vals.get(i, "") for i in range(width)])
        else:
            rows.append([])
    return rows


# ------------------------------------------------------------------ parsers
def _opt_float(cell: str) -> Optional[float]:
    """Parse a numeric cell; SSGA workbooks use '-' as a missing marker."""
    cell = (cell or "").strip()
    if not cell or cell == "-":
        return None
    return float(cell)


def parse_ssga_nav_history(path) -> List[dict]:
    """Parse an SSGA ``navhist-us-en-<ticker>.xlsx`` NAV-history workbook.

    Layout (verified 2026-09-03): title rows, then header row
    ``Date | NAV | Shares Outstanding | Total Net Assets`` with dates as
    ``DD-Mon-YYYY`` (descending). Returns ascending-date list of dicts with
    keys ``date`` (datetime.date), ``nav`` (float), ``shares_outstanding``,
    ``total_net_assets`` (the latter two may be None where the workbook
    prints '-').
    """
    grid = xlsx_grid(path)
    header_idx = None
    for i, row in enumerate(grid):
        if row and row[0].strip().lower() == "date":
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("navhist header row ('Date') not found")
    out = []
    for row in grid[header_idx + 1 :]:
        if not row or not row[0].strip():
            continue
        raw_date = row[0].strip()
        # real files interleave banner/footer text rows (e.g. rebranding
        # notices); only rows whose first cell is a DD-Mon-YYYY date are data
        try:
            d = dt.datetime.strptime(raw_date, "%d-%b-%Y").date()
        except ValueError:
            continue
        nav = _opt_float(row[1]) if len(row) > 1 else None
        if nav is None:
            continue  # non-priced placeholder row; recorded by gap audit upstream
        out.append(
            {
                "date": d,
                "nav": nav,
                "shares_outstanding": _opt_float(row[2]) if len(row) > 2 else None,
                "total_net_assets": _opt_float(row[3]) if len(row) > 3 else None,
            }
        )
    out.sort(key=lambda r: r["date"])
    return out


def parse_spdr_distributions(path, ticker: Optional[str] = None) -> List[dict]:
    """Parse the SPDR ETF historical distributions workbook.

    Layout (verified 2026-09-03): one header row
    ``FUND NAME | TICKER | CUSIP | EX-DATE | RECORD DATE | PAYABLE DATE |`
    DIVIDEND ($) | SHORT TERM CAPITAL GAIN ($) | LONG TERM CAPITAL GAIN ($)``
    with dates as ``MM/DD/YYYY``. Optionally filter by ticker. Returns
    ascending ex-date list of dicts; ``amount`` is dividend + STCG + LTCG
    (empty cells count as zero).
    """
    grid = xlsx_grid(path)
    header_idx = None
    for i, row in enumerate(grid):
        if row and row[0].strip().upper() == "FUND NAME":
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("distributions header row ('FUND NAME') not found")

    def _num(cell: str) -> float:
        return _opt_float(cell) or 0.0

    out = []
    for row in grid[header_idx + 1 :]:
        if not row or not row[0].strip():
            continue
        # footer/banner rows have no parseable MM/DD/YYYY ex-date: skip them
        try:
            ex_date = (
                dt.datetime.strptime(row[3].strip(), "%m/%d/%Y").date()
                if len(row) > 3 and row[3].strip()
                else None
            )
        except ValueError:
            continue
        if ex_date is None:
            continue
        rec = {
            "fund_name": row[0].strip(),
            "ticker": row[1].strip() if len(row) > 1 else "",
            "cusip": row[2].strip() if len(row) > 2 else "",
            "ex_date": ex_date,
            "record_date": row[4].strip() if len(row) > 4 else "",
            "payable_date": row[5].strip() if len(row) > 5 else "",
            "dividend": _num(row[6]) if len(row) > 6 else 0.0,
            "st_capital_gain": _num(row[7]) if len(row) > 7 else 0.0,
            "lt_capital_gain": _num(row[8]) if len(row) > 8 else 0.0,
        }
        rec["amount"] = rec["dividend"] + rec["st_capital_gain"] + rec["lt_capital_gain"]
        if ticker is None or rec["ticker"] == ticker:
            out.append(rec)
    out.sort(key=lambda r: (r["ex_date"] or dt.date.min, r["ticker"]))
    return out


# ------------------------------------------------------- total-return model
TR_CONVENTION = (
    "total-return factor uses cash distributions reinvested at the same "
    "session's NAV on the ex-date: f_t = (nav_t + dist_t) / nav_{t-1}, "
    "f_0 = 1; splits are absent from SSGA ETF NAV history in the sampled "
    "files and any split event must be added as a separate factor record "
    "before use"
)


def reconstruct_total_return(
    nav_by_date: Dict[dt.date, float],
    distributions: Sequence[dict],
) -> Dict[dt.date, float]:
    """Reconstruct a cumulative total-return index from raw NAV + distributions.

    ``distributions`` items need ``ex_date`` and ``amount``. Any distribution
    whose ex-date is missing from ``nav_by_date`` is recorded by
    :func:`distribution_coverage_conflicts` and silently SKIPPED here by
    design (the caller must reconcile the conflict report).
    """
    dates = sorted(nav_by_date)
    if not dates:
        return {}
    dist_by_date: Dict[dt.date, float] = {}
    for rec in distributions:
        ex = rec.get("ex_date")
        if ex is not None:
            dist_by_date[ex] = dist_by_date.get(ex, 0.0) + float(rec.get("amount", 0.0))
    index: Dict[dt.date, float] = {dates[0]: 1.0}
    prev = nav_by_date[dates[0]]
    prev_date = dates[0]
    for d in dates[1:]:
        nav = nav_by_date[d]
        f = (nav + dist_by_date.get(d, 0.0)) / prev
        index[d] = index[prev_date] * f
        prev = nav
        prev_date = d
    return index


def distribution_coverage_conflicts(
    nav_dates: Sequence[dt.date],
    distributions: Sequence[dict],
) -> List[dict]:
    """Distributions whose ex-date has no NAV observation (recorded conflicts)."""
    have = set(nav_dates)
    return [
        {"ex_date": rec.get("ex_date"), "amount": rec.get("amount"), "ticker": rec.get("ticker", "")}
        for rec in distributions
        if rec.get("ex_date") is not None and rec["ex_date"] not in have
    ]


@dataclass
class ReconciliationReport:
    """Pairwise series comparison with per-date conflict records."""

    status: str
    declared_tolerance_rel: float
    n_common_dates: int
    max_abs_rel_diff: float
    mean_abs_rel_diff: float
    conflicts: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def compare_series_on_common_dates(
    series_a: Dict[dt.date, float],
    series_b: Dict[dt.date, float],
    tolerance_rel: float,
) -> ReconciliationReport:
    """Compare two cumulative-index series on common dates with declared tol."""
    common = sorted(set(series_a) & set(series_b))
    conflicts: List[dict] = []
    max_diff = 0.0
    total = 0.0
    for d in common:
        va, vb = float(series_a[d]), float(series_b[d])
        denom = max(abs(vb), 1e-12)
        rel = abs(va - vb) / denom
        total += rel
        max_diff = max(max_diff, rel)
        if rel > tolerance_rel:
            conflicts.append(
                {"date": d.isoformat(), "series_a": va, "series_b": vb, "rel_diff": rel}
            )
    return ReconciliationReport(
        status="PASS" if not conflicts and common else ("CONFLICT" if conflicts else "NO_COMMON_DATES"),
        declared_tolerance_rel=tolerance_rel,
        n_common_dates=len(common),
        max_abs_rel_diff=max_diff,
        mean_abs_rel_diff=(total / len(common)) if common else 0.0,
        conflicts=conflicts,
    )


def nav_vs_close_conflicts(
    nav_by_date: Dict[dt.date, float],
    close_by_date: Dict[dt.date, float],
    tolerance_rel: float,
    label_close: str = "provider_close",
) -> ReconciliationReport:
    """NAV vs exchange-close premium/discount conflicts, recorded not averaged.

    ETF NAV and close legitimately differ by the premium/discount; the point
    here is to RECORD the magnitude distribution and flag dates beyond the
    declared tolerance so the cohort lane can block affected instruments.
    """
    report = compare_series_on_common_dates(close_by_date, nav_by_date, tolerance_rel)
    report.status = (
        "PASS" if report.n_common_dates and not report.conflicts else
        ("CONFLICT" if report.conflicts else "NO_COMMON_DATES")
    )
    return report
