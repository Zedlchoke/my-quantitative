"""Synthetic goldens for SPY TR reconstruction + reconciliation (A3).

Includes a HAND-COMPUTED toy example: NAV 100 -> 101 (ex-date distribution
1.00 on day 2) -> 102 must give daily growth factors 102/100 and 102/101
and cumulative TR 1.02 * 102/101.
"""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MODULE_PATH = REPO_ROOT / "research" / "stocks_free_v1" / "spy_benchmark.py"
_SPEC = importlib.util.spec_from_file_location("z1_a3_spy_benchmark", _MODULE_PATH)
spy = importlib.util.module_from_spec(_SPEC)
sys.modules["z1_a3_spy_benchmark"] = spy
_SPEC.loader.exec_module(spy)

# --- hand-computed toy reconstruction --------------------------------------------- #


def _toy_nav_rows() -> list[spy.NavRow]:
    return [
        spy.NavRow(nav_date=date(2016, 1, 4), nav=100.0),
        spy.NavRow(nav_date=date(2016, 1, 5), nav=101.0),
        spy.NavRow(nav_date=date(2016, 1, 6), nav=102.0),
    ]


def test_hand_computed_toy_total_return() -> None:
    dists = [
        spy.DistributionRow(ex_date=date(2016, 1, 5), ordinary=1.0),
    ]
    rec = spy.reconstruct_total_return(_toy_nav_rows(), dists)
    assert rec.status == "RECONCILED"
    # day 2: (101 + 1.00) / 100 = 1.02 exactly
    # day 3: 102 / 101 (no distribution)
    expected_cumulative = (102.0 / 100.0) * (102.0 / 101.0)
    levels = rec.tr.tr_levels
    assert levels[0] == 1.0
    assert levels[1] == pytest.approx(1.02, abs=1e-15)
    assert levels[2] == pytest.approx(expected_cumulative, abs=1e-15)
    assert rec.distribution_count_applied == 1
    assert rec.ex_dates_missing_from_nav == ()
    assert rec.conflicts == ()


def test_no_distribution_matches_price_only_exactly() -> None:
    rec = spy.reconstruct_total_return(_toy_nav_rows(), [])
    price_index = {row.nav_date: row.nav for row in _toy_nav_rows()}
    report = spy.reconcile_tr_vs_price(rec.tr, price_index)
    assert report.status == "RECONCILED"
    assert report.cumulative_relative_difference == pytest.approx(0.0, abs=1e-15)
    # TR and price growth identical with zero distributions
    assert report.tr_growth == pytest.approx(1.02, abs=1e-15)


def test_distribution_not_reinvested_would_understate_detected() -> None:
    # if the ex-date distribution were (wrongly) dropped, TR growth would
    # equal price growth; slack must then expose the discrepancy on a
    # distribution-paying series
    dists = [spy.DistributionRow(ex_date=date(2016, 1, 5), ordinary=1.0)]
    rec = spy.reconstruct_total_return(_toy_nav_rows(), dists)
    # price-only growth (102/100) is strictly below TR growth ((102+1)/100)*(102/101)
    price_index = {row.nav_date: row.nav for row in _toy_nav_rows()}
    report = spy.reconcile_tr_vs_price(rec.tr, price_index)
    assert report.cumulative_relative_difference > 0.0


def test_ex_date_missing_from_nav_is_recorded_not_dropped() -> None:
    dists = [
        spy.DistributionRow(ex_date=date(2016, 1, 5), ordinary=1.0),
        spy.DistributionRow(ex_date=date(2016, 1, 7), ordinary=0.5),  # not a NAV date
    ]
    rec = spy.reconstruct_total_return(_toy_nav_rows(), dists)
    assert rec.status == "CONFLICTS_RECORDED"
    assert date(2016, 1, 7) in rec.ex_dates_missing_from_nav
    kinds = {c.kind for c in rec.conflicts}
    assert "DISTRIBUTION_EX_DATE_NOT_IN_NAV" in kinds
    # the applied distribution is still exactly the hand-computed one
    assert rec.tr.tr_levels[1] == pytest.approx(1.02, abs=1e-15)


def test_nonpositive_nav_fails_closed() -> None:
    rows = [
        spy.NavRow(nav_date=date(2016, 1, 4), nav=100.0),
        spy.NavRow(nav_date=date(2016, 1, 5), nav=0.0),
    ]
    with pytest.raises(spy.SpyBenchmarkError):
        spy.reconstruct_total_return(rows, [])


def test_single_nav_row_fails_closed() -> None:
    with pytest.raises(spy.SpyBenchmarkError):
        spy.reconstruct_total_return([spy.NavRow(nav_date=date(2016, 1, 4), nav=1.0)], [])


# --- reconcilers -------------------------------------------------------------------


def test_reconcile_vs_price_needs_overlapping_dates() -> None:
    rec = spy.reconstruct_total_return(_toy_nav_rows(), [])
    report = spy.reconcile_tr_vs_price(rec.tr, {date(2016, 1, 4): 100.0})
    assert report.status == "FAIL"
    assert report.conflicts[0].kind == "FAIL"


def test_tr_below_price_growth_is_a_recorded_conflict() -> None:
    rec = spy.reconstruct_total_return(_toy_nav_rows(), [])
    # fake "price" index that grew MORE than raw NAV (impossible raw-vs-TR
    # relationship) -> must be surfaced, never silently accepted
    price_index = {
        date(2016, 1, 4): 100.0,
        date(2016, 1, 5): 105.0,
        date(2016, 1, 6): 110.0,
    }
    report = spy.reconcile_tr_vs_price(rec.tr, price_index)
    assert report.status == "CONFLICTS_RECORDED"
    assert report.conflicts[0].kind == "TR_BELOW_PRICE_GROWTH"


def test_reconcile_vs_adjusted_within_tolerance_passes() -> None:
    rec = spy.reconstruct_total_return(_toy_nav_rows(), [])
    adjusted = dict(zip(rec.tr.dates, rec.tr.tr_levels))
    report = spy.reconcile_tr_vs_adjusted(rec.tr, adjusted)
    assert report.status == "RECONCILED"
    assert report.conflicts == ()


def test_reconcile_vs_adjusted_growth_step_perturbation_conflicts() -> None:
    rec = spy.reconstruct_total_return(_toy_nav_rows(), [])
    # perturb ONE daily growth step by +5% (level shift alone would cancel
    # in a growth-based comparison by construction)
    dates = list(rec.tr.dates)
    levels = list(rec.tr.tr_levels)
    adjusted_levels = [
        level * (1.05 if i == 1 else 1.0) for i, level in enumerate(levels)
    ]
    adjusted = dict(zip(dates, adjusted_levels))
    report = spy.reconcile_tr_vs_adjusted(rec.tr, adjusted)
    assert report.status == "CONFLICTS_RECORDED"
    kinds = {c.kind for c in report.conflicts}
    assert "DAILY_LOG_TOLERANCE_EXCEEDED" in kinds
    # conflicts carry detail; nothing is silently resolved
    assert all(c.detail for c in report.conflicts)


def test_reconcile_vs_adjusted_insufficient_overlap_fails() -> None:
    rec = spy.reconstruct_total_return(_toy_nav_rows(), [])
    report = spy.reconcile_tr_vs_adjusted(rec.tr, {date(2016, 1, 4): 1.0})
    assert report.status == "FAIL"


# --- coverage summary ----------------------------------------------------------------


def test_summarize_coverage_golden() -> None:
    summary = spy.summarize_coverage(_toy_nav_rows())
    assert summary.first == date(2016, 1, 4)
    assert summary.last == date(2016, 1, 6)
    assert summary.rows == 3
    assert summary.years == pytest.approx(2 / 365.25, abs=1e-9)
    as_dict = summary.as_dict()
    assert as_dict["first"] == "2016-01-04"
    assert as_dict["rows"] == 3


# --- stdlib xlsx reader (synthetic workbook built in-tmp) ---------------------------- #

_XLSX_XML = """<?xml version="1.0"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <sheets><sheet name="t" sheetId="1" r:id="r1"/></sheets>
</workbook>"""


def _write_synthetic_xlsx(path: Path) -> None:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="r2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        "</Relationships>"
    )
    shared = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="4" uniqueCount="4">'
        "<si><t>Date</t></si><si><t>NAV</t></si>"
        "<si><t>04-Jan-2016</t></si><si><t>05-Jan-2016</t></si>"
        "</sst>"
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
        '<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2"><v>100.5</v></c></row>'
        '<row r="3"><c r="A3" t="s"><v>3</v></c><c r="B3"><v>101.25</v></c></row>'
        "</worksheet>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", _XLSX_XML)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def test_parse_synthetic_ssga_style_nav_workbook(tmp_path) -> None:
    workbook = tmp_path / "synthetic-nav.xlsx"
    _write_synthetic_xlsx(workbook)
    rows = spy.parse_ssga_nav_history(workbook)
    assert [(r.nav_date.isoformat(), r.nav) for r in rows] == [
        ("2016-01-04", 100.5),
        ("2016-01-05", 101.25),
    ]


def test_xlsx_reader_missing_file_fails_closed(tmp_path) -> None:
    with pytest.raises(spy.SpyBenchmarkError):
        spy.read_xlsx_rows(tmp_path / "nope.xlsx")


def test_sha256_file_golden(tmp_path) -> None:
    target = tmp_path / "blob.bin"
    target.write_bytes(b"z1-a3-spy-tr-benchmark")
    # sha256 of the exact byte string above (computed independently)
    import hashlib

    assert spy.sha256_file(target) == hashlib.sha256(b"z1-a3-spy-tr-benchmark").hexdigest()


# --- real downloaded official files (staged outside Git) ------------------------------ #
# When the A3 lane's staged SSGA downloads exist, parse them and record the
# measured coverage; otherwise the checks are NOT_RUN (never faked).

STAGING = REPO_ROOT.parent / "staging-cohort"
NAV_FILE = STAGING / "navhist-us-en-spy.xlsx"
DIST_FILE = STAGING / "spdr-etf-historical-distributions.xlsx"


def test_official_ssga_files_parse_when_staged() -> None:
    if not (NAV_FILE.is_file() and DIST_FILE.is_file()):
        pytest.skip("staged SSGA downloads not present on this host: NOT_RUN")
    nav = spy.parse_ssga_nav_history(NAV_FILE)
    dists = spy.parse_ssga_distributions(DIST_FILE, "SPY")
    assert len(nav) > 5000 and len(dists) > 100
    rec = spy.reconstruct_total_return(nav, dists)
    # TR must exceed price-only growth over the staged coverage
    price_index = {row.nav_date: row.nav for row in nav}
    report = spy.reconcile_tr_vs_price(rec.tr, price_index)
    assert report.status == "RECONCILED"
    assert report.cumulative_relative_difference > 0.05  # dividends matter
